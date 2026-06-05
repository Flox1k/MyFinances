# -*- coding: utf-8 -*-
"""
Страница настроек (New UI) — встроена в боковую панель как вкладка.

Настройки:
- Тема (тёмная / светлая)
- Основная валюта
- Режим UI (новый / старый)
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QRadioButton, QButtonGroup, QComboBox, QFrame, QScrollArea,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from config import (
    get_current_theme, set_theme, AVAILABLE_THEMES,
    get_main_currency, set_main_currency, MULTI_CURRENCIES,
    get_ui_mode, set_ui_mode, UI_MODE_OLD, UI_MODE_NEW,
    get_ui_scale, set_ui_scale, UI_SCALE_STANDARD, UI_SCALE_LARGE,
)
from ui.styles import THEME_DARK, THEME_LIGHT
from ui.new_styles import new_colors


class SettingsPage(QWidget):
    """
    Страница настроек (вкладка в боковой панели).

    Сигналы:
        theme_changed(str)    — смена темы (требует перезагрузки)
        currency_changed(str) — смена основной валюты
        ui_mode_changed(str)  — смена режима UI (требует перезагрузки)
        restart_requested()   — нужно пересоздать главное окно
    """

    theme_changed    = pyqtSignal(str)
    currency_changed = pyqtSignal(str)
    ui_mode_changed  = pyqtSignal(str)
    restart_requested = pyqtSignal()

    def __init__(self, user=None, parent=None):
        super().__init__(parent)
        self._user = user
        self._build_ui()

    # ─── Build ────────────────────────────────────────────────────────

    def _build_ui(self):
        c = new_colors()

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{ background: transparent; border: none; }}
            QScrollBar:vertical {{
                background: {c['bg_card']}; width: 8px; border-radius: 4px; margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {c['border']}; border-radius: 4px; min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {c['primary']}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px; background: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        vlay = QVBoxLayout(container)
        vlay.setContentsMargins(40, 40, 40, 40)
        vlay.setSpacing(28)

        # ── Title with watermark ──────────────────────────────────────
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Настройки")
        title.setStyleSheet(
            f"font-size: 24px; font-weight: 700; color: {c['text_primary']};"
            " background: transparent; border: none;"
        )
        title_layout.addWidget(title)
        
        title_layout.addStretch()
        
        watermark = QLabel("Development by Flox1k")
        watermark.setStyleSheet(
            f"font-size: 11px; color: {c['text_secondary']}; background: transparent; border: none;"
        )
        watermark.setAlignment(Qt.AlignRight)
        title_layout.addWidget(watermark)
        
        vlay.addLayout(title_layout)

        # ── Theme card ────────────────────────────────────────────────
        vlay.addWidget(self._section_label("Тема приложения"))
        theme_card = self._card()
        tc_lay = QVBoxLayout(theme_card)
        tc_lay.setContentsMargins(20, 16, 20, 16)
        tc_lay.setSpacing(12)

        self._theme_group = QButtonGroup(self)
        self._radio_dark = QRadioButton("Тёмная тема")
        self._radio_light = QRadioButton("Светлая тема")
        self._radio_dark.setChecked(get_current_theme() == THEME_DARK)
        self._radio_light.setChecked(get_current_theme() == THEME_LIGHT)
        self._theme_group.addButton(self._radio_dark, 0)
        self._theme_group.addButton(self._radio_light, 1)
        for rb in (self._radio_dark, self._radio_light):
            self._style_radio(rb)
            tc_lay.addWidget(rb)
        vlay.addWidget(theme_card)

        # ── Currency card ─────────────────────────────────────────────
        vlay.addWidget(self._section_label("Основная валюта"))
        cur_card = self._card()
        cc_lay = QVBoxLayout(cur_card)
        cc_lay.setContentsMargins(20, 16, 20, 16)
        cc_lay.setSpacing(10)

        cur_desc = QLabel(
            "Все балансы будут пересчитаны в выбранную валюту по имеющимся курсам."
        )
        cur_desc.setWordWrap(True)
        cur_desc.setStyleSheet(
            f"font-size: 13px; color: {c['text_secondary']}; background: transparent; border: none;"
        )
        cc_lay.addWidget(cur_desc)

        self._currency_combo = QComboBox()
        self._currency_combo.addItems(MULTI_CURRENCIES)
        curr = get_main_currency()
        idx = MULTI_CURRENCIES.index(curr) if curr in MULTI_CURRENCIES else 0
        self._currency_combo.setCurrentIndex(idx)
        cc_lay.addWidget(self._currency_combo)
        vlay.addWidget(cur_card)

        # ── UI mode card ──────────────────────────────────────────────
        vlay.addWidget(self._section_label("Масштаб интерфейса"))
        ui_card = self._card()
        uc_lay = QVBoxLayout(ui_card)
        uc_lay.setContentsMargins(20, 16, 20, 16)
        uc_lay.setSpacing(12)

        scale_desc = QLabel(
            "Крупный режим увеличивает шрифт и элементы интерфейса примерно на 25 %."
        )
        scale_desc.setWordWrap(True)
        scale_desc.setStyleSheet(
            f"font-size: 13px; color: {c['text_secondary']}; background: transparent; border: none;"
        )
        uc_lay.addWidget(scale_desc)

        self._ui_group = QButtonGroup(self)
        self._radio_standard = QRadioButton("Стандартный интерфейс")
        self._radio_large    = QRadioButton("Увеличенный интерфейс")
        self._radio_standard.setChecked(get_ui_scale() == UI_SCALE_STANDARD)
        self._radio_large.setChecked(get_ui_scale() == UI_SCALE_LARGE)
        self._ui_group.addButton(self._radio_standard, 0)
        self._ui_group.addButton(self._radio_large, 1)
        for rb in (self._radio_standard, self._radio_large):
            self._style_radio(rb)
            uc_lay.addWidget(rb)
        vlay.addWidget(ui_card)

        # ── AI Key card ───────────────────────────────────────────────
        vlay.addWidget(self._section_label("API ключ ИИ (OpenRouter)"))
        ai_card = self._card()
        ai_lay = QVBoxLayout(ai_card)
        ai_lay.setContentsMargins(20, 16, 20, 16)
        ai_lay.setSpacing(10)

        ai_desc = QLabel(
            "Ключ используется для запросов к нейронной сети через OpenRouter. "
            "Хранится в файле APIforNeyro.env в папке приложения."
        )
        ai_desc.setWordWrap(True)
        ai_desc.setStyleSheet(
            f"font-size: 13px; color: {c['text_secondary']}; background: transparent; border: none;"
        )
        ai_lay.addWidget(ai_desc)

        from PyQt5.QtWidgets import QLineEdit as _QLineEdit
        self._ai_key_input = _QLineEdit()
        self._ai_key_input.setPlaceholderText("sk-or-v1-...")
        self._ai_key_input.setMinimumHeight(38)
        self._ai_key_input.setStyleSheet(f"""
            QLineEdit {{
                background: {c['bg_main']}; border: 1px solid {c['border']};
                border-radius: 8px; padding: 6px 12px;
                color: {c['text_primary']}; font-size: 14px;
            }}
            QLineEdit:focus {{ border-color: {c['primary']}; }}
        """)
        # Load existing key
        from ui.ai_chat_page import _read_ai_key, _read_ai_model, _write_ai_model
        self._ai_key_input.setText(_read_ai_key())
        ai_lay.addWidget(self._ai_key_input)

        # Модель ИИ
        model_label = QLabel("Модель ИИ")
        model_label.setStyleSheet(
            f"font-size: 13px; font-weight: 600; color: {c['text_primary']}; background: transparent; border: none;"
        )
        ai_lay.addWidget(model_label)

        _FREE_MODELS = [
            "google/gemma-4-31b-it:free",
            "google/gemma-4-26b-a4b-it:free",
            "meta-llama/llama-3.3-70b-instruct:free",
            "nvidia/nemotron-3-super-120b-a12b:free",
            "tencent/hy3-preview:free",
            "qwen/qwen3-next-80b-a3b-instruct:free",
            "minimax/minimax-m2.5:free",
            "nvidia/nemotron-3-nano-30b-a3b:free",
            "nvidia/nemotron-nano-9b-v2:free",
        ]
        from PyQt5.QtWidgets import QComboBox as _QComboBox

        class _NoWheelCombo(_QComboBox):
            def wheelEvent(self, e):
                e.ignore()

        self._ai_model_combo = _NoWheelCombo()
        self._ai_model_combo.setEditable(True)
        self._ai_model_combo.addItems(_FREE_MODELS)
        cur_model = _read_ai_model()
        if cur_model in _FREE_MODELS:
            self._ai_model_combo.setCurrentText(cur_model)
        else:
            self._ai_model_combo.insertItem(0, cur_model)
            self._ai_model_combo.setCurrentIndex(0)
        self._ai_model_combo.setMinimumHeight(38)
        self._ai_model_combo.setStyleSheet(f"""
            QComboBox {{
                background: {c['bg_main']}; border: 1px solid {c['border']};
                border-radius: 8px; padding: 6px 12px;
                color: {c['text_primary']}; font-size: 13px;
            }}
            QComboBox:focus {{ border-color: {c['primary']}; }}
            QComboBox QAbstractItemView {{
                background: {c['bg_card']}; color: {c['text_primary']};
                selection-background-color: {c['primary']};
            }}
        """)
        ai_lay.addWidget(self._ai_model_combo)
        vlay.addWidget(ai_card)

        # Шаблоны категорий (only when user is provided)
        if self._user is not None:
            vlay.addWidget(self._section_label("Шаблоны категорий"))
            tpl_card = self._card()
            tpl_lay = QVBoxLayout(tpl_card)
            tpl_lay.setContentsMargins(20, 16, 20, 16)
            tpl_lay.setSpacing(10)

            tpl_desc = QLabel(
                "Создайте стандартный набор категорий: Еда, Транспорт, Развлечения, "
                "Подписки, Здоровье, Одежда, Прочее — с предустановленными ключевыми словами."
            )
            tpl_desc.setWordWrap(True)
            tpl_desc.setStyleSheet(
                f"font-size: 13px; color: {c['text_secondary']}; background: transparent; border: none;"
            )
            tpl_lay.addWidget(tpl_desc)

            tpl_btn = QPushButton("Создать стандартный набор")
            tpl_btn.setMinimumHeight(38)
            tpl_btn.setCursor(Qt.PointingHandCursor)
            tpl_btn.clicked.connect(self._on_create_templates)
            tpl_lay.addWidget(tpl_btn)
            vlay.addWidget(tpl_card)

        self._info_label = QLabel("")
        self._info_label.setWordWrap(True)
        self._info_label.setStyleSheet(
            f"font-size: 13px; color: {c['warning']}; background: transparent; border: none;"
        )
        self._info_label.hide()
        vlay.addWidget(self._info_label)

        # ── Save button ───────────────────────────────────────────────
        btn_save = QPushButton("Применить")
        btn_save.setMinimumHeight(44)
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet(f"""
            QPushButton {{
                background: {c['primary']}; color: #fff; border: none;
                border-radius: 10px; font-size: 15px; font-weight: 600; padding: 10px 28px;
            }}
            QPushButton:hover {{ background: {c['primary_hover']}; }}
        """)
        btn_save.clicked.connect(self._on_save)
        btn_row = QHBoxLayout()
        btn_row.addWidget(btn_save)
        btn_row.addStretch()
        vlay.addLayout(btn_row)

        # Connect change-detection
        self._radio_dark.toggled.connect(self._on_any_change)
        self._radio_light.toggled.connect(self._on_any_change)
        self._radio_standard.toggled.connect(self._on_any_change)
        self._radio_large.toggled.connect(self._on_any_change)
        self._currency_combo.currentIndexChanged.connect(self._on_any_change)

        vlay.addStretch()

        scroll.setWidget(container)
        root_lay = QVBoxLayout(self)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.addWidget(scroll)

    # ─── Helpers ──────────────────────────────────────────────────────

    def _section_label(self, text: str) -> QLabel:
        c = new_colors()
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"font-size: 15px; font-weight: 600; color: {c['text_primary']};"
            " background: transparent; border: none;"
        )
        return lbl

    def _card(self) -> QFrame:
        c = new_colors()
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: {c['bg_card']}; border-radius: 14px;"
            f" border: 1px solid {c['border']}; }}"
        )
        return card

    def _style_radio(self, rb: QRadioButton):
        c = new_colors()
        rb.setStyleSheet(
            f"QRadioButton {{ color: {c['text_primary']}; font-size: 14px; background: transparent; border: none; }}"
            f"QRadioButton::indicator {{ width: 18px; height: 18px; }}"
            f"QRadioButton::indicator:unchecked {{ border: 2px solid {c['border']};"
            " border-radius: 9px; background: transparent; }"
            f"QRadioButton::indicator:checked {{ border: 2px solid {c['primary']};"
            f" border-radius: 9px; background: {c['primary']}; }}"
        )

    # ─── Slots ────────────────────────────────────────────────────────

    def _on_any_change(self):
        """Show restart warning if theme or scale will change."""
        c = new_colors()
        theme_will_change = (
            (self._radio_dark.isChecked() and get_current_theme() != THEME_DARK) or
            (self._radio_light.isChecked() and get_current_theme() != THEME_LIGHT)
        )
        scale_will_change = (
            (self._radio_standard.isChecked() and get_ui_scale() != UI_SCALE_STANDARD) or
            (self._radio_large.isChecked() and get_ui_scale() != UI_SCALE_LARGE)
        )
        if theme_will_change or scale_will_change:
            self._info_label.setText(
                "После нажатия «Применить» приложение перезагрузится для применения изменений."
            )
            self._info_label.show()
        else:
            self._info_label.hide()

    def _on_save(self):
        # Save AI key and model
        if hasattr(self, "_ai_key_input"):
            from ui.ai_chat_page import _write_ai_key, _write_ai_model
            _write_ai_key(self._ai_key_input.text().strip())
        if hasattr(self, "_ai_model_combo"):
            from ui.ai_chat_page import _write_ai_model
            _write_ai_model(self._ai_model_combo.currentText().strip())

        new_theme      = THEME_DARK if self._radio_dark.isChecked() else THEME_LIGHT
        new_currency   = self._currency_combo.currentText()
        new_scale      = UI_SCALE_STANDARD if self._radio_standard.isChecked() else UI_SCALE_LARGE

        old_theme      = get_current_theme()
        old_currency   = get_main_currency()
        old_scale      = get_ui_scale()

        theme_changed    = new_theme    != old_theme
        currency_changed = new_currency != old_currency
        scale_changed    = new_scale    != old_scale

        if not theme_changed and not currency_changed and not scale_changed:
            return

        if currency_changed:
            set_main_currency(new_currency)
            self.currency_changed.emit(new_currency)

        if theme_changed:
            set_theme(new_theme)
            self.theme_changed.emit(new_theme)

        if scale_changed:
            set_ui_scale(new_scale)
            self.ui_mode_changed.emit(new_scale)

        if theme_changed or scale_changed:
            self.restart_requested.emit()

    def refresh(self):
        """Reload settings values (e.g. when returning to this page)."""
        self._radio_dark.blockSignals(True)
        self._radio_light.blockSignals(True)
        self._radio_standard.blockSignals(True)
        self._radio_large.blockSignals(True)
        self._currency_combo.blockSignals(True)

        self._radio_dark.setChecked(get_current_theme() == THEME_DARK)
        self._radio_light.setChecked(get_current_theme() == THEME_LIGHT)
        self._radio_standard.setChecked(get_ui_scale() == UI_SCALE_STANDARD)
        self._radio_large.setChecked(get_ui_scale() == UI_SCALE_LARGE)
        curr = get_main_currency()
        idx = MULTI_CURRENCIES.index(curr) if curr in MULTI_CURRENCIES else 0
        self._currency_combo.setCurrentIndex(idx)

        self._radio_dark.blockSignals(False)
        self._radio_light.blockSignals(False)
        self._radio_standard.blockSignals(False)
        self._radio_large.blockSignals(False)
        self._currency_combo.blockSignals(False)

        self._info_label.hide()

        # Reload AI key and model
        if hasattr(self, "_ai_key_input"):
            from ui.ai_chat_page import _read_ai_key
            self._ai_key_input.setText(_read_ai_key())
        if hasattr(self, "_ai_model_combo"):
            from ui.ai_chat_page import _read_ai_model
            self._ai_model_combo.setCurrentText(_read_ai_model())

    def _on_create_templates(self):
        from services.services import CategoryService
        from PyQt5.QtWidgets import QMessageBox
        if self._user is None:
            QMessageBox.warning(self, "Ошибка", "Пользователь не определён.")
            return
        created = CategoryService.create_default_templates(self._user.id)
        if created:
            QMessageBox.information(self, "Готово",
                f"Создано категорий: {len(created)}. "
                "Управляйте ими через раздел «Бюджеты» на главной странице.")
        else:
            QMessageBox.information(self, "Информация",
                "У вас уже есть категории с такими названиями, новые не созданы.")
