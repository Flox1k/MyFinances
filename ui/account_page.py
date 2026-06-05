# -*- coding: utf-8 -*-
"""
Страница аккаунта пользователя (New UI)

Функционал:
- Просмотр аватара, никнейма, email, активов
- Редактирование никнейма и аватарки (кнопка «Редактировать»)
- Смена почты (кнопка «Смена почты»)
- Смена пароля (кнопка «Смена пароля»)
- Экспорт / импорт данных аккаунта
"""

import json
import os

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QDialog, QDialogButtonBox, QFormLayout,
    QFileDialog, QMessageBox, QSizePolicy, QScrollArea, QFrame,
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QPixmap, QPainter, QBrush, QColor, QPainterPath, QFont, QCursor

from models.models import User
from services.services import AuthService, WalletService, AccountDataService
from config import (
    get_main_currency,
    get_user_avatar, set_user_avatar,
)
from ui.new_styles import get_new_colors, new_colors


# ─── helpers ────────────────────────────────────────────────────────────────

def _current_colors():
    return new_colors()


def _make_circle_pixmap(pixmap: QPixmap, size: int) -> QPixmap:
    """Обрезать QPixmap в круг заданного размера."""
    result = QPixmap(size, size)
    result.fill(Qt.transparent)
    painter = QPainter(result)
    painter.setRenderHint(QPainter.Antialiasing)
    path = QPainterPath()
    path.addEllipse(0, 0, size, size)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, size, size, pixmap)
    painter.end()
    return result


