"""
view.py
Рівень представлення: усі віджети PyQt5 та клас UserInterface.
"""

from __future__ import annotations
import logging
from datetime import datetime
import os
import sys
import ctypes

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QGraphicsDropShadowEffect, QSizePolicy, QTableWidget,
    QTableWidgetItem, QHeaderView, QScrollArea, QButtonGroup, QRadioButton,
    QFileDialog, QAbstractItemView, QSplitter, QStackedWidget,
    QGraphicsOpacityEffect, 
)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal, QPoint
from PyQt5.QtGui import (
    QPainter, QLinearGradient, QColor, QFont, QPainterPath,
    QPen, QPixmap, QImage, QPalette, QIcon, QCursor, 
)

from matplotlib.figure import Figure

from model import Loan, LoanType, PaymentSchedule
from validator import LoanFormData
from chart_generator import ChartGenerator

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(__file__)

# ── змінні дизайну ─────────────────────────────────────────────────────────────
_SANS = "Segoe UI"
_MONO = "Courier New"
_ANIM_MED = 260

_INPUT_BASE = """
    QLineEdit {
        background: rgba(10,25,65,0.75);
        padding-left: 8px;
        border: 1.5px solid rgba(80,130,255,0.45);
        border-radius: 9px; color: #e8f0ff;
        font-size: 14px; font-family: Courier New;
        min-height: 42px; max-height: 42px;
        selection-background-color: rgba(30,111,255,0.5);
    }
    QLineEdit#smallInput {
        font-size: 11px;
    }
    QLineEdit#smallInput2 {
        font-size: 9px;
    }
    QLineEdit:hover  { border: 1.5px solid rgba(100,160,255,0.75);
                       background: rgba(15,35,80,0.85); }
    QLineEdit:focus  { border: 2px solid rgba(30,140,255,0.95);
                       background: rgba(12,30,75,0.95); color:#ffffff; }
    QLineEdit:disabled { color: rgba(255,255,255,0.22);
                         border: 1.5px solid rgba(60,90,160,0.20);
                         background: rgba(8,15,40,0.40); }
"""

_SCROLL_BAR = """
    QScrollBar:vertical { background: rgba(255,255,255,0.04);
        width:5px; border-radius:3px; margin:0; }
    QScrollBar::handle:vertical { background: rgba(100,160,255,0.35);
        border-radius:3px; min-height:20px; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
    QScrollBar:horizontal { height:0; }
"""

_TABLE_SS = f"""
    QTableWidget {{ background:transparent; color:#e8f0ff;
        font-family:Courier New; font-size:12px; border:none;
        gridline-color:rgba(255,255,255,0.07);
        selection-background-color:rgba(30,111,255,0.28); outline:none; }}
    QHeaderView::section {{ background:rgba(20,60,140,0.7); color:rgba(160,200,255,0.9);
        font-family:Segoe UI; font-size:10px; font-weight:700;
        letter-spacing:1.2px; border:none; padding:9px 8px;
        border-bottom:1px solid rgba(100,160,255,0.25); }}
    QTableWidget::item {{ padding:5px 10px; border:none; }}
    QTableCornerButton::section {{ background:rgba(20,60,140,0.7); border:none; }}
    {_SCROLL_BAR}
"""

_TOOLTIP = """
    QToolTip {
        background-color: #0e1a33;
        color: #d6e4ff;
        border: 1px solid #1e3a6b;
        font-size: 11px;
    }
"""

class AnimatedTooltip(QLabel):

    def __init__(self, text, parent=None):
        super().__init__(text, parent)

        self.setStyleSheet("""
        QLabel {
            background:#0e1a33;
            color:#d6e4ff;
            border:1px solid #2c5cff;
            padding:6px;
            border-radius:6px;
            font-size:12px;
        }
        """)

        self.setWindowFlags(Qt.ToolTip)

        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)

        self.anim = QPropertyAnimation(effect, b"opacity")
        self.anim.setDuration(150)
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)

    def show_at_cursor(self):
        self.move(QCursor.pos() + QPoint(12, 12))
        self.show()
        self.anim.start()


def attach_tooltip(widget, text):

    tooltip = AnimatedTooltip(text)
    timer = QTimer(widget)
    timer.setSingleShot(True)
    timer.setInterval(300)

    def show_tip():
        tooltip.show_at_cursor()

    def enter(event):
        timer.start()

    def leave(event):
        timer.stop()
        tooltip.hide()

    timer.timeout.connect(show_tip)

    widget.enterEvent = enter
    widget.leaveEvent = leave

# ══════════════════════════════════════════════════════════════════════════════
#  КЛАСИ ВІДЖЕТІВ
# ══════════════════════════════════════════════════════════════════════════════

class GradientBackground(QWidget):
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        g = QLinearGradient(0, 0, self.width(), self.height())
        g.setColorAt(0.00, QColor("#080d24"))
        g.setColorAt(0.45, QColor("#091230"))
        g.setColorAt(1.00, QColor("#070c22"))
        p.fillRect(self.rect(), g)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(30, 111, 255, 12))
        p.drawEllipse(-120, -120, 560, 560)
        p.setBrush(QColor(0, 220, 255, 8))
        p.drawEllipse(self.width() - 350, self.height() - 350, 700, 700)


class GlassCard(QFrame):
    def __init__(self, radius=14, alpha0=20, alpha1=8, parent=None):
        super().__init__(parent)
        self._r, self._a0, self._a1 = radius, alpha0, alpha1
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 70))
        self.setGraphicsEffect(shadow)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), self._r, self._r)
        g = QLinearGradient(0, 0, 0, self.height())
        g.setColorAt(0, QColor(255, 255, 255, self._a0))
        g.setColorAt(1, QColor(255, 255, 255, self._a1))
        p.fillPath(path, g)
        p.setPen(QPen(QColor(255, 255, 255, 28), 1.0))
        p.drawPath(path)


