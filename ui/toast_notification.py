# -*- coding: utf-8 -*-
"""
Toast-уведомление - небольшое анимированное беззвучное уведомление

Классы:
- ToastNotification: компонент для вывода уведомлений
"""

from PyQt5.QtWidgets import QLabel, QWidget
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QRect
from PyQt5.QtGui import QFont, QColor


class ToastNotification(QLabel):
    """
    Простое Toast-уведомление
    Появляется в верхней части окна с прозрачностью
    Автоматически исчезает через несколько секунд
    """
    
    def __init__(self, message: str, parent=None, duration: int = 3000):
        """
        Args:
            message: Текст уведомления
            parent: Родительское окно
            duration: Время отображения в миллисекундах (по умолчанию 3 секунды)
        """
        super().__init__(message, parent)
        self.duration = duration
        
        # Стиль уведомления
        self.setStyleSheet("""
            QLabel {
                background-color: #1f2937;
                color: #ffffff;
                border-radius: 6px;
                padding: 12px 20px;
                font-size: 13px;
                font-weight: bold;
                border: 1px solid #374151;
            }
        """)
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        
        # Позиционирование в верхний центр экрана
        if parent:
            parent_geometry = parent.geometry()
            center_x = parent_geometry.x() + parent_geometry.width() // 2
            top_y = parent_geometry.y() + 30
            self.setGeometry(center_x - 150, top_y, 300, 45)
        
        # Анимация прозрачности
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(300)
        self.animation.setStartValue(0)
        self.animation.setEndValue(0.95)
        
        # Таймер для скрытия
        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.on_timeout)
        
    def show_notification(self):
        """Показать уведомление с анимацией"""
        self.setWindowOpacity(0)
        self.show()
        self.animation.start()
        self.hide_timer.start(self.duration)
    
    def on_timeout(self):
        """Скрыть уведомление с анимацией"""
        hide_animation = QPropertyAnimation(self, b"windowOpacity")
        hide_animation.setDuration(300)
        hide_animation.setStartValue(0.95)
        hide_animation.setEndValue(0)
        hide_animation.finished.connect(self.hide)
        hide_animation.start()


def show_toast(parent, message: str, duration: int = 3000):
    """
    Удобная функция для вывода Toast-уведомления
    
    Args:
        parent: Родительское окно
        message: Текст уведомления
        duration: Время отображения в миллисекундах
    """
    toast = ToastNotification(message, parent, duration)
    toast.show_notification()
    return toast
