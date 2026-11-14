# Je productiviteitstool online zetten (stap voor stap)

Je hebt hier niets van programmeren voor nodig. Je gaat drie dingen doen:
**A.** een database maken (hier worden je taken bewaard),
**B.** de app online zetten,
**C.** hem op je telefoon zetten.

Het kost niets en duurt ongeveer 20 minuten.

---

## A. De database maken (Supabase)

1. Ga naar **supabase.com** en klik op *Start your project*. Log in met je GitHub-account.
2. Klik op *New project*. Kies een naam (bijv. `productiviteit`), bedenk een databasewachtwoord
   (bewaar dat in je wachtwoordmanager, je hebt het zelf niet meer nodig) en kies als regio
   *West EU (Ireland)* of *Frankfurt*. Klik op *Create project* en wacht een minuutje.
3. Klik links op **SQL Editor** → *New query*.
4. Open het bestand `supabase_tabel.sql` uit deze repository, kopieer alles, plak het in het
   vak en klik op **Run**. Je ziet *Success*. Je tabel staat nu klaar.
5. Haal twee gegevens op, die heb je zo nodig:
   - Klik links op **Project Settings** (tandwiel) → **API Keys**.
   - **Project URL** staat bovenaan (iets als `https://abcd1234.supabase.co`).
   - Kopieer de **secret key** (ook wel `service_role` genoemd). Dit is een geheime sleutel:
     deel hem met niemand en zet hem nergens openbaar.

## B. De app online zetten (Streamlit Community Cloud)

1. Ga naar **share.streamlit.io** en log in met GitHub.
2. Klik op *Create app* → *Deploy a public app from GitHub*.
3. Vul in:
   - Repository: `Nonimus666/blank-app`
   - Branch: `claude/weekly-productivity-tracker-sdbz1o`
     (of `main`, als je de wijzigingen daar hebt samengevoegd)
   - Main file path: `streamlit_app.py`
4. Klik op **Advanced settings** → vak **Secrets**. Plak dit en vul je eigen gegevens in:

   ```
   app_password = "kies-een-lang-wachtwoord"

   [supabase]
   url = "https://JOUWPROJECT.supabase.co"
   key = "JOUW-GEHEIME-SLEUTEL"
   ```
5. Klik op **Deploy**. Na een paar minuten krijg je een link zoals
   `https://jouwnaam.streamlit.app`. Dat is jouw app.

Bij het openen vraagt de app om je wachtwoord. Daarna zie je je weekoverzicht.

## C. Op je telefoon en pc zetten

- **iPhone (Safari):** open de link → deel-knop → *Zet op beginscherm*.
- **Android (Chrome):** open de link → menu (drie puntjes) → *Toevoegen aan startscherm*.
- **Pc (Chrome of Edge):** open de link en maak een bladwijzer, of kies in het menu
  *Opslaan en delen* → *Installeren / Snelkoppeling maken*.

---

## Goed om te weten

- **Je data blijft bewaard.** Alles staat in Supabase, dus een nieuwe sessie, een andere
  telefoon of een herstart van de app verandert niets.
- **Eerste keer openen duurt even.** Als je de app een tijd niet gebruikt, gaat hij op de
  gratis versie in slaapstand. Klik dan op *Yes, get this app back up* en wacht een paar seconden.
- **Supabase pauzeert gratis projecten na ongeveer een week zonder gebruik.** Je data blijft
  bestaan; je kunt het project in Supabase met één klik weer aanzetten.
- **Lokaal testen** blijft kunnen met `streamlit run streamlit_app.py`. Zonder instellingen
  gebruikt de app dan een bestandje `tasks.json` op je eigen pc.
