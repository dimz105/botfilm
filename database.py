# bot/database.py

from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import os
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    language = Column(String, default='uk')
    analyses = relationship("UserAnalysis", back_populates="user")

class UserAnalysis(Base):
    __tablename__ = 'user_analyses'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String, nullable=False)
    dob = Column(String, nullable=False)
    life_path = Column(Integer, nullable=False)
    expression = Column(Integer, nullable=False)
    soul = Column(Integer, nullable=False)
    personality = Column(Integer, nullable=False)
    improvement = Column(Integer, nullable=False)
    destiny = Column(Integer, nullable=True)
    career = Column(Integer, nullable=True)
    relationship = Column(Integer, nullable=True)
    lucky_day = Column(Integer, nullable=True)
    lucky_week = Column(Integer, nullable=True)
    lucky_month = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="analyses")

# Налаштування бази даних
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///numerology.db")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)
