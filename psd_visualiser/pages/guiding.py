"""Exact Kepler motion and the first-order guiding-centre construction.

The main diagram is transformed as a single physical construction when the
reference frame is changed. The small panel always uses radial/tangential
coordinates about G, making the retrograde epicycle easy to inspect.
"""

from __future__ import annotations

from time import perf_counter

import numpy as np
from matplotlib.ticker import MaxNLocator
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from psd_visualiser.models.guiding import (
    first_order_relative,
    from_guiding_frame,
    guiding_centre,
    kepler_position,
    signed_angle,
    solve_kepler,
    to_guiding_frame,
    true_anomaly,
)
from psd_visualiser.widgets import (
    BLUE,
    GREEN,
    MUTED,
    ORANGE,
    PURPLE,
    TEXT,
    PlotPanel,
    SliderControl,
    note,
    section_title,
)


class GuidingPage(QWidget):
    """Interactive, dimensionless two-body orbit with a = 1."""

    PERIOD_SECONDS = 12.0
    DEFAULT_PHASE = 45.0

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._cycle = np.linspace(0.0, 2.0 * np.pi, 481)
        self._mean_anomaly = np.deg2rad(self.DEFAULT_PHASE)
        self._last_tick = perf_counter()
        self._cached_e = None
        self._lines = {}
        self._labels = {}

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(16)
        controls = QWidget()
        controls.setMaximumWidth(310)
        side = QVBoxLayout(controls)
        side.setContentsMargins(12, 12, 12, 12)
        side.setSpacing(14)
        side.addWidget(section_title("Guiding centre"))
        side.addWidget(note("A Kepler orbit viewed from a point G moving uniformly on a circle of radius a = 1."))
        self.eccentricity = SliderControl("Eccentricity e", 0, 0.5, 0.2, step=0.01, decimals=2)
        self.phase = SliderControl("Mean anomaly M", 0, 360, self.DEFAULT_PHASE, step=0.1, decimals=1, suffix="°")
        side.addWidget(self.eccentricity)
        side.addWidget(self.phase)

        buttons = QHBoxLayout()
        self.start_button = QPushButton("Start animation")
        self.start_button.setObjectName("primary")
        self.reset_button = QPushButton("Reset")
        buttons.addWidget(self.start_button, 1)
        buttons.addWidget(self.reset_button)
        side.addLayout(buttons)

        self.rotating = QCheckBox("Change to rotating reference frame")
        self.show_e = QCheckBox("Show eccentric anomaly construction")
        side.addWidget(self.rotating)
        side.addWidget(self.show_e)
        self.readout = QLabel()
        self.readout.setWordWrap(True)
        self.readout.setTextFormat(Qt.TextFormat.RichText)
        side.addWidget(self.readout)
        side.addWidget(section_title("How to read the diagram"))
        side.addWidget(note("M follows G at a constant rate. True anomaly f follows the exact particle P. The signed angle f − M is the equation of centre."))
        side.addWidget(note("The smaller panel always looks from G: x is radially outwards, y is prograde. Motion around G is retrograde."))
        side.addWidget(note("First order in small e:\nx = −ae cos M\ny = 2ae sin M\nThe approximation is less accurate as e grows."))
        self.circular_note = note("")
        side.addWidget(self.circular_note)
        side.addStretch()
        side.addWidget(note("Murray & Dermott · §2.6, pp. 42–45\nTremaine · §1.8.2"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setWidget(controls)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setMinimumWidth(315)
        scroll.setMaximumWidth(325)
        layout.addWidget(scroll)

        self.plot = PlotPanel()
        self.plot.figure.clear()
        self.plot.figure.set_layout_engine(None)
        grid = self.plot.figure.add_gridspec(1, 2, width_ratios=(1.75, 1.0), wspace=0.25)
        self.axes = self.plot.figure.add_subplot(grid[0, 0])
        self.relative_axes = self.plot.figure.add_subplot(grid[0, 1])
        self.plot.axes = self.axes
        self.plot.figure.subplots_adjust(left=0.065, right=0.965, bottom=0.15, top=0.87)
        layout.addWidget(self.plot, 1)
        self._create_artists()

        self.timer = QTimer(self)
        self.timer.setInterval(33)
        self.timer.timeout.connect(self._tick)
        self.eccentricity.valueChanged.connect(self._redraw)
        self.phase.valueChanged.connect(self._phase_changed)
        self.rotating.toggled.connect(self._redraw)
        self.show_e.toggled.connect(self._redraw)
        self.start_button.clicked.connect(self._toggle_animation)
        self.reset_button.clicked.connect(self.reset)
        self._redraw()

    def _create_artists(self):
        for ax in (self.axes, self.relative_axes):
            ax.set_aspect("equal", adjustable="box")
            ax.set_facecolor("#ffffff")
            ax.tick_params(labelsize=8, colors=MUTED)
            ax.xaxis.set_major_locator(MaxNLocator(5))
            ax.yaxis.set_major_locator(MaxNLocator(5))
            ax.grid(True, color="#e8edf3", linewidth=0.65)
            for spine in ax.spines.values():
                spine.set_color("#d5dfe8")
        self.axes.set_xlabel("x / a", fontsize=9, color=MUTED)
        self.axes.set_ylabel("y / a", fontsize=9, color=MUTED)
        self.relative_axes.set_xlabel("radial x / a", fontsize=9, color=MUTED)
        self.relative_axes.set_ylabel("tangential y / a", fontsize=9, color=MUTED)
        self.relative_axes.set_title("Motion relative to G", fontsize=11, color=TEXT, pad=14)

        def line(key, ax, **kwargs):
            self._lines[key], = ax.plot([], [], **kwargs)

        line("orbit", self.axes, color=BLUE, linewidth=2.0, label="Exact Kepler orbit")
        line("circle", self.axes, color=GREEN, linewidth=1.2, linestyle=":", label="Guiding-centre circle")
        line("approx_orbit", self.axes, color=ORANGE, linewidth=1.2, linestyle="--", alpha=0.8)
        line("reference", self.axes, color=MUTED, linewidth=1, linestyle="--")
        line("fg", self.axes, color=GREEN, linewidth=1.1, alpha=0.65)
        line("fp", self.axes, color=BLUE, linewidth=1.1, alpha=0.65)
        line("gp", self.axes, color=PURPLE, linewidth=1.2)
        line("M", self.axes, color=GREEN, linewidth=2)
        line("f", self.axes, color=BLUE, linewidth=2)
        line("delta", self.axes, color=PURPLE, linewidth=2)
        line("aux_circle", self.axes, color=ORANGE, linewidth=1.0, alpha=0.5)
        line("aux_projection", self.axes, color=ORANGE, linewidth=1, linestyle=":")
        line("cq", self.axes, color=ORANGE, linewidth=1)
        line("c_ref", self.axes, color=ORANGE, linewidth=1, linestyle=":")
        line("E", self.axes, color=ORANGE, linewidth=2)
        line("focus", self.axes, color=TEXT, marker="o", markersize=9, zorder=8)
        line("particle", self.axes, color=BLUE, marker="o", markersize=7, zorder=10)
        line("guiding", self.axes, color=GREEN, marker="o", markersize=7, markerfacecolor="white", markeredgewidth=2, zorder=9)
        line("approx", self.axes, color=ORANGE, marker="x", markersize=10, markeredgewidth=2, zorder=11)
        line("centre", self.axes, color=ORANGE, marker="+", markersize=7, zorder=9)
        line("aux_point", self.axes, color=ORANGE, marker="o", markersize=5, zorder=9)

        line("relative_exact", self.relative_axes, color=BLUE, linewidth=2, label="Exact relative path")
        line("relative_approx", self.relative_axes, color=ORANGE, linewidth=1.6, linestyle="--", label="First-order epicycle")
        line("relative_g", self.relative_axes, color=GREEN, marker="o", markersize=6, markerfacecolor="white", markeredgewidth=1.5)
        line("relative_p", self.relative_axes, color=BLUE, marker="o", markersize=7, zorder=8)
        line("relative_a", self.relative_axes, color=ORANGE, marker="x", markersize=10, markeredgewidth=2, zorder=9)

        for key, color in (("F", TEXT), ("P", BLUE), ("G", GREEN), ("M", GREEN), ("f", BLUE), ("delta", PURPLE), ("E", ORANGE), ("C", ORANGE), ("Q", ORANGE), ("ref", MUTED)):
            self._labels[key] = self.axes.text(0, 0, "", color=color, fontsize=10, ha="center", va="center", zorder=15,
                                              bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.8, "pad": 0.6})
        self.relative_axes.annotate("G", (0, 0), xytext=(7, -12), textcoords="offset points", color=GREEN, fontsize=10)
        self.axes.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), frameon=False, fontsize=8)
        self.relative_axes.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), frameon=False, fontsize=8)

    def _phase_changed(self, value):
        self._mean_anomaly = np.deg2rad(value)
        self._last_tick = perf_counter()
        self._redraw()

    def _toggle_animation(self):
        if self.timer.isActive():
            self._pause()
        else:
            self._last_tick = perf_counter()
            self.timer.start()
            self.start_button.setText("Pause")

    def _pause(self):
        self.timer.stop()
        self.start_button.setText("Start animation")

    def _tick(self):
        now = perf_counter()
        elapsed = now - self._last_tick
        self._last_tick = now
        self._mean_anomaly = (self._mean_anomaly + elapsed * 2 * np.pi / self.PERIOD_SECONDS) % (2 * np.pi)
        self.phase.blockSignals(True)
        self.phase.set_value(float(np.rad2deg(self._mean_anomaly)))
        self.phase.blockSignals(False)
        self._redraw()

    def on_leave(self):
        """A hidden page must never keep its animation running."""
        self._pause()

    def on_enter(self):
        """Keep the previous phase and controls when revisiting the page."""

    def reset(self):
        self._pause()
        for control, value in ((self.eccentricity, 0.2), (self.phase, self.DEFAULT_PHASE)):
            control.blockSignals(True)
            control.set_value(value)
            control.blockSignals(False)
        self.rotating.blockSignals(True)
        self.rotating.setChecked(False)
        self.rotating.blockSignals(False)
        self.show_e.blockSignals(True)
        self.show_e.setChecked(False)
        self.show_e.blockSignals(False)
        self._mean_anomaly = np.deg2rad(self.DEFAULT_PHASE)
        self._redraw()

    def _set_line(self, key, points):
        points = np.asarray(points, dtype=float).reshape(-1, 2)
        self._lines[key].set_data(points[:, 0], points[:, 1])

    def _display(self, points):
        if self.rotating.isChecked():
            return to_guiding_frame(points, self._mean_anomaly)
        return np.asarray(points)

    def _main_line(self, key, points):
        self._set_line(key, self._display(points))

    def _label(self, key, position, text, offset=(0.0, 0.0)):
        position = self._display(np.asarray(position)) + np.asarray(offset)
        self._labels[key].set_position(position)
        self._labels[key].set_text(text)
        self._labels[key].set_visible(bool(text))

    def _angle(self, key, start, angle, radius, label, origin=None):
        origin = np.zeros(2) if origin is None else np.asarray(origin)
        visible = abs(angle) > 0.008
        theta = np.linspace(start, start + angle, max(4, int(abs(angle) * 24)))
        points = origin + radius * np.column_stack((np.cos(theta), np.sin(theta)))
        self._main_line(key, points)
        self._lines[key].set_visible(visible)
        mid = start + angle / 2
        self._label(key, origin + (radius + 0.06) * np.array([np.cos(mid), np.sin(mid)]), label if visible else "")

    def _update_curves(self, eccentricity):
        if eccentricity == self._cached_e:
            return
        self._cached_e = eccentricity
        self._orbit = kepler_position(self._cycle, eccentricity)
        self._guiding_circle = guiding_centre(self._cycle)
        self._relative_curve = to_guiding_frame(self._orbit, self._cycle)
        self._epicycle = first_order_relative(self._cycle, eccentricity)
        self._approx_curve = from_guiding_frame(self._epicycle, self._cycle)
        self._set_line("relative_exact", self._relative_curve)
        self._set_line("relative_approx", self._epicycle)
        self._set_line("relative_g", [[0, 0]])
        limit = max(0.12, 2.5 * eccentricity)
        self.relative_axes.set_xlim(-limit, limit)
        self.relative_axes.set_ylim(-limit, limit)

    def _redraw(self, *_):
        e = self.eccentricity.value()
        mean = self._mean_anomaly
        self._update_curves(e)
        E = float(solve_kepler(mean, e))
        f = float(true_anomaly(E, e))
        if mean > np.pi and f < 1e-10:
            f = 2 * np.pi
        delta = float(signed_angle(f - mean))
        p = kepler_position(mean, e)
        g = guiding_centre(mean)
        approximate_relative = first_order_relative(mean, e)
        approximate = from_guiding_frame(approximate_relative, mean)

        self._main_line("orbit", self._orbit)
        self._main_line("circle", self._guiding_circle)
        self._main_line("approx_orbit", self._approx_curve)
        self._main_line("reference", [[0, 0], [1.26, 0]])
        self._main_line("fg", [[0, 0], g])
        self._main_line("fp", [[0, 0], p])
        self._main_line("gp", [g, p])
        self._main_line("focus", [[0, 0]])
        self._main_line("particle", [p])
        self._main_line("guiding", [g])
        self._main_line("approx", [approximate])
        self._angle("M", 0, mean, 0.23, "M")
        self._angle("f", 0, f, 0.36, "f")
        self._angle("delta", mean, delta, 0.52, "f − M")
        self._label("F", [0, 0], "F", offset=(-0.07, -0.1))
        self._label("P", p, "P" if e > 1e-8 else "P = G", offset=(0.0, 0.13))
        self._label("G", g, "G" if e > 1e-8 else "", offset=(0.08, -0.13))
        self._label("ref", [1.30, 0], "periapsis\ndirection", offset=(0, 0.12))

        centre = np.array([-e, 0.0])
        auxiliary_point = centre + np.array([np.cos(E), np.sin(E)])
        auxiliary_circle = centre + np.column_stack((np.cos(self._cycle), np.sin(self._cycle)))
        self._main_line("aux_circle", auxiliary_circle)
        self._main_line("aux_projection", [auxiliary_point, p])
        self._main_line("cq", [centre, auxiliary_point])
        self._main_line("c_ref", [centre, centre + [0.38, 0]])
        self._main_line("centre", [centre])
        self._main_line("aux_point", [auxiliary_point])
        self._angle("E", 0, E, 0.16, "E", origin=centre)
        self._label("C", centre, "C", offset=(0.0, -0.14))
        self._label("Q", auxiliary_point, "Q", offset=(0.0, 0.16))
        for key in ("aux_circle", "aux_projection", "cq", "c_ref", "centre", "aux_point"):
            self._lines[key].set_visible(self.show_e.isChecked())
        self._lines["E"].set_visible(self.show_e.isChecked() and abs(E) > 0.008)
        for key in ("C", "Q", "E"):
            self._labels[key].set_visible(self.show_e.isChecked() and (key != "E" or abs(E) > 0.008))

        relative_particle = to_guiding_frame(p, mean)
        self._set_line("relative_p", [relative_particle])
        self._set_line("relative_a", [approximate_relative])
        if self.rotating.isChecked():
            self.axes.set_xlim(-2.7, 2.7)
            self.axes.set_ylim(-2.7, 2.7)
            self.axes.set_title("Frame rotating with G", fontsize=12, color=TEXT, pad=14)
        else:
            self.axes.set_xlim(-1.85, 1.65)
            self.axes.set_ylim(-1.75, 1.75)
            self.axes.set_title("Inertial frame · fixed periapsis", fontsize=12, color=TEXT, pad=14)

        error = np.linalg.norm(relative_particle - approximate_relative)
        self.readout.setText(
            f"<b>M</b> = {np.rad2deg(mean):.1f}° &nbsp; "
            f"<b>f</b> = {np.rad2deg(f):.1f}°<br>"
            f"<b>f − M</b> = {np.rad2deg(delta):+.1f}°<br>"
            f"<b>E</b> = {np.rad2deg(E):.1f}°<br>"
            f"First-order position error: {error:.4f} a"
        )
        self.circular_note.setText(
            "At e = 0, P and G coincide. The epicycle collapses to a point; the periapsis direction is conventional."
            if e < 1e-8 else
            "Blue: exact P. Orange ×: first-order particle. Dashed orange: first-order path."
        )
        self.plot.canvas.draw_idle()
