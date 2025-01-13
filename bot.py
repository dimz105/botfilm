# bot/bot.py

import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater, 
    CommandHandler, 
    MessageHandler, 
    Filters, 
    ConversationHandler, 
    CallbackContext, 
    CallbackQueryHandler
)
from dotenv import load_dotenv
import os
from numerology import (
    calculate_life_path_number,
    calculate_expression_number,
    calculate_soul_number,
    calculate_personality_number,
    calculate_improvement_number,
    calculate_destiny_number,
    calculate_career_number,
    calculate_relationship_number,
    calculate_lucky_number
)
from database import Session, User, UserAnalysis
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler
import datetime

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
NAME, DOB, PARTNER_NAME, RELATIONSHIP_DOB, LANGUAGE_SELECTION, TEST_SELECTION, TEST_QUESTION, TEST_NUMBER, LUCKY_SELECTION = range(9)

# Ініціалізація Flask-додатку
app = Flask(__name__)

# Ініціалізація бота та диспетчера
from telegram import Bot
from telegram.ext import Dispatcher

bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot, None, workers=0)

# Ініціалізація планувальника
scheduler = BackgroundScheduler()
scheduler.start()

# Додаткові функції для бота
def start(update: Update, context: CallbackContext) -> int:
    """Обробник команди /start"""
    user = update.message.from_user
    session = Session()
    db_user = session.query(User).filter_by(telegram_id=user.id).first()
    if not db_user:
        db_user = User(telegram_id=user.id)
        session.add(db_user)
        session.commit()
    session.close()
    
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
        "/analyze - Провести аналіз заново\n"
        "/history - Переглянути історію аналізів\n"
        "/compatibility - Аналіз сумісності з партнером\n"
        "/learn - Навчальні матеріали\n"
        "/test - Пройти нумерологічний тест\n"
        "/lucky - Генератор щасливих чисел\n"
        "/language - Вибір мови\n"
        "/share - Поділитися аналізом\n"
        "/cancel - Скасувати діалог"
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
    name = update.message.text.strip()
    if not validate_name(name):
        update.message.reply_text(
            "Будь ласка, введіть коректне ім'я (тільки літери та пробіли)."
        )
        return NAME
    logger.info("User %s entered name: %s", user.first_name, name)
    context.user_data['name'] = name
    update.message.reply_text(
        "Дякую! Тепер введіть вашу дату народження у форматі DD-MM-YYYY (наприклад, 25-12-1990)."
    )
    return DOB

def dob_received(update: Update, context: CallbackContext) -> int:
    """Обробник отримання дати народження"""
    user = update.message.from_user
    dob = update.message.text.strip()
    logger.info("User %s entered DOB: %s", user.first_name, dob)
    
    if not validate_dob(dob):
        update.message.reply_text(
            "Неправильний формат дати. Будь ласка, введіть дату народження у форматі DD-MM-YYYY."
        )
        return DOB
    
    dob_formatted = dob
    context.user_data['dob'] = dob_formatted
    
    # Розрахунок чисел
    name = context.user_data['name']
    life_path = calculate_life_path_number(dob_formatted)
    expression = calculate_expression_number(name)
    soul = calculate_soul_number(name)
    personality = calculate_personality_number(name)
    improvement = calculate_improvement_number(life_path, expression)
    destiny = calculate_destiny_number(life_path, expression)
    career = calculate_career_number(expression, destiny)
    
    analysis = (
        f"**Нумерологічний Аналіз**\n\n"
        f"**Ім'я:** {name}\n"
        f"**Дата народження:** {dob_formatted}\n\n"
        f"**Число Життєвого Шляху:** {life_path}\n"
        f"**Число Вираження:** {expression}\n"
        f"**Число Душі:** {soul}\n"
        f"**Число Особистості:** {personality}\n"
        f"**Число Вдосконалення:** {improvement}\n"
        f"**Число Судьби:** {destiny}\n"
        f"**Число Кар'єри:** {career}\n"
    )
    
    update.message.reply_text(analysis, parse_mode='Markdown')
    
    # Збереження аналізу в базі даних
    session = Session()
    db_user = session.query(User).filter_by(telegram_id=user.id).first()
    if not db_user:
        db_user = User(telegram_id=user.id)
        session.add(db_user)
        session.commit()
    
    user_analysis = UserAnalysis(
        user_id=db_user.id,
        name=name,
        dob=dob_formatted,
        life_path=life_path,
        expression=expression,
        soul=soul,
        personality=personality,
        improvement=improvement,
        destiny=destiny,
        career=career
    )
    session.add(user_analysis)
    session.commit()
    session.close()
    
    # Збереження останнього аналізу для команди /share
    context.user_data['latest_analysis'] = analysis
    
    # Запланувати щоденні прогнози
    schedule_daily_forecast(user.id, user.id, life_path)
    
    # Показати головне меню
    main_menu(update, context)
    
    return ConversationHandler.END

