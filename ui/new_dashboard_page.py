# -*- coding: utf-8 -*-
"""
Новый Dashboard — «New UI» версия.

Карточки кошельков, градиентный блок баланса, активная цель
с цветовыми индикаторами статуса.
"""

from datetime import date as _date

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QInputDialog, QScrollArea, QProgressBar, QSizePolicy,
    QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QBrush, QFontMetrics, QCursor, QLinearGradient
from PyQt5.QtCore import QRect

from models.models import User, Wallet, TransactionType
from services.services import WalletService, TransactionService, GoalService, ExchangeRateService, BalanceHistoryService, BudgetService
from utils.helpers import format_currency
from config import get_main_currency, MULTI_CURRENCIES
from ui.new_styles import new_colors, nc_primary, nc_secondary, nc_danger, nc_text, nc_text2, nc_border, nc_card, msgbox_question, msgbox_critical, msgbox_information, inputdlg_text, inputdlg_item, scale_px, scale_css
from ui.balance_chart_widget import BalanceChartWidget


# ─── String-key chip (chart type, aggregation) ───────────────────────────────

class _StrChip(QWidget):
    """
    Кнопка-чип с произвольным строковым ключом.
    Используется для выбора типа графика и агрегации.
    Нарисована вручную, не зависит от глобального стиля кнопок.
    """
    clicked = pyqtSignal(str)

    def __init__(self, label: str, key: str, parent=None):
        super().__init__(parent)
        self.label = label
        self.key   = key
        self.active  = False
        self._hover  = False
        # Авто-ширина по тексту
        fm = QFontMetrics(QFont())
        self.setFixedSize(max(58, fm.horizontalAdvance(label) + 24), 26)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setAttribute(Qt.WA_Hover)

    def set_active(self, v: bool):
        self.active = v
        self.update()

    def paintEvent(self, event):
        c = new_colors()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        r = 5
        if self.active:
            bg          = QColor(c['primary'])
            text_col    = QColor(c['text_on_primary'])
            border_col  = QColor(c['primary'])
        elif self._hover:
            bg          = QColor(c['bg_card'])
            text_col    = QColor(c['text_primary'])
            border_col  = QColor(c['primary'])
        else:
            bg          = QColor(c['bg_hover'])
            text_col    = QColor(c['text_secondary'])
            border_col  = QColor(c['border'])
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(bg))
        p.drawRoundedRect(0, 0, w, h, r, r)
        p.setPen(QPen(border_col, 1))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(0, 0, w - 1, h - 1, r, r)
        f = QFont(); f.setPointSize(10); f.setBold(self.active)
        p.setFont(f)
        p.setPen(text_col)
        p.drawText(QRect(0, 0, w, h), Qt.AlignCenter, self.label)
        p.end()

    def enterEvent(self, e):  self._hover = True;  self.update()
    def leaveEvent(self, e):  self._hover = False; self.update()
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit(self.key)


# ─── Collapsible Section ─────────────────────────────────────────────────────
class CollapsibleSection(QWidget):
    """
    Виджет с заголовком-кнопкой и сворачиваемым телом.
    Нажатие на заголовок скрывает/показывает тело.
    """

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._collapsed = False
        c = new_colors()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header row
        self._header_btn = QPushButton()
        self._header_btn.setCursor(Qt.PointingHandCursor)
        self._header_btn.setObjectName("collapsible_header")
        self._title = title
        self._header_btn.clicked.connect(self._toggle)
        layout.addWidget(self._header_btn)

        # Body
        self._body = QWidget()
        self._body_layout = QVBoxLayout(self._body)
        self._body_layout.setContentsMargins(0, 6, 0, 0)
        self._body_layout.setSpacing(0)
        layout.addWidget(self._body)

        self._update_header()

    def add_widget(self, widget: QWidget):
        self._body_layout.addWidget(widget)

    def body_layout(self) -> QVBoxLayout:
        return self._body_layout

    def _toggle(self):
        self._collapsed = not self._collapsed
        self._body.setVisible(not self._collapsed)
        self._update_header()

    def _update_header(self):
        c = new_colors()
        arrow = "▶" if self._collapsed else "▼"
        self._header_btn.setText(f"{arrow}  {self._title}")
        self._header_btn.setStyleSheet(f"""
            QPushButton#collapsible_header {{
                background: transparent;
                color: {c['text_primary']};
                border: none;
                text-align: left;
                font-size: 15px;
                font-weight: 700;
                padding: 4px 0px;
            }}
            QPushButton#collapsible_header:hover {{
                color: {c['primary']};
            }}
        """)


