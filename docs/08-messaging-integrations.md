# 08 — Sources & Connectors (WhatsApp, Telegram, staff, manual)

Messaging platforms are UniFlow's **primary information sources**. This document covers how messages get *in*. What happens to them next is in [12-intelligence.md](12-intelligence.md).

## Principles

1. **Academic groups only.** UniFlow connects programme, intake, course, section, school and university groups and channels. Marketplace, rental, social and entertainment groups are refused.
2. **Groups and channels only, never personal chats.**
3. **Connected once, shared by everyone.** When one student connects a group, every student in it benefits.
4. **People in the group are told.** When the UniFlow account joins a group, it posts one short notice explaining what it does and how to remove it.
5. **Connectors are thin and replaceable.** A connector only delivers messages to the backend. All understanding happens in the backend, so a connector can be swapped (for example for an official API) without touching anything else.

## Source types

| Source | Mechanism | Official? | Real time | Trust |
|---|---|---|---|---|
| **WhatsApp group** | The UniFlow WhatsApp connector (a dedicated UniFlow number) | **No**, see below | Yes | Normal |
| **Telegram group** | The UniFlow bot, added by a group admin, privacy mode off | Yes (Bot API) | Yes | Normal |
| **Telegram channel** | The UniFlow bot, added as a channel admin | Yes (Bot API) | Yes | Normal, or Official for university channels |
| **Staff post** | The Django admin in the pilot; a staff form later | — | Yes | Official |
| **Manual paste** | A form: paste one or more messages and choose the group they came from | — | — | Normal |
| **WhatsApp chat export** | Upload the `.txt` file from WhatsApp's own "Export chat" | Yes (a WhatsApp feature) | No | Normal |
| **Timetable file or link** | A student uploads a timetable image, PDF or spreadsheet, or pastes a Google Drive link, on the Timetable page | — | — | Normal |

Trust is stored on the `Source` and affects importance, never who is allowed to change a timetable: timetable changes always need the student's confirmation.

## Connecting a group (students)

