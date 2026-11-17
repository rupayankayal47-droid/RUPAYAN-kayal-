import os
import html
import logging
import sqlite3
from datetime import datetime, timezone

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_IDS = {
    int(value.strip())
    for value in os.getenv("ADMIN_IDS", "").split(",")
    if value.strip().isdigit()
}
DB_PATH = os.getenv("DB_PATH", "bot_database.db")
INITIAL_CREDITS = 10

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("rupayan-ai-bot")


def connect_db():
    return sqlite3.connect(DB_PATH, timeout=30)


def init_db():
    with connect_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                credits INTEGER NOT NULL DEFAULT 10,
                joined_at TEXT NOT NULL
            )
        """)
        conn.commit()


def register_user(user):
    with connect_db() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO users
                (user_id, username, first_name, credits, joined_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            user.id,
            user.username or "",
            user.first_name or "User",
            INITIAL_CREDITS,
            datetime.now(timezone.utc).isoformat(),
        ))
        # Keep profile details current without resetting credits.
        conn.execute("""
            UPDATE users SET username = ?, first_name = ?
            WHERE user_id = ?
        """, (user.username or "", user.first_name or "User", user.id))
        conn.commit()


def get_user(user_id):
    with connect_db() as conn:
        return conn.execute(
            "SELECT user_id, username, first_name, credits, joined_at "
            "FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()


def add_credits(user_id, amount):
    with connect_db() as conn:
        cur = conn.execute(
            "UPDATE users SET credits = credits + ? WHERE user_id = ?",
            (amount, user_id),
        )
        conn.commit()
        return cur.rowcount > 0


def user_count():
    with connect_db() as conn:
        return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]


def total_credits():
    with connect_db() as conn:
        return conn.execute(
            "SELECT COALESCE(SUM(credits), 0) FROM users"
        ).fetchone()[0]


def is_admin(user_id):
    return user_id in ADMIN_IDS


def main_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👤 PROFILE", callback_data="profile"),
            InlineKeyboardButton("💎 CREDITS", callback_data="credits"),
        ],
        [
            InlineKeyboardButton("⚡ HELP", callback_data="help"),
            InlineKeyboardButton("🔥 ABOUT", callback_data="about"),
        ],
    ])


def admin_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 BOT STATISTICS", callback_data="admin_stats")],
        [InlineKeyboardButton("🏠 MAIN MENU", callback_data="home")],
    ])


WELCOME = (
    "🔥⚡🔥⚡🔥⚡🔥⚡🔥\n\n"
    "<b>RUPAYAN AI BOT</b>\n"
    "<b>✨ WELCOME TO THE SYSTEM ✨</b>\n\n"
    "⚡ <b>SYSTEM STATUS:</b> 🟢 ONLINE\n"
    "💎 <b>ACCOUNT:</b> READY\n"
    "🔥━━━━━━━━━━━━━━━━━━🔥\n\n"
    "Welcome, <b>{name}</b>!\n"
    "Your bot experience starts here.\n\n"
    "⚡ <b>POWERED BY RUPAYAN</b> ⚡\n"
    "🔥━━━━━━━━━━━━━━━━━━🔥"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user)
    await update.effective_message.reply_text(
        WELCOME.format(name=html.escape(user.first_name or "User")),
        parse_mode="HTML",
        reply_markup=main_keyboard(),
    )


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user)
    row = get_user(user.id)
    await update.effective_message.reply_text(
        "👤 <b>YOUR PROFILE</b>\n\n"
        f"Name: {html.escape(row[2] or 'User')}\n"
        f"User ID: <code>{row[0]}</code>\n"
        f"Username: @{html.escape(row[1]) if row[1] else 'Not set'}\n"
        f"Credits: 💎 <b>{row[3]}</b>\n"
        f"Joined: {html.escape(row[4][:10])}",
        parse_mode="HTML",
    )


async def credits_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    register_user(update.effective_user)
    row = get_user(update.effective_user.id)
    await update.effective_message.reply_text(
        f"💎 Your credits: <b>{row[3]}</b>",
        parse_mode="HTML",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "🔥 <b>RUPAYAN AI BOT HELP</b>\n\n"
        "/start — Open the welcome menu\n"
        "/profile — View your profile\n"
        "/credits — Check your credits\n"
        "/help — Show this help\n\n"
        "Admin commands:\n"
        "/admin — Open admin panel\n"
        "/stats — View bot statistics\n"
        "/addcredits USER_ID AMOUNT — Add credits",
        parse_mode="HTML",
    )


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.effective_message.reply_text("⛔ Admin access only.")
        return
    await update.effective_message.reply_text(
        "👑 <b>RUPAYAN ADMIN PANEL</b>",
        parse_mode="HTML",
        reply_markup=admin_keyboard(),
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.effective_message.reply_text("⛔ Admin access only.")
        return
    await update.effective_message.reply_text(
        "📊 <b>BOT STATISTICS</b>\n\n"
        f"👥 Registered users: <b>{user_count()}</b>\n"
        f"💎 Total credits: <b>{total_credits()}</b>",
        parse_mode="HTML",
    )


async def addcredits_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.effective_message.reply_text("⛔ Admin access only.")
        return

    if len(context.args) != 2:
        await update.effective_message.reply_text(
            "Usage: /addcredits USER_ID AMOUNT"
        )
        return

    try:
        target_id = int(context.args[0])
        amount = int(context.args[1])
        if amount <= 0 or amount > 100000:
            raise ValueError
    except ValueError:
        await update.effective_message.reply_text(
            "Please provide a valid user ID and an amount from 1 to 100000."
        )
        return

    if not add_credits(target_id, amount):
        await update.effective_message.reply_text("❌ User not found.")
        return

    await update.effective_message.reply_text(
        f"✅ Added {amount} credits to user {target_id}."
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    register_user(user)

    if query.data == "profile":
        row = get_user(user.id)
        text = (
            "👤 <b>YOUR PROFILE</b>\n\n"
            f"Name: {html.escape(row[2] or 'User')}\n"
            f"User ID: <code>{row[0]}</code>\n"
            f"Credits: 💎 <b>{row[3]}</b>"
        )
        await query.message.reply_text(text, parse_mode="HTML")

    elif query.data == "credits":
        row = get_user(user.id)
        await query.message.reply_text(
            f"💎 Your credits: <b>{row[3]}</b>",
            parse_mode="HTML",
        )

    elif query.data == "help":
        await query.message.reply_text(
            "Use /start, /profile, /credits and /help."
        )

    elif query.data == "about":
        await query.message.reply_text(
            "🔥 <b>RUPAYAN AI BOT</b>\n⚡ Powered by RUPAYAN",
            parse_mode="HTML",
        )

    elif query.data == "admin_stats":
        if not is_admin(user.id):
            return
        await query.message.reply_text(
            "📊 <b>BOT STATISTICS</b>\n\n"
            f"👥 Users: <b>{user_count()}</b>\n"
            f"💎 Credits: <b>{total_credits()}</b>",
            parse_mode="HTML",
        )

    elif query.data == "home":
        await query.message.reply_text(
            "🔥 <b>MAIN MENU</b>",
            parse_mode="HTML",
            reply_markup=main_keyboard(),
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.exception("Unhandled bot error", exc_info=context.error)


def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN is missing. Add it in Render Environment Variables."
        )

    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("credits", credits_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("addcredits", addcredits_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_error_handler(error_handler)

    logger.info("RUPAYAN AI BOT is starting...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
