# -*- coding: utf-8 -*-
"""
Новое окно входа / регистрации (New UI)

Центрированная карточка, чистый дизайн без эмодзи,
inline-сообщения об ошибках.
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTabWidget, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QColor

from services.services import AuthService
from models.models import User
from ui.toast_notification import show_toast
from ui.new_styles import get_new_stylesheet, set_new_current_theme, get_new_colors, apply_dark_title_bar
from config import get_current_theme


class NewLoginWindow(QMainWindow):
    """
    Современное окно входа / регистрации (New UI).
    Эмитит login_success(User) при успешном входе.
    """

    login_success = pyqtSignal(User)

    def __init__(self):
        super().__init__()
        self.theme = get_current_theme()
        set_new_current_theme(self.theme)
        self.c = get_new_colors(self.theme)

        self.setWindowTitle("MyFinances")
        self.setMinimumSize(520, 620)
        self.resize(520, 640)
        self.setStyleSheet(get_new_stylesheet(self.theme))
        self._build_ui()
        apply_dark_title_bar(self)

    # ─── UI ───────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        root_lay = QVBoxLayout(root)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setAlignment(Qt.AlignCenter)

        # Фон
        root.setStyleSheet(f"background-color: {self.c['bg_main']};")

        # ─── Центральная карточка ─────────────────────────────────────
        card = QWidget()
        card.setObjectName("login_card")
        card.setFixedWidth(420)
        card.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        card.setStyleSheet(f"""
            QWidget#login_card {{
                background-color: {self.c['bg_card']};
                border: 1px solid {self.c['border']};
                border-radius: 16px;
            }}
            QWidget#login_card QWidget,
            QWidget#login_card QLabel {{
                border: none;
                background: transparent;
            }}
        """)
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(36, 36, 36, 36)
        card_lay.setSpacing(8)

        # Заголовок
        brand = QLabel("MyFinances")
        bf = QFont(); bf.setPointSize(24); bf.setBold(True)
        brand.setFont(bf)
        brand.setAlignment(Qt.AlignCenter)
        brand.setStyleSheet(f"color: {self.c['primary']}; border: none;")
        card_lay.addWidget(brand)

        desc = QLabel("Управление личными финансами")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet(f"color: {self.c['text_secondary']}; font-size: 14px; margin-bottom: 8px;")
        card_lay.addWidget(desc)

        # ─── Tabs ─────────────────────────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: transparent;
            }}
            QTabBar {{
                background: transparent;
            }}
            QTabBar::tab {{
                background: transparent;
                color: {self.c['text_secondary']};
                padding: 10px 0px;
                margin: 0 14px;
                font-weight: 600;
                font-size: 14px;
                border: none;
                border-bottom: 2px solid transparent;
                min-width: 100px;
            }}
            QTabBar::tab:selected {{
                color: {self.c['primary']};
                border-bottom: 2px solid {self.c['primary']};
            }}
            QTabBar::tab:hover {{
                color: {self.c['text_primary']};
            }}
        """)
        self.tabs.tabBar().setExpanding(True)

        self.tabs.addTab(self._build_register_tab(), "Регистрация")
        self.tabs.addTab(self._build_login_tab(), "Вход")
        self.tabs.setCurrentIndex(1)  # По умолчанию — вкладка «Вход»
        card_lay.addWidget(self.tabs)

        # Вотермарка
        card_lay.addSpacing(12)
        watermark = QLabel("Development by Flox1k")
        watermark.setAlignment(Qt.AlignCenter)
        watermark.setStyleSheet(f"color: {self.c['text_secondary']}; font-size: 11px; opacity: 0.7;")
        card_lay.addWidget(watermark)

        root_lay.addWidget(card)

    # ── Стиль input ───────────────────────────────────────────────────
    def _input_style(self) -> str:
        return f"""
            QLineEdit {{
                background-color: {self.c['bg_input']};
                color: {self.c['text_primary']};
                border: 1px solid {self.c['border']};
                border-radius: 8px;
                padding: 11px 14px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 2px solid {self.c['border_focus']};
            }}
        """

    def _label_style(self) -> str:
        return f"color: {self.c['text_primary']}; font-weight: 600; font-size: 13px;"

    def _btn_primary_style(self) -> str:
        return f"""
            QPushButton {{
                background-color: {self.c['primary']};
                color: {self.c['text_on_primary']};
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 700;
                padding: 12px;
            }}
            QPushButton:hover {{
                background-color: {self.c['primary_hover']};
            }}
        """

    def _error_style(self) -> str:
        return f"color: {self.c['danger']}; font-size: 13px; font-weight: 600;"

    # ─── Вкладка входа ────────────────────────────────────────────────
    def _build_login_tab(self) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet("border: none; background: transparent;")
        lay = QVBoxLayout(tab)
        lay.setSpacing(6)
        lay.setContentsMargins(0, 16, 0, 8)

        lbl_u = QLabel("Имя пользователя")
        lbl_u.setStyleSheet(self._label_style())
        lay.addWidget(lbl_u)
        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText("Введите имя пользователя")
        self.login_username.setMinimumHeight(42)
        self.login_username.setStyleSheet(self._input_style())
        self.login_username.returnPressed.connect(self._on_login)
        lay.addWidget(self.login_username)

        lay.addSpacing(4)

        lbl_p = QLabel("Пароль")
        lbl_p.setStyleSheet(self._label_style())
        lay.addWidget(lbl_p)
        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("Введите пароль")
        self.login_password.setMinimumHeight(42)
        self.login_password.setEchoMode(QLineEdit.Password)
        self.login_password.setStyleSheet(self._input_style())
        self.login_password.returnPressed.connect(self._on_login)
        lay.addWidget(self.login_password)

        # Inline-ошибка
        self.login_error = QLabel("")
        self.login_error.setStyleSheet(self._error_style())
        self.login_error.setWordWrap(True)
        self.login_error.setVisible(False)
        lay.addWidget(self.login_error)

        lay.addSpacing(8)

        btn = QPushButton("Войти")
        btn.setMinimumHeight(44)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(self._btn_primary_style())
        btn.clicked.connect(self._on_login)
        lay.addWidget(btn)

        lay.addStretch()
        return tab

    # ─── Вкладка регистрации ──────────────────────────────────────────
    def _build_register_tab(self) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet("border: none; background: transparent;")
        lay = QVBoxLayout(tab)
        lay.setSpacing(5)
        lay.setContentsMargins(0, 16, 0, 8)

        fields = [
            ("Имя пользователя", "3-50 символов, буквы, цифры, _ и -"),
            ("Email",            "example@mail.com"),
            ("Пароль",           "Минимум 6 символов"),
            ("Подтверждение",    "Повторите пароль"),
        ]
        self._reg_inputs = []
        for label_text, placeholder in fields:
            lbl = QLabel(label_text)
            lbl.setStyleSheet(self._label_style())
            lay.addWidget(lbl)
            inp = QLineEdit()
            inp.setPlaceholderText(placeholder)
            inp.setMinimumHeight(38)
            inp.setStyleSheet(self._input_style())
            if "пароль" in label_text.lower() or "подтверждение" in label_text.lower():
                inp.setEchoMode(QLineEdit.Password)
            lay.addWidget(inp)
            self._reg_inputs.append(inp)

        # Последнее поле (подтверждение пароля) — Enter запускает регистрацию
        self._reg_inputs[-1].returnPressed.connect(self._on_register)

        # Inline-ошибка
        self.register_error = QLabel("")
        self.register_error.setStyleSheet(self._error_style())
        self.register_error.setWordWrap(True)
        self.register_error.setVisible(False)
        lay.addWidget(self.register_error)

        lay.addSpacing(6)

        btn = QPushButton("Зарегистрироваться")
        btn.setMinimumHeight(44)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(self._btn_primary_style())
        btn.clicked.connect(self._on_register)
        lay.addWidget(btn)

        lay.addStretch()
        return tab

    # ─── Обработчики ──────────────────────────────────────────────────
    def _on_login(self):
        self.login_error.setVisible(False)
        username = self.login_username.text().strip()
        password = self.login_password.text()
        if not username or not password:
            self._show_error(self.login_error, "Заполните все поля")
            return
        success, message, user = AuthService.login(username, password)
        if success:
            self.login_username.clear()
            self.login_password.clear()
            self.login_success.emit(user)
        else:
            self._show_error(self.login_error, message)

    def _on_register(self):
        self.register_error.setVisible(False)
        vals = [inp.text().strip() if i < 2 else inp.text() for i, inp in enumerate(self._reg_inputs)]
        username, email, password, password_confirm = vals

        success, message, user = AuthService.register(username, email, password, password_confirm)
        if success:
            for inp in self._reg_inputs:
                inp.clear()
            show_toast(self, "Регистрация успешна! Войдите в аккаунт", 2000)
            self.tabs.setCurrentIndex(1)  # Переключить на вкладку «Вход»
        else:
            self._show_error(self.register_error, message)

    @staticmethod
    def _show_error(label: QLabel, text: str):
        label.setText(text)
        label.setVisible(True)
