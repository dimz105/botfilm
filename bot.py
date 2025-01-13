# bot/bot.py

import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Updater, 
    CommandHandler, 
    MessageHandler, 
    Filters, 
    ConversationHandler, 
    CallbackContext
)
from dotenv import load_dotenv
import os
from numerology import (
    calculate_life_path_number,
    calculate_expression_number,
    calculate_soul_number,
    calculate_personality_number,
    calculate_improvement_number
)

# Завантаження змінних середовища
load_dotenv()

# Отримання токена з змінних середовища
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("Встановіть змінну середовища TELEGRAM_BOT_TOKEN у файлі .env")

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Стани для ConversationHandler
NAME, DOB = range(2)

def start(update: Update, context: CallbackContext) -> int:
    """Обробник команди /start"""
    user = update.message.from_user
    logger.info("User %s started the conversation.", user.first_name)
    update.message.reply_text(
        "Вітаю! Я NumerologyGuruBot. Я допоможу вам дізнатися ваші нумерологічні числа.\n\n"
        "Щоб почати, введіть своє повне ім'я."
    )
    return NAME

def help_command(update: Update, context: CallbackContext) -> None:
    """Обробник команди /help"""
    update.message.reply_text(
        "Доступні команди:\n"
        "/start - Почати нумерологічний аналіз\n"
        "/help - Отримати допомогу\n"
        "/analyze - Провести аналіз (запустити діалог заново)"
    )

def analyze(update: Update, context: CallbackContext) -> int:
    """Обробник команди /analyze"""
    user = update.message.from_user
    logger.info("User %s initiated analysis.", user.first_name)
    update.message.reply_text(
        "Давайте проведемо ваш нумерологічний аналіз.\n\n"
        "Будь ласка, введіть своє повне ім'я."
    )
    return NAME

def name_received(update: Update, context: CallbackContext) -> int:
    """Обробник отримання імені користувача"""
    user = update.message.from_user
    name = update.message.text
    logger.info("User %s entered name: %s", user.first_name, name)
    context.user_data['name'] = name
    update.message.reply_text(
        "Дякую! Тепер введіть вашу дату народження у форматі DD-MM-YYYY (наприклад, 25-12-1990)."
    )
    return DOB

def dob_received(update: Update, context: CallbackContext) -> int:
    """Обробник отримання дати народження"""
    user = update.message.from_user
    dob = update.message.text
    logger.info("User %s entered DOB: %s", user.first_name, dob)
    
    # Перевірка формату дати
    try:
        day, month, year = map(int, dob.split('-'))
        dob_formatted = f"{day:02d}-{month:02d}-{year}"
    except ValueError:
        update.message.reply_text(
            "Неправильний формат дати. Будь ласка, введіть дату народження у форматі DD-MM-YYYY."
        )
        return DOB
    
    context.user_data['dob'] = dob_formatted
    
    # Проведення нумерологічного аналізу
    name = context.user_data['name']
    life_path = calculate_life_path_number(dob_formatted)
    expression = calculate_expression_number(name)
    soul = calculate_soul_number(name)
    personality = calculate_personality_number(name)
    improvement = calculate_improvement_number(life_path, expression)
    
    analysis = (
        f"**Нумерологічний Аналіз**\n\n"
        f"**Ім'я:** {name}\n"
        f"**Дата народження:** {dob_formatted}\n\n"
        f"**Число Життєвого Шляху:** {life_path}\n"
        f"**Число Вираження:** {expression}\n"
        f"**Число Душі:** {soul}\n"
        f"**Число Особистості:** {personality}\n"
        f"**Число Вдосконалення:** {improvement}\n"
    )
    
    update.message.reply_text(analysis, parse_mode='Markdown')
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> int:
    """Обробник команди /cancel"""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        "Аналіз скасовано. Ви можете розпочати заново за допомогою команди /start.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def invalid_input(update: Update, context: CallbackContext) -> int:
    """Обробник неправильних введень"""
    update.message.reply_text(
        "Вибачте, я не зрозумів. Будь ласка, введіть правильні дані."
    )
    return

def main() -> None:
    """Основна функція запуску бота"""
    updater = Updater(TOKEN, use_context=True)
    
    dispatcher = updater.dispatcher
    
    # Додання обробника команд /start, /help, /analyze
    dispatcher.add_handler(CommandHandler("help", help_command))
    
    # ConversationHandler для аналізу
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), CommandHandler('analyze', analyze)],
        
        states={
            NAME: [MessageHandler(Filters.text & ~Filters.command, name_received)],
            DOB: [MessageHandler(Filters.text & ~Filters.command, dob_received)],
        },
        
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    dispatcher.add_handler(conv_handler)
    
    # Обробник неочікуваних команд
    dispatcher.add_handler(MessageHandler(Filters.command, invalid_input))
    
    # Запуск бота
    updater.start_polling()
    
    # Зупинка бота при натисканні Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()
