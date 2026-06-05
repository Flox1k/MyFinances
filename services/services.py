# -*- coding: utf-8 -*-
"""
Сервисы приложения (бизнес-логика)

Классы:
- AuthService: аутентификация и регистрация пользователей
- WalletService: управление кошельками
- TransactionService: управление транзакциями
- AdminService: административные функции

Сервисы используют Репозитории для доступа к БД
"""

from db.database import get_session
from db.repositories import UserRepository, WalletRepository, TransactionRepository, ExchangeRateRepository, GoalRepository, GoalTransactionRepository, DebtRepository, DebtTransactionRepository, CategoryRepository, BudgetRepository
from models.models import User, Wallet, TransactionType, DebtType, Category, Budget
from utils.helpers import (
    hash_password, verify_password, validate_email, 
    validate_password, validate_username, validate_amount
)
import requests


class AuthService:
    """
    Сервис аутентификации и регистрации пользователей
    Отвечает за регистрацию, вход и проверку учетных данных
    """
    
    @staticmethod
    def register(username: str, email: str, password: str, password_confirm: str) -> tuple[bool, str, User]:
        """
        Зарегистрировать нового пользователя
        
        Args:
            username: имя пользователя
            email: адрес электронной почты
            password: пароль
            password_confirm: подтверждение пароля
            
        Returns:
            tuple: (success, message, user)
                - success (bool): успешна ли регистрация
                - message (str): сообщение об ошибке или успехе
                - user (User): созданный пользователь или None
        """
        # Валидация имени пользователя
        valid, error = validate_username(username)
        if not valid:
            return False, error, None
        
        # Валидация email
        if not validate_email(email):
            return False, "Неверный формат email", None
        
        # Валидация пароля
        valid, error = validate_password(password)
        if not valid:
            return False, error, None
        
        # Проверка совпадения пароля и подтверждения
        if password != password_confirm:
            return False, "Пароли не совпадают", None
        
        session = get_session()
        try:
            user_repo = UserRepository(session)
            
            # Проверить, что пользователь с таким именем не существует
            if user_repo.get_user_by_username(username):
                return False, "Пользователь с таким именем уже существует", None
            
            # Проверить, что пользователь с таким email не существует
            if user_repo.get_user_by_email(email):
                return False, "Пользователь с таким email уже зарегистрирован", None
            
            # Хешировать пароль
            password_hash = hash_password(password)
            
            # Создать пользователя
            user = user_repo.create_user(username, email, password_hash)
            
            # Инициализировать дефолтные курсы для нового пользователя
            session.close()  # Закрыть текущую сессию
            ExchangeRateService.init_default_rates(user.id)
            
            return True, f"Пользователь {username} успешно зарегистрирован", user
            
        except Exception as e:
            return False, f"Ошибка регистрации: {str(e)}", None
        finally:
            session.close()
    
    @staticmethod
    def login(username: str, password: str) -> tuple[bool, str, User]:
        """
        Вход пользователя в систему
        
        Args:
            username: имя пользователя
            password: пароль
            
        Returns:
            tuple: (success, message, user)
                - success (bool): успешен ли вход
                - message (str): сообщение об ошибке или успехе
                - user (User): объект пользователя или None
        """
        if not username or not password:
            return False, "Заполните все поля", None
        
        session = get_session()
        try:
            user_repo = UserRepository(session)
            user = user_repo.get_user_by_username(username)
            
            if not user:
                return False, "Пользователь не найден", None
            
            # Проверить пароль
            if not verify_password(password, user.password_hash):
                return False, "Неверный пароль", None
            
            return True, f"Добро пожаловать, {username}!", user
            
        except Exception as e:
            return False, f"Ошибка входа: {str(e)}", None
        finally:
            session.close()

    @staticmethod
    def update_username(user_id: int, new_username: str) -> tuple[bool, str, object]:
        """Сменить имя пользователя."""
        new_username = new_username.strip()
        valid, error = validate_username(new_username)
        if not valid:
            return False, error, None
        session = get_session()
        try:
            repo = UserRepository(session)
            if repo.get_user_by_username(new_username):
                return False, "Имя пользователя уже занято", None
            user = repo.update_user(user_id, username=new_username)
            return True, "Имя пользователя изменено", user
        except Exception as e:
            return False, f"Ошибка: {str(e)}", None
        finally:
            session.close()

    @staticmethod
    def update_email(user_id: int, new_email: str, current_password: str) -> tuple[bool, str, object]:
        """Сменить email (требуется текущий пароль)."""
        new_email = new_email.strip()
        if not validate_email(new_email):
            return False, "Неверный формат email", None
        session = get_session()
        try:
            repo = UserRepository(session)
            user = repo.get_user_by_id(user_id)
            if not user:
                return False, "Пользователь не найден", None
            if not verify_password(current_password, user.password_hash):
                return False, "Неверный пароль", None
            if repo.get_user_by_email(new_email):
                return False, "Email уже используется другим аккаунтом", None
            user = repo.update_user(user_id, email=new_email)
            return True, "Email успешно изменён", user
        except Exception as e:
            return False, f"Ошибка: {str(e)}", None
        finally:
            session.close()

    @staticmethod
    def update_password(user_id: int, current_password: str, new_password: str, confirm: str) -> tuple[bool, str]:
        """Сменить пароль (требуется текущий пароль)."""
        if new_password != confirm:
            return False, "Новые пароли не совпадают"
        valid, error = validate_password(new_password)
        if not valid:
            return False, error
        session = get_session()
        try:
            repo = UserRepository(session)
            user = repo.get_user_by_id(user_id)
            if not user:
                return False, "Пользователь не найден"
            if not verify_password(current_password, user.password_hash):
                return False, "Неверный текущий пароль"
            new_hash = hash_password(new_password)
            repo.update_user(user_id, password_hash=new_hash)
            return True, "Пароль успешно изменён"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
        finally:
            session.close()