class FadeInCard(GlassCard):
    """GlassCard, що анімує прозорість від 0 до 1 під час reveal()."""

    def __init__(self, radius=14, alpha0=25, alpha1=10, parent=None):
        super().__init__(radius, alpha0, alpha1, parent)
        self._opacity  = 0.0
        self._o_target = 1.0
        self._o_timer  = QTimer(self)
        self._o_timer.setInterval(12)
        self._o_timer.timeout.connect(self._tick)

    def reveal(self):
        self._opacity  = 0.0
        self._o_target = 1.0
        self.setVisible(True)
        self._o_timer.start()

    def _tick(self):
        diff = self._o_target - self._opacity
        if abs(diff) < 0.015:
            self._opacity = self._o_target
            self._o_timer.stop()
        else:
            self._opacity += diff * 0.22
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setOpacity(max(0.0, min(1.0, self._opacity)))
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), self._r, self._r)
        g = QLinearGradient(0, 0, 0, self.height())
        g.setColorAt(0, QColor(255, 255, 255, self._a0))
        g.setColorAt(1, QColor(255, 255, 255, self._a1))
        p.fillPath(path, g)
        p.setPen(QPen(QColor(255, 255, 255, 28), 1.0))
        p.drawPath(path)


class StyledInput(QLineEdit):
    """QLineEdit з анімованим світінням при фокусі."""

    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setStyleSheet(_INPUT_BASE)
        self.setMinimumHeight(42)
        self.setMaximumHeight(42)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._glow_t   = 0.0
        self._g_target = 0.0
        self._timer    = QTimer(self)
        self._timer.setInterval(12)
        self._timer.timeout.connect(self._tick)

    def _tick(self):
        diff = self._g_target - self._glow_t
        if abs(diff) < 0.015:
            self._glow_t = self._g_target
            self._timer.stop()
        else:
            self._glow_t += diff * 0.25
        self.update()

    def focusInEvent(self, e):
        self._g_target = 1.0
        self._timer.start()
        super().focusInEvent(e)

    def focusOutEvent(self, e):
        self._g_target = 0.0
        self._timer.start()
        super().focusOutEvent(e)

    def paintEvent(self, e):
        super().paintEvent(e)
        if self._glow_t > 0.01:
            p = QPainter(self)
            p.setRenderHint(QPainter.Antialiasing)
            p.setClipRect(self.rect())
            pen = QPen(QColor(30, 140, 255, int(self._glow_t * 55)), 3.5)
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(1, 1, self.width() - 2, self.height() - 2, 9, 9)

    def mark_error(self):
        self.setStyleSheet(_INPUT_BASE +
            "QLineEdit { border:2px solid #ff6b8a; background:rgba(80,10,30,0.5); }")

    def clear_error(self):
        self.setStyleSheet(_INPUT_BASE)


class GradientButton(QPushButton):
    """Анімована основна/другорядна кнопка зі станами наведення та натискання."""

    def __init__(self, text, primary=True, parent=None):
        super().__init__(text, parent)
        self._primary  = primary
        self._hover_t  = 0.0
        self._press_t  = 0.0
        self._h_target = 0.0
        self._p_target = 0.0
        self._timer    = QTimer(self)
        self._timer.setInterval(12)
        self._timer.timeout.connect(self._tick)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(46)
        self.setMaximumHeight(46)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setAttribute(Qt.WA_Hover, True)
        self._apply_base_style()

    def _apply_base_style(self):
        border = "border:none;" if self._primary \
                 else "border:1px solid rgba(255,255,255,0.16);"
        self.setStyleSheet(f"""QPushButton {{
            background:transparent; {border} border-radius:10px;
            color:{'white' if self._primary else 'rgba(180,210,255,0.85)'};
            font-size:{'13' if self._primary else '12'}px;
            font-weight:{'700' if self._primary else '600'};
            letter-spacing:{'1.8' if self._primary else '1.2'}px;
            font-family:{_SANS}; }}""")

    def _tick(self):
        settled = True
        for attr, target in (("_hover_t", self._h_target),
                              ("_press_t", self._p_target)):
            diff = target - getattr(self, attr)
            if abs(diff) < 0.015:
                setattr(self, attr, target)
            else:
                setattr(self, attr, getattr(self, attr) + diff * 0.28)
                settled = False
        if settled:
            self._timer.stop()
        self.update()

    def enterEvent(self, e):
        self._h_target = 1.0
        self._timer.start()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._h_target = 0.0
        self._p_target = 0.0
        self._timer.start()
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        self._p_target = 1.0
        self._timer.start()
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        self._p_target = 0.0
        self._timer.start()
        super().mouseReleaseEvent(e)

    def paintEvent(self, _):
        p   = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h    = self.width(), self.height()
        ht, pt  = self._hover_t, self._press_t
        scale   = 1.0 - pt * 0.018
        if scale < 1.0:
            p.translate(w / 2, h / 2)
            p.scale(scale, scale)
            p.translate(-w / 2, -h / 2)
        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h, 10, 10)
        if self._primary:
            grad = QLinearGradient(0, 0, w, 0)
            grad.setColorAt(0, QColor(
                max(0, min(255, int(30  + ht * 28  - pt * 16))),
                max(0, min(255, int(111 + ht * 17  - pt * 30))),
                max(0, min(255, int(255 - pt * 30)))))
            grad.setColorAt(1, QColor(
                max(0, min(255, int(0   + ht * 20  - pt * 10))),
                max(0, min(255, int(198 + ht * 20  - pt * 40))),
                max(0, min(255, int(255 - pt * 30)))))
            p.setPen(Qt.NoPen)
            p.fillPath(path, grad)
            sheen = QLinearGradient(0, 0, 0, h * 0.5)
            sheen.setColorAt(0, QColor(255, 255, 255, int(25 + ht * 12)))
            sheen.setColorAt(1, QColor(255, 255, 255, 0))
            p.fillPath(path, sheen)
        else:
            p.setPen(Qt.NoPen)
            p.fillPath(path, QColor(255, 255, 255, int(18 + ht * 20 + pt * 8)))
            p.setPen(QPen(QColor(255, 255, 255, int(40 + ht * 60)), 1.0))
            p.drawPath(path)
        p.setPen(QColor(255, 255, 255, 230) if self._primary
                 else QColor(180, 210, 255, int(200 + ht * 55)))
        font = QFont(_SANS, 11 if self._primary else 10,
                     QFont.Bold if self._primary else QFont.DemiBold)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 1.8 if self._primary else 1.2)
        p.setFont(font)
        p.drawText(0, 0, w, h, Qt.AlignCenter, self.text())


