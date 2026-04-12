from PyQt6.QtCore import QPropertyAnimation, QRectF, Qt, pyqtProperty, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPainterPath
from PyQt6.QtWidgets import QWidget


class ToggleSwitch(QWidget):
    toggled = pyqtSignal(bool)

    _OFF_TRACK = QColor("#3a4150")
    _ON_TRACK = QColor("#e8a838")
    _KNOB = QColor("#e8e0d5")

    def __init__(self, parent=None):
        super().__init__(parent)
        self._checked = False
        self._pos = 0.0  # 0.0 = off, 1.0 = on

        self._anim = QPropertyAnimation(self, b"pos_value", self)
        self._anim.setDuration(150)

        self.setFixedSize(40, 22)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    # --- public API (drop-in for QCheckBox) ---

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool) -> None:
        if self._checked == checked:
            return
        self._checked = checked
        self._animate_to(1.0 if checked else 0.0)

    # --- animated property ---

    @pyqtProperty(float)
    def pos_value(self) -> float:
        return self._pos

    @pos_value.setter
    def pos_value(self, value: float) -> None:
        self._pos = value
        self.update()

    # --- interaction ---

    def mousePressEvent(self, event) -> None:
        self._checked = not self._checked
        self._animate_to(1.0 if self._checked else 0.0)
        self.toggled.emit(self._checked)

    def _animate_to(self, target: float) -> None:
        self._anim.stop()
        self._anim.setStartValue(self._pos)
        self._anim.setEndValue(target)
        self._anim.start()

    # --- painting ---

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        t = self._pos

        # Interpolate track colour off → on
        off, on = self._OFF_TRACK, self._ON_TRACK
        track = QColor(
            int(off.red()   + (on.red()   - off.red())   * t),
            int(off.green() + (on.green() - off.green()) * t),
            int(off.blue()  + (on.blue()  - off.blue())  * t),
        )

        # Track (rounded pill)
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), h / 2, h / 2)
        p.fillPath(path, track)

        # Knob
        margin = 2
        knob_d = h - margin * 2
        travel = w - knob_d - margin * 2
        kx = margin + travel * t
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self._KNOB)
        p.drawEllipse(QRectF(kx, margin, knob_d, knob_d))

        p.end()