# ─── Delete Circle Button ────────────────────────────────────────────────────

class _CrossButton(QWidget):
    """
    Круглая кнопка удаления — рисуется QPainterом.
    Круг + крест нарисованы с толстыми линиями.
    Не наследует QPushButton, чтобы глобальный стиль не перекрывал.
    """
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(30, 30)
        self.setCursor(Qt.PointingHandCursor)
        self._hovered = False

    def paintEvent(self, event):
        c = new_colors()
        danger = QColor(c['danger'])
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        margin = 2
        radius = 6  # rounded corner radius
        # Draw filled rounded rect on hover, border rounded rect otherwise
        if self._hovered:
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(danger))
            p.drawRoundedRect(margin, margin, w - 2 * margin, h - 2 * margin, radius, radius)
            cross_color = QColor("#ffffff")
        else:
            pen_rect = QPen(danger, 2)
            p.setPen(pen_rect)
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(margin, margin, w - 2 * margin, h - 2 * margin, radius, radius)
            cross_color = danger

        # Draw X with thick lines
        inset = 8
        pen_cross = QPen(cross_color, 3.0)
        pen_cross.setCapStyle(Qt.RoundCap)
        p.setPen(pen_cross)
        p.drawLine(inset, inset, w - inset, h - inset)
        p.drawLine(w - inset, inset, inset, h - inset)
        p.end()

    def enterEvent(self, event):
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()


# ─── Wallet Card ──────────────────────────────────────────────────────────────

class NewWalletCard(QPushButton):
    """Карточка кошелька — чистый стиль, без эмодзи."""

    double_clicked = pyqtSignal(Wallet)
    delete_requested = pyqtSignal(Wallet)

    def __init__(self, wallet: Wallet):
        super().__init__()
        self.wallet = wallet

        txns = TransactionService.get_wallet_transactions(wallet.id)
        income  = sum(t.amount for t in txns if t.type == TransactionType.INCOME)
        expense = sum(t.amount for t in txns if t.type == TransactionType.EXPENSE)
        main_curr = get_main_currency()

        c = new_colors()
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(scale_px(76))
        self.setMaximumHeight(scale_px(82))
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 12px;
                padding: 12px 18px;
                text-align: left;
            }}
            QPushButton:hover {{
                border: 1px solid {c['primary']};
                background-color: {c['bg_hover']};
            }}
        """)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(28)

        # Название + валюта
        left = QWidget(); ll = QVBoxLayout(left); ll.setContentsMargins(0,0,0,0); ll.setSpacing(2)
        nm = QLabel(wallet.name)
        nm.setStyleSheet(scale_css(f"font-size: 15px; font-weight: 700; color: {c['text_primary']};"))
        ll.addWidget(nm)
        cur = QLabel(wallet.currency)
        cur.setStyleSheet(scale_css(f"font-size: 12px; color: {c['text_secondary']};"))
        ll.addWidget(cur)
        lay.addWidget(left, 1)

        # Доход
        inc_w = QWidget(); il = QVBoxLayout(inc_w); il.setContentsMargins(0,0,0,0); il.setSpacing(0)
        il.addWidget(self._tiny("Доход", c['text_secondary']))
        il.addWidget(self._val(f"+{format_currency(income, wallet.currency)}", c['secondary']))
        lay.addWidget(inc_w)

        # Расход
        exp_w = QWidget(); el = QVBoxLayout(exp_w); el.setContentsMargins(0,0,0,0); el.setSpacing(0)
        el.addWidget(self._tiny("Расход", c['text_secondary']))
        el.addWidget(self._val(f"-{format_currency(expense, wallet.currency)}", c['danger']))
        lay.addWidget(exp_w)

        # Баланс
        bal_w = QWidget(); bl = QVBoxLayout(bal_w); bl.setContentsMargins(0,0,0,0); bl.setSpacing(0)
        bl.addWidget(self._tiny("Баланс", c['text_secondary']))
        if wallet.balance > 0:
            bal_color = c['secondary']
        elif wallet.balance < 0:
            bal_color = c['danger']
        else:
            bal_color = c['text_primary']
        bl.addWidget(self._val(format_currency(wallet.balance, wallet.currency), bal_color, bold=True))
        lay.addWidget(bal_w, 1)

        # Кнопка удаления
        del_btn = _CrossButton()
        del_btn.setToolTip("Удалить кошелёк")
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self.wallet))
        lay.addWidget(del_btn)

    # helpers
    @staticmethod
    def _tiny(text, color):
        l = QLabel(text); l.setStyleSheet(scale_css(f"font-size: 12px; color: {color};")); return l
    @staticmethod
    def _val(text, color, bold=False):
        w = "bold" if bold else "600"
        l = QLabel(text); l.setStyleSheet(scale_css(f"font-size: 14px; font-weight: {w}; color: {color};")); return l

    def mouseDoubleClickEvent(self, event):
        try:
            if self.wallet and not self.signalsBlocked():
                self.double_clicked.emit(self.wallet)
        except RuntimeError:
            pass


class NewAddWalletCard(QPushButton):
    """Кнопка «+ Создать кошелёк» — dashed border."""
    def __init__(self):
        super().__init__("+ Создать кошелёк")
        c = new_colors()
        self.setMinimumHeight(70)
        self.setMaximumHeight(76)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 2px dashed {c['border']};
                border-radius: 12px;
                font-size: 14px;
                font-weight: 600;
                color: {c['text_secondary']};
            }}
            QPushButton:hover {{
                border-color: {c['primary']};
                color: {c['primary']};
            }}
        """)


