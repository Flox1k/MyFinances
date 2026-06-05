# -*- coding: utf-8 -*-
"""
Репозитории для работы с БД (Repository Pattern)

Классы:
- UserRepository: работа с пользователями
- WalletRepository: работа с кошельками
- TransactionRepository: работа с транзакциями

Репозитории инкапсулируют SQL-логику и используются Services
"""

from sqlalchemy.orm import Session, joinedload
from models.models import User, Wallet, Transaction, TransactionType, ExchangeRate, Goal, GoalTransaction, GoalTransactionType, Debt, DebtTransaction, DebtType, Category, CategoryKeyword, Budget
from config import now_almaty


class UserRepository:
    """
    Репозиторий для работы с пользователями
    Содержит методы для CRUD операций с пользователями
    """
    
    def __init__(self, session: Session):
        """
        Args:
            session: сессия SQLAlchemy
        """
        self.session = session
    
    def create_user(self, username: str, email: str, password_hash: str) -> User:
        """
        Создать нового пользователя
        
        Args:
            username: имя пользователя
            email: email адрес
            password_hash: хеш пароля
            
        Returns:
            User: созданный пользователь
            
        Raises:
            Exception: если пользователь с таким именем уже существует
        """
        user = User(username=username, email=email, password_hash=password_hash)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user
    
    def get_user_by_id(self, user_id: int) -> User:
        """
        Получить пользователя по ID
        
        Args:
            user_id: id пользователя
            
        Returns:
            User или None если не найден
        """
        return self.session.query(User).filter_by(id=user_id).first()
    
    def get_user_by_username(self, username: str) -> User:
        """
        Получить пользователя по имени пользователя
        
        Args:
            username: имя пользователя
            
        Returns:
            User или None если не найден
        """
        return self.session.query(User).filter_by(username=username).first()
    
    def get_user_by_email(self, email: str) -> User:
        """
        Получить пользователя по email
        
        Args:
            email: адрес электронной почты
            
        Returns:
            User или None если не найден
        """
        return self.session.query(User).filter_by(email=email).first()
    
    def get_all_users(self) -> list[User]:
        """
        Получить всех пользователей (для админки)
        
        Returns:
            list: список всех пользователей
        """
        return self.session.query(User).all()
    
    def update_user(self, user_id: int, **kwargs) -> User:
        """
        Обновить данные пользователя
        
        Args:
            user_id: id пользователя
            **kwargs: поля для обновления (username, email, password_hash)
            
        Returns:
            User: обновленный пользователь
        """
        user = self.get_user_by_id(user_id)
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            self.session.commit()
            self.session.refresh(user)
        return user
    
    def delete_user(self, user_id: int) -> bool:
        """
        Удалить пользователя (и все связанные кошельки и транзакции)
        
        Args:
            user_id: id пользователя
            
        Returns:
            bool: True если успешно, False иначе
        """
        user = self.get_user_by_id(user_id)
        if user:
            self.session.delete(user)
            self.session.commit()
            return True
        return False


