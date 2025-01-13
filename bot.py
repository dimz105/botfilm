from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, CallbackContext, ConversationHandler, MessageHandler, filters
from sqlalchemy.orm import sessionmaker
from models import init_db, Request, User, RequestAssignment, Comment

# Ініціалізація бази даних
engine = init_db()
Session = sessionmaker(bind=engine)
session = Session()

# Стан для ConversationHandler
CREATE_REQUEST, ASSIGN_REQUEST, SET_PRIORITY, SET_TYPE, CONFIRM_REQUEST = range(5)

# Команда /start
async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    if not session.query(User).filter_by(telegram_id=user.id).first():
        session.add(User(telegram_id=user.id, username=user.username, name=user.full_name))
        session.commit()
    await update.message.reply_text("Привіт! Я бот для технічної підтримки. Введіть /help для списку команд.")

# Команда /help
async def help_command(update: Update, context: CallbackContext):
    commands = (
        "/create_request - Створити нову заявку\n"
        "/assign - Призначити відповідальних\n"
        "/set_status - Змінити статус заявки\n"
        "/request_info - Переглянути інформацію про заявку\n"
        "/comment - Додати коментар до заявки\n"
        "/list_requests - Переглянути всі заявки\n"
        "/reports - Отримати звіт про заявки"
    )
    await update.message.reply_text(f"Доступні команди:\n{commands}")

# Команда /create_request
async def create_request(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Немає інтернету", callback_data="no_internet"),
         InlineKeyboardButton("Проблеми з Wi-Fi", callback_data="wifi_issues")],
        [InlineKeyboardButton("Пошкодження кабелю", callback_data="cable_damage")]
    ]
    await update.message.reply_text(
        "Оберіть тип проблеми:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SET_TYPE

async def set_type(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    context.user_data['type'] = query.data

    keyboard = [
        [InlineKeyboardButton("Терміновий", callback_data="urgent"),
         InlineKeyboardButton("Високий", callback_data="high")],
        [InlineKeyboardButton("Звичайний", callback_data="normal"),
         InlineKeyboardButton("Низький", callback_data="low")]
    ]
    await query.edit_message_text(
        "Оберіть пріоритет:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SET_PRIORITY

async def set_priority(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    context.user_data['priority'] = query.data

    await query.edit_message_text("Введіть опис проблеми:")
    return CREATE_REQUEST

async def save_request(update: Update, context: CallbackContext):
    description = update.message.text
    context.user_data['description'] = description

    new_request = Request(
        description=context.user_data['description'],
        address="Не вказано",
        priority=context.user_data['priority'],
        status="Нова"
    )
    session.add(new_request)
    session.commit()

    await update.message.reply_text(
        f"Заявку створено з ID {new_request.id}. Тип: {context.user_data['type']}, Пріоритет: {context.user_data['priority']}"
    )
    return ConversationHandler.END

# Команда /reports
async def reports(update: Update, context: CallbackContext):
    total_requests = session.query(Request).count()
    completed_requests = session.query(Request).filter_by(status="Виконано").count()
    in_progress_requests = session.query(Request).filter_by(status="В роботі").count()

    types_stats = session.query(Request).with_entities(Request.description, func.count(Request.id)).group_by(Request.description).all()

    types_report = "\n".join([f"{t[0]}: {t[1]}" for t in types_stats])

    report = (
        f"Загальна кількість заявок: {total_requests}\n"
        f"Виконано: {completed_requests}\n"
        f"В роботі: {in_progress_requests}\n"
        f"Типи заявок:\n{types_report}"
    )
    await update.message.reply_text(report)

# Основний блок для запуску бота
application = Application.builder().token("YOUR_TELEGRAM_BOT_TOKEN").build()

# Реєстрація хендлерів
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(ConversationHandler(
    entry_points=[CommandHandler("create_request", create_request)],
    states={
        SET_TYPE: [CallbackQueryHandler(set_type)],
        SET_PRIORITY: [CallbackQueryHandler(set_priority)],
        CREATE_REQUEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_request)]
    },
    fallbacks=[]
))
application.add_handler(CommandHandler("reports", reports))

if __name__ == "__main__":
    application.run_polling()
