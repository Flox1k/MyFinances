# -*- coding: utf-8 -*-
"""
MyFinances - Цифровой кошелёк для управления финансами

Главная точка входа приложения
Инициализирует БД, создает QApplication и управляет окнами (новая архитектура)
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from db.database import init_db


class MyFinancesApp:
    """
    Главное приложение
    Управляет окнами: LoginWindow → ModernMainWindow (с боковым меню и страницами)
    """
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.current_user = None
        
        # Инициализировать БД
        init_db()
        
        # Создать окно входа (выбор по режиму UI)
        self.login_window = self._create_login_window()
        self.main_window = None
    
    def _create_login_window(self):
        """Создать окно входа"""
        from ui.new_login_window import NewLoginWindow
        win = NewLoginWindow()
        win.login_success.connect(self.on_login_success)
        return win

    def on_login_success(self, user):
        """
        Обработчик успешного входа
        Открыть главное окно приложения
        """
        self.current_user = user
        self.login_window.hide()

        from ui.new_main_window import NewMainWindow
        self.main_window = NewMainWindow(user)

        self.main_window.logout.connect(self.on_logout)
        self.main_window.show()
    
    def on_logout(self):
        """
        Обработчик: пользователь вышел из аккаунта
        Вернуться на окно входа
        """
        self.current_user = None
        
        # Закрыть главное окно
        if self.main_window:
            self.main_window.close()
            self.main_window = None
        
        # Создать новое окно входа (выбор по режиму UI)
        self.login_window = self._create_login_window()
        self.login_window.show()
    
    def run(self):
        """Запустить приложение"""
        self.login_window.show()
        sys.exit(self.app.exec_())


if __name__ == "__main__":
    # Создать и запустить приложение
    app = MyFinancesApp()
    app.run()