class WalletRepository:
    """
    Репозиторий для работы с кошельками
    Содержит методы для CRUD операций с кошельками
    """
    
    def __init__(self, session: Session):
        """
        Args:
            session: сессия SQLAlchemy
        """
        self.session = session
    
    def create_wallet(self, user_id: int, name: str, currency: str = "KZT") -> Wallet:
        """
        Создать новый кошелёк
        
        Args:
            user_id: ID пользователя
            name: название кошелька
            currency: валюта (по умолчанию KZT)
            
        Returns:
            Wallet: созданный кошелек
        """
        wallet = Wallet(user_id=user_id, name=name, currency=currency, balance=0.0)
        self.session.add(wallet)
        self.session.commit()
        self.session.refresh(wallet)
        return wallet
    
    def get_wallet_by_id(self, wallet_id: int) -> Wallet:
        """
        Получить кошелёк по ID
        
        Args:
            wallet_id: id кошелька
            
        Returns:
            Wallet или None если не найден
        """
        return self.session.query(Wallet).filter_by(id=wallet_id).first()
    
    def get_wallets_by_user(self, user_id: int) -> list[Wallet]:
        """
        Получить все кошельки пользователя
        
        Args:
            user_id: id пользователя
            
        Returns:
            list: список кошельков пользователя
        """
        return self.session.query(Wallet).filter_by(user_id=user_id).all()
    
    def get_total_balance(self, user_id: int) -> float:
        """
        Получить общий баланс всех кошельков пользователя (ВАЖНО: все в валюте первого кошелька!)
        
        Args:
            user_id: id пользователя
            
        Returns:
            float: сумма всех балансов
        """
        wallets = self.get_wallets_by_user(user_id)
        total = sum(wallet.balance for wallet in wallets)
        return total
    
    def update_wallet(self, wallet_id: int, **kwargs) -> Wallet:
        """
        Обновить данные кошелька
        
        Args:
            wallet_id: id кошелька
            **kwargs: поля для обновления (name, balance, currency)
            
        Returns:
            Wallet: обновленный кошелек
        """
        wallet = self.get_wallet_by_id(wallet_id)
        if wallet:
            for key, value in kwargs.items():
                if hasattr(wallet, key):
                    setattr(wallet, key, value)
            wallet.updated_at = now_almaty()
            self.session.commit()
            self.session.refresh(wallet)
        return wallet
    
    def delete_wallet(self, wallet_id: int) -> bool:
        """
        Удалить кошелёк (и все его транзакции)
        
        Args:
            wallet_id: id кошелька
            
        Returns:
            bool: True если успешно, False иначе
        """
        wallet = self.get_wallet_by_id(wallet_id)
        if wallet:
            self.session.delete(wallet)
            self.session.commit()
            return True
        return False
    
    def update_balance(self, wallet_id: int, amount: float):
        """
        Обновить баланс кошелька на сумму (может быть положительной или отрицательной)
        
        Args:
            wallet_id: id кошелька
            amount: сумма для добавления (может быть отрицательной для вычитания)
            
        Returns:
            Wallet: обновленный кошелек с новым балансом
        """
        wallet = self.get_wallet_by_id(wallet_id)
        if wallet:
            wallet.balance += amount
            wallet.updated_at = now_almaty()
            self.session.commit()
            self.session.refresh(wallet)
        return wallet


