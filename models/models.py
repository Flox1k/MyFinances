# -*- coding: utf-8 -*-
"""
Модели данных приложения MyFinances (SQLAlchemy)

Таблицы:
- User: пользователи приложения
- Wallet: кошельки пользователей
- Transaction: транзакции (доходы и расходы)
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Boolean, Date, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum
from config import now_almaty

Base = declarative_base()


class TransactionType(enum.Enum):
    """Типы транзакций"""
    INCOME = "income"      # Доход
    EXPENSE = "expense"    # Расход


class DebtType(enum.Enum):
    """Типы долговых операций"""
    GAVE = "gave"        # Дал в долг (мне должны)
    TOOK = "took"        # Взял в долг (я должен)


class GoalTransactionType(enum.Enum):
    """Типы операций по цели"""
    ADD = "add"          # Добавление суммы
    SUBTRACT = "subtract"  # Убавление суммы


class User(Base):
    """
    Модель пользователя
    
    Атрибуты:
        id: уникальный идентификатор
        username: имя пользователя (уникальное)
        email: адрес электронной почты
        password_hash: хеш пароля (не пароль в открытом виде)
        created_at: дата создания аккаунта
        wallets: связь с кошельками пользователя (one-to-many)
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=now_almaty, nullable=False)
    
    # Связь с кошельками
    wallets = relationship("Wallet", back_populates="user", cascade="all, delete-orphan")
    # Связь с курсами валют
    exchange_rates = relationship("ExchangeRate", back_populates="user", cascade="all, delete-orphan")
    # Связь с целями
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    # Связь с долгами
    debts = relationship("Debt", back_populates="user", cascade="all, delete-orphan")
    # Связь с категориями
    categories = relationship("Category", back_populates="user", cascade="all, delete-orphan")
    # Связь с бюджетами
    budgets = relationship("Budget", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"


class Wallet(Base):
    """
    Модель кошелька
    
    Атрибуты:
        id: уникальный идентификатор
        user_id: id владельца кошелька (внешний ключ)
        name: название кошелька (например, "Основной", "Сберегательный")
        balance: текущий баланс (сумма всех транзакций)
        currency: валюта кошелька (KZT, USD, EUR и т.д.)
        created_at: дата создания кошелька
        updated_at: дата последнего обновления баланса
        user: связь с пользователем (many-to-one)
        transactions: связь с транзакциями (one-to-many)
    """
    __tablename__ = "wallets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    balance = Column(Float, default=0.0, nullable=False)
    currency = Column(String(3), default="KZT", nullable=False)
    created_at = Column(DateTime, default=now_almaty, nullable=False)
    updated_at = Column(DateTime, default=now_almaty, onupdate=now_almaty, nullable=False)
    
    # Связи
    user = relationship("User", back_populates="wallets")
    transactions = relationship("Transaction", back_populates="wallet", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Wallet(id={self.id}, user_id={self.user_id}, name={self.name}, balance={self.balance})>"


class Transaction(Base):
    """
    Модель транзакции (доход или расход)
    
    Атрибуты:
        id: уникальный идентификатор
        wallet_id: id кошелька (внешний ключ)
        type: тип транзакции (income или expense)
        amount: сумма операции (в валюте кошелька)
        description: комментарий/описание транзакции
        created_at: дата и время операции
        updated_at: дата последнего изменения
        wallet: связь с кошельком (many-to-one)
    """
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False, index=True)
    type = Column(Enum(TransactionType), nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String(500), default="", nullable=False)
    created_at = Column(DateTime, default=now_almaty, nullable=False, index=True)
    updated_at = Column(DateTime, default=now_almaty, onupdate=now_almaty, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

    # Связи
    wallet = relationship("Wallet", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, wallet_id={self.wallet_id}, type={self.type}, amount={self.amount})>"


class ExchangeRate(Base):
    """
    Модель курса валют (сохраняется в БД для каждого пользователя)
    
    Атрибуты:
        id: уникальный идентификатор
        user_id: id пользователя (внешний ключ)
        from_currency: валюта источника (например, USD)
        to_currency: валюта назначения (например, KZT)
        rate: курс обмена (сколько to_currency за 1 from_currency)
        last_updated: дата последнего обновления курса
        user: связь с пользователем (many-to-one)
    """
    __tablename__ = "exchange_rates"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    from_currency = Column(String(3), nullable=False)
    to_currency = Column(String(3), nullable=False)
    rate = Column(Float, nullable=False)
    last_updated = Column(DateTime, default=now_almaty, onupdate=now_almaty, nullable=False)
    
    # Связь с пользователем
    user = relationship("User", back_populates="exchange_rates")
    
    def __repr__(self):
        return f"<ExchangeRate(id={self.id}, user_id={self.user_id}, {self.from_currency}->{self.to_currency}: {self.rate})>"


class Goal(Base):
    """
    Модель финансовой цели пользователя

    Атрибуты:
        id: уникальный идентификатор
        user_id: id владельца (внешний ключ)
        name: название цели
        target_amount: целевая сумма
        current_amount: текущая накопленная сумма
        currency: валюта цели
        start_date: дата начала
        end_date: дата окончания
        is_tracked: отслеживается ли на главном экране (только одна)
        description: описание/заметка
        created_at: дата создания
        user: связь с пользователем (many-to-one)
    """
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0.0, nullable=False)
    currency = Column(String(3), default="KZT", nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_tracked = Column(Boolean, default=False, nullable=False)
    description = Column(String(500), default="", nullable=False)
    created_at = Column(DateTime, default=now_almaty, nullable=False)

    # Связь с пользователем
    user = relationship("User", back_populates="goals")
    # Связь с транзакциями по цели
    goal_transactions = relationship("GoalTransaction", back_populates="goal", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Goal(id={self.id}, user_id={self.user_id}, name={self.name}, target={self.target_amount})>"


class GoalTransaction(Base):
    """
    Транзакция по цели (добавление / убавление накопленной суммы)

    Атрибуты:
        id: уникальный идентификатор
        goal_id: id цели (внешний ключ)
        type: тип операции (add / subtract)
        amount: сумма операции (всегда положительная)
        created_at: дата и время операции
    """
    __tablename__ = "goal_transactions"

    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=False, index=True)
    type = Column(Enum(GoalTransactionType), nullable=False)
    amount = Column(Float, nullable=False)
    created_at = Column(DateTime, default=now_almaty, nullable=False, index=True)

    goal = relationship("Goal", back_populates="goal_transactions")

    def __repr__(self):
        return f"<GoalTransaction(id={self.id}, goal_id={self.goal_id}, type={self.type}, amount={self.amount})>"


class Debt(Base):
    """
    Модель кейса долга (аналог кошелька)

    Каждый кейс — это человек/организация, которому вы должны или кто должен вам.
    balance > 0 → вам должны, balance < 0 → вы должны
    """
    __tablename__ = "debts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)  # имя человека / название
    balance = Column(Float, default=0.0, nullable=False)
    currency = Column(String(3), default="KZT", nullable=False)
    created_at = Column(DateTime, default=now_almaty, nullable=False)
    updated_at = Column(DateTime, default=now_almaty, onupdate=now_almaty, nullable=False)

    user = relationship("User", back_populates="debts")
    transactions = relationship("DebtTransaction", back_populates="debt", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Debt(id={self.id}, name={self.name}, balance={self.balance})>"


class DebtTransaction(Base):
    """
    Транзакция по долгу (дал / взял в долг)
    """
    __tablename__ = "debt_transactions"

    id = Column(Integer, primary_key=True, index=True)
    debt_id = Column(Integer, ForeignKey("debts.id"), nullable=False, index=True)
    type = Column(Enum(DebtType), nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String(500), default="", nullable=False)
    created_at = Column(DateTime, default=now_almaty, nullable=False, index=True)
    updated_at = Column(DateTime, default=now_almaty, onupdate=now_almaty, nullable=False)

    debt = relationship("Debt", back_populates="transactions")

    def __repr__(self):
        return f"<DebtTransaction(id={self.id}, debt_id={self.debt_id}, type={self.type}, amount={self.amount})>"


class Category(Base):
    """
    Категория транзакции (пользовательская)

    Атрибуты:
        id: уникальный идентификатор
        user_id: id владельца (внешний ключ)
        name: название категории
        color: цвет-идентификатор в HEX (например "#6366f1")
        is_default: категория по умолчанию для новых транзакций
        created_at: дата создания
    """
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    color = Column(String(7), default="#6366f1", nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=now_almaty, nullable=False)

    user = relationship("User", back_populates="categories")
    keywords = relationship("CategoryKeyword", back_populates="category", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="category")
    budgets = relationship("Budget", back_populates="category", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Category(id={self.id}, user_id={self.user_id}, name={self.name})>"


class CategoryKeyword(Base):
    """
    Ключевое слово для авто-классификации транзакции по категории

    Атрибуты:
        id: уникальный идентификатор
        category_id: id категории (внешний ключ, cascade delete)
        keyword: слово/фраза в нижнем регистре
    """
    __tablename__ = "category_keywords"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    keyword = Column(String(100), nullable=False)

    category = relationship("Category", back_populates="keywords")

    def __repr__(self):
        return f"<CategoryKeyword(id={self.id}, category_id={self.category_id}, keyword={self.keyword})>"


class Budget(Base):
    """
    Месячный бюджет (лимит расходов) для категории

    Атрибуты:
        id: уникальный идентификатор
        user_id: id владельца (внешний ключ)
        category_id: id категории (внешний ключ, cascade delete)
        year: год расчётного периода
        month: месяц расчётного периода (1–12)
        limit_amount: лимит расходов за период
        warning_threshold: порог предупреждения в процентах (по умолчанию 80)
    """
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    limit_amount = Column(Float, nullable=False)
    warning_threshold = Column(Float, default=80.0, nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "category_id", "year", "month", name="uq_budget_user_cat_month"),)

    user = relationship("User", back_populates="budgets")
    category = relationship("Category", back_populates="budgets")

    def __repr__(self):
        return f"<Budget(id={self.id}, category_id={self.category_id}, {self.year}/{self.month}, limit={self.limit_amount})>"

