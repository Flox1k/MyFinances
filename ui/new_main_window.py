# -*- coding: utf-8 -*-
"""
Новое главное окно приложения (New UI)

Чистый sidebar без эмодзи, индиго-акцент, аватар пользователя.
Переиспользует существующие страницы (Goals, Debts, ExchangeRates, Admin)
через новый стиль, а Dashboard — собственный NewDashboardPage.
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QMessageBox, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap, QPainter, QBrush, QColor, QPainterPath

from models.models import User
from ui.new_styles import get_new_stylesheet, set_new_current_theme, get_new_colors, apply_dark_title_bar, msgbox_question
from ui.account_page import AccountPage, _make_circle_pixmap, _make_initials_pixmap
from ui.settings_page import SettingsPage
from ui.new_dashboard_page import NewDashboardPage
from ui.wallet_details_page import WalletDetailsPage
from ui.exchange_rates_page import ExchangeRatesPage
from ui.goals_page import GoalsPage
from ui.debts_page import DebtsPage
from ui.debt_details_page import DebtDetailsPage
from ui.admin_panel_page import AdminPanelPage
from ui.ai_chat_page import AIChatPage
from config import get_current_theme, get_ui_mode, UI_MODE_NEW


class NewMainWindow(QMainWindow):
    """
    Главное окно (New UI).

    Сигналы:
        logout — пользователь вышел из аккаунта
    """

    logout = pyqtSignal()

    def __init__(self, user: User):
        super().__init__()
        self.current_user = user
        self.current_page = None
        self.current_theme = get_current_theme()

        self.setWindowTitle(f"MyFinances — {user.username}")
        self.setGeometry(50, 50, 1400, 800)

        self._apply_theme(self.current_theme)
        self._build_ui()
        self.set_page("dashboard")
        apply_dark_title_bar(self)

    # ─── Theme ────────────────────────────────────────────────────────
    def _apply_theme(self, theme: str):
        self.current_theme = theme
        set_new_current_theme(theme)
        self.setStyleSheet(get_new_stylesheet(theme))

    # ─── UI ───────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        main = QHBoxLayout(root)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        main.addWidget(self._build_sidebar())
        main.addWidget(self._build_content(), 1)

    # ─── Sidebar ──────────────────────────────────────────────────────
    def _build_sidebar(self) -> QWidget:
        c = get_new_colors(self.current_theme)

        sidebar = QWidget()
        sidebar.setObjectName("new_sidebar")
        sidebar.setFixedWidth(230)

        lay = QVBoxLayout(sidebar)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # ── Header: аватар + имя ──────────────────────────────────────
        header = QWidget()
        header.setStyleSheet(f"background: transparent; border-bottom: 1px solid {c['bg_sidebar_hover']};")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(18, 22, 18, 18)
        hl.setSpacing(12)

        # Аватар (инициалы) — кликабельный
        initials = self.current_user.username[:2].upper()
        self._sidebar_avatar = QLabel(initials)
        self._sidebar_avatar.setObjectName("new_avatar")
        self._sidebar_avatar.setFixedSize(40, 40)
        self._sidebar_avatar.setAlignment(Qt.AlignCenter)
        self._sidebar_avatar.setCursor(Qt.PointingHandCursor)
        self._update_sidebar_avatar()
        hl.addWidget(self._sidebar_avatar)

        # Имя + роль — кликабельный
        info = QWidget()
        info.setStyleSheet("background: transparent; border: none;")
        il = QVBoxLayout(info)
        il.setContentsMargins(0, 0, 0, 0)
        il.setSpacing(0)
        self._sidebar_uname = QLabel(self.current_user.username)
        self._sidebar_uname.setStyleSheet(f"color: {c['text_sidebar_active']}; font-size: 15px; font-weight: 700; border: none;")
        self._sidebar_uname.setCursor(Qt.PointingHandCursor)
        il.addWidget(self._sidebar_uname)
        role = QLabel("Администратор" if self.current_user.username == "Flox1kAdmin" else "Пользователь")
        role.setStyleSheet(f"color: {c['text_sidebar']}; font-size: 12px; border: none;")
        il.addWidget(role)
        hl.addWidget(info, 1)

        # Сделать весь header кликабельным
        header.mousePressEvent = lambda e: self.set_page("account")
        self._sidebar_avatar.mousePressEvent = lambda e: self.set_page("account")
        self._sidebar_uname.mousePressEvent = lambda e: self.set_page("account")

        lay.addWidget(header)

        # ── Navigation ────────────────────────────────────────────────
        nav = QVBoxLayout()
        nav.setSpacing(2)
        nav.setContentsMargins(0, 14, 0, 14)

        self.menu_buttons = {}
        items = [
            ("dashboard",      "Мои кошельки"),
            ("exchange_rates", "Курсы валют"),
            ("goals",          "Цели"),
            ("debts",          "Долги"),
            ("ai_chat",        "Чат с ИИ"),
        ]
        if self.current_user.username == "Flox1kAdmin":
            items.append(("admin", "Администрация"))

        for key, text in items:
            btn = QPushButton(text)
            btn.setObjectName("new_nav_btn")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key: self.set_page(k))
            self.menu_buttons[key] = btn
            nav.addWidget(btn)

        lay.addLayout(nav)
        lay.addStretch()

        # ── Bottom buttons ────────────────────────────────────────────
        bot = QVBoxLayout()
        bot.setSpacing(2)
        bot.setContentsMargins(0, 0, 0, 18)

        self._btn_settings = QPushButton("Настройки")
        self._btn_settings.setObjectName("new_nav_btn")
        self._btn_settings.setCursor(Qt.PointingHandCursor)
        self._btn_settings.clicked.connect(lambda: self.set_page("settings"))
        bot.addWidget(self._btn_settings)

        btn_logout = QPushButton("Выход")
        btn_logout.setObjectName("new_nav_btn")
        btn_logout.setCursor(Qt.PointingHandCursor)
        btn_logout.clicked.connect(self._on_logout)
        bot.addWidget(btn_logout)

        lay.addLayout(bot)
        return sidebar

    # ─── Content area ─────────────────────────────────────────────────
    def _build_content(self) -> QWidget:
        container = QWidget()
        cl = QVBoxLayout(container)
        cl.setContentsMargins(28, 24, 28, 24)
        cl.setSpacing(0)

        self.stacked = QStackedWidget()

        # Dashboard (New)
        self.dashboard_page = NewDashboardPage(self.current_user)
        self.dashboard_page.wallet_selected.connect(self._on_wallet_selected)
        self.stacked.addWidget(self.dashboard_page)

        # Wallet details (reuse)
        self.wallet_details_page = WalletDetailsPage()
        self.wallet_details_page.back_requested.connect(lambda: self.set_page("dashboard"))
        self.stacked.addWidget(self.wallet_details_page)

        # Exchange rates (reuse)
        self.exchange_rates_page = ExchangeRatesPage(self.current_user)
        self.stacked.addWidget(self.exchange_rates_page)

        # Goals (reuse)
        self.goals_page = GoalsPage(self.current_user)
        self.stacked.addWidget(self.goals_page)

        # Debts (reuse)
        self.debts_page = DebtsPage(self.current_user)
        self.debts_page.debt_selected.connect(self._on_debt_selected)
        self.stacked.addWidget(self.debts_page)

        # Debt details (reuse)
        self.debt_details_page = DebtDetailsPage()
        self.debt_details_page.back_requested.connect(lambda: self.set_page("debts"))
        self.stacked.addWidget(self.debt_details_page)

        # Admin (reuse)
        if self.current_user.username == "Flox1kAdmin":
            self.admin_panel_page = AdminPanelPage()
            self.stacked.addWidget(self.admin_panel_page)

        # AI Chat
        self.ai_chat_page = AIChatPage(self.current_user)
        self.stacked.addWidget(self.ai_chat_page)

        # Account page
        self.account_page = AccountPage(self.current_user)
        self.account_page.username_changed.connect(self._on_username_changed)
        self.stacked.addWidget(self.account_page)

        # Settings page
        self.settings_page = SettingsPage(self.current_user)
        self.settings_page.currency_changed.connect(self._on_currency_changed)
        self.settings_page.restart_requested.connect(self._recreate_window)
        self.stacked.addWidget(self.settings_page)

        cl.addWidget(self.stacked)
        return container

    # ─── Navigation ───────────────────────────────────────────────────
    def set_page(self, name: str):
        self.current_page = name

        for key, btn in self.menu_buttons.items():
            active = (key == name)
            btn.setObjectName("new_nav_btn_active" if active else "new_nav_btn")
            btn.setStyle(btn.style())

        page_map = {
            "dashboard":      (self.dashboard_page,      True),
            "wallet":         (self.wallet_details_page, False),
            "exchange_rates": (self.exchange_rates_page, False),
            "goals":          (self.goals_page,          True),
            "debts":          (self.debts_page,          True),
            "debt_details":   (self.debt_details_page,   False),
            "admin":          (getattr(self, "admin_panel_page", None), True),
            "account":        (self.account_page,        True),
            "settings":       (self.settings_page,       True),
            "ai_chat":        (self.ai_chat_page,        True),
        }
        target, needs_refresh = page_map.get(name, (None, False))
        if target is None:
            return
        self.stacked.setCurrentWidget(target)
        if needs_refresh and hasattr(target, "refresh"):
            target.refresh()
        # Refresh sidebar avatar when navigating
        self._update_sidebar_avatar()
        # Highlight settings button when on settings page
        if hasattr(self, "_btn_settings"):
            self._btn_settings.setObjectName(
                "new_nav_btn_active" if name == "settings" else "new_nav_btn"
            )
            self._btn_settings.setStyle(self._btn_settings.style())

    # ─── Slots ────────────────────────────────────────────────────────
    def _on_wallet_selected(self, wallet):
        self.wallet_details_page.set_wallet(wallet)
        self.set_page("wallet")

    def _on_debt_selected(self, debt):
        self.debt_details_page.set_debt(debt)
        self.set_page("debt_details")

    def _on_logout(self):
        from PyQt5.QtWidgets import QMessageBox
        reply = msgbox_question(
            self, "Выход", "Вы уверены, что хотите выйти?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.logout.emit()

    def _update_sidebar_avatar(self):
        """Загрузить аватар пользователя в боковую панель (инициалы или изображение)."""
        from config import get_user_avatar
        import os
        if not hasattr(self, "_sidebar_avatar"):
            return
        c = get_new_colors(self.current_theme)
        path = get_user_avatar(self.current_user.id)
        if path and os.path.isfile(path):
            px = QPixmap(path)
            if not px.isNull():
                circle = _make_circle_pixmap(px, 40)
                self._sidebar_avatar.setPixmap(circle)
                self._sidebar_avatar.setText("")
                return
        # Fallback: initials
        self._sidebar_avatar.setPixmap(QPixmap())
        self._sidebar_avatar.setText(self.current_user.username[:2].upper())

    def _on_username_changed(self, new_username: str):
        """Обновить никнейм в сайдбаре после редактирования на странице аккаунта."""
        self.current_user.username = new_username
        if hasattr(self, "_sidebar_uname"):
            self._sidebar_uname.setText(new_username)
            if hasattr(self, "_sidebar_avatar"):
                self._sidebar_avatar.setText(new_username[:2].upper())
        self._update_sidebar_avatar()

    def _on_currency_changed(self, currency: str):
        if self.current_page == "dashboard":
            self.dashboard_page.refresh()

    def _recreate_window(self):
        """Пересоздать окно с учётом текущей темы."""
        self.close()
        win = NewMainWindow(self.current_user)
        win.logout.connect(self.logout.emit)
        win.show()
