from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

# Ініціалізація базового класу
Base = declarative_base()

# Модель для заявки
class Request(Base):
    __tablename__ = 'requests'
    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(Text, nullable=False)
    address = Column(String, nullable=True)
    priority = Column(String, nullable=False, default="Звичайний")
    status = Column(String, nullable=False, default="Нова")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Модель для користувачів
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String, nullable=True)
    name = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)

# Модель для зв'язку заявок із відповідальними користувачами
class RequestAssignment(Base):
    __tablename__ = 'request_assignments'
    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(Integer, ForeignKey('requests.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

# Модель для коментарів
class Comment(Base):
    __tablename__ = 'comments'
    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(Integer, ForeignKey('requests.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    comment_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Ініціалізація бази даних
def init_db():
    # Використовується SQLite. Для MySQL або PostgreSQL змініть рядок підключення.
    engine = create_engine('sqlite:///support_bot.db')
    Base.metadata.create_all(engine)
    return engine

# Створення сесії для роботи з базою даних
engine = init_db()
Session = sessionmaker(bind=engine)
session = Session()
