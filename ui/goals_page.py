# -*- coding: utf-8 -*-
"""
Страница управления финансовыми целями

Функции:
- Создание / редактирование / удаление целей
- Отображение прогресса по каждой цели
- Выбор цели для отслеживания на главном экране
"""

from datetime import date

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QScrollArea, QDialog, QFormLayout, QLineEdit, QDateEdit,
    QComboBox, QTextEdit, QMessageBox, QProgressBar, QDoubleSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy,
    QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor

from models.models import User
from services.services import GoalService, GoalTransactionService
from models.models import GoalTransactionType
from utils.helpers import format_currency
from ui.styles import (
    get_text_color, get_text_secondary_color,
    get_income_color, get_expense_color, get_primary_color
)
from ui.new_styles import new_colors, get_new_stylesheet, apply_dark_title_bar, msgbox_critical, msgbox_question, msgbox_information, inputdlg_double, scale_px, scale_css
from config import get_ui_mode, UI_MODE_NEW

CURRENCIES = ["KZT", "USD", "EUR", "RUB", "GBP", "CNY"]


# ──────────────────────────────────────────────────────────────────────────────
#  Диалог истории транзакций по цели
# ──────────────────────────────────────────────────────────────────────────────

class GoalHistoryDialog(QDialog):
    """Диалог просмотра истории добавлений/убавлений по цели."""

    def __init__(self, goal, parent=None):
        super().__init__(parent)
        self.goal = goal
        self.setWindowTitle(f"История — {goal.name}")
        self.setMinimumSize(520, 400)
        self.setModal(True)
        if get_ui_mode() == UI_MODE_NEW:
            from config import get_current_theme
            self.setStyleSheet(get_new_stylesheet(get_current_theme()))
        self._build_ui()
        self._load()

    def showEvent(self, event):
        super().showEvent(event)
        if get_ui_mode() == UI_MODE_NEW:
            apply_dark_title_bar(self)

    def _build_ui(self):
        is_new_ui = get_ui_mode() == UI_MODE_NEW
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Заголовок
        title = QLabel(f"История изменений: {self.goal.name}")
        tf = QFont()
        tf.setPointSize(13)
        tf.setBold(True)
        title.setFont(tf)
        layout.addWidget(title)

        # Таблица
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Дата", "Операция", f"Сумма ({self.goal.currency})"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        # Кнопка закрыть
        close_btn = QPushButton("Закрыть")
        close_btn.setFixedHeight(34)
        close_btn.clicked.connect(self.accept)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(close_btn)
        layout.addLayout(row)

    def _load(self):
        transactions = GoalTransactionService.get_transactions(self.goal.id)
        self.table.setRowCount(len(transactions))
        is_new_ui = get_ui_mode() == UI_MODE_NEW
        if is_new_ui:
            c = new_colors()
            add_color = QColor(c["secondary"])
            sub_color = QColor(c["danger"])
        else:
            add_color = QColor("#10b981")
            sub_color = QColor("#ef4444")

        for row, tx in enumerate(transactions):
            date_str = tx.created_at.strftime("%d.%m.%Y %H:%M")
            op_str = "Добавление" if tx.type == GoalTransactionType.ADD else "Убавление"
            amount_str = f"{tx.amount:,.2f}"

            date_item = QTableWidgetItem(date_str)
            op_item = QTableWidgetItem(op_str)
            amt_item = QTableWidgetItem(amount_str)
            amt_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            color = add_color if tx.type == GoalTransactionType.ADD else sub_color
            for item in (date_item, op_item, amt_item):
                item.setForeground(color)

            self.table.setItem(row, 0, date_item)
            self.table.setItem(row, 1, op_item)
            self.table.setItem(row, 2, amt_item)

        if not transactions:
            self.table.setRowCount(1)
            empty = QTableWidgetItem("Нет записей об изменениях")
            empty.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(0, 0, empty)
            self.table.setSpan(0, 0, 1, 3)


