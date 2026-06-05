# -*- coding: utf-8 -*-
"""
Стили Нового UI для MyFinances

Современный минималистичный дизайн, вдохновлённый Tailwind / Linear / Revolut.
Цветовая палитра: Indigo + Slate.
"""

import re

from ui.styles import THEME_DARK, THEME_LIGHT

# ─── Палитра: Светлая тема ───────────────────────────────────────────────────
NEW_COLORS_LIGHT = {
    # Акцент
    "primary":        "#6366F1",
    "primary_hover":  "#4F46E5",
    "primary_light":  "#EEF2FF",
    # Семантика
    "secondary":      "#22C55E",
    "secondary_light":"#DCFCE7",
    "danger":         "#EF4444",
    "danger_light":   "#FEE2E2",
    "warning":        "#F59E0B",
    # Фон
    "bg_main":        "#F8FAFC",
    "bg_sidebar":     "#1E293B",
    "bg_sidebar_hover":"#334155",
    "bg_sidebar_active":"#0F172A",
    "bg_card":        "#FFFFFF",
    "bg_hover":       "#F1F5F9",
    "bg_input":       "#FFFFFF",
    # Текст
    "text_primary":   "#0F172A",
    "text_secondary": "#64748B",
    "text_sidebar":   "#94A3B8",
    "text_sidebar_active": "#FFFFFF",
    "text_on_primary":"#FFFFFF",
    # Границы
    "border":         "#E2E8F0",
    "border_focus":   "#6366F1",
    "border_light":   "#F1F5F9",
    # Баланс-карточка (плоский)
    "balance_bg":     "#4F46E5",
    # Белый (для явных мест)
    "white":          "#FFFFFF",
}

# ─── Палитра: Тёмная тема ────────────────────────────────────────────────────
NEW_COLORS_DARK = {
    "primary":        "#818CF8",
    "primary_hover":  "#6366F1",
    "primary_light":  "#312E81",
    "secondary":      "#4ADE80",
    "secondary_light":"#14532D",
    "danger":         "#F87171",
    "danger_light":   "#7F1D1D",
    "warning":        "#FBBF24",
    "bg_main":        "#0F172A",
    "bg_sidebar":     "#020617",
    "bg_sidebar_hover":"#1E293B",
    "bg_sidebar_active":"#1E293B",
    "bg_card":        "#1E293B",
    "bg_hover":       "#1E293B",
    "bg_input":       "#0F172A",
    "text_primary":   "#E2E8F0",
    "text_secondary": "#94A3B8",
    "text_sidebar":   "#64748B",
    "text_sidebar_active":"#E2E8F0",
    "text_on_primary":"#FFFFFF",
    "border":         "#334155",
    "border_focus":   "#818CF8",
    "border_light":   "#1E293B",
    "balance_bg":     "#4338CA",
    "white":          "#FFFFFF",
}


def get_new_colors(theme: str = THEME_DARK) -> dict:
    """Получить палитру нового UI для заданной темы."""
    return NEW_COLORS_DARK if theme == THEME_DARK else NEW_COLORS_LIGHT


# ─── Хранилище текущей темы нового UI ────────────────────────────────────────
_new_current_theme = THEME_DARK


def set_new_current_theme(theme: str):
    global _new_current_theme
    _new_current_theme = theme


def new_colors():
    """Быстрый доступ к текущей палитре нового UI."""
    return get_new_colors(_new_current_theme)


def nc_primary():       return new_colors()["primary"]
def nc_primary_hover(): return new_colors()["primary_hover"]
def nc_secondary():     return new_colors()["secondary"]
def nc_danger():        return new_colors()["danger"]
def nc_text():          return new_colors()["text_primary"]
def nc_text2():         return new_colors()["text_secondary"]
def nc_bg():            return new_colors()["bg_main"]
def nc_card():          return new_colors()["bg_card"]
def nc_border():        return new_colors()["border"]


