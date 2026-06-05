# -*- coding: utf-8 -*-
"""
Страница «Долги» — аналог Dashboard для долговых кейсов

Отображает:
- Общая сумма (дал в долг − взял в долг)
- Маленьким текстом: «Мне должны» и «Я должен» раздельно
- Список кейсов-карточек (аналог WalletCard)
- Кнопка создания нового кейса
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QInputDialog, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from models.models import User, DebtType
from services.services import DebtService, DebtTransactionService
from utils.helpers import format_currency
from config import MULTI_CURRENCIES, get_main_currency, get_ui_mode, UI_MODE_NEW
from ui.styles import (
    get_income_color, get_expense_color, get_text_color,
    get_text_secondary_color
)
from ui.new_styles import new_colors, msgbox_question, msgbox_critical, msgbox_information, inputdlg_text, inputdlg_item, scale_px, scale_css
from ui.new_dashboard_page import _CrossButton


# ──────────────────────────────────────────────────────────────────────────────
#  Карточка кейса долга
# ──────────────────────────────────────────────────────────────────────────────

class DebtCard(QPushButton):
    """Карточка одного кейса долга"""

    double_clicked = pyqtSignal(object)
    delete_requested = pyqtSignal(object)

    def __init__(self, debt):
        super().__init__()
        self.debt = debt

        # Посчитать дал / взял
        txs = DebtTransactionService.get_debt_transactions(debt.id)
        self.gave = sum(t.amount for t in txs if t.type == DebtType.GAVE)
        self.took = sum(t.amount for t in txs if t.type == DebtType.TOOK)

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
        expense_color = get_expense_color()

        self.setMinimumHeight(70)
        self.setMaximumHeight(75)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {card_bg};
                border: 1px solid {card_border};
                border-radius: 6px;
                padding: 10px 15px;
                text-align: left;
                color: {text_color};
            }}
            QPushButton:hover {{
                background-color: {card_hover_bg};
                border: 1px solid {card_border};
            }}
            QPushButton:pressed {{
                background-color: {card_hover_bg};
            }}
        """)
        self.setCursor(Qt.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(30)

        # Имя + валюта
        left = QWidget()
        ll = QVBoxLayout(left); ll.setContentsMargins(0,0,0,0); ll.setSpacing(0)
        name_lbl = QLabel(debt.name)
        name_lbl.setStyleSheet(scale_css(f"font-size: 14px; font-weight: bold; color: {name_color};"))
        ll.addWidget(name_lbl)
        cur_lbl = QLabel(debt.currency)
        cur_lbl.setStyleSheet(scale_css(f"font-size: 11px; color: {secondary};"))
        ll.addWidget(cur_lbl)
        layout.addWidget(left, 1)

        # Дал в долг
        gw = QWidget()
        gl = QVBoxLayout(gw); gl.setContentsMargins(0,0,0,0); gl.setSpacing(0)
        gt = QLabel("Дал в долг")
        gt.setStyleSheet(scale_css(f"font-size: 10px; color: {secondary};"))
        gl.addWidget(gt)
        gv = QLabel(f"+{format_currency(self.gave, debt.currency)}")
        gv.setStyleSheet(scale_css(f"font-size: 12px; font-weight: bold; color: {income_color};"))
        gl.addWidget(gv)
        layout.addWidget(gw, 0)

        # Взял в долг
        tw = QWidget()
        tl = QVBoxLayout(tw); tl.setContentsMargins(0,0,0,0); tl.setSpacing(0)
        tt = QLabel("Взял в долг")
        tt.setStyleSheet(scale_css(f"font-size: 10px; color: {secondary};"))
        tl.addWidget(tt)
        tv = QLabel(f"-{format_currency(self.took, debt.currency)}")
        tv.setStyleSheet(scale_css(f"font-size: 12px; font-weight: bold; color: {expense_color};"))
        tl.addWidget(tv)
        layout.addWidget(tw, 0)

        # Баланс
        rw = QWidget()
        rl = QVBoxLayout(rw); rl.setContentsMargins(0,0,0,0); rl.setSpacing(0)
        bt = QLabel("Баланс")
        bt.setStyleSheet(scale_css(f"font-size: 10px; color: {secondary};"))
        rl.addWidget(bt)
        bv = QLabel(format_currency(debt.balance, debt.currency))
        bfs = scale_css("font-size: 14px; font-weight: bold;")
        if debt.balance > 0:
            bv.setStyleSheet(f"{bfs} color: {income_color};")
        elif debt.balance < 0:
            bv.setStyleSheet(f"{bfs} color: {expense_color};")
        else:
            bv.setStyleSheet(f"{bfs} color: {text_color};")
        rl.addWidget(bv)
        layout.addWidget(rw, 1)

        # Кнопка удаления
        del_btn = _CrossButton()
        del_btn.setToolTip("Удалить кейс")
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self.debt))
        layout.addWidget(del_btn)

    def mouseDoubleClickEvent(self, event):
        try:
            if self.debt and not self.signalsBlocked():
                self.double_clicked.emit(self.debt)
        except RuntimeError:
            pass


