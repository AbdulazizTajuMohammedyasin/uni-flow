# UniFlow WhatsApp connector

A small Node.js program that runs **UniFlow's own WhatsApp number** (docs/08). It joins the
groups students add in UniFlow, posts one notice saying what UniFlow does, and forwards new
group messages and their files (photos, PDFs, Excel) to the backend's private, signed
addresses (`/api/v1/internal/`). It ignores private chats and sends nothing else.

It uses [Baileys](https://github.com/WhiskeySockets/Baileys) (approved before M6.3), an
**unofficial** WhatsApp library: WhatsApp may ban the number. Use a dedicated SIM.

## Run it

Needs Node.js 24, and the backend running with the same `CONNECTOR_SECRET`.

```powershell
cd connectors/whatsapp
npm ci
Copy-Item .env.example .env   # then fill in CONNECTOR_SECRET and WHATSAPP_NUMBER
npm start
```

**First time only (login):** the connector prints a **pairing code**. On the UniFlow phone:
WhatsApp → Linked devices → Link a device → *Link with phone number instead* → type the
code. The session is saved in `auth/` (never commit or share it). To log in again, stop
the connector, delete `auth/`, and start it.

## Try it

1. In the Django admin, add a **Source**: platform *WhatsApp group*, status *Waiting to
   join*, and the group's invite link (`https://chat.whatsapp.com/…`).
2. Within a few minutes the connector joins it, posts the notice, and the source becomes
   *Active*. If the group needs admin approval, it waits until an admin accepts.
3. Send a message in the group: it appears under Intelligence → Messages and is sorted by
   the AI (with Redis and the Celery worker running).
4. Stop the connector, send a message, start it again: the missed message arrives once.

## If linking fails ("Couldn't link device")

- The phone must be logged in to WhatsApp **with the number in `.env`**.
- Type the code within a minute; only one code is printed per start.
- Before each new try: stop the connector, delete `auth/`, start again.
- Known Baileys problem (October 2026): since late July WhatsApp sends a new linking
  step (`companion_reg_refresh`) that Baileys 7.0.0-rc14 doesn't handle yet
  ([Baileys #2737](https://github.com/WhiskeySockets/Baileys/issues/2737)). If linking
  still fails, update Baileys once a release fixes it, or apply the fix as a patch
  (needs approval: see docs/PROGRESS.md, Open decisions).

## Tests

```powershell
npm test
```
