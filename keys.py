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

    await update.message.reply_text(
        f"✅ New Key:\n\n"
        f"🔑 Key: `{key}`\n"
        f"⏳ Validity: {days} day(s)\n"
        f"📅 Expires: {expiry}",
        parse_mode="Markdown"
    )
