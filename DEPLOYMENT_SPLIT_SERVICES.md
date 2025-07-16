# MR HUX Alpha Bot - Bot-Only Deployment Guide (Render Free Tier)

## Overview

If you only care about the Telegram bot (and not the web dashboard), you can run the bot on Render’s free web service slot. This is the simplest and free way to keep your bot running.

---

## Render Free Tier Bot-Only Deployment (Step-by-Step)

1. **Go to [Render.com](https://render.com/)** and log in.
2. Click **“New Web Service”**.
3. Connect your GitLab repository.
4. Set the **start command** to:
   ```
   python bot.py
   ```
5. Set your environment variables:
   - `BOT_TOKEN` (Telegram bot token)
   - `TELEGRAM_API_ID` (Telegram API ID)
   - `TELEGRAM_API_HASH` (Telegram API hash)
   - Any other required variables (see your .env or settings)
6. Click **“Create Web Service”** and deploy.
7. **Ignore any warnings** about no open ports detected. The bot will still run!
8. Check the logs to confirm the bot is running and connected to Telegram.

---

## What to Expect
- The bot will run and monitor Telegram as long as the Render free web service is active.
- The web dashboard will NOT be available.
- You may see warnings about no open ports—this is normal for a bot-only service.
- The service may spin down after inactivity (free tier limitation).

---

## Troubleshooting
- If the bot stops, just restart the service from the Render dashboard.
- If you need 24/7 uptime, consider running the bot on your own computer, a Raspberry Pi, or a paid plan.

---

## Example Environment Variables
```
BOT_TOKEN=your_bot_token_here
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here
DATABASE_URL=sqlite:///mr_hux_alpha_bot.db
LOG_LEVEL=INFO
ENV=production
```

---

## Summary Table
| Platform      | Web Dashboard | Bot (Background Worker) | Free Tier?         |
|---------------|--------------|-------------------------|--------------------|
| Render        | No           | Yes (as web service)    | 1 web service only |
| Railway       | Yes          | Yes (limited)           | Usage limits apply |
| Fly.io        | Yes          | Yes (limited)           | Usage limits apply |
| Local         | Yes (dev)    | Yes                     | Always free        |

---

**You’re all set! Just follow the checklist above and your Telegram bot will run for free on Render.** 