def _make_initials_pixmap(initials: str, size: int, bg: str, fg: str) -> QPixmap:
    """Нарисовать круглый аватар с инициалами."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QBrush(QColor(bg)))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(0, 0, size, size)
    painter.setPen(QColor(fg))
    font = QFont("Segoe UI", int(size * 0.3), QFont.Bold)
    painter.setFont(font)
    painter.drawText(0, 0, size, size, Qt.AlignCenter, initials)
    painter.end()
    return pixmap


# ─── Avatar widget ───────────────────────────────────────────────────────────

class AvatarWidget(QLabel):
    """Круглый виджет аватара, который можно сделать кликабельным."""

    clicked = pyqtSignal()

    def __init__(self, size: int = 80, parent=None):
        super().__init__(parent)
        self._size = size
        self._clickable = False
        self._hovered = False
        self.setFixedSize(size, size)
        self.setCursor(Qt.ArrowCursor)

    def set_clickable(self, flag: bool):
        self._clickable = flag
        self.setCursor(Qt.PointingHandCursor if flag else Qt.ArrowCursor)
        self.update()

    def enterEvent(self, event):
        if self._clickable:
            self._hovered = True
            self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self.update()

    def mousePressEvent(self, event):
        if self._clickable and event.button() == Qt.LeftButton:
            self.clicked.emit()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._clickable and self._hovered:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QBrush(QColor(0, 0, 0, 90)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(0, 0, self._size, self._size)
            # Camera icon hint
            painter.setPen(QColor(255, 255, 255, 200))
            font = QFont("Segoe UI", 10)
            painter.setFont(font)
            painter.drawText(0, 0, self._size, self._size, Qt.AlignCenter, "📷")
            painter.end()


# ─── Change-email dialog ─────────────────────────────────────────────────────

class ChangeEmailDialog(QDialog):
    def __init__(self, user: User, parent=None):
        super().__init__(parent)
        self.user = user
        self.setWindowTitle("Смена почты")
        self.setModal(True)
        self.setMinimumWidth(380)
        self._build_ui()

    def _build_ui(self):
        c = _current_colors()
        self.setStyleSheet(f"""
            QDialog {{ background: {c['bg_card']}; }}
            QLabel {{ color: {c['text_primary']}; font-size: 14px; background: transparent; border: none; }}
            QLineEdit {{
                background: {c['bg_input']}; color: {c['text_primary']};
                border: 1px solid {c['border']}; border-radius: 8px; padding: 8px 12px; font-size: 14px;
            }}
            QLineEdit:focus {{ border-color: {c['primary']}; }}
            QPushButton {{
                background: {c['primary']}; color: #fff; border: none;
                border-radius: 8px; padding: 9px 20px; font-size: 14px; font-weight: 600;
            }}
            QPushButton:hover {{ background: {c['primary_hover']}; }}
            QPushButton#btn_cancel {{
                background: {c['bg_hover']}; color: {c['text_primary']};
            }}
            QPushButton#btn_cancel:hover {{ background: {c['border']}; }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(14)

        title = QLabel("Смена адреса почты")
        title.setStyleSheet(f"font-size: 17px; font-weight: 700; color: {_current_colors()['text_primary']}; background: transparent; border: none;")
        lay.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("Новый email")
        form.addRow("Новый email:", self.email_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Текущий пароль")
        self.password_edit.setEchoMode(QLineEdit.Password)
        form.addRow("Пароль:", self.password_edit)

        lay.addLayout(form)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"color: {_current_colors()['danger']}; font-size: 12px; background: transparent; border: none;")
        self.error_label.setWordWrap(True)
        lay.addWidget(self.error_label)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Отмена")
        btn_cancel.setObjectName("btn_cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("Сохранить")
        btn_ok.clicked.connect(self._on_save)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        lay.addLayout(btn_row)

    def _on_save(self):
        email = self.email_edit.text().strip()
        pwd = self.password_edit.text()
        if not email or not pwd:
            self.error_label.setText("Заполните все поля")
            return
        ok, msg, _ = AuthService.update_email(self.user.id, email, pwd)
        if ok:
            self.accept()
        else:
            self.error_label.setText(msg)


# ─── Change-password dialog ──────────────────────────────────────────────────

class ChangePasswordDialog(QDialog):
    def __init__(self, user: User, parent=None):
        super().__init__(parent)
        self.user = user
        self.setWindowTitle("Смена пароля")
        self.setModal(True)
        self.setMinimumWidth(380)
        self._build_ui()

    def _build_ui(self):
        c = _current_colors()
        self.setStyleSheet(f"""
            QDialog {{ background: {c['bg_card']}; }}
            QLabel {{ color: {c['text_primary']}; font-size: 14px; background: transparent; border: none; }}
            QLineEdit {{
                background: {c['bg_input']}; color: {c['text_primary']};
                border: 1px solid {c['border']}; border-radius: 8px; padding: 8px 12px; font-size: 14px;
            }}
            QLineEdit:focus {{ border-color: {c['primary']}; }}
            QPushButton {{
                background: {c['primary']}; color: #fff; border: none;
                border-radius: 8px; padding: 9px 20px; font-size: 14px; font-weight: 600;
            }}
            QPushButton:hover {{ background: {c['primary_hover']}; }}
            QPushButton#btn_cancel {{
                background: {c['bg_hover']}; color: {c['text_primary']};
            }}
            QPushButton#btn_cancel:hover {{ background: {c['border']}; }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(14)

        title = QLabel("Смена пароля")
        title.setStyleSheet(f"font-size: 17px; font-weight: 700; color: {_current_colors()['text_primary']}; background: transparent; border: none;")
        lay.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        self.old_edit = QLineEdit()
        self.old_edit.setPlaceholderText("Текущий пароль")
        self.old_edit.setEchoMode(QLineEdit.Password)
        form.addRow("Текущий пароль:", self.old_edit)

        self.new_edit = QLineEdit()
        self.new_edit.setPlaceholderText("Новый пароль (мин. 6 симв.)")
        self.new_edit.setEchoMode(QLineEdit.Password)
        form.addRow("Новый пароль:", self.new_edit)

        self.confirm_edit = QLineEdit()
        self.confirm_edit.setPlaceholderText("Повторите новый пароль")
        self.confirm_edit.setEchoMode(QLineEdit.Password)
        form.addRow("Подтверждение:", self.confirm_edit)

        lay.addLayout(form)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"color: {_current_colors()['danger']}; font-size: 12px; background: transparent; border: none;")
        self.error_label.setWordWrap(True)
        lay.addWidget(self.error_label)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Отмена")
        btn_cancel.setObjectName("btn_cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("Сохранить")
        btn_ok.clicked.connect(self._on_save)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        lay.addLayout(btn_row)

    def _on_save(self):
        old = self.old_edit.text()
        new = self.new_edit.text()
        confirm = self.confirm_edit.text()
        if not old or not new or not confirm:
            self.error_label.setText("Заполните все поля")
            return
        ok, msg = AuthService.update_password(self.user.id, old, new, confirm)
        if ok:
            self.accept()
        else:
            self.error_label.setText(msg)


# ─── Account page ────────────────────────────────────────────────────────────

class AccountPage(QWidget):
    """
    Страница аккаунта.

    Сигналы:
        username_changed(str)  — после успешной смены никнейма
    """

    username_changed = pyqtSignal(str)

    def __init__(self, user: User, parent=None):
        super().__init__(parent)
        self.user = user
        self._edit_mode = False
        self._pending_avatar_path: str | None = None

        self._build_ui()
        self._load_avatar()
        self._refresh_balance()

    # ─── Build ────────────────────────────────────────────────────────

    def _build_ui(self):
        c = _current_colors()

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{ background: transparent; border: none; }}
            QScrollBar:vertical {{
                background: {c['bg_card']};
                width: 8px;
                border-radius: 4px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {c['border']};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {c['primary']};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
                background: none;
            }}
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        vlay = QVBoxLayout(container)
        vlay.setContentsMargins(40, 40, 40, 40)
        vlay.setSpacing(28)

        # ── Title ─────────────────────────────────────────────────────
        title = QLabel("Аккаунт")
        title.setStyleSheet(
            f"font-size: 24px; font-weight: 700; color: {c['text_primary']};"
            " background: transparent; border: none;"
        )
        vlay.addWidget(title)

        # ── Profile card ──────────────────────────────────────────────
        profile_card = QFrame()
        profile_card.setStyleSheet(
            f"QFrame {{ background: {c['bg_card']}; border-radius: 16px;"
            f" border: 1px solid {c['border']}; }}"
        )
        profile_lay = QVBoxLayout(profile_card)
        profile_lay.setContentsMargins(28, 28, 28, 28)
        profile_lay.setSpacing(20)

        # Avatar row
        avatar_row = QHBoxLayout()
        avatar_row.setSpacing(20)

        self.avatar_widget = AvatarWidget(size=80)
        avatar_row.addWidget(self.avatar_widget)
        self.avatar_widget.clicked.connect(self._on_avatar_clicked)

        # Name + email column
        name_col = QVBoxLayout()
        name_col.setSpacing(4)

        # Username (normal label OR line edit in edit mode)
        self.username_label = QLabel(self.user.username)
        self.username_label.setStyleSheet(
            f"font-size: 20px; font-weight: 700; color: {c['text_primary']};"
            " background: transparent; border: none;"
        )
        self.username_edit = QLineEdit(self.user.username)
        self.username_edit.setStyleSheet(
            f"font-size: 18px; font-weight: 700; color: {c['text_primary']};"
            f" background: {c['bg_input']}; border: 1px solid {c['border']};"
            " border-radius: 8px; padding: 5px 10px;"
        )
        self.username_edit.hide()
        name_col.addWidget(self.username_label)
        name_col.addWidget(self.username_edit)

        self.email_label = QLabel(self.user.email)
        self.email_label.setStyleSheet(
            f"font-size: 13px; color: {c['text_secondary']};"
            " background: transparent; border: none;"
        )
        name_col.addWidget(self.email_label)
        name_col.addStretch()
        avatar_row.addLayout(name_col)
        avatar_row.addStretch()
        profile_lay.addLayout(avatar_row)

        # Edit-mode save/cancel row (hidden by default)
        self.edit_action_row = QWidget()
        ear_lay = QHBoxLayout(self.edit_action_row)
        ear_lay.setContentsMargins(0, 0, 0, 0)
        ear_lay.setSpacing(10)
        self.btn_save_edit = QPushButton("Сохранить")
        self.btn_save_edit.setObjectName("btn_primary")
        self.btn_save_edit.clicked.connect(self._on_save_edit)
        self.btn_cancel_edit = QPushButton("Отмена")
        self.btn_cancel_edit.setObjectName("btn_cancel_edit")
        self.btn_cancel_edit.clicked.connect(self._on_cancel_edit)
        ear_lay.addWidget(self.btn_save_edit)
        ear_lay.addWidget(self.btn_cancel_edit)
        ear_lay.addStretch()
        self.edit_action_row.hide()
        self.edit_action_row.setStyleSheet(f"""
            QPushButton#btn_primary {{
                background: {c['primary']}; color: #fff;
                border: none; border-radius: 8px; padding: 9px 22px;
                font-size: 14px; font-weight: 600;
            }}
            QPushButton#btn_primary:hover {{ background: {c['primary_hover']}; }}
            QPushButton#btn_cancel_edit {{
                background: {c['bg_hover']}; color: {c['text_primary']};
                border: none; border-radius: 8px; padding: 9px 22px;
                font-size: 14px; font-weight: 600;
            }}
            QPushButton#btn_cancel_edit:hover {{ background: {c['border']}; }}
        """)
        profile_lay.addWidget(self.edit_action_row)

        vlay.addWidget(profile_card)

        # ── Assets card ───────────────────────────────────────────────
        assets_card = QFrame()
        assets_card.setStyleSheet(
            f"QFrame {{ background: {c['balance_bg']}; border-radius: 16px; border: none; }}"
        )
        assets_lay = QVBoxLayout(assets_card)
        assets_lay.setContentsMargins(28, 20, 28, 20)
        assets_lay.setSpacing(4)

        assets_title = QLabel("Активы")
        assets_title.setStyleSheet(
            "font-size: 13px; color: rgba(255,255,255,0.75); background: transparent; border: none;"
        )
        assets_lay.addWidget(assets_title)

        self.assets_label = QLabel("0 KZT")
        self.assets_label.setStyleSheet(
            "font-size: 26px; font-weight: 700; color: #fff; background: transparent; border: none;"
        )
        assets_lay.addWidget(self.assets_label)

        vlay.addWidget(assets_card)

        # ── Action buttons ────────────────────────────────────────────
        actions_label = QLabel("Управление аккаунтом")
        actions_label.setStyleSheet(
            f"font-size: 15px; font-weight: 600; color: {c['text_primary']};"
            " background: transparent; border: none;"
        )
        vlay.addWidget(actions_label)

        btn_grid = QVBoxLayout()
        btn_grid.setSpacing(10)

        self.btn_edit = self._action_btn("Редактировать профиль", "edit")
        self.btn_edit.clicked.connect(self._on_enter_edit)
        btn_grid.addWidget(self.btn_edit)

        self.btn_change_email = self._action_btn("Смена почты", "email")
        self.btn_change_email.clicked.connect(self._on_change_email)
        btn_grid.addWidget(self.btn_change_email)

        self.btn_change_password = self._action_btn("Смена пароля", "password")
        self.btn_change_password.clicked.connect(self._on_change_password)
        btn_grid.addWidget(self.btn_change_password)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {c['border']}; background: {c['border']};")
        sep.setFixedHeight(1)
        btn_grid.addWidget(sep)

        self.btn_export = self._action_btn("Экспорт данных", "export")
        self.btn_export.clicked.connect(self._on_export)
        btn_grid.addWidget(self.btn_export)

        self.btn_import = self._action_btn("Импорт данных", "import")
        self.btn_import.clicked.connect(self._on_import)
        btn_grid.addWidget(self.btn_import)

        vlay.addLayout(btn_grid)
        vlay.addStretch()

        scroll.setWidget(container)

        root_lay = QVBoxLayout(self)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.addWidget(scroll)

    def _action_btn(self, text: str, key: str) -> QPushButton:
        c = _current_colors()
        btn = QPushButton(f"  {text}")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setMinimumHeight(48)
        btn.setStyleSheet(
            f"QPushButton {{ background: {c['bg_card']}; color: {c['text_primary']};"
            f" border: 1px solid {c['border']}; border-radius: 10px;"
            f" padding: 10px 18px; text-align: left; font-size: 14px; font-weight: 500; }}"
            f"QPushButton:hover {{ background: {c['bg_hover']}; border-color: {c['primary']}; }}"
        )
        return btn

    # ─── Avatar ───────────────────────────────────────────────────────

    def _load_avatar(self, path: str | None = None):
        c = _current_colors()
        resolved = path if path is not None else get_user_avatar(self.user.id)
        if resolved and os.path.isfile(resolved):
            px = QPixmap(resolved)
            if not px.isNull():
                self.avatar_widget.setPixmap(_make_circle_pixmap(px, 80))
                return
        # Fallback to initials
        initials = self.user.username[:2].upper()
        px = _make_initials_pixmap(initials, 80, c["primary"], "#ffffff")
        self.avatar_widget.setPixmap(px)

    def _on_avatar_clicked(self):
        if not self._edit_mode:
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Выбрать аватарку", "",
            "Изображения (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if path:
            self._pending_avatar_path = path
            self._load_avatar(path)

    # ─── Balance ──────────────────────────────────────────────────────

    def _refresh_balance(self):
        try:
            currency = get_main_currency()
            data = WalletService.get_balance_multi_currency(self.user.id, currency)
            total = data.get("total", 0.0)
            self.assets_label.setText(f"{total:,.2f} {currency}")
        except Exception:
            self.assets_label.setText("— —")

    # ─── Edit mode ────────────────────────────────────────────────────

    def _on_enter_edit(self):
        self._edit_mode = True
        self._pending_avatar_path = None
        self.username_label.hide()
        self.username_edit.setText(self.user.username)
        self.username_edit.show()
        self.username_edit.setFocus()
        self.avatar_widget.set_clickable(True)
        self.edit_action_row.show()
        self.btn_edit.hide()

    def _on_cancel_edit(self):
        self._edit_mode = False
        self._pending_avatar_path = None
        self.username_edit.hide()
        self.username_label.show()
        self.avatar_widget.set_clickable(False)
        self.edit_action_row.hide()
        self.btn_edit.show()
        self._load_avatar()  # restore saved avatar

    def _on_save_edit(self):
        new_name = self.username_edit.text().strip()
        changed_name = False

        if new_name and new_name != self.user.username:
            ok, msg, updated = AuthService.update_username(self.user.id, new_name)
            if not ok:
                QMessageBox.warning(self, "Ошибка", msg)
                return
            self.user.username = updated.username
            self.username_label.setText(self.user.username)
            changed_name = True

        if self._pending_avatar_path:
            set_user_avatar(self.user.id, self._pending_avatar_path)

        self._edit_mode = False
        self._pending_avatar_path = None
        self.username_edit.hide()
        self.username_label.show()
        self.avatar_widget.set_clickable(False)
        self.edit_action_row.hide()
        self.btn_edit.show()
        self._load_avatar()

        if changed_name:
            self.username_changed.emit(self.user.username)

    # ─── Change email ─────────────────────────────────────────────────

    def _on_change_email(self):
        dlg = ChangeEmailDialog(self.user, self)
        if dlg.exec_() == QDialog.Accepted:
            # Reload fresh user data
            from db.database import get_session
            from db.repositories import UserRepository
            session = get_session()
            try:
                updated = UserRepository(session).get_user_by_id(self.user.id)
                if updated:
                    self.user.email = updated.email
                    self.email_label.setText(self.user.email)
            finally:
                session.close()
            QMessageBox.information(self, "Успешно", "Email успешно изменён.")

    # ─── Change password ──────────────────────────────────────────────

    def _on_change_password(self):
        dlg = ChangePasswordDialog(self.user, self)
        if dlg.exec_() == QDialog.Accepted:
            QMessageBox.information(self, "Успешно", "Пароль успешно изменён.")

    # ─── Export ───────────────────────────────────────────────────────

    def _on_export(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Экспорт данных аккаунта",
            f"myfinances_{self.user.username}.json",
            "JSON файл (*.json)"
        )
        if not path:
            return
        data = AccountDataService.export_data(self.user.id)
        if not data:
            QMessageBox.warning(self, "Ошибка", "Не удалось получить данные аккаунта.")
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "Экспорт", f"Данные сохранены:\n{path}")
        except OSError as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось записать файл:\n{e}")

    # ─── Import ───────────────────────────────────────────────────────

    def _on_import(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Импорт данных аккаунта", "",
            "JSON файл (*.json)"
        )
        if not path:
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение импорта",
            "Все текущие данные (кошельки, транзакции, цели, долги, курсы) "
            "будут заменены данными из файла.\n\nПродолжить?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось прочитать файл:\n{e}")
            return

        ok, msg = AccountDataService.import_data(self.user.id, data)
        if ok:
            # Update displayed username in case it changed
            imp_user = data.get("user", {})
            new_uname = imp_user.get("username", "").strip()
            if new_uname and new_uname != self.user.username:
                self.user.username = new_uname
                self.username_label.setText(new_uname)
                self.username_changed.emit(new_uname)
            self._refresh_balance()
            QMessageBox.information(self, "Импорт", msg)
        else:
            QMessageBox.critical(self, "Ошибка импорта", msg)

    # ─── Public ───────────────────────────────────────────────────────

    def refresh(self):
        """Обновить баланс и email (вызывается при переключении на страницу)."""
        # Reload fresh user data from DB
        try:
            from db.database import get_session
            from db.repositories import UserRepository
            session = get_session()
            try:
                updated = UserRepository(session).get_user_by_id(self.user.id)
                if updated:
                    self.user.email = updated.email
                    self.user.username = updated.username
            finally:
                session.close()
        except Exception:
            pass
        self._refresh_balance()
        self.username_label.setText(self.user.username)
        self.email_label.setText(self.user.email)
        self._load_avatar()