def scale_px(v: int) -> int:
    """Масштабировать пиксельное значение (×1.25 при крупном интерфейсе)."""
    from config import get_ui_scale, UI_SCALE_LARGE
    return round(v * 1.25) if get_ui_scale() == UI_SCALE_LARGE else v


def scale_css(css: str) -> str:
    """Масштабировать font-size: NNpx в строке стилей (×1.25 при крупном)."""
    from config import get_ui_scale, UI_SCALE_LARGE
    if get_ui_scale() != UI_SCALE_LARGE:
        return css
    return re.sub(
        r'font-size:\s*(\d+)px',
        lambda m: f"font-size: {round(int(m.group(1)) * 1.25)}px",
        css,
    )


# ─── Генерация QSS ───────────────────────────────────────────────────────────

def get_new_stylesheet(theme: str = THEME_DARK) -> str:
    from config import get_ui_scale, UI_SCALE_LARGE
    c = get_new_colors(theme)
    css = f"""
/* ===================== NEW UI STYLESHEET ===================== */

/* --- Глобальный фон и цвет текста --- */
QMainWindow {{
    background-color: {c['bg_main']};
    color: {c['text_primary']};
}}
QWidget {{
    background-color: {c['bg_main']};
    color: {c['text_primary']};
    font-family: "Segoe UI", "Inter", sans-serif;
}}

/* --- Sidebar --- */
QWidget#new_sidebar {{
    background-color: {c['bg_sidebar']};
}}
QLabel#new_sidebar_title {{
    color: {c['white']};
    font-size: 18px;
    font-weight: 700;
    letter-spacing: 0.5px;
}}
QLabel#new_sidebar_subtitle {{
    color: {c['text_sidebar']};
    font-size: 11px;
}}
QPushButton#new_nav_btn {{
    background: transparent;
    color: {c['text_sidebar']};
    border: none;
    border-left: 3px solid transparent;
    border-radius: 0px;
    padding: 13px 22px;
    text-align: left;
    font-size: 14px;
    font-weight: 500;
}}
QPushButton#new_nav_btn:hover {{
    background-color: {c['bg_sidebar_hover']};
    color: {c['text_sidebar_active']};
}}
QPushButton#new_nav_btn_active {{
    background-color: {c['bg_sidebar_active']};
    color: {c['text_sidebar_active']};
    border: none;
    border-left: 3px solid {c['primary']};
    border-radius: 0px;
    padding: 13px 22px;
    text-align: left;
    font-size: 14px;
    font-weight: 600;
}}

/* --- Avatar circle --- */
QLabel#new_avatar {{
    background-color: {c['primary']};
    color: {c['white']};
    border-radius: 20px;
    font-size: 14px;
    font-weight: 700;
}}

/* --- Кнопки --- */
QPushButton {{
    background-color: {c['primary']};
    color: {c['text_on_primary']};
    border: none;
    border-radius: 8px;
    padding: 10px 18px;
    font-size: 14px;
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: {c['primary_hover']};
}}
QPushButton:pressed {{
    background-color: {c['primary_hover']};
}}
QPushButton#btn_secondary {{
    background-color: {c['secondary']};
}}
QPushButton#btn_secondary:hover {{
    background-color: {c['secondary']};
}}
QPushButton#btn_danger {{
    background-color: {c['danger']};
}}
QPushButton#btn_danger:hover {{
    background-color: {c['danger']};
}}
QPushButton#btn_ghost {{
    background: transparent;
    color: {c['primary']};
    border: 1px solid {c['border']};
    border-radius: 8px;
    font-size: 14px;
}}
QPushButton#btn_ghost:hover {{
    background-color: {c['primary_light']};
}}

/* --- Поля ввода --- */
QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox {{
    background-color: {c['bg_input']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 14px;
}}
QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 2px solid {c['border_focus']};
}}
/* QLineEdit placeholder color is set via QPalette, not supported in Qt QSS */

/* --- Combobox --- */
QComboBox {{
    background-color: {c['bg_input']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 14px;
}}
QComboBox:focus {{
    border: 2px solid {c['border_focus']};
}}
QComboBox QAbstractItemView {{
    background-color: {c['bg_card']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    selection-background-color: {c['primary_light']};
    selection-color: {c['primary']};
}}

/* --- Метки --- */
QLabel {{
    color: {c['text_primary']};
    background: transparent;
    border: none;
}}

/* --- Карточки (GroupBox) --- */
QGroupBox {{
    background-color: {c['bg_card']};
    border: 1px solid {c['border']};
    border-radius: 10px;
    padding: 16px;
    margin-top: 10px;
    color: {c['text_primary']};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {c['text_primary']};
    font-weight: 600;
}}

/* --- Таблицы --- */
QTableWidget {{
    background-color: {c['bg_card']};
    alternate-background-color: {c['bg_main']};
    gridline-color: {c['border']};
    border: 1px solid {c['border']};
    border-radius: 8px;
    color: {c['text_primary']};
}}
QTableWidget::item {{
    padding: 8px;
    border: none;
    color: {c['text_primary']};
}}
QHeaderView {{
    background-color: {c['bg_hover']};
    border: none;
}}
QHeaderView::section {{
    background-color: {c['bg_hover']};
    color: {c['text_primary']};
    padding: 10px 8px;
    border: none;
    border-bottom: 2px solid {c['border']};
    font-weight: 600;
    font-size: 13px;
}}
QHeaderView::section:vertical {{
    background-color: {c['bg_hover']};
    color: {c['text_secondary']};
    padding: 4px 8px;
    border: none;
    border-right: 2px solid {c['border']};
    font-size: 11px;
}}
QTableCornerButton::section {{
    background-color: {c['bg_hover']};
    border: none;
    border-bottom: 2px solid {c['border']};
}}

/* --- Tabs --- */
QTabWidget::pane {{
    border: 1px solid {c['border']};
    background-color: {c['bg_card']};
    border-radius: 8px;
}}
QTabBar::tab {{
    background-color: transparent;
    color: {c['text_secondary']};
    padding: 10px 32px;
    margin: 0 2px;
    border: none;
    border-bottom: 2px solid transparent;
    font-weight: 600;
    font-size: 14px;
    min-width: 140px;
}}
QTabBar::tab:selected {{
    color: {c['primary']};
    border-bottom: 2px solid {c['primary']};
}}
QTabBar::tab:hover {{
    color: {c['text_primary']};
}}

/* --- Scrollbar --- */
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background-color: {c['border']};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {c['text_secondary']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 8px;
}}
QScrollBar::handle:horizontal {{
    background-color: {c['border']};
    border-radius: 4px;
}}

/* --- Radio Button --- */
QRadioButton {{
    color: {c['text_primary']};
    spacing: 8px;
    padding: 6px;
    font-size: 14px;
}}
QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 9px;
}}
QRadioButton::indicator:unchecked {{
    background-color: {c['bg_input']};
    border: 2px solid {c['border']};
}}
QRadioButton::indicator:checked {{
    background-color: {c['primary']};
    border: 2px solid {c['primary']};
}}

/* --- CheckBox --- */
QCheckBox {{
    color: {c['text_primary']};
    spacing: 8px;
    font-size: 14px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
}}
QCheckBox::indicator:unchecked {{
    background-color: {c['bg_input']};
    border: 2px solid {c['border']};
}}
QCheckBox::indicator:checked {{
    background-color: {c['primary']};
    border: 2px solid {c['primary']};
}}

/* --- Dialog --- */
QDialog {{
    background-color: {c['bg_main']};
    color: {c['text_primary']};
}}

/* --- ScrollArea --- */
QScrollArea {{
    border: none;
    background: transparent;
}}

/* --- ProgressBar --- */
QProgressBar {{
    background-color: {c['border']};
    border-radius: 6px;
    border: none;
    text-align: center;
    font-size: 10px;
    color: {c['text_secondary']};
}}
QProgressBar::chunk {{
    background-color: {c['primary']};
    border-radius: 6px;
}}

/* --- MessageBox --- */
QMessageBox {{
    background-color: {c['bg_card']};
    color: {c['text_primary']};
}}
QMessageBox QLabel {{
    color: {c['text_primary']};
}}

/* --- DateEdit / DateTimeEdit --- */
QDateEdit, QDateTimeEdit {{
    background-color: {c['bg_input']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 14px;
}}
QDateEdit:focus, QDateTimeEdit:focus {{
    border: 2px solid {c['border_focus']};
}}
QDateEdit::drop-down, QDateTimeEdit::drop-down {{
    border: none;
    width: 24px;
}}
QDateEdit::down-arrow, QDateTimeEdit::down-arrow {{
    width: 10px;
    height: 10px;
}}

/* --- Calendar popup --- */
QCalendarWidget {{
    background-color: {c['bg_card']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 8px;
}}
QCalendarWidget QToolButton {{
    background-color: {c['bg_card']};
    color: {c['text_primary']};
    border: none;
    padding: 4px 8px;
    font-size: 13px;
    font-weight: 600;
}}
QCalendarWidget QToolButton:hover {{
    background-color: {c['bg_hover']};
    border-radius: 4px;
}}
QCalendarWidget QMenu {{
    background-color: {c['bg_card']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
}}
QCalendarWidget QSpinBox {{
    background-color: {c['bg_input']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 4px;
    padding: 2px 4px;
}}
QCalendarWidget QWidget#qt_calendar_navigationbar {{
    background-color: {c['bg_hover']};
    border-bottom: 1px solid {c['border']};
    border-radius: 0px;
}}
QCalendarWidget QAbstractItemView {{
    background-color: {c['bg_card']};
    color: {c['text_primary']};
    selection-background-color: {c['primary']};
    selection-color: #ffffff;
    gridline-color: {c['border']};
    border: none;
    outline: none;
}}
QCalendarWidget QAbstractItemView:disabled {{
    color: {c['text_secondary']};
}}
"""

    # Крупный интерфейс: масштабируем все font-size на 25 %
    if get_ui_scale() == UI_SCALE_LARGE:
        def _scale_font(m):
            return f"font-size: {round(int(m.group(1)) * 1.25)}px"
        css = re.sub(r'font-size:\s*(\d+)px', _scale_font, css)

    return css


