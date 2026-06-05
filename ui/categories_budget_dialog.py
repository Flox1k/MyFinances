# -*- coding: utf-8 -*-
"""
Диалог управления категориями и бюджетами.

Вкладки:
- «Категории»: CRUD категорий, ключевые слова для авто-классификации
- «Бюджеты»:   установка месячных лимитов расходов, прогресс по категориям
"""

import datetime

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QListWidget, QListWidgetItem, QPushButton, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox,
    QComboBox, QDoubleSpinBox, QProgressBar, QMessageBox,
    QInputDialog, QColorDialog, QSizePolicy,
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor, QFont

from models.models import User
from services.services import CategoryService, BudgetService
from ui.new_styles import (
    new_colors, get_new_stylesheet, msgbox_warning,
    msgbox_question, msgbox_information,
)
from ui.toast_notification import show_toast
from config import get_current_theme as _get_theme

# Paleta preset colours (cycle on click)
_PALETTE = [
    "#6366f1", "#3b82f6", "#10b981", "#f59e0b",
    "#ef4444", "#8b5cf6", "#ec4899", "#f97316",
    "#14b8a6", "#6b7280",
]

MONTHS_RU = [
    "", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
]


class CategoryBudgetDialog(QDialog):
    """
    Диалоговое окно управления категориями и бюджетами.
    """

    def __init__(self, user: User, parent=None):
        super().__init__(parent)
        self.user = user
        self.current_theme = _get_theme()
        self.setWindowTitle("Категории и бюджеты")
        self.setMinimumSize(720, 560)
        self.setModal(True)
        self.setStyleSheet(get_new_stylesheet(self.current_theme))

        # state
        self._selected_cat_id = None   # id выбранной категории
        self._selected_color = "#6366f1"

        self._build_ui()
        self._load_categories()

    # ─────────────────────────────────────────────────────────────────────────
    # Build
    # ─────────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_categories_tab(), "Категории")
        self.tabs.addTab(self._build_budgets_tab(), "Бюджеты")
        root.addWidget(self.tabs)

        # close button
        close_btn = QPushButton("Закрыть")
        close_btn.setMinimumHeight(36)
        close_btn.clicked.connect(self.accept)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(close_btn)
        root.addLayout(row)

    # ── Categories tab ────────────────────────────────────────────────────────

    def _build_categories_tab(self) -> QWidget:
        tab = QWidget()
        lay = QHBoxLayout(tab)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(12)

        # Left: list + action buttons
        left = QVBoxLayout()
        left.setSpacing(6)

        self.cat_list = QListWidget()
        self.cat_list.setMinimumWidth(220)
        self.cat_list.currentItemChanged.connect(self._on_cat_selected)
        left.addWidget(self.cat_list)

        btn_row1 = QHBoxLayout()
        btn_add = QPushButton("+ Добавить")
        btn_add.clicked.connect(self._on_cat_add)
        btn_edit = QPushButton("Изменить")
        btn_edit.clicked.connect(self._on_cat_edit)
        btn_row1.addWidget(btn_add)
        btn_row1.addWidget(btn_edit)
        left.addLayout(btn_row1)

        btn_row2 = QHBoxLayout()
        btn_del = QPushButton("Удалить")
        btn_del.clicked.connect(self._on_cat_delete)
        btn_default = QPushButton("По умолчанию")
        btn_default.clicked.connect(self._on_cat_set_default)
        btn_row2.addWidget(btn_del)
        btn_row2.addWidget(btn_default)
        left.addLayout(btn_row2)

        lay.addLayout(left)

        # Right: keyword editor
        right = QVBoxLayout()
        right.setSpacing(6)

        kw_title = QLabel("Ключевые слова (авто-классификация):")
        kw_title.setStyleSheet("font-weight: 600;")
        right.addWidget(kw_title)

        self.kw_list = QListWidget()
        right.addWidget(self.kw_list)

        kw_input_row = QHBoxLayout()
        self.kw_input = QLineEdit()
        self.kw_input.setPlaceholderText("Новое ключевое слово…")
        self.kw_input.setMinimumHeight(34)
        self.kw_input.returnPressed.connect(self._on_kw_add)
        kw_input_row.addWidget(self.kw_input, 1)
        btn_kw_add = QPushButton("+")
        btn_kw_add.setFixedSize(34, 34)
        btn_kw_add.clicked.connect(self._on_kw_add)
        kw_input_row.addWidget(btn_kw_add)
        right.addLayout(kw_input_row)

        btn_kw_del = QPushButton("- Удалить выбранное слово")
        btn_kw_del.clicked.connect(self._on_kw_delete)
        right.addWidget(btn_kw_del)

        lay.addLayout(right, 1)
        return tab

    # ── Budgets tab ───────────────────────────────────────────────────────────

    def _build_budgets_tab(self) -> QWidget:
        tab = QWidget()
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(8)

        # Month selector
        month_row = QHBoxLayout()
        month_row.addWidget(QLabel("Год:"))
        self.year_spin = QSpinBox()
        self.year_spin.setRange(2000, 2100)
        self.year_spin.setValue(datetime.date.today().year)
        self.year_spin.setMinimumHeight(32)
        month_row.addWidget(self.year_spin)

        month_row.addWidget(QLabel("Месяц:"))
        self.month_combo = QComboBox()
        for i, m in enumerate(MONTHS_RU[1:], 1):
            self.month_combo.addItem(m, i)
        self.month_combo.setCurrentIndex(datetime.date.today().month - 1)
        self.month_combo.setMinimumHeight(32)
        month_row.addWidget(self.month_combo)

        btn_load = QPushButton("Загрузить")
        btn_load.setMinimumHeight(32)
        btn_load.clicked.connect(self._load_budgets)
        month_row.addWidget(btn_load)
        month_row.addStretch()
        lay.addLayout(month_row)

        # Budget table
        self.budget_table = QTableWidget()
        self.budget_table.setColumnCount(5)
        self.budget_table.setHorizontalHeaderLabels(
            ["Категория", "Лимит", "Потрачено", "Прогресс", "Порог %"]
        )
        self.budget_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.budget_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.budget_table.setColumnWidth(1, 100)
        self.budget_table.setColumnWidth(2, 100)
        self.budget_table.setColumnWidth(4, 80)
        self.budget_table.setAlternatingRowColors(True)
        self.budget_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.budget_table.setSelectionBehavior(QTableWidget.SelectRows)
        lay.addWidget(self.budget_table)

        # Action buttons
        btn_row = QHBoxLayout()
        btn_set = QPushButton("+ Добавить / Изменить бюджет")
        btn_set.clicked.connect(self._on_budget_set)
        btn_del_b = QPushButton("Удалить бюджет")
        btn_del_b.clicked.connect(self._on_budget_delete)
        btn_row.addWidget(btn_set)
        btn_row.addWidget(btn_del_b)
        btn_row.addStretch()
        lay.addLayout(btn_row)

        self._load_budgets()
        return tab

    # ─────────────────────────────────────────────────────────────────────────
    # Categories logic
    # ─────────────────────────────────────────────────────────────────────────

    def _load_categories(self):
        prev_id = self._selected_cat_id
        self.cat_list.clear()
        cats = CategoryService.get_user_categories(self.user.id)
        for cat in cats:
            item = QListWidgetItem()
            label = cat.name
            if cat.is_default:
                label += "  ★"
            item.setText(label)
            item.setData(Qt.UserRole, cat.id)
            item.setData(Qt.UserRole + 1, cat.color)
            item.setForeground(QColor(cat.color))
            self.cat_list.addItem(item)
        # restore selection
        if prev_id is not None:
            for i in range(self.cat_list.count()):
                if self.cat_list.item(i).data(Qt.UserRole) == prev_id:
                    self.cat_list.setCurrentRow(i)
                    break

    def _on_cat_selected(self, current, _previous):
        if current is None:
            self._selected_cat_id = None
            self.kw_list.clear()
            return
        self._selected_cat_id = current.data(Qt.UserRole)
        self._load_keywords()

    def _load_keywords(self):
        self.kw_list.clear()
        if self._selected_cat_id is None:
            return
        from db.database import get_session
        from db.repositories import CategoryRepository
        session = get_session()
        try:
            kws = CategoryRepository(session).get_keywords(self._selected_cat_id)
            for kw in kws:
                item = QListWidgetItem(kw.keyword)
                item.setData(Qt.UserRole, kw.id)
                self.kw_list.addItem(item)
        finally:
            session.close()

    def _on_cat_add(self):
        name, ok = QInputDialog.getText(self, "Новая категория", "Название категории:")
        if not ok or not name.strip():
            return
        color = self._pick_color("#6366f1")
        ok2, msg, _ = CategoryService.create_category(
            self.user.id, name.strip(), color
        )
        if ok2:
            self._load_categories()
        else:
            msgbox_warning(self, "Ошибка", msg)

    def _on_cat_edit(self):
        if self._selected_cat_id is None:
            msgbox_warning(self, "Внимание", "Выберите категорию")
            return
        item = self.cat_list.currentItem()
        old_name = item.text().replace("  ★", "").strip()
        old_color = item.data(Qt.UserRole + 1)
        name, ok = QInputDialog.getText(
            self, "Переименовать", "Новое название:", text=old_name
        )
        if not ok or not name.strip():
            return
        color = self._pick_color(old_color)
        ok2, msg, _ = CategoryService.update_category(
            self._selected_cat_id, name=name.strip(), color=color
        )
        if ok2:
            self._load_categories()
        else:
            msgbox_warning(self, "Ошибка", msg)

    def _on_cat_delete(self):
        if self._selected_cat_id is None:
            msgbox_warning(self, "Внимание", "Выберите категорию")
            return
        reply = msgbox_question(
            self, "Подтверждение",
            "Удалить категорию? Транзакции потеряют привязку к ней.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            ok, msg = CategoryService.delete_category(self._selected_cat_id)
            if ok:
                self._selected_cat_id = None
                self.kw_list.clear()
                self._load_categories()
                self._load_budgets()
            else:
                msgbox_warning(self, "Ошибка", msg)

    def _on_cat_set_default(self):
        if self._selected_cat_id is None:
            msgbox_warning(self, "Внимание", "Выберите категорию")
            return
        ok, msg, _ = CategoryService.update_category(
            self._selected_cat_id, is_default=True
        )
        if ok:
            self._load_categories()
        else:
            msgbox_warning(self, "Ошибка", msg)

    def _pick_color(self, current: str) -> str:
        """Открыть QColorDialog, вернуть выбранный hex или current."""
        color = QColorDialog.getColor(QColor(current), self, "Выберите цвет")
        if color.isValid():
            return color.name()
        return current

    # ─────────────────────────────────────────────────────────────────────────
    # Keywords logic
    # ─────────────────────────────────────────────────────────────────────────

    def _on_kw_add(self):
        if self._selected_cat_id is None:
            msgbox_warning(self, "Внимание", "Сначала выберите категорию")
            return
        kw = self.kw_input.text().strip()
        if not kw:
            return
        ok, msg, _ = CategoryService.add_keyword(self._selected_cat_id, kw)
        if ok:
            self.kw_input.clear()
            self._load_keywords()
        else:
            msgbox_warning(self, "Ошибка", msg)

    def _on_kw_delete(self):
        item = self.kw_list.currentItem()
        if item is None:
            msgbox_warning(self, "Внимание", "Выберите ключевое слово")
            return
        kw_id = item.data(Qt.UserRole)
        ok, msg = CategoryService.remove_keyword(kw_id)
        if ok:
            self._load_keywords()
        else:
            msgbox_warning(self, "Ошибка", msg)

    # ─────────────────────────────────────────────────────────────────────────
    # Budgets logic
    # ─────────────────────────────────────────────────────────────────────────

    def _load_budgets(self):
        year = self.year_spin.value()
        month = self.month_combo.currentData()
        items = BudgetService.get_budgets_with_progress(self.user.id, year, month)

        self.budget_table.setRowCount(len(items))
        for row, info in enumerate(items):
            cat = info["category"]
            budget = info["budget"]

            # Category name
            name_item = QTableWidgetItem(cat.name if cat else "—")
            if cat:
                name_item.setForeground(QColor(cat.color))
            self.budget_table.setItem(row, 0, name_item)

            # Limit
            limit_item = QTableWidgetItem(f"{info['limit']:,.0f}")
            self.budget_table.setItem(row, 1, limit_item)

            # Spent
            spent_item = QTableWidgetItem(f"{info['spent']:,.0f}")
            self.budget_table.setItem(row, 2, spent_item)

            # Progress bar
            bar = QProgressBar()
            pct_clamped = min(int(info["pct"]), 100)
            bar.setValue(pct_clamped)
            bar.setFormat(f"{info['pct']:.1f}%")
            bar.setTextVisible(True)
            bar.setMinimumHeight(22)
            if info["over_limit"]:
                bar.setStyleSheet(
                    "QProgressBar::chunk { background: #ef4444; border-radius: 4px; }"
                    "QProgressBar { border-radius: 4px; border: 1px solid #6b7280; }"
                )
            elif info["at_warning"]:
                bar.setStyleSheet(
                    "QProgressBar::chunk { background: #f59e0b; border-radius: 4px; }"
                    "QProgressBar { border-radius: 4px; border: 1px solid #6b7280; }"
                )
            else:
                bar.setStyleSheet(
                    "QProgressBar::chunk { background: #10b981; border-radius: 4px; }"
                    "QProgressBar { border-radius: 4px; border: 1px solid #6b7280; }"
                )
            self.budget_table.setCellWidget(row, 3, bar)

            # Threshold
            thr_item = QTableWidgetItem(f"{budget.warning_threshold:.0f}%")
            thr_item.setData(Qt.UserRole, budget.id)
            self.budget_table.setItem(row, 4, thr_item)

    def _on_budget_set(self):
        cats = CategoryService.get_user_categories(self.user.id)
        if not cats:
            msgbox_warning(self, "Внимание", "Сначала создайте хотя бы одну категорию")
            return

        dlg = _SetBudgetDialog(cats, self.year_spin.value(),
                               self.month_combo.currentData(), self)
        if dlg.exec_() == QDialog.Accepted:
            ok, msg, _ = BudgetService.set_budget(
                user_id=self.user.id,
                category_id=dlg.selected_category_id,
                year=dlg.selected_year,
                month=dlg.selected_month,
                limit_amount=dlg.limit_amount,
                warning_threshold=dlg.warning_threshold,
            )
            if ok:
                self._load_budgets()
            else:
                msgbox_warning(self, "Ошибка", msg)

    def _on_budget_delete(self):
        row = self.budget_table.currentRow()
        if row < 0:
            msgbox_warning(self, "Внимание", "Выберите бюджет")
            return
        item = self.budget_table.item(row, 4)
        if item is None:
            return
        budget_id = item.data(Qt.UserRole)
        reply = msgbox_question(
            self, "Подтверждение", "Удалить этот бюджет?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            ok, msg = BudgetService.delete_budget(budget_id)
            if ok:
                self._load_budgets()
            else:
                msgbox_warning(self, "Ошибка", msg)


# ─────────────────────────────────────────────────────────────────────────────
# Sub-dialog: set budget
# ─────────────────────────────────────────────────────────────────────────────

class _SetBudgetDialog(QDialog):
    """Диалог для установки/изменения лимита бюджета."""

    def __init__(self, categories, year: int, month: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Установить бюджет")
        self.setModal(True)
        self.setMinimumWidth(360)
        self.setStyleSheet(parent.styleSheet() if parent else "")

        self.selected_category_id = None
        self.selected_year = year
        self.selected_month = month
        self.limit_amount = 0.0
        self.warning_threshold = 80.0

        lay = QVBoxLayout(self)
        lay.setSpacing(10)
        lay.setContentsMargins(16, 16, 16, 16)

        lay.addWidget(QLabel("Категория:"))
        self.cat_combo = QComboBox()
        for cat in categories:
            self.cat_combo.addItem(cat.name, cat.id)
        self.cat_combo.setMinimumHeight(34)
        lay.addWidget(self.cat_combo)

        # Year + month
        ym_row = QHBoxLayout()
        ym_row.addWidget(QLabel("Год:"))
        self.year_spin = QSpinBox()
        self.year_spin.setRange(2000, 2100)
        self.year_spin.setValue(year)
        self.year_spin.setMinimumHeight(34)
        ym_row.addWidget(self.year_spin)
        ym_row.addWidget(QLabel("Месяц:"))
        self.month_combo = QComboBox()
        for i, m in enumerate(MONTHS_RU[1:], 1):
            self.month_combo.addItem(m, i)
        self.month_combo.setCurrentIndex(month - 1)
        self.month_combo.setMinimumHeight(34)
        ym_row.addWidget(self.month_combo)
        lay.addLayout(ym_row)

        lay.addWidget(QLabel("Лимит расходов:"))
        self.limit_spin = QDoubleSpinBox()
        self.limit_spin.setRange(0.01, 999_999_999)
        self.limit_spin.setDecimals(2)
        self.limit_spin.setValue(10_000)
        self.limit_spin.setMinimumHeight(34)
        lay.addWidget(self.limit_spin)

        lay.addWidget(QLabel("Порог предупреждения (%):"))
        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(1, 100)
        self.threshold_spin.setDecimals(0)
        self.threshold_spin.setValue(80)
        self.threshold_spin.setMinimumHeight(34)
        lay.addWidget(self.threshold_spin)

        btn_row = QHBoxLayout()
        ok_btn = QPushButton("Сохранить")
        ok_btn.setMinimumHeight(36)
        ok_btn.clicked.connect(self._on_ok)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.setMinimumHeight(36)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        lay.addLayout(btn_row)

    def _on_ok(self):
        self.selected_category_id = self.cat_combo.currentData()
        self.selected_year = self.year_spin.value()
        self.selected_month = self.month_combo.currentData()
        self.limit_amount = self.limit_spin.value()
        self.warning_threshold = self.threshold_spin.value()
        self.accept()
