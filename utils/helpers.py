# -*- coding: utf-8 -*-
"""
Вспомогательные функции для приложения MyFinances

Функции:
- hash_password(): хеширование пароля
- verify_password(): проверка пароля против хеша
- validate_email(): валидация email адреса
- validate_amount(): валидация суммы (положительное число)
- format_date(): форматирование даты для отображения
"""

import re
from datetime import datetime, timezone, timedelta
import bcrypt
from config import PASSWORD_MIN_LENGTH, ALMATY_TZ, now_almaty  # re-export now_almaty


def hash_password(password: str) -> str:
    """
    Хешировать пароль с использованием bcrypt
    
    Args:
        password: пароль в открытом виде
        
    Returns:
        str: хеш пароля (безопасно для хранения в БД)
    """
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Проверить, совпадает ли пароль с хешем
    
    Args:
        password: пароль для проверки (открытый вид)
        password_hash: хеш из БД
        
    Returns:
        bool: True если пароль верный, False иначе
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception:
        return False


def validate_email(email: str) -> bool:
    """
    Валидация email адреса
    
    Args:
        email: адрес для проверки
        
    Returns:
        bool: True если формат верный, False иначе
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password: str) -> tuple[bool, str]:
    """
    Валидация пароля
    
    Args:
        password: пароль для проверки
        
    Returns:
        tuple: (is_valid, error_message)
            - is_valid (bool): валиден ли пароль
            - error_message (str): сообщение об ошибке (пусто если валиден)
    """
    if not password:
        return False, "Пароль не может быть пустым"
    
    if len(password) < PASSWORD_MIN_LENGTH:
        return False, f"Пароль должен содержать минимум {PASSWORD_MIN_LENGTH} символов"
    
    return True, ""


def validate_username(username: str) -> tuple[bool, str]:
    """
    Валидация имени пользователя
    
    Args:
        username: имя пользователя для проверки
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not username:
        return False, "Имя пользователя не может быть пустым"
    
    if len(username) < 3:
        return False, "Имя пользователя должно содержать минимум 3 символа"
    
    if len(username) > 50:
        return False, "Имя пользователя не может быть длиннее 50 символов"
    
    # Только буквы, цифры, подчеркивание и дефис
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "Имя может содержать только буквы, цифры, подчёркивание и дефис"
    
    return True, ""


def validate_amount(amount: str) -> tuple[bool, str, float]:
    """
    Валидация суммы (должна быть положительным числом)
    
    Args:
        amount: сумма в виде строки
        
    Returns:
        tuple: (is_valid, error_message, parsed_amount)
            - is_valid (bool): валидна ли сумма
            - error_message (str): сообщение об ошибке (пусто если валидна)
            - parsed_amount (float): распарсенное значение или 0.0
    """
    try:
        value = float(amount)
        if value <= 0:
            return False, "Сумма должна быть больше нуля", 0.0
        return True, "", value
    except ValueError:
        return False, "Сумма должна быть числом", 0.0


def format_date(date: datetime, format_str: str = "%d.%m.%Y %H:%M") -> str:
    """
    Форматирование даты для отображения в UI
    
    Args:
        date: объект datetime
        format_str: строка формата (по умолчанию "23.03.2026 14:30")
        
    Returns:
        str: отформатированная дата
    """
    if not date:
        return ""
    return date.strftime(format_str)


def format_currency(amount: float, currency: str = "KZT") -> str:
    """
    Форматирование денежной суммы для отображения
    
    Args:
        amount: сумма
        currency: код валюты
        
    Returns:
        str: форматированная строка (например, "1 234.50 KZT")
    """
    return f"{amount:,.2f} {currency}".replace(",", " ")
