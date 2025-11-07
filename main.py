import logging
import json
import random
from collections import Counter
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)

# === ФАЙЛЫ ДАННЫХ ===
VOTES_FILE = "votes.json"
ANON_FILE = "anon_users.json"

# === ЗАГРУЗКА ДАННЫХ ===
def load_data(file, default):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return default

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

votes = load_data(VOTES_FILE, {})
anon_users = load_data(ANON_FILE, {})  # user_id -> code (например: 1234567)

# === ГЛАВНОЕ МЕНЮ ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🟩 За открытые двери", callback_data="for")],
        [InlineKeyboardButton("🟥 Против", callback_data="against")],
        [InlineKeyboardButton("📊 Посмотреть результаты", callback_data="result")],
        [InlineKeyboardButton("💬 Анонимный чат", callback_data="anon_chat")],
        [InlineKeyboardButton("🔗 Вступить в группу", url="https://t.me/podslushkaKZO")]
    ]
    await update.message.reply_text(
        "📢 *Голосование и анонимный чат*\n"
        "Выберите вариант:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# === ГОЛОСОВАНИЕ ===
async def vote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    choice = query.data

    if choice in ["for", "against"]:
        votes[user_id] = choice
        save_data(VOTES_FILE, votes)
        await query.answer("✅ Голос принят!")
    elif choice == "result":
        await show_result(query)
    elif choice == "anon_chat":
        if str(user_id) not in anon_users:
            anon_code = random.randint(1000000, 9999999)
            anon_users[str(user_id)] = anon_code
            save_data(ANON_FILE, anon_users)
        await query.answer("💬 Вы вошли в анонимный чат!")
        await query.edit_message_text(
            "💬 Теперь вы можете писать сюда, и вас увидят другие участники анонимного чата.\n"
            "Ваш код: `{}`".format(anon_users[str(user_id)]),
            parse_mode="Markdown"
        )

# === ПОКАЗ РЕЗУЛЬТАТОВ ===
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

# === АНОНИМНЫЙ ЧАТ ===
async def anonymous_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if str(user_id) not in anon_users:
        return  # если человек не в чате — не обрабатывать

    code = anon_users[str(user_id)]
    message_text = update.message.text

    for uid_str in anon_users.keys():
        uid = int(uid_str)
        if uid != user_id:
            try:
                await context.bot.send_message(
                    chat_id=uid,
                    text=f"{code}: {message_text}"
                )
            except:
                pass  # если не получилось отправить (например, человек заблокировал бота)

def main():
    app = ApplicationBuilder().token("токен").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(vote))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), anonymous_message))

    print("✅ Bot started")
    app.run_polling()

if __name__ == "__main__":
    main()