# ─── Dashboard ────────────────────────────────────────────────────────────────

class NewDashboardPage(QWidget):
    """Обновлённая страница Dashboard (New UI)."""

    wallet_selected = pyqtSignal(Wallet)

    def __init__(self, user: User):
        super().__init__()
        self.current_user = user
        self.wallets = []
        self._build_ui()

    # ── build ─────────────────────────────────────────────────────────
    def _build_ui(self):
        c = new_colors()

        # Outer layout — just holds the scroll area
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        _page_scroll = QScrollArea()
        _page_scroll.setWidgetResizable(True)
        _page_scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                background: transparent; width: 5px; border-radius: 2px; margin: 0;
            }
            QScrollBar::handle:vertical {
                background: rgba(255,255,255,0.20); border-radius: 2px; min-height: 30px;
            }
            QScrollBar::handle:vertical:hover { background: rgba(255,255,255,0.40); }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px; background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        _content = QWidget()
        _content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(_content)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 0, 0, 0)

        # ── Заголовок ─────────────────────────────────────────────────
        header = QVBoxLayout()
        title = QLabel("Мои финансы")
        tf = QFont(); tf.setPointSize(22); tf.setBold(True)
        title.setFont(tf)
        title.setStyleSheet(f"color: {c['text_primary']};")
        header.addWidget(title)

        sub = QLabel("Обзор кошельков и целей")
        sub.setStyleSheet(f"color: {c['text_secondary']}; font-size: 14px;")
        header.addWidget(sub)
        layout.addLayout(header)

        # ── Баланс-карточка (плоский фон) ────────────────────────
        bal_card = QWidget()
        bal_card.setObjectName("balance_card")
        bal_card.setStyleSheet(f"""
            QWidget#balance_card {{
                background-color: {c['balance_bg']};
                border-radius: 14px;
            }}
            QWidget#balance_card QLabel {{
                background: transparent;
                border: none;
            }}
        """)
        bl = QVBoxLayout(bal_card)
        bl.setContentsMargins(24, 22, 24, 22)
        bl.setSpacing(4)

        bt = QLabel("Общий баланс")
        bt.setStyleSheet("color: rgba(255,255,255,0.80); font-size: 14px; font-weight: 500;")
        bl.addWidget(bt)

        self.total_balance_label = QLabel("0 KZT")
        bfnt = QFont(); bfnt.setPointSize(28); bfnt.setBold(True)
        self.total_balance_label.setFont(bfnt)
        self.total_balance_label.setStyleSheet("color: #FFFFFF;")
        bl.addWidget(self.total_balance_label)

        # Разбивка по валютам
        self._curr_breakdown_label = QLabel("")
        self._curr_breakdown_label.setStyleSheet(
            "color: rgba(255,255,255,0.82); font-size: 14px; font-weight: 500;"
            " background: transparent; border: none;"
        )
        self._curr_breakdown_label.setWordWrap(True)
        self._curr_breakdown_label.hide()
        bl.addWidget(self._curr_breakdown_label)

        layout.addWidget(bal_card)

        # ── График общего баланса (сворачиваемый) ─────────────────────
        self._chart_section = CollapsibleSection("Графики")

        # Состояние выбора
        self._chart_type = 'balance'   # 'balance' | 'expense' | 'income'
        self._agg_mode   = 'daily'     # 'daily'   | 'weekly'  | 'monthly'

        # ── Строка выбора типа графика ──────────────────────────────────
        type_row_w = QWidget(); type_row_w.setStyleSheet("background: transparent;")
        type_row = QHBoxLayout(type_row_w)
        type_row.setContentsMargins(0, 4, 0, 0)
        type_row.setSpacing(6)
        type_lbl = QLabel("Тип:")
        type_lbl.setStyleSheet(f"font-size: 11px; color: {c['text_secondary']}; background: transparent;")
        type_row.addWidget(type_lbl)
        self._type_chips: dict = {}
        for label, key in [("Баланс", "balance"), ("Расходы", "expense"), ("Доходы", "income")]:
            chip = _StrChip(label, key)
            chip.clicked.connect(self._on_chart_type)
            self._type_chips[key] = chip
            type_row.addWidget(chip)
        type_row.addStretch()
        self._chart_section.add_widget(type_row_w)

        # ── Строка агрегации ───────────────────────────────────────────
        self._agg_row_widget = QWidget()
        self._agg_row_widget.setStyleSheet("background: transparent;")
        agg_row = QHBoxLayout(self._agg_row_widget)
        agg_row.setContentsMargins(0, 8, 0, 0)
        agg_row.setSpacing(6)
        agg_lbl = QLabel("Период:")
        agg_lbl.setStyleSheet(f"font-size: 11px; color: {c['text_secondary']}; background: transparent;")
        agg_row.addWidget(agg_lbl)
        self._agg_chips: dict = {}
        for label, key in [("День", "daily"), ("Неделя", "weekly"), ("Месяц", "monthly")]:
            chip = _StrChip(label, key)
            chip.clicked.connect(self._on_agg_change)
            self._agg_chips[key] = chip
            agg_row.addWidget(chip)
        agg_row.addStretch()
        self._chart_section.add_widget(self._agg_row_widget)

        # Начальное состояние чипов
        self._refresh_type_chips()
        self._refresh_agg_chips()
        # Месяц скрыт по умолчанию (доступен только при 365 дн)
        if 'monthly' in self._agg_chips:
            self._agg_chips['monthly'].hide()

        # ── Сам график ──────────────────────────────────────────────────
        self.total_chart = BalanceChartWidget(currency=get_main_currency())
        self.total_chart.setMinimumHeight(230)
        self.total_chart.setMaximumHeight(270)
        self.total_chart.range_changed.connect(self._on_chart_range_changed)
        self._chart_section.add_widget(self.total_chart)
        layout.addWidget(self._chart_section)

        # ── Активная цель (сворачиваемый контейнер) ───────────────────
        self._goal_collapse = CollapsibleSection("Активная цель")
        self.goal_section = QWidget()
        self.goal_section_layout = QVBoxLayout(self.goal_section)
        self.goal_section_layout.setContentsMargins(0, 0, 0, 0)
        self.goal_section_layout.setSpacing(8)
        self._goal_collapse.add_widget(self.goal_section)
        self._goal_collapse.hide()  # скрыть до загрузки
        layout.addWidget(self._goal_collapse)

        # ── Список кошельков (сворачиваемый) ──────────────────────────
        self._wallets_collapse = CollapsibleSection("Кошельки")

        self.wallets_list_layout = QVBoxLayout()
        self.wallets_list_layout.setSpacing(10)

        container = QWidget()
        container.setLayout(self.wallets_list_layout)
        container.setStyleSheet("background: transparent;")
        self._wallets_collapse.add_widget(container)
        layout.addWidget(self._wallets_collapse)
        # Бюджеты (сворачиваемый)
        self._build_budget_section(layout)
        _page_scroll.setWidget(_content)
        outer.addWidget(_page_scroll)

    # ─── Budget section setup (called from _build_ui) ──────────────────────
    def _build_budget_section(self, layout: QVBoxLayout):
        """Build the collapsible budget section and append to layout."""
        from PyQt5.QtWidgets import QProgressBar
        c = new_colors()

        self._budget_collapse = CollapsibleSection("Бюджеты текущего месяца")

        # Container inside the collapsible
        self._budget_container = QWidget()
        self._budget_container.setStyleSheet("background: transparent;")
        self._budget_inner_layout = QVBoxLayout(self._budget_container)
        self._budget_inner_layout.setContentsMargins(0, 4, 0, 0)
        self._budget_inner_layout.setSpacing(8)
        self._budget_collapse.add_widget(self._budget_container)

        # Button to open CategoryBudgetDialog
        manage_btn = QPushButton("Управление категориями и бюджетами")
        manage_btn.setMinimumHeight(36)
        manage_btn.setCursor(Qt.PointingHandCursor)
        manage_btn.clicked.connect(self._on_manage_budgets)
        self._budget_collapse.add_widget(manage_btn)

        layout.addWidget(self._budget_collapse)

    # ── refresh ───────────────────────────────────────────────────────
    def refresh(self):
        self._refresh_wallets()
        self._refresh_goal()
        self._refresh_total_chart()
        self._refresh_budgets()

    def _refresh_budgets(self):
        """Refresh the budget progress bars for the current month."""
        from PyQt5.QtWidgets import QProgressBar
        import datetime as _dt

        # Clear existing budget rows
        while self._budget_inner_layout.count():
            item = self._budget_inner_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        today = _dt.date.today()
        c = new_colors()
        items = BudgetService.get_budgets_with_progress(
            self.current_user.id, today.year, today.month
        )

        if not items:
            lbl = QLabel("Бюджеты не установлены. Нажмите «Управление» чтобы добавить.")
            lbl.setStyleSheet(f"color: {c['text_secondary']}; font-size: 13px;")
            self._budget_inner_layout.addWidget(lbl)
            return

        for info in items:
            row_w = QWidget()
            row_w.setStyleSheet(f"""
                QWidget {{
                    background: {c['bg_card']};
                    border: 1px solid {c['border']};
                    border-radius: 8px;
                }}
                QLabel {{ border: none; background: transparent; }}
            """)
            row_l = QHBoxLayout(row_w)
            row_l.setContentsMargins(12, 8, 12, 8)
            row_l.setSpacing(10)

            # Category label
            cat = info["category"]
            cat_color = cat.color if cat else c["primary"]
            cat_name = cat.name if cat else "—"
            cat_lbl = QLabel(cat_name)
            cat_lbl.setFixedWidth(120)
            cat_lbl.setStyleSheet(f"color: {cat_color}; font-weight: 600; font-size: 13px;")
            row_l.addWidget(cat_lbl)

            # Progress bar
            bar = QProgressBar()
            pct_clamped = min(int(info["pct"]), 100)
            bar.setValue(pct_clamped)
            bar.setFormat(f"{info['pct']:.1f}%")
            bar.setTextVisible(True)
            bar.setMinimumHeight(22)
            if info["over_limit"]:
                bar_color = "#ef4444"
            elif info["at_warning"]:
                bar_color = "#f59e0b"
            else:
                bar_color = "#10b981"
            bar.setStyleSheet(f"""
                QProgressBar {{
                    border: 1px solid {c['border']};
                    border-radius: 5px;
                    background: {c['bg_hover']};
                    color: {c['text_primary']};
                    font-size: 11px;
                }}
                QProgressBar::chunk {{
                    background: {bar_color};
                    border-radius: 4px;
                }}
            """)
            row_l.addWidget(bar, 1)

            # Amount label
            amt_lbl = QLabel(f"{info['spent']:,.0f} / {info['limit']:,.0f}")
            amt_lbl.setStyleSheet(f"color: {c['text_secondary']}; font-size: 12px; min-width: 130px;")
            row_l.addWidget(amt_lbl)

            self._budget_inner_layout.addWidget(row_w)

    def _on_manage_budgets(self):
        from ui.categories_budget_dialog import CategoryBudgetDialog
        dlg = CategoryBudgetDialog(self.current_user, self)
        dlg.exec_()
        self._refresh_budgets()

    def _refresh_total_chart(self):
        self.total_chart.currency = get_main_currency()
        self._update_chart_loader()

    # ── Chart type / aggregation logic ───────────────────────────────

    def _refresh_type_chips(self):
        for key, chip in self._type_chips.items():
            chip.set_active(key == self._chart_type)

    def _refresh_agg_chips(self):
        for key, chip in self._agg_chips.items():
            chip.set_active(key == self._agg_mode)

    def _on_chart_type(self, key: str):
        if key == self._chart_type:
            return
        self._chart_type = key
        self._refresh_type_chips()
        self._on_chart_range_changed(self.total_chart.get_range_days())

    def _on_agg_change(self, key: str):
        if key == self._agg_mode:
            return
        self._agg_mode = key
        self._refresh_agg_chips()
        self._update_chart_loader()

    def _on_chart_range_changed(self, days: int):
        """Вызывается при смене диапазона в BalanceChartWidget."""
        # Месяц — только для 365 дней
        monthly_chip = self._agg_chips.get('monthly')
        if monthly_chip:
            monthly_chip.setVisible(days == 365)
        if self._agg_mode == 'monthly' and days != 365:
            self._agg_mode = 'daily'
            self._refresh_agg_chips()
        # Агрегация показывается начиная с 28 дней
        self._agg_row_widget.setVisible(days >= 28)
        self._update_chart_loader()

    def _update_chart_loader(self):
        uid  = self.current_user.id
        curr = get_main_currency()
        ct   = self._chart_type
        agg  = self._agg_mode
        if ct == 'balance':
            self.total_chart.set_loader(
                lambda days, _uid=uid, _curr=curr, _agg=agg:
                    BalanceHistoryService.get_total_balance_history_agg(_uid, days, _curr, _agg)
            )
        else:
            flow = 'expense' if ct == 'expense' else 'income'
            self.total_chart.set_loader(
                lambda days, _uid=uid, _curr=curr, _flow=flow, _agg=agg:
                    BalanceHistoryService.get_total_flow_history(_uid, days, _flow, _agg, _curr)
            )

    def _refresh_goal(self):
        while self.goal_section_layout.count():
            item = self.goal_section_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        goal = GoalService.get_tracked_goal(self.current_user.id)
        if not goal:
            self._goal_collapse.hide()
            return
        self._goal_collapse.show()

        c = new_colors()
        # Определить статус
        pct = min(goal.current_amount / goal.target_amount * 100, 100) if goal.target_amount > 0 else 0
        today = _date.today()
        end_d = goal.end_date if isinstance(goal.end_date, _date) else goal.end_date.date()

        if pct >= 100:
            status_color = c['secondary']   # Зелёный — выполнено
            status_text  = "Выполнена"
        elif end_d < today:
            status_color = c['danger']      # Красный — просрочена
            status_text  = "Просрочена"
        else:
            status_color = c['primary']     # Индиго — в процессе
            status_text  = "В процессе"

        card = QWidget()
        card.setStyleSheet(f"""
            QWidget#new_goal_card {{
                background-color: {c['bg_card']};
                border: 1px solid {status_color};
                border-left: 4px solid {status_color};
                border-radius: 12px;
            }}
            QWidget#new_goal_card QWidget,
            QWidget#new_goal_card QLabel {{
                border: none; background: transparent;
            }}
        """)
        card.setObjectName("new_goal_card")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(18, 14, 18, 14)
        cl.setSpacing(8)

        # Верх: название + бейдж статуса
        top = QHBoxLayout()
        nlbl = QLabel(goal.name)
        nf = QFont(); nf.setPointSize(14); nf.setBold(True)
        nlbl.setFont(nf)
        nlbl.setStyleSheet(f"color: {c['text_primary']};")
        top.addWidget(nlbl)
        top.addStretch()
        badge = QLabel(status_text)
        badge.setStyleSheet(f"""
            color: {status_color};
            font-size: 12px;
            font-weight: 700;
            padding: 3px 10px;
            border: 1px solid {status_color};
            border-radius: 10px;
        """)
        top.addWidget(badge)
        tw = QWidget(); tw.setLayout(top)
        cl.addWidget(tw)

        # Даты
        dates_lbl = QLabel(
            f"{goal.start_date.strftime('%d.%m.%Y')} — {goal.end_date.strftime('%d.%m.%Y')}"
        )
        dates_lbl.setStyleSheet(f"font-size: 12px; color: {c['text_secondary']};")
        cl.addWidget(dates_lbl)

        # Сумма
        amt = QLabel(
            f"{format_currency(goal.current_amount, goal.currency)}"
            f"  из  {format_currency(goal.target_amount, goal.currency)}"
            f"    ({pct:.1f} %)"
        )
        amt.setStyleSheet(f"font-size: 13px; color: {c['text_secondary']};")
        cl.addWidget(amt)

        # Прогресс-бар
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(int(pct))
        bar.setTextVisible(False)
        bar.setFixedHeight(10)
        bar.setStyleSheet(f"""
            QProgressBar {{ background-color: {c['border']}; border-radius: 5px; border: none; }}
            QProgressBar::chunk {{ background-color: {status_color}; border-radius: 5px; }}
        """)
        cl.addWidget(bar)

        self.goal_section_layout.addWidget(card)

    def _refresh_wallets(self):
        c = new_colors()
        self.wallets = WalletService.get_user_wallets(self.current_user.id)

        main_curr = get_main_currency()
        info = WalletService.get_balance_multi_currency(self.current_user.id, main_curr)
        self.total_balance_label.setText(format_currency(info["total"], main_curr))

        # Разбивка по валютам
        bd = info["breakdown"]
        show_bd = sorted(bd.keys())
        if len(show_bd) > 1 or (len(show_bd) == 1 and show_bd[0] != main_curr):
            parts = []
            for cur in show_bd:
                fmt = f"{bd[cur]:,.0f}".replace(",", " ")
                parts.append(f"{cur}  {fmt}")
            self._curr_breakdown_label.setText("     ·     ".join(parts))
            self._curr_breakdown_label.show()
        else:
            self._curr_breakdown_label.hide()

        # clear
        while self.wallets_list_layout.count():
            ch = self.wallets_list_layout.takeAt(0)
            if ch.widget():
                w = ch.widget()
                try:
                    w.blockSignals(True)
                    if hasattr(w, 'double_clicked'):
                        w.double_clicked.disconnect()
                except:
                    pass
                w.deleteLater()

        if not self.wallets:
            el = QLabel("У вас пока нет кошельков — создайте первый!")
            el.setStyleSheet(f"color: {c['text_secondary']}; font-size: 15px;")
            self.wallets_list_layout.addWidget(el)
        else:
            for wallet in self.wallets:
                wc = NewWalletCard(wallet)
                wc.double_clicked.connect(self._on_wallet)
                wc.delete_requested.connect(self._on_delete_wallet)
                self.wallets_list_layout.addWidget(wc)

        add = NewAddWalletCard()
        add.clicked.connect(self._on_add_wallet)
        self.wallets_list_layout.addWidget(add)
        self.wallets_list_layout.addStretch()

    # ── actions ───────────────────────────────────────────────────────
    def _on_wallet(self, wallet: Wallet):
        self.wallet_selected.emit(wallet)

    def _on_delete_wallet(self, wallet: Wallet):
        reply = msgbox_question(
            self, "Удалить кошелёк",
            f"Удалить кошелёк «{wallet.name}»?\nВсе транзакции будут удалены без возможности восстановления.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, msg = WalletService.delete_wallet(wallet.id)
            if success:
                self._refresh_wallets()
            else:
                msgbox_critical(self, "Ошибка", msg)

    def _on_add_wallet(self):
        name, ok = inputdlg_text(self, "Новый кошелёк", "Название кошелька:")
        if not ok or not name:
            return
        currency, ok2 = inputdlg_item(
            self, "Валюта", "Выберите валюту:", MULTI_CURRENCIES, 0, False
        )
        if not ok2:
            return
        success, msg, wallet = WalletService.create_wallet(self.current_user.id, name, currency)
        if success:
            msgbox_information(self, "Готово", msg)
            self._refresh_wallets()
        else:
            msgbox_critical(self, "Ошибка", msg)