class WalletService:
    """
    Сервис управления кошельками
    Отвечает за создание, редактирование и удаление кошельков
    """
    
    @staticmethod
    def create_wallet(user_id: int, name: str, currency: str = "KZT") -> tuple[bool, str, Wallet]:
        """
        Создать новый кошелёк для пользователя
        
        Args:
            user_id: id пользователя
            name: название кошелька
            currency: валюта (по умолчанию KZT)
            
        Returns:
            tuple: (success, message, wallet)
        """
        if not name or not name.strip():
            return False, "Название кошелька не может быть пустым", None
        
        session = get_session()
        try:
            wallet_repo = WalletRepository(session)
            wallet = wallet_repo.create_wallet(user_id, name.strip(), currency)
            return True, f"Кошелёк '{name}' создан", wallet
        except Exception as e:
            return False, f"Ошибка создания кошелька: {str(e)}", None
        finally:
            session.close()
    
    @staticmethod
    def get_user_wallets(user_id: int) -> list[Wallet]:
        """
        Получить все кошельки пользователя
        
        Args:
            user_id: id пользователя
            
        Returns:
            list: список кошельков
        """
        session = get_session()
        try:
            wallet_repo = WalletRepository(session)
            return wallet_repo.get_wallets_by_user(user_id)
        finally:
            session.close()
    
    @staticmethod
    def get_total_balance(user_id: int) -> float:
        """
        Получить общий баланс всех кошельков пользователя
        
        Args:
            user_id: id пользователя
            
        Returns:
            float: сумма всех балансов (внимание: в разных валютах!)
        """
        session = get_session()
        try:
            wallet_repo = WalletRepository(session)
            return wallet_repo.get_total_balance(user_id)
        finally:
            session.close()

    @staticmethod
    def get_balance_multi_currency(user_id: int, main_currency: str) -> dict:
        """
        Получить баланс по валютам и общий баланс в основной валюте.

        Args:
            user_id: id пользователя
            main_currency: основная валюта (KZT, USD, RUB)

        Returns:
            dict: {
                "total": float,             # итого в main_currency
                "main_currency": str,
                "breakdown": {currency: balance},  # суммы по валютам
            }
        """
        wallets = WalletService.get_user_wallets(user_id)
        rates = ExchangeRateService.get_user_rates(user_id)

        breakdown: dict[str, float] = {}
        for w in wallets:
            breakdown[w.currency] = breakdown.get(w.currency, 0.0) + w.balance

        total = 0.0
        for curr, amount in breakdown.items():
            total += WalletService._convert(amount, curr, main_currency, rates)

        return {
            "total": total,
            "main_currency": main_currency,
            "breakdown": breakdown,
        }

    @staticmethod
    def _convert(amount: float, from_curr: str, to_curr: str, rates: dict) -> float:
        """Конвертировать сумму используя имеющиеся курсы."""
        if from_curr == to_curr:
            return amount
        # Прямой курс: from_curr -> to_curr
        direct = rates.get((from_curr, to_curr))
        if direct:
            return amount * direct
        # Обратный курс: to_curr -> from_curr
        reverse = rates.get((to_curr, from_curr))
        if reverse and reverse != 0:
            return amount / reverse
        # Если нет прямого пути — попробуем через USD
        for mid in ("USD", "KZT", "RUB", "EUR"):
            if mid == from_curr or mid == to_curr:
                continue
            r1 = rates.get((from_curr, mid)) or (1.0 / rates[(mid, from_curr)] if rates.get((mid, from_curr)) else None)
            r2 = rates.get((mid, to_curr)) or (1.0 / rates[(to_curr, mid)] if rates.get((to_curr, mid)) else None)
            if r1 and r2:
                return amount * r1 * r2
        # Не удалось конвертировать — вернуть как есть
        return amount
    
    @staticmethod
    def delete_wallet(wallet_id: int) -> tuple[bool, str]:
        """
        Удалить кошелёк (и все его транзакции)
        
        Args:
            wallet_id: id кошелька
            
        Returns:
            tuple: (success, message)
        """
        session = get_session()
        try:
            wallet_repo = WalletRepository(session)
            if wallet_repo.delete_wallet(wallet_id):
                return True, "Кошелёк удален"
            else:
                return False, "Кошелёк не найден"
        except Exception as e:
            return False, f"Ошибка удаления кошелька: {str(e)}"
        finally:
            session.close()
    
    @staticmethod
    def rename_wallet(wallet_id: int, new_name: str) -> tuple[bool, str, Wallet]:
        """
        Переименовать кошелёк
        
        Args:
            wallet_id: id кошелька
            new_name: новое название
            
        Returns:
            tuple: (success, message, wallet)
        """
        if not new_name or not new_name.strip():
            return False, "Название кошелька не может быть пустым", None
        
        session = get_session()
        try:
            wallet_repo = WalletRepository(session)
            wallet = wallet_repo.update_wallet(wallet_id, name=new_name.strip())
            if wallet:
                return True, "Кошелёк переименован", wallet
            else:
                return False, "Кошелёк не найден", None
        except Exception as e:
            return False, f"Ошибка: {str(e)}", None
        finally:
            session.close()


class TransactionService:
    """
    Сервис управления транзакциями
    Отвечает за добавление, редактирование и удаление операций
    """
    
    @staticmethod
    def add_transaction(wallet_id: int, transaction_type: str,
                       amount: str, description: str = "",
                       category_id: int = None) -> tuple[bool, str]:
        """
        Добавить новую транзакцию и обновить баланс кошелька

        Args:
            wallet_id: id кошелька
            transaction_type: тип ("income" или "expense")
            amount: сумма (строка, будет валидирована)
            description: комментарий/описание
            category_id: id категории (None = без категории)

        Returns:
            tuple: (success, message)
        """
        # Валидация суммы
        valid, error, parsed_amount = validate_amount(amount)
        if not valid:
            return False, error
        
        # Валидация типа
        if transaction_type not in ["income", "expense"]:
            return False, "Неверный тип транзакции"
        
        session = get_session()
        try:
            trans_repo = TransactionRepository(session)
            wallet_repo = WalletRepository(session)
            
            # Проверить, что кошелек существует
            wallet = wallet_repo.get_wallet_by_id(wallet_id)
            if not wallet:
                return False, "Кошелёк не найден"
            
            # Определить тип транзакции
            trans_type = TransactionType.INCOME if transaction_type == "income" else TransactionType.EXPENSE
            
            # Создать транзакцию
            trans_repo.create_transaction(wallet_id, trans_type, parsed_amount, description)
            
            # Привязать категорию, если указана
            txn = trans_repo.get_transactions_by_wallet(wallet_id, limit=1)
            if txn and category_id is not None:
                txn[0].category_id = category_id
                session.commit()
            
            # Обновить баланс кошелька
            # При доходе: добавить сумму
            # При расходе: вычесть сумму
            balance_change = parsed_amount if transaction_type == "income" else -parsed_amount
            wallet_repo.update_balance(wallet_id, balance_change)
            
            type_text = "Доход" if transaction_type == "income" else "Расход"
            return True, f"{type_text} на сумму {parsed_amount} добавлен"
            
        except Exception as e:
            return False, f"Ошибка добавления транзакции: {str(e)}"
        finally:
            session.close()
    
    @staticmethod
    def update_transaction(transaction_id: int, transaction_type: str,
                          amount: str, description: str = "",
                          category_id: int = None) -> tuple[bool, str]:
        """
        Обновить существующую транзакцию

        Args:
            transaction_id: id транзакции
            transaction_type: тип ("income" или "expense")
            amount: сумма (строка, будет валидирована)
            description: комментарий/описание
            category_id: id категории (None = без категории)

        Returns:
            tuple: (success, message)
        """
        # Валидация суммы
        valid, error, parsed_amount = validate_amount(amount)
        if not valid:
            return False, error
        
        # Валидация типа
        if transaction_type not in ["income", "expense"]:
            return False, "Неверный тип транзакции"
        
        session = get_session()
        try:
            trans_repo = TransactionRepository(session)
            wallet_repo = WalletRepository(session)
            
            # Получить старую транзакцию
            old_transaction = trans_repo.get_transaction_by_id(transaction_id)
            if not old_transaction:
                return False, "Транзакция не найдена"
            
            # Вычислить разницу баланса
            old_amount = old_transaction.amount
            old_was_income = old_transaction.type == TransactionType.INCOME
            new_is_income = transaction_type == "income"
            
            # Вычислить изменение баланса
            # Сначала отменяем старую транзакцию
            if old_was_income:
                balance_change = -old_amount
            else:
                balance_change = old_amount
            
            # Потом применяем новую
            if new_is_income:
                balance_change += parsed_amount
            else:
                balance_change -= parsed_amount
            
            # Обновить баланс кошелька
            wallet_repo.update_balance(old_transaction.wallet_id, balance_change)
            
            # Определить новый тип транзакции
            new_trans_type = TransactionType.INCOME if transaction_type == "income" else TransactionType.EXPENSE
            
            # Обновить транзакцию в БД
            trans_repo.update_transaction(
                transaction_id,
                amount=parsed_amount,
                description=description,
                type=new_trans_type
            )

            # Обновить категорию
            updated_txn = trans_repo.get_transaction_by_id(transaction_id)
            if updated_txn is not None:
                updated_txn.category_id = category_id
                session.commit()
            
            type_text = "Доход" if transaction_type == "income" else "Расход"
            return True, f"{type_text} обновлён"
            
        except Exception as e:
            return False, f"Ошибка обновления транзакции: {str(e)}"
        finally:
            session.close()
    
    @staticmethod
    def get_wallet_transactions(wallet_id: int) -> list:
        """
        Получить все транзакции кошелька
        
        Args:
            wallet_id: id кошелька
            
        Returns:
            list: список транзакций (отсортированы по дате убывания)
        """
        session = get_session()
        try:
            trans_repo = TransactionRepository(session)
            return trans_repo.get_transactions_by_wallet(wallet_id)
        finally:
            session.close()
    
    @staticmethod
    def delete_transaction(transaction_id: int) -> tuple[bool, str]:
        """
        Удалить транзакцию и вернуть баланс кошелька
        
        Args:
            transaction_id: id транзакции
            
        Returns:
            tuple: (success, message)
        """
        session = get_session()
        try:
            trans_repo = TransactionRepository(session)
            if trans_repo.delete_transaction(transaction_id):
                return True, "Транзакция удалена, баланс восстановлен"
            else:
                return False, "Транзакция не найдена"
        except Exception as e:
            return False, f"Ошибка удаления: {str(e)}"
        finally:
            session.close()


