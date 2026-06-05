# -*- coding: utf-8 -*-
"""
Стили и цветовая схема для приложения MyFinances

Использует современный дизайн с приятной цветовой палитрой
Поддерживает тёмную и светлую темы
"""

# Темы
THEME_LIGHT = "light"
THEME_DARK = "dark"

# Цветовые палитры для разных тем
COLORS_LIGHT = {
    # Основные цвета
    "primary": "#2563eb",      # Синий (основной)
    "secondary": "#10b981",     # Зелёный (доход)
    "danger": "#ef4444",        # Красный (расход)
    "warning": "#f59e0b",       # Оранжевый (предупреждение)
    
    # Нейтральные цвета
    "white": "#ffffff",
    "black": "#1f2937",
    "gray": "#6b7280",
    "gray_light": "#f3f4f6",
    "gray_lighter": "#e5e7eb",
    
    # Фон
    "bg_main": "#ffffff",
    "bg_sidebar": "#1e293b",
    "bg_hover": "#f8f9fa",
    "bg_card": "#f9fafb",
    "text_primary": "#1f2937",
    "text_secondary": "#6b7280",
}

COLORS_DARK = {
    # Основные цвета
    "primary": "#60a5fa",      # Голубой (яркий и видимый в тёмной теме)
    "secondary": "#34d399",     # Зелёный (доход, более яркий)
    "danger": "#f87171",        # Красный (розовый оттенок для мягкости)
    "warning": "#fbbf24",       # Оранжевый
    
    # Нейтральные цвета
    "white": "#ffffff",
    "black": "#1f2937",
    "gray": "#9ca3af",
    "gray_light": "#4b5563",
    "gray_lighter": "#6b7280",
    
    # Фон (вдохновляемся дизайном GitHub Dark)
    "bg_main": "#0d1117",       # Очень тёмный фон
    "bg_sidebar": "#161b22",    # Боковое меню (немного светлее)
    "bg_hover": "#1c2128",      # При наведении
    "bg_card": "#21262d",       # Карточки (светлее для контраста)
    "text_primary": "#c9d1d9",  # Светло-серый текст (хорошо видно)
    "text_secondary": "#8b949e", # Серый текст для вторичной информации
}

# По умолчанию явно указываем светлую тему
COLORS = COLORS_LIGHT


