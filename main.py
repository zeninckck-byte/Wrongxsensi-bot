import requests

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from keys import generate_key
from database import save_key, get_key, mark_used, reset_key, save_ip, get_ip

TOKEN = "8873787131:AAHsJc_rvxPmwwQmcRuZVtrpw3z_JV63sJQ"
ADMIN_ID = 8226572649

API_URL = "https://wrongxsensi-bot-production.up.railway.app/activate"

waiting_for_key = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔑 Activate Key", callback_data="activate")],
        [InlineKeyboardButton("👤 Profile", callback_data="profile")],
        [InlineKeyboardButton("📢 Join Channel", url="https://t.me/+UCI8v9aNQyJkNDY1")]
    ]

    await update.message.reply_text(
        "🔥 Welcome to WRONGxSENSI BOT 🔥\n\nChoose an option:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "activate":
        waiting_for_key.add(query.from_user.id)

        await query.edit_message_text(
            "🔑 Send your activation key."
        )

    elif query.data == "profile":
        user = query.from_user
        username = user.username if user.username else "No username"

        await query.edit_message_text(
            f"👤 Profile\n\n"
            f"Name: {user.first_name}\n"
            f"Username: @{username}"
        )


async def genkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not the admin.")
        return

    if len(context.args) != 1:
        await update.message.reply_text(
            "Usage:\n/genkey 1\n/genkey 7\n/genkey 30"
        )
        return

    try:
        days = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Enter a valid number.")
        return

    key, expiry = generate_key(days)

    save_key(key, expiry)

    await update.message.reply_text(
        f"✅ New Key\n\n"
        f"🔑 Key: `{key}`\n"
        f"⏳ Validity: {days} day(s)\n"
        f"📅 Expires: {expiry}",
        parse_mode="Markdown"
    )


async def activate_key(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id not in waiting_for_key:
        return

    waiting_for_key.remove(update.effective_user.id)

    key = update.message.text.strip()

    data = get_key(key)

    if data is None:
        await update.message.reply_text("❌ Invalid key.")
        return

    if data[2] == 1:
        await update.message.reply_text("❌ This key has already been used.")
        return

    mark_used(key)

    try:
        response = requests.post(
            "https://wrongxsensi-bot-production.up.railway.app/activate",
            json={"key": key},
            timeout=10
        )

        ip_data = response.json()
        user_ip = ip_data.get("ip", "Unknown")

        save_ip(key, user_ip)

    except Exception as e:
        user_ip = "Not connected"

    await update.message.reply_text(
        f"✅ Key Activated Successfully!\n\n"
        f"📅 Expires: {data[1]}\n"
        f"🌐 IP Lock: {user_ip}"
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not the admin.")
        return

    if len(context.args) != 1:
        await update.message.reply_text(
            "Usage:\n/reset KEY"
        )
        return

    key = context.args[0]

    reset_key(key)

    await update.message.reply_text(
        "✅ Key reset successfully."
    )

async def bind(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only")
        return

    if len(context.args) != 2:
        await update.message.reply_text(
            "Usage:\n/bind KEY IP"
        )
        return

    key = context.args[0]
    ip = context.args[1]

    save_ip(key, ip)

    await update.message.reply_text(
        f"✅ IP Locked\n\n"
        f"🔑 Key: {key}\n"
        f"🌐 IP: {ip}"
    )

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("genkey", genkey))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(CommandHandler("reset", reset))
app.add_handler(CommandHandler("bind", bind))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, activate_key))

print("Bot Started...")
app.run_polling()