class TransactionRepository:
    """
    Репозиторий для работы с транзакциями
    Содержит методы для CRUD операций с транзакциями
    """
    
    def __init__(self, session: Session):
        """
        Args:
            session: сессия SQLAlchemy
        """
        self.session = session
    
    def create_transaction(self, wallet_id: int, transaction_type: TransactionType, 
                          amount: float, description: str = "") -> Transaction:
        """
        Создать новую транзакцию
        
        Args:
            wallet_id: id кошелька
            transaction_type: тип транзакции (income или expense)
            amount: сумма операции
            description: комментарий
            
        Returns:
            Transaction: созданная транзакция
        """
        transaction = Transaction(
            wallet_id=wallet_id,
            type=transaction_type,
            amount=amount,
            description=description
        )
        self.session.add(transaction)
        self.session.commit()
        self.session.refresh(transaction)
        return transaction
    
    def get_transaction_by_id(self, transaction_id: int) -> Transaction:
        """
        Получить транзакцию по ID
        
        Args:
            transaction_id: id транзакции
            
        Returns:
            Transaction или None если не найдена
        """
        return self.session.query(Transaction).filter_by(id=transaction_id).first()
    
    def get_transactions_by_wallet(self, wallet_id: int, limit: int = None) -> list[Transaction]:
        """
        Получить все транзакции кошелька (отсортированы по дате убывания)
        
        Args:
            wallet_id: id кошелька
            limit: максимальное количество (None = все)
            
        Returns:
            list: список транзакций
        """
        query = (self.session.query(Transaction)
                 .options(joinedload(Transaction.category))
                 .filter_by(wallet_id=wallet_id)
                 .order_by(Transaction.created_at.desc()))
        if limit:
            query = query.limit(limit)
        return query.all()
    
    def get_transactions_by_type(self, wallet_id: int, 
                                 transaction_type: TransactionType) -> list[Transaction]:
        """
        Получить транзакции кошелька по типу (доход или расход)
        
        Args:
            wallet_id: id кошелька
            transaction_type: тип (income или expense)
            
        Returns:
            list: список транзакций данного типа
        """
        return self.session.query(Transaction).filter_by(
            wallet_id=wallet_id,
            type=transaction_type
        ).order_by(Transaction.created_at.desc()).all()
    
    def delete_transaction(self, transaction_id: int) -> bool:
        """
        Удалить транзакцию и вернуть баланс кошелька
        
        Args:
            transaction_id: id транзакции
            
        Returns:
            bool: True если успешно, False иначе
        """
        transaction = self.get_transaction_by_id(transaction_id)
        if transaction:
            wallet_id = transaction.wallet_id
            amount = transaction.amount
            type_ = transaction.type
            
            # Удалить транзакцию
            self.session.delete(transaction)
            self.session.commit()
            
            # Вернуть баланс: если это был доход, вычесть; если расход, добавить
            return_amount = -amount if type_ == TransactionType.INCOME else amount
            
            # Обновить баланс кошелька
            wallet_repo = WalletRepository(self.session)
            wallet_repo.update_balance(wallet_id, return_amount)
            
            return True
        return False
    
    def update_transaction(self, transaction_id: int, **kwargs) -> Transaction:
        """
        Обновить данные транзакции
        
        Args:
            transaction_id: id транзакции
            **kwargs: поля для обновления (amount, description, type)
            
        Returns:
            Transaction: обновленная транзакция
        """
        transaction = self.get_transaction_by_id(transaction_id)
        if transaction:
            for key, value in kwargs.items():
                if hasattr(transaction, key) and key not in ['wallet_id', 'created_at']:
                    setattr(transaction, key, value)
            transaction.updated_at = now_almaty()
            self.session.commit()
            self.session.refresh(transaction)
        return transaction


class ExchangeRateRepository:
    """
    Репозиторий для работы с курсами валют
    Содержит методы для CRUD операций с курсами, сохранёнными в БД
    """
    
    def __init__(self, session: Session):
        """
        Args:
            session: сессия SQLAlchemy
        """
        self.session = session
    
    def create_rate(self, user_id: int, from_currency: str, 
                   to_currency: str, rate: float) -> ExchangeRate:
        """
        Создать новый курс валют для пользователя
        
        Args:
            user_id: id пользователя
            from_currency: валюта источника (например, USD)
            to_currency: валюта назначения (например, KZT)
            rate: курс обмена
            
        Returns:
            ExchangeRate: созданный курс
        """
        # Проверить дублирование - если уже существует, обновить
        existing = self.session.query(ExchangeRate).filter_by(
            user_id=user_id,
            from_currency=from_currency,
            to_currency=to_currency
        ).first()
        
        if existing:
            existing.rate = rate
            existing.last_updated = now_almaty()
            self.session.commit()
            self.session.refresh(existing)
            return existing
        
        rate_obj = ExchangeRate(
            user_id=user_id,
            from_currency=from_currency,
            to_currency=to_currency,
            rate=rate
        )
        self.session.add(rate_obj)
        self.session.commit()
        self.session.refresh(rate_obj)
        return rate_obj
    
    def get_user_rates(self, user_id: int) -> list[ExchangeRate]:
        """
        Получить все курсы пользователя
        
        Args:
            user_id: id пользователя
            
        Returns:
            list: список курсов
        """
        return self.session.query(ExchangeRate).filter_by(
            user_id=user_id
        ).order_by(ExchangeRate.from_currency, ExchangeRate.to_currency).all()
    
    def get_rate(self, user_id: int, from_curr: str, to_curr: str) -> ExchangeRate:
        """
        Получить конкретный курс для пользователя
        
        Args:
            user_id: id пользователя
            from_curr: валюта источника
            to_curr: валюта назначения
            
        Returns:
            ExchangeRate: курс или None
        """
        return self.session.query(ExchangeRate).filter_by(
            user_id=user_id,
            from_currency=from_curr,
            to_currency=to_curr
        ).first()
    
    def delete_rate(self, rate_id: int) -> bool:
        """
        Удалить курс валют
        
        Args:
            rate_id: id курса
            
        Returns:
            bool: True если успешно, False иначе
        """
        rate = self.session.query(ExchangeRate).filter_by(id=rate_id).first()
        if rate:
            self.session.delete(rate)
            self.session.commit()
            return True
        return False
    
    def delete_user_rate(self, user_id: int, from_curr: str, to_curr: str) -> bool:
        """
        Удалить курс пользователя по валютам
        
        Args:
            user_id: id пользователя
            from_curr: валюта источника
            to_curr: валюта назначения
            
        Returns:
            bool: True если успешно, False иначе
        """
        rate = self.session.query(ExchangeRate).filter_by(
            user_id=user_id,
            from_currency=from_curr,
            to_currency=to_curr
        ).first()
        if rate:
            self.session.delete(rate)
            self.session.commit()
            return True
        return False

