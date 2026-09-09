# Wekkers vanaf Android naar het dashboard

Het dashboard heeft een endpoint `POST /api/alarms`. Laat je telefoon daar de eerstvolgende wekker
naartoe sturen. Werkt met MacroDroid (gratis) of Tasker. Telefoon en laptop moeten op hetzelfde
Wi-Fi zitten (of gebruik Tailscale). Zet in `.env` `DASHBOARD_HOST=0.0.0.0` zodat de laptop
bereikbaar is op het LAN, en vul `DASHBOARD_SECRET` in.

## MacroDroid
1. Nieuwe macro. Trigger: **Alarm** -> "Alarm set/changed" (bij oudere versies: "Next alarm changed").
2. Actie: **HTTP Request (POST)**
   - URL: `http://<laptop-ip>:8000/api/alarms`
   - Header: `X-Dashboard-Secret` = het geheim uit `.env`
   - Content type: `application/json`
   - Body:
     ```json
     {"app": "phone", "label": "Wekker", "at": "{alarm_time_ms}"}
     ```
     (`at` mag een epoch in milliseconden of een ISO-tijd zijn. Leeg = wekker weg.)
3. Optioneel: tweede macro met trigger "Alarm dismissed" die dezelfde POST doet met `"at": ""`.

## Testen vanaf de laptop
```bash
curl -X POST http://127.0.0.1:8000/api/alarms -H "X-Dashboard-Secret: $SECRET" \
  -H "Content-Type: application/json" -d '{"app":"phone","label":"Test","at":"2026-09-10T07:30:00"}'
```