class AddDebtCard(QPushButton):
    """Кнопка создания нового кейса"""

    def __init__(self):
        super().__init__()
        self.setText("+ Создать новый кейс долга")
        self.setMinimumHeight(scale_px(70))
        self.setMaximumHeight(scale_px(75))
        is_new_ui = get_ui_mode() == UI_MODE_NEW
        if is_new_ui:
            c = new_colors()
            self.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: 2px dashed {c['border']};
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: bold;
                    color: {c['text_secondary']};
                    padding: 10px;
                }}
                QPushButton:hover {{
                    border-color: {c['primary']};
                    color: {c['primary']};
                }}
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #f3f4f6;
                    border: 2px dashed #d1d5db;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: bold;
                    color: #6b7280;
                    padding: 10px;
                }
                QPushButton:hover {
                    background-color: #e5e7eb;
                    border: 2px dashed #9ca3af;
                    color: #1f2937;
                }
            """)


# ──────────────────────────────────────────────────────────────────────────────
#  Главная страница долгов
# ──────────────────────────────────────────────────────────────────────────────

class DebtsPage(QWidget):
    """Страница со списком кейсов долгов и сводкой"""

    debt_selected = pyqtSignal(object)  # при двойном клике

    def __init__(self, user: User):
        super().__init__()
        self.current_user = user
        self.debts = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 0, 0, 0)

        secondary = get_text_secondary_color()

        # Заголовок
        is_new = get_ui_mode() == UI_MODE_NEW
        header = QVBoxLayout()
        title = QLabel("Долги" if is_new else "Долги 🤝")
        tf = QFont(); tf.setPointSize(20); tf.setBold(True)
        title.setFont(tf)
        header.addWidget(title)

        sub = QLabel("Отслеживайте кто кому должен")
        sub.setStyleSheet(f"color: {secondary}; font-size: 14px;")
        header.addWidget(sub)
        layout.addLayout(header)

        # Сводка
        is_new = get_ui_mode() == UI_MODE_NEW
        summary_widget = QWidget()
        summary_widget.setAttribute(Qt.WA_StyledBackground, True)
        summary_widget.setObjectName("debt_summary")
        summary_widget.setStyleSheet("""
            QWidget#debt_summary {
                background-color: #1e293b;
                border-radius: 10px;
            }
        """)
        outer = QVBoxLayout(summary_widget)
        outer.setContentsMargins(16, 10, 16, 10)
        outer.setSpacing(6)

        # ── Центр: чистый итог ──
        top_col = QVBoxLayout()
        top_col.setSpacing(1)
        self.net_label = QLabel("0 KZT")
        nf = QFont(); nf.setPointSize(scale_px(22)); nf.setBold(True)
        self.net_label.setFont(nf)
        self.net_label.setStyleSheet("color: #ffffff;")
        self.net_label.setAlignment(Qt.AlignHCenter)
        top_col.addWidget(self.net_label)
        self.net_sub = QLabel("Чистый итог по долгам")
        self.net_sub.setStyleSheet("color: rgba(255,255,255,0.65); font-size: 12px;")
        self.net_sub.setAlignment(Qt.AlignHCenter)
        top_col.addWidget(self.net_sub)
        outer.addLayout(top_col)

        # Тонкая разделительная линия
        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: rgba(255,255,255,0.2);")
        outer.addWidget(sep)

        # ── Две колонки: мне должны / я должен ──
        cols_row = QHBoxLayout()
        cols_row.setSpacing(0)

        # Левая: Мне должны
        left_col = QVBoxLayout()
        left_col.setSpacing(4)
        gave_hdr = QLabel("МНЕ ДОЛЖНЫ")
        gave_hdr.setStyleSheet("color: rgba(255,255,255,0.65); font-size: 11px; font-weight: 600; letter-spacing: 1px;")
        left_col.addWidget(gave_hdr)
        self.gave_total_label = QLabel("0 KZT")
        gf = QFont(); gf.setPointSize(scale_px(14)); gf.setBold(True)
        self.gave_total_label.setFont(gf)
        self.gave_total_label.setStyleSheet("color: #4ade80;")
        left_col.addWidget(self.gave_total_label)
        # Контейнер для чипов валют
        self._gave_chips = QWidget()
        self._gave_chips.setStyleSheet("background: transparent;")
        self._gave_chips_layout = QVBoxLayout(self._gave_chips)
        self._gave_chips_layout.setContentsMargins(0, 2, 0, 0)
        self._gave_chips_layout.setSpacing(3)
        left_col.addWidget(self._gave_chips)
        left_col.addStretch()

        # Вертикальная разделительная линия
        vsep = QWidget()
        vsep.setFixedWidth(1)
        vsep.setStyleSheet("background: rgba(255,255,255,0.2);")

        # Правая: Я должен
        right_col = QVBoxLayout()
        right_col.setSpacing(4)
        took_hdr = QLabel("Я ДОЛЖЕН")
        took_hdr.setStyleSheet("color: rgba(255,255,255,0.65); font-size: 11px; font-weight: 600; letter-spacing: 1px;")
        right_col.addWidget(took_hdr)
        self.took_total_label = QLabel("0 KZT")
        tf2 = QFont(); tf2.setPointSize(scale_px(14)); tf2.setBold(True)
        self.took_total_label.setFont(tf2)
        self.took_total_label.setStyleSheet("color: #f87171;")
        right_col.addWidget(self.took_total_label)
        self._took_chips = QWidget()
        self._took_chips.setStyleSheet("background: transparent;")
        self._took_chips_layout = QVBoxLayout(self._took_chips)
        self._took_chips_layout.setContentsMargins(0, 2, 0, 0)
        self._took_chips_layout.setSpacing(3)
        right_col.addWidget(self._took_chips)
        right_col.addStretch()

        cols_row.addLayout(left_col, 1)
        cols_row.addWidget(vsep)
        cols_row.addSpacing(12)
        cols_row.addLayout(right_col, 1)
        outer.addLayout(cols_row)

        self._summary_widget = summary_widget
        layout.addWidget(summary_widget)

        # Список кейсов
        list_title = QLabel("Мои кейсы")
        ltf = QFont(); ltf.setPointSize(14); ltf.setBold(True)
        list_title.setFont(ltf)
        layout.addWidget(list_title)

        self.list_layout = QVBoxLayout()
        self.list_layout.setSpacing(10)

        container = QWidget()
        container.setLayout(self.list_layout)
        container.setStyleSheet("background: transparent;")

        scroll = QScrollArea()
        scroll.setWidget(container)
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

    # ──────────────────────────────────────────────────────────────────────────

    def refresh(self):
        self._load()

    def _load(self):
        self.debts = DebtService.get_user_debts(self.current_user.id)

        main_curr = get_main_currency()
        summary = DebtService.get_summary_multi_currency(self.current_user.id, main_curr)

        self._update_summary(summary, main_curr)

        # Очистить
        while self.list_layout.count():
            child = self.list_layout.takeAt(0)
            if child.widget():
                w = child.widget()
                try:
                    w.blockSignals(True)
                    if hasattr(w, 'double_clicked'):
                        w.double_clicked.disconnect()
                except:
                    pass
                w.deleteLater()

        secondary = get_text_secondary_color()

        if not self.debts:
            lbl = QLabel("Нет кейсов. Создайте первый!")
            lbl.setStyleSheet(f"color: {secondary}; font-size: 14px;")
            self.list_layout.addWidget(lbl)
        else:
            for debt in self.debts:
                card = DebtCard(debt)
                card.double_clicked.connect(self._on_card_double_click)
                card.delete_requested.connect(self._on_delete_debt)
                self.list_layout.addWidget(card)

        add_btn = AddDebtCard()
        add_btn.clicked.connect(self._on_add)
        self.list_layout.addWidget(add_btn)

        self.list_layout.addStretch()

    # ──────────────────────────────────────────────────────────────────────────

    def _update_summary(self, summary: dict, main_curr: str):
        """Обновить сводный блок «Итого по долгам»."""
        bal = summary["balance"]
        gave = summary["gave"]
        took = summary["took"]
        breakdown = summary.get("breakdown", {})

        # Чистый итог — цвет в зависимости от знака
        sign = "+" if bal > 0 else ""
        self.net_label.setText(f"{sign}{format_currency(bal, main_curr)}")
        self.net_label.setStyleSheet("color: #ffffff;")

        self.gave_total_label.setText(format_currency(gave, main_curr))
        self.took_total_label.setText(format_currency(took, main_curr))

        # Пересоздать чипы валют для «Мне должны»
        while self._gave_chips_layout.count():
            item = self._gave_chips_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Пересоздать чипы валют для «Я должен»
        while self._took_chips_layout.count():
            item = self._took_chips_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        chip_style = (
            "background: rgba(255,255,255,0.12); border-radius: 4px;"
            " padding: 2px 6px; font-size: 14px; color: rgba(255,255,255,0.9);"
        )

        for curr in sorted(breakdown.keys()):
            g = breakdown[curr]["gave"]
            t = breakdown[curr]["took"]
            if g > 0:
                chip = QLabel(f"{curr}  {g:,.0f}".replace(",", " "))
                chip.setStyleSheet(chip_style)
                chip.setAttribute(Qt.WA_StyledBackground, True)
                self._gave_chips_layout.addWidget(chip)
            if t > 0:
                chip2 = QLabel(f"{curr}  {t:,.0f}".replace(",", " "))
                chip2.setStyleSheet(chip_style)
                chip2.setAttribute(Qt.WA_StyledBackground, True)
                self._took_chips_layout.addWidget(chip2)

    # ──────────────────────────────────────────────────────────────────────────

    def _on_card_double_click(self, debt):
        self.debt_selected.emit(debt)

    def _on_delete_debt(self, debt):
        reply = msgbox_question(
            self, "Удалить кейс",
            f"Удалить кейс «{debt.name}»?\nВсе транзакции будут удалены без возможности восстановления.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, msg = DebtService.delete_debt(debt.id)
            if success:
                self._load()
            else:
                msgbox_critical(self, "Ошибка", msg)

    def _on_add(self):
        name, ok = inputdlg_text(self, "Новый кейс", "Имя человека / название:")
        if ok and name:
            currency, ok2 = inputdlg_item(
                self, "Валюта кейса", "Выберите валюту:",
                MULTI_CURRENCIES, 0, False
            )
            if not ok2:
                return
            success, msg, _ = DebtService.create_debt(self.current_user.id, name, currency)
            if success:
                msgbox_information(self, "Успех", msg)
                self._load()
            else:
                msgbox_critical(self, "Ошибка", msg)
