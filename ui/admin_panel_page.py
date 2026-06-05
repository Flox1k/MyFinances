# -*- coding: utf-8 -*-
"""
Страница администрации - управление пользователями, кошельками и транзакциями

Содержит вкладки:
- Пользователи
- Кошельки
- Транзакции
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from services.services import AdminService, TransactionService, WalletService
from utils.helpers import format_date, format_currency
from config import get_ui_mode, UI_MODE_NEW


class AdminPanelPage(QWidget):
    """
    Страница администрации
    Содержит управление пользователями, кошельками и транзакциями
    """
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # === Заголовок ===
        title = QLabel("Администрирование")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # === Вкладки ===
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Вкладка пользователей
        is_new = get_ui_mode() == UI_MODE_NEW
        users_tab = self.create_users_tab()
        self.tabs.addTab(users_tab, "Пользователи" if is_new else "👥 Пользователи")
        
        # Вкладка кошельков
        wallets_tab = self.create_wallets_tab()
        self.tabs.addTab(wallets_tab, "Кошельки" if is_new else "💰 Кошельки")
        
        # Вкладка транзакций
        transactions_tab = self.create_transactions_tab()
        self.tabs.addTab(transactions_tab, "Транзакции" if is_new else "📊 Транзакции")
    
    def create_users_tab(self) -> QWidget:
        """Создать вкладку пользователей"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Таблица пользователей
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(4)
        self.users_table.setHorizontalHeaderLabels(["ID", "Имя пользователя", "Email", "Дата создания"])
        self.users_table.setAlternatingRowColors(True)
        layout.addWidget(self.users_table)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("↻ Обновить")
        refresh_btn.clicked.connect(self.refresh_users)
        button_layout.addWidget(refresh_btn)
        
        delete_btn = QPushButton("- Удалить пользователя")
        delete_btn.setObjectName("btn_danger")
        delete_btn.clicked.connect(self.delete_user)
        button_layout.addWidget(delete_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Загрузить данные
        self.refresh_users()
        
        return tab
    
    def create_wallets_tab(self) -> QWidget:
        """Создать вкладку кошельков"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Таблица кошельков
        self.wallets_table = QTableWidget()
        self.wallets_table.setColumnCount(5)
        self.wallets_table.setHorizontalHeaderLabels(
            ["ID", "Пользователь", "Название", "Баланс", "Валюта"]
        )
        self.wallets_table.setAlternatingRowColors(True)
        layout.addWidget(self.wallets_table)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("↻ Обновить")
        refresh_btn.clicked.connect(self.refresh_wallets)
        button_layout.addWidget(refresh_btn)
        
        delete_btn = QPushButton("- Удалить кошелёк")
        delete_btn.setObjectName("btn_danger")
        delete_btn.clicked.connect(self.delete_wallet)
        button_layout.addWidget(delete_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Загрузить данные
        self.refresh_wallets()
        
        return tab
    
    def create_transactions_tab(self) -> QWidget:
        """Создать вкладку транзакций"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Таблица транзакций
        self.transactions_table = QTableWidget()
        self.transactions_table.setColumnCount(6)
        self.transactions_table.setHorizontalHeaderLabels(
            ["ID", "Кошелёк", "Тип", "Сумма", "Комментарий", "Дата"]
        )
        self.transactions_table.setAlternatingRowColors(True)
        layout.addWidget(self.transactions_table)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("↻ Обновить")
        refresh_btn.clicked.connect(self.refresh_transactions)
        button_layout.addWidget(refresh_btn)
        
        delete_btn = QPushButton("- Удалить транзакцию")
        delete_btn.setObjectName("btn_danger")
        delete_btn.clicked.connect(self.delete_transaction)
        button_layout.addWidget(delete_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Загрузить данные
        self.refresh_transactions()
        
        return tab
    
    def refresh(self):
        """Обновить все данные"""
        self.refresh_users()
        self.refresh_wallets()
        self.refresh_transactions()
    
    def refresh_users(self):
        """Обновить таблицу пользователей"""
        users = AdminService.get_all_users()
        
        self.users_table.setRowCount(len(users))
        
        for row, user in enumerate(users):
            self.users_table.setItem(row, 0, QTableWidgetItem(str(user.id)))
            self.users_table.setItem(row, 1, QTableWidgetItem(user.username))
            self.users_table.setItem(row, 2, QTableWidgetItem(user.email))
            self.users_table.setItem(row, 3, QTableWidgetItem(format_date(user.created_at)))
    
    def refresh_wallets(self):
        """Обновить таблицу кошельков"""
        users = AdminService.get_all_users()
        
        rows = []
        for user in users:
            user_details = AdminService.get_user_details(user.id)
            for wallet in user_details.get("wallets", []):
                rows.append({
                    "id": wallet.id,
                    "user": user.username,
                    "name": wallet.name,
                    "balance": wallet.balance,
                    "currency": wallet.currency
                })
        
        self.wallets_table.setRowCount(len(rows))
        
        for row, data in enumerate(rows):
            self.wallets_table.setItem(row, 0, QTableWidgetItem(str(data["id"])))
            self.wallets_table.setItem(row, 1, QTableWidgetItem(data["user"]))
            self.wallets_table.setItem(row, 2, QTableWidgetItem(data["name"]))
            self.wallets_table.setItem(row, 3, QTableWidgetItem(format_currency(data["balance"], data["currency"])))
            self.wallets_table.setItem(row, 4, QTableWidgetItem(data["currency"]))
    
    def refresh_transactions(self):
        """Обновить таблицу транзакций"""
        users = AdminService.get_all_users()
        
        rows = []
        for user in users:
            user_details = AdminService.get_user_details(user.id)
            for wallet in user_details.get("wallets", []):
                transactions = TransactionService.get_wallet_transactions(wallet.id)
                for trans in transactions:
                    rows.append({
                        "id": trans.id,
                        "wallet": wallet.name,
                        "type": "Доход" if trans.type.value == "income" else "Расход",
                        "amount": trans.amount,
                        "description": trans.description,
                        "date": format_date(trans.created_at)
                    })
        
        self.transactions_table.setRowCount(len(rows))
        
        for row, data in enumerate(rows):
            self.transactions_table.setItem(row, 0, QTableWidgetItem(str(data["id"])))
            self.transactions_table.setItem(row, 1, QTableWidgetItem(data["wallet"]))
            self.transactions_table.setItem(row, 2, QTableWidgetItem(data["type"]))
            self.transactions_table.setItem(row, 3, QTableWidgetItem(str(data["amount"])))
            self.transactions_table.setItem(row, 4, QTableWidgetItem(data["description"]))
            self.transactions_table.setItem(row, 5, QTableWidgetItem(data["date"]))
    
    def delete_user(self):
        """Удалить пользователя"""
        current_row = self.users_table.currentRow()
        
        if current_row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите пользователя для удаления")
            return
        
        user_id = int(self.users_table.item(current_row, 0).text())
        username = self.users_table.item(current_row, 1).text()
        
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить пользователя '{username}' и все его данные?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, message = AdminService.delete_user(user_id)
            
            if success:
                QMessageBox.information(self, "Успех", message)
                self.refresh_users()
            else:
                QMessageBox.critical(self, "Ошибка", message)
    
    def delete_wallet(self):
        """Удалить кошелёк"""
        current_row = self.wallets_table.currentRow()
        
        if current_row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите кошелёк для удаления")
            return
        
        wallet_id = int(self.wallets_table.item(current_row, 0).text())
        
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Удалить кошелёк и все его транзакции?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, message = WalletService.delete_wallet(wallet_id)
            
            if success:
                QMessageBox.information(self, "Успех", message)
                self.refresh_wallets()
                self.refresh_transactions()
            else:
                QMessageBox.critical(self, "Ошибка", message)
    
    def delete_transaction(self):
        """Удалить транзакцию"""
        current_row = self.transactions_table.currentRow()
        
        if current_row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите транзакцию для удаления")
            return
        
        transaction_id = int(self.transactions_table.item(current_row, 0).text())
        
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Удалить транзакцию?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, message = TransactionService.delete_transaction(transaction_id)
            
            if success:
                QMessageBox.information(self, "Успех", message)
                self.refresh_transactions()
                self.refresh_wallets()
            else:
                QMessageBox.critical(self, "Ошибка", message)


from PyQt5.QtWidgets import QLabel
