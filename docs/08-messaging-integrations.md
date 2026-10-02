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
| **Staff post** | Staff dashboard form | — | Yes | Official |
| **Manual paste** | A form: paste one or more messages and choose the group they came from | — | — | Normal |
| **WhatsApp chat export** | Upload the `.txt` file from WhatsApp's own "Export chat" | Yes (a WhatsApp feature) | No | Normal |

Trust is stored on the `Source` and affects importance, never who is allowed to change a timetable: timetable changes always need the student's confirmation.

## Connecting a group (students)

1. The student opens **Sources → Connect a group** and pastes the group's invite link (`https://chat.whatsapp.com/…` or `https://t.me/…`).
2. The student chooses what the group is for (for example "CDE2313 Section A", "SCI 2024 October intake", "University announcements"). This sets the source's **scope**, which helps the AI resolve who is affected.
3. **WhatsApp:** the connector joins through the invite link. **Telegram:** the student is shown how to ask the group admin to add the UniFlow bot (a bot cannot join by link).
4. The connector posts the notice from principle 4.
5. An admin can review new sources, fix their scope, or disconnect them.

A group that is already connected is not joined twice; the student is simply linked to it (`SourceSubscription`), which also counts as a relevance signal.

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

- A **separate small process** (`connectors/whatsapp/`, outside Django), because WhatsApp libraries keep a long-lived connection. Candidate libraries: Baileys (Node.js) or whatsmeow through neonize (Python). **The library is chosen and approved in the connector task** (see [11](11-roadmap.md)).
- It does three things: join a group from an invite link, receive new group messages, and send each message to the backend.
- It sends messages to `POST /api/v1/internal/messages/`, signed with a shared secret (`CONNECTOR_SECRET`). It has no database of its own.
- It is run as a systemd service next to Django ([10](10-testing-and-deployment.md)).

## The Telegram bot

- One UniFlow bot, created through @BotFather, using the official Bot API.
- Updates arrive at `POST /api/v1/integrations/telegram/webhook/`, checked with Telegram's `secret_token` header. No separate process is needed.
- **Groups:** a group admin adds the bot; privacy mode must be off (or the bot made admin) so it receives all messages. **Channels:** the bot is added as a channel admin and receives `channel_post` updates.
- A bot only receives messages sent **after** it joins. Earlier history can be added with a manual chat export where available.
- Docs: https://core.telegram.org/bots/api and https://core.telegram.org/bots/features#privacy-mode

## Staff posts

Staff with the matching capability post official information in the staff dashboard (the `announcements` app, built on the `publishing` base from M2.6 and the school boundary from M2.7). When published, a staff post becomes an insight directly: staff already supply the kind, audience and importance, so no AI extraction is needed. It then goes through the same delivery and notification steps as every other insight.

## Manual paste and chat-export upload

- **Paste:** a form where a student or staff member pastes messages and chooses the source. Useful before the connectors exist, and for groups the connectors can't reach.
- **Chat export:** WhatsApp's "Export chat" produces a `.txt` file. UniFlow parses it into `Message` rows (sender, time, text) for the chosen source. Only messages newer than the last one already stored are processed.

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
