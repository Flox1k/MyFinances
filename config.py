# -*- coding: utf-8 -*-
"""
Конфигурация приложения MyFinances
"""

import os
import json
import sys
from datetime import datetime, timezone, timedelta

# Часовой пояс Алматы (GMT+5)
ALMATY_TZ = timezone(timedelta(hours=5))


def now_almaty() -> datetime:
    """Текущее время по Алматы (GMT+5), возвращает naive datetime."""
    return datetime.now(ALMATY_TZ).replace(tzinfo=None)

# Базовый путь проекта
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Определение пути для данных (сборка .exe или разработка) ───────────────
def _get_data_dir():
    """
    Получить папку для хранения данных приложения (БД, настройки).
    Для .exe версии: используется AppData\Local\MyFinances
    Для разработки: используется папка проекта
    """
    if getattr(sys, 'frozen', False):
        # Приложение запущено как exe
        data_dir = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'MyFinances')
    else:
        # Режим разработки
        data_dir = BASE_DIR
    
    # Создать папку, если её нет
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

DATA_DIR = _get_data_dir()

# Путь к БД SQLite
DATABASE_URL = f"sqlite:///{os.path.join(DATA_DIR, 'myfinances.db')}"

# Путь к файлу конфигурации пользователя
CONFIG_FILE = os.path.join(DATA_DIR, 'user_settings.json')

# Константы приложения
APP_NAME = "MyFinances"
APP_VERSION = "1.0.0"

# Константы типов транзакций
TRANSACTION_INCOME = "income"
TRANSACTION_EXPENSE = "expense"

TRANSACTION_TYPES = [
    (TRANSACTION_INCOME, "Доход"),
    (TRANSACTION_EXPENSE, "Расход"),
]

# Валюты
DEFAULT_CURRENCY = "KZT"
SUPPORTED_CURRENCIES = ["KZT", "USD", "EUR", "GBP", "RUB"]
MULTI_CURRENCIES = ["KZT", "USD", "RUB"]  # Основные валюты для мультивалютности

# PyQt5 конфигурация
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 600

# Размеры таблиц
TABLE_ROW_HEIGHT = 30

# Константы для хеширования паролей
PASSWORD_MIN_LENGTH = 6

# Темы
DEFAULT_THEME = "dark"  # По умолчанию тёмная тема
AVAILABLE_THEMES = ["light", "dark"]


def load_user_settings():
    """Загрузить настройки пользователя из JSON файла"""
    default_settings = {
        "theme": DEFAULT_THEME,
        "main_currency": DEFAULT_CURRENCY
    }
    
    if not os.path.exists(CONFIG_FILE):
        return default_settings
    
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            return settings if settings else default_settings
    except (json.JSONDecodeError, IOError):
        return default_settings


def save_user_settings(settings):
    """Сохранить настройки пользователя в JSON файл"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except IOError as e:
        print(f"Ошибка при сохранении настроек: {e}")


def get_current_theme():
    """Получить текущую тему приложения"""
    settings = load_user_settings()
    return settings.get("theme", DEFAULT_THEME)


def set_theme(theme: str):
    """Установить тему приложения"""
    settings = load_user_settings()
    if theme in AVAILABLE_THEMES:
        settings["theme"] = theme
        save_user_settings(settings)
        return True
    return False


def get_main_currency():
    """Получить основную валюту пользователя"""
    settings = load_user_settings()
    return settings.get("main_currency", DEFAULT_CURRENCY)


def set_main_currency(currency: str):
    """Установить основную валюту"""
    if currency in MULTI_CURRENCIES:
        settings = load_user_settings()
        settings["main_currency"] = currency
        save_user_settings(settings)
        return True
    return False


# ── UI режим ────────────────────────────────────────────────────────────────
UI_MODE_OLD = "old"
UI_MODE_NEW = "new"
DEFAULT_UI_MODE = UI_MODE_NEW


def get_ui_mode() -> str:
    """Получить текущий режим UI ('old' или 'new')"""
    settings = load_user_settings()
    return settings.get("ui_mode", DEFAULT_UI_MODE)


def set_ui_mode(mode: str) -> bool:
    """Установить режим UI"""
    if mode in (UI_MODE_OLD, UI_MODE_NEW):
        settings = load_user_settings()
        settings["ui_mode"] = mode
        save_user_settings(settings)
        return True
    return False


# ── Масштаб интерфейса ──────────────────────────────────────────────────────
UI_SCALE_STANDARD = "standard"
UI_SCALE_LARGE    = "large"
DEFAULT_UI_SCALE  = UI_SCALE_STANDARD


def get_ui_scale() -> str:
    """Получить масштаб интерфейса ('standard' или 'large')."""
    settings = load_user_settings()
    return settings.get("ui_scale", DEFAULT_UI_SCALE)


def set_ui_scale(scale: str) -> bool:
    """Установить масштаб интерфейса."""
    if scale in (UI_SCALE_STANDARD, UI_SCALE_LARGE):
        settings = load_user_settings()
        settings["ui_scale"] = scale
        save_user_settings(settings)
        return True
    return False


# ── Цвет фона сводки долгов ──────────────────────────────────────────────────
DEBTS_SUMMARY_COLOR_OPTIONS = [
    ("Тёмный синий",      "#172554"),
    ("Полночный индиго",  "#1e1b4b"),
    ("Сланцевый",         "#1e293b"),
    ("Антрацит",          "#18181b"),
    ("Военно-морской",    "#14213d"),
    ("Тёмно-серый",       "#1c1c2e"),
    ("Уголь",             "#0d1321"),
    ("Тёмный изумруд",    "#052e16"),
]
DEFAULT_DEBTS_SUMMARY_COLOR = "#172554"


def get_debts_summary_color() -> str:
    settings = load_user_settings()
    return settings.get("debts_summary_color", DEFAULT_DEBTS_SUMMARY_COLOR)


def set_debts_summary_color(color: str) -> None:
    settings = load_user_settings()
    settings["debts_summary_color"] = color
    save_user_settings(settings)


# ── Аватар пользователя ──────────────────────────────────────────────────────

def get_user_avatar(user_id: int) -> str:
    """Получить путь к аватару пользователя (или '' если не задан)."""
    settings = load_user_settings()
    return settings.get(f"avatar_{user_id}", "")


def set_user_avatar(user_id: int, path: str) -> None:
    """Сохранить путь к аватару пользователя."""
    settings = load_user_settings()
    settings[f"avatar_{user_id}"] = path
    save_user_settings(settings)
