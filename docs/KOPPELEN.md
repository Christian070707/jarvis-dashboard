# Jarvis koppelen aan je apps en services

Deze handleiding legt stap voor stap uit hoe je elke bron aan Jarvis koppelt: je rooster,
agenda's, deadlines, mail en de wekker van je telefoon. Lees hem rustig door; je hoeft niet
alles te koppelen. Alles wat je leeg laat, staat gewoon uit. De eigen takenlijst werkt altijd,
ook zonder één enkele koppeling.

Inhoud

1. [Hoe Jarvis werkt](#1-hoe-jarvis-werkt)
2. [Voordat je begint](#2-voordat-je-begint)
3. [De instellingenpagina](#3-de-instellingenpagina)
4. [Rooster: TimeEdit](#4-rooster-timeedit)
5. [Deadlines: Canvas](#5-deadlines-canvas)
6. [Google: agenda en Gmail](#6-google-agenda-en-gmail)
7. [Outlook-agenda (UT of werk)](#7-outlook-agenda-ut-of-werk)
8. [Trello](#8-trello)
9. [Wekkers vanaf je Android-telefoon](#9-wekkers-vanaf-je-android-telefoon)
10. [Outlook mail en To Do via Microsoft Graph (geavanceerd)](#10-outlook-mail-en-to-do-via-microsoft-graph-geavanceerd)
11. [Instellen via een .env-bestand (zonder wizard)](#11-instellen-via-een-env-bestand-zonder-wizard)
12. [Controleren of alles werkt](#12-controleren-of-alles-werkt)
13. [Problemen oplossen](#13-problemen-oplossen)
14. [Privacy en veiligheid](#14-privacy-en-veiligheid)
15. [Overzicht van alle instellingen](#15-overzicht-van-alle-instellingen)

---

## 1. Hoe Jarvis werkt

Jarvis is een programma dat op je eigen computer draait. Het haalt op de achtergrond gegevens op
bij de bronnen die je hebt gekoppeld, zet ze in een lokale database en toont ze op één pagina in
je browser. Elk item op het dashboard linkt terug naar de bron: klik op een college en TimeEdit
opent, klik op een deadline en je zit in Canvas.

Er zijn twee manieren waarop een bron gekoppeld kan zijn:

- **Via een agendalink (iCal / ICS).** Bijna elke agenda-app kan een geheime link uitdelen waar
  je agenda als bestand achter zit. Jarvis downloadt die link elke 15 minuten. Je hoeft nergens
  in te loggen en er is geen ontwikkelaarsaccount nodig. Dit is de makkelijkste manier en voor de
  meeste mensen genoeg.
- **Via een API-koppeling.** Hierbij log je in of maak je een toegangssleutel aan. Jarvis krijgt
  dan rijkere informatie (bijvoorbeeld ongelezen mail, of welke Canvas-opdrachten je al hebt
  ingeleverd) en ververst vaker. Dit kost wat meer moeite om in te stellen.

Voor Canvas en Google Agenda bestaan beide varianten. Als je de API-variant koppelt, schakelt
Jarvis automatisch de agendalink-variant van dezelfde bron uit, zodat je geen dubbele items ziet.

Hoe vaak elke bron ververst:

| Bron | Ververst elke |
|---|---|
| TimeEdit, Canvas-agenda, Google-agendalink, Outlook-agendalink | 15 minuten |
| Canvas API | 10 minuten |
| Trello, Google Calendar API | 5 minuten |
| Outlook via Microsoft Graph | 3 minuten |
| Gmail | 2 minuten |

Je kunt een bron altijd handmatig verversen door bovenin het dashboard op de pil van die bron te
klikken.

---

## 2. Voordat je begint

**Wat je nodig hebt**

- Jarvis geïnstalleerd en gestart. Zie de README voor het downloaden van de app of het starten
  vanuit de broncode.
- Een browser waarin je bent ingelogd bij de diensten die je wilt koppelen (TimeEdit, Canvas,
  Google, Outlook, Trello).
- Ongeveer 5 minuten per bron. De agendalinks zijn in een minuut gedaan; Google via de knop
  "Verbinden" kost twee minuten; de geavanceerde Microsoft-koppeling kan een kwartier duren en
  werkt niet bij elke universiteit.

**Waar je gegevens staan**

Alles wat je invult blijft op je eigen computer, in een map die Jarvis onderaan de
instellingenpagina laat zien:

| Systeem | Map |
|---|---|
| Windows | `%APPDATA%\Jarvis` (meestal `C:\Users\<jij>\AppData\Roaming\Jarvis`) |
| Linux | `~/.local/share/Jarvis` |
| Mac | `~/Library/Application Support/Jarvis` |
| Vanuit de broncode | de map `data/` in het project |

In deze map staan de database (`dashboard.sqlite3`), eventuele tokens (`google_token.json`,
`ms_token.json`), het logbestand (`jarvis.log`) en optioneel een `.env`-bestand.

**Aanbevolen volgorde**

Begin met de agendalinks (TimeEdit, Canvas, Outlook). Die zijn snel en kunnen niet stuk. Koppel
daarna Google en Trello. Doe de wekker en Microsoft Graph als laatste, alleen als je ze echt
wilt.

---

## 3. De instellingenpagina

Bij de eerste start opent Jarvis automatisch de instellingenpagina. Later kom je er terug door
op het tandwiel (⚙) rechtsboven op het dashboard te klikken, of door naar
`http://127.0.0.1:8000/setup` te gaan (het poortnummer kan anders zijn als je de app gebruikt;
kijk in de adresbalk).

De pagina bestaat uit genummerde stappen. Elke stap heeft dezelfde drie knoppen:

- **Test.** Probeert de bron op te halen met wat je nu hebt ingevuld, zonder op te slaan. Je
  ziet een groen vinkje met het aantal gevonden items en een voorbeeld, een gele waarschuwing
  als de verbinding werkt maar er nog niets in staat, of een rood kruis met de foutmelding.
- **Opslaan.** Slaat de waarde op in de database en herstart de bron direct.
- **Status-pil naast de kop.** Toont "uit", "actief · 12 items" of "! fout". Beweeg je muis
  over "fout" om de foutmelding te zien.

Test altijd eerst, sla daarna op. Als je klaar bent, klik je onderaan op "Klaar → naar het
dashboard". Die knop hoef je maar één keer te gebruiken; daarna opent Jarvis direct op het
dashboard.

**Stap 1: Universiteit.** Kies "Universiteit Twente" als je daar studeert. Jarvis vult dan de
juiste TimeEdit- en Canvas-adressen in en toont instructies die bij de UT passen. Kies anders
"Andere instelling"; je moet dan zelf het Canvas-adres invullen bij de geavanceerde
Canvas-instelling.

---

## 4. Rooster: TimeEdit

TimeEdit is het roostersysteem van de UT (en van veel andere instellingen). Jarvis toont je
colleges en tentamens in het blok "Vandaag" en in het overzicht van de komende dagen.

**Stap voor stap (UT)**

1. Ga naar https://cloud.timeedit.net/nl_utwente/web/ en log in met je UT-account.
2. Open je persoonlijke rooster (meestal "Mijn rooster" of "My schedule"). Zorg dat de vakken
   die je volgt erin staan.
3. Zoek de knop **Abonneren** (Engels: *Subscribe*), soms een agenda-icoon bovenaan het rooster.
4. Kies **Kopieer link** of *Copy link*. Kies niet "Downloaden"; dan krijg je een bestand dat
   nooit meer bijwerkt.
5. De link lijkt op `https://cloud.timeedit.net/nl_utwente/web/.../ri1234567.ics` en eindigt op
   `.ics`. Begint de link met `webcal://`? Dat is prima, Jarvis zet dat zelf om.
6. Plak de link in Jarvis bij stap 2, klik op **Test** en daarna op **Opslaan**.

**Andere instelling**

Zoek in je roostersysteem naar "Abonneren", "iCal", "ICS" of "Agenda-koppeling". Bijna elk
systeem kan een abonnementslink maken. Plak die op dezelfde plek.

**Goed om te weten**

- Jarvis toont van roosters en agenda's alles van gisteren tot 30 dagen vooruit.
- TimeEdit-links hebben soms een houdbaarheid van een semester. Krijg je later "! fout" op de
  TimeEdit-pil, maak dan gewoon een nieuwe link aan.
- Klik je op een college in Jarvis, dan opent het TimeEdit-webrooster. Dat adres staat in de
  instelling `TIMEEDIT_WEB_URL`; bij de UT is dat al ingevuld.

---

## 5. Deadlines: Canvas

Canvas is de leeromgeving met je opdrachten, quizzes en inleverdeadlines. Er zijn twee manieren
om te koppelen. De agendalink volstaat voor de meeste mensen. De API-koppeling is fijner omdat
ingeleverde opdrachten dan automatisch verdwijnen, maar niet elke universiteit staat die toe.

### 5a. Canvas-agendalink (aanbevolen om mee te beginnen)

1. Ga naar https://canvas.utwente.nl (of het Canvas-adres van je instelling) en log in.
2. Klik in de linkerbalk op **Agenda** (*Calendar*).
3. Klik rechtsonder op **Calendar Feed** (Nederlands soms "Agendafeed").
4. Er verschijnt een venster met een link die lijkt op
   `https://canvas.utwente.nl/feeds/calendars/user_AbCdEf123.ics`. Kopieer die.
5. Plak de link in Jarvis bij stap 3, **Test**, **Opslaan**.

Wat je ziet: alle opdrachten met een inleverdatum uit de vakken die je in Canvas hebt
aangevinkt in de agenda. Jarvis toont deadlines van twee weken terug tot 60 dagen vooruit.

Let op: de agendalink weet niet of je iets al hebt ingeleverd. Een opdracht blijft dus staan
tot de deadline voorbij is. Wil je dat niet, gebruik dan de API-koppeling hieronder of verberg
het item op het dashboard.

### 5b. Canvas-API-token (geavanceerd)

1. Ga in Canvas naar **Account** (linksboven, je foto) en dan **Instellingen** (*Settings*).
2. Scrol naar **Goedgekeurde integraties** (*Approved Integrations*) en klik op
   **+ Nieuw toegangstoken** (*+ New Access Token*).
3. Vul als doel "Jarvis" in. Laat de vervaldatum leeg of kies een datum ver in de toekomst.
4. Klik op **Token genereren** en kopieer het token direct. Canvas laat het maar één keer zien.
5. Open in Jarvis bij stap 3 het uitklapdeel **Geavanceerd: Canvas-API-token**. Controleer dat
   het Canvas-adres klopt (voor de UT `https://canvas.utwente.nl`) en plak het token.
6. **Test**, **Opslaan**.

Zie je de knop "Nieuw toegangstoken" niet? Dan staat je instelling het niet toe. De agendalink
uit 5a werkt dan nog steeds.

Wat de API-koppeling extra doet: ingeleverde en beoordeelde opdrachten verdwijnen automatisch,
je ziet het aantal punten, en Canvas-agenda-items (bijvoorbeeld een ingeplande presentatie)
komen ook mee. Zodra deze koppeling actief is, negeert Jarvis de agendalink uit 5a om dubbele
items te voorkomen.

---

## 6. Google: agenda en Gmail

Google kun je op twee manieren koppelen.

- **Verbinden met Google** (één klik): geeft Jarvis leestoegang tot al je Google-agenda's en tot
  je ongelezen Gmail. Dit is de volledige koppeling.
- **Agendalink van één agenda**: alleen je agenda, geen mail. Geen inloggen nodig.

### 6a. Verbinden met Google (agenda + Gmail)

Deze optie werkt alleen als de build van Jarvis die je gebruikt het bestand
`google_credentials.json` bevat. Staat bij stap 4 een knop **Verbinden met Google**, dan is dat
zo. Staat er in plaats daarvan een melding dat de koppeling niet beschikbaar is, ga dan naar 6b
of naar 6c om zelf zo'n bestand te maken.

1. Klik bij stap 4 op **Verbinden met Google**.
2. Je browser opent een Google-inlogpagina. Kies het account dat je wilt koppelen.
3. Google waarschuwt mogelijk dat de app "niet geverifieerd" is. Dat is normaal voor een
   persoonlijk programma. Klik op **Geavanceerd** en dan op **Doorgaan naar Jarvis**.
4. Geef toestemming voor "Agenda bekijken" en "E-mail bekijken". Jarvis vraagt alleen
   leesrechten; het kan niets versturen, wijzigen of verwijderen.
5. Sluit het browsertabblad en ga terug naar Jarvis. Binnen een paar seconden verschijnt
   "✓ Google gekoppeld (Gmail + Agenda)".

Je hebt vijf minuten om in te loggen; daarna geeft de knop een time-out en klik je gewoon
opnieuw.

Wat je ziet: alle agenda's die je in Google Agenda hebt aangevinkt (gisteren tot 30 dagen
vooruit) en de 30 nieuwste ongelezen mails in je inbox. Klik op een mail en Gmail opent het
juiste gesprek.

**Ontkoppelen:** klik op **Ontkoppelen** naast de knop. Jarvis verwijdert het token van je
computer. Wil je ook aan de kant van Google alles intrekken, ga dan naar
https://myaccount.google.com/permissions en verwijder Jarvis.

### 6b. Agendalink van één Google-agenda (zonder inloggen)

1. Ga naar https://calendar.google.com op een computer.
2. Klik op het tandwiel rechtsboven en dan op **Instellingen**.
3. Kies links onder "Instellingen voor mijn agenda's" de agenda die je wilt koppelen.
4. Scrol naar **Agenda integreren**.
5. Kopieer het **Privéadres in iCal-formaat**. Dit adres bevat `/private-` en eindigt op
   `basic.ics`. Gebruik niet het "Openbare adres"; dat werkt alleen als je agenda openbaar is.
6. Plak de link in Jarvis bij stap 4 onder het uitklapdeel **Alternatief zonder inloggen**,
   **Test**, **Opslaan**.

Wil je meerdere Google-agenda's? Dat kan alleen met de volledige koppeling uit 6a. De
agendalink neemt precies één agenda mee.

Heb je het privéadres per ongeluk gedeeld? Klik in dezelfde Google-instellingen op
**Privé-URL's opnieuw instellen**. De oude link werkt dan niet meer en je plakt de nieuwe in
Jarvis.

### 6c. Zelf een Google-credentialsbestand maken (voor gevorderden)

Dit is alleen nodig als je Jarvis vanuit de broncode draait of als je build geen
`google_credentials.json` meekrijgt, en je toch Gmail wilt. Het kost een keer een kwartier.

1. Ga naar https://console.cloud.google.com en log in.
2. Maak een nieuw project (bijvoorbeeld "Jarvis").
3. Ga naar **APIs & Services → Library**. Zoek en activeer de **Gmail API** en de
   **Google Calendar API**.
4. Ga naar **APIs & Services → OAuth consent screen**. Kies **External**, vul een naam en je
   e-mailadres in. Zet de app in **Testing** en voeg onder **Test users** je eigen
   Gmail-adres toe.
5. Ga naar **APIs & Services → Credentials → Create credentials → OAuth client ID**. Kies
   als type **Desktop app**. Download het JSON-bestand.
6. Zet dat bestand in de datamap van Jarvis (zie hoofdstuk 2) onder de naam
   `google_credentials.json`. Vanuit de broncode is dat `data/google_credentials.json`.
7. Herstart Jarvis. Bij stap 4 staat nu de knop **Verbinden met Google**. Volg 6a.

Vanuit de broncode kun je in plaats van de knop ook dit script draaien; het doet hetzelfde:

```bash
.venv/bin/python scripts/google_auth.py
```

Belangrijk: zolang je Google-project in de stand "Testing" staat, verloopt het token na
7 dagen. Jarvis meldt dan "Google-token ongeldig". Klik dan opnieuw op **Verbinden met Google**.
Wil je daarvan af, zet het project dan in de Google Console op **In production**. Google vraagt
dan om een verificatie; voor eigen gebruik kun je die overslaan, de "niet geverifieerd"-melding
bij het inloggen blijft dan gewoon staan.

---

## 7. Outlook-agenda (UT of werk)

Dit is de agenda van je universiteits- of werkaccount in Microsoft 365. Deze koppeling gaat via
een gepubliceerde agendalink en werkt bij bijna elke organisatie, ook als de IT-afdeling
app-koppelingen blokkeert.

1. Ga naar https://outlook.office.com en log in met je UT- of werkaccount.
2. Klik op het tandwiel rechtsboven en open **Instellingen** (*Settings*).
3. Ga naar **Agenda → Gedeelde agenda's** (*Calendar → Shared calendars*).
4. Onder **Een agenda publiceren** (*Publish a calendar*) kies je je agenda (meestal
   "Agenda" of "Calendar") en als machtiging **Kan alle details bekijken**
   (*Can view all details*). Met "Alleen beschikbaarheid" zie je in Jarvis alleen "Bezet"
   zonder titel.
5. Klik op **Publiceren**. Er verschijnen twee links: een HTML-link en een **ICS**-link.
   Kopieer de ICS-link; die lijkt op
   `https://outlook.office365.com/owa/calendar/…/calendar.ics`.
6. Plak de link in Jarvis bij stap 5, **Test**, **Opslaan**.

Staat de optie "Een agenda publiceren" er niet? Dan heeft de organisatie publiceren
uitgeschakeld. Probeer dan de geavanceerde Microsoft Graph-koppeling in hoofdstuk 10, of vraag
de IT-helpdesk.

Goed om te weten: Microsoft ververst een gepubliceerde agenda niet direct. Een nieuwe afspraak
kan tot een paar uur later pas in de link staan. Dat ligt niet aan Jarvis.

**Intrekken:** ga terug naar dezelfde instellingenpagina in Outlook en klik op
**Publiceren opheffen**. De link werkt dan direct niet meer.

---

## 8. Trello

Trello-kaarten met een vervaldatum verschijnen in Jarvis als deadlines; kaarten zonder datum als
taken. Kaarten in een lijst met een naam als "Done", "Klaar", "Afgerond", "Gereed", "Archief"
of "Completed" slaat Jarvis over, net als gearchiveerde kaarten en kaarten waarvan de
vervaldatum is afgevinkt.

Je hebt drie dingen nodig: een API-key, een token en het id van je bord.

**API-key en token**

1. Ga naar https://trello.com/power-ups/admin en log in.
2. Klik op **Nieuw** (*New*) om een Power-Up aan te maken. Vul in:
   - Naam: `Jarvis`
   - Workspace: de workspace waarin je bord staat
   - E-mail en overige velden: je eigen gegevens, de rest mag leeg
3. Open na het aanmaken het tabblad **API key** en klik op **Een nieuwe API-key genereren**
   (*Generate a new API key*). Kopieer de key: een reeks van 32 tekens.
4. Rechts van de key staat een link **Token**. Klik erop. Trello vraagt of "Jarvis" toegang
   mag tot je account; kies **Toestaan** (*Allow*). Kopieer het token dat verschijnt: een lange
   reeks van ongeveer 64 tekens.

Het token is standaard onbeperkt geldig en geeft leestoegang tot alle borden van je account.
Jarvis leest alleen het bord dat je opgeeft.

**Board-id**

Open je bord in de browser. De adresbalk ziet er zo uit:

```
https://trello.com/b/AbCd1234/duitenberg
```

Het board-id is het korte stuk tussen `/b/` en de volgende schuine streep, hier `AbCd1234`.
Alleen dat stuk, niet de naam erachter.

**In Jarvis**

Plak de drie waarden bij stap 6 in de velden API key, token en board-id. Klik op **Test**; je
ziet dan het aantal open kaarten. Klik op **Opslaan**.

**Intrekken:** ga naar https://trello.com/my/account, onder **Applicaties** (*Applications*)
kun je Jarvis verwijderen. Het token werkt dan niet meer.

---

## 9. Wekkers vanaf je Android-telefoon

Optioneel. Je telefoon stuurt de eerstvolgende wekker naar Jarvis, zodat het dashboard toont
hoe laat je morgen opstaat. Dit werkt met de gratis app **MacroDroid** of met Tasker. Het
principe: elke keer als je een wekker zet of wijzigt, doet je telefoon een klein webverzoek naar
je computer.

**Vereisten**

- Telefoon en computer zitten op hetzelfde wifi-netwerk (of zijn via Tailscale verbonden).
- Jarvis moet bereikbaar zijn vanaf het netwerk, niet alleen vanaf de computer zelf. De
  desktop-app en de startscripts (`start.sh`, `start.bat`) luisteren altijd alleen op
  `127.0.0.1`; daar kan je telefoon niet bij. Voor de wekkerkoppeling start je Jarvis daarom
  vanuit de broncode met uvicorn en een open host:

  ```bash
  .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
  ```

  Op Windows: `.venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000`. Gebruik je de
  systemd-service uit `scripts/dashboard.service`, pas daar dan de host aan.
- Je computer moet een vast lokaal IP-adres hebben of je moet het adres weten. Op Linux:
  `ip addr`, op Windows: `ipconfig`, op Mac: **Systeeminstellingen → Netwerk**. Het ziet er
  uit als `192.168.1.23`.
- Een firewall op de computer moet poort 8000 doorlaten voor het lokale netwerk.

**Stap 1: geheim instellen**

Verzin bij stap 7 in Jarvis een geheim (een willekeurig wachtwoord, bijvoorbeeld 20 tekens) en
klik op **Opslaan**. Zonder geheim weigert Jarvis alle wekkerberichten.

**Stap 2: MacroDroid instellen**

1. Installeer MacroDroid uit de Play Store en open de app.
2. Tik op **Macro toevoegen**.
3. **Trigger**: kies **Apparaatgebeurtenissen → Alarm** en dan **Alarm ingesteld/gewijzigd**
   (bij oudere versies "Volgende alarm gewijzigd").
4. **Actie**: kies **Connectiviteit → HTTP-verzoek**. Vul in:
   - Methode: `POST`
   - URL: `http://192.168.1.23:8000/api/alarms` (vervang het IP-adres door dat van jouw
     computer)
   - Onder **Headers** voeg je één header toe: naam `X-Dashboard-Secret`, waarde je geheim
     uit stap 1.
   - Content type: `application/json`
   - Body (kies "Tekst" of "Raw"):

     ```json
     {"app": "phone", "label": "Wekker", "at": "{alarm_time_ms}"}
     ```

     MacroDroid vervangt `{alarm_time_ms}` zelf door de tijd van de wekker.
5. Geef de macro een naam ("Jarvis wekker") en sla op.
6. Optioneel: maak een tweede macro met trigger **Alarm uitgezet** (*Alarm dismissed*) en
   dezelfde HTTP-actie, maar met als body `{"app": "phone", "at": ""}`. Jarvis haalt de wekker
   dan van het dashboard zodra hij is afgegaan.

**Stap 3: testen**

Zet een wekker op je telefoon. Binnen enkele seconden zou hij op het dashboard moeten staan in
het blok "Vandaag" of in de briefing. Zie je niets, controleer dan in MacroDroid het logboek
van de macro. De meest voorkomende foutcodes:

| Code | Betekenis |
|---|---|
| 401 | Het geheim klopt niet of ontbreekt. |
| 400 | De tijd is niet leesbaar. Controleer dat de body precies klopt. |
| Geen verbinding / time-out | IP-adres verkeerd, Jarvis luistert niet op `0.0.0.0`, of de firewall blokkeert. |

Vanaf de computer zelf kun je het endpoint testen met:

```bash
curl -X POST http://127.0.0.1:8000/api/alarms \
  -H "X-Dashboard-Secret: JOUW_GEHEIM" \
  -H "Content-Type: application/json" \
  -d '{"app":"phone","label":"Test","at":"2026-09-15T07:30:00"}'
```

Het veld `at` mag een tijd in milliseconden zijn of een ISO-tijd zoals hierboven. Meerdere
apparaten? Geef elk een eigen waarde voor `app` (bijvoorbeeld `"tablet"`).

---

## 10. Outlook mail en To Do via Microsoft Graph (geavanceerd)

Met deze koppeling toont Jarvis ook je ongelezen UT-mail, je Outlook-agenda (zonder de
vertraging van een gepubliceerde link) en je Microsoft To Do-taken. Hij vereist dat je zelf een
app registreert bij Microsoft en dat je organisatie toestaat dat gebruikers zelf apps
toestemming geven.

Eerlijke waarschuwing: veel universiteiten, waaronder mogelijk de UT, blokkeren dit. Je merkt
dat bij het inloggen aan de melding "Need admin approval" of "Beheerdersgoedkeuring vereist".
In dat geval gebruik je de agendalink uit hoofdstuk 7 en de eigen takenlijst van Jarvis; die
werken altijd. Deze koppeling is nog niet in de wizard opgenomen en gaat via het `.env`-bestand
en een script vanuit de broncode.

**Stap 1: app registreren**

1. Ga naar https://entra.microsoft.com en log in met je UT- of werkaccount.
2. Ga naar **Identity → Applications → App registrations** en klik op **New registration**.
3. Vul in:
   - Name: `Jarvis`
   - Supported account types: **Accounts in any organizational directory and personal
     Microsoft accounts**
   - Redirect URI: leeg laten
4. Klik op **Register**. Kopieer op de overzichtspagina de **Application (client) ID**.
5. Ga links naar **Authentication**. Scrol naar **Advanced settings → Allow public client
   flows** en zet die op **Yes**. Klik op **Save**.
6. Ga naar **API permissions → Add a permission → Microsoft Graph → Delegated permissions**.
   Vink aan: `Mail.Read`, `Calendars.Read` en `Tasks.Read`. Klik op **Add permissions**.

Krijg je bij stap 2 al geen toegang tot "App registrations"? Dan staat de organisatie het niet
toe en houdt het hier op.

**Stap 2: client-id invullen**

Zet in het `.env`-bestand (zie hoofdstuk 11):

```
MS_CLIENT_ID=de-application-client-id-uit-stap-1
```

**Stap 3: inloggen**

Draai vanuit de broncode:

```bash
.venv/bin/python scripts/ms_auth.py
```

Het script toont een code en een adres (https://microsoft.com/devicelogin). Open dat adres in je
browser, vul de code in en log in met je UT-account. Als alles goed gaat, meldt het script dat
het token is opgeslagen in `ms_token.json`. Herstart Jarvis; de bron "Outlook" verschijnt
bovenin.

Zie je "Need admin approval"? Dan blokkeert de organisatie het. Je kunt een verzoek indienen
bij de IT-afdeling, maar reken er niet op. Gebruik hoofdstuk 7.

---

## 11. Instellen via een .env-bestand (zonder wizard)

Alles wat je in de wizard invult, kun je ook in een tekstbestand zetten. Dat is handig als je
Jarvis op een server draait, je instellingen wilt back-uppen, of instellingen wilt gebruiken die
niet in de wizard staan (zoals `DASHBOARD_HOST` en `MS_CLIENT_ID`).

**Waar het bestand staat**

- Desktop-app: maak een bestand met de naam `.env` in de datamap uit hoofdstuk 2.
- Vanuit de broncode: kopieer `.env.example` naar `.env` in de projectmap.

**Volgorde van voorrang**

Wat je in de wizard opslaat, staat in de database en gaat vóór het `.env`-bestand. Het
`.env`-bestand gaat vóór de standaardwaarden. Heb je dus een waarde in de wizard opgeslagen en
zet je een andere in `.env`, dan wint de wizard. Maak het veld in de wizard leeg en sla op als
je wilt dat `.env` weer geldt.

**Voorbeeld**

```
TZ=Europe/Amsterdam
DASHBOARD_SECRET=een-lang-willekeurig-geheim

TIMEEDIT_ICS_URL=https://cloud.timeedit.net/nl_utwente/web/.../ri123.ics
CANVAS_ICS_URL=https://canvas.utwente.nl/feeds/calendars/user_abc.ics
OUTLOOK_ICS_URL=https://outlook.office365.com/owa/calendar/.../calendar.ics
GCAL_ICS_URL=

TRELLO_KEY=
TRELLO_TOKEN=
TRELLO_BOARD_ID=

CANVAS_BASE_URL=https://canvas.utwente.nl
CANVAS_TOKEN=

MS_CLIENT_ID=
```

Een lege waarde betekent: bron uit. Na het wijzigen van `.env` herstart je Jarvis. Het volledige
overzicht van alle sleutels staat in hoofdstuk 15.

---

## 12. Controleren of alles werkt

**Op het dashboard.** Bovenin staat per actieve bron een pil met een icoon, de naam en het
aantal items. Een groene pil met een getal betekent dat de laatste ophaalronde is gelukt. Een
rode pil met een uitroepteken betekent een fout; beweeg de muis erover voor de melding. Klik op
een pil om die bron nu te verversen.

**Op de instellingenpagina.** Naast elke kop staat dezelfde status. Gebruik de Test-knop om te
zien wat er precies wordt opgehaald.

**Via de API.** Ga naar `http://127.0.0.1:8000/api/status` voor een JSON-overzicht met per bron
de laatste ophaaltijd, het aantal items en een eventuele foutmelding.

**In het logbestand.** In de datamap staat `jarvis.log`. Daarin staat elke ophaalronde en elke
fout met de volledige melding. Dit is de eerste plek om te kijken als iets niet werkt.

---

## 13. Problemen oplossen

**"✗ HTTPStatusError: 401" of "403" bij een agendalink**
De link is verlopen of ingetrokken. Maak een nieuwe aan bij de bron (TimeEdit: opnieuw
abonneren; Google: privé-URL opnieuw instellen; Outlook: opnieuw publiceren) en plak die.

**"✗ HTTPStatusError: 404"**
De link is niet compleet gekopieerd of het board-id klopt niet. Controleer of de link eindigt
op `.ics` en of je bij Trello alleen het korte stuk na `/b/` hebt gebruikt.

**"⚠ verbinding werkt, maar 0 items gevonden"**
De koppeling is goed, er staat alleen niets in het tijdvenster. Voor roosters is dat gisteren
tot 30 dagen vooruit; voor deadlines twee weken terug tot 60 dagen vooruit. In de zomervakantie
is dit normaal. Bij Google: controleer dat je de juiste agenda hebt gekozen. Bij Outlook:
controleer dat je "Kan alle details bekijken" hebt gekozen bij het publiceren.

**"Google-token ongeldig; draai scripts/google_auth.py opnieuw"**
Het token is verlopen (na 7 dagen als het Google-project in testmodus staat) of je hebt de
toegang ingetrokken. Klik op **Verbinden met Google** in de wizard en log opnieuw in.

**"ontbreekt: …/google_credentials.json"**
Deze build heeft geen Google-credentials aan boord. Gebruik de agendalink (6b) of maak zelf een
bestand (6c).

**Google zegt "Deze app is geblokkeerd" of "Toegang geweigerd"**
Je e-mailadres staat niet bij de test users van het Google-project (zie 6c stap 4), of je
gebruikt een school- of werkaccount van Google waarvan de beheerder externe apps blokkeert.

**Dubbele items**
Je hebt dezelfde agenda twee keer gekoppeld, bijvoorbeeld TimeEdit rechtstreeks én via een
Google-agenda waarin je op TimeEdit bent geabonneerd. Kies er één. Canvas en Google Calendar
ontdubbelt Jarvis zelf zodra de API-variant actief is.

**Items staan een uur verkeerd**
Controleer de tijdzone. Standaard is dat `Europe/Amsterdam`; je kunt hem aanpassen met `TZ=` in
`.env`.

**De wekker van de telefoon komt niet aan**
Zie de tabel met foutcodes in hoofdstuk 9. Controleer in deze volgorde: geheim ingevuld en
opgeslagen, Jarvis gestart met uvicorn en `--host 0.0.0.0` (niet via de desktop-app of de
startscripts), juiste IP-adres, firewall, zelfde wifi.

**Trello-kaarten ontbreken**
Kaarten in een lijst die "Done", "Klaar", "Afgerond", "Gereed", "Archief" of "Completed" heet,
laat Jarvis bewust weg. Ook kaarten waarvan de vervaldatum is afgevinkt en gearchiveerde
kaarten worden niet getoond.

**Een bron blijft hangen op "! fout" na het oplossen**
Klik op de pil van die bron om direct te verversen, of wacht tot de volgende automatische
ronde.

**Alles opnieuw beginnen**
Sluit Jarvis, verwijder de datamap uit hoofdstuk 2 (of alleen `dashboard.sqlite3` als je de
tokens wilt houden) en start opnieuw. De wizard opent dan weer.

---

## 14. Privacy en veiligheid

- Jarvis stuurt niets naar een server van de makers. Alle gegevens gaan rechtstreeks tussen jouw
  computer en de bron (TimeEdit, Google, enzovoort).
- Alles wat je invult, staat in leesbare vorm in de datamap op je computer. Wie toegang heeft tot
  je gebruikersaccount, kan die bestanden lezen. Deel de datamap niet, en zet hem niet in een
  gedeelde cloudmap.
- Agendalinks zijn geheime adressen. Iedereen die de link heeft, kan je agenda lezen. Deel ze
  niet en trek ze in bij de bron als je twijfelt (zie de intrekstappen in elk hoofdstuk).
- Jarvis vraagt bij Google en Microsoft alleen leesrechten. Het kan geen mail versturen, geen
  afspraken maken en niets verwijderen.
- Het Trello-token geeft leestoegang tot al je borden, ook al gebruikt Jarvis er maar één.
  Verwijder het token in je Trello-account als je stopt met Jarvis.
- Jarvis luistert standaard alleen op `127.0.0.1`. Alleen als je de wekkerkoppeling wilt, start
  je hem met een open host voor het lokale netwerk. Doe dat niet op een openbaar wifi-netwerk. Het dashboard
  zelf heeft geen wachtwoord; iedereen op het netwerk kan het dan bekijken.
- Bij het verwijderen van Jarvis: verwijder de datamap en trek de tokens in bij Google, Trello
  en Microsoft.

---

## 15. Overzicht van alle instellingen

| Sleutel | Wizard-stap | Betekenis |
|---|---|---|
| `UNIVERSITY` | 1 | `utwente` of `other`. Bepaalt hulpteksten en standaardadressen. |
| `TIMEEDIT_ICS_URL` | 2 | Abonnementslink van je rooster. |
| `TIMEEDIT_WEB_URL` | 2 (automatisch) | Adres dat opent als je op een college klikt. |
| `CANVAS_ICS_URL` | 3 | Calendar Feed-link van Canvas. |
| `CANVAS_BASE_URL` | 3, geavanceerd | Adres van je Canvas, zonder slash aan het eind. |
| `CANVAS_TOKEN` | 3, geavanceerd | Persoonlijk toegangstoken van Canvas. |
| `GCAL_ICS_URL` | 4, alternatief | Privéadres in iCal-formaat van één Google-agenda. |
| `GOOGLE_CREDENTIALS_FILE` | alleen `.env` | Pad naar het OAuth-clientbestand. Standaard `google_credentials.json` in de datamap. |
| `GOOGLE_TOKEN_FILE` | alleen `.env` | Waar het Google-token wordt bewaard. Standaard `google_token.json` in de datamap. |
| `OUTLOOK_ICS_URL` | 5 | ICS-link van een gepubliceerde Outlook-agenda. |
| `TRELLO_KEY` | 6 | Trello API-key. |
| `TRELLO_TOKEN` | 6 | Trello-token. |
| `TRELLO_BOARD_ID` | 6 | Korte code na `trello.com/b/`. |
| `DASHBOARD_SECRET` | 7 | Geheim voor wekkerberichten vanaf je telefoon. |
| `MS_CLIENT_ID` | alleen `.env` | Application (client) ID van je Entra-app. |
| `MS_TOKEN_FILE` | alleen `.env` | Waar het Microsoft-token wordt bewaard. Standaard `ms_token.json` in de datamap. |
| `DASHBOARD_HOST` | alleen `.env` | Gewenste host. Let op: de desktop-app en de startscripts negeren dit en gebruiken altijd `127.0.0.1`; geef bij uvicorn `--host` mee. |
| `DASHBOARD_PORT` | alleen `.env` | Poortnummer, standaard 8000. De desktop-app kiest zelf een vrije poort tenzij deze variabele in de systeemomgeving staat. |
| `TZ` | alleen `.env` | Tijdzone, standaard `Europe/Amsterdam`. |
| `SETUP_DONE` | knop "Klaar" | Zet de wizard uit bij het starten. |

Namen van de bronnen zoals ze in `/api/status` en bij de Test-knop heten:

| Naam | Bron |
|---|---|
| `timeedit` | TimeEdit-rooster |
| `canvas_ics` | Canvas via agendalink |
| `canvas` | Canvas via API |
| `gcal_ics` | Google Agenda via agendalink |
| `gcal` | Google Calendar via API |
| `gmail` | Gmail |
| `outlook_ics` | Outlook-agenda via gepubliceerde link |
| `outlook` | Outlook via Microsoft Graph |
| `trello` | Trello |
