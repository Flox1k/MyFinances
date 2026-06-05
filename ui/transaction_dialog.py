# -*- coding: utf-8 -*-
"""
Диалоговое окно для добавления и редактирования транзакций

Классы:
- TransactionDialog: диалог для работы с транзакциями
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QTextEdit,
    QPushButton, QMessageBox, QDateTimeEdit
)
from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtGui import QFont
from config import now_almaty, get_ui_mode, UI_MODE_NEW
from services.services import TransactionService, CategoryService
from models.models import Wallet
from ui.toast_notification import show_toast
from ui.styles import (
    get_stylesheet, get_current_colors,
    get_primary_color, get_text_color, get_text_secondary_color
)
from ui.new_styles import get_new_stylesheet, apply_dark_title_bar
from config import get_current_theme as config_get_current_theme, get_ui_mode, UI_MODE_NEW


class TransactionDialog(QDialog):
    """
    Диалоговое окно для добавления и редактирования транзакций
    
    Позволяет выбрать:
    - Тип транзакции (Доход / Расход)
    - Сумму
    - Комментарий
    - Дату и время
    """
    
    def __init__(self, wallet: Wallet, transaction=None, parent=None):
        super().__init__(parent)
        self.wallet = wallet
        self.transaction = transaction  # None для новой, Transaction для редактирования
        self.user_id = wallet.user_id
        
        # Получить текущую тему
        self.current_theme = config_get_current_theme()
        self.colors = get_current_colors()
        
        self.init_ui()
        
        if transaction:
            self.setWindowTitle("Редактировать транзакцию")
            self.load_transaction_data()
        else:
            self.setWindowTitle("Новая транзакция")
        
        self.setGeometry(200, 200, 500, 600)
        self.setModal(True)
        if get_ui_mode() == UI_MODE_NEW:
            self.setStyleSheet(get_new_stylesheet(self.current_theme))
        else:
            self.setStyleSheet(get_stylesheet(self.current_theme))

    def showEvent(self, event):
        super().showEvent(event)
        if get_ui_mode() == UI_MODE_NEW:
            apply_dark_title_bar(self)

    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        is_new = get_ui_mode() == UI_MODE_NEW
        primary_color = get_primary_color()
        text_color = get_text_color()
        secondary_color = get_text_secondary_color()

        # Определяем цвета только для старого UI
        if not is_new:
            if self.current_theme == "dark":
                label_color = text_color
                input_bg = self.colors["bg_main"]
                input_text = text_color
                input_placeholder = secondary_color
                input_border = self.colors["gray_lighter"]
                input_border_focus = primary_color
                button_cancel_bg = self.colors["gray_light"]
                button_cancel_text = text_color
                button_cancel_hover = self.colors["gray_lighter"]
                button_cancel_pressed = "#6b7280"
            else:
                label_color = "#1f2937"
                input_bg = "#f9fafb"
                input_text = "#1f2937"
                input_placeholder = "#6b7280"
                input_border = "#d1d5db"
                input_border_focus = "#2563eb"
                button_cancel_bg = "#e5e7eb"
                button_cancel_text = "#1f2937"
                button_cancel_hover = "#d1d5db"
                button_cancel_pressed = "#9ca3af"

        # === Информация о кошельке ===
        wallet_label = QLabel(f"Кошелёк: {self.wallet.name} ({self.wallet.currency})")
        wallet_font = QFont()
        wallet_font.setPointSize(11)
        wallet_font.setBold(True)
        wallet_label.setFont(wallet_font)
        if not is_new:
            wallet_label.setStyleSheet(f"color: {primary_color};")
        layout.addWidget(wallet_label)

        # === Тип транзакции ===
        type_label = QLabel("Тип транзакции:")
        if not is_new:
            type_label.setStyleSheet(f"font-weight: bold; color: {label_color}; font-size: 12px;")
        layout.addWidget(type_label)

        self.type_combo = QComboBox()
        self.type_combo.addItem("Доход" if is_new else "💰 Доход", "income")
        self.type_combo.addItem("Расход" if is_new else "📉 Расход", "expense")
        self.type_combo.setMinimumHeight(35)
        if not is_new:
            self.type_combo.setStyleSheet(f"""
                QComboBox {{
                    border: 1px solid {input_border};
                    border-radius: 6px;
                    padding: 8px;
                    font-size: 13px;
                    background-color: {input_bg};
                    color: {input_text};
                }}
                QComboBox:focus {{
                    border: 2px solid {input_border_focus};
                    background-color: {input_bg};
                }}
            """)
        layout.addWidget(self.type_combo)

        # === Сумма ===
        amount_label = QLabel("Сумма:")
        if not is_new:
            amount_label.setStyleSheet(f"font-weight: bold; color: {label_color}; font-size: 12px;")
        layout.addWidget(amount_label)

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Введите сумму (например, 100.50)")
        self.amount_input.setMinimumHeight(35)
        if not is_new:
            self.amount_input.setStyleSheet(f"""
                QLineEdit {{
                    border: 1px solid {input_border};
                    border-radius: 6px;
                    padding: 8px;
                    font-size: 13px;
                    background-color: {input_bg};
                    color: {input_text};
                }}
                QLineEdit:focus {{
                    border: 2px solid {input_border_focus};
                    background-color: {input_bg};
                }}
                QLineEdit::placeholder {{
                    color: {input_placeholder};
                }}
            """)
        layout.addWidget(self.amount_input)

        # === Комментарий ===
        comment_label = QLabel("Комментарий:")
        if not is_new:
            comment_label.setStyleSheet(f"font-weight: bold; color: {label_color}; font-size: 12px;")
        layout.addWidget(comment_label)

        self.comment_input = QTextEdit()
        self.comment_input.setPlaceholderText("Опишите операцию (опционально)")
        self.comment_input.setMaximumHeight(70)
        if not is_new:
            self.comment_input.setStyleSheet(f"""
                QTextEdit {{
                    border: 1px solid {input_border};
                    border-radius: 6px;
                    padding: 8px;
                    font-size: 13px;
                    background-color: {input_bg};
                    color: {input_text};
                }}
                QTextEdit:focus {{
                    border: 2px solid {input_border_focus};
                    background-color: {input_bg};
                }}
                QTextEdit::placeholder {{
                    color: {input_placeholder};
                }}
            """)
        layout.addWidget(self.comment_input)

        # === Категория ===
        cat_label = QLabel("Категория:")
        if not is_new:
            cat_label.setStyleSheet(f"font-weight: bold; color: {label_color}; font-size: 12px;")
        layout.addWidget(cat_label)

        cat_row = QHBoxLayout()
        self.category_combo = QComboBox()
        self.category_combo.setMinimumHeight(35)
        self.category_combo.addItem("Без категории", None)
        for cat in CategoryService.get_user_categories(self.user_id):
            self.category_combo.addItem(cat.name, cat.id)
        cat_row.addWidget(self.category_combo, 1)

        self.classify_btn = QPushButton("Определить")
        self.classify_btn.setMinimumHeight(35)
        self.classify_btn.setToolTip("Авто-определить категорию по комментарию")
        self.classify_btn.clicked.connect(self.on_auto_classify)
        cat_row.addWidget(self.classify_btn)
        layout.addLayout(cat_row)

        # === Дата и время ===
        datetime_label = QLabel("Дата и время:")
        if not is_new:
            datetime_label.setStyleSheet(f"font-weight: bold; color: {label_color}; font-size: 12px;")
        layout.addWidget(datetime_label)

        self.datetime_input = QDateTimeEdit()
        _now = now_almaty()
        self.datetime_input.setDateTime(QDateTime(_now.year, _now.month, _now.day, _now.hour, _now.minute))
        self.datetime_input.setDisplayFormat("dd.MM.yyyy HH:mm")
        self.datetime_input.setMinimumHeight(35)
        if not is_new:
            self.datetime_input.setStyleSheet(f"""
                QDateTimeEdit {{
                    border: 1px solid {input_border};
                    border-radius: 6px;
                    padding: 8px;
                    font-size: 13px;
                    background-color: {input_bg};
                    color: {input_text};
                }}
                QDateTimeEdit:focus {{
                    border: 2px solid {input_border_focus};
                    background-color: {input_bg};
                }}
            """)
        layout.addWidget(self.datetime_input)

        layout.addSpacing(10)

        # === Кнопки ===
        button_layout = QHBoxLayout()

        ok_btn = QPushButton("OK")
        ok_btn.setMinimumHeight(40)
        ok_btn.setMinimumWidth(100)
        if not is_new:
            ok_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {primary_color};
                    color: #ffffff;
                    border: none;
                    border-radius: 6px;
                    font-size: 13px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {primary_color};
                    opacity: 0.85;
                }}
                QPushButton:pressed {{
                    background-color: {primary_color};
                    opacity: 0.7;
                }}
            """)
        ok_btn.clicked.connect(self.on_ok)
        button_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.setMinimumWidth(100)
        if not is_new:
            cancel_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {button_cancel_bg};
                    color: {button_cancel_text};
                    border: none;
                    border-radius: 6px;
                    font-size: 13px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {button_cancel_hover};
                }}
                QPushButton:pressed {{
                    background-color: {button_cancel_pressed};
                }}
            """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    def load_transaction_data(self):
        """Загрузить данные транзакции в форму при редактировании"""
        if not self.transaction:
            return
        
        # Установить тип
        index = self.type_combo.findData(self.transaction.type)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)
        
        # Установить сумму
        self.amount_input.setText(str(self.transaction.amount))
        
        # Установить комментарий
        self.comment_input.setText(self.transaction.description)

        # Установить категорию
        if self.transaction.category_id is not None:
            idx = self.category_combo.findData(self.transaction.category_id)
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)
        
        # Установить дату и время
        self.datetime_input.setDateTime(self.transaction.created_at)
    
    def on_auto_classify(self):
        """Авто-классификация по тексту комментария"""
        text = self.comment_input.toPlainText().strip()
        if not text:
            show_toast(self, "Введите комментарий для определения категории", 2000)
            return
        cat = CategoryService.auto_classify(self.user_id, text)
        if cat:
            idx = self.category_combo.findData(cat.id)
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)
            show_toast(self, f"Категория: {cat.name}", 2000)
        else:
            show_toast(self, "Категория не определена", 2000)

    def on_ok(self):
        """Обработчик кнопки OK"""
        # Получить данные
        transaction_type = self.type_combo.currentData()
        amount = self.amount_input.text().strip()
        comment = self.comment_input.toPlainText().strip()
        category_id = self.category_combo.currentData()
        
        # Валидация
        if not amount:
            show_toast(self, "Введите сумму", 2000)
            return
        
        if self.transaction:
            # Редактирование существующей транзакции
            success, message = TransactionService.update_transaction(
                self.transaction.id,
                transaction_type,
                amount,
                comment,
                category_id
            )
        else:
            # Добавление новой транзакции
            success, message = TransactionService.add_transaction(
                self.wallet.id,
                transaction_type,
                amount,
                comment,
                category_id
            )
        
        if success:
            show_toast(self, message, 2000)
            self.accept()  # Закрыть диалог с кодом успеха
        else:
            show_toast(self, message, 3000)
