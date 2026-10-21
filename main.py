import os
import sqlite3
import logging
import asyncio
import threading
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ==========================================
# WRONGxSENSI TELEGRAM BOT
# ==========================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
API_URL = os.getenv("API_URL", "").strip()

DB_NAME = "bot.db"


# ==========================================
# HEALTH SERVER FOR REPLIT
# ==========================================

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"WRONGxSENSI BOT IS RUNNING")

    def log_message(self, format, *args):
        pass


def start_health_server():
    port = int(os.getenv("PORT", "5000"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    logger.info("Health server running on port %s", port)
    server.serve_forever()


# ==========================================
# DATABASE
# ==========================================

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS keys (
                key TEXT PRIMARY KEY,
                expiry TEXT NOT NULL,
                used INTEGER DEFAULT 0
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                joined_at TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS bindings (
                key TEXT PRIMARY KEY,
                ip TEXT NOT NULL
            )
        """)


def generate_key(days):
    import secrets

    key = "WRONG-" + secrets.token_hex(4).upper()
    expiry = (
        datetime.now(timezone.utc) + timedelta(days=days)
    ).isoformat()

    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            "INSERT INTO keys (key, expiry, used) VALUES (?, ?, 0)",
            (key, expiry),
        )

    return key, expiry


def get_key(key):
    with sqlite3.connect(DB_NAME) as conn:
        return conn.execute(
            "SELECT key, expiry, used FROM keys WHERE key = ?",
            (key,),
        ).fetchone()


def delete_key(key):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("DELETE FROM keys WHERE key = ?", (key,))
        conn.execute("DELETE FROM bindings WHERE key = ?", (key,))


def save_user(user):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            INSERT OR REPLACE INTO users (user_id, username, joined_at)
            VALUES (?, ?, COALESCE(
                (SELECT joined_at FROM users WHERE user_id = ?), ?
            ))
        """, (
            user.id,
            user.username or "",
            user.id,
            datetime.now(timezone.utc).isoformat(),
        ))


def is_admin(update):
    user = update.effective_user
    return user is not None and ADMIN_ID != 0 and user.id == ADMIN_ID


# ==========================================
# START COMMAND
# ==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_user(user)

    keyboard = [
        [
            InlineKeyboardButton(
                "🔑 Activate Key",
                callback_data="activate",
            )
        ],
        [
            InlineKeyboardButton(
                "👤 Profile",
                callback_data="profile",
            )
        ],
        [
            InlineKeyboardButton(
                "📢 Join Channel",
                url="https://t.me/",
            )
        ],
    ]

    await update.message.reply_text(
        "🔥 Welcome to WRONGxSENSI BOT 🔥\n\n"
        "Choose an option:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ==========================================
# BUTTON HANDLER
# ==========================================

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "activate":
        context.user_data["waiting_for_key"] = True

        await query.message.reply_text(
            "🔑 Send your activation key.\n\n"
            "Example: WRONG-ABC12345"
        )

    elif query.data == "profile":
        user = query.from_user

        await query.message.reply_text(
            "👤 YOUR PROFILE\n\n"
            f"🆔 User ID: {user.id}\n"
            f"👤 Username: @{user.username or 'Not set'}"
        )


# ==========================================
# ACTIVATION HANDLER
# ==========================================

async def activate_key(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not context.user_data.get("waiting_for_key"):
        return

    key = update.message.text.strip().upper()
    context.user_data["waiting_for_key"] = False

    record = get_key(key)

    if not record:
        await update.message.reply_text(
            "❌ Invalid key. Please check and try again."
        )
        return

    _, expiry_text, used = record

    try:
        expiry = datetime.fromisoformat(expiry_text)
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
    except ValueError:
        await update.message.reply_text(
            "❌ Key expiry information is invalid. Contact the admin."
        )
        return

    if datetime.now(timezone.utc) >= expiry:
        await update.message.reply_text(
            "⌛ This activation key has expired."
        )
        return

    if used:
        await update.message.reply_text(
            "⚠️ This key has already been used."
        )
        return

    if not API_URL:
        await update.message.reply_text(
            "⚠️ Activation service is not configured.\n"
            "Please contact the administrator."
        )
        return

    await update.message.reply_text(
        "⏳ Checking your key with the activation service..."
    )

    try:
        response = await asyncio.to_thread(
            requests.post,
            API_URL,
            json={
                "key": key,
                "user_id": update.effective_user.id,
            },
            timeout=15,
        )

        if 200 <= response.status_code < 300:
            with sqlite3.connect(DB_NAME) as conn:
                conn.execute(
                    "UPDATE keys SET used = 1 WHERE key = ? AND used = 0",
                    (key,),
                )

            await update.message.reply_text(
                "✅ Activation request accepted by the service."
            )
        else:
            logger.warning(
                "Activation service returned HTTP %s",
                response.status_code,
            )
            await update.message.reply_text(
                "❌ The activation service rejected the request.\n"
                "Please contact the administrator."
            )

    except requests.RequestException:
        logger.exception("Activation service connection failed")

        await update.message.reply_text(
            "❌ Could not connect to the activation service.\n"
            "Please try again later."
        )


# ==========================================
# GENERATE KEY — ADMIN ONLY
# Usage: /genkey 1
#        /genkey 7
#        /genkey 30
# ==========================================

async def genkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ Admin only.")
        return

    if not context.args:
        await update.message.reply_text(
            "Usage:\n"
            "/genkey 1\n"
            "/genkey 7\n"
            "/genkey 30"
        )
        return

    try:
        days = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Enter a valid number of days."
        )
        return

    if days < 1 or days > 365:
        await update.message.reply_text(
            "❌ Days must be between 1 and 365."
        )
        return

    key, expiry = generate_key(days)

    await update.message.reply_text(
        "✅ KEY GENERATED\n\n"
        f"🔑 Key: `{key}`\n"
        f"📅 Valid for: {days} day(s)\n"
        f"⌛ Expires: {expiry}",
        parse_mode="Markdown",
    )


# ==========================================
# RESET KEY — ADMIN ONLY
# Usage: /reset WRONG-ABC12345
# ==========================================

async def reset_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ Admin only.")
        return

    if not context.args:
        await update.message.reply_text(
            "Usage: /reset WRONG-ABC12345"
        )
        return

    key = context.args[0].upper()

    with sqlite3.connect(DB_NAME) as conn:
        result = conn.execute(
            "UPDATE keys SET used = 0 WHERE key = ?",
            (key,),
        )

    if result.rowcount:
        await update.message.reply_text(
            "✅ Key reset successfully."
        )
    else:
        await update.message.reply_text(
            "❌ Key not found."
        )


# ==========================================
# BIND KEY TO IP — ADMIN ONLY
# Usage: /bind WRONG-ABC12345 1.2.3.4
# ==========================================

async def bind_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ Admin only.")
        return

    if len(context.args) != 2:
        await update.message.reply_text(
            "Usage: /bind WRONG-ABC12345 IP_ADDRESS"
        )
        return

    key = context.args[0].upper()
    ip = context.args[1]

    if not get_key(key):
        await update.message.reply_text(
            "❌ Key not found."
        )
        return

    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO bindings (key, ip) VALUES (?, ?)",
            (key, ip),
        )

    await update.message.reply_text(
        f"✅ Key bound to IP: {ip}"
    )


# ==========================================
# ERROR HANDLER
# ==========================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):
    logger.error(
        "Telegram handler error",
        exc_info=context.error,
    )


# ==========================================
# MAIN
# ==========================================

def main():
    if not TOKEN:
        raise RuntimeError(
            "Missing TELEGRAM_BOT_TOKEN. Add it in Replit Secrets."
        )

    init_db()

    threading.Thread(
        target=start_health_server,
        daemon=True,
    ).start()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("genkey", genkey))
    app.add_handler(CommandHandler("reset", reset_key))
    app.add_handler(CommandHandler("bind", bind_key))

    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            activate_key,
        )
    )

    app.add_error_handler(error_handler)

    logger.info("WRONGxSENSI BOT starting...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
