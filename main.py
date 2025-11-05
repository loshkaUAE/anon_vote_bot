import logging
import json
from collections import Counter
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(level=logging.INFO)

VOTES_FILE = "votes.json"

# Загружаем голоса из файла
try:
    with open(VOTES_FILE, "r") as f:
        votes = json.load(f)
        votes = {int(k): v for k, v in votes.items()}  # ключи должны быть int
except FileNotFoundError:
    votes = {}

# Главная кнопка
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🟩 За открытые двери", callback_data="for")],
        [InlineKeyboardButton("🟥 Против", callback_data="against")],
        [InlineKeyboardButton("📊 Посмотреть результаты", callback_data="result")],
        [InlineKeyboardButton("🔗 Вступить в группу", url="https://t.me/podslushkaKZO")]
    ]
    await update.message.reply_text(
        "📢 *Голосование*\nВыберите вариант:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# Обработка голосования
async def vote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    choice = query.data

    if choice in ["for", "against"]:
        votes[user_id] = choice
        # Сохраняем в файл
        with open(VOTES_FILE, "w") as f:
            json.dump(votes, f)
        await query.answer("✅ Голос принят!")
    elif choice == "result":
        await show_result(query)

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

def main():
    app = ApplicationBuilder().token("токен от бота").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(vote))

    print("✅ Bot started")
    app.run_polling()

if __name__ == "__main__":
    main()