class ToggleSwitch(QWidget):
    toggled = pyqtSignal(int)

    def __init__(self, left_text: str, right_text: str, parent=None):
        super().__init__(parent)
        self._texts  = [left_text, right_text]
        self._state  = 0
        self._pill_x = 0.0
        self._target = 0.0
        self.setFixedHeight(30)
        self.setMinimumWidth(144)
        self.setCursor(Qt.PointingHandCursor)
        self._timer = QTimer(self)
        self._timer.setInterval(12)
        self._timer.timeout.connect(self._tick)

    def state(self) -> int:
        return self._state

    def mousePressEvent(self, _):
        self._state  = 1 - self._state
        self._target = float(self._state)
        self._timer.start()
        self.toggled.emit(self._state)

    def _tick(self):
        diff = self._target - self._pill_x
        if abs(diff) < 0.012:
            self._pill_x = self._target
            self._timer.stop()
        else:
            self._pill_x += diff * 0.22
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        r    = h // 2
        track = QPainterPath()
        track.addRoundedRect(0, 0, w, h, r, r)
        p.fillPath(track, QColor(255, 255, 255, 18))
        p.setPen(QPen(QColor(255, 255, 255, 28), 1))
        p.drawPath(track)
        hw = w / 2
        px = self._pill_x * hw
        pill = QPainterPath()
        pill.addRoundedRect(px, 0, hw, h, r, r)
        pg = QLinearGradient(px, 0, px + hw, 0)
        pg.setColorAt(0, QColor("#1e6fff"))
        pg.setColorAt(1, QColor("#00c6ff"))
        p.setPen(Qt.NoPen)
        p.fillPath(pill, pg)
        font = QFont(_SANS, 9, QFont.Bold)
        p.setFont(font)
        for i, txt in enumerate(self._texts):
            alpha = int(255 * (1 - self._pill_x * 0.6)) if i == 0 \
                    else int(140 + 115 * self._pill_x)
            p.setPen(QColor(255, 255, 255, max(80, min(255, alpha))))
            p.drawText(int(i * hw), 0, int(hw), h, Qt.AlignCenter, txt)


