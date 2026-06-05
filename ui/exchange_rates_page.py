# -*- coding: utf-8 -*-
"""
Страница курсов валют

Отображает:
- Текущие курсы валют
- Функция добавления новых курсов
- Функция удаления курсов
- Обновление курсов
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QMessageBox, QScrollArea, QDialog, QInputDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QFont, QColor

from models.models import User
from utils.helpers import format_currency
from services.services import ExchangeRateService
from ui.toast_notification import show_toast
from ui.styles import (
    get_text_color, get_text_secondary_color, get_primary_color
)
from ui.new_styles import new_colors, get_new_stylesheet, apply_dark_title_bar, msgbox_warning, msgbox_question, inputdlg_item, scale_px, scale_css
from config import get_ui_mode, UI_MODE_NEW


class ExchangeRateCard(QWidget):
    """Карточка курса валют — современный стиль"""

    def __init__(self, from_currency: str, to_currency: str, rate: float):
        super().__init__()
        self.from_currency = from_currency
        self.to_currency = to_currency
        self.rate = rate

        is_new_ui = get_ui_mode() == UI_MODE_NEW

        self.setMinimumHeight(scale_px(70))
        self.setMaximumHeight(scale_px(76))
        self.setAttribute(Qt.WA_StyledBackground, True)

        if is_new_ui:
            c = new_colors()
            self.setObjectName("rate_card")
            self.setStyleSheet(f"""
                QWidget#rate_card {{
                    background-color: {c['bg_card']};
                    border: 1px solid {c['border']};
                    border-radius: 12px;
                }}
                QWidget#rate_card QLabel {{
                    background: transparent;
                    border: none;
                }}
            """)

            layout = QHBoxLayout(self)
            layout.setContentsMargins(18, 12, 18, 12)
            layout.setSpacing(0)

            # Левый блок: FROM → TO
            from_lbl = QLabel(from_currency)
            from_lbl.setStyleSheet(scale_css(
                f"font-size: 20px; font-weight: 800; color: {c['text_primary']};"
            ))
            layout.addWidget(from_lbl)

            arrow_lbl = QLabel(" → ")
            arrow_lbl.setStyleSheet(scale_css(
                f"font-size: 22px; font-weight: 700; color: {c['primary']}; padding: 0 8px;"
            ))
            layout.addWidget(arrow_lbl)

            to_lbl = QLabel(to_currency)
            to_lbl.setStyleSheet(scale_css(
                f"font-size: 20px; font-weight: 800; color: {c['text_primary']};"
            ))
            layout.addWidget(to_lbl)

            layout.addStretch()

            # Правый блок: курс + подпись
            right = QWidget()
            right.setStyleSheet("background: transparent; border: none;")
            rl = QVBoxLayout(right)
            rl.setContentsMargins(0, 0, 0, 0)
            rl.setSpacing(2)

            rate_val = QLabel(f"{rate:.2f} {to_currency}")
            rf = QFont()
            rf.setPointSize(scale_px(14))
            rf.setBold(True)
            rate_val.setFont(rf)
            rate_val.setStyleSheet(f"color: {c['primary']};")
            rate_val.setAlignment(Qt.AlignRight)
            rl.addWidget(rate_val)

            rate_sub = QLabel(f"за 1 {from_currency}")
            rate_sub.setStyleSheet(scale_css(
                f"font-size: 11px; color: {c['text_secondary']};"
            ))
            rate_sub.setAlignment(Qt.AlignRight)
            rl.addWidget(rate_sub)

            layout.addWidget(right)
        else:
            # Old UI
            primary_color = get_primary_color()
            secondary_color = get_text_secondary_color()
            self.setStyleSheet(f"""
                QWidget {{
                    background-color: #ffffff;
                    border: 1px solid #e5e7eb;
                    border-radius: 6px;
                }}
                QWidget QLabel {{
                    background: transparent;
                    border: none;
                }}
            """)
            layout = QHBoxLayout(self)
            layout.setContentsMargins(10, 10, 10, 10)
            layout.setSpacing(20)

            pair_lbl = QLabel(f"{from_currency} → {to_currency}")
            pair_lbl.setStyleSheet("font-size: 13px; font-weight: bold;")
            layout.addWidget(pair_lbl, 1)

            rate_lbl = QLabel(f"1 {from_currency} = {rate:.4f} {to_currency}")
            rf = QFont()
            rf.setPointSize(12)
            rf.setBold(True)
            rate_lbl.setFont(rf)
            rate_lbl.setStyleSheet(f"color: {primary_color};")
            layout.addWidget(rate_lbl, 1)


class ExchangeRatesPage(QWidget):
    """
    Страница курсов валют
    Отображает текущие курсы и позволяет управлять ими
    
    Сигналы:
        None
    """
    
    def __init__(self, user: User):
        super().__init__()
        self.current_user = user
        self.exchange_rates = {}  # {(from, to): rate}
        self.loading = False
        # Валюты, которые поддерживает forex-python + KZT (основная валюта)
        self.currency_codes = ['KZT', 'USD', 'EUR', 'GBP', 'JPY', 'RUB', 'CNY', 'CHF', 'CAD', 'AUD', 'INR']
        
        self.init_ui()
        self.load_default_rates()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Получить цвета
        secondary_color = get_text_secondary_color()
        
        # === Заголовок ===
        header_layout = QVBoxLayout()
        
        greeting = QLabel(f"Курсы валют")
        greeting_font = QFont()
        greeting_font.setPointSize(20)
        greeting_font.setBold(True)
        greeting.setFont(greeting_font)
        header_layout.addWidget(greeting)
        
        subtitle = QLabel("Основная валюта: KZT")
        subtitle.setStyleSheet(f"color: {secondary_color}; font-size: 14px;")
        header_layout.addWidget(subtitle)

        self.last_updated_label = QLabel("")
        self.last_updated_label.setStyleSheet(f"color: {secondary_color}; font-size: 12px;")
        header_layout.addWidget(self.last_updated_label)
        
        layout.addLayout(header_layout)
        
        # === Список курсов ===
        rates_title = QLabel("Текущие курсы")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        rates_title.setFont(title_font)
        layout.addWidget(rates_title)
        
        # === Карточки курсов (VBoxLayout) ===
        self.rates_list_layout = QVBoxLayout()
        self.rates_list_layout.setSpacing(10)
        self.rates_list_layout.addStretch()  # Растяжимое пространство в конце
        
        rates_container = QWidget()
        rates_container.setLayout(self.rates_list_layout)
        rates_container.setStyleSheet("background: transparent;")
        
        scroll = QScrollArea()
        scroll.setWidget(rates_container)
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
        
        # === Кнопки управления ===
        buttons_layout = QHBoxLayout()
        
        is_new = get_ui_mode() == UI_MODE_NEW
        btn_refresh = QPushButton("Обновить курсы" if is_new else "🔄 Обновить курсы")
        btn_refresh.clicked.connect(self.on_refresh_rates)
        buttons_layout.addWidget(btn_refresh)
        
        btn_add = QPushButton("+ Добавить курс")
        btn_add.clicked.connect(self.on_add_rate)
        buttons_layout.addWidget(btn_add)
        
        btn_manage = QPushButton("Управление курсами")
        btn_manage.clicked.connect(self.on_manage_rates)
        buttons_layout.addWidget(btn_manage)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
    
    def load_default_rates(self):
        """Загрузить курсы пользователя из БД"""
        try:
            # Получить все курсы из БД
            self.exchange_rates = ExchangeRateService.get_user_rates(self.current_user.id)
            self.refresh_display()
            
            if not self.exchange_rates:
                show_toast(self, "Дефолтные курсы не найдены, инициализирую...", 2000)
                ExchangeRateService.init_default_rates(self.current_user.id)
                self.exchange_rates = ExchangeRateService.get_user_rates(self.current_user.id)
                self.refresh_display()
        except Exception as e:
            show_toast(self, f"Ошибка загрузки курсов: {str(e)}", 3000)
    
    def refresh_display(self):
        """Обновить отображение курсов"""
        # Получить цвета
        secondary_color = get_text_secondary_color()

        # Обновить дату последнего обновления
        self._update_last_updated()
        
        # Очистить все кроме последнего элемента (stretch) с отключением сигналов
        while self.rates_list_layout.count() > 1:
            child = self.rates_list_layout.takeAt(0)
            if child.widget():
                widget = child.widget()
                try:
                    widget.blockSignals(True)
                except:
                    pass
                widget.deleteLater()
        
        # Добавить карточки
        if not self.exchange_rates:
            empty_label = QLabel("Курсы не найдены. Добавьте первый курс!")
            empty_label.setStyleSheet(f"color: {secondary_color}; font-size: 14px;")
            self.rates_list_layout.insertWidget(0, empty_label)
        else:
            index = 0
            for (from_curr, to_curr), rate in sorted(self.exchange_rates.items()):
                card = ExchangeRateCard(from_curr, to_curr, rate)
                self.rates_list_layout.insertWidget(index, card)
                index += 1
    
    def on_refresh_rates(self):
        """Обновить все курсы валют"""
        try:
            # Обновить все курсы из API
            for from_curr, to_curr in list(self.exchange_rates.keys()):
                success, message, rate = ExchangeRateService.refresh_rate(
                    self.current_user.id, from_curr, to_curr
                )
                if success:
                    self.exchange_rates[(from_curr, to_curr)] = rate
            
            self.refresh_display()
            show_toast(self, "Курсы обновлены", 2000)
        except Exception as e:
            show_toast(self, f"Ошибка: {str(e)}", 3000)
    
    def on_add_rate(self):
        """Добавить новый курс валют"""
        dialog = AddRateDialog(self.currency_codes, list(self.exchange_rates.keys()))
        if dialog.exec_() == QDialog.Accepted:
            from_curr, to_curr = dialog.get_selection()
            
            # Добавить курс через сервис
            success, message = ExchangeRateService.add_rate(
                self.current_user.id, from_curr, to_curr
            )
            
            if success:
                # Перезагрузить курсы из БД
                self.load_default_rates()
                show_toast(self, message, 2000)
            else:
                show_toast(self, f"Ошибка: {message}", 3000)
    
    def on_manage_rates(self):
        """Управление существующими курсами"""
        if not self.exchange_rates:
            show_toast(self, "Нет курсов для управления", 2000)
            return
        
        rate_names = [f"{from_c} → {to_c}" for from_c, to_c in self.exchange_rates.keys()]
        rate_name, ok = inputdlg_item(
            self, "Управление курсами",
            "Выберите курс для удаления:",
            rate_names
        )
        
        if ok:
            # Найти соответствующую пару
            for (from_c, to_c) in self.exchange_rates.keys():
                if f"{from_c} → {to_c}" == rate_name:
                    reply = msgbox_question(
                        self, "Подтверждение",
                        f"Удалить курс {rate_name}?",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    
                    if reply == QMessageBox.Yes:
                        # Удалить курс через сервис
                        success, message = ExchangeRateService.delete_rate(
                            self.current_user.id, from_c, to_c
                        )
                        
                        if success:
                            del self.exchange_rates[(from_c, to_c)]
                            self.refresh_display()
                            show_toast(self, message, 2000)
                        else:
                            show_toast(self, f"Ошибка: {message}", 3000)
                        show_toast(self, f"Курс {rate_name} удален", 2000)
                    break

    def _update_last_updated(self):
        """Обновить надпись 'последнее обновление' по самой свежей дате"""
        try:
            rate_objects = ExchangeRateService.get_user_rates_objects(self.current_user.id)
            if not rate_objects:
                self.last_updated_label.setText("")
                return
            latest = max(r["last_updated"] for r in rate_objects if r["last_updated"])
            self.last_updated_label.setText(
                f"Последнее обновление: {latest.strftime('%d.%m.%Y %H:%M')}"
            )
        except Exception:
            self.last_updated_label.setText("")


class AddRateDialog(QDialog):
    """Диалог добавления нового курса валют"""
    
    def __init__(self, currency_codes, existing_pairs, parent=None):
        super().__init__(parent)
        self.currency_codes = currency_codes
        self.existing_pairs = existing_pairs
        self.from_currency = None
        self.to_currency = None
        
        self.init_ui()
        self.setWindowTitle("Добавить новый курс")
        self.setGeometry(200, 200, 400, 200)
        self.setModal(True)
        if get_ui_mode() == UI_MODE_NEW:
            from config import get_current_theme
            self.setStyleSheet(get_new_stylesheet(get_current_theme()))

    def showEvent(self, event):
        super().showEvent(event)
        if get_ui_mode() == UI_MODE_NEW:
            apply_dark_title_bar(self)

    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Из какой валюты
        layout.addWidget(QLabel("Из валюты:"))
        self.from_combo = QComboBox()
        self.from_combo.addItems(self.currency_codes)
        layout.addWidget(self.from_combo)
        
        # В какую валюту
        layout.addWidget(QLabel("В валюту:"))
        self.to_combo = QComboBox()
        self.to_combo.addItems(self.currency_codes)
        self.to_combo.setCurrentIndex(1)  # По умолчанию вторая
        layout.addWidget(self.to_combo)
        
        layout.addSpacing(10)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.on_ok)
        button_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def on_ok(self):
        """Проверить и принять"""
        from_curr = self.from_combo.currentText()
        to_curr = self.to_combo.currentText()
        
        if from_curr == to_curr:
            msgbox_warning(self, "Ошибка", "Валюты не должны быть одинаковыми")
            return
        
        if (from_curr, to_curr) in self.existing_pairs:
            QMessageBox.warning(self, "Ошибка", f"Курс {from_curr}/{to_curr} уже существует")
            return
        
        self.from_currency = from_curr
        self.to_currency = to_curr
        self.accept()
    
    def get_selection(self):
        """Получить выбранные валюты"""
        return self.from_currency, self.to_currency