class GoalRepository:
    """
    Репозиторий для работы с финансовыми целями
    """

    def __init__(self, session: Session):
        self.session = session

    def create_goal(self, user_id: int, name: str, target_amount: float,
                    currency: str, start_date, end_date,
                    description: str = "") -> Goal:
        goal = Goal(
            user_id=user_id,
            name=name,
            target_amount=target_amount,
            current_amount=0.0,
            currency=currency,
            start_date=start_date,
            end_date=end_date,
            is_tracked=False,
            description=description
        )
        self.session.add(goal)
        self.session.commit()
        self.session.refresh(goal)
        return goal

    def get_goal_by_id(self, goal_id: int) -> Goal:
        return self.session.query(Goal).filter_by(id=goal_id).first()

    def get_goals_by_user(self, user_id: int) -> list:
        return self.session.query(Goal).filter_by(user_id=user_id).order_by(
            Goal.created_at.desc()
        ).all()

    def get_tracked_goal(self, user_id: int) -> Goal:
        return self.session.query(Goal).filter_by(
            user_id=user_id, is_tracked=True
        ).first()

    def set_tracked(self, user_id: int, goal_id: int):
        """Set one goal as tracked (untrack all others first)"""
        self.session.query(Goal).filter_by(user_id=user_id).update({"is_tracked": False})
        goal = self.get_goal_by_id(goal_id)
        if goal:
            goal.is_tracked = True
        self.session.commit()
        if goal:
            self.session.refresh(goal)
        return goal

    def untrack_all(self, user_id: int):
        self.session.query(Goal).filter_by(user_id=user_id).update({"is_tracked": False})
        self.session.commit()

    def update_goal(self, goal_id: int, **kwargs) -> Goal:
        goal = self.get_goal_by_id(goal_id)
        if goal:
            for key, value in kwargs.items():
                if hasattr(goal, key):
                    setattr(goal, key, value)
            self.session.commit()
            self.session.refresh(goal)
        return goal

    def delete_goal(self, goal_id: int) -> bool:
        goal = self.get_goal_by_id(goal_id)
        if goal:
            self.session.delete(goal)
            self.session.commit()
            return True
        return False


