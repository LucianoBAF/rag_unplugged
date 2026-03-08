# Channel Setup

## Telegram

### 1. Create a bot

1. Open Telegram, search for **@BotFather**
2. Send `/newbot`, follow the prompts
3. Copy the token (looks like `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### 2. Configure

Set the token in `.env`:
```
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
```

### 3. Run

The bot starts automatically with `docker compose up`. It uses **polling** —
no need to expose ports or configure webhooks.

### Commands

| Command | Action |
|---------|--------|
| `/reset` | Clears conversation history for your session |

---

## WhatsApp (via WAHA)

> **Warning**: WhatsApp does not officially support bots. WAHA uses reverse-
> engineered protocols. There is a risk of account ban. Use a secondary
> phone number.

### 1. Start WAHA

WAHA starts automatically as part of `docker compose up`.

### 2. Pair your phone

1. Open `http://localhost:3000/` (WAHA dashboard)
2. Start the default session
3. Scan the QR code with WhatsApp on your phone

### 3. Configure the webhook

Tell WAHA to forward messages to the app. Via the dashboard or API:

```bash
curl -X PUT http://localhost:3000/api/sessions/default \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "webhooks": [{
        "url": "http://app:8080/webhook/whatsapp",
        "events": ["message"]
      }]
    }
  }'
```

### 4. Test

Send a WhatsApp message to the paired number — you should get a reply.

### Troubleshooting

- **QR code not appearing**: Restart WAHA (`docker compose restart waha`)
- **Messages not forwarded**: Check the webhook URL uses the Docker service
  name (`app`), not `localhost`
- **Session lost**: Re-scan the QR code. WAHA persists sessions across restarts
  if you mount a volume (not configured by default — add a volume to the WAHA
  service in `docker-compose.yml` if needed)