# ──────────────────────────────────────────────────────────────────────────────
#  Диалог создания / редактирования цели
# ──────────────────────────────────────────────────────────────────────────────

class GoalDialog(QDialog):
    """Диалог для создания или редактирования финансовой цели"""

    def __init__(self, parent=None, goal=None):
        super().__init__(parent)
        self.goal = goal  # None → создание, объект → редактирование
        title = "Редактировать цель" if goal else "Новая цель"
        self.setWindowTitle(title)
        self.setMinimumWidth(420)
        self.setModal(True)
        if get_ui_mode() == UI_MODE_NEW:
            from config import get_current_theme
            self.setStyleSheet(get_new_stylesheet(get_current_theme()))
        self._build_ui()
        if goal:
            self._fill_from_goal(goal)

    def showEvent(self, event):
        super().showEvent(event)
        if get_ui_mode() == UI_MODE_NEW:
            apply_dark_title_bar(self)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        form = QFormLayout()
        form.setSpacing(10)

        # Название
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Например: Новый автомобиль")
        form.addRow("Название:", self.name_edit)

        # Целевая сумма
        self.target_spin = QDoubleSpinBox()
        self.target_spin.setRange(0.01, 999_999_999.0)
        self.target_spin.setDecimals(2)
        self.target_spin.setSingleStep(1000)
        self.target_spin.setValue(10000)
        form.addRow("Целевая сумма:", self.target_spin)

        # Текущая накопленная сумма
        self.current_spin = QDoubleSpinBox()
        self.current_spin.setRange(0.0, 999_999_999.0)
        self.current_spin.setDecimals(2)
        self.current_spin.setSingleStep(1000)
        self.current_spin.setValue(0)
        form.addRow("Уже накоплено:", self.current_spin)

        # Валюта
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(CURRENCIES)
        form.addRow("Валюта:", self.currency_combo)

        # Дата начала
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())
        form.addRow("Дата начала:", self.start_date)

        # Дата конца
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate().addMonths(6))
        form.addRow("Дата окончания:", self.end_date)

        # Описание
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Комментарий (необязательно)")
        self.description_edit.setMaximumHeight(80)
        form.addRow("Описание:", self.description_edit)

        layout.addLayout(form)

        # Кнопки
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        save_btn.setObjectName("primary_button")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def _fill_from_goal(self, goal):
        self.name_edit.setText(goal.name)
        self.target_spin.setValue(goal.target_amount)
        self.current_spin.setValue(goal.current_amount)
        idx = CURRENCIES.index(goal.currency) if goal.currency in CURRENCIES else 0
        self.currency_combo.setCurrentIndex(idx)
        self.start_date.setDate(QDate(goal.start_date.year, goal.start_date.month, goal.start_date.day))
        self.end_date.setDate(QDate(goal.end_date.year, goal.end_date.month, goal.end_date.day))
        self.description_edit.setPlainText(goal.description or "")

    # ── Getters ──────────────────────────────────────────────────────────────

    def get_name(self) -> str:
        return self.name_edit.text().strip()

    def get_target_amount(self) -> float:
        return self.target_spin.value()

    def get_current_amount(self) -> float:
        return self.current_spin.value()

    def get_currency(self) -> str:
        return self.currency_combo.currentText()

    def get_start_date(self) -> date:
        qd = self.start_date.date()
        return date(qd.year(), qd.month(), qd.day())

    def get_end_date(self) -> date:
        qd = self.end_date.date()
        return date(qd.year(), qd.month(), qd.day())

    def get_description(self) -> str:
        return self.description_edit.toPlainText().strip()


# ──────────────────────────────────────────────────────────────────────────────
#  Карточка цели
# ──────────────────────────────────────────────────────────────────────────────