def get_stylesheet(theme: str = THEME_DARK) -> str:
    """
    Получить CSS стили для приложения в зависимости от темы
    
    Args:
        theme: 'light' для светлой темы, 'dark' для тёмной (по умолчанию)
        
    Returns:
        CSS стили в виде строки
    """
    colors = COLORS_DARK if theme == THEME_DARK else COLORS_LIGHT
    
    # Определяем цвета для карточек
    if theme == THEME_LIGHT:
        card_bg = "#f9fafb"
        card_border = "#e5e7eb"
        card_text = "#1f2937"
        card_hover_bg = "#f3f4f6"
        card_hover_border = "#d1d5db"
        input_bg = "#ffffff"
        input_text = "#1f2937"
        input_border = "#e5e7eb"
        input_border_focus = "#2563eb"
    else:
        # Тёмная тема с улучшенным контрастом
        card_bg = "#21262d"
        card_border = "#30363d"
        card_text = "#c9d1d9"
        card_hover_bg = "#30363d"
        card_hover_border = "#444c56"
        input_bg = "#0d1117"
        input_text = "#c9d1d9"
        input_border = "#30363d"
        input_border_focus = "#60a5fa"
    
    stylesheet = f"""
/* === Главное окно === */
QMainWindow {{
    background-color: {colors['bg_main']};
    color: {colors['text_primary']};
}}

/* === Боковое меню === */
QWidget#sidebar {{
    background-color: {colors['bg_sidebar']};
    border-right: 1px solid {colors['gray_lighter']};
}}

QLabel#sidebar_title {{
    color: {colors['white']};
    font-size: 16px;
    font-weight: bold;
    padding: 20px 15px;
    background-color: {colors['primary']};
}}

/* === Кнопки меню === */
QPushButton#menu_button {{
    background-color: {colors['bg_sidebar']};
    color: {colors['text_secondary']};
    border: none;
    padding: 15px 20px;
    text-align: left;
    font-size: 13px;
    font-weight: 500;
    border-left: 3px solid transparent;
    margin: 5px 0px;
}}

QPushButton#menu_button:hover {{
    background-color: {colors['bg_hover']};
    border-left: 3px solid {colors['primary']};
    color: {colors['text_primary']};
}}

QPushButton#menu_button:pressed {{
    background-color: {colors['bg_card']};
}}

QPushButton#menu_button_active {{
    background-color: {colors['bg_card']};
    color: {colors['primary']};
    border-left: 3px solid {colors['primary']};
    font-weight: 600;
}}

/* === Кнопки действий === */
QPushButton {{
    background-color: {colors['primary']};
    color: {colors['white']};
    border: none;
    border-radius: 6px;
    padding: 10px 16px;
    font-size: 12px;
    font-weight: 500;
}}

QPushButton:hover {{
    background-color: {colors['primary']};
    opacity: 0.85;
}}

QPushButton:pressed {{
    background-color: {colors['primary']};
    opacity: 0.7;
}}

QPushButton#btn_secondary {{
    background-color: {colors['secondary']};
}}

QPushButton#btn_secondary:hover {{
    background-color: {colors['secondary']};
    opacity: 0.85;
}}

QPushButton#btn_danger {{
    background-color: {colors['danger']};
}}

QPushButton#btn_danger:hover {{
    background-color: {colors['danger']};
    opacity: 0.85;
}}

/* === Таблицы === */
QTableWidget {{
    background-color: {card_bg};
    alternate-background-color: {colors['bg_main']};
    gridline-color: {input_border};
    border: 1px solid {input_border};
    border-radius: 6px;
    color: {colors['text_primary']};
}}

QTableWidget::item {{
    padding: 8px;
    border: none;
    color: {colors['text_primary']};
    background-color: {card_bg};
}}

QHeaderView::section {{
    background-color: {colors['bg_card']};
    color: {colors['text_primary']};
    padding: 8px;
    border: 1px solid {input_border};
    font-weight: 600;
}}

/* === Поля ввода === */
QLineEdit, QTextEdit, QComboBox {{
    background-color: {input_bg};
    color: {input_text};
    border: 1px solid {input_border};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 12px;
}}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
    border: 1px solid {input_border_focus};
    outline: none;
}}

QLineEdit::placeholder {{
    color: {colors['text_secondary']};
}}

/* === Метки === */
QLabel {{
    color: {colors['text_primary']};
}}

QLabel#title {{
    font-size: 18px;
    font-weight: bold;
    color: {colors['text_primary']};
}}

QLabel#subtitle {{
    font-size: 14px;
    color: {colors['text_secondary']};
}}

/* === Карточки (групповые боксы) === */
QGroupBox {{
    background-color: {colors['bg_card']};
    border: 1px solid {input_border};
    border-radius: 8px;
    padding: 15px;
    margin-top: 8px;
    color: {colors['text_primary']};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 3px;
}}

/* === Диалоги === */
QDialog {{
    background-color: {colors['bg_main']};
    color: {colors['text_primary']};
}}

/* === Scrollbar === */
QScrollBar:vertical {{
    background-color: {colors['bg_main']};
    width: 12px;
    border-radius: 6px;
}}

QScrollBar::handle:vertical {{
    background-color: {colors['gray_light']};
    border-radius: 6px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {colors['gray_lighter']};
}}

/* === Tab Widget === */
QTabBar::tab {{
    background-color: {colors['bg_card']};
    color: {colors['text_primary']};
    padding: 8px 20px;
    margin: 0px 2px;
    border-radius: 4px;
}}

QTabBar::tab:selected {{
    background-color: {colors['primary']};
    color: {colors['white']};
}}

/* === Карточки кошельков и курсов === */
QPushButton#wallet_card {{
    background-color: {card_bg};
    border: 1px solid {card_border};
    border-radius: 6px;
    padding: 10px 15px;
    text-align: left;
    color: {card_text};
}}

QPushButton#wallet_card:hover {{
    background-color: {card_hover_bg};
    border: 1px solid {card_hover_border};
}}

QPushButton#wallet_card:pressed {{
    background-color: {card_hover_bg};
}}

/* === Radio Button === */
QRadioButton {{
    color: {colors['text_primary']};
    spacing: 5px;
    padding: 5px;
}}

QRadioButton::indicator {{
    width: 18px;
    height: 18px;
}}

QRadioButton::indicator:unchecked {{
    background-color: {input_bg};
    border: 1px solid {input_border};
    border-radius: 9px;
}}

QRadioButton::indicator:unchecked:hover {{
    border: 1px solid {input_border_focus};
}}

QRadioButton::indicator:checked {{
    background-color: {input_bg};
    border: 2px solid {colors['primary']};
    border-radius: 9px;
}}

QRadioButton::indicator:checked:after {{
    background-color: {colors['primary']};
    width: 8px;
    height: 8px;
    border-radius: 4px;
    position: absolute;
    top: 4px;
    left: 4px;
}}
"""
    return stylesheet

# По умолчанию используем тёмную тему
STYLESHEET = get_stylesheet(THEME_DARK)


# Текущая активная тема (для получения цветов из других файлов)
_current_theme = THEME_DARK


def set_current_theme(theme: str):
    """Установить текущую активную тему для глобального использования"""
    global _current_theme
    _current_theme = theme


def get_current_colors():
    """Получить цветовую палитру текущей темы"""
    return COLORS_DARK if _current_theme == THEME_DARK else COLORS_LIGHT


def get_income_color():
    """Получить цвет для доходов (зелёный)"""
    colors = get_current_colors()
    return colors["secondary"]


def get_expense_color():
    """Получить цвет для расходов (красный)"""
    colors = get_current_colors()
    return colors["danger"]


def get_primary_color():
    """Получить основной цвет (синий)"""
    colors = get_current_colors()
    return colors["primary"]


def get_text_color():
    """Получить основной цвет текста"""
    colors = get_current_colors()
    return colors["text_primary"]


def get_text_secondary_color():
    """Получить вторичный цвет текста"""
    colors = get_current_colors()
    return colors["text_secondary"]


def get_card_style(label_text: str = "", text_color: str = None, secondary: bool = False) -> str:
    """
    Получить CSS стиль для элемента карточки
    
    Args:
        label_text: текст метки (не используется в стиле, но может быть полезно)
        text_color: цвет текста (если None, используется стандартный)
        secondary: использовать вторичный цвет текста
        
    Returns:
        CSS стиль в виде строки
    """
    colors = get_current_colors()
    
    if text_color is None:
        if secondary:
            text_color = colors["text_secondary"]
        else:
            text_color = colors["text_primary"]
    
    return f"color: {text_color};"


def get_card_title_style(size: int = 14) -> str:
    """Получить стиль для заголовока карточки"""
    text_color = get_text_color()
    return f"font-size: {size}px; font-weight: bold; color: {text_color};"


def get_card_subtitle_style(size: int = 11) -> str:
    """Получить стиль для подзаголовка карточки"""
    text_color = get_text_secondary_color()
    return f"font-size: {size}px; color: {text_color};"