class AdminService:
    """
    Сервис для административных функций
    Используется для админки: просмотр и управление пользователями, кошельками, транзакциями
    """
    
    @staticmethod
    def get_all_users() -> list[User]:
        """
        Получить всех пользователей (для админки)
        
        Returns:
            list: список пользователей
        """
        session = get_session()
        try:
            user_repo = UserRepository(session)
            return user_repo.get_all_users()
        finally:
            session.close()
    
    @staticmethod
    def delete_user(user_id: int) -> tuple[bool, str]:
        """
        Удалить пользователя и все его данные (для админки)
        
        Args:
            user_id: id пользователя
            
        Returns:
            tuple: (success, message)
        """
        session = get_session()
        try:
            user_repo = UserRepository(session)
            if user_repo.delete_user(user_id):
                return True, "Пользователь удален"
            else:
                return False, "Пользователь не найден"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
        finally:
            session.close()
    
    @staticmethod
    def get_user_details(user_id: int) -> dict:
        """
        Получить полную информацию о пользователе с его кошельками и транзакциями
        
        Args:
            user_id: id пользователя
            
        Returns:
            dict: информация о пользователе
        """
        session = get_session()
        try:
            user_repo = UserRepository(session)
            wallet_repo = WalletRepository(session)
            
            user = user_repo.get_user_by_id(user_id)
            if not user:
                return {}
            
            wallets = wallet_repo.get_wallets_by_user(user_id)
            
            return {
                "user": user,
                "wallets": wallets,
                "total_balance": wallet_repo.get_total_balance(user_id),
                "wallet_count": len(wallets)
            }
        finally:
            session.close()


class ExchangeRateService:
    """
    Сервис для управления курсами валют
    Получает актуальные курсы из API и сохраняет в БД для каждого пользователя
    """
    
    API_KEY = "165f151bb424941ac371164d"  # exchangerate-api.com ключ
    API_URL = "https://v6.exchangerate-api.com/v6/{api_key}/latest/{currency}"
    
    @staticmethod
    def init_default_rates(user_id: int) -> tuple[bool, str]:
        """
        Инициализировать 3 дефолтных курса для нового пользователя
        USD -> KZT, RUB -> KZT, USD -> RUB
        
        Args:
            user_id: id пользователя
            
        Returns:
            tuple: (success, message)
        """
        session = get_session()
        try:
            rate_repo = ExchangeRateRepository(session)
            
            # Попробуем получить актуальные курсы
            default_pairs = [
                ('USD', 'KZT'),
                ('RUB', 'KZT'),
                ('USD', 'RUB'),
            ]
            
            for from_curr, to_curr in default_pairs:
                try:
                    rate = ExchangeRateService.fetch_rate(from_curr, to_curr)
                    if rate:
                        rate_repo.create_rate(user_id, from_curr, to_curr, rate)
                except:
                    # Если не получилось, используем дефолтные значения
                    default_rates = {
                        ('USD', 'KZT'): 475.0,
                        ('RUB', 'KZT'): 5.5,
                        ('USD', 'RUB'): 86.0,
                    }
                    rate_repo.create_rate(user_id, from_curr, to_curr, default_rates.get((from_curr, to_curr), 1.0))
            
            return True, "Дефолтные курсы инициализированы"
        except Exception as e:
            return False, f"Ошибка инициализации: {str(e)}"
        finally:
            session.close()
    
    @staticmethod
    def fetch_rate(from_currency: str, to_currency: str) -> float:
        """
        Получить курс из API exchangerate-api.com
        
        Args:
            from_currency: валюта источника (например, USD)
            to_currency: валюта назначения (например, KZT)
            
        Returns:
            float: курс обмена или None если ошибка
        """
        try:
            url = ExchangeRateService.API_URL.format(
                api_key=ExchangeRateService.API_KEY,
                currency=from_currency
            )
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('result') == 'success':
                    rates = data.get('conversion_rates', {})
                    return rates.get(to_currency)
            return None
        except Exception as e:
            print(f"Ошибка получения курса {from_currency}->{to_currency}: {e}")
            return None
    
    @staticmethod
    def refresh_rate(user_id: int, from_curr: str, to_curr: str) -> tuple[bool, str, float]:
        """
        Обновить курс для пользователя из API
        
        Args:
            user_id: id пользователя
            from_curr: валюта источника
            to_curr: валюта назначения
            
        Returns:
            tuple: (success, message, rate)
        """
        session = get_session()
        try:
            rate_repo = ExchangeRateRepository(session)
            
            # Получить новый курс из API
            new_rate = ExchangeRateService.fetch_rate(from_curr, to_curr)
            
            if new_rate is None:
                return False, "Не удалось получить курс (проверьте интернет)", None
            
            # Сохранить в БД
            rate_obj = rate_repo.create_rate(user_id, from_curr, to_curr, new_rate)
            
            return True, f"Курс {from_curr}/{to_curr} обновлён", new_rate
        except Exception as e:
            return False, f"Ошибка обновления: {str(e)}", None
        finally:
            session.close()
    
    @staticmethod
    def get_user_rates(user_id: int) -> dict:
        """
        Получить все курсы пользователя
        
        Args:
            user_id: id пользователя
            
        Returns:
            dict: {(from, to): rate}
        """
        session = get_session()
        try:
            rate_repo = ExchangeRateRepository(session)
            rates = rate_repo.get_user_rates(user_id)
            
            return {(r.from_currency, r.to_currency): r.rate for r in rates}
        finally:
            session.close()

    @staticmethod
    def get_user_rates_objects(user_id: int) -> list:
        """
        Получить все объекты ExchangeRate пользователя (с last_updated).
        """
        session = get_session()
        try:
            rate_repo = ExchangeRateRepository(session)
            rates = rate_repo.get_user_rates(user_id)
            # Отвязать от сессии — скопировать нужные поля
            result = []
            for r in rates:
                result.append({
                    "from_currency": r.from_currency,
                    "to_currency": r.to_currency,
                    "rate": r.rate,
                    "last_updated": r.last_updated,
                })
            return result
        finally:
            session.close()
    
    @staticmethod
    def add_rate(user_id: int, from_curr: str, to_curr: str) -> tuple[bool, str]:
        """
        Добавить новый курс для пользователя
        
        Args:
            user_id: id пользователя
            from_curr: валюта источника
            to_curr: валюта назначения
            
        Returns:
            tuple: (success, message)
        """
        # Попробуемьполучить актуальный курс
        rate = ExchangeRateService.fetch_rate(from_curr, to_curr)
        
        if rate is None:
            return False, f"Валютная пара {from_curr}/{to_curr} не поддерживается или недоступна"
        
        session = get_session()
        try:
            rate_repo = ExchangeRateRepository(session)
            rate_repo.create_rate(user_id, from_curr, to_curr, rate)
            return True, f"Курс {from_curr}/{to_curr} добавлен: 1 {from_curr} = {rate:.4f} {to_curr}"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
        finally:
            session.close()
    
    @staticmethod
    def delete_rate(user_id: int, from_curr: str, to_curr: str) -> tuple[bool, str]:
        """
        Удалить курс пользователя
        
        Args:
            user_id: id пользователя
            from_curr: валюта источника
            to_curr: валюта назначения
            
        Returns:
            tuple: (success, message)
        """
        session = get_session()
        try:
            rate_repo = ExchangeRateRepository(session)
            if rate_repo.delete_user_rate(user_id, from_curr, to_curr):
                return True, f"Курс {from_curr}/{to_curr} удален"
            else:
                return False, "Курс не найден"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
        finally:
            session.close()


