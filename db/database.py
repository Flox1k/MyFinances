# -*- coding: utf-8 -*-
"""
Инициализация и управление базой данных SQLite с использованием SQLAlchemy

Функции:
- init_db(): создание таблиц при первом запуске
- get_session(): получение сессии БД для запросов
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from config import DATABASE_URL
from models.models import Base


# Создание движка SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Для SQLite
    echo=False  # Установите True для отладки SQL-запросов
)

# Фабрика сессий
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def run_migrations(eng):
    """
    Применить миграции схемы БД (для добавления новых колонок к существующим таблицам).
    Использует PRAGMA table_info для проверки наличия колонок перед ALTER TABLE.
    """
    with eng.connect() as conn:
        # Добавить category_id в transactions, если отсутствует
        result = conn.execute(__import__("sqlalchemy").text("PRAGMA table_info(transactions)"))
        cols = [row[1] for row in result]
        if "category_id" not in cols:
            conn.execute(__import__("sqlalchemy").text(
                "ALTER TABLE transactions ADD COLUMN category_id INTEGER REFERENCES categories(id)"
            ))
            conn.commit()
            print("✓ Миграция: добавлена колонка category_id в transactions")


def init_db(create_admin: bool = True):
    """
    Инициализация БД: создание всех таблиц на основе моделей
    Вызывается один раз при запуске приложения
    
    Args:
        create_admin (bool): создавать ли администратора при первом запуске
    """
    Base.metadata.create_all(bind=engine)
    run_migrations(engine)
    print("✓ База данных инициализирована")
    
    if create_admin:
        create_admin_user()


def create_admin_user():
    """
    Создать пользователя-администратора, если он ещё не существует
    
    Учетные данные:
    - Username: Flox1kAdmin
    - Password: Admin2811066!
    """
    from models.models import User
    from utils.helpers import hash_password
    from services.services import ExchangeRateService
    
    session = SessionLocal()
    try:
        # Проверить, существует ли админ
        admin = session.query(User).filter_by(username="Flox1kAdmin").first()
        
        if not admin:
            # Создать администратора
            admin_password_hash = hash_password("Admin2811066!")
            admin_user = User(
                username="Flox1kAdmin",
                email="admin@myfinances.local",
                password_hash=admin_password_hash
            )
            session.add(admin_user)
            session.commit()
            print("✓ Администратор Flox1kAdmin создан")
            
            # Инициализировать дефолтные курсы для админа
            ExchangeRateService.init_default_rates(admin_user.id)
        else:
            print("✓ Администратор уже существует")
    except Exception as e:
        print(f"⚠️  Ошибка при создании администратора: {e}")
    finally:
        session.close()


def get_session() -> Session:
    """
    Получить сессию НА СЛЕДУЮЩИЙ SQL-запрос
    
    Пример использования:
        session = get_session()
        user = session.query(User).filter_by(username="ivan").first()
        session.close()
    
    Или лучше с контекстным менеджером:
        with get_session() as session:
            user = session.query(User).filter_by(username="ivan").first()
            # сессия закроется автоматически
    
    Returns:
        Session: объект сессии SQLAlchemy
    """
    return SessionLocal()


def close_session(session: Session):
    """Закрыть сессию БД"""
    if session:
        session.close()
