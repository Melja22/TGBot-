import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackContext, filters, ConversationHandler

# Заменить на свой ID — бот будет отправлять тебе ответы сюда
ADMIN_ID = 301661957  # твой Telegram ID

# Этапы диалога
QUESTION1, QUESTION2, POLL, PHONE = range(4)

# Временное хранилище
user_data = {}

# Логирование
logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: CallbackContext.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Давай начнём. Напиши, пожалуйста, чем ты интересуешься?")
    return QUESTION1

async def question1(update: Update, context: CallbackContext.DEFAULT_TYPE):
    user_data[update.effective_user.id] = {'interest': update.message.text}
    await update.message.reply_text("Спасибо! А теперь скажи, сколько у тебя свободного времени в день?")
    return QUESTION2

async def question2(update: Update, context: CallbackContext.DEFAULT_TYPE):
    user_data[update.effective_user.id]['time'] = update.message.text
    reply_keyboard = [["Утром", "Днём", "Вечером"]]
    await update.message.reply_text(
        "Когда тебе удобно выходить на связь?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return POLL

async def poll(update: Update, context: CallbackContext.DEFAULT_TYPE):
    user_data[update.effective_user.id]['time_pref'] = update.message.text
    contact_button = KeyboardButton("Отправить номер телефона", request_contact=True)
    reply_markup = ReplyKeyboardMarkup([[contact_button]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Окей! Остался только номер телефона для связи:", reply_markup=reply_markup)
    return PHONE

async def phone(update: Update, context: CallbackContext.DEFAULT_TYPE):
    contact = update.message.contact.phone_number if update.message.contact else update.message.text
    user_data[update.effective_user.id]['phone'] = contact

    # Сборка сообщения
    data = user_data[update.effective_user.id]
    text = (
        f"📥 Новый ответ от @{update.effective_user.username}:\n\n"
        f"🧠 Интересуется: {data['interest']}\n"
        f"⏱ Время в день: {data['time']}\n"
        f"🕒 Удобное время связи: {data['time_pref']}\n"
        f"📞 Телефон: {data['phone']}"
    )

    # Отправка тебе
    await context.bot.send_message(chat_id=ADMIN_ID, text=text)
    await update.message.reply_text("Спасибо! Мы скоро с тобой свяжемся 💬")
    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext.DEFAULT_TYPE):
    await update.message.reply_text("Диалог прерван.")
    return ConversationHandler.END

def main():
    import os
    TOKEN = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            QUESTION1: [MessageHandler(filters.TEXT & ~filters.COMMAND, question1)],
            QUESTION2: [MessageHandler(filters.TEXT & ~filters.COMMAND, question2)],
            POLL: [MessageHandler(filters.TEXT & ~filters.COMMAND, poll)],
            PHONE: [MessageHandler(filters.CONTACT | filters.TEXT & ~filters.COMMAND, phone)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == '__main__':
    main()
