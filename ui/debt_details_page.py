# -*- coding: utf-8 -*-
"""
Страница деталей кейса долга — просмотр и управление операциями
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QComboBox, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor

from models.models import DebtType
from services.services import DebtTransactionService, BalanceHistoryService
from utils.helpers import format_currency, format_date
from ui.debt_transaction_dialog import DebtTransactionDialog
from ui.new_styles import new_colors, msgbox_warning, msgbox_question, msgbox_information, msgbox_critical
from ui.balance_chart_widget import BalanceChartWidget
from config import get_ui_mode, UI_MODE_NEW


class DebtDetailsPage(QWidget):
    """Страница операций по конкретному кейсу долга"""

    back_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.debt = None
        self.transactions = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)

        # Заголовок
        header = QHBoxLayout()

        self.info_label = QLabel()
        f = QFont(); f.setPointSize(18); f.setBold(True)
        self.info_label.setFont(f)
        header.addWidget(self.info_label)

        self.balance_label = QLabel()
        bf = QFont(); bf.setPointSize(18); bf.setBold(True)
        self.balance_label.setFont(bf)
        header.addWidget(self.balance_label)

        header.addStretch()
        layout.addLayout(header)

        # График изменения баланса долга
        self.balance_chart = BalanceChartWidget(currency="")
        self.balance_chart.setMinimumHeight(220)
        self.balance_chart.setMaximumHeight(260)
        layout.addWidget(self.balance_chart)

        # Фильтр
        flt = QHBoxLayout()
        flt.addWidget(QLabel("Фильтр:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("Все операции", "all")
        self.filter_combo.addItem("Дал в долг", "gave")
        self.filter_combo.addItem("Взял в долг", "took")
        self.filter_combo.currentIndexChanged.connect(self._on_filter)
        flt.addWidget(self.filter_combo)
        flt.addStretch()
        layout.addLayout(flt)

        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Дата", "Тип", "Сумма", "Комментарий", ""])
        self.table.setColumnWidth(0, 120)
        self.table.setColumnWidth(1, 130)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 350)
        self.table.hideColumn(4)
        self.table.setMinimumHeight(450)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().hide()
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

        # Кнопки
        btns = QHBoxLayout()

        btn_add = QPushButton("+ Добавить операцию")
        btn_add.clicked.connect(self._on_add)
        btns.addWidget(btn_add)

        btn_edit = QPushButton("Редактировать")
        btn_edit.clicked.connect(self._on_edit)
        btns.addWidget(btn_edit)

        btn_del = QPushButton("- Удалить")
        btn_del.setObjectName("btn_danger")
        btn_del.clicked.connect(self._on_delete)
        btns.addWidget(btn_del)

        btns.addStretch()

        btn_back = QPushButton("← Назад")
        btn_back.clicked.connect(lambda: self.back_requested.emit())
        btns.addWidget(btn_back)

        layout.addLayout(btns)

    # ──────────────────────────────────────────────────────────────────────────

    def set_debt(self, debt):
        self.debt = debt
        did = debt.id
        self.balance_chart.currency = debt.currency
        self.balance_chart.set_loader(
            lambda days, _did=did: BalanceHistoryService.get_debt_balance_history(_did, days)
        )
        self.refresh()

    def refresh(self):
        if not self.debt:
            return
        # Перечитать debt из БД для актуального баланса
        from services.services import DebtService
        fresh = DebtService.get_debt_by_id(self.debt.id)
        if fresh:
            self.debt = fresh
        self.info_label.setText(self.debt.name)
        self.balance_label.setText(format_currency(self.debt.balance, self.debt.currency))
        if self.debt.balance > 0:
            self.balance_label.setStyleSheet("color: #10b981;")
        elif self.debt.balance < 0:
            self.balance_label.setStyleSheet("color: #ef4444;")
        else:
            self.balance_label.setStyleSheet("")
        self.transactions = DebtTransactionService.get_debt_transactions(self.debt.id)
        self._populate(self.transactions)

    def _populate(self, txs):
        self.table.setRowCount(len(txs))
        for row, t in enumerate(txs):
            self.table.setItem(row, 0, QTableWidgetItem(format_date(t.created_at)))

            is_gave = (t.type == DebtType.GAVE)
            type_text = "Дал в долг" if is_gave else "Взял в долг"
            ti = QTableWidgetItem(type_text)
            ti.setForeground(QColor("#10b981") if is_gave else QColor("#ef4444"))
            self.table.setItem(row, 1, ti)

            amt_text = f"+{t.amount}" if is_gave else f"-{t.amount}"
            ai = QTableWidgetItem(amt_text)
            ai.setForeground(QColor("#10b981") if is_gave else QColor("#ef4444"))
            self.table.setItem(row, 2, ai)

            self.table.setItem(row, 3, QTableWidgetItem(t.description))
            self.table.setItem(row, 4, QTableWidgetItem(str(t.id)))

    def _on_filter(self):
        ft = self.filter_combo.currentData()
        if ft == "all":
            self._populate(self.transactions)
        elif ft == "gave":
            self._populate([t for t in self.transactions if t.type == DebtType.GAVE])
        else:
            self._populate([t for t in self.transactions if t.type == DebtType.TOOK])

    def _on_add(self):
        dlg = DebtTransactionDialog(self.debt)
        if dlg.exec_():
            self.refresh()

    def _on_edit(self):
        row = self.table.currentRow()
        if row < 0:
            msgbox_warning(self, "Внимание", "Выберите операцию")
            return
        tid = int(self.table.item(row, 4).text())
        tx = next((t for t in self.transactions if t.id == tid), None)
        if not tx:
            return
        dlg = DebtTransactionDialog(self.debt, tx)
        if dlg.exec_():
            self.refresh()

    def _on_delete(self):
        row = self.table.currentRow()
        if row < 0:
            msgbox_warning(self, "Внимание", "Выберите операцию")
            return
        tid = int(self.table.item(row, 4).text())
        reply = msgbox_question(
            self, "Подтверждение", "Удалить эту операцию?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            ok, msg = DebtTransactionService.delete_transaction(tid)
            if ok:
                msgbox_information(self, "Успех", msg)
                self.refresh()
            else:
                msgbox_critical(self, "Ошибка", msg)