class GoalService:
    """
    Сервис управления финансовыми целями
    """

    @staticmethod
    def create_goal(user_id: int, name: str, target_amount: str,
                    currency: str, start_date, end_date,
                    description: str = "") -> tuple:
        """
        Создать новую цель.

        Returns:
            tuple: (success, message, goal)
        """
        from utils.helpers import validate_amount
        if not name or not name.strip():
            return False, "Название цели не может быть пустым", None
        valid, error, amount = validate_amount(str(target_amount))
        if not valid:
            return False, error, None
        if amount <= 0:
            return False, "Целевая сумма должна быть положительной", None
        if start_date >= end_date:
            return False, "Дата окончания должна быть позже даты начала", None

        session = get_session()
        try:
            goal_repo = GoalRepository(session)
            goal = goal_repo.create_goal(
                user_id=user_id,
                name=name.strip(),
                target_amount=amount,
                currency=currency,
                start_date=start_date,
                end_date=end_date,
                description=description.strip()
            )
            return True, f"Цель '{name}' создана", goal
        except Exception as e:
            return False, f"Ошибка создания цели: {str(e)}", None
        finally:
            session.close()

    @staticmethod
    def get_user_goals(user_id: int) -> list:
        session = get_session()
        try:
            goal_repo = GoalRepository(session)
            return goal_repo.get_goals_by_user(user_id)
        finally:
            session.close()

    @staticmethod
    def get_tracked_goal(user_id: int):
        session = get_session()
        try:
            goal_repo = GoalRepository(session)
            return goal_repo.get_tracked_goal(user_id)
        finally:
            session.close()

    @staticmethod
    def set_tracked(user_id: int, goal_id: int) -> tuple:
        session = get_session()
        try:
            goal_repo = GoalRepository(session)
            goal = goal_repo.set_tracked(user_id, goal_id)
            return True, "Цель выбрана для отслеживания"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
        finally:
            session.close()

    @staticmethod
    def untrack_all(user_id: int):
        session = get_session()
        try:
            goal_repo = GoalRepository(session)
            goal_repo.untrack_all(user_id)
        finally:
            session.close()

    @staticmethod
    def update_current_amount(goal_id: int, amount: str) -> tuple:
        from utils.helpers import validate_amount
        valid, error, parsed = validate_amount(str(amount))
        if not valid:
            return False, error
        if parsed < 0:
            return False, "Сумма не может быть отрицательной"
        session = get_session()
        try:
            goal_repo = GoalRepository(session)
            goal = goal_repo.update_goal(goal_id, current_amount=parsed)
            if goal:
                return True, "Сумма обновлена"
            return False, "Цель не найдена"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
        finally:
            session.close()

    @staticmethod
    def update_goal(goal_id: int, name: str, target_amount: str,
                    currency: str, start_date, end_date,
                    description: str = "") -> tuple:
        from utils.helpers import validate_amount
        if not name or not name.strip():
            return False, "Название цели не может быть пустым", None
        valid, error, amount = validate_amount(str(target_amount))
        if not valid:
            return False, error, None
        if start_date >= end_date:
            return False, "Дата окончания должна быть позже даты начала", None
        session = get_session()
        try:
            goal_repo = GoalRepository(session)
            goal = goal_repo.update_goal(
                goal_id,
                name=name.strip(),
                target_amount=amount,
                currency=currency,
                start_date=start_date,
                end_date=end_date,
                description=description.strip()
            )
            if goal:
                return True, "Цель обновлена", goal
            return False, "Цель не найдена", None
        except Exception as e:
            return False, f"Ошибка: {str(e)}", None
        finally:
            session.close()

    @staticmethod
    def delete_goal(goal_id: int) -> tuple:
        session = get_session()
        try:
            goal_repo = GoalRepository(session)
            if goal_repo.delete_goal(goal_id):
                return True, "Цель удалена"
            return False, "Цель не найдена"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
        finally:
            session.close()


class GoalTransactionService:
    """Сервис для работы с транзакциями по целям (добавление/убавление суммы)."""

    @staticmethod
    def add_amount(goal_id: int, amount: str) -> tuple:
        """Добавить сумму к цели и записать транзакцию."""
        from utils.helpers import validate_amount
        from models.models import GoalTransactionType
        valid, error, parsed = validate_amount(str(amount))
        if not valid:
            return False, error
        if parsed <= 0:
            return False, "Сумма должна быть положительной"
        session = get_session()
        try:
            goal_repo = GoalRepository(session)
            goal = goal_repo.get_goal_by_id(goal_id)
            if not goal:
                return False, "Цель не найдена"
            new_amount = goal.current_amount + parsed
            goal_repo.update_goal(goal_id, current_amount=new_amount)
            GoalTransactionRepository(session).create(goal_id, GoalTransactionType.ADD, parsed)
            return True, f"Добавлено {parsed}"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
        finally:
            session.close()

    @staticmethod
    def subtract_amount(goal_id: int, amount: str) -> tuple:
        """Убавить сумму из цели и записать транзакцию."""
        from utils.helpers import validate_amount
        from models.models import GoalTransactionType
        valid, error, parsed = validate_amount(str(amount))
        if not valid:
            return False, error
        if parsed <= 0:
            return False, "Сумма должна быть положительной"
        session = get_session()
        try:
            goal_repo = GoalRepository(session)
            goal = goal_repo.get_goal_by_id(goal_id)
            if not goal:
                return False, "Цель не найдена"
            new_amount = max(0.0, goal.current_amount - parsed)
            goal_repo.update_goal(goal_id, current_amount=new_amount)
            GoalTransactionRepository(session).create(goal_id, GoalTransactionType.SUBTRACT, parsed)
            return True, f"Убрано {parsed}"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
        finally:
            session.close()

    @staticmethod
    def get_transactions(goal_id: int) -> list:
        """Получить историю транзакций по цели."""
        session = get_session()
        try:
            return GoalTransactionRepository(session).get_by_goal(goal_id)
        finally:
            session.close()


