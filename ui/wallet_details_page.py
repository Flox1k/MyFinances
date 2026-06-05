# -*- coding: utf-8 -*-
"""
Страница деталей кошелька - просмотр и управление транзакциями

Отображает:
- Информацию о кошельке
- Таблицу транзакций с фильтрацией
- Кнопки для управления транзакциями
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QComboBox, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor

from models.models import Wallet, TransactionType
from services.services import TransactionService, BalanceHistoryService
from utils.helpers import format_currency, format_date
from ui.transaction_dialog import TransactionDialog
from ui.new_styles import new_colors, get_new_stylesheet, msgbox_warning, msgbox_question, msgbox_information, msgbox_critical
from ui.balance_chart_widget import BalanceChartWidget
from config import get_ui_mode, UI_MODE_NEW
from config import get_current_theme as config_get_current_theme


class WalletDetailsPage(QWidget):
    """
    Страница деталей кошелька
    Отображает транзакции и управление операциями
    
    Сигналы:
        back_requested: испускается при запросе выхода на Dashboard
    """
    
    back_requested = pyqtSignal()  # Вернуться на Dashboard
    
    def __init__(self):
        super().__init__()
        self.wallet = None
        self.transactions = []
        self.init_ui()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)

        # === Информация о кошельке ===
        header_layout = QHBoxLayout()
        
        self.wallet_info_label = QLabel()
        wallet_font = QFont()
        wallet_font.setPointSize(18)
        wallet_font.setBold(True)
        self.wallet_info_label.setFont(wallet_font)
        header_layout.addWidget(self.wallet_info_label)
        
        self.balance_label = QLabel()
        balance_font = QFont()
        balance_font.setPointSize(18)
        balance_font.setBold(True)
        self.balance_label.setFont(balance_font)
        header_layout.addWidget(self.balance_label)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # === График баланса ===
        self.balance_chart = BalanceChartWidget(currency="")
        self.balance_chart.setMinimumHeight(220)
        self.balance_chart.setMaximumHeight(260)
        layout.addWidget(self.balance_chart)

        # === Фильтрация ===
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Фильтр:"))
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("Все транзакции", "all")
        self.filter_combo.addItem("Доход", "income")
        self.filter_combo.addItem("Расход", "expense")
        self.filter_combo.currentIndexChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.filter_combo)
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # === Таблица транзакций ===
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Дата", "Тип", "Сумма", "Комментарий", "Категория", ""])
        self.table.setColumnWidth(0, 120)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 260)
        self.table.setColumnWidth(4, 120)
        self.table.hideColumn(5)  # Скрытая колонка для ID
        self.table.setMinimumHeight(450)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().hide()

        # Шрифт и цвета таблицы
        if get_ui_mode() == UI_MODE_NEW:
            c = new_colors()
            self.table.setStyleSheet(f"""
                QTableWidget {{
                    font-size: 12px;
                    background-color: {c['bg_card']};
                    alternate-background-color: {c['bg_main']};
                    gridline-color: {c['border']};
                    border: 1px solid {c['border']};
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
                    font-size: 12px;
                    font-weight: bold;
                    padding: 8px;
                    border: none;
                    border-bottom: 2px solid {c['border']};
                }}
                QTableCornerButton::section {{
                    background-color: {c['bg_hover']};
                    border: none;
                    border-bottom: 2px solid {c['border']};
                }}
            """)
        else:
            self.table.setStyleSheet("""
                QTableWidget { font-size: 12px; }
                QHeaderView::section { font-size: 12px; font-weight: bold; padding: 8px; }
            """)
        layout.addWidget(self.table)
        
        # === Кнопки управления ===
        button_layout = QHBoxLayout()
        
        btn_add = QPushButton("+ Добавить транзакцию")
        btn_add.clicked.connect(self.on_add_transaction)
        button_layout.addWidget(btn_add)
        
        btn_edit = QPushButton("Редактировать")
        btn_edit.clicked.connect(self.on_edit_transaction)
        button_layout.addWidget(btn_edit)
        
        btn_delete = QPushButton("- Удалить")
        btn_delete.setObjectName("btn_danger")
        btn_delete.clicked.connect(self.on_delete_transaction)
        button_layout.addWidget(btn_delete)
        
        button_layout.addStretch()
        
        btn_back = QPushButton("← Назад")
        btn_back.clicked.connect(self.on_back)
        button_layout.addWidget(btn_back)
        
        layout.addLayout(button_layout)
    
    def set_wallet(self, wallet: Wallet):
        """Установить кошелёк и обновить содержимое"""
        self.wallet = wallet
        wid = wallet.id
        self.balance_chart.currency = wallet.currency
        self.balance_chart.set_loader(
            lambda days, _wid=wid: BalanceHistoryService.get_wallet_balance_history(_wid, days)
        )
        self.refresh()
    
    def refresh(self):
        """Обновить страницу"""
        if not self.wallet:
            return
        
        # Обновить информацию о кошельке
        self.wallet_info_label.setText(f"{self.wallet.name}")
        self.balance_label.setText(format_currency(self.wallet.balance, self.wallet.currency))
        
        # Обновить таблицу
        self.refresh_transactions()
    
    def refresh_transactions(self):
        """Обновить таблицу транзакций"""
        self.transactions = TransactionService.get_wallet_transactions(self.wallet.id)
        self.populate_table(self.transactions)
    
    def populate_table(self, transactions):
        """Заполнить таблицу транзакциями"""
        self.table.setRowCount(len(transactions))
        
        for row, transaction in enumerate(transactions):
            # Дата
            date_item = QTableWidgetItem(format_date(transaction.created_at))
            self.table.setItem(row, 0, date_item)
            
            # Тип
            type_text = "Доход" if transaction.type == TransactionType.INCOME else "Расход"
            type_item = QTableWidgetItem(type_text)
            
            if transaction.type == TransactionType.INCOME:
                type_item.setForeground(QColor("#10b981"))  # Зелёный
            else:
                type_item.setForeground(QColor("#ef4444"))  # Красный
            
            self.table.setItem(row, 1, type_item)
            
            # Сумма
            amount_text = f"+{transaction.amount}" if transaction.type == TransactionType.INCOME else f"-{transaction.amount}"
            amount_item = QTableWidgetItem(amount_text)
            
            if transaction.type == TransactionType.INCOME:
                amount_item.setForeground(QColor("#10b981"))
            else:
                amount_item.setForeground(QColor("#ef4444"))
            
            self.table.setItem(row, 2, amount_item)
            
            # Комментарий
            comment_item = QTableWidgetItem(transaction.description)
            self.table.setItem(row, 3, comment_item)

            # Категория
            cat_name = transaction.category.name if transaction.category else "—"
            cat_item = QTableWidgetItem(cat_name)
            if transaction.category:
                cat_item.setForeground(QColor(transaction.category.color))
            self.table.setItem(row, 4, cat_item)

            # ID (скрытый)
            id_item = QTableWidgetItem(str(transaction.id))
            self.table.setItem(row, 5, id_item)
    
    def on_filter_changed(self):
        """Обработчик: изменение фильтра"""
        filter_type = self.filter_combo.currentData()
        
        filtered_transactions = self.transactions
        if filter_type != "all":
            if filter_type == "income":
                filtered_transactions = [t for t in self.transactions if t.type == TransactionType.INCOME]
            else:
                filtered_transactions = [t for t in self.transactions if t.type == TransactionType.EXPENSE]
        
        self.populate_table(filtered_transactions)
    
    def on_add_transaction(self):
        """Обработчик: добавить транзакцию"""
        dialog = TransactionDialog(self.wallet)
        if dialog.exec_():
            self.refresh()
    
    def on_edit_transaction(self):
        """Обработчик: редактировать транзакцию"""
        current_row = self.table.currentRow()
        
        if current_row < 0:
            msgbox_warning(self, "Внимание", "Выберите транзакцию для редактирования")
            return
        
        transaction_id = int(self.table.item(current_row, 5).text())
        transaction = next((t for t in self.transactions if t.id == transaction_id), None)
        
        if not transaction:
            msgbox_warning(self, "Ошибка", "Не удалось найти транзакцию")
            return
        
        dialog = TransactionDialog(self.wallet, transaction)
        if dialog.exec_():
            self.refresh()
    
    def on_delete_transaction(self):
        """Обработчик: удалить транзакцию"""
        current_row = self.table.currentRow()
        
        if current_row < 0:
            msgbox_warning(self, "Внимание", "Выберите транзакцию для удаления")
            return
        
        transaction_id = int(self.table.item(current_row, 5).text())
        
        reply = msgbox_question(
            self, "Подтверждение",
            "Удалить эту транзакцию?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, message = TransactionService.delete_transaction(transaction_id)
            
            if success:
                msgbox_information(self, "Успех", message)
                self.refresh()
            else:
                msgbox_critical(self, "Ошибка", message)
    
    def on_back(self):
        """Обработчик: вернуться на Dashboard"""
        self.back_requested.emit()