# ─── Windows dark title bar ──────────────────────────────────────────────────

def apply_dark_title_bar(widget) -> None:
    """
    Apply Windows 10/11 dark mode title bar (close/min/max buttons area).
    No-op on non-Windows platforms or if DWM is not available.
    """
    try:
        import ctypes
        import sys
        if sys.platform != "win32":
            return
        hwnd = int(widget.winId())
        # DWMWA_USE_IMMERSIVE_DARK_MODE = 20 (Win10 1903+)
        # Fallback to 19 for older builds
        for attr in (20, 19):
            try:
                value = ctypes.c_int(1)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, attr,
                    ctypes.byref(value),
                    ctypes.sizeof(value)
                )
            except OSError:
                continue
    except Exception:
        pass


# ─── Dark-themed dialog helpers ──────────────────────────────────────────────
# Use these instead of static QMessageBox/QInputDialog calls so that
# the Windows title bar gets the dark-mode treatment in New UI.

def _is_new_ui() -> bool:
    from config import get_ui_mode, UI_MODE_NEW
    return get_ui_mode() == UI_MODE_NEW


def _apply_new_style(widget) -> None:
    """Apply current-theme stylesheet + dark title bar to any QWidget."""
    from config import get_current_theme
    widget.setStyleSheet(get_new_stylesheet(get_current_theme()))
    widget.winId()          # force native window handle creation
    apply_dark_title_bar(widget)


