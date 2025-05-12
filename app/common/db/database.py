# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
import logging

from ..config import DATABASE_URL

logger = logging.getLogger(__name__)

try:
    # echo=True полезно для отладки, показывает генерируемые SQL запросы
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)

    # sessionmaker создает фабрику сессий
    # autocommit=False и autoflush=False - стандартные настройки для ORM
    SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # scoped_session обеспечивает уникальную сессию для каждого потока (важно для GUI приложений)
    SessionLocal = scoped_session(SessionFactory)

    # Base - базовый класс для всех ORM моделей
    Base = declarative_base()
    logger.info("Database engine and session factory created successfully.")

except Exception as e:
    logger.error(f"Failed to connect to database or create session factory: {e}")
    # В реальном приложении здесь нужна более надежная обработка ошибок
    # Например, выход из приложения или попытка переподключения
    raise # Перевыброс исключения, чтобы приложение знало о проблеме


def get_db():
    """ Функция-генератор для получения сессии БД """
    db = SessionLocal()
    try:
        yield db
    finally:
        # Закрывает сессию после использования
        # SessionLocal.remove() или db.close()
        SessionLocal.remove()

def init_db():
    """
    Создает все таблицы в базе данных, определенные через Base.metadata.
    Вызывать только если таблицы еще не существуют.
    Т.к. у тебя БД уже есть, этот вызов НЕ НУЖЕН, но полезно иметь.
    """
    # Импортируем модели, чтобы SQLAlchemy знал о них
    from . import models
    try:
        logger.info("Initializing database schema (creating tables if they don't exist)...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema initialized successfully.")
    except Exception as e:
        logger.error(f"Error during schema initialization: {e}")
        raise