class DebtRepository:
    """Репозиторий для работы с кейсами долгов"""

    def __init__(self, session: Session):
        self.session = session

    def create_debt(self, user_id: int, name: str, currency: str = "KZT") -> Debt:
        debt = Debt(user_id=user_id, name=name, balance=0.0, currency=currency)
        self.session.add(debt)
        self.session.commit()
        self.session.refresh(debt)
        return debt

    def get_debt_by_id(self, debt_id: int) -> Debt:
        return self.session.query(Debt).filter_by(id=debt_id).first()

    def get_debts_by_user(self, user_id: int) -> list:
        return self.session.query(Debt).filter_by(user_id=user_id).order_by(Debt.created_at.desc()).all()

    def update_debt(self, debt_id: int, **kwargs) -> Debt:
        debt = self.get_debt_by_id(debt_id)
        if debt:
            for key, value in kwargs.items():
                if hasattr(debt, key):
                    setattr(debt, key, value)
            debt.updated_at = now_almaty()
            self.session.commit()
            self.session.refresh(debt)
        return debt

    def delete_debt(self, debt_id: int) -> bool:
        debt = self.get_debt_by_id(debt_id)
        if debt:
            self.session.delete(debt)
            self.session.commit()
            return True
        return False

    def update_balance(self, debt_id: int, amount: float):
        debt = self.get_debt_by_id(debt_id)
        if debt:
            debt.balance += amount
            debt.updated_at = now_almaty()
            self.session.commit()
            self.session.refresh(debt)
        return debt

    def get_total_gave(self, user_id: int) -> float:
        debts = self.get_debts_by_user(user_id)
        total = 0.0
        for d in debts:
            if d.balance > 0:
                total += d.balance
        return total

    def get_total_took(self, user_id: int) -> float:
        debts = self.get_debts_by_user(user_id)
        total = 0.0
        for d in debts:
            if d.balance < 0:
                total += abs(d.balance)
        return total


class DebtTransactionRepository:
    """Репозиторий для транзакций по долгам"""

    def __init__(self, session: Session):
        self.session = session

    def create_transaction(self, debt_id: int, debt_type: DebtType,
                           amount: float, description: str = "") -> DebtTransaction:
        t = DebtTransaction(
            debt_id=debt_id, type=debt_type,
            amount=amount, description=description
        )
        self.session.add(t)
        self.session.commit()
        self.session.refresh(t)
        return t

    def get_transaction_by_id(self, tid: int) -> DebtTransaction:
        return self.session.query(DebtTransaction).filter_by(id=tid).first()

    def get_transactions_by_debt(self, debt_id: int) -> list:
        return self.session.query(DebtTransaction).filter_by(
            debt_id=debt_id
        ).order_by(DebtTransaction.created_at.desc()).all()

    def delete_transaction(self, tid: int) -> bool:
        t = self.get_transaction_by_id(tid)
        if t:
            debt_id = t.debt_id
            amount = t.amount
            dtype = t.type
            self.session.delete(t)
            self.session.commit()
            return_amount = -amount if dtype == DebtType.GAVE else amount
            debt_repo = DebtRepository(self.session)
            debt_repo.update_balance(debt_id, return_amount)
            return True
        return False

    def update_transaction(self, tid: int, **kwargs) -> DebtTransaction:
        t = self.get_transaction_by_id(tid)
        if t:
            for key, value in kwargs.items():
                if hasattr(t, key) and key not in ['debt_id', 'created_at']:
                    setattr(t, key, value)
            t.updated_at = now_almaty()
            self.session.commit()
            self.session.refresh(t)
        return t


