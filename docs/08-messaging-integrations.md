# 08 — WhatsApp & Telegram Integration Strategy

## Principle

UniFlow **must work fully without any messaging integration.** Integrations are optional feeders that save time. The system never depends on them. **No scraping, no unofficial clients, no personal-account automation.**

> Platform capabilities change. Re-check the official documentation for both platforms (links below) before starting the Telegram work (post-MVP).

## What is officially possible

### Telegram — the most integrable

| Capability | Official? | Notes |
|---|---|---|
| Deep links to public groups and channels | ✔ | `https://t.me/<username>` |
| Invite links to private groups and channels | ✔ | `https://t.me/+<hash>`. The group admin creates these. |
| A **bot** reads posts in a **channel** | ✔ | The bot must be **added as an admin** of the channel. It then receives `channel_post` and `edited_channel_post` updates. |
| A bot reads messages in a **group** | ✔, with limits | With *privacy mode* on (the default), the bot only receives commands, replies to itself and mentions. To see all messages, turn privacy mode off through @BotFather or make the bot a group admin. Group members must be told about the bot. |
| A bot reads history from **before** it joined | ✘ | Bots receive only new updates. |
| A bot **posts** into a channel or group | ✔ | `sendMessage` or `sendDocument` wherever it is an admin or member. This allows **outbound** broadcasting from UniFlow. |
| Receiving updates | ✔ | A webhook (`setWebhook` with `secret_token`) or `getUpdates` polling. |
| Reading groups the university does not control | ✘ | Only an admin of the group can add the bot. |

Docs: https://core.telegram.org/bots/api and https://core.telegram.org/bots/features#privacy-mode

### WhatsApp — deliberately restricted

| Capability | Official? | Notes |
|---|---|---|
| Deep link to a group invite | ✔ | `https://chat.whatsapp.com/<code>` |
| Deep link to a **channel** | ✔ | `https://whatsapp.com/channel/<id>` |
| Click-to-chat with a business or person | ✔ | `https://wa.me/<number>?text=...` |
| Reading messages from ordinary WhatsApp **groups or channels** | ✘ | There is no official API. Tools that do this (for example whatsapp-web.js or Baileys) automate the WhatsApp Web client, which breaks WhatsApp's terms and risks bans. **Not allowed in UniFlow.** |
| **WhatsApp Business Platform (Cloud API)** | ✔ | This is 1:1 messaging between a verified business number and users who **opted in**. Outbound messages outside the 24-hour customer-service window must use **pre-approved templates** and are **charged per message**. It needs a Meta Business account, business verification and a dedicated phone number. |
| Business group features | Limited | Meta has been adding limited group features for business-created groups on the Cloud API. They **do not** give access to existing student-run groups. Check the current status before relying on them. |

Docs: https://developers.facebook.com/docs/whatsapp and https://faq.whatsapp.com/5913398998672934 (click-to-chat)

## Strategy by phase

### MVP (M0–M10): links and manual publishing

1. **Community directory with verified links.** `CommunityLink` rows store the URLs. On save, the backend validates that each URL's host matches its platform:

   | Platform | Allowed hosts |
   |---|---|
   | `whatsapp_group` | `chat.whatsapp.com` |
   | `whatsapp_channel` | `whatsapp.com/channel/`, `www.whatsapp.com/channel/` |
   | `telegram_*` | `t.me`, `telegram.me` |

   This stops look-alike phishing links.
2. **Source attribution.** Every announcement or event can carry `source_platform` and `source_url`, and the UI shows "Originally posted in: Robotics Club Telegram →". Students can jump to the discussion, and UniFlow does not try to host it.
3. **Manual publishing, made fast.** Publishers paste the text of a WhatsApp or Telegram post into the announcement form in the **staff dashboard**. The form keeps line breaks and turns URLs into links. The source URL field is right there. This is the whole integration in the MVP, and it works for every source.
4. **Links pointing outward.** Each announcement's share action copies a UniFlow link (`/announcements/214`). When publishers post that link in WhatsApp, the groups send traffic into UniFlow.

### [Later] Telegram bot, inbound

- The university and each club register a channel with one UniFlow bot and add it as a channel admin.
- `TelegramSource(chat_id, title, community FK / department FK, default_category, is_active)` maps chats to publishers.
- The webhook stores each post as an `InboxItem(source, raw_text, attachments, message_link, received_at, status)`.
- **Nothing auto-publishes.** A publisher for that community reviews the inbox, clicks "Convert to announcement or event", chooses an audience and publishes. The Telegram message link fills `source_url` automatically.
- Media: the backend fetches files with `getFile` and stores them as `Document`s.

### [Later] Telegram bot, outbound (optional)

- When an announcement is published, UniFlow can optionally post a short summary and link into a linked Telegram channel. The publisher chooses this with a checkbox.

### WhatsApp: later, and only if justified

- **Outbound only**, through the Cloud API, for opt-in students (for example "urgent announcements to my WhatsApp"). This needs a business number, approved templates, per-message cost and a consent flow. It should be evaluated only after the mobile push notifications exist, because push is free and covers the same need.
- **Inbound from WhatsApp will stay manual.** No official mechanism exists for community groups.

## Risks

| Risk | Mitigation |
|---|---|
| A club's link is revoked or rotated | Managers edit their links. A "Report broken link" action notifies the managers. |
| A bot in a group reads private discussion | Use channels only for inbound (post-MVP), and do not ingest group chat. Group chat is conversation, not announcements. |
| Phishing through community links | Host validation, a verified badge for admin-approved communities, and `rel="noopener noreferrer"` on links. |