class DebtService:
    """
    Сервис управления долгами
    """

    @staticmethod
    def create_debt(user_id: int, name: str, currency: str = "KZT") -> tuple:
        if not name or not name.strip():
            return False, "Имя не может быть пустым", None
        session = get_session()
        try:
            repo = DebtRepository(session)
            debt = repo.create_debt(user_id, name.strip(), currency)
            return True, f"Кейс '{name}' создан", debt
        except Exception as e:
            return False, f"Ошибка: {str(e)}", None
        finally:
            session.close()

    @staticmethod
    def get_user_debts(user_id: int) -> list:
        session = get_session()
        try:
            repo = DebtRepository(session)
            return repo.get_debts_by_user(user_id)
        finally:
            session.close()

    @staticmethod
    def get_debt_by_id(debt_id: int):
        session = get_session()
        try:
            repo = DebtRepository(session)
            return repo.get_debt_by_id(debt_id)
        finally:
            session.close()

    @staticmethod
    def rename_debt(debt_id: int, new_name: str) -> tuple:
        if not new_name or not new_name.strip():
            return False, "Имя не может быть пустым", None
        session = get_session()
        try:
            repo = DebtRepository(session)
            debt = repo.update_debt(debt_id, name=new_name.strip())
            if debt:
                return True, "Переименовано", debt
            return False, "Не найдено", None
        except Exception as e:
            return False, f"Ошибка: {str(e)}", None
        finally:
            session.close()

    @staticmethod
    def delete_debt(debt_id: int) -> tuple:
        session = get_session()
        try:
            repo = DebtRepository(session)
            if repo.delete_debt(debt_id):
                return True, "Кейс удалён"
            return False, "Кейс не найден"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
        finally:
            session.close()

    @staticmethod
    def get_summary(user_id: int) -> dict:
        """Итого по долгам: gave (= мне должны), took (= я должен), balance"""
        session = get_session()
        try:
            repo = DebtRepository(session)
            gave = repo.get_total_gave(user_id)
            took = repo.get_total_took(user_id)
            return {"gave": gave, "took": took, "balance": gave - took}
        finally:
            session.close()

    @staticmethod
    def get_summary_multi_currency(user_id: int, main_currency: str) -> dict:
        """
        Итого по долгам с мультивалютностью.

        Конвертирует суммы всех кейсов в основную валюту.

        Returns:
            dict: {
                "gave": float,        # итого «мне должны» в main_currency
                "took": float,        # итого «я должен» в main_currency
                "balance": float,     # gave - took в main_currency
                "main_currency": str,
                "breakdown": {currency: {"gave": float, "took": float, "balance": float}},
            }
        """
        debts = DebtService.get_user_debts(user_id)
        rates = ExchangeRateService.get_user_rates(user_id)

        breakdown: dict[str, dict] = {}
        for d in debts:
            txs = DebtTransactionService.get_debt_transactions(d.id)
            g = sum(t.amount for t in txs if t.type == DebtType.GAVE)
            t_ = sum(t.amount for t in txs if t.type == DebtType.TOOK)
            entry = breakdown.setdefault(d.currency, {"gave": 0.0, "took": 0.0, "balance": 0.0})
            entry["gave"] += g
            entry["took"] += t_
            entry["balance"] += d.balance

        total_gave = 0.0
        total_took = 0.0
        for curr, vals in breakdown.items():
            total_gave += WalletService._convert(vals["gave"], curr, main_currency, rates)
            total_took += WalletService._convert(vals["took"], curr, main_currency, rates)

        return {
            "gave": total_gave,
            "took": total_took,
            "balance": total_gave - total_took,
            "main_currency": main_currency,
            "breakdown": breakdown,
        }


class DebtTransactionService:
    """
    Сервис транзакций по долгам
    """

    @staticmethod
    def add_transaction(debt_id: int, debt_type: str,
                        amount: str, description: str = "") -> tuple:
        valid, error, parsed = validate_amount(amount)
        if not valid:
            return False, error
        if debt_type not in ["gave", "took"]:
            return False, "Неверный тип операции"
        session = get_session()
        try:
            t_repo = DebtTransactionRepository(session)
            d_repo = DebtRepository(session)
            debt = d_repo.get_debt_by_id(debt_id)
            if not debt:
                return False, "Кейс не найден"
            dt = DebtType.GAVE if debt_type == "gave" else DebtType.TOOK
            t_repo.create_transaction(debt_id, dt, parsed, description)
            balance_change = parsed if debt_type == "gave" else -parsed
            d_repo.update_balance(debt_id, balance_change)
            label = "Дал в долг" if debt_type == "gave" else "Взял в долг"
            return True, f"{label}: {parsed}"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
        finally:
            session.close()

    @staticmethod
    def update_transaction(tid: int, debt_type: str,
                           amount: str, description: str = "") -> tuple:
        valid, error, parsed = validate_amount(amount)
        if not valid:
            return False, error
        if debt_type not in ["gave", "took"]:
            return False, "Неверный тип операции"
        session = get_session()
        try:
            t_repo = DebtTransactionRepository(session)
            d_repo = DebtRepository(session)
            old = t_repo.get_transaction_by_id(tid)
            if not old:
                return False, "Транзакция не найдена"
            old_amount = old.amount
            old_was_gave = (old.type == DebtType.GAVE)
            new_is_gave = (debt_type == "gave")
            bc = (-old_amount if old_was_gave else old_amount)
            bc += (parsed if new_is_gave else -parsed)
            d_repo.update_balance(old.debt_id, bc)
            new_dt = DebtType.GAVE if new_is_gave else DebtType.TOOK
            t_repo.update_transaction(tid, amount=parsed, description=description, type=new_dt)
            return True, "Операция обновлена"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
        finally:
            session.close()

    @staticmethod
    def get_debt_transactions(debt_id: int) -> list:
        session = get_session()
        try:
            repo = DebtTransactionRepository(session)
            return repo.get_transactions_by_debt(debt_id)
        finally:
            session.close()

    @staticmethod
    def delete_transaction(tid: int) -> tuple:
        session = get_session()
        try:
            repo = DebtTransactionRepository(session)
            if repo.delete_transaction(tid):
                return True, "Операция удалена"
            return False, "Операция не найдена"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
        finally:
            session.close()


