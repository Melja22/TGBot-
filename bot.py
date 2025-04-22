import logging
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)

# Твой Telegram ID
ADMIN_ID = 301661957

# Этапы диалога
QUESTION1, QUESTION2, POLL, PHONE = range(4)

# Временное хранилище
user_data = {}

# Логирование
logging.basicConfig(level=logging.INFO)

# Стартовая команда
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Давай начнём. Напиши, пожалуйста, что тебя интересует? (Покупка/аренда квартиры/дома)"
    )
    return QUESTION1

# Ответ на первый вопрос
async def question1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {'interest': update.message.text}
    await update.message.reply_text("Какой город?")
    return QUESTION2

# Ответ на второй вопрос
async def question2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id]['city'] = update.message.text
    reply_keyboard = [["До 1000€", "До 2000€", "От 2000€"]]
    await update.message.reply_text(
        "Какой бюджет?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return POLL

# Выбор бюджета
async def poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id]['budget'] = update.message.text
    contact_button = KeyboardButton("Отправить номер телефона", request_contact=True)
    reply_markup = ReplyKeyboardMarkup([[contact_button]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "Окей! Остался только номер телефона для связи:",
        reply_markup=reply_markup
    )
    return PHONE

# Получение телефона
async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    contact = update.message.contact.phone_number if update.message.contact else update.message.text
    user_data[user_id]['phone'] = contact

    data = user_data[user_id]
    text = (
        f"📥 Новый ответ от @{update.effective_user.username or 'Неизвестно'}:\n\n"
        f"🧠 Интересуется: {data['interest']}\n"
        f"🏙 Город: {data['city']}\n"
        f"💶 Бюджет: {data['budget']}\n"
        f"📞 Телефон: {data['phone']}"
    )

    await context.bot.send_message(chat_id=ADMIN_ID, text=text)
    await update.message.reply_text("Спасибо! Мы скоро с тобой свяжемся 💬")
    return ConversationHandler.END

# Отмена
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Диалог прерван.")
    return ConversationHandler.END

# Запуск бота
async def main():
    TOKEN = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            QUESTION1: [MessageHandler(filters.TEXT & ~filters.COMMAND, question1)],
            QUESTION2: [MessageHandler(filters.TEXT & ~filters.COMMAND, question2)],
            POLL: [MessageHandler(filters.TEXT & ~filters.COMMAND, poll)],
            PHONE: [MessageHandler(filters.CONTACT | (filters.TEXT & ~filters.COMMAND), phone)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    logging.info("Бот запущен...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()
    await app.stop()
    await app.shutdown()

# Для запуска через asyncio
if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
