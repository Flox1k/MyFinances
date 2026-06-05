# -*- coding: utf-8 -*-
"""
Диалог настроек приложения

Позволяет пользователю:
- Выбирать тему приложения (тёмная/светлая)
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QRadioButton, QButtonGroup, QGroupBox, QMessageBox, QComboBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from config import (
    get_current_theme, set_theme, AVAILABLE_THEMES,
    get_main_currency, set_main_currency, MULTI_CURRENCIES,
    get_ui_mode, set_ui_mode, UI_MODE_OLD, UI_MODE_NEW
)
from ui.styles import THEME_DARK, THEME_LIGHT, get_stylesheet, COLORS_DARK, COLORS_LIGHT


class SettingsDialog(QDialog):
    """
    Диалог настроек приложения
    
    Сигналы:
        theme_changed: испускается когда пользователь меняет тему (передаёт новую тему)
    """
    
    theme_changed = pyqtSignal(str)  # Передаёт новую тему
    currency_changed = pyqtSignal(str)  # Передаёт новую основную валюту
    ui_mode_changed = pyqtSignal(str)  # Передаёт новый режим UI
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.setGeometry(100, 100, 500, 400)
        self.setModal(True)
        
        self.current_theme = get_current_theme()
        self.current_currency = get_main_currency()
        self.current_ui_mode = get_ui_mode()
        self.init_ui()
        self.apply_stylesheet()
    
    def init_ui(self):
        """Инициализация интерфейса диалога"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # === Заголовок ===
        title = QLabel("Параметры приложения")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # === Группа тем ===
        theme_group_box = QGroupBox("Тема приложения")
        theme_layout = QVBoxLayout(theme_group_box)
        theme_layout.setSpacing(10)
        
        # Группа кнопок для темы
        self.theme_button_group = QButtonGroup()
        
        # Кнопка для тёмной темы
        is_new = get_ui_mode() == UI_MODE_NEW
        self.radio_dark = QRadioButton("Тёмная тема" if is_new else "🌙 Тёмная тема")
        self.radio_dark.setCheckable(True)
        self.radio_dark.setChecked(self.current_theme == THEME_DARK)
        self.theme_button_group.addButton(self.radio_dark, 0)
        theme_layout.addWidget(self.radio_dark)
        
        # Кнопка для светлой темы
        self.radio_light = QRadioButton("Светлая тема" if is_new else "☀️ Светлая тема")
        self.radio_light.setCheckable(True)
        self.radio_light.setChecked(self.current_theme == THEME_LIGHT)
        self.theme_button_group.addButton(self.radio_light, 1)
        theme_layout.addWidget(self.radio_light)
        
        layout.addWidget(theme_group_box)
        
        # === Группа основной валюты ===
        currency_group_box = QGroupBox("Основная валюта")
        currency_layout = QVBoxLayout(currency_group_box)
        currency_layout.setSpacing(10)

        currency_desc = QLabel(
            "Все балансы на главном экране будут пересчитаны\n"
            "в выбранную валюту по имеющимся курсам."
        )
        if self.current_theme == THEME_DARK:
            desc_color = COLORS_DARK["text_secondary"]
        else:
            desc_color = COLORS_LIGHT["text_secondary"]
        currency_desc.setStyleSheet(f"color: {desc_color}; font-size: 11px;")
        currency_desc.setWordWrap(True)
        currency_layout.addWidget(currency_desc)

        self.currency_combo = QComboBox()
        self.currency_combo.addItems(MULTI_CURRENCIES)
        current_idx = MULTI_CURRENCIES.index(self.current_currency) if self.current_currency in MULTI_CURRENCIES else 0
        self.currency_combo.setCurrentIndex(current_idx)
        currency_layout.addWidget(self.currency_combo)

        layout.addWidget(currency_group_box)

        # === Группа режима UI ===
        ui_group_box = QGroupBox("Режим интерфейса")
        ui_layout = QVBoxLayout(ui_group_box)
        ui_layout.setSpacing(10)

        self.ui_button_group = QButtonGroup()

        self.radio_new_ui = QRadioButton("Новый UI (без эмодзи, чистый стиль)")
        self.radio_new_ui.setChecked(self.current_ui_mode == UI_MODE_NEW)
        self.ui_button_group.addButton(self.radio_new_ui, 0)
        ui_layout.addWidget(self.radio_new_ui)

        self.radio_old_ui = QRadioButton("Старый UI (с эмодзи)")
        self.radio_old_ui.setChecked(self.current_ui_mode == UI_MODE_OLD)
        self.ui_button_group.addButton(self.radio_old_ui, 1)
        ui_layout.addWidget(self.radio_old_ui)

        layout.addWidget(ui_group_box)
        
        # === Информационный текст ===
        info_label = QLabel("Выберите предпочитаемую тему приложения.\nТема будет применена после сохранения.")
        
        # Выбрать правильный цвет для информационного текста
        if self.current_theme == THEME_DARK:
            info_color = COLORS_DARK["text_secondary"]
        else:
            info_color = COLORS_LIGHT["text_secondary"]
        
        info_label.setStyleSheet(f"color: {info_color}; font-size: 11px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # === Пространство ===
        layout.addStretch()
        
        # === Кнопки действий ===
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Кнопка отмены
        cancel_btn = QPushButton("Отмена")
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        button_layout.addStretch()
        
        # Кнопка сохранения
        save_btn = QPushButton("Сохранить")
        save_btn.setMinimumWidth(100)
        save_btn.setObjectName("btn_primary")
        save_btn.clicked.connect(self.on_save)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def apply_stylesheet(self):
        """Применить стили к диалогу"""
        if self.current_ui_mode == UI_MODE_NEW:
            from ui.new_styles import get_new_stylesheet
            self.setStyleSheet(get_new_stylesheet(self.current_theme))
        else:
            stylesheet = get_stylesheet(self.current_theme)
            self.setStyleSheet(stylesheet)
    
    def on_save(self):
        """Обработчик: сохранить настройки"""
        # Определить выбранную тему
        if self.radio_dark.isChecked():
            new_theme = THEME_DARK
        else:
            new_theme = THEME_LIGHT

        # Определить выбранную валюту
        new_currency = self.currency_combo.currentText()

        # Определить выбранный режим UI
        new_ui_mode = UI_MODE_NEW if self.radio_new_ui.isChecked() else UI_MODE_OLD

        theme_changed = (new_theme != self.current_theme)
        currency_changed = (new_currency != self.current_currency)
        ui_changed = (new_ui_mode != self.current_ui_mode)

        if not theme_changed and not currency_changed and not ui_changed:
            self.accept()
            return

        # Сохранить валюту
        if currency_changed:
            set_main_currency(new_currency)
            self.currency_changed.emit(new_currency)

        # Сохранить режим UI
        if ui_changed:
            set_ui_mode(new_ui_mode)
            self.current_ui_mode = new_ui_mode
            self.ui_mode_changed.emit(new_ui_mode)

        # Сохранить тему
        if theme_changed:
            if set_theme(new_theme):
                self.current_theme = new_theme
                self.theme_changed.emit(new_theme)

        # Показать сообщение и перезагрузить при структурных изменениях
        if theme_changed or ui_changed:
            QMessageBox.information(
                self,
                "Успех",
                "Настройки сохранены! Приложение перезагрузится.",
                QMessageBox.Ok
            )
            self.accept()
            return

        if currency_changed:
            QMessageBox.information(
                self,
                "Успех",
                f"Основная валюта изменена на {new_currency}.",
                QMessageBox.Ok
            )
        self.accept()