class AnimatedTabWidget(QWidget):
    """Панель вкладок із переходом між сторінками з плавним згасанням прозорості."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tabs: list[tuple[str, QWidget]] = []
        self._current = 0
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self._bar        = QWidget()
        self._bar.setFixedHeight(38)
        self._bar.setStyleSheet("background:transparent;")
        self._bar_layout = QHBoxLayout(self._bar)
        self._bar_layout.setContentsMargins(8, 0, 0, 0)
        self._bar_layout.setSpacing(2)
        self._bar_layout.addStretch()
        root.addWidget(self._bar)
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background:transparent;")
        self._stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        root.addWidget(self._stack)
        self._opacity = QGraphicsOpacityEffect(self._stack)
        self._stack.setGraphicsEffect(self._opacity)
        self._opacity.setOpacity(1.0)
        self._anim = QPropertyAnimation(self._opacity, b"opacity")
        self._anim.setDuration(_ANIM_MED)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._pending_idx = -1
        self._anim.finished.connect(self._fade_in)

    def add_tab(self, widget: QWidget, label: str):
        idx = len(self._tabs)
        self._tabs.append((label, widget))
        self._stack.addWidget(widget)
        btn = QPushButton(label)
        btn.setCheckable(True)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(30)
        btn.setMinimumWidth(110)
        btn.clicked.connect(lambda _, i=idx: self.switch_to(i))
        btn.setStyleSheet(self._btn_style(False))
        self._bar_layout.insertWidget(idx, btn)
        if idx == 0:
            self.force_current(0)

    def _btn_style(self, active: bool) -> str:
        if active:
            return (f"QPushButton {{ background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                    f"stop:0 rgba(30,111,255,0.45),stop:1 rgba(0,198,255,0.3));"
                    f"border:1px solid rgba(100,180,255,0.35);"
                    f"border-bottom:2px solid #1e6fff; border-radius:7px 7px 0 0;"
                    f"color:#e8f0ff; font-family:{_SANS}; font-size:10px;"
                    f"font-weight:700; letter-spacing:1.2px; padding:0 14px; }}")
        return (f"QPushButton {{ background:rgba(255,255,255,0.05);"
                f"border:1px solid rgba(255,255,255,0.10);"
                f"border-bottom:1px solid rgba(255,255,255,0.05);"
                f"border-radius:7px 7px 0 0; color:rgba(160,190,255,0.65);"
                f"font-family:{_SANS}; font-size:10px; font-weight:600;"
                f"letter-spacing:1.2px; padding:0 14px; }}"
                f"QPushButton:hover {{ background:rgba(255,255,255,0.10);"
                f"color:rgba(200,220,255,0.9); }}")

    def _update_buttons(self):
        for i in range(len(self._tabs)):
            btn = self._bar_layout.itemAt(i).widget()
            if btn:
                btn.setStyleSheet(self._btn_style(i == self._current))
                btn.setChecked(i == self._current)

    def switch_to(self, idx: int):
        if idx == self._current:
            return
        self._pending_idx = idx
        self._anim.stop()
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.start()

    def _fade_in(self):
        if self._pending_idx >= 0:
            self._current = self._pending_idx
            self._stack.setCurrentIndex(self._current)
            self._update_buttons()
            self._pending_idx = -1
            self._anim.setStartValue(0.0)
            self._anim.setEndValue(1.0)
            self._anim.start()

    def force_current(self, idx: int):
        self._anim.stop()
        self._pending_idx = -1
        self._current = idx
        self._stack.setCurrentIndex(idx)
        self._update_buttons()
        self._opacity.setOpacity(1.0)


class ResponsiveChartView(QLabel):
    """Відображає фігуру Matplotlib як масштабоване зображення."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self._pix: QPixmap | None = None
        self._show_placeholder()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(300, 260)
        self._fx   = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._fx)
        self._fx.setOpacity(1.0)
        self._anim = QPropertyAnimation(self._fx, b"opacity")
        self._anim.setDuration(_ANIM_MED)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

    def _show_placeholder(self):
        self.setStyleSheet(
            f"color:rgba(130,165,255,0.35); font-family:{_SANS}; font-size:12px;")
        self.setText("Графік з’явиться після розрахунку")

    def load_figure(self, fig: Figure):
        from PyQt5.QtGui import QImage
        from chart_generator import ChartGenerator
        data = ChartGenerator.figure_to_bytes(fig)
        img  = QImage.fromData(data)
        self._pix = QPixmap.fromImage(img)
        self._rescale()
        if self._anim.state() != QPropertyAnimation.Running:
            self._anim.stop()
            self._anim.setStartValue(0.0)
            self._anim.setEndValue(1.0)
            self._anim.start()

    def set_error(self, msg: str = ""):
        self._pix = None
        self.setPixmap(QPixmap())
        self.setStyleSheet(
            f"color:rgba(255,107,138,0.7); font-family:{_SANS}; font-size:11px;")
        self.setText("Chart error — please check inputs")
        logger.error("Chart render error: %s", msg)

    def _rescale(self):
        if self._pix is None:
            return
        scaled = self._pix.scaled(
            max(1, self.width() - 8), max(1, self.height() - 8),
            Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(scaled)
        self.setText("")
        self.setStyleSheet("")

    def resizeEvent(self, ev):
        if self._pix:
            self._rescale()
        super().resizeEvent(ev)

    def clear_chart(self):
        self._pix = None
        self.setPixmap(QPixmap())
        self._show_placeholder()

    def full_pixmap(self) -> QPixmap | None:
        return self._pix


class CustomCheckBox(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self._checked = False
        self._text    = text
        self._hovered = False
        self._fill_t  = 0.0
        self._target  = 0.0
        self._timer   = QTimer(self)
        self._timer.setInterval(12)
        self._timer.timeout.connect(self._tick)
        self.setFixedHeight(28)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover, True)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, val: bool):
        if val != self._checked:
            self._checked = val
            self._target  = 1.0 if val else 0.0
            self._timer.start()
            self.toggled.emit(self._checked)

    def mousePressEvent(self, _):
        self.setChecked(not self._checked)

    def _tick(self):
        diff = self._target - self._fill_t
        if abs(diff) < 0.02:
            self._fill_t = self._target
            self._timer.stop()
        else:
            self._fill_t += diff * 0.25
        self.update()

    def enterEvent(self, _):
        self._hovered = True
        self.update()

    def leaveEvent(self, _):
        self._hovered = False
        self.update()

    def paintEvent(self, _):
        p      = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        BOX    = 17
        RADIUS = 4
        top_y  = (self.height() - BOX) // 2
        t      = self._fill_t
        idle   = QColor(10, 22, 65, 180)
        active = QColor(20, 90, 240, 220)
        bg     = QColor(
            int(idle.red()   + t * (active.red()   - idle.red())),
            int(idle.green() + t * (active.green() - idle.green())),
            int(idle.blue()  + t * (active.blue()  - idle.blue())),
            int(idle.alpha() + t * (active.alpha() - idle.alpha())),
        )
        box_path = QPainterPath()
        box_path.addRoundedRect(0, top_y, BOX, BOX, RADIUS, RADIUS)
        p.setPen(Qt.NoPen)
        p.fillPath(box_path, bg)
        border_alpha = min(255, int(100 + t * 155 + (40 if self._hovered else 0)))
        p.setPen(QPen(QColor(60, 140, 255, border_alpha), 1.5))
        p.drawPath(box_path)
        if t > 0.05:
            pen = QPen(QColor(255, 255, 255, int(255 * min(t * 1.5, 1.0))), 2.2)
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            cx, cy = BOX // 2, top_y + BOX // 2
            p.drawLine(int(cx - 4.5), int(cy + 0.5), int(cx - 1), int(cy + 3.5))
            p.drawLine(int(cx - 1),   int(cy + 3.5), int(cx + 5), int(cy - 3))
        label_x = BOX + 9
        label_w = self.width() - label_x
        p.setPen(QColor(232, 240, 255, int(160 + 95 * t)))
        font = QFont(_SANS, 7)
        font.setWeight(QFont.Normal)
        p.setFont(font)
        fm     = p.fontMetrics()
        elided = fm.elidedText(self._text, Qt.ElideRight, max(1, label_w - 4))
        p.drawText(label_x, 0, label_w, self.height(),
                   Qt.AlignVCenter | Qt.AlignLeft, elided)


