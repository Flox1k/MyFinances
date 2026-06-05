# -*- coding: utf-8 -*-
"""
Интерактивный линейный график изменения баланса.

Реализован на чистом PyQt5 (QPainter) без внешних зависимостей.

Использование:
    chart = BalanceChartWidget(currency="KZT")
    chart.set_loader(lambda days: BalanceHistoryService.get_wallet_balance_history(wid, days))
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
from PyQt5.QtCore import Qt, QPoint, QRect, pyqtSignal
from PyQt5.QtGui import (
    QPainter, QPen, QColor, QFont,
    QPainterPath, QFontMetrics, QBrush, QCursor,
)
from ui.new_styles import new_colors

# (label, days)
_RANGES = [("7дн", 7), ("28дн", 28), ("90дн", 90), ("365дн", 365)]


# ── Кнопка диапазона (не QPushButton — чтобы глобальный стиль не влиял) ─────────

class _RangeChip(QWidget):
    """
    Минимальный виджет кнопки диапазона, нарисованный QPainterьем.
    Не базируется на QPushButton, так что глобальные стили кнопок не влияют.
    """
    clicked = pyqtSignal(int)   # эмитит days

    def __init__(self, label: str, days: int, parent=None):
        super().__init__(parent)
        self.label = label
        self.days = days
        self.active = False
        self._hover = False
        self.setFixedSize(52, 26)
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
            bg = QColor(c['primary'])
            text_col = QColor(c['text_on_primary'])
            border_col = QColor(c['primary'])
        elif self._hover:
            bg = QColor(c['bg_card'])
            text_col = QColor(c['text_primary'])
            border_col = QColor(c['primary'])
        else:
            bg = QColor(c['bg_hover'])
            text_col = QColor(c['text_secondary'])
            border_col = QColor(c['border'])

        # Background
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(bg))
        p.drawRoundedRect(0, 0, w, h, r, r)

        # Border
        pen = QPen(border_col, 1)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(0, 0, w - 1, h - 1, r, r)

        # Text
        f = QFont()
        f.setPointSize(10)
        f.setBold(self.active)
        p.setFont(f)
        p.setPen(text_col)
        p.drawText(QRect(0, 0, w, h), Qt.AlignCenter, self.label)
        p.end()

    def enterEvent(self, event):
        self._hover = True
        self.update()

    def leaveEvent(self, event):
        self._hover = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.days)



class BalanceChartWidget(QWidget):
    """
    Виджет линейного графика с выбором периода (7дн / 28дн / 90дн / 365дн).

    Параметры:
        title    — необязательная строка-заголовок (слева от кнопок).
        currency — обозначение валюты (отображается в tooltip).
    """
    range_changed = pyqtSignal(int)   # эмитит days при смене диапазона

    def __init__(self, title: str = "", currency: str = "KZT", parent=None):
        super().__init__(parent)
        self.title = title
        self.currency = currency
        self._data: list = []        # list[(date, float)]
        self._range_days: int = 28
        self._loader = None
        self._build_ui()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        c = new_colors()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(4)

        # Header row: optional title + range buttons
        header = QHBoxLayout()
        header.setContentsMargins(4, 0, 4, 0)
        header.setSpacing(6)

        if self.title:
            lbl = QLabel(self.title)
            lbl.setStyleSheet(
                f"font-size: 13px; font-weight: 600; color: {c['text_secondary']};"
            )
            header.addWidget(lbl)

        header.addStretch()

        self._range_chips: list[_RangeChip] = []
        for label, days in _RANGES:
            chip = _RangeChip(label, days)
            chip.clicked.connect(self._on_range_click)
            self._range_chips.append(chip)
            header.addWidget(chip)

        layout.addLayout(header)
        self._refresh_chips()

        # Canvas
        self._canvas = _ChartCanvas(self)
        self._canvas.setMinimumHeight(180)
        self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self._canvas)

    def _refresh_chips(self):
        for chip in self._range_chips:
            chip.set_active(chip.days == self._range_days)

    # ── Public API ─────────────────────────────────────────────────────────────────────

    def set_loader(self, loader_fn):
        """
        Устанавливает функцию загрузки данных.
        loader_fn(days: int) -> list[(date, float)]
        Вызывается немедленно и при каждой смене диапазона.
        """
        self._loader = loader_fn
        self._reload()

    def set_data(self, data: list, currency: str = ""):
        """Установить данные напрямую (list of (date, float), sorted asc)."""
        self._data = data or []
        if currency:
            self.currency = currency
        self._canvas.update()

    def get_range_days(self) -> int:
        return self._range_days

    # ── Internal ──────────────────────────────────────────────────────────────

    def _on_range_click(self, days: int):
        if days == self._range_days:
            return
        self._range_days = days
        self._refresh_chips()
        self.range_changed.emit(days)
        self._reload()

    def _reload(self):
        if self._loader:
            try:
                self.set_data(self._loader(self._range_days))
            except Exception:
                self.set_data([])


# ── Internal canvas ───────────────────────────────────────────────────────────

class _ChartCanvas(QWidget):
    """Область отрисовки графика (используется только внутри BalanceChartWidget)."""

    _ML = 82   # left  — для меток Y (увеличен, чтобы подписи не наезжали)
    _MR = 18   # right
    _MT = 14   # top
    _MB = 40   # bottom — для меток X

    def __init__(self, chart: BalanceChartWidget):
        super().__init__(chart)
        self._chart = chart
        self._hover_idx: int = -1
        self.setMouseTracking(True)
        self.setAutoFillBackground(False)

    # ── Geometry ──────────────────────────────────────────────────────────────

    def _plot_rect(self):
        """(px, py, pw, ph) — координаты области построения."""
        return (
            self._ML,
            self._MT,
            self.width() - self._ML - self._MR,
            self.height() - self._MT - self._MB,
        )

    def _compute_pts(self, data, px, py, pw, ph):
        """Перевести (date, value) в экранные координаты QPoint."""
        if not data:
            return [], 0.0, 0.0
        vals = [v for _, v in data]
        min_v, max_v = min(vals), max(vals)
        span = max_v - min_v
        if abs(span) < 1e-9:
            pad = max(abs(max_v) * 0.1, 100.0)
            min_v -= pad
            max_v += pad
            span = max_v - min_v
        else:
            pad = span * 0.08
            min_v -= pad
            max_v += pad
            span = max_v - min_v
        n = len(data)
        pts = []
        for i, (_, v) in enumerate(data):
            x = px + (i / max(n - 1, 1)) * pw
            y = py + (1.0 - (v - min_v) / span) * ph
            pts.append(QPoint(int(round(x)), int(round(y))))
        return pts, min_v, max_v

    # ── Paint ─────────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        c = new_colors()
        data = self._chart._data
        w, h = self.width(), self.height()
        px, py, pw, ph = self._plot_rect()

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Reset any dirty-rect clip Qt may have set, so grid lines always span full width
        painter.setClipRect(self.rect(), Qt.ReplaceClip)

        # Background with rounded corners
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(c['bg_card'])))
        painter.drawRoundedRect(0, 0, w, h, 10, 10)

        # Clip all subsequent drawing to the rounded shape
        clip_path = QPainterPath()
        clip_path.addRoundedRect(0, 0, w, h, 10, 10)
        painter.setClipPath(clip_path, Qt.IntersectClip)

        if len(data) < 2:
            painter.setPen(QColor(c['text_secondary']))
            f = QFont()
            f.setPointSize(11)
            painter.setFont(f)
            painter.drawText(QRect(px, py, pw, ph), Qt.AlignCenter, "Нет данных")
            painter.end()
            return

        pts, min_v, max_v = self._compute_pts(data, px, py, pw, ph)

        # ── Y grid + labels ───────────────────────────────────────────────────
        n_ticks = 4
        grid_pen = QPen(QColor(c['border']))
        grid_pen.setWidth(1)
        lf = QFont()
        lf.setPointSize(9)
        painter.setFont(lf)
        for i in range(n_ticks + 1):
            ratio = i / n_ticks
            gy = py + ratio * ph
            painter.setPen(grid_pen)
            painter.drawLine(px, int(gy), px + pw, int(gy))
            val = max_v - ratio * (max_v - min_v)
            if val >= 0:
                painter.setPen(QColor(c['text_secondary']))
                painter.drawText(
                    QRect(0, int(gy) - 10, px - 6, 20),
                    Qt.AlignRight | Qt.AlignVCenter,
                    self._fmt(val),
                )

        # ── X labels ──────────────────────────────────────────────────────────
        n_days = len(data)
        if n_days <= 7:
            step = 1
        elif n_days <= 28:
            step = 7
        elif n_days <= 90:
            step = 14
        else:
            step = 60

        painter.setPen(QColor(c['text_secondary']))
        xf = QFont()
        xf.setPointSize(9)
        painter.setFont(xf)
        for i, (d, _) in enumerate(data):
            if i % step == 0 or i == n_days - 1:
                x = px + (i / max(n_days - 1, 1)) * pw
                label = f"{d.day:02d}.{d.month:02d}"
                # Clamp left edge so X labels never overlap Y-axis labels
                xl = max(int(x) - 26, px - 4)
                # Clamp right edge so last label stays inside widget
                xr = min(xl, self.width() - 52)
                painter.drawText(
                    QRect(xr, h - self._MB + 5, 52, 20),
                    Qt.AlignCenter,
                    label,
                )

        # ── Line ──────────────────────────────────────────────────────────────
        line_pen = QPen(QColor(c['primary']))
        line_pen.setWidth(2)
        line_pen.setCapStyle(Qt.RoundCap)
        line_pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(line_pen)
        lpath = QPainterPath()
        lpath.moveTo(pts[0].x(), pts[0].y())
        for p in pts[1:]:
            lpath.lineTo(p.x(), p.y())
        painter.drawPath(lpath)

        # ── Small dots (only when few points) ─────────────────────────────────
        if n_days <= 30:
            for i, p in enumerate(pts):
                if i == self._hover_idx:
                    continue
                painter.setPen(QPen(QColor(c['primary']), 1))
                painter.setBrush(QBrush(QColor(c['bg_card'])))
                painter.drawEllipse(p.x() - 3, p.y() - 3, 6, 6)

        # ── Hover ─────────────────────────────────────────────────────────────
        if 0 <= self._hover_idx < len(pts):
            hi = self._hover_idx
            hp = pts[hi]
            hd, hv = data[hi]

            # Vertical dotted line
            vpen = QPen(QColor(c['primary']))
            vpen.setStyle(Qt.DotLine)
            vpen.setWidth(1)
            painter.setPen(vpen)
            painter.drawLine(hp.x(), py, hp.x(), py + ph)

            # Highlighted dot
            painter.setPen(QPen(QColor(c['primary']), 2))
            painter.setBrush(QBrush(QColor(c['primary'])))
            painter.drawEllipse(hp.x() - 5, hp.y() - 5, 10, 10)

            # Tooltip
            date_str = f"{hd.day:02d}.{hd.month:02d}.{hd.year}"
            val_str = f"{self._fmt_full(hv)} {self._chart.currency}"
            tip = f"{date_str}   {val_str}"
            tf = QFont()
            tf.setPointSize(10)
            tf.setBold(True)
            painter.setFont(tf)
            fm = QFontMetrics(tf)
            tw = fm.horizontalAdvance(tip) + 26
            th = 30
            tx = hp.x() - tw // 2
            ty = hp.y() - th - 12
            tx = max(px, min(tx, px + pw - tw))
            ty = max(py, ty)

            bg_c = QColor(c['bg_hover'])
            bg_c.setAlpha(230)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(bg_c))
            painter.drawRoundedRect(tx, ty, tw, th, 6, 6)

            painter.setPen(QPen(QColor(c['primary']), 1))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(tx, ty, tw, th, 6, 6)

            painter.setPen(QColor(c['text_primary']))
            painter.setFont(tf)
            painter.drawText(QRect(tx, ty, tw, th), Qt.AlignCenter, tip)

        painter.end()

    # ── Mouse ─────────────────────────────────────────────────────────────────

    def mouseMoveEvent(self, event):
        data = self._chart._data
        if len(data) < 2:
            return
        px, _py, pw, _ph = self._plot_rect()
        n = len(data)
        raw = (event.x() - px) / pw * (n - 1)
        nearest = max(0, min(n - 1, int(round(raw))))
        if self._hover_idx != nearest:
            self._hover_idx = nearest
            self.update()

    def leaveEvent(self, event):
        if self._hover_idx != -1:
            self._hover_idx = -1
            self.update()

    # ── Formatting ────────────────────────────────────────────────────────────

    @staticmethod
    def _fmt(val: float) -> str:
        """Short format for axis labels (K/M suffix)."""
        av = abs(val)
        sign = "-" if val < 0 else ""
        if av >= 1_000_000:
            return f"{sign}{av / 1_000_000:.1f}M"
        if av >= 1_000:
            return f"{sign}{av / 1_000:.1f}K"
        return f"{val:.0f}"

    @staticmethod
    def _fmt_full(val: float) -> str:
        """Full format for tooltip (with thousands separator)."""
        if abs(val) >= 1_000_000:
            av = abs(val)
            sign = "-" if val < 0 else ""
            return f"{sign}{av / 1_000_000:.2f}M"
        return f"{val:,.2f}".replace(",", " ")