class AccountDataService:
    """
    Сервис экспорта и импорта всех данных аккаунта.
    """

    @staticmethod
    def export_data(user_id: int) -> dict:
        """
        Собрать все данные пользователя в один словарь.

        Returns:
            dict: полный снимок данных аккаунта
        """
        from db.repositories import (
            UserRepository, WalletRepository, TransactionRepository,
            ExchangeRateRepository, GoalRepository,
            DebtRepository, DebtTransactionRepository,
        )
        session = get_session()
        try:
            user = UserRepository(session).get_user_by_id(user_id)
            if not user:
                return {}

            wallets_data = []
            for w in WalletRepository(session).get_wallets_by_user(user_id):
                txns = TransactionRepository(session).get_transactions_by_wallet(w.id)
                wallets_data.append({
                    "name": w.name,
                    "currency": w.currency,
                    "balance": w.balance,
                    "transactions": [
                        {
                            "type": t.type.value,
                            "amount": t.amount,
                            "description": t.description,
                            "created_at": t.created_at.isoformat() if t.created_at else None,
                        }
                        for t in txns
                    ],
                })

            rates_data = []
            for r in ExchangeRateRepository(session).get_user_rates(user_id):
                rates_data.append({
                    "from_currency": r.from_currency,
                    "to_currency": r.to_currency,
                    "rate": r.rate,
                })

            goals_data = []
            for g in GoalRepository(session).get_goals_by_user(user_id):
                goals_data.append({
                    "name": g.name,
                    "target_amount": g.target_amount,
                    "current_amount": g.current_amount,
                    "currency": g.currency,
                    "start_date": g.start_date.isoformat() if g.start_date else None,
                    "end_date": g.end_date.isoformat() if g.end_date else None,
                    "is_tracked": g.is_tracked,
                    "description": g.description,
                })

            debts_data = []
            for d in DebtRepository(session).get_debts_by_user(user_id):
                dt_list = DebtTransactionRepository(session).get_transactions_by_debt(d.id)
                debts_data.append({
                    "name": d.name,
                    "currency": d.currency,
                    "balance": d.balance,
                    "transactions": [
                        {
                            "type": dt.type.value,
                            "amount": dt.amount,
                            "description": dt.description,
                            "created_at": dt.created_at.isoformat() if dt.created_at else None,
                        }
                        for dt in dt_list
                    ],
                })

            return {
                "app": "MyFinances",
                "version": "1.0",
                "user": {
                    "username": user.username,
                    "email": user.email,
                },
                "wallets": wallets_data,
                "exchange_rates": rates_data,
                "goals": goals_data,
                "debts": debts_data,
                "categories": [
                    {
                        "name": c.name,
                        "color": c.color,
                        "is_default": c.is_default,
                        "keywords": [kw.keyword for kw in c.keywords],
                    }
                    for c in CategoryRepository(session).get_by_user(user_id)
                ],
                "budgets": [
                    {
                        "category_name": b.category.name if b.category else "",
                        "year": b.year,
                        "month": b.month,
                        "limit_amount": b.limit_amount,
                        "warning_threshold": b.warning_threshold,
                    }
                    for b in BudgetRepository(session).get_by_user_month(
                        user_id,
                        __import__("datetime").date.today().year,
                        __import__("datetime").date.today().month
                    )
                ],
            }
        finally:
            session.close()

    @staticmethod
    def import_data(user_id: int, data: dict) -> tuple[bool, str]:
        """
        Заменить все данные пользователя данными из словаря.

        Данные аутентификации (пароль) НЕ перезаписываются.
        """
        from db.repositories import (
            UserRepository, WalletRepository, TransactionRepository,
            ExchangeRateRepository, GoalRepository,
            DebtRepository, DebtTransactionRepository,
        )
        from models.models import (
            Wallet, Transaction, TransactionType,
            ExchangeRate, Goal, Debt, DebtTransaction, DebtType,
        )
        from datetime import date, datetime

        if data.get("app") != "MyFinances":
            return False, "Неверный формат файла"

        session = get_session()
        try:
            user_repo = UserRepository(session)
            user = user_repo.get_user_by_id(user_id)
            if not user:
                return False, "Пользователь не найден"

            # Обновить username если он не занят другим пользователем
            imp_user = data.get("user", {})
            new_username = imp_user.get("username", "").strip()
            if new_username and new_username != user.username:
                existing = user_repo.get_user_by_username(new_username)
                if not existing:
                    user.username = new_username

            # Удалить старые данные (каскадно удаляются транзакции/debt_transactions)
            for w in session.query(Wallet).filter_by(user_id=user_id).all():
                session.delete(w)
            for r in session.query(ExchangeRate).filter_by(user_id=user_id).all():
                session.delete(r)
            for g in session.query(Goal).filter_by(user_id=user_id).all():
                session.delete(g)
            for d in session.query(Debt).filter_by(user_id=user_id).all():
                session.delete(d)
            session.flush()

            # Импортировать кошельки
            for wd in data.get("wallets", []):
                w = Wallet(
                    user_id=user_id,
                    name=wd.get("name", "Кошелёк"),
                    currency=wd.get("currency", "KZT"),
                    balance=wd.get("balance", 0.0),
                )
                session.add(w)
                session.flush()
                for td in wd.get("transactions", []):
                    ttype = (TransactionType.INCOME
                             if td.get("type") == "income"
                             else TransactionType.EXPENSE)
                    created = None
                    if td.get("created_at"):
                        try:
                            created = datetime.fromisoformat(td["created_at"])
                        except ValueError:
                            created = None
                    t = Transaction(
                        wallet_id=w.id,
                        type=ttype,
                        amount=td.get("amount", 0.0),
                        description=td.get("description", ""),
                        created_at=created or datetime.now(),
                    )
                    session.add(t)

            # Импортировать курсы
            for rd in data.get("exchange_rates", []):
                r = ExchangeRate(
                    user_id=user_id,
                    from_currency=rd.get("from_currency", "USD"),
                    to_currency=rd.get("to_currency", "KZT"),
                    rate=rd.get("rate", 1.0),
                )
                session.add(r)

            # Импортировать цели
            for gd in data.get("goals", []):
                def _parse_date(s):
                    if not s:
                        return date.today()
                    try:
                        return date.fromisoformat(s)
                    except ValueError:
                        return date.today()
                g = Goal(
                    user_id=user_id,
                    name=gd.get("name", "Цель"),
                    target_amount=gd.get("target_amount", 0.0),
                    current_amount=gd.get("current_amount", 0.0),
                    currency=gd.get("currency", "KZT"),
                    start_date=_parse_date(gd.get("start_date")),
                    end_date=_parse_date(gd.get("end_date")),
                    is_tracked=gd.get("is_tracked", False),
                    description=gd.get("description", ""),
                )
                session.add(g)

            # Импортировать долги
            for dd in data.get("debts", []):
                d = Debt(
                    user_id=user_id,
                    name=dd.get("name", "Долг"),
                    currency=dd.get("currency", "KZT"),
                    balance=dd.get("balance", 0.0),
                )
                session.add(d)
                session.flush()
                for dtd in dd.get("transactions", []):
                    dtype = (DebtType.GAVE
                             if dtd.get("type") == "gave"
                             else DebtType.TOOK)
                    created = None
                    if dtd.get("created_at"):
                        try:
                            created = datetime.fromisoformat(dtd["created_at"])
                        except ValueError:
                            created = None
                    dt = DebtTransaction(
                        debt_id=d.id,
                        type=dtype,
                        amount=dtd.get("amount", 0.0),
                        description=dtd.get("description", ""),
                        created_at=created or datetime.now(),
                    )
                    session.add(dt)

            session.commit()
            imported_username = user.username

            # Импортировать категории
            cat_name_to_id = {}
            for cd in data.get("categories", []):
                c_name = cd.get("name", "").strip()
                if not c_name:
                    continue
                existing_cat = session.query(Category).filter_by(
                    user_id=user_id, name=c_name
                ).first()
                if not existing_cat:
                    cat = Category(
                        user_id=user_id,
                        name=c_name,
                        color=cd.get("color", "#6366f1"),
                        is_default=cd.get("is_default", False),
                    )
                    session.add(cat)
                    session.flush()
                    for kw in cd.get("keywords", []):
                        if kw.strip():
                            session.add(__import__("models.models", fromlist=["CategoryKeyword"]).CategoryKeyword(
                                category_id=cat.id, keyword=kw.lower().strip()
                            ))
                    cat_name_to_id[c_name] = cat.id
                else:
                    cat_name_to_id[c_name] = existing_cat.id

            # Импортировать бюджеты
            for bd in data.get("budgets", []):
                cat_id = cat_name_to_id.get(bd.get("category_name", ""))
                if cat_id:
                    BudgetRepository(session).create_or_update(
                        user_id=user_id,
                        category_id=cat_id,
                        year=bd.get("year", __import__("datetime").date.today().year),
                        month=bd.get("month", __import__("datetime").date.today().month),
                        limit_amount=bd.get("limit_amount", 0.0),
                        warning_threshold=bd.get("warning_threshold", 80.0),
                    )

            session.commit()
            return True, f"Данные успешно импортированы для @{imported_username}"
        except Exception as e:
            session.rollback()
            return False, f"Ошибка импорта: {str(e)}"
        finally:
            session.close()