class CountUpLabel(QLabel):
    """Анімує числове значення, поступово збільшуючи його від нуля."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._target = 0.0
        self._current = 0.0
        self._prefix = ""
        self._decimals = 2
        self._steps = 0
        self._max_steps = 18
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)

    def animate_to(self, value: float, prefix="", decimals=2):
        self._target     = value
        self._current    = 0.0
        self._prefix     = prefix
        self._decimals   = decimals
        self._steps      = 0
        self._timer.start()

    def _tick(self):
        self._steps += 1
        t = 1 - (1 - min(self._steps / self._max_steps, 1.0)) ** 2
        self._current = t * self._target
        self._update_text()
        if self._steps >= self._max_steps:
            self._timer.stop()
            self._current = self._target
            self._update_text()

    def _update_text(self):
        fmt = f"{self._prefix}{self._current:,.{self._decimals}f}" \
              if self._decimals else f"{self._prefix}{self._current:,.0f}"
        self.setText(fmt)


class LeftScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setStyleSheet(
            f"QScrollArea {{ background:transparent; border:none; }}"
            f"QScrollArea > QWidget > QWidget {{ background:transparent; }}"
            f"{_SCROLL_BAR}")

# ── допоміжні функції компонування ───────────────────────────────────────────────────

def _lbl(text, size=11, color="#e8f0ff", bold=False,
         family=_SANS, spacing=0, wrap=False) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"color:{color}; font-size:{size}px; font-family:{family};"
        f"font-weight:{'700' if bold else '400'};"
        f"letter-spacing:{spacing}px; background:transparent;")
    if wrap:
        lbl.setWordWrap(True)
    return lbl


def _divider() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.HLine)
    f.setFixedHeight(1)
    f.setStyleSheet("background:rgba(255,255,255,0.09); border:none;")
    return f


def _summary_divider() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.HLine)
    f.setFixedHeight(1)
    f.setStyleSheet("background:rgba(255,255,255,0.06); border:none; margin:0 4px;")
    return f


def _section_label(text: str) -> QLabel:
    return _lbl(text, 9, "rgba(80,140,255,0.65)", bold=True, spacing=1.8)


def _field(label_text: str, widget: QWidget, hint="", gap=6) -> QVBoxLayout:
    lay = QVBoxLayout()
    lay.setSpacing(gap)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.addWidget(_lbl(label_text, 10, "rgba(150,185,255,0.75)", bold=True, spacing=1.5))
    lay.addWidget(widget)
    if hint:
        lay.addWidget(
            (lambda w: (w.setStyleSheet(w.styleSheet() + " padding-right:10px;"), w)[1])
            (_lbl(hint, 11, "rgba(120,155,255,0.4)"))
        )
    return lay


def _summary_row(label: str, accent=False) -> tuple[QHBoxLayout, CountUpLabel]:
    lay = QHBoxLayout()
    lay.setContentsMargins(0, 6, 0, 6)
    val = CountUpLabel()
    val.setStyleSheet(
        f"color:{'#00e5ff' if accent else '#d8e8ff'}; "
        f"font-size:{'18' if accent else '13'}px; "
        f"font-weight:{'700' if accent else '500'}; "
        f"font-family:{_MONO}; background:transparent; letter-spacing:0.4px;")
    val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    lay.addWidget(_lbl(label, 12, "rgba(150,185,255,0.7)"))
    lay.addStretch()
    lay.addWidget(val)
    return lay, val


# ══════════════════════════════════════════════════════════════════════════════
#  Користувацький інтерфейс
# ══════════════════════════════════════════════════════════════════════════════

class UserInterface(QWidget):
    """
    Єдиний клас View. Створює вікно, підключає віджети та взаємодіє
    виключно через LoanController — бізнес-логіка тут відсутня.
    """

    BP_SMALL  = 820
    BP_MEDIUM = 1050
    app = QApplication(sys.argv)

    app.setStyleSheet(_TOOLTIP)

    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("bankvault.app")

    def __init__(self, controller) -> None:
        super().__init__()
        self._controller = controller
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(120)
        self._resize_timer.timeout.connect(self._on_resize_done)
        self._drag_pos = None
        
        self.setWindowTitle("Loan Calculator | Кредитний калькулятор")
        self.setMinimumSize(700, 600)
        self.resize(1200, 780)
        self.setWindowIcon(QIcon(os.path.join(BASE_DIR, "ico.png")))
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._build_ui()

        # зворотні виклики контролера
        controller.on_success(self._on_calculation_success)
        controller.on_validation_error(self._on_validation_error)

    # ── перетягування вікна ───────────────────────────────────────────────────────────

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and e.y() < 54:
            self._drag_pos = e.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.LeftButton and self._drag_pos:
            self.move(e.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, _):
        self._drag_pos = None

    def resizeEvent(self, e):
        self._bg.setGeometry(0, 0, self.width(), self.height())
        self._apply_responsive_layout()
        self._resize_timer.start()
        super().resizeEvent(e)

    def _on_resize_done(self):
        if self._controller.get_last_schedule():
            self._draw_chart()

    # ── побудова інтерфейсу ───────────────────────────────────────────────────────

    def _build_ui(self):
        self._bg = GradientBackground(self)
        self._bg.setGeometry(0, 0, self.width(), self.height())
        self._bg.lower()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_titlebar())

        self._splitter = QSplitter(Qt.Horizontal)
        self._splitter.setHandleWidth(1)
        self._splitter.setStyleSheet(
            "QSplitter::handle { background:rgba(255,255,255,0.08); }")

        self._left_scroll = LeftScrollArea()
        left_content = QWidget()
        left_content.setStyleSheet("background:transparent;")
        left_content.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self._left_layout = QVBoxLayout(left_content)
        self._left_layout.setContentsMargins(22, 12, 22, 22)
        self._left_layout.setSpacing(12)
        self._build_left_panel(self._left_layout)
        self._left_scroll.setWidget(left_content)
        self._left_scroll.setMinimumWidth(340)
        self._left_scroll.setMaximumWidth(520)

        self._right_panel = self._build_right_panel()
        self._right_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._splitter.addWidget(self._left_scroll)
        self._splitter.addWidget(self._right_panel)
        self._splitter.setStretchFactor(0, 38)
        self._splitter.setStretchFactor(1, 62)
        self._splitter.setSizes([420, 720])

        body = QHBoxLayout()
        body.setContentsMargins(14, 0, 14, 14)
        body.addWidget(self._splitter)
        root.addLayout(body, 1)

    def _build_titlebar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(54)
        bar.setStyleSheet("background:transparent;")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(22, 0, 14, 0)

        col = QVBoxLayout()
        col.setSpacing(1)
        col.addWidget(_lbl("⬡ TrustVault", 13, "rgba(90,160,255,0.9)",
                           bold=True, spacing=2.5))
        col.addWidget(_lbl("Аналітична платформа розрахунку кредитів", 10, "rgba(80,130,255,0.5)"))

        def wc_btn(symbol, hover_bg):
            b = QPushButton(symbol)
            b.setFixedSize(26, 26)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(f"QPushButton {{ background:rgba(255,255,255,0.08); "
                            f"border:none; border-radius:13px; "
                            f"color:rgba(180,210,255,0.7); font-size:12px; }}"
                            f"QPushButton:hover {{ background:{hover_bg}; color:white; }}")
            return b

        min_b = wc_btn("─", "rgba(255,190,40,0.45)")
        cls_b = wc_btn("✕", "rgba(255,70,70,0.50)")
        min_b.clicked.connect(self.showMinimized)
        cls_b.clicked.connect(self.close)
        lay.addLayout(col)
        lay.addStretch()
        lay.addWidget(min_b)
        lay.addSpacing(6)
        lay.addWidget(cls_b)
        return bar

    def _build_left_panel(self, lay: QVBoxLayout):
        CARD_PAD  = 20
        GAP       = 14
        INNER_GAP = 6
        OPT_GAP   = 12

        lay.addWidget(_lbl("Кредитний калькулятор", 24, "#ffffff",
                           bold=True, family="Georgia", spacing=-0.3))
        lay.addSpacing(3)
        lay.addWidget(_lbl("Введіть параметри для отримання детального графіка платежів",
                           12, "rgba(140,175,255,0.6)"))
        lay.addSpacing(12)

        # ── параметри кредиту ──────────────────────────────────────────────
        p_card = GlassCard(radius=14)
        p_lay  = QVBoxLayout(p_card)
        p_lay.setContentsMargins(CARD_PAD, CARD_PAD, CARD_PAD, CARD_PAD)
        p_lay.setSpacing(0)
        p_lay.addWidget(_section_label("ПАРАМЕТРИ КРЕДИТУ"))
        p_lay.addSpacing(10)
        p_lay.addWidget(_divider())
        p_lay.addSpacing(GAP)

        self.inp_amount = StyledInput("250000")
        p_lay.addLayout(_field("СУМА КРЕДИТУ", self.inp_amount, gap=INNER_GAP))
        p_lay.addSpacing(GAP)

        self.inp_rate = StyledInput("5.5")
        p_lay.addLayout(_field("ВІДСОТКОВА СТАВКА (%)", self.inp_rate,
                               hint="Введіть значення від 0 до 100",
                               gap=INNER_GAP))
        p_lay.addSpacing(GAP)

        term_hdr = QHBoxLayout()
        term_hdr.setContentsMargins(0, 0, 0, 0)
        self._term_lbl = _lbl("СТРОК КРЕДИТУВАННЯ", 10, "rgba(150,185,255,0.75)",
                               bold=True, spacing=1.5)
        self.toggle_term = ToggleSwitch("Роки", "Місяці")
        self.toggle_term.toggled.connect(
            lambda s: self._term_lbl.setText(
                "СТРОК КРЕДИТУВАННЯ" if s else "СТРОК КРЕДИТУВАННЯ"))
        term_hdr.addWidget(self._term_lbl)
        term_hdr.addStretch()
        term_hdr.addWidget(self.toggle_term)
        self.inp_term = StyledInput("10")
        term_block = QVBoxLayout()
        term_block.setContentsMargins(0, 0, 0, 0)
        term_block.setSpacing(INNER_GAP)
        term_block.addLayout(term_hdr)
        term_block.addWidget(self.inp_term)
        p_lay.addLayout(term_block)
        p_lay.addSpacing(GAP)

        p_lay.addWidget(_lbl("ТИП ПЛАТЕЖІВ", 10, "rgba(150,185,255,0.75)",
                             bold=True, spacing=1.5))
        p_lay.addSpacing(INNER_GAP)
        _rb_ss = (f"QRadioButton {{ color:#e8f0ff; font-size:13px; "
                  f"font-family:{_SANS}; spacing:8px; }}"
                  f"QRadioButton::indicator {{ width:15px; height:15px; "
                  f"border-radius:8px; border:2px solid rgba(100,160,255,0.5); "
                  f"background:transparent; }}"
                  f"QRadioButton::indicator:checked {{ background:#1e6fff; "
                  f"border:2px solid #00c6ff; }}")
        self.rb_annuity = QRadioButton("Ануїтетний")
        self.rb_diff    = QRadioButton("Диференційований")
        for rb in (self.rb_annuity, self.rb_diff):
            rb.setStyleSheet(_rb_ss)
        self.rb_annuity.setChecked(True)
        self._type_grp = QButtonGroup(self)
        self._type_grp.addButton(self.rb_annuity, 0)
        self._type_grp.addButton(self.rb_diff, 1)
        type_row = QHBoxLayout()
        type_row.setSpacing(24)
        type_row.setContentsMargins(0, 5, 0, 0)
        type_row.addWidget(self.rb_annuity)
        type_row.addWidget(self.rb_diff)
        type_row.addStretch()
        p_lay.addLayout(type_row)
        lay.addWidget(p_card)
        lay.addSpacing(12)

        # ── додаткові параметри ──────────────────────────────────────────
        CB_W = 130

        def opt_row(cb_text, *inputs):
            cb = CustomCheckBox(cb_text)



            cb.setFixedWidth(CB_W)
            cb.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            for inp in inputs:
                inp.setEnabled(False)
                inp.setFixedHeight(42)
            cb.toggled.connect(lambda v, ins=inputs: [i.setEnabled(v) for i in ins])
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(10)
            row.addWidget(cb)
            for inp in inputs:
                row.addWidget(inp, 1)
            return row, cb

        o_card = GlassCard(radius=14)
        o_lay  = QVBoxLayout(o_card)
        o_lay.setContentsMargins(CARD_PAD, CARD_PAD, CARD_PAD, CARD_PAD)
        o_lay.setSpacing(0)
        o_lay.addWidget(_section_label("ДОДАТКОВІ ПАРАМЕТРИ"))
        o_lay.addSpacing(10)
        o_lay.addWidget(_divider())
        o_lay.addSpacing(OPT_GAP)

        self.inp_down    = StyledInput("50000")
        self.inp_comm    = StyledInput("1000")
        self.inp_early   = StyledInput("Сума (2000)")
        self.inp_early_m = StyledInput("У місяці (3)")

        self.inp_early.setObjectName("smallInput")
        self.inp_early_m.setObjectName("smallInput2")

        r1, self.cb_down  = opt_row("Початковий внесок",    self.inp_down)
        r2, self.cb_comm  = opt_row("Commission ($)",      self.inp_comm)
        r3, self.cb_early = opt_row("Достроковий платіж", self.inp_early, self.inp_early_m)

        attach_tooltip(self.cb_down, "Початковий внесок")
        attach_tooltip(self.cb_early, "Достроковий платіж")
        

        o_lay.addLayout(r1)
        o_lay.addSpacing(OPT_GAP)
        o_lay.addLayout(r3)
        lay.addWidget(o_card)
        lay.addSpacing(12)

        # ── кнопки ────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.setContentsMargins(0, 0, 0, 0)
        self.btn_calc  = GradientButton("РОЗРАХУВАТИ")
        self.btn_reset = GradientButton("—", primary=False)
        self.btn_calc.setFixedHeight(46)
        self.btn_reset.setFixedHeight(46)
        self.btn_reset.setFixedWidth(76)
        self.btn_reset.setMaximumWidth(110)
        self.btn_calc.clicked.connect(self._on_calculate_clicked)
        self.btn_reset.clicked.connect(self._on_reset_clicked)
        btn_row.addWidget(self.btn_calc, 1)
        btn_row.addWidget(self.btn_reset)
        lay.addLayout(btn_row)

        self.lbl_error = _lbl("", 12, "#ff6b8a", wrap=True)
        self.lbl_error.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.lbl_error)

        # ── картка підсумку платежів ──────────────────────────────────────────────
        self.summary_card = FadeInCard(radius=14, alpha0=25, alpha1=10)
        self.summary_card.setVisible(False)
        s_lay = QVBoxLayout(self.summary_card)
        s_lay.setContentsMargins(CARD_PAD, 18, CARD_PAD, 20)
        s_lay.setSpacing(0)
        s_lay.addWidget(_section_label("ПІДСУМОК ПЛАТЕЖІВ"))
        s_lay.addSpacing(8)
        s_lay.addWidget(_divider())
        s_lay.addSpacing(10)

        r_monthly,  self.val_monthly  = _summary_row("Щомісячний платіж", accent=True)
        r_total,    self.val_total    = _summary_row("Загальна сума виплат")
        r_interest, self.val_interest = _summary_row("Загальна сума відсотків")
        r_effect,   self.val_effect   = _summary_row("Фактична вартість (з комісіями)")
        r_months,   self.val_months   = _summary_row("Кількість місяців")

        s_lay.addLayout(r_monthly)
        s_lay.addWidget(_summary_divider())
        s_lay.addLayout(r_total)
        s_lay.addLayout(r_interest)
        s_lay.addWidget(_summary_divider())
        s_lay.addLayout(r_effect)
        s_lay.addLayout(r_months)

        lay.addSpacing(4)
        lay.addWidget(self.summary_card)
        lay.addStretch(1)

    def _build_right_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(4, 12, 4, 4)
        lay.setSpacing(0)
        self._tabs = AnimatedTabWidget()

        chart_page = QWidget()
        chart_page.setStyleSheet("background:transparent;")
        c_lay = QVBoxLayout(chart_page)
        c_lay.setContentsMargins(8, 6, 8, 8)
        c_lay.setSpacing(8)
        self.chart_view = ResponsiveChartView()
        c_lay.addWidget(self.chart_view, 1)
        exp_row = QHBoxLayout()
        exp_row.addStretch()
        self.btn_export_chart = GradientButton("ЕКСПОРТ У PNG  ⭣", primary=False)
        self.btn_export_chart.setFixedWidth(200)
        self.btn_export_chart.setMinimumHeight(36)
        self.btn_export_chart.setMaximumHeight(36)
        self.btn_export_chart.setEnabled(False)
        self.btn_export_chart.clicked.connect(self._on_export_chart)
        exp_row.addWidget(self.btn_export_chart)
        c_lay.addLayout(exp_row)

        table_page = QWidget()
        table_page.setStyleSheet("background:transparent;")
        t_lay = QVBoxLayout(table_page)
        t_lay.setContentsMargins(8, 6, 8, 8)
        t_lay.setSpacing(8)
        self.table = QTableWidget()
        self.table.setStyleSheet(_TABLE_SS)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Місяць", "Залишок боргу", "Тіло кредиту", "Відсотки", "Платіж"])
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.Stretch)
        hdr.setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(False)
        self.table.setSortingEnabled(True)
        t_lay.addWidget(self.table, 1)
        texp_row = QHBoxLayout()
        texp_row.addStretch()
        self.btn_export_table = GradientButton("ЕКСПОРТ У CSV  ⭣", primary=False)
        self.btn_export_table.setFixedWidth(200)
        self.btn_export_table.setMinimumHeight(36)
        self.btn_export_table.setMaximumHeight(36)
        self.btn_export_table.setEnabled(False)
        self.btn_export_table.clicked.connect(self._on_export_table)
        texp_row.addWidget(self.btn_export_table)
        t_lay.addLayout(texp_row)

        self._tabs.add_tab(table_page,  "ГРАФІК ПОГАШЕННЯ")
        self._tabs.add_tab(chart_page,  "ВІЗУАЛІЗАЦІЯ")
        lay.addWidget(self._tabs, 1)
        return panel

    # ── адаптивне компонування ─────────────────────────────────────────────────────

    def _apply_responsive_layout(self):
        w = self.width()
        if w < self.BP_SMALL:
            if self._splitter.orientation() != Qt.Vertical:
                self._splitter.setOrientation(Qt.Vertical)
                self._left_scroll.setMaximumWidth(99999)
        else:
            if self._splitter.orientation() != Qt.Horizontal:
                self._splitter.setOrientation(Qt.Horizontal)
                self._left_scroll.setMaximumWidth(520)
            ratio = 0.44 if w < self.BP_MEDIUM else 0.37
            self._splitter.setSizes([int(w * ratio), int(w * (1 - ratio))])

    # ── обробники подій контролера (викликаються LoanController) ─────────────────

    def _on_calculation_success(self, loan: Loan, schedule: PaymentSchedule):
        logger.debug("View received calculation success")
        self._clear_all_errors()
        self.lbl_error.setText("")

        effective_cost = schedule.total_payment + loan.commission
        self.val_monthly.animate_to(schedule.first_payment)
        self.val_total.animate_to(schedule.total_payment)
        self.val_interest.animate_to(schedule.total_interest)
        self.val_effect.animate_to(effective_cost)
        self.val_months.animate_to(schedule.month_count, prefix="", decimals=0)
        self.summary_card.reveal()

        self._fill_table(schedule)
        self._tabs.force_current(0)
        QTimer.singleShot(0, self._render_chart_first_pass)

        self.btn_export_chart.setEnabled(True)
        self.btn_export_table.setEnabled(True)

    def _on_validation_error(self, field: str, message: str):
        logger.debug("View received validation error: field=%s", field)
        self.lbl_error.setText(f"⚠  {message}")
        self.summary_card.setVisible(False)
        self._mark_error_field(field)

    # ── обробники дій користувача (підключені в _build_left_panel) ─────────────────────

    def _scroll_to_bottom(self):
        bar = self._left_scroll.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _on_calculate_clicked(self):
        self.btn_calc.setDisabled(True)

        self._clear_all_errors()

        form = LoanFormData(
            amount         = self.inp_amount.text(),
            rate           = self.inp_rate.text(),
            term           = self.inp_term.text(),
            term_in_months = self.toggle_term.state() == 1,
            loan_type      = (LoanType.DIFFERENTIATED
                              if self._type_grp.checkedId() == 1
                              else LoanType.ANNUITY),
            down_payment   = self.inp_down.text(),
            down_enabled   = self.cb_down.isChecked(),
            commission     = self.inp_comm.text(),
            comm_enabled   = self.cb_comm.isChecked(),
            early_amount   = self.inp_early.text(),
            early_month    = self.inp_early_m.text(),
            early_enabled  = self.cb_early.isChecked(),
        )
        self._controller.calculate(form)

        QTimer.singleShot(0, self._scroll_to_bottom)
        QTimer.singleShot(2000, lambda: self.btn_calc.setDisabled(False))


    def _on_reset_clicked(self):
        self._controller.reset()
        for inp in (self.inp_amount, self.inp_rate, self.inp_term,
                    self.inp_down, self.inp_comm, self.inp_early, self.inp_early_m):
            inp.clear()
            inp.clear_error()
        self.lbl_error.setText("")
        self.summary_card.setVisible(False)
        self.table.setRowCount(0)
        self.chart_view.clear_chart()
        self.btn_export_chart.setEnabled(False)
        self.btn_export_table.setEnabled(False)
        self.rb_annuity.setChecked(True)
        for cb in (self.cb_down, self.cb_comm, self.cb_early):
            cb.setChecked(False)

    def _on_export_chart(self):
        pix = self.chart_view.full_pixmap()
        if pix is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Експорт візуалізації",
            f"loan_chart_{datetime.now():%Y%m%d_%H%M%S}.png",
            "PNG Image (*.png)")
        if path:
            pix.save(path, "PNG")
            logger.info("Графік збережений за шляхом %s", path)

    def _on_export_table(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Експорт таблиці платежів",
            f"loan_table_{datetime.now():%Y%m%d_%H%M%S}.csv",
            "CSV Files (*.csv)")
        if path:
            self._controller.export_schedule_csv(path)

    # ── допоміжні функції побудови графіків ─────────────────────────────────────────────────

    def _render_chart_first_pass(self):
        self._draw_chart()
        QTimer.singleShot(120, self._draw_chart)

    def _draw_chart(self):
        schedule = self._controller.get_last_schedule()
        if not schedule:
            return
        cw = self.chart_view.width()
        ch = self.chart_view.height()
        if cw < 100 or ch < 100:
            cw, ch = 700, 440
        dpi   = 110
        fig_w = max(4.5, (cw - 32) / dpi)
        fig_h = max(2.8, (ch - 32) / dpi)
        try:
            fig = self._controller.get_chart_generator().render(schedule, fig_w, fig_h)
            self.chart_view.load_figure(fig)
        except Exception as exc:
            self.chart_view.set_error(str(exc))

    # ── допоміжна функція для таблиці ──────────────────────────────────────────────────────────

    def _fill_table(self, schedule: PaymentSchedule):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        for i, pmt in enumerate(schedule):
            row = self.table.rowCount()
            self.table.insertRow(row)
            vals   = [str(pmt.month),
                      f"{pmt.remaining_balance:,.2f}",
                      f"{pmt.principal_part:,.2f}",
                      f"{pmt.interest_part:,.2f}",
                      f"{pmt.total_payment:,.2f}"]
            aligns = [Qt.AlignCenter,
                      Qt.AlignRight | Qt.AlignVCenter,
                      Qt.AlignRight | Qt.AlignVCenter,
                      Qt.AlignRight | Qt.AlignVCenter,
                      Qt.AlignRight | Qt.AlignVCenter]
            bg = QColor(255, 255, 255, 7) if i % 2 == 0 else QColor(0, 0, 0, 0)
            for col, (v, a) in enumerate(zip(vals, aligns)):
                item = QTableWidgetItem(v)
                item.setTextAlignment(a)
                item.setBackground(bg)
                self.table.setItem(row, col, item)
        self.table.setSortingEnabled(True)

    # ── функції для обробки помилок ─────────────────────────────────────────────────────────

    _FIELD_TO_WIDGET = None   # заповнюється після створення віджетів

    def _input_map(self) -> dict[str, StyledInput]:
        return {
            "amount":       self.inp_amount,
            "rate":         self.inp_rate,
            "term":         self.inp_term,
            "down_payment": self.inp_down,
            "commission":   self.inp_comm,
            "early_amount": self.inp_early,
            "early_month":  self.inp_early_m,
        }

    def _mark_error_field(self, field: str):
        inp = self._input_map().get(field)
        if inp:
            inp.mark_error()

    def _clear_all_errors(self):
        for inp in self._input_map().values():
            inp.clear_error()
