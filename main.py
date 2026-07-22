from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from keys import generate_key
from database import save_key, get_key, mark_used

TOKEN = "8873787131:AAHsJc_rvxPmwwQmcRuZVtrpw3z_JV63sJQ"
ADMIN_ID = 8226572649

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

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("genkey", genkey))
app.add_handler(CallbackQueryHandler(button))

print("Bot Started...")
app.run_polling()