def history(update: Update, context: CallbackContext) -> None:
    """Обробник команди /history"""
    user = update.message.from_user
    session = Session()
    db_user = session.query(User).filter_by(telegram_id=user.id).first()
    if not db_user:
        update.message.reply_text("Ви ще не проводили нумерологічний аналіз.")
        session.close()
        return
    
    analyses = session.query(UserAnalysis).filter_by(user_id=db_user.id).order_by(UserAnalysis.timestamp.desc()).all()
    session.close()
    
    if not analyses:
        update.message.reply_text("Ви ще не проводили нумерологічний аналіз.")
        return
    
    message = "**Ваші Попередні Аналізи:**\n\n"
    for analysis in analyses[:5]:  # Показати останні 5 аналізів
        message += (
            f"*Дата:* {analysis.timestamp.strftime('%d-%m-%Y %H:%M')}\n"
            f"*Ім'я:* {analysis.name}\n"
            f"*Число Життєвого Шляху:* {analysis.life_path}\n\n"
        )
    
    update.message.reply_text(message, parse_mode='Markdown')

def compatibility(update: Update, context: CallbackContext) -> int:
    """Обробник команди /compatibility"""
    user = update.message.from_user
    update.message.reply_text(
        "Введіть повне ім'я партнера для аналізу сумісності."
    )
    return PARTNER_NAME

def relationship_name_received(update: Update, context: CallbackContext) -> int:
    """Обробник отримання імені партнера"""
    partner_name = update.message.text.strip()
    if not validate_name(partner_name):
        update.message.reply_text(
            "Будь ласка, введіть коректне ім'я партнера (тільки літери та пробіли)."
        )
        return PARTNER_NAME
    context.user_data['partner_name'] = partner_name
    update.message.reply_text(
        "Введіть дату народження партнера у форматі DD-MM-YYYY."
    )
    return RELATIONSHIP_DOB

def relationship_dob_received(update: Update, context: CallbackContext) -> int:
    """Обробник отримання дати народження партнера"""
    partner_dob = update.message.text.strip()
    if not validate_dob(partner_dob):
        update.message.reply_text(
            "Неправильний формат дати. Будь ласка, введіть дату народження у форматі DD-MM-YYYY."
        )
        return RELATIONSHIP_DOB
    
    context.user_data['partner_dob'] = partner_dob
    
    # Розрахунок чисел для партнера
    partner_life_path = calculate_life_path_number(partner_dob)
    partner_expression = calculate_expression_number(context.user_data['partner_name'])
    
    # Розрахунок сумісності
    life_path_compat = calculate_relationship_number(context.user_data['life_path'], partner_life_path)
    expression_compat = calculate_relationship_number(context.user_data['expression'], partner_expression)
    
    analysis = (
        f"**Аналіз Сумісності**\n\n"
        f"**Ваше Ім'я:** {context.user_data['name']}\n"
        f"**Ім'я Партнера:** {context.user_data['partner_name']}\n\n"
        f"**Ваше Число Життєвого Шляху:** {context.user_data['life_path']}\n"
        f"**Число Життєвого Шляху Партнера:** {partner_life_path}\n\n"
        f"**Сумісність Чисел Життєвого Шляху:** {life_path_compat}\n"
        f"**Сумісність Чисел Вираження:** {expression_compat}\n\n"
        f"Ці числа свідчать про рівень гармонії та потенціал вашого співжиття."
    )
    
    update.message.reply_text(analysis, parse_mode='Markdown')
    return ConversationHandler.END