class GoalTransactionRepository:
    """Репозиторий для транзакций по целям"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, goal_id: int, tx_type: GoalTransactionType,
               amount: float) -> GoalTransaction:
        t = GoalTransaction(goal_id=goal_id, type=tx_type, amount=amount)
        self.session.add(t)
        self.session.commit()
        self.session.refresh(t)
        return t

    def get_by_goal(self, goal_id: int) -> list:
        return self.session.query(GoalTransaction).filter_by(
            goal_id=goal_id
        ).order_by(GoalTransaction.created_at.desc()).all()


class CategoryRepository:
    """Репозиторий категорий транзакций"""

    def __init__(self, session: Session):
        self.session = session

    def create_category(self, user_id: int, name: str,
                        color: str = "#6366f1",
                        is_default: bool = False) -> Category:
        if is_default:
            # Сбросить is_default у других категорий этого пользователя
            self.session.query(Category).filter_by(
                user_id=user_id, is_default=True
            ).update({"is_default": False})
        cat = Category(user_id=user_id, name=name, color=color, is_default=is_default)
        self.session.add(cat)
        self.session.commit()
        self.session.refresh(cat)
        return cat

    def get_by_id(self, category_id: int):
        return self.session.query(Category).filter_by(id=category_id).first()

    def get_by_user(self, user_id: int) -> list:
        return self.session.query(Category).filter_by(
            user_id=user_id
        ).order_by(Category.name).all()

    def update(self, category_id: int, **kwargs) -> Category:
        cat = self.get_by_id(category_id)
        if cat:
            if kwargs.get("is_default"):
                self.session.query(Category).filter_by(
                    user_id=cat.user_id, is_default=True
                ).update({"is_default": False})
            for key, value in kwargs.items():
                if hasattr(cat, key):
                    setattr(cat, key, value)
            self.session.commit()
            self.session.refresh(cat)
        return cat

    def delete(self, category_id: int) -> bool:
        cat = self.get_by_id(category_id)
        if cat:
            # NULL категорию у всех связанных транзакций
            self.session.query(Transaction).filter_by(
                category_id=category_id
            ).update({"category_id": None})
            self.session.delete(cat)
            self.session.commit()
            return True
        return False

    def add_keyword(self, category_id: int, keyword: str) -> CategoryKeyword:
        kw = CategoryKeyword(category_id=category_id, keyword=keyword.lower().strip())
        self.session.add(kw)
        self.session.commit()
        self.session.refresh(kw)
        return kw

    def remove_keyword(self, keyword_id: int) -> bool:
        kw = self.session.query(CategoryKeyword).filter_by(id=keyword_id).first()
        if kw:
            self.session.delete(kw)
            self.session.commit()
            return True
        return False

    def get_keywords(self, category_id: int) -> list:
        return self.session.query(CategoryKeyword).filter_by(
            category_id=category_id
        ).all()

    def get_all_keywords_for_user(self, user_id: int) -> list:
        """Вернуть все ключевые слова пользователя вместе с категориями"""
        return (
            self.session.query(CategoryKeyword)
            .join(Category, CategoryKeyword.category_id == Category.id)
            .filter(Category.user_id == user_id)
            .all()
        )


class BudgetRepository:
    """Репозиторий бюджетов"""

    def __init__(self, session: Session):
        self.session = session

    def create_or_update(self, user_id: int, category_id: int,
                         year: int, month: int,
                         limit_amount: float,
                         warning_threshold: float = 80.0) -> Budget:
        existing = self.session.query(Budget).filter_by(
            user_id=user_id, category_id=category_id,
            year=year, month=month
        ).first()
        if existing:
            existing.limit_amount = limit_amount
            existing.warning_threshold = warning_threshold
            self.session.commit()
            self.session.refresh(existing)
            return existing
        budget = Budget(
            user_id=user_id, category_id=category_id,
            year=year, month=month,
            limit_amount=limit_amount,
            warning_threshold=warning_threshold
        )
        self.session.add(budget)
        self.session.commit()
        self.session.refresh(budget)
        return budget

    def get_by_id(self, budget_id: int):
        return self.session.query(Budget).filter_by(id=budget_id).first()

    def get_by_user_month(self, user_id: int, year: int, month: int) -> list:
        return (self.session.query(Budget)
                .options(joinedload(Budget.category))
                .filter_by(user_id=user_id, year=year, month=month)
                .all())

    def delete(self, budget_id: int) -> bool:
        b = self.get_by_id(budget_id)
        if b:
            self.session.delete(b)
            self.session.commit()
            return True
        return False