class GoalCard(QWidget):
    """Карточка одной финансовой цели с прогресс-баром"""

    def __init__(self, goal, on_edit, on_delete, on_track, on_update_amount,
                 on_add_amount, on_subtract_amount, on_history):
        super().__init__()
        self.goal = goal
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._build(on_edit, on_delete, on_track, on_update_amount,
                    on_add_amount, on_subtract_amount, on_history)

    def _build(self, on_edit, on_delete, on_track, on_update_amount,
               on_add_amount, on_subtract_amount, on_history):
        is_new_ui = get_ui_mode() == UI_MODE_NEW
        text_color = get_text_color()
        if is_new_ui:
            c = new_colors()
            name_color = c['text_primary']
            secondary = c['text_secondary']
            card_bg = c['bg_card']
            card_border = c['border']
            card_hover_bg = c['bg_hover']
        else:
            name_color = "#000000"
            secondary = get_text_secondary_color()
            card_bg = "#ffffff"
            card_border = "#e5e7eb"
            card_hover_bg = "#f9fafb"
        income_color = get_income_color()
        danger_color = get_expense_color()
        primary_color = get_primary_color()

        self.setObjectName("goal_card")
        is_new_ui_mode = get_ui_mode() == UI_MODE_NEW
        if is_new_ui_mode:
            c_n = new_colors()
            # Более заметный фон карточки
            self.setStyleSheet(f"""
                QWidget#goal_card {{
                    background-color: {c_n['bg_card']};
                    border: 1.5px solid {c_n['border']};
                    border-radius: 10px;
                }}
            """)
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(16)
            shadow.setXOffset(0)
            shadow.setYOffset(3)
            shadow.setColor(QColor(0, 0, 0, 60))
            self.setGraphicsEffect(shadow)
        else:
            self.setStyleSheet(f"""
                QWidget#goal_card {{
                    background-color: {card_bg};
                    border: 1px solid {card_border};
                    border-radius: 6px;
                }}
            """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 12, 14, 12)
        outer.setSpacing(8)

        # ── Строка 1: название + бейдж "отслеживается" ──
        top_row = QHBoxLayout()
        name_lbl = QLabel(self.goal.name)
        name_font = QFont()
        name_font.setPointSize(13)
        name_font.setBold(True)
        name_lbl.setFont(name_font)
        name_lbl.setStyleSheet(f"color: {name_color};")
        top_row.addWidget(name_lbl)

        if self.goal.is_tracked:
            tracked_badge = QLabel("Отслеживаемое")
            badge_color = c['primary'] if is_new_ui else primary_color
            tracked_badge.setStyleSheet(
                f"color: #ffffff; background-color: {badge_color}; border-radius: 4px;"
                "padding: 2px 8px; font-size: 11px; font-weight: bold;"
            )
            top_row.addWidget(tracked_badge)

        top_row.addStretch()
        outer.addLayout(top_row)

        # ── Строка 2: суммы + период ──
        info_row = QHBoxLayout()
        progress_pct = 0.0
        if self.goal.target_amount > 0:
            progress_pct = min(self.goal.current_amount / self.goal.target_amount * 100, 100)

        amt_lbl = QLabel(
            f"{format_currency(self.goal.current_amount, self.goal.currency)}"
            f" из {format_currency(self.goal.target_amount, self.goal.currency)}"
            f"  ({progress_pct:.1f}%)"
        )
        amt_lbl.setStyleSheet(scale_css(f"font-size: 12px; color: {secondary};"))
        info_row.addWidget(amt_lbl)

        info_row.addStretch()

        dates_lbl = QLabel(
            f"{self.goal.start_date.strftime('%d.%m.%Y')} — {self.goal.end_date.strftime('%d.%m.%Y')}"
        )
        dates_lbl.setStyleSheet(scale_css(f"font-size: 11px; color: {secondary};"))
        info_row.addWidget(dates_lbl)
        outer.addLayout(info_row)

        # ── Прогресс-бар ──
        bar = QProgressBar()
        bar.setMinimum(0)
        bar.setMaximum(100)
        bar.setValue(int(progress_pct))
        bar.setTextVisible(False)
        bar.setFixedHeight(scale_px(10))

        bar_color = income_color if progress_pct >= 100 else (c['primary'] if is_new_ui else primary_color)
        bar_track = c['border'] if is_new_ui else "#e5e7eb"
        bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {bar_track};
                border-radius: 5px;
            }}
            QProgressBar::chunk {{
                background-color: {bar_color};
                border-radius: 5px;
            }}
        """)
        outer.addWidget(bar)

        # ── Описание ──
        if self.goal.description:
            desc_lbl = QLabel(self.goal.description)
            desc_lbl.setStyleSheet(scale_css(f"font-size: 11px; color: {secondary}; font-style: italic;"))
            desc_lbl.setWordWrap(True)
            outer.addWidget(desc_lbl)

        # ── Кнопки действий ──
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        is_new_ui = get_ui_mode() == UI_MODE_NEW

        # Стиль нейтральных кнопок (для нового UI)
        if is_new_ui:
            neutral_style = scale_css(
                f"QPushButton {{ font-size: 11px; padding: 2px 8px;"
                f" background-color: rgba(99,102,241,0.12); color: {c['primary']};"
                f" border: 1px solid rgba(99,102,241,0.35); border-radius: 4px; }}"
                f" QPushButton:hover {{ background-color: rgba(99,102,241,0.22); color: {c['primary']}; }}"
            )
        else:
            neutral_style = "QPushButton { font-size: 11px; padding: 2px 8px; }"

        # Обновить сумму
        upd_btn = QPushButton("Установить сумму")
        upd_btn.setFixedHeight(scale_px(28))
        upd_btn.setStyleSheet(neutral_style)
        upd_btn.clicked.connect(lambda: on_update_amount(self.goal))
        btn_row.addWidget(upd_btn)

        # Добавить сумму
        add_btn = QPushButton("+ Добавить")
        add_btn.setFixedHeight(scale_px(28))
        if is_new_ui:
            add_btn.setStyleSheet(scale_css(
                f"QPushButton {{ font-size: 11px; padding: 2px 8px; background-color: {c['primary']};"
                " color: #ffffff; font-weight: bold; border-radius: 4px; }"
            ))
        else:
            add_btn.setStyleSheet("QPushButton { font-size: 11px; padding: 2px 8px; }")
        add_btn.clicked.connect(lambda: on_add_amount(self.goal))
        btn_row.addWidget(add_btn)

        # Убавить сумму
        sub_btn = QPushButton("− Убавить")
        sub_btn.setFixedHeight(scale_px(28))
        if is_new_ui:
            sub_btn.setStyleSheet(scale_css(
                "QPushButton { font-size: 11px; padding: 2px 8px; background-color: #818cf8;"
                " color: #ffffff; font-weight: bold; border-radius: 4px; }"
            ))
        else:
            sub_btn.setStyleSheet("QPushButton { font-size: 11px; padding: 2px 8px; }")
        sub_btn.clicked.connect(lambda: on_subtract_amount(self.goal))
        btn_row.addWidget(sub_btn)

        # История
        hist_btn = QPushButton("История")
        hist_btn.setFixedHeight(scale_px(28))
        hist_btn.setStyleSheet(neutral_style)
        hist_btn.clicked.connect(lambda: on_history(self.goal))
        btn_row.addWidget(hist_btn)

        # Редактировать
        edit_btn = QPushButton("Редактировать" if is_new_ui else "✏️ Редактировать")
        edit_btn.setFixedHeight(scale_px(28))
        edit_btn.setStyleSheet(neutral_style)
        edit_btn.clicked.connect(lambda: on_edit(self.goal))
        btn_row.addWidget(edit_btn)

        # Отслеживать / снять
        if self.goal.is_tracked:
            track_btn = QPushButton("Убрать с экрана")
            if is_new_ui:
                track_btn.setStyleSheet(scale_css(
                    f"QPushButton {{ font-size: 11px; padding: 2px 8px; background-color: {c['primary']}; color: #ffffff; font-weight: bold; border-radius: 4px; }}"
                ))
            else:
                track_btn.setStyleSheet(
                    f"QPushButton {{ font-size: 11px; padding: 2px 8px; color: {primary_color}; font-weight: bold; }}"
                )
        else:
            track_btn = QPushButton("Отслеживать")
            track_btn.setStyleSheet(neutral_style)
        track_btn.setFixedHeight(scale_px(28))
        track_btn.clicked.connect(lambda: on_track(self.goal))
        btn_row.addWidget(track_btn)

        btn_row.addStretch()

        # Удалить
        del_btn = QPushButton("Удалить" if is_new_ui else "🗑 Удалить")
        del_btn.setFixedHeight(scale_px(28))
        if is_new_ui:
            del_btn.setStyleSheet(scale_css(
                f"QPushButton {{ font-size: 11px; padding: 2px 8px; background-color: {danger_color}; color: #1f2937; font-weight: bold; border-radius: 4px; }}"
            ))
        else:
            del_btn.setStyleSheet(
                f"QPushButton {{ font-size: 11px; padding: 2px 8px; color: {danger_color}; font-weight: bold; }}"
            )
        del_btn.clicked.connect(lambda: on_delete(self.goal))
        btn_row.addWidget(del_btn)

        outer.addLayout(btn_row)


# ──────────────────────────────────────────────────────────────────────────────
#  Главная страница целей
# ──────────────────────────────────────────────────────────────────────────────

class GoalsPage(QWidget):
    """
    Страница управления финансовыми целями пользователя.
    Отображает список целей с прогресс-барами и кнопками управления.
    """

    def __init__(self, user: User):
        super().__init__()
        self.current_user = user
        self.goals = []
        self._build_ui()

    # ── Инициализация UI ──────────────────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 0, 0, 0)

        secondary = get_text_secondary_color()

        # Заголовок
        is_new_ui = get_ui_mode() == UI_MODE_NEW
        header_row = QHBoxLayout()
        title = QLabel("Мои цели" if is_new_ui else "🎯 Мои цели")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        header_row.addWidget(title)
        header_row.addStretch()

        add_btn = QPushButton("+ Новая цель")
        add_btn.setObjectName("primary_button")
        add_btn.setFixedHeight(36)
        add_btn.clicked.connect(self.on_add_goal)
        header_row.addWidget(add_btn)
        layout.addLayout(header_row)

        subtitle = QLabel("Создайте цели накопления и следите за прогрессом")
        subtitle.setStyleSheet(f"color: {secondary}; font-size: 13px;")
        layout.addWidget(subtitle)

        # Список целей в ScrollArea
        self.goals_layout = QVBoxLayout()
        self.goals_layout.setSpacing(12)

        goals_container = QWidget()
        goals_container.setLayout(self.goals_layout)
        goals_container.setStyleSheet("background: transparent;")

        scroll = QScrollArea()
        scroll.setWidget(goals_container)
        scroll.setWidgetResizable(True)
        c_s = new_colors()
        scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{
                background: {c_s['bg_card']}; width: 8px; border-radius: 4px; margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {c_s['border']}; border-radius: 4px; min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {c_s['primary']}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px; background: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)
        layout.addWidget(scroll)

    # ── Обновление данных ─────────────────────────────────────────────────────

    def refresh(self):
        self._load_goals()

    def _load_goals(self):
        self.goals = GoalService.get_user_goals(self.current_user.id)

        # Очистить
        while self.goals_layout.count():
            item = self.goals_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        secondary = get_text_secondary_color()

        if not self.goals:
            empty = QLabel("У вас нет целей. Создайте первую с помощью кнопки выше!")
            empty.setStyleSheet(f"color: {secondary}; font-size: 14px;")
            self.goals_layout.addWidget(empty)
        else:
            for goal in self.goals:
                card = GoalCard(
                    goal=goal,
                    on_edit=self.on_edit_goal,
                    on_delete=self.on_delete_goal,
                    on_track=self.on_track_goal,
                    on_update_amount=self.on_update_amount,
                    on_add_amount=self.on_add_amount,
                    on_subtract_amount=self.on_subtract_amount,
                    on_history=self.on_show_history,
                )
                self.goals_layout.addWidget(card)

        self.goals_layout.addStretch()

    # ── Обработчики событий ───────────────────────────────────────────────────

    def on_add_goal(self):
        dlg = GoalDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            name = dlg.get_name()
            target = dlg.get_target_amount()
            current = dlg.get_current_amount()
            currency = dlg.get_currency()
            start = dlg.get_start_date()
            end = dlg.get_end_date()
            description = dlg.get_description()

            success, message, goal = GoalService.create_goal(
                user_id=self.current_user.id,
                name=name,
                target_amount=str(target),
                currency=currency,
                start_date=start,
                end_date=end,
                description=description
            )
            if not success:
                QMessageBox.critical(self, "Ошибка", message)
                return

            # Обновить текущую сумму если она > 0
            if current > 0 and goal:
                GoalService.update_current_amount(goal.id, str(current))

            self._load_goals()

    def on_edit_goal(self, goal):
        dlg = GoalDialog(self, goal=goal)
        if dlg.exec_() == QDialog.Accepted:
            success, message, _ = GoalService.update_goal(
                goal_id=goal.id,
                name=dlg.get_name(),
                target_amount=str(dlg.get_target_amount()),
                currency=dlg.get_currency(),
                start_date=dlg.get_start_date(),
                end_date=dlg.get_end_date(),
                description=dlg.get_description()
            )
            if not success:
                QMessageBox.critical(self, "Ошибка", message)
                return

            # Обновить текущую сумму
            GoalService.update_current_amount(goal.id, str(dlg.get_current_amount()))
            self._load_goals()

    def on_delete_goal(self, goal):
        reply = msgbox_question(
            self, "Удаление цели",
            f"Удалить цель «{goal.name}»?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, message = GoalService.delete_goal(goal.id)
            if success:
                self._load_goals()
            else:
                msgbox_critical(self, "Ошибка", message)

    def on_track_goal(self, goal):
        if goal.is_tracked:
            # Убрать с отслеживания
            GoalService.untrack_all(self.current_user.id)
        else:
            # Поставить на отслеживание
            GoalService.set_tracked(self.current_user.id, goal.id)
        self._load_goals()

    def on_update_amount(self, goal):
        new_val, ok = inputdlg_double(
            self,
            "Установить сумму",
            f"Текущая сумма накоплений для «{goal.name}»:",
            value=goal.current_amount,
            min_val=0,
            max_val=999_999_999,
            decimals=2
        )
        if ok:
            success, message = GoalService.update_current_amount(goal.id, str(new_val))
            if success:
                self._load_goals()
            else:
                msgbox_critical(self, "Ошибка", message)

    def on_add_amount(self, goal):
        amount, ok = inputdlg_double(
            self,
            "Добавить к цели",
            f"Сколько добавить к «{goal.name}» ({goal.currency}):",
            value=0.0,
            min_val=0.01,
            max_val=999_999_999,
            decimals=2
        )
        if ok:
            success, message = GoalTransactionService.add_amount(goal.id, str(amount))
            if success:
                self._load_goals()
            else:
                msgbox_critical(self, "Ошибка", message)

    def on_subtract_amount(self, goal):
        amount, ok = inputdlg_double(
            self,
            "Убавить из цели",
            f"Сколько убавить из «{goal.name}» ({goal.currency}):",
            value=0.0,
            min_val=0.01,
            max_val=999_999_999,
            decimals=2
        )
        if ok:
            success, message = GoalTransactionService.subtract_amount(goal.id, str(amount))
            if success:
                self._load_goals()
            else:
                msgbox_critical(self, "Ошибка", message)

    def on_show_history(self, goal):
        dlg = GoalHistoryDialog(goal, self)
        dlg.exec_()