# ── QMessageBox wrappers ─────────────────────────────────────────────────────

def msgbox_question(parent, title: str, text: str,
                    buttons=None, default=None) -> int:
    """QMessageBox.question with dark title bar in New UI."""
    from PyQt5.QtWidgets import QMessageBox
    if buttons is None:
        buttons = QMessageBox.Yes | QMessageBox.No
    if _is_new_ui():
        msg = QMessageBox(QMessageBox.Question, title, text, buttons, parent)
        _apply_new_style(msg)
        return msg.exec_()
    return QMessageBox.question(parent, title, text, buttons)


def msgbox_warning(parent, title: str, text: str) -> int:
    """QMessageBox.warning with dark title bar in New UI."""
    from PyQt5.QtWidgets import QMessageBox
    if _is_new_ui():
        msg = QMessageBox(QMessageBox.Warning, title, text, QMessageBox.Ok, parent)
        _apply_new_style(msg)
        return msg.exec_()
    return QMessageBox.warning(parent, title, text)


def msgbox_information(parent, title: str, text: str) -> int:
    """QMessageBox.information with dark title bar in New UI."""
    from PyQt5.QtWidgets import QMessageBox
    if _is_new_ui():
        msg = QMessageBox(QMessageBox.Information, title, text, QMessageBox.Ok, parent)
        _apply_new_style(msg)
        return msg.exec_()
    return QMessageBox.information(parent, title, text)


