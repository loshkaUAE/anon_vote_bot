import logging
from collections import Counter
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)

votes = {}  # user_id -> vote
anonymous_mode = set()  # user_id, кто в анонимном чате

# Главная кнопка
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🟩 За открытые двери", callback_data="for")],
        [InlineKeyboardButton("🟥 Против", callback_data="against")],
        [InlineKeyboardButton("📊 Посмотреть результаты", callback_data="result")],
        [InlineKeyboardButton("💬 Анонимный чат", callback_data="anon_chat")]
    ]
    await update.message.reply_text(
        "📢 *Голосование и анонимный чат*\n"
        "Выберите вариант:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# Голосование и кнопки
async def vote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    choice = query.data

    if choice in ["for", "against"]:
        votes[user_id] = choice
        await query.answer("✅ Голос принят!")
    elif choice == "result":
        await show_result(query)
    elif choice == "anon_chat":
        anonymous_mode.add(user_id)
        await query.answer("💬 Теперь вы в анонимном чате. Отправляйте сообщения сюда!")

# Показ результатов
async def show_result(query):
    if not votes:
        await query.answer()
        await query.edit_message_text("❗ Пока никто не проголосовал")
        return

    count = Counter(votes.values())
    for_votes = count.get("for", 0)
    against_votes = count.get("against", 0)

    total = for_votes + against_votes
    pct_for = round(for_votes / total * 100, 1)
    pct_against = round(against_votes / total * 100, 1)

    text = (
        "📊 *Результаты голосования:*\n\n"
        f"🟩 За открытые двери: *{for_votes}* ({pct_for}%)\n"
        f"🟥 Против: *{against_votes}* ({pct_against}%)\n\n"
        f"👥 Всего голосов: {total}"
    )

    await query.answer()
    await query.edit_message_text(text, parse_mode="Markdown")

# Обработка сообщений в анонимном чате
async def anonymous_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in anonymous_mode:
        # Отправляем всем, кто в анонимном чате
        for uid in anonymous_mode:
            if uid != user_id:
                try:
                    await context.bot.send_message(chat_id=uid, text=f"💬 Аноним: {update.message.text}")
                except:
                    pass  # если не удалось отправить
        await update.message.delete()  # удаляем исходное сообщение для анонимности

def main():
    app = ApplicationBuilder().token("8594247473:AAF3gahl3-jwT1lpjbuN98_n88l0Jfdkxso").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(vote))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), anonymous_message))

    print("✅ Bot started")
    app.run_polling()

if __name__ == "__main__":
    main()