class BalanceHistoryService:
    """
    Сервис истории баланса для построения линейных графиков.

    Алгоритм:
        1. Берёт все транзакции объекта (кошелёк / долг), сортирует по возрастанию даты.
        2. Вычисляет накопительный баланс после каждой транзакции.
        3. Для запрошенного диапазона (days):
            - Находит последний известный баланс до начала диапазона.
            - Для каждого дня: если есть транзакция — обновляет баланс,
              иначе — использует последнее известное значение (forward fill).
        4. Возвращает список (date, float) длиной ровно days.

    Конвертация для общего баланса: суммирует балансы кошельков,
    конвертируя каждый в main_currency через сохранённые курсы пользователя.
    """

    @staticmethod
    def get_wallet_balance_history(wallet_id: int, days: int) -> list:
        """
        История баланса кошелька за последние N дней.

        Returns:
            list[(date, float)] длиной days, отсортированный по дате.
        """
        from datetime import date as _date
        from models.models import Transaction, TransactionType

        session = get_session()
        try:
            txns = (
                session.query(Transaction)
                .filter_by(wallet_id=wallet_id)
                .order_by(Transaction.created_at.asc())
                .all()
            )
            snapshots = []
            running = 0.0
            for t in txns:
                running += t.amount if t.type == TransactionType.INCOME else -t.amount
                snapshots.append((t.created_at.date(), running))
            return BalanceHistoryService._build_daily(snapshots, days)
        finally:
            session.close()

    @staticmethod
    def get_debt_balance_history(debt_id: int, days: int) -> list:
        """
        История баланса долга за последние N дней.

        Returns:
            list[(date, float)] длиной days.
        """
        from datetime import date as _date
        from models.models import DebtTransaction, DebtType

        session = get_session()
        try:
            txns = (
                session.query(DebtTransaction)
                .filter_by(debt_id=debt_id)
                .order_by(DebtTransaction.created_at.asc())
                .all()
            )
            snapshots = []
            running = 0.0
            for t in txns:
                running += t.amount if t.type == DebtType.GAVE else -t.amount
                snapshots.append((t.created_at.date(), running))
            return BalanceHistoryService._build_daily(snapshots, days)
        finally:
            session.close()

    @staticmethod
    def get_total_balance_history(user_id: int, days: int, main_currency: str) -> list:
        """
        История суммарного баланса всех кошельков пользователя,
        конвертированного в main_currency.

        Конвертация выполняется по сохранённым курсам пользователя
        (ExchangeRateService.get_user_rates). Если прямого курса нет —
        используется обратный или кросс-курс через USD/KZT/RUB.

        Returns:
            list[(date, float)] длиной days.
        """
        from datetime import date as _date, timedelta

        wallets = WalletService.get_user_wallets(user_id)
        if not wallets:
            end = _date.today()
            return [
                (end - timedelta(days=days - 1 - i), 0.0)
                for i in range(days)
            ]

        rates = ExchangeRateService.get_user_rates(user_id)
        wallet_histories = [
            (w.currency, BalanceHistoryService.get_wallet_balance_history(w.id, days))
            for w in wallets
        ]

        result = []
        for i in range(days):
            d = wallet_histories[0][1][i][0]
            total = sum(
                WalletService._convert(hist[i][1], curr, main_currency, rates)
                for curr, hist in wallet_histories
            )
            result.append((d, total))
        return result

    @staticmethod
    def _build_daily(snapshots: list, days: int) -> list:
        """
        Превращает список (date, running_balance) в ежедневный ряд длиной days.

        Дни без транзакций заполняются последним известным значением (forward fill).
        Если до начала диапазона транзакций не было — начальный баланс равен 0.
        """
        from datetime import date as _date, timedelta

        end_date = _date.today()
        start_date = end_date - timedelta(days=days - 1)

        # Баланс в момент начала диапазона (последний снапшот до start_date)
        last_balance = 0.0
        for dt, bal in snapshots:
            if dt < start_date:
                last_balance = bal

        # Последний баланс за каждый день внутри диапазона
        day_balance: dict = {}
        for dt, bal in snapshots:
            if start_date <= dt <= end_date:
                day_balance[dt] = bal  # перезапись → оставляем последнее за день

        result = []
        current = last_balance
        for i in range(days):
            d = start_date + timedelta(days=i)
            if d in day_balance:
                current = day_balance[d]
            result.append((d, current))
        return result

    # ── Расходы / Доходы ─────────────────────────────────────────────────────

    @staticmethod
    def get_total_flow_history(user_id: int, days: int, flow_type: str,
                               aggregation: str, main_currency: str) -> list:
        """
        Ежедневные / еженедельные / ежемесячные расходы или доходы по всем
        кошелькам пользователя, приведённые к main_currency.

        Args:
            flow_type:   'expense' | 'income'
            aggregation: 'daily' | 'weekly' | 'monthly'

        Returns:
            list[(date, float)]  — отсортировано по дате.
        """
        from datetime import date as _date, timedelta
        from models.models import Transaction, TransactionType

        wallets = WalletService.get_user_wallets(user_id)
        rates   = ExchangeRateService.get_user_rates(user_id)

        end_date   = _date.today()
        start_date = end_date - timedelta(days=days - 1)

        t_type = (TransactionType.EXPENSE
                  if flow_type == 'expense' else TransactionType.INCOME)

        session = get_session()
        try:
            daily_totals: dict = {}
            for wallet in wallets:
                txns = (
                    session.query(Transaction)
                    .filter(
                        Transaction.wallet_id  == wallet.id,
                        Transaction.type       == t_type,
                        Transaction.created_at >= start_date,
                        Transaction.created_at <= end_date,
                    )
                    .all()
                )
                for t in txns:
                    d      = t.created_at.date()
                    amount = WalletService._convert(
                        t.amount, wallet.currency, main_currency, rates)
                    daily_totals[d] = daily_totals.get(d, 0.0) + amount
        finally:
            session.close()

        daily_data = [
            (start_date + timedelta(days=i),
             daily_totals.get(start_date + timedelta(days=i), 0.0))
            for i in range(days)
        ]
        return BalanceHistoryService._aggregate_flow(daily_data, aggregation)

    @staticmethod
    def _aggregate_flow(daily_data: list, aggregation: str) -> list:
        """
        Агрегировать ежедневный ряд (date, float) в еженедельный или ежемесячный.

        aggregation: 'daily' | 'weekly' | 'monthly'
        Возвращает список (первая_дата_периода, сумма_за_период).
        """
        if aggregation == 'daily' or not daily_data:
            return daily_data

        result = []
        if aggregation == 'weekly':
            period_start = daily_data[0][0]
            period_sum   = 0.0
            for d, v in daily_data:
                if (d - period_start).days >= 7:
                    result.append((period_start, period_sum))
                    period_start = d
                    period_sum   = v
                else:
                    period_sum += v
            result.append((period_start, period_sum))

        elif aggregation == 'monthly':
            period_key   = (daily_data[0][0].year, daily_data[0][0].month)
            period_start = daily_data[0][0]
            period_sum   = 0.0
            for d, v in daily_data:
                curr_key = (d.year, d.month)
                if curr_key != period_key:
                    result.append((period_start, period_sum))
                    period_key   = curr_key
                    period_start = d
                    period_sum   = v
                else:
                    period_sum += v
            result.append((period_start, period_sum))

        return result if result else daily_data

    # ── Агрегация баланса (resample) ──────────────────────────────────────────

    @staticmethod
    def get_total_balance_history_agg(user_id: int, days: int,
                                       main_currency: str, aggregation: str) -> list:
        """
        Суммарный баланс с опциональной агрегацией.
        aggregation: 'daily' | 'weekly' | 'monthly'
        При 'weekly'/'monthly' берётся значение на КОНЕЦ периода.
        """
        daily = BalanceHistoryService.get_total_balance_history(user_id, days, main_currency)
        return BalanceHistoryService._resample_balance(daily, aggregation)

    @staticmethod
    def _resample_balance(daily_data: list, aggregation: str) -> list:
        """Resample cumulative balance — берём последнее значение за каждый период."""
        if aggregation == 'daily' or not daily_data:
            return daily_data

        result = []
        if aggregation == 'weekly':
            i = 0
            while i < len(daily_data):
                end = min(i + 6, len(daily_data) - 1)
                result.append(daily_data[end])
                i += 7
        elif aggregation == 'monthly':
            curr_key   = (daily_data[0][0].year, daily_data[0][0].month)
            last_entry = daily_data[0]
            for d, v in daily_data:
                m_key = (d.year, d.month)
                if m_key != curr_key:
                    result.append(last_entry)
                    curr_key = m_key
                last_entry = (d, v)
            result.append(last_entry)

        return result if result else daily_data


# ─────────────────────────────────────────────────────────────────────────────
# CategoryService
# ─────────────────────────────────────────────────────────────────────────────