def msgbox_critical(parent, title: str, text: str) -> int:
    """QMessageBox.critical with dark title bar in New UI."""
    from PyQt5.QtWidgets import QMessageBox
    if _is_new_ui():
        msg = QMessageBox(QMessageBox.Critical, title, text, QMessageBox.Ok, parent)
        _apply_new_style(msg)
        return msg.exec_()
    return QMessageBox.critical(parent, title, text)


# ── QInputDialog wrappers ────────────────────────────────────────────────────

def inputdlg_text(parent, title: str, label: str,
                  text: str = "") -> tuple[str, bool]:
    """QInputDialog.getText with dark title bar in New UI."""
    from PyQt5.QtWidgets import QInputDialog, QDialog
    if _is_new_ui():
        dlg = QInputDialog(parent)
        dlg.setWindowTitle(title)
        dlg.setLabelText(label)
        dlg.setTextValue(text)
        dlg.setInputMode(QInputDialog.TextInput)
        _apply_new_style(dlg)
        ok = dlg.exec_() == QDialog.Accepted
        return dlg.textValue(), ok
    return QInputDialog.getText(parent, title, label, text=text)


def inputdlg_item(parent, title: str, label: str, items: list,
                  current: int = 0, editable: bool = False) -> tuple[str, bool]:
    """QInputDialog.getItem with dark title bar in New UI."""
    from PyQt5.QtWidgets import QInputDialog, QDialog
    if _is_new_ui():
        dlg = QInputDialog(parent)
        dlg.setWindowTitle(title)
        dlg.setLabelText(label)
        dlg.setComboBoxItems(items)
        dlg.setComboBoxEditable(editable)
        if 0 <= current < len(items):
            dlg.setTextValue(items[current])
        _apply_new_style(dlg)
        ok = dlg.exec_() == QDialog.Accepted
        return dlg.textValue(), ok
    return QInputDialog.getItem(parent, title, label, items, current, editable)


def inputdlg_double(parent, title: str, label: str,
                    value: float = 0.0, min_val: float = 0.0,
                    max_val: float = 999_999_999.0,
                    decimals: int = 2) -> tuple[float, bool]:
    """QInputDialog.getDouble with dark title bar in New UI."""
    from PyQt5.QtWidgets import QInputDialog, QDialog
    if _is_new_ui():
        dlg = QInputDialog(parent)
        dlg.setWindowTitle(title)
        dlg.setLabelText(label)
        dlg.setInputMode(QInputDialog.DoubleInput)
        dlg.setDoubleValue(value)
        dlg.setDoubleMinimum(min_val)
        dlg.setDoubleMaximum(max_val)
        dlg.setDoubleDecimals(decimals)
        _apply_new_style(dlg)
        ok = dlg.exec_() == QDialog.Accepted
        return dlg.doubleValue(), ok
    return QInputDialog.getDouble(
        parent, title, label, value, min_val, max_val, decimals
    )