1. The student opens **Sources → Add a group** and pastes the group's invite link (`https://chat.whatsapp.com/…` or `https://t.me/…`). Students never give UniFlow their phone number or access to their WhatsApp; their registered `@student.aiu.edu.my` email is the only verification.
2. The student chooses what the group is for (for example "CDE2313 Section A", "SCI 2024 October intake", "University announcements"). This is a **suggested scope**: it becomes confirmed when messages in the group or the students who added it match it, or when an admin confirms it. Until then it only lightly affects who is reached.
3. **WhatsApp:** in the background, the connector (UniFlow's own number) joins through the invite link. If the group requires admin approval, the source stays **pending** until the group's admin accepts the UniFlow number. Many groups only let admins share the link; then the student asks the group admin to connect it. **Telegram:** the student is shown how to ask the group admin to add the UniFlow bot (a bot cannot join by link).
4. The connector posts the notice from principle 4.
5. An admin can review new sources, fix their scope, or disconnect them.

A group that is already connected is not joined again; the student is simply added to its members.

## Who is in each group

UniFlow knows a group's members from the **students who added that group in the app** (`SourceMember`). It does not read WhatsApp's member list and never asks students for their phone numbers. Every student who adds a group they are in helps UniFlow tell who a message affects and who "Abdulaziz" is, so the app encourages students to add all their academic groups.

## The WhatsApp connector

### Decision and honest risks

WhatsApp has **no official API for reading groups**. The developer has chosen to build an **unofficial connector** anyway, because WhatsApp groups are where most academic information at AIU is posted. The risks are recorded here so the decision stays visible:

| Risk | What it means |
|---|---|
| **WhatsApp's terms** | Automating a normal WhatsApp account breaks WhatsApp's terms of service. |
| **The number can be banned at any time** | WhatsApp detects automation. A ban stops all WhatsApp input until a new number is set up and re-added to every group. |
| **Breaking changes** | Unofficial libraries break when WhatsApp changes its web protocol; fixes can take days. |
| **Consent** | Every member's messages are read, not just the student who connected the group. |
| **University approval** | The university may object. Its approval should be obtained before launch. |

### Safeguards

- A **dedicated number** owned by the project, never a student's personal number.
- **Read-only behaviour:** the connector sends nothing except the one join notice. No bulk messaging, no replies.
- Joins only through invite links students submit, at a slow rate.
- The join notice explains what UniFlow reads, and that a group admin can simply remove the number.
- Only academic groups; admins can disconnect any source.
- Raw message text is deleted after the retention period ([09](09-security.md)).
- **Everything else keeps working if WhatsApp input stops:** Telegram, staff posts, manual paste and chat-export upload.
- Because the connector is isolated, it can be replaced by an official route if one becomes available.

### How it is built

- A **separate small process** (`connectors/whatsapp/`, outside Django), because WhatsApp libraries keep a long-lived connection. The library is **Baileys** (Node.js), approved in M6.3; neonize (Python) was the alternative.
- It does three things: join a group from an invite link, receive new group messages (with image, PDF and spreadsheet attachments), and send them to the backend. It ignores private messages and never reads members' phone numbers.
- It sends messages to `POST /api/v1/internal/messages/`, signed with a shared secret (`CONNECTOR_SECRET`). It has no database of its own.
- **Built so far (M6.2):** the Django side, `apps/intelligence/connector.py` (addresses and signing in [04](04-api.md)). The connector asks for groups to join, reports each join (and whether the notice was sent), sends each message once with a sender id that UniFlow hashes again (so a phone number is never stored), then uploads any files. The connector program itself is M6.3.
- **Built (M6.3):** `connectors/whatsapp/` (`src/index.js` WhatsApp side, `src/messages.js` message conversion and the join notice, `src/uniflow.js` signed requests; setup in its `README.md`). It logs in once with a **pairing code** (session in the git-ignored `auth/` folder), asks for groups to join every 5 minutes and joins **one per round** (each link at most once an hour), posts the notice, reports the join, forwards messages and then their files, stays "offline", and ignores private chats, status updates and its own messages. After a restart WhatsApp delivers what was missed and the backend stores each message once.
- **Known issue (October 2026):** Baileys 7.0.0-rc14 can fail to link ("Couldn't link device"). Its built-in WhatsApp Web version is out of date (fixed: the connector fetches the current one), and since late July 2026 WhatsApp sends a `companion_reg_refresh` step Baileys doesn't handle yet ([Baileys #2737](https://github.com/WhiskeySockets/Baileys/issues/2737); unreleased fix). If linking still fails, either wait for the next Baileys release or apply that fix as a patch (needs approval).
- It is run as a systemd service next to Django ([10](10-testing-and-deployment.md)).

## The Telegram bot

- One UniFlow bot, created through @BotFather, using the official Bot API.
- Updates arrive at `POST /api/v1/integrations/telegram/webhook/`, checked with Telegram's `secret_token` header. No separate process is needed.
- **Groups:** the bot does **not** need to be an admin. Turn privacy mode off once in @BotFather (`/setprivacy` → Disable) and it sees every message as a normal member. The setting only applies to groups the bot joins afterwards, so remove and re-add it in older groups. Someone in the group must add it (a bot can't join by invite link); some groups only let admins add members. **Channels:** Telegram only allows bots in a channel as admins, but every admin permission can be switched off (read-only). It receives `channel_post` updates.
- *Considered:* a normal Telegram user account run by a program ("userbot") could join by invite link without anyone adding it, but it needs its own phone number and a new library, and can be banned like the WhatsApp number. Kept as an option if many group admins refuse to add the bot.
- A bot only receives messages sent **after** it joins. Earlier history can be added with a manual chat export where available.
- Docs: https://core.telegram.org/bots/api and https://core.telegram.org/bots/features#privacy-mode
- **Built (M6.1):** `apps/intelligence/telegram.py`. The first message (or the bot being added) creates the group's `Source` (active); removing the bot marks it disconnected and its messages are then ignored. Each message is stored once (Telegram's message id), with the sender's name and a hash of their Telegram id, its reply, and its text or caption; joins, stickers and private chats are ignored. A photo, PDF or Excel file is downloaded in the background (`getFile`, checked by real contents, same size limit as uploads) before the AI sorts the message. Edited messages are not used yet.
- **Setting it up:** create the bot with @BotFather; put `TELEGRAM_BOT_TOKEN` and a random `TELEGRAM_WEBHOOK_SECRET` in `backend/.env`; turn privacy mode off (`/setprivacy` → Disable); then, where UniFlow is online over https, run `pipenv run python manage.py set_telegram_webhook https://<site>` (`--info` shows the state, `--delete` stops it). Telegram can't reach a laptop without a public https address.

## Staff posts

A staff post is an `Insight` with `origin = staff` (built on the `publishing` base from M2.6, with the school boundary from M2.7). Staff supply the kind, title, summary, importance and audience, so no AI extraction is needed. Publishing it delivers it through the same steps as every other insight. In the pilot staff posts are created in the Django admin; a staff form comes later.

## Manual paste and chat-export upload

- **Paste:** a form where a student or staff member pastes messages and chooses the source. Useful before the connectors exist, and for groups the connectors can't reach.
- **Chat export:** WhatsApp's "Export chat" produces a `.txt` file. UniFlow parses it into `Message` rows (sender, time, text) for the chosen source. Only messages newer than the last one already stored are processed.

## Timetable files and Google Drive links

- Images, PDFs and spreadsheets attached to messages in connected groups are kept as `MessageFile` rows (WhatsApp: downloaded by the connector; Telegram: fetched with `getFile`).
- Google Drive links in messages, or pasted by a student, are fetched only if public, from `drive.google.com` or `docs.google.com` only, as PDF or XLSX.
- **Links that only open with an AIU account** (common for school timetables) can't be fetched by the server. The student opens the link, chooses File → Download → Microsoft Excel (.xlsx), and uploads the file; UniFlow says so when a link fails. *[Later]*: "Connect your Google account" so UniFlow can download with the student's permission (needs Google's app review).
- The AI decides whether a file is a timetable; if so, it is read into classes for students to confirm ([12](12-intelligence.md#reading-timetables)).

## Linking back to the original

| Platform | What "open original" does |
|---|---|
| Telegram channel | Opens the exact post (`https://t.me/<channel>/<message_id>`) |
| Telegram group | Opens the message for members (`https://t.me/c/<id>/<message_id>`) |
| WhatsApp | WhatsApp has no per-message links. UniFlow shows the original message text, sender and time inside UniFlow, and a button to open the group. |
| Staff post | The post itself |

## Risks

| Risk | Mitigation |
|---|---|
| WhatsApp number banned | Other sources keep working; a replacement number can be registered; the connector is isolated |
| A non-academic or private group is connected | Admin review of new sources; academic-only rule; disconnect button |
| Someone connects a group to spy on it | The join notice tells members; group admins can remove the account; admins can disconnect |
| Fake or phishing invite links | Host validation (`chat.whatsapp.com`, `t.me`, `telegram.me`) |
| Forged messages to the internal endpoint | Signed requests with `CONNECTOR_SECRET`; the endpoint is not reachable from outside the server |
