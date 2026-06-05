# -*- coding: utf-8 -*-
"""
Диалог добавления / редактирования транзакции по долгу
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QTextEdit,
    QPushButton, QDateTimeEdit
)
from PyQt5.QtCore import QDateTime
from PyQt5.QtGui import QFont
from config import now_almaty, get_ui_mode, UI_MODE_NEW

from services.services import DebtTransactionService
from ui.toast_notification import show_toast
from ui.styles import (
    get_stylesheet, get_current_colors,
    get_primary_color, get_text_color, get_text_secondary_color
)
from ui.new_styles import get_new_stylesheet, apply_dark_title_bar
from config import get_current_theme as config_get_current_theme


class DebtTransactionDialog(QDialog):
    """Диалог для добавления / редактирования операции по долгу"""

    def __init__(self, debt, transaction=None, parent=None):
        super().__init__(parent)
        self.debt = debt
        self.transaction = transaction

        self.current_theme = config_get_current_theme()
        self.colors = get_current_colors()

        self.init_ui()

        if transaction:
            self.setWindowTitle("Редактировать операцию")
            self._load_data()
        else:
            self.setWindowTitle("Новая операция")

        self.setGeometry(200, 200, 500, 400)
        self.setModal(True)
        if get_ui_mode() == UI_MODE_NEW:
            self.setStyleSheet(get_new_stylesheet(self.current_theme))
        else:
            self.setStyleSheet(get_stylesheet(self.current_theme))

    def showEvent(self, event):
        super().showEvent(event)
        if get_ui_mode() == UI_MODE_NEW:
            apply_dark_title_bar(self)

    # ──────────────────────────────────────────────────────────────────────────

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        is_new = get_ui_mode() == UI_MODE_NEW
        primary_color = get_primary_color()
        text_color = get_text_color()
        secondary_color = get_text_secondary_color()

        if not is_new:
            if self.current_theme == "dark":
                label_color = text_color
                input_bg = self.colors["bg_main"]
                input_text = text_color
                input_placeholder = secondary_color
                input_border = self.colors["gray_lighter"]
                input_border_focus = primary_color
                btn_cancel_bg = self.colors["gray_light"]
                btn_cancel_text = text_color
                btn_cancel_hover = self.colors["gray_lighter"]
                btn_cancel_pressed = "#6b7280"
            else:
                label_color = "#1f2937"
                input_bg = "#f9fafb"
                input_text = "#1f2937"
                input_placeholder = "#6b7280"
                input_border = "#d1d5db"
                input_border_focus = "#2563eb"
                btn_cancel_bg = "#e5e7eb"
                btn_cancel_text = "#1f2937"
                btn_cancel_hover = "#d1d5db"
                btn_cancel_pressed = "#9ca3af"

        # Информация
        info_lbl = QLabel(f"Кейс: {self.debt.name} ({self.debt.currency})")
        info_font = QFont(); info_font.setPointSize(11); info_font.setBold(True)
        info_lbl.setFont(info_font)
        if not is_new:
            info_lbl.setStyleSheet(f"color: {primary_color};")
        layout.addWidget(info_lbl)

        # Тип
        type_label = QLabel("Тип операции:")
        if not is_new:
            type_label.setStyleSheet(f"font-weight: bold; color: {label_color}; font-size: 12px;")
        layout.addWidget(type_label)

        self.type_combo = QComboBox()
        self.type_combo.addItem("Дал в долг (мне должны)" if is_new else "📤 Дал в долг (мне должны)", "gave")
        self.type_combo.addItem("Взял в долг (я должен)" if is_new else "📥 Взял в долг (я должен)", "took")
        self.type_combo.setMinimumHeight(35)
        if not is_new:
            self.type_combo.setStyleSheet(f"""
                QComboBox {{
                    border: 1px solid {input_border}; border-radius: 6px;
                    padding: 8px; font-size: 13px;
                    background-color: {input_bg}; color: {input_text};
                }}
                QComboBox:focus {{ border: 2px solid {input_border_focus}; }}
            """)
        layout.addWidget(self.type_combo)

        # Сумма
        amount_label = QLabel("Сумма:")
        if not is_new:
            amount_label.setStyleSheet(f"font-weight: bold; color: {label_color}; font-size: 12px;")
        layout.addWidget(amount_label)

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Введите сумму")
        self.amount_input.setMinimumHeight(35)
        if not is_new:
            self.amount_input.setStyleSheet(f"""
                QLineEdit {{
                    border: 1px solid {input_border}; border-radius: 6px;
                    padding: 8px; font-size: 13px;
                    background-color: {input_bg}; color: {input_text};
                }}
                QLineEdit:focus {{ border: 2px solid {input_border_focus}; }}
            """)
        layout.addWidget(self.amount_input)

        # Комментарий
        comment_label = QLabel("Комментарий:")
        if not is_new:
            comment_label.setStyleSheet(f"font-weight: bold; color: {label_color}; font-size: 12px;")
        layout.addWidget(comment_label)

        self.comment_input = QTextEdit()
        self.comment_input.setPlaceholderText("Описание (опционально)")
        self.comment_input.setMaximumHeight(70)
        if not is_new:
            self.comment_input.setStyleSheet(f"""
                QTextEdit {{
                    border: 1px solid {input_border}; border-radius: 6px;
                    padding: 8px; font-size: 13px;
                    background-color: {input_bg}; color: {input_text};
                }}
                QTextEdit:focus {{ border: 2px solid {input_border_focus}; }}
            """)
        layout.addWidget(self.comment_input)

        # Дата
        dt_label = QLabel("Дата и время:")
        if not is_new:
            dt_label.setStyleSheet(f"font-weight: bold; color: {label_color}; font-size: 12px;")
        layout.addWidget(dt_label)

        self.datetime_input = QDateTimeEdit()
        _now = now_almaty()
        self.datetime_input.setDateTime(QDateTime(_now.year, _now.month, _now.day, _now.hour, _now.minute))
        self.datetime_input.setDisplayFormat("dd.MM.yyyy HH:mm")
        self.datetime_input.setMinimumHeight(35)
        if not is_new:
            self.datetime_input.setStyleSheet(f"""
                QDateTimeEdit {{
                    border: 1px solid {input_border}; border-radius: 6px;
                    padding: 8px; font-size: 13px;
                    background-color: {input_bg}; color: {input_text};
                }}
                QDateTimeEdit:focus {{ border: 2px solid {input_border_focus}; }}
            """)
        layout.addWidget(self.datetime_input)

        layout.addSpacing(10)

        # Кнопки
        btn_layout = QHBoxLayout()

        ok_btn = QPushButton("OK")
        ok_btn.setMinimumHeight(40); ok_btn.setMinimumWidth(100)
        if not is_new:
            ok_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {primary_color}; color: #ffffff;
                    border: none; border-radius: 6px; font-size: 13px; font-weight: bold;
                }}
                QPushButton:hover {{ opacity: 0.85; }}
            """)
        ok_btn.clicked.connect(self.on_ok)
        btn_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setMinimumHeight(40); cancel_btn.setMinimumWidth(100)
        if not is_new:
            cancel_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {btn_cancel_bg}; color: {btn_cancel_text};
                    border: none; border-radius: 6px; font-size: 13px; font-weight: bold;
                }}
                QPushButton:hover {{ background-color: {btn_cancel_hover}; }}
            """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    # ──────────────────────────────────────────────────────────────────────────

    def _load_data(self):
        if not self.transaction:
            return
        idx = self.type_combo.findData(self.transaction.type)
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)
        self.amount_input.setText(str(self.transaction.amount))
        self.comment_input.setText(self.transaction.description)
        self.datetime_input.setDateTime(self.transaction.created_at)

    def on_ok(self):
        dtype = self.type_combo.currentData()
        amount = self.amount_input.text().strip()
        comment = self.comment_input.toPlainText().strip()
        if not amount:
            show_toast(self, "Введите сумму", 2000)
            return
        if self.transaction:
            ok, msg = DebtTransactionService.update_transaction(
                self.transaction.id, dtype, amount, comment
            )
        else:
            ok, msg = DebtTransactionService.add_transaction(
                self.debt.id, dtype, amount, comment
            )
        if ok:
            show_toast(self, msg, 2000)
            self.accept()
        else:
            show_toast(self, msg, 3000)