def learn(update: Update, context: CallbackContext) -> int:
    """Обробник команди /learn"""
    keyboard = [
        ['Основи нумерології', 'Розрахунок чисел'],
        ['Значення чисел', 'Інтерактивні уроки']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    update.message.reply_text(
        "Виберіть категорію для навчання:",
        reply_markup=reply_markup
    )
    return LANGUAGE_SELECTION  # Використовується як стан для навчання

def learn_category_received(update: Update, context: CallbackContext) -> int:
    category = update.message.text
    if category == 'Основи нумерології':
        update.message.reply_text("Надаю матеріали по основах нумерології: [Посилання](https://example.com/numology-basics)", parse_mode='Markdown')
    elif category == 'Розрахунок чисел':
        update.message.reply_text("Детальний розрахунок чисел: [Посилання](https://example.com/calculate-numbers)", parse_mode='Markdown')
    elif category == 'Значення чисел':
        update.message.reply_text("Значення нумерологічних чисел: [Посилання](https://example.com/number-meanings)", parse_mode='Markdown')
    elif category == 'Інтерактивні уроки':
        update.message.reply_text("Перегляньте наші інтерактивні уроки: [Посилання](https://example.com/interactive-lessons)", parse_mode='Markdown')
    else:
        update.message.reply_text("Будь ласка, виберіть одну з доступних категорій.")
    # Показати головне меню після навчання
    main_menu(update, context)
    return ConversationHandler.END

def test(update: Update, context: CallbackContext) -> int:
    """Обробник команди /test"""
    keyboard = [['Тест на знання нумерології', 'Визначення вашого числа'], ['Вихід']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    update.message.reply_text(
        "Виберіть тест для проходження:",
        reply_markup=reply_markup
    )
    return TEST_SELECTION

def test_selection_received(update: Update, context: CallbackContext) -> int:
    selection = update.message.text
    if selection == 'Тест на знання нумерології':
        context.user_data['test'] = 'knowledge'
        update.message.reply_text("Питання 1: Що таке число Життєвого Шляху?")
        return TEST_QUESTION
    elif selection == 'Визначення вашого числа':
        context.user_data['test'] = 'number'
        update.message.reply_text("Введіть своє повне ім'я для визначення числа:")
        return TEST_NUMBER
    elif selection == 'Вихід':
        update.message.reply_text("Вихід з тесту.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    else:
        update.message.reply_text("Будь ласка, виберіть одну з доступних опцій.")
        return TEST_SELECTION

def test_question_received(update: Update, context: CallbackContext) -> int:
    answer = update.message.text.lower()
    correct_answer = "число життєвого шляху визначає життєвий шлях та цілі користувача"
    if answer == correct_answer:
        update.message.reply_text("Правильно! Продовжуйте.")
        # Додайте наступні питання тут
    else:
        update.message.reply_text("Неправильна відповідь. Спробуйте ще раз.")
    return TEST_QUESTION  # Залишаємо в стані TEST_QUESTION для повтору

def test_number_received(update: Update, context: CallbackContext) -> int:
    name = update.message.text.strip()
    if not validate_name(name):
        update.message.reply_text(
            "Будь ласка, введіть коректне ім'я (тільки літери та пробіли)."
        )
        return TEST_NUMBER
    number = calculate_expression_number(name)
    update.message.reply_text(f"Ваше число Вираження: {number}")
    # Додайте аналіз числа
    return ConversationHandler.END

def lucky(update: Update, context: CallbackContext) -> int:
    """Обробник команди /lucky"""
    keyboard = [['Сьогодні', 'Тиждень', 'Місяць'], ['Вихід']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    update.message.reply_text(
        "Виберіть період для визначення щасливого числа:",
        reply_markup=reply_markup
    )
    return LUCKY_SELECTION

def lucky_selection_received(update: Update, context: CallbackContext) -> int:
    selection = update.message.text
    if selection == 'Сьогодні':
        lucky_number = calculate_lucky_number(context.user_data, period='day')
        update.message.reply_text(f"Ваше щасливе число на сьогодні: {lucky_number}")
    elif selection == 'Тиждень':
        lucky_number = calculate_lucky_number(context.user_data, period='week')
        update.message.reply_text(f"Ваше щасливе число на тиждень: {lucky_number}")
    elif selection == 'Місяць':
        lucky_number = calculate_lucky_number(context.user_data, period='month')
        update.message.reply_text(f"Ваше щасливе число на місяць: {lucky_number}")
    elif selection == 'Вихід':
        update.message.reply_text("Вихід з генератора щасливих чисел.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    else:
        update.message.reply_text("Будь ласка, виберіть одну з доступних опцій.")
    return ConversationHandler.END

def share(update: Update, context: CallbackContext) -> None:
    """Обробник команди /share"""
    chat_id = update.message.chat_id
    analysis = context.user_data.get('latest_analysis', 'No analysis available.')
    share_text = f"Мій нумерологічний аналіз:\n{analysis}\n#NumerologyGuruBot"
    share_url = f"https://telegram.me/share/url?url={share_text}&text=Поділюсь своїм нумерологічним аналізом!"
    
    keyboard = [
        [InlineKeyboardButton("Поділитися на Facebook", url=f"https://facebook.com/sharer/sharer.php?u={share_url}")],
        [InlineKeyboardButton("Поділитися на Twitter", url=f"https://twitter.com/intent/tweet?text={share_text}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text("Поділіться своїм аналізом:", reply_markup=reply_markup)

def language_selection_received(update: Update, context: CallbackContext) -> int:
    """Обробник вибору мови"""
    selection = update.message.text
    session = Session()
    user = update.message.from_user
    db_user = session.query(User).filter_by(telegram_id=user.id).first()
    if not db_user:
        db_user = User(telegram_id=user.id)
        session.add(db_user)
    
    if selection == 'Українська':
        db_user.language = 'uk'
        update.message.reply_text("Мова змінена на українську.", reply_markup=ReplyKeyboardRemove())
    elif selection == 'English':
        db_user.language = 'en'
        update.message.reply_text("Language changed to English.", reply_markup=ReplyKeyboardRemove())
    elif selection == 'Вихід':
        update.message.reply_text("Вихід з налаштувань мови.", reply_markup=ReplyKeyboardRemove())
        session.close()
        return ConversationHandler.END
    else:
        update.message.reply_text("Будь ласка, виберіть одну з доступних мов.")
        session.close()
        return LANGUAGE_SELECTION
    
    session.commit()
    session.close()
    # Показати головне меню після зміни мови
    main_menu(update, context)
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

def main_menu(update: Update, context: CallbackContext) -> None:
    """Показує головне меню бота"""
    keyboard = [
        [InlineKeyboardButton("Почати Аналіз", callback_data='start_analysis')],
        [InlineKeyboardButton("Історія Аналізів", callback_data='history')],
        [InlineKeyboardButton("Навчальні Матеріали", callback_data='learn')],
        [InlineKeyboardButton("Сумісність", callback_data='compatibility')],
        [InlineKeyboardButton("Щасливі Числа", callback_data='lucky')],
        [InlineKeyboardButton("Поділитися Аналізом", callback_data='share')],
        [InlineKeyboardButton("Мова", callback_data='language')],
        [InlineKeyboardButton("Допомога", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Виберіть опцію:", reply_markup=reply_markup)

def button_handler(update: Update, context: CallbackContext) -> None:
    """Обробник натискань кнопок"""
    query = update.callback_query
    query.answer()
    
    if query.data == 'start_analysis':
        analyze(update, context)
    elif query.data == 'history':
        history(update, context)
    elif query.data == 'learn':
        learn(update, context)
    elif query.data == 'compatibility':
        compatibility(update, context)
    elif query.data == 'lucky':
        lucky(update, context)
    elif query.data == 'share':
        share(update, context)
    elif query.data == 'language':
        set_language(update, context)
    elif query.data == 'help':
        help_command(update, context)

def set_language(update: Update, context: CallbackContext) -> int:
    """Команда для вибору мови"""
    keyboard = [['Українська', 'English'], ['Вихід']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    update.message.reply_text(
        "Виберіть мову взаємодії:",
        reply_markup=reply_markup
    )
    return LANGUAGE_SELECTION

def handle_update(update: Update, context: CallbackContext) -> None:
    """Обробник оновлень з Telegram"""
    dispatcher.process_update(update)

# ConversationHandler для аналізу
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start), CommandHandler('analyze', analyze)],
    
    states={
        NAME: [MessageHandler(Filters.text & ~Filters.command, name_received)],
        DOB: [MessageHandler(Filters.text & ~Filters.command, dob_received)],
        PARTNER_NAME: [MessageHandler(Filters.text & ~Filters.command, relationship_name_received)],
        RELATIONSHIP_DOB: [MessageHandler(Filters.text & ~Filters.command, relationship_dob_received)],
        LANGUAGE_SELECTION: [MessageHandler(Filters.text & ~Filters.command, language_selection_received)],
        TEST_SELECTION: [MessageHandler(Filters.text & ~Filters.command, test_selection_received)],
        TEST_QUESTION: [MessageHandler(Filters.text & ~Filters.command, test_question_received)],
        TEST_NUMBER: [MessageHandler(Filters.text & ~Filters.command, test_number_received)],
        LUCKY_SELECTION: [MessageHandler(Filters.text & ~Filters.command, lucky_selection_received)],
    },
    
    fallbacks=[CommandHandler('cancel', cancel)],
)

# ConversationHandler для навчання
learn_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('learn', learn)],
    
    states={
        LANGUAGE_SELECTION: [MessageHandler(Filters.text & ~Filters.command, learn_category_received)],
    },
    
    fallbacks=[CommandHandler('cancel', cancel)],
)

# ConversationHandler для тесту
test_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('test', test)],
    
    states={
        TEST_SELECTION: [MessageHandler(Filters.text & ~Filters.command, test_selection_received)],
        TEST_QUESTION: [MessageHandler(Filters.text & ~Filters.command, test_question_received)],
        TEST_NUMBER: [MessageHandler(Filters.text & ~Filters.command, test_number_received)],
    },
    
    fallbacks=[CommandHandler('cancel', cancel)],
)

# ConversationHandler для мовного вибору
language_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('language', set_language)],
    
    states={
        LANGUAGE_SELECTION: [MessageHandler(Filters.regex('^(Українська|English|Вихід)$'), language_selection_received)],
    },
    
    fallbacks=[CommandHandler('cancel', cancel)],
)

# Додавання обробників до диспетчера
dispatcher.add_handler(conv_handler)
dispatcher.add_handler(learn_conv_handler)
dispatcher.add_handler(test_conv_handler)
dispatcher.add_handler(language_conv_handler)
dispatcher.add_handler(CommandHandler("help", help_command))
dispatcher.add_handler(CallbackQueryHandler(button_handler))

def send_daily_forecast(chat_id, life_path):
    """Функція для надсилання щоденного прогнозу"""
    forecast = f"Щоденний прогноз для вас: Сьогодні ваше число Життєвого Шляху {life_path} впливає на вашу енергію та настрій. Будьте відкриті до нових можливостей!"
    bot.send_message(chat_id=chat_id, text=forecast)

def schedule_daily_forecast(user_id, chat_id, life_path, time='09:00'):
    """Функція для планування щоденного прогнозу"""
    hour, minute = map(int, time.split(':'))
    scheduler.add_job(
        send_daily_forecast, 
        'cron', 
        hour=hour, 
        minute=minute, 
        args=[chat_id, life_path],
        id=str(user_id) + '_daily_forecast',
        replace_existing=True
    )

def validate_name(name):
    """Валідація імені (тільки літери та пробіли)"""
    return name.replace(" ", "").isalpha()

def validate_dob(dob):
    """Валідація дати народження у форматі DD-MM-YYYY"""
    try:
        day, month, year = map(int, dob.split('-'))
        datetime.datetime(year, month, day)
        return True
    except ValueError:
        return False

def main() -> None:
    """Основна функція запуску бота"""
    # Ініціалізація Flask-додатку
    @app.route('/webhook', methods=['POST'])
    def webhook():
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
        return 'ok'

    # Запуск Flask-додатку
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

if __name__ == '__main__':
    main()