class CategoryService:
    """
    Сервис управления категориями транзакций.
    Поддерживает CRUD, ключевые слова, авто-классификацию и шаблоны.
    """

    DEFAULT_TEMPLATES = [
        ("Еда", "#f59e0b", ["еда", "продукты", "магазин", "кафе", "ресторан",
                             "обед", "ужин", "завтрак", "food", "grocery"]),
        ("Транспорт", "#3b82f6", ["такси", "транспорт", "автобус", "бензин", "метро",
                                  "uber", "яндекс", "авто", "проездной", "transport"]),
        ("Развлечения", "#8b5cf6", ["кино", "театр", "игра", "steam", "netflix",
                                    "spotify", "концерт", "развлечения", "game", "play"]),
        ("Подписки", "#ec4899", ["подписка", "subscription", "apple", "google",
                                  "youtube", "premium", "plan", "monthly"]),
        ("Здоровье", "#10b981", ["аптека", "врач", "клиника", "здоровье",
                                  "медицина", "pharmacy", "doctor", "health"]),
        ("Одежда", "#f97316", ["одежда", "обувь", "zara", "h&m",
                               "wildberries", "ozon", "clothes", "fashion"]),
        ("Прочее", "#6b7280", []),
    ]

    @staticmethod
    def create_category(user_id: int, name: str,
                        color: str = "#6366f1",
                        is_default: bool = False) -> tuple:
        if not name or not name.strip():
            return False, "Название категории не может быть пустым", None
        session = get_session()
        try:
            repo = CategoryRepository(session)
            cat = repo.create_category(user_id, name.strip(), color, is_default)
            return True, "Категория создана", cat
        except Exception as e:
            return False, f"Ошибка: {str(e)}", None
        finally:
            session.close()

    @staticmethod
    def get_user_categories(user_id: int) -> list:
        session = get_session()
        try:
            return CategoryRepository(session).get_by_user(user_id)
        finally:
            session.close()

    @staticmethod
    def update_category(category_id: int, **kwargs) -> tuple:
        session = get_session()
        try:
            cat = CategoryRepository(session).update(category_id, **kwargs)
            if cat:
                return True, "Категория обновлена", cat
            return False, "Категория не найдена", None
        except Exception as e:
            return False, f"Ошибка: {str(e)}", None
        finally:
            session.close()

    @staticmethod
    def delete_category(category_id: int) -> tuple:
        session = get_session()
        try:
            if CategoryRepository(session).delete(category_id):
                return True, "Категория удалена"
            return False, "Категория не найдена"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
        finally:
            session.close()

    @staticmethod
    def add_keyword(category_id: int, keyword: str) -> tuple:
        if not keyword or not keyword.strip():
            return False, "Ключевое слово не может быть пустым", None
        session = get_session()
        try:
            kw = CategoryRepository(session).add_keyword(category_id, keyword.strip())
            return True, "Ключевое слово добавлено", kw
        except Exception as e:
            return False, f"Ошибка: {str(e)}", None
        finally:
            session.close()

    @staticmethod
    def remove_keyword(keyword_id: int) -> tuple:
        session = get_session()
        try:
            if CategoryRepository(session).remove_keyword(keyword_id):
                return True, "Ключевое слово удалено"
            return False, "Ключевое слово не найдено"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
        finally:
            session.close()

    @staticmethod
    def auto_classify(user_id: int, text: str):
        """
        Авто-классификация по тексту.
        Возвращает Category с наибольшим числом совпадений ключевых слов,
        или None если совпадений нет.
        """
        if not text:
            return None
        text_lower = text.lower()
        session = get_session()
        try:
            repo = CategoryRepository(session)
            categories = repo.get_by_user(user_id)
            scores = {}
            for cat in categories:
                score = 0
                for kw in cat.keywords:
                    if kw.keyword and kw.keyword in text_lower:
                        score += 1
                if score > 0:
                    scores[cat.id] = (score, cat)
            if not scores:
                return None
            best_id = max(scores, key=lambda k: scores[k][0])
            return scores[best_id][1]
        finally:
            session.close()

    @staticmethod
    def create_default_templates(user_id: int) -> tuple:
        """Создать стандартный набор категорий (пропускает уже существующие по имени)."""
        session = get_session()
        try:
            repo = CategoryRepository(session)
            existing_names = {c.name for c in repo.get_by_user(user_id)}
            created = 0
            for name, color, keywords in CategoryService.DEFAULT_TEMPLATES:
                if name not in existing_names:
                    cat = repo.create_category(user_id, name, color, False)
                    for kw in keywords:
                        repo.add_keyword(cat.id, kw)
                    created += 1
            return True, f"Создано {created} категорий"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
        finally:
            session.close()


# ─────────────────────────────────────────────────────────────────────────────
# BudgetService
# ─────────────────────────────────────────────────────────────────────────────

class BudgetService:
    """
    Сервис управления бюджетами (месячные лимиты расходов по категориям).
    """

    @staticmethod
    def set_budget(user_id: int, category_id: int,
                   year: int, month: int,
                   limit_amount: float,
                   warning_threshold: float = 80.0) -> tuple:
        if limit_amount <= 0:
            return False, "Лимит должен быть больше нуля", None
        if not (0 < warning_threshold <= 100):
            return False, "Порог предупреждения должен быть от 1 до 100", None
        session = get_session()
        try:
            b = BudgetRepository(session).create_or_update(
                user_id, category_id, year, month, limit_amount, warning_threshold
            )
            return True, "Бюджет установлен", b
        except Exception as e:
            return False, f"Ошибка: {str(e)}", None
        finally:
            session.close()

    @staticmethod
    def get_user_budgets(user_id: int, year: int, month: int) -> list:
        session = get_session()
        try:
            return BudgetRepository(session).get_by_user_month(user_id, year, month)
        finally:
            session.close()

    @staticmethod
    def delete_budget(budget_id: int) -> tuple:
        session = get_session()
        try:
            if BudgetRepository(session).delete(budget_id):
                return True, "Бюджет удалён"
            return False, "Бюджет не найден"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
        finally:
            session.close()

    @staticmethod
    def get_category_spending(user_id: int, category_id: int,
                              year: int, month: int) -> float:
        """
        Суммарные расходы по категории за указанный месяц
        (по всем кошелькам пользователя).
        """
        from models.models import Transaction, TransactionType as TT
        import datetime
        session = get_session()
        try:
            wallets = WalletRepository(session).get_wallets_by_user(user_id)
            wallet_ids = [w.id for w in wallets]
            if not wallet_ids:
                return 0.0
            start = datetime.datetime(year, month, 1)
            end = (datetime.datetime(year + 1, 1, 1)
                   if month == 12
                   else datetime.datetime(year, month + 1, 1))
            total = (
                session.query(Transaction)
                .filter(
                    Transaction.wallet_id.in_(wallet_ids),
                    Transaction.category_id == category_id,
                    Transaction.type == TT.EXPENSE,
                    Transaction.created_at >= start,
                    Transaction.created_at < end,
                )
                .all()
            )
            return sum(t.amount for t in total)
        finally:
            session.close()

    @staticmethod
    def get_budgets_with_progress(user_id: int, year: int, month: int) -> list:
        """
        Возвращает список dict с информацией о каждом бюджете и прогрессе.

        Поля dict: budget, category, spent, limit, pct,
                   over_limit (pct>=100), at_warning (pct>=threshold).
        """
        budgets = BudgetService.get_user_budgets(user_id, year, month)
        result = []
        for b in budgets:
            spent = BudgetService.get_category_spending(
                user_id, b.category_id, year, month
            )
            pct = (spent / b.limit_amount * 100) if b.limit_amount > 0 else 0.0
            result.append({
                "budget": b,
                "category": b.category,
                "spent": spent,
                "limit": b.limit_amount,
                "pct": pct,
                "over_limit": pct >= 100.0,
                "at_warning": pct >= b.warning_threshold,
            })
        return result

