import logging
import os
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, filters

# Подключаем данные и настройки
ADMIN_ID = 301661957

QUESTION1, QUESTION2, POLL, CONFIRM, PHONE = range(5)
user_data = {}

logging.basicConfig(level=logging.INFO)

# /start
async def start(update, context):
    user_id = update.effective_user.id
    if user_id in user_data:
        await update.message.reply_text(
            "Ты уже начал диалог. Напиши /cancel, если хочешь начать заново."
        )
        return ConversationHandler.END

    user_data[user_id] = {}
    await update.message.reply_text(
        "Привет! Давай начнём. Напиши, пожалуйста, что тебя интересует? (Покупка/аренда квартиры/дома)"
    )
    return QUESTION1

# Интерес
async def question1(update, context):
    user_id = update.effective_user.id
    user_data[user_id]['interest'] = update.message.text
    await update.message.reply_text("Какой город?")
    return QUESTION2

# Город
async def question2(update, context):
    user_id = update.effective_user.id
    user_data[user_id]['city'] = update.message.text

    reply_keyboard = [["До 1000€", "До 2000€", "От 2000€"]]
    await update.message.reply_text(
        "Какой бюджет?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return POLL

# Бюджет
async def poll(update, context):
    user_id = update.effective_user.id
    user_data[user_id]['budget'] = update.message.text

    data = user_data[user_id]
    summary = (
        f"Вот что ты указал:\n\n"
        f"🧠 Интерес: {data['interest']}\n"
        f"🏙 Город: {data['city']}\n"
        f"💶 Бюджет: {data['budget']}\n\n"
        "Если всё верно, отправь номер телефона для связи:"
    )

    contact_button = KeyboardButton("Отправить номер телефона", request_contact=True)
    reply_markup = ReplyKeyboardMarkup([[contact_button]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(summary, reply_markup=reply_markup)

    return PHONE

# Телефон
async def phone(update, context):
    user_id = update.effective_user.id
    contact = update.message.contact.phone_number if update.message.contact else update.message.text
    user_data[user_id]['phone'] = contact

    data = user_data[user_id]

    username = update.effective_user.username or update.effective_user.first_name or "Неизвестно"
    text = (
        f"📥 Новый ответ от @{username}:\n\n"
        f"🧠 Интересуется: {data['interest']}\n"
        f"🏙 Город: {data['city']}\n"
        f"💶 Бюджет: {data['budget']}\n"
        f"📞 Телефон: {data['phone']}"
    )

    await context.bot.send_message(chat_id=ADMIN_ID, text=text)
    await update.message.reply_text("Спасибо! Мы скоро с тобой свяжемся 💬")

    # Удаляем данные пользователя после завершения
    user_data.pop(user_id, None)

    return ConversationHandler.END

# Отмена
async def cancel(update, context):
    user_id = update.effective_user.id
    user_data.pop(user_id, None)
    await update.message.reply_text("Диалог прерван.")
    return ConversationHandler.END

# Основной запуск
async def start_bot():
    TOKEN = os.getenv("BOT_TOKEN")
    app = Application.builder().token(TOKEN).build()

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
    await app.run_polling()

if __name__ == '__main__':
    # Запуск бота
    import asyncio
    asyncio.run(start_bot())
