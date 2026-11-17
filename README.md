# RUPAYAN AI BOT — 3D Fire Edition

A Telegram bot starter with a fire-themed welcome message, profile, credits,
basic admin statistics, and SQLite storage.

## Files
- `main.py` — bot source
- `requirements.txt` — Python dependency
- `.env.example` — environment variable template

## Important token safety
The Telegram bot token previously pasted into chat should be considered exposed.
Revoke it with @BotFather (`/revoke`) and create a new token. Put only the NEW
token into Render Environment Variables. Do not put it in `main.py` or GitHub.

## GitHub files
Upload `main.py` and `requirements.txt` to the root of your repository.
`.env.example` is a template only; do not put real secrets in it.

## Render Background Worker
- Runtime / Language: Python 3
- Build Command: `pip install -r requirements.txt`
- Start Command: `python main.py`

Environment Variables:
- `BOT_TOKEN`: your newly generated BotFather token
- `ADMIN_IDS`: your Telegram numeric user ID (comma-separated if multiple)
- `DB_PATH`: optional path on a mounted persistent disk, e.g. `/var/data/bot_database.db`

## Notes
- The welcome uses Telegram HTML text and emoji. It is not a full-screen phone
  animation; a true animated effect would require sending an animation GIF.
- Render Background Workers are not necessarily available on a free always-on
  basis. Check current plan limits before relying on 24/7 operation.
- SQLite data on an ephemeral filesystem may be lost when the service is
  replaced or redeployed. Use a persistent disk or managed database if you
  need durable user records.
- This starter intentionally does not perform phone-number lookups or retrieve
  private personal records about other people.
