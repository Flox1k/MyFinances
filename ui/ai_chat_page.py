# -*- coding: utf-8 -*-
"""
Страница «Чат с ИИ» (AI Chat) — вкладка в главном окне приложения MyFinances.

Функции:
- История сообщений (QTextEdit, read-only)
- Поле ввода + кнопка "Отправить"
- Кнопка "Указать кошелёк" → диалог выбора кошельков и периода
- Асинхронные запросы к OpenRouter через QThread
"""

import json
import os
import re
from datetime import datetime, timedelta

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
    QLineEdit, QLabel, QDialog, QCheckBox, QScrollArea, QFrame,
    QButtonGroup, QRadioButton, QMessageBox, QSizePolicy,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

from config import get_ui_scale, UI_SCALE_LARGE, DATA_DIR
from db.database import SessionLocal
from db.repositories import WalletRepository, TransactionRepository
from ui.new_styles import new_colors


# ─── Путь до .env файла с ключом ─────────────────────────────────────────────
_ENV_PATH = os.path.join(DATA_DIR, "APIforNeyro.env")


def _read_ai_key() -> str:
    """Прочитать AI_key из APIforNeyro.env."""
    return _read_env_var("AI_key")


def _read_env_var(name: str) -> str:
    """Прочитать переменную из APIforNeyro.env (вспомогательная — будет переопределена ниже)."""
    if not os.path.isfile(_ENV_PATH):
        return ""
    with open(_ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith(name):
                parts = stripped.split("=", 1)
                if len(parts) == 2:
                    return parts[1].strip()
    return ""


def _write_ai_key(key: str):
    """Записать/перезаписать AI_key в APIforNeyro.env."""
    _write_env_var("AI_key", key)


_DEFAULT_MODEL = "google/gemma-4-31b-it:free"


def _read_env_var(name: str) -> str:
    """Прочитать переменную из APIforNeyro.env."""
    if not os.path.isfile(_ENV_PATH):
        return ""
    with open(_ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith(name):
                parts = stripped.split("=", 1)
                if len(parts) == 2:
                    return parts[1].strip()
    return ""


def _write_env_var(name: str, value: str):
    """Записать/перезаписать переменную в APIforNeyro.env."""
    new_line = f"{name} = {value}\n"
    if os.path.isfile(_ENV_PATH):
        with open(_ENV_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
        written = False
        for i, line in enumerate(lines):
            if line.strip().startswith(name):
                lines[i] = new_line
                written = True
                break
        if not written:
            lines.append(new_line)
        with open(_ENV_PATH, "w", encoding="utf-8") as f:
            f.writelines(lines)
    else:
        with open(_ENV_PATH, "w", encoding="utf-8") as f:
            f.write(new_line)


def _read_ai_model() -> str:
    """Прочитать AI_model из APIforNeyro.env."""
    return _read_env_var("AI_model") or _DEFAULT_MODEL


def _write_ai_model(model: str):
    """Записать AI_model в APIforNeyro.env."""
    _write_env_var("AI_model", model)


# ─── QThread для запросов к OpenRouter ───────────────────────────────────────

class AIChatWorker(QThread):
    """Выполняет запрос к OpenRouter в фоновом потоке."""

    response_ready = pyqtSignal(str)   # успешный ответ
    error_occurred = pyqtSignal(str)   # сообщение об ошибке

    def __init__(self, api_key: str, messages: list, parent=None):
        super().__init__(parent)
        self._api_key = api_key
        self._messages = messages

    def run(self):
        try:
            from openai import OpenAI
            model = _read_ai_model()
            client = OpenAI(
                api_key=self._api_key,
                base_url="https://openrouter.ai/api/v1",
            )
            completion = client.chat.completions.create(
                model=model,
                messages=self._messages,
            )
            text = completion.choices[0].message.content or ""
            self.response_ready.emit(text)
        except Exception as exc:
            self.error_occurred.emit(str(exc))


# ─── Диалог выбора кошельков и периода ───────────────────────────────────────

PERIOD_LABELS = [
    ("7 дней",    7),
    ("28 дней",   28),
    ("90 дней",   90),
    ("365 дней",  365),
    ("Всё время", None),
]


class WalletPickerDialog(QDialog):
    """Диалог: выбрать кошельки + период для аналитики."""

    def __init__(self, user_id: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Указать кошелёк")
        self.setModal(True)
        self.setMinimumWidth(400)
        self._user_id = user_id
        self._wallet_checkboxes: list[tuple[QCheckBox, int, str]] = []  # (cb, id, name)
        self._period_group = QButtonGroup(self)
        self._build_ui()

    def _build_ui(self):
        c = new_colors()
        self.setStyleSheet(f"""
            QDialog {{ background: {c['bg_main']}; }}
            QLabel {{ color: {c['text_primary']}; background: transparent; }}
            QCheckBox {{ color: {c['text_primary']}; background: transparent; }}
            QRadioButton {{ color: {c['text_primary']}; background: transparent; }}
            QPushButton {{
                background: {c['primary']}; color: #fff; border: none;
                border-radius: 8px; font-size: 14px; padding: 8px 20px;
            }}
            QPushButton:hover {{ background: {c['primary_hover']}; }}
            QPushButton#btn_cancel {{
                background: {c['bg_card']}; color: {c['text_primary']};
                border: 1px solid {c['border']};
            }}
            QPushButton#btn_cancel:hover {{ background: {c['border']}; }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        # Заголовок
        title = QLabel("Выберите кошельки")
        title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {c['text_primary']};")
        root.addWidget(title)

        # "Выбрать все"
        self._cb_all = QCheckBox("Все кошельки")
        self._cb_all.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {c['primary']};")
        self._cb_all.stateChanged.connect(self._on_select_all)
        root.addWidget(self._cb_all)

        # Список кошельков
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setMaximumHeight(200)
        wallet_widget = QWidget()
        wallet_widget.setStyleSheet("background: transparent;")
        self._wallet_layout = QVBoxLayout(wallet_widget)
        self._wallet_layout.setSpacing(6)
        self._wallet_layout.setContentsMargins(0, 0, 0, 0)
        self._load_wallets()
        scroll.setWidget(wallet_widget)
        root.addWidget(scroll)

        # Период
        period_label = QLabel("Период аналитики")
        period_label.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {c['text_primary']};")
        root.addWidget(period_label)

        period_frame = QFrame()
        period_frame.setStyleSheet(
            f"QFrame {{ background: {c['bg_card']}; border-radius: 10px; border: 1px solid {c['border']}; }}"
        )
        pf_lay = QVBoxLayout(period_frame)
        pf_lay.setContentsMargins(14, 10, 14, 10)
        pf_lay.setSpacing(6)
        for i, (label, _days) in enumerate(PERIOD_LABELS):
            rb = QRadioButton(label)
            rb.setStyleSheet(
                f"QRadioButton {{ color: {c['text_primary']}; font-size: 13px; background: transparent; border: none; }}"
                f"QRadioButton::indicator {{ width: 16px; height: 16px; }}"
                f"QRadioButton::indicator:checked {{ background: {c['primary']}; border: 2px solid {c['primary']}; border-radius: 8px; }}"
                f"QRadioButton::indicator:unchecked {{ border: 2px solid {c['border']}; border-radius: 8px; background: transparent; }}"
            )
            if i == 0:
                rb.setChecked(True)
            self._period_group.addButton(rb, i)
            pf_lay.addWidget(rb)
        root.addWidget(period_frame)

        # Кнопки
        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Отмена")
        btn_cancel.setObjectName("btn_cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("Применить")
        btn_ok.clicked.connect(self._on_ok)
        btn_row.addWidget(btn_cancel)
        btn_row.addStretch()
        btn_row.addWidget(btn_ok)
        root.addLayout(btn_row)

    def _load_wallets(self):
        session = SessionLocal()
        try:
            repo = WalletRepository(session)
            wallets = repo.get_wallets_by_user(self._user_id)
            for w in wallets:
                cb = QCheckBox(f"{w.name}  ({w.currency})")
                self._wallet_checkboxes.append((cb, w.id, w.name))
                self._wallet_layout.addWidget(cb)
        finally:
            session.close()

    def _on_select_all(self, state: int):
        checked = state == Qt.Checked
        for cb, _wid, _name in self._wallet_checkboxes:
            cb.blockSignals(True)
            cb.setChecked(checked)
            cb.blockSignals(False)

    def _on_ok(self):
        selected = [(wid, name) for cb, wid, name in self._wallet_checkboxes if cb.isChecked()]
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите хотя бы один кошелёк.")
            return
        period_idx = self._period_group.checkedId()
        self._selected_wallets = selected
        self._selected_period = PERIOD_LABELS[period_idx]
        self.accept()

    # Public getters
    def selected_wallets(self) -> list:
        return getattr(self, "_selected_wallets", [])

    def selected_period(self) -> tuple:
        return getattr(self, "_selected_period", PERIOD_LABELS[0])


# ─── Основная страница чата ───────────────────────────────────────────────────

SYSTEM_PROMPT = (
    "Ты — профессиональный финансовый ассистент приложения MyFinances. "
    "Твоя задача — анализировать предоставленные данные JSON и давать краткие, "
    "полезные советы по экономии и управлению средствами. "
    "Отвечай на языке пользователя."
)


# ─── Markdown → HTML ─────────────────────────────────────────────────────────

def _inline_md(text: str, c: dict) -> str:
    """Inline markdown (bold, italic, code) → HTML. Input already HTML-escaped."""
    code_bg = c.get("bg_main", "#0F172A")
    code_fg = c.get("text_secondary", "#94A3B8")
    # Inline code
    text = re.sub(
        r'`([^`]+)`',
        lambda m: (
            f'<code style="background:{code_bg}; color:{code_fg};'
            f' font-family:Consolas,monospace; font-size:13px;'
            f' padding:1px 5px; border-radius:3px;">{m.group(1)}</code>'
        ),
        text,
    )
    # Bold+italic
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<b><i>\1</i></b>', text)
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # Italic * or _
    text = re.sub(r'\*([^*\n]+)\*', r'<i>\1</i>', text)
    text = re.sub(r'_([^_\n]+)_', r'<i>\1</i>', text)
    return text


def _md_to_html(text: str, c: dict) -> str:
    """Convert a Markdown subset to HTML for QTextEdit.append()."""
    code_bg  = c.get("bg_main", "#0F172A")
    code_fg  = c.get("text_secondary", "#94A3B8")
    text_col = c.get("text_primary", "#E2E8F0")

    lines = text.split("\n")
    result: list[str] = []
    in_code = False
    code_buf: list[str] = []
    code_lang = ""

    for line in lines:
        stripped = line.strip()

        # ── Code block boundaries ──────────────────────────────────
        if stripped.startswith("```"):
            if not in_code:
                in_code = True
                code_lang = stripped[3:].strip()
                code_buf = []
            else:
                raw = "\n".join(code_buf)
                raw = raw.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                lang_label = f'<span style="font-size:11px; color:{code_fg};">{code_lang}</span><br>' if code_lang else ""
                result.append(
                    f'<div style="background:{code_bg}; border-radius:6px;'
                    f' padding:8px 10px; margin:4px 0; font-family:Consolas,monospace;'
                    f' font-size:13px; color:{code_fg}; white-space:pre-wrap;">'
                    f'{lang_label}{raw}</div>'
                )
                in_code = False
                code_buf = []
                code_lang = ""
            continue

        if in_code:
            code_buf.append(line)
            continue

        # ── Escape HTML ────────────────────────────────────────────
        esc = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        # ── Headers ───────────────────────────────────────────────
        if esc.startswith("### "):
            content = _inline_md(esc[4:], c)
            result.append(f'<p style="font-size:15px; font-weight:700; color:{text_col}; margin:6px 0 1px 0;">{content}</p>')
            continue
        if esc.startswith("## "):
            content = _inline_md(esc[3:], c)
            result.append(f'<p style="font-size:17px; font-weight:700; color:{text_col}; margin:8px 0 2px 0;">{content}</p>')
            continue
        if esc.startswith("# "):
            content = _inline_md(esc[2:], c)
            result.append(f'<p style="font-size:20px; font-weight:700; color:{text_col}; margin:10px 0 4px 0;">{content}</p>')
            continue

        # ── Horizontal rule ───────────────────────────────────────
        if stripped in ("---", "***", "___"):
            border_col = c.get("border", "#334155")
            result.append(f'<hr style="border:none; border-top:1px solid {border_col}; margin:6px 0;"/>')
            continue

        # ── Bullet list ───────────────────────────────────────────
        m = re.match(r'^(\s*)[*\-+]\s+(.+)$', esc)
        if m:
            indent = len(m.group(1)) // 2
            content = _inline_md(m.group(2), c)
            pad = "&nbsp;" * (indent * 4)
            result.append(f'{pad}&bull;&nbsp;{content}<br>')
            continue

        # ── Numbered list ─────────────────────────────────────────
        m = re.match(r'^(\s*)(\d+)\.\s+(.+)$', esc)
        if m:
            indent = len(m.group(1)) // 2
            content = _inline_md(m.group(3), c)
            pad = "&nbsp;" * (indent * 4)
            result.append(f'{pad}{m.group(2)}.&nbsp;{content}<br>')
            continue

        # ── Empty line ────────────────────────────────────────────
        if stripped == "":
            result.append("<br>")
            continue

        # ── Normal line ───────────────────────────────────────────
        result.append(_inline_md(esc, c) + "<br>")

    # Unclosed code block
    if in_code and code_buf:
        raw = "\n".join(code_buf).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        result.append(
            f'<code style="background:{code_bg}; color:{code_fg}; font-family:Consolas,monospace;">{raw}</code><br>'
        )

    return "".join(result)


class AIChatPage(QWidget):
    """Страница «Чат с ИИ»."""

    def __init__(self, user, parent=None):
        super().__init__(parent)
        self._user = user
        self._selected_wallets: list = []   # [(wallet_id, wallet_name), ...]
        self._selected_period: tuple = ("7 дней", 7)
        self._worker: AIChatWorker | None = None
        # Базовый размер шрифта с учётом масштаба UI
        self._base_font_size: int = 18 if get_ui_scale() == UI_SCALE_LARGE else 14
        self._font_size: int = self._base_font_size
        self._build_ui()

    # ─── Build UI ─────────────────────────────────────────────────────

    def _build_ui(self):
        c = new_colors()
        fs = self._font_size
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 32, 32, 32)
        root.setSpacing(16)

        # ── Заголовок + кнопки зума ────────────────────────────────────
        title_row = QHBoxLayout()
        title = QLabel("Чат с ИИ")
        title.setStyleSheet(
            f"font-size: {fs + 10}px; font-weight: 700; color: {c['text_primary']}; background: transparent;"
        )
        title_row.addWidget(title)
        title_row.addStretch()

        zoom_style = f"""
            QPushButton {{
                background: transparent; color: {c['text_secondary']};
                border: 1px solid {c['border']}; border-radius: 6px;
                font-size: 16px; font-weight: 700; padding: 2px 10px;
            }}
            QPushButton:hover {{ color: {c['primary']}; border-color: {c['primary']}; }}
        """
        btn_zoom_out = QPushButton("−")
        btn_zoom_out.setFixedSize(32, 32)
        btn_zoom_out.setCursor(Qt.PointingHandCursor)
        btn_zoom_out.setStyleSheet(zoom_style)
        btn_zoom_out.setToolTip("Уменьшить шрифт")
        btn_zoom_out.clicked.connect(self._zoom_out)
        title_row.addWidget(btn_zoom_out)

        btn_zoom_reset = QPushButton("✕")
        btn_zoom_reset.setFixedSize(32, 32)
        btn_zoom_reset.setCursor(Qt.PointingHandCursor)
        btn_zoom_reset.setStyleSheet(zoom_style)
        btn_zoom_reset.setToolTip("Сбросить размер")
        btn_zoom_reset.clicked.connect(self._zoom_reset)
        title_row.addWidget(btn_zoom_reset)

        btn_zoom_in = QPushButton("+")
        btn_zoom_in.setFixedSize(32, 32)
        btn_zoom_in.setCursor(Qt.PointingHandCursor)
        btn_zoom_in.setStyleSheet(zoom_style)
        btn_zoom_in.setToolTip("Увеличить шрифт")
        btn_zoom_in.clicked.connect(self._zoom_in)
        title_row.addWidget(btn_zoom_in)

        root.addLayout(title_row)

        # Индикатор контекста (верхний — минималистичный)
        self._wallet_indicator = QLabel("Кошелёк не выбран — ИИ ответит только на общий вопрос.")
        self._wallet_indicator.setStyleSheet(
            f"font-size: {fs - 1}px; color: {c['text_secondary']}; background: transparent; padding: 2px 0;"
        )
        self._wallet_indicator.setWordWrap(True)
        root.addWidget(self._wallet_indicator)

        # История чата
        self._chat_history = QTextEdit()
        self._chat_history.setReadOnly(True)
        self._chat_history.setStyleSheet(f"""
            QTextEdit {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 12px;
                padding: 14px;
                color: {c['text_primary']};
                font-size: {fs}px;
                font-family: "Segoe UI", Arial, sans-serif;
            }}
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
        root.addWidget(self._chat_history, 1)

        # Нижняя панель
        bottom = QVBoxLayout()
        bottom.setSpacing(8)

        # Строка ввода + кнопка отправить
        input_row = QHBoxLayout()
        input_row.setSpacing(10)
        self._input_field = QLineEdit()
        self._input_field.setPlaceholderText("Введите сообщение...")
        self._input_field.setMinimumHeight(44)
        self._input_field.setStyleSheet(f"""
            QLineEdit {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 10px;
                padding: 8px 14px;
                color: {c['text_primary']};
                font-size: {fs}px;
            }}
            QLineEdit:focus {{ border-color: {c['primary']}; }}
        """)
        self._input_field.returnPressed.connect(self._on_send)
        input_row.addWidget(self._input_field, 1)

        self._btn_send = QPushButton("Отправить")
        self._btn_send.setMinimumHeight(44)
        self._btn_send.setCursor(Qt.PointingHandCursor)
        self._btn_send.setStyleSheet(f"""
            QPushButton {{
                background: {c['primary']}; color: #fff;
                border: none; border-radius: 10px;
                font-size: {fs}px; font-weight: 600; padding: 8px 22px;
            }}
            QPushButton:hover {{ background: {c['primary_hover']}; }}
            QPushButton:disabled {{ background: {c['border']}; color: {c['text_secondary']}; }}
        """)
        self._btn_send.clicked.connect(self._on_send)
        input_row.addWidget(self._btn_send)
        bottom.addLayout(input_row)

        # ── Chips area (кошельки + период) ─────────────────────────
        self._chips_frame = QFrame()
        self._chips_frame.setVisible(False)
        self._chips_frame.setStyleSheet(
            f"QFrame {{ background: transparent; border-radius: 8px;"
            f" border: 1px solid {c['border']}; }}"
        )
        chips_lay = QHBoxLayout(self._chips_frame)
        chips_lay.setContentsMargins(10, 8, 10, 8)
        chips_lay.setSpacing(8)

        # Кошельки (чип в цвет акцента, без заливки)
        self._wallet_chip = QLabel()
        self._wallet_chip.setStyleSheet(
            f"QLabel {{ background: transparent; color: {c['primary']};"
            f" border-radius: 6px; padding: 3px 10px; font-size: 13px;"
            f" font-weight: 600; border: 1px solid {c['primary']}; }}"
        )
        chips_lay.addWidget(self._wallet_chip)

        # Период (чип в цвет границы, нейтральный)
        self._period_chip = QLabel()
        self._period_chip.setStyleSheet(
            f"QLabel {{ background: transparent; color: {c['text_secondary']};"
            f" border-radius: 6px; padding: 3px 10px; font-size: 13px;"
            f" font-weight: 600; border: 1px solid {c['border']}; }}"
        )
        chips_lay.addWidget(self._period_chip)
        chips_lay.addStretch()

        # Кнопка «убрать» внутри chips frame
        btn_rm = QPushButton("Убрать")
        btn_rm.setCursor(Qt.PointingHandCursor)
        btn_rm.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {c['text_secondary']};"
            f" border: none; font-size: 12px; padding: 2px 6px; }}"
            f"QPushButton:hover {{ color: {c['danger']}; }}"
        )
        btn_rm.clicked.connect(self._on_clear_wallet)
        chips_lay.addWidget(btn_rm)
        bottom.addWidget(self._chips_frame)

        # ── Кнопка "Указать кошелёк" ────────────────────────────────
        btn_row2 = QHBoxLayout()
        self._btn_wallet = QPushButton("Прикрепить кошелёк")
        self._btn_wallet.setCursor(Qt.PointingHandCursor)
        self._btn_wallet.setMinimumHeight(36)
        self._btn_wallet.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {c['primary']};
                border: 1px solid {c['primary']}; border-radius: 8px;
                font-size: 13px; padding: 6px 18px;
            }}
            QPushButton:hover {{ background: {c['primary']}; color: #fff; }}
        """)
        self._btn_wallet.clicked.connect(self._on_pick_wallet)
        btn_row2.addWidget(self._btn_wallet)
        btn_row2.addStretch()
        bottom.addLayout(btn_row2)

        root.addLayout(bottom)

    # ─── Zoom ──────────────────────────────────────────────────────────

    def _zoom_in(self):
        self._font_size = min(self._font_size + 2, 32)
        self._apply_font_size()

    def _zoom_out(self):
        self._font_size = max(self._font_size - 2, 10)
        self._apply_font_size()

    def _zoom_reset(self):
        self._font_size = self._base_font_size
        self._apply_font_size()

    def _apply_font_size(self):
        fs = self._font_size
        c = new_colors()
        self._chat_history.setStyleSheet(f"""
            QTextEdit {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 12px;
                padding: 14px;
                color: {c['text_primary']};
                font-size: {fs}px;
                font-family: "Segoe UI", Arial, sans-serif;
            }}
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
        self._input_field.setStyleSheet(f"""
            QLineEdit {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 10px;
                padding: 8px 14px;
                color: {c['text_primary']};
                font-size: {fs}px;
            }}
            QLineEdit:focus {{ border-color: {c['primary']}; }}
        """)
        self._btn_send.setStyleSheet(f"""
            QPushButton {{
                background: {c['primary']}; color: #fff;
                border: none; border-radius: 10px;
                font-size: {fs}px; font-weight: 600; padding: 8px 22px;
            }}
            QPushButton:hover {{ background: {c['primary_hover']}; }}
            QPushButton:disabled {{ background: {c['border']}; color: {c['text_secondary']}; }}
        """)

    # ─── Slots ────────────────────────────────────────────────────────

    def _on_pick_wallet(self):
        dlg = WalletPickerDialog(self._user.id, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self._selected_wallets = dlg.selected_wallets()
            self._selected_period = dlg.selected_period()
            self._update_chips_display()

    def _on_clear_wallet(self):
        self._selected_wallets = []
        self._selected_period = ("7 дней", 7)
        self._update_chips_display()

    def _update_chips_display(self):
        """Обновить чипсы и верхний индикатор."""
        c = new_colors()
        if not self._selected_wallets:
            self._chips_frame.setVisible(False)
            self._wallet_indicator.setText("Кошелёк не выбран — ИИ ответит только на общий вопрос.")
            self._wallet_indicator.setStyleSheet(
                f"font-size: 13px; color: {c['text_secondary']}; background: transparent; padding: 2px 0;"
            )
            return
        names = ", ".join(n for _wid, n in self._selected_wallets)
        period_label = self._selected_period[0]
        self._wallet_chip.setText(names)
        self._period_chip.setText(period_label)
        self._chips_frame.setVisible(True)
        self._wallet_indicator.setText("Финансовый контекст прикреплён")
        self._wallet_indicator.setStyleSheet(
            f"font-size: 13px; font-weight: 600; color: {c['primary']};"
            f" background: transparent; padding: 2px 0;"
        )

    def _on_send(self):
        text = self._input_field.text().strip()
        if not text:
            return

        api_key = _read_ai_key()
        if not api_key:
            QMessageBox.warning(
                self, "API ключ не задан",
                "Укажите ключ OpenRouter в Настройках → API ключ ИИ."
            )
            return

        self._input_field.clear()
        # Передать снимок текущих кошельков/периода прямо в сообщение
        wallet_snapshot = list(self._selected_wallets)
        period_snapshot = self._selected_period
        self._append_message("Вы", text, wallets=wallet_snapshot, period=period_snapshot)
        self._set_busy(True)

        # Собрать системный промпт
        system_content = SYSTEM_PROMPT
        if wallet_snapshot:
            financial_data = self._collect_financial_data()
            system_content += f"\n\nДанные пользователя (JSON):\n{json.dumps(financial_data, ensure_ascii=False, separators=(',', ':'))}"

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": text},
        ]

        self._worker = AIChatWorker(api_key, messages, parent=self)
        self._worker.response_ready.connect(self._on_response)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.finished.connect(lambda: self._set_busy(False))
        self._worker.start()

    def _on_response(self, text: str):
        self._append_message("ИИ", text)

    def _on_error(self, error: str):
        if "429" in error or "rate" in error.lower() or "rate-limited" in error.lower():
            msg = (
                "Превышен лимит запросов к бесплатной модели (429).\n"
                "Подождите минуту и попробуйте снова, или смените модель в Настройках."
            )
            self._append_message("Ошибка", msg, is_error=True)
        elif "404" in error or "No endpoints found" in error:
            msg = (
                "Модель недоступна (404) — вероятно, её убрали с OpenRouter.\n"
                "Смените модель в Настройках на другую из списка."
            )
            self._append_message("Ошибка", msg, is_error=True)
        else:
            self._append_message("Ошибка", error, is_error=True)

    # ─── Helpers ──────────────────────────────────────────────────────

    def _set_busy(self, busy: bool):
        self._btn_send.setEnabled(not busy)
        self._input_field.setEnabled(not busy)
        self._btn_send.setText("Жду ответа..." if busy else "Отправить")

    def _append_message(
        self,
        sender: str,
        text: str,
        is_error: bool = False,
        wallets: list | None = None,
        period: tuple | None = None,
    ):
        c = new_colors()
        if sender == "Вы":
            color = c.get("primary", "#6366f1")
            label_html = f'<span style="color:{color}; font-weight:700;">Вы:</span>'
        elif is_error:
            color = c.get("danger", "#ef4444")
            label_html = f'<span style="color:{color}; font-weight:700;">Ошибка:</span>'
        else:
            color = c.get("secondary", "#4ADE80")
            label_html = f'<span style="color:{color}; font-weight:700;">ИИ:</span>'

        # Строка привязанных кошельков (только для сообщений пользователя)
        wallet_badge = ""
        if wallets:
            names = ", ".join(n for _wid, n in wallets)
            period_label = period[0] if period else ""
            wallet_badge = (
                f'<p style="color:{color}; font-size:12px; font-weight:700; margin:2px 0 0 0;">'
                f'{names} &nbsp;&bull;&nbsp; {period_label}</p>'
            )

        # Преобразуем markdown в HTML
        if sender in ("ИИ", "Ошибка"):
            body_html = _md_to_html(text, c)
        else:
            # Сообщение пользователя: просто экранируем
            safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
            body_html = safe + "<br>"

        html = f'{label_html} {body_html}{wallet_badge}<br>'
        self._chat_history.append(html)

    def _collect_financial_data(self) -> dict:
        """Собрать транзакции и баланс по выбранным кошелькам за выбранный период."""
        _period_label, period_days = self._selected_period
        wallet_ids = [wid for wid, _name in self._selected_wallets]

        session = SessionLocal()
        try:
            wallet_repo = WalletRepository(session)
            tx_repo = TransactionRepository(session)

            wallets_data = []
            for wid, wname in self._selected_wallets:
                wallet = wallet_repo.get_wallet_by_id(wid)
                if wallet is None:
                    continue

                # Фильтр по дате
                if period_days is not None:
                    date_from = datetime.now() - timedelta(days=period_days)
                else:
                    date_from = None

                txs = tx_repo.get_transactions_by_wallet(wid)
                if date_from:
                    txs = [t for t in txs if t.created_at >= date_from]

                transactions = []
                for t in txs:
                    transactions.append({
                        "date": t.created_at.strftime("%Y-%m-%d"),
                        "type": t.type.value,
                        "amount": t.amount,
                        "description": t.description or "",
                    })

                wallets_data.append({
                    "wallet": wname,
                    "currency": wallet.currency,
                    "balance": wallet.balance,
                    "transactions": transactions,
                })

            return {"wallets": wallets_data}
        finally:
            session.close()

    def refresh(self):
        """Вызывается при переключении на страницу."""
        pass
