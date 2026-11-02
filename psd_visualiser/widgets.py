"""Small reusable Qt controls and Matplotlib styling."""

import math

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDoubleSpinBox, QHBoxLayout, QLabel, QSizePolicy, QSlider,
    QVBoxLayout, QWidget,
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

BLUE = "#2263a6"
ORANGE = "#d07819"
GREEN = "#16806a"
PURPLE = "#8652a3"
TEXT = "#23364a"
MUTED = "#64748b"


def section_title(text):
    label = QLabel(text)
    label.setObjectName("sectionTitle")
    label.setWordWrap(True)
    return label


def note(text):
    label = QLabel(text)
    label.setObjectName("note")
    label.setWordWrap(True)
    label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    return label


class SliderControl(QWidget):
    """Slider with a synchronised, keyboard-editable numeric value."""

    valueChanged = Signal(float)

    def __init__(self, label, minimum, maximum, default, step=1.0,
                 decimals=0, suffix="", parent=None):
        super().__init__(parent)
        self.minimum, self.maximum, self.step, self.default = minimum, maximum, step, default
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, round((maximum - minimum) / step))
        self.slider.setAccessibleName(label)
        self.spin = QDoubleSpinBox()
        self.spin.setRange(minimum, maximum)
        self.spin.setDecimals(decimals)
        self.spin.setSingleStep(step)
        self.spin.setSuffix(suffix)
        self.spin.setKeyboardTracking(False)
        self.spin.setAccessibleName(label + " value")
        self.spin.setMinimumWidth(84)
        self.spin.setMaximumWidth(106)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        top = QHBoxLayout()
        title = QLabel(label)
        title.setBuddy(self.spin)
        top.addWidget(title, 1)
        top.addWidget(self.spin)
        layout.addLayout(top)
        layout.addWidget(self.slider)
        self.slider.valueChanged.connect(self._from_slider)
        self.spin.valueChanged.connect(self._from_spin)
        self.set_value(default)

    def value(self):
        return self.spin.value()

    def set_value(self, value):
        if not math.isfinite(value):
            raise ValueError("Slider value must be finite")
        self.spin.setValue(value)
        self._sync_slider()

    def _sync_slider(self):
        blocked = self.slider.blockSignals(True)
        self.slider.setValue(round((self.value() - self.minimum) / self.step))
        self.slider.blockSignals(blocked)

    def _from_slider(self, position):
        self.spin.setValue(self.minimum + position * self.step)

    def _from_spin(self, value):
        self._sync_slider()
        self.valueChanged.emit(value)


class PlotPanel(QWidget):
    """Embedded Matplotlib canvas. Pages may replace or add axes."""

    def __init__(self, projection=None, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(8, 6), facecolor="white", layout="constrained")
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.canvas.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.axes = self.figure.add_subplot(111, projection=projection)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        self.setMinimumWidth(440)


def style_3d(axes, extent, xlabel="x", ylabel="y", zlabel="z"):
    """Apply a quiet, equal-aspect reference cube."""
    axes.set(xlim=(-extent, extent), ylim=(-extent, extent), zlim=(-extent, extent),
             xlabel=xlabel, ylabel=ylabel, zlabel=zlabel)
    axes.set_box_aspect((1, 1, 1))
    axes.tick_params(labelsize=8, colors=MUTED, pad=1)
    for axis in (axes.xaxis, axes.yaxis, axes.zaxis):
        axis.set_pane_color((0.97, 0.98, 0.99, 0.5))
        axis.label.set_color(MUTED)
    axes.grid(True, alpha=0.25)
