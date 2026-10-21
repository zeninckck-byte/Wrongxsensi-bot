import os
import sqlite3
import logging
import asyncio
import threading
import secrets
from datetime import datetime, timedelta, timezone

from flask import Flask, request, render_template_string, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
Application,
CommandHandler,
CallbackQueryHandler,
MessageHandler,
ContextTypes,
filters,
)

==========================================

CONFIGURATION

==========================================

logging.basicConfig(
format=”%(asctime)s - %(name)s - %(levelname)s - %(message)s”,
level=logging.INFO,
)

logger = logging.getLogger(name)

TOKEN = os.getenv(“TELEGRAM_BOT_TOKEN”, “”).strip()
ADMIN_ID = int(os.getenv(“ADMIN_ID”, “0”))
BOT_USERNAME = os.getenv(“BOT_USERNAME”, “YOUR_BOT_USERNAME”).lstrip(”@”)
CHANNEL_URL = os.getenv(“CHANNEL_URL”, “https://t.me/”)

DB_NAME = “bot.db”

web = Flask(name)

==========================================

DATABASE

==========================================

def init_db():
with sqlite3.connect(DB_NAME) as conn:
conn.execute(”””
CREATE TABLE IF NOT EXISTS keys (
key TEXT PRIMARY KEY,
expiry TEXT NOT NULL,
used INTEGER DEFAULT 0
)
“””)
conn.execute(”””
CREATE TABLE IF NOT EXISTS users (
user_id INTEGER PRIMARY KEY,
username TEXT,
joined_at TEXT
)
“””)

def generate_key(days):
key = “WRONG-” + secrets.token_hex(4).upper()
expiry = (
datetime.now(timezone.utc) + timedelta(days=days)
).isoformat()

with sqlite3.connect(DB_NAME) as conn:
    conn.execute(
        "INSERT INTO keys (key, expiry, used) VALUES (?, ?, 0)",
        (key, expiry),
    )
return key, expiry

def is_admin(update):
user = update.effective_user
return user is not None and ADMIN_ID != 0 and user.id == ADMIN_ID

def save_user(user):
if user is None:
return

with sqlite3.connect(DB_NAME) as conn:
    conn.execute("""
        INSERT INTO users (user_id, username, joined_at)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET username=excluded.username
    """, (
        user.id,
        user.username or "",
        datetime.now(timezone.utc).isoformat(),
    ))

==========================================

WEBSITE

==========================================

HTML = “””

<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#090909">
<title>WRONGxSENSI</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#080808;color:#fff;font-family:Arial,sans-serif}
header{display:flex;justify-content:space-between;align-items:center;padding:20px;border-bottom:1px solid #292929}
.logo{color:#ff3030;font-size:21px;font-weight:900}
header a{color:#fff;text-decoration:none}
.hero{text-align:center;padding:75px 20px 55px}
.badge{display:inline-block;border:1px solid #ff3030;color:#ff5555;padding:9px 14px;border-radius:30px;font-size:11px;letter-spacing:2px}
h1{font-size:clamp(38px,10vw,68px);font-weight:900;margin:24px 0}
h1 span{color:#ff3030}
p{color:#aaa;line-height:1.7}
.button{display:inline-block;border:0;border-radius:8px;padding:14px 19px;margin:8px 4px;background:#ff3030;color:#fff;text-decoration:none;font-weight:bold;cursor:pointer}
.secondary{background:#171717;border:1px solid #333}
section{max-width:800px;margin:auto;padding:25px 20px}
.card{background:#111;border:1px solid #292929;border-radius:14px;padding:22px;margin:15px 0}
input{width:100%;padding:15px;background:#080808;color:white;border:1px solid #393939;border-radius:8px;font-size:16px;margin:10px 0}
#result{overflow-wrap:anywhere}
footer{text-align:center;padding:30px;border-top:1px solid #292929;color:#888;font-size:12px}
</style>
</head>
<body>
<header>
<div class="logo">WRONGxSENSI</div>
<a href="#services">EXPLORE ↓</a>
</header>
<div class="hero">
<div class="badge">FREE FIRE GAMING</div>
<h1>DOMINATE <span>THE GAME.</span></h1>
<p>Welcome to WRONGxSENSI — sensitivity settings, gaming content and activation key management.</p>
<a class="button" href="#activate">🔑 Check Key</a>
<a class="button secondary" href="https://t.me/{{ bot }}">🤖 Open Telegram Bot</a>
</div>
<section id="services">
<h2>Our Services</h2>
<div class="card">
<h3>🔑 Activation Keys</h3>
<p>Check your key's validity and expiry status.</p>
<a class="button" href="#activate">Check a Key</a>
</div>
<div class="card">
<h3>👤 Player Profile</h3>
<p>Open Telegram to access your bot profile.</p>
<a class="button secondary" href="https://t.me/{{ bot }}">Open Profile</a>
</div>
<div class="card">
<h3>💎 Buy Keys</h3>
<p>Contact the administrator for prices and availability.</p>
<a class="button secondary" href="https://t.me/{{ bot }}">Contact Us</a>
</div>
</section>
<section id="activate">
<h2>🔑 Check Activation Key</h2>
<div class="card">
<p>This checks your key's status. It does not activate an external service.</p>
<form id="keyForm">
<input id="key" maxlength="50" placeholder="WRONG-XXXXXXXX" required autocomplete="off">
<button class="button" type="submit">Check Key</button>
</form>
<p id="result" role="status"></p>
</div>
</section>
<footer>© 2026 WRONGxSENSI · Gaming Community</footer>
<script>
document.getElementById("keyForm").addEventListener("submit",async function(e){
e.preventDefault();
const result=document.getElementById("result");
result.textContent="Checking...";
try{
const response=await fetch("/api/check-key",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({key:document.getElementById("key").value})
});
const data=await response.json();
result.textContent=data.message||"Unable to check key.";
}catch(err){result.textContent="Connection error. Please try again."}
});
</script>
</body>
</html>
"""

@web.route(”/”)
def home():
return render_template_string(HTML, bot=BOT_USERNAME)

@web.route(”/health”)
def health():
return “WRONGxSENSI ONLINE”, 200

@web.route(”/api/check-key”, methods=[“POST”])
def check_key():
data = request.get_json(silent=True) or {}
key = data.get(“key”, “”)

if not isinstance(key, str) or not key.strip():
    return jsonify(message="Please enter a key."), 400
key = key.strip().upper()
try:
    with sqlite3.connect(DB_NAME, timeout=5) as conn:
        row = conn.execute(
            "SELECT expiry, used FROM keys WHERE key = ?", (key,)
        ).fetchone()
except sqlite3.Error:
    web.logger.exception("Database error")
    return jsonify(message="Temporarily unavailable."), 503
if not row:
    return jsonify(message="❌ Invalid key.")
expiry_text, used = row
try:
    expiry = datetime.fromisoformat(expiry_text)
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)
except ValueError:
    return jsonify(message="Invalid expiry information."), 500
if datetime.now(timezone.utc) >= expiry:
    return jsonify(message="⌛ Key expired.")
if used:
    return jsonify(message="⚠️ Key already used.")
return jsonify(message="✅ Key is valid and unused. Activate through Telegram.")

==========================================

TELEGRAM COMMANDS

==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
user = update.effective_user
save_user(user)

keyboard = [
    [InlineKeyboardButton("🔑 Activate Key", callback_data="activate")],
    [InlineKeyboardButton("👤 Profile", callback_data="profile")],
    [InlineKeyboardButton("🌐 Website", url=os.getenv("WEBSITE_URL", "https://replit.com"))],
    [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_URL)],
]
await update.effective_message.reply_text(
    "🔥 Welcome to WRONGxSENSI BOT 🔥\n\nChoose an option:",
    reply_markup=InlineKeyboardMarkup(keyboard),
)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()

if query.data == "activate":
    context.user_data["waiting_for_key"] = True
    await query.message.reply_text(
        "🔑 Send your activation key.\nExample: WRONG-ABC12345"
    )
elif query.data == "profile":
    user = query.from_user
    await query.message.reply_text(
        f"👤 YOUR PROFILE\n\n🆔 User ID: {user.id}\n"
        f"👤 Username: @{user.username or 'Not set'}"
    )

async def activate_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
if not context.user_data.get(“waiting_for_key”):
return

context.user_data["waiting_for_key"] = False
key = update.effective_message.text.strip().upper()
with sqlite3.connect(DB_NAME) as conn:
    row = conn.execute(
        "SELECT expiry, used FROM keys WHERE key = ?", (key,)
    ).fetchone()
if not row:
    await update.effective_message.reply_text("❌ Invalid key.")
    return
expiry_text, used = row
try:
    expiry = datetime.fromisoformat(expiry_text)
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)
except ValueError:
    await update.effective_message.reply_text("❌ Invalid expiry information.")
    return
if datetime.now(timezone.utc) >= expiry:
    await update.effective_message.reply_text("⌛ This key has expired.")
    return
if used:
    await update.effective_message.reply_text("⚠️ This key has already been used.")
    return
await update.effective_message.reply_text(
    "✅ Key is valid and unused. External activation is not configured."
)

async def genkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
if not is_admin(update):
await update.effective_message.reply_text(“⛔ Admin only.”)
return

if not context.args:
    await update.effective_message.reply_text("Usage: /genkey 1, /genkey 7, /genkey 30")
    return
try:
    days = int(context.args[0])
    if not 1 <= days <= 365:
        raise ValueError
    key, expiry = generate_key(days)
except (ValueError, sqlite3.IntegrityError):
    await update.effective_message.reply_text("❌ Enter days from 1 to 365.")
    return
await update.effective_message.reply_text(
    f"✅ KEY GENERATED\n\n🔑 Key: {key}\n📅 Valid for: {days} day(s)\n⌛ Expires: {expiry}"
)

async def reset_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
if not is_admin(update):
await update.effective_message.reply_text(“⛔ Admin only.”)
return

if not context.args:
    await update.effective_message.reply_text("Usage: /reset WRONG-ABC12345")
    return
with sqlite3.connect(DB_NAME) as conn:
    cur = conn.execute("UPDATE keys SET used=0 WHERE key=?", (context.args[0].upper(),))
await update.effective_message.reply_text(
    "✅ Key reset." if cur.rowcount else "❌ Key not found."
)

==========================================

START BOTH SERVICES

==========================================

def run_web():
port = int(os.getenv(“PORT”, “5000”))
web.run(host=“0.0.0.0”, port=port, use_reloader=False, threaded=True)

async def run_bot():
application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler(“start”, start))
application.add_handler(CommandHandler(“genkey”, genkey))
application.add_handler(CommandHandler(“reset”, reset_key))
application.add_handler(CallbackQueryHandler(button))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, activate_key))

await application.initialize()
await application.start()
await application.updater.start_polling(drop_pending_updates=True)
logger.info("WRONGxSENSI Telegram bot started")
try:
    await asyncio.Event().wait()
finally:
    await application.updater.stop()
    await application.stop()
    await application.shutdown()

def main():
if not TOKEN:
raise RuntimeError(“Missing TELEGRAM_BOT_TOKEN. Add it in Replit Secrets.”)

init_db()
threading.Thread(target=run_web, daemon=True).start()
asyncio.run(run_bot())

if name == “main”:
main()
