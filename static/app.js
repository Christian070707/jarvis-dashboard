/* Jarvis: klok, dagvoortgang, aftellers, ververs-animaties, briefing, focusmodus. Geen frameworks. */
(function () {
  'use strict';
  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
  const pad = n => String(n).padStart(2, '0');
  const store = {
    get(k, d) { try { const v = localStorage.getItem(k); return v === null ? d : JSON.parse(v); } catch { return d; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch {} },
    del(k) { try { localStorage.removeItem(k); } catch {} },
  };

  // ---------- klok + dagvoortgang + ring-wijzer ----------
  function tick() {
    const d = new Date();
    const clock = $('#clock');
    if (clock) clock.textContent =
      d.toLocaleDateString('nl-NL', { weekday: 'long', day: 'numeric', month: 'long' }) + ' · ' +
      pad(d.getHours()) + ':' + pad(d.getMinutes());
    const pct = (d.getHours() * 3600 + d.getMinutes() * 60 + d.getSeconds()) / 864;
    const dp = $('#dayprog');
    if (dp) { dp.querySelector('i').style.width = pct + '%'; dp.querySelector('b').textContent = Math.round(pct) + '%'; }
    const hand = $('#ring-hand');
    if (hand) hand.setAttribute('transform', `rotate(${pct * 3.6} 100 100)`);
    const el = $('#ring-elapsed');
    if (el) el.setAttribute('stroke-dasharray', `${pct} ${100 - pct}`);
    const rc = $('#ring-clock');
    if (rc) rc.textContent = pad(d.getHours()) + ':' + pad(d.getMinutes());
    const rp = $('#ring-pct');
    if (rp) rp.textContent = Math.round(pct) + '% van de dag';
  }
  tick(); setInterval(tick, 5000);

  // ---------- aftellers (data-countdown="ISO") ----------
  function fmtDelta(ms) {
    const s = Math.max(0, Math.round(ms / 1000));
    const d = Math.floor(s / 86400), h = Math.floor((s % 86400) / 3600), m = Math.floor((s % 3600) / 60), sec = s % 60;
    if (d > 0) return `${d} d ${h} u`;
    if (h > 0) return `${h} u ${pad(m)} min`;
    if (m > 0) return `${m}:${pad(sec)} min`;
    return `${sec} s`;
  }
  function countdowns() {
    const now = Date.now();
    $$('[data-countdown]').forEach(el => {
      const at = el.dataset.countdown; if (!at) { el.textContent = ''; return; }
      const ms = new Date(at).getTime() - now;
      el.textContent = (el.dataset.prefix || '') + (ms <= 0 ? 'nu' : fmtDelta(ms)) + (ms > 0 ? (el.dataset.suffix || '') : '');
      el.classList.toggle('soon', ms > 0 && ms < 15 * 60 * 1000);
    });
  }
  countdowns(); setInterval(countdowns, 1000);

  // ---------- ververs-animaties ----------
  document.body.addEventListener('htmx:afterSwap', e => {
    const t = e.detail.target;
    const col = t.closest('.col') || t;
    col.classList.remove('sweep'); void col.offsetWidth; col.classList.add('sweep');
    setTimeout(() => col.classList.remove('sweep'), 1200);
    $$('.item', t).forEach((li, i) => li.style.setProperty('--i', Math.min(i, 14)));
    if (t.id === 'status') $$('.pill', t).forEach(p => p.classList.add('pulse'));
    countdowns();
    if (t.id === 'briefing') maybeShowBriefing();
  });

  // ---------- briefing ----------
  const todayKey = () => new Date().toISOString().slice(0, 10);
  function maybeShowBriefing(force) {
    const box = $('#briefing'); if (!box || !box.children.length) return;
    const dismissed = store.get('jarvis.briefing.dismissed', '') === todayKey();
    box.hidden = dismissed && !force;
  }
  $('#btn-briefing').addEventListener('click', () => {
    const box = $('#briefing');
    if (!box.hidden) { box.hidden = true; return; }
    store.del('jarvis.briefing.dismissed'); maybeShowBriefing(true);
    box.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
  document.body.addEventListener('click', e => {
    if (e.target.id === 'briefing-close') { store.set('jarvis.briefing.dismissed', todayKey()); $('#briefing').hidden = true; }
    if (e.target.id === 'briefing-speak') speak(e.target.dataset.text, e.target);
  });
  function speak(text, btn) {
    if (!('speechSynthesis' in window)) { alert('Geen spraak beschikbaar in deze browser.'); return; }
    const synth = window.speechSynthesis;
    if (synth.speaking) { synth.cancel(); btn.classList.remove('active'); return; }
    const u = new SpeechSynthesisUtterance(text);
    const voices = synth.getVoices();
    u.voice = voices.find(v => /nl[-_]NL/i.test(v.lang)) || voices.find(v => /^nl/i.test(v.lang)) || null;
    u.lang = 'nl-NL'; u.rate = 1.02; u.pitch = 0.9;
    u.onend = () => btn.classList.remove('active');
    btn.classList.add('active'); synth.speak(u);
  }
  if ('speechSynthesis' in window) speechSynthesis.getVoices();

  // ---------- focusmodus ----------
  const focus = {
    el: $('#focus'), pick: $('#focus-pick'), run: $('#focus-run'), timer: null, minutes: 25,
    state: store.get('jarvis.focus', null),
  };
  function openFocus() {
    focus.el.hidden = false; document.body.classList.add('focused');
    if (focus.state && focus.state.endAt > Date.now()) { showRun(); }
    else { focus.pick.hidden = false; focus.run.hidden = true; htmx.trigger(document.body, 'focusopen'); }
  }
  function closeFocus() {
    focus.el.hidden = true; document.body.classList.remove('focused');
    if (focus.timer) { clearInterval(focus.timer); focus.timer = null; }
  }
  function startFocus(title, url) {
    focus.state = { title, url, endAt: Date.now() + focus.minutes * 60000, total: focus.minutes * 60000 };
    store.set('jarvis.focus', focus.state); showRun();
    if ('Notification' in window && Notification.permission === 'default') Notification.requestPermission();
  }
  function showRun() {
    focus.pick.hidden = true; focus.run.hidden = false;
    $('#focus-title').textContent = focus.state.title;
    const link = $('#focus-link'); link.hidden = !focus.state.url; link.href = focus.state.url || '#';
    if (focus.timer) clearInterval(focus.timer);
    const step = () => {
      const left = focus.state.endAt - Date.now();
      const s = Math.max(0, Math.ceil(left / 1000));
      $('#focus-timer').textContent = `${pad(Math.floor(s / 60))}:${pad(s % 60)}`;
      $('#focus-bar').style.width = Math.max(0, Math.min(100, 100 - (left / focus.state.total) * 100)) + '%';
      document.title = left > 0 ? `${pad(Math.floor(s / 60))}:${pad(s % 60)} · Jarvis` : 'Jarvis';
      if (left <= 0) { clearInterval(focus.timer); focus.timer = null; finishFocus(); }
    };
    step(); focus.timer = setInterval(step, 500);
  }
  function finishFocus() {
    $('#focus-timer').textContent = 'KLAAR';
    beep();
    if ('Notification' in window && Notification.permission === 'granted')
      new Notification('Jarvis', { body: `Focusblok klaar: ${focus.state.title}` });
    store.del('jarvis.focus'); focus.state = null;
  }
  function beep() {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      [0, 0.18, 0.36].forEach(t => {
        const o = ctx.createOscillator(), g = ctx.createGain();
        o.type = 'sine'; o.frequency.value = 880; o.connect(g); g.connect(ctx.destination);
        g.gain.setValueAtTime(0.0001, ctx.currentTime + t);
        g.gain.exponentialRampToValueAtTime(0.2, ctx.currentTime + t + 0.02);
        g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + t + 0.15);
        o.start(ctx.currentTime + t); o.stop(ctx.currentTime + t + 0.16);
      });
    } catch {}
  }
  $('#btn-focus').addEventListener('click', () => focus.el.hidden ? openFocus() : closeFocus());
  $('#focus-close').addEventListener('click', closeFocus);
  $('#focus-stop').addEventListener('click', () => { store.del('jarvis.focus'); focus.state = null; document.title = 'Jarvis'; closeFocus(); });
  $('#focus-plus').addEventListener('click', () => { if (focus.state) { focus.state.endAt += 5 * 60000; focus.state.total += 5 * 60000; store.set('jarvis.focus', focus.state); } });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && !focus.el.hidden) closeFocus(); });
  focus.pick.addEventListener('click', e => {
    const dur = e.target.closest('.dur');
    if (dur) { focus.minutes = +dur.dataset.min; $$('.dur', focus.pick).forEach(b => b.classList.toggle('on', b === dur)); return; }
    const p = e.target.closest('.pick');
    if (p) startFocus(p.dataset.title, p.dataset.url);
  });
  focus.pick.addEventListener('submit', e => {
    if (e.target.id !== 'focus-custom') return;
    e.preventDefault();
    const v = e.target.querySelector('input').value.trim();
    if (v) startFocus(v, '');
  });
  document.body.addEventListener('htmx:afterSwap', e => {
    if (e.detail.target.id === 'focus-pick') $$('.dur', focus.pick).forEach(b => b.classList.toggle('on', +b.dataset.min === focus.minutes));
  });
  // ---------- thema's ----------
  const THEMES = ['arc', 'blush', 'matrix'];
  function currentTheme() { return document.documentElement.dataset.theme || 'arc'; }
  function applyTheme(name) {
    if (name === 'arc') delete document.documentElement.dataset.theme; else document.documentElement.dataset.theme = name;
    store.set('jarvis.theme', name);
    $('#btn-theme').textContent = '◐ ' + name;
    rain.update();
  }
  $('#btn-theme').addEventListener('click', () => applyTheme(THEMES[(THEMES.indexOf(currentTheme()) + 1) % THEMES.length]));
  $('#btn-theme').textContent = '◐ ' + currentTheme();

  // matrix-regen: alleen actief in het groene thema
  const rain = {
    canvas: $('#rain'), raf: null, drops: [],
    update() { if (currentTheme() === 'matrix') this.start(); else this.stop(); },
    start() {
      if (this.raf) return;
      const c = this.canvas, ctx = c.getContext('2d');
      const chars = 'ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉ0123456789ABCDEFXYZ<>/\\|=+*';
      const size = 16;
      const resize = () => { c.width = innerWidth; c.height = innerHeight; this.drops = Array(Math.ceil(c.width / size)).fill(0).map(() => Math.random() * -50); };
      resize(); addEventListener('resize', resize);
      let last = 0;
      const frame = t => {
        this.raf = requestAnimationFrame(frame);
        if (t - last < 70) return; last = t;
        ctx.fillStyle = 'rgba(0,0,0,.08)'; ctx.fillRect(0, 0, c.width, c.height);
        ctx.font = size + 'px monospace';
        this.drops.forEach((y, i) => {
          const ch = chars[Math.floor(Math.random() * chars.length)];
          ctx.fillStyle = Math.random() < .08 ? '#ccffd6' : '#00ff41';
          ctx.fillText(ch, i * size, y * size);
          this.drops[i] = y * size > c.height && Math.random() > .975 ? 0 : y + 1;
        });
      };
      this.raf = requestAnimationFrame(frame);
    },
    stop() { if (this.raf) { cancelAnimationFrame(this.raf); this.raf = null; } const ctx = this.canvas.getContext('2d'); ctx.clearRect(0, 0, this.canvas.width, this.canvas.height); },
  };
  rain.update();

  // ---------- init: server-side voorgerenderde inhoud behandelen als eerste swap ----------
  $$('.col').forEach(col => $$('.item', col).forEach((li, i) => li.style.setProperty('--i', Math.min(i, 14))));
  maybeShowBriefing();
  if (focus.state && focus.state.endAt > Date.now()) openFocus();
})();
