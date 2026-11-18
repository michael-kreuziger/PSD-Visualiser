"""Tadpole and horseshoe motion in the planar circular restricted problem."""

from __future__ import annotations

from collections import OrderedDict
from time import perf_counter

import numpy as np
from matplotlib.lines import Line2D
from matplotlib.transforms import Affine2D
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QVBoxLayout, QWidget,
)

from psd_visualiser.models.coorbital import (
    ROUTH_MU, checked_example, effective_potential, integrate_orbit, lagrange_points, recommended_angle_range,
    osculating_eccentricity, rotating_to_inertial,
)
from psd_visualiser.widgets import (
    BLUE, GREEN, MUTED, ORANGE, PURPLE, TEXT, PlotPanel, SliderControl,
    note, section_title,
)


class CoorbitalPage(QWidget):
    """Numerical CR3BP orbits; both views have the barycentre at the origin."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cache = OrderedDict()
        self.trajectory = None
        self._contours = []
        self._grid_mu = None
        self._progress = 0.0
        self._last_tick = perf_counter()
        self._checked_example = None
        self._example_pending = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(16)
        controls = QWidget()
        controls.setMaximumWidth(310)
        side = QVBoxLayout(controls)
        side.setContentsMargins(12, 12, 12, 12)
        side.setSpacing(12)
        side.addWidget(section_title("Tadpole and horseshoe orbits"))
        side.addWidget(note("Planar circular restricted three-body problem: a massless particle feels a star and a planet on circular orbits."))
        self.orbit_selector = QComboBox()
        self.orbit_selector.addItems(["Tadpole initial conditions", "Horseshoe initial conditions"])
        self.orbit_selector.setAccessibleName("Starting-condition family")
        side.addWidget(self.orbit_selector)
        self.centre_selector = QComboBox()
        self.centre_selector.addItems(["L4 · leading", "L5 · trailing"])
        self.centre_selector.setAccessibleName("Tadpole libration centre")
        side.addWidget(self.centre_selector)
        self.auto_example = QCheckBox("Choose family starts automatically")
        self.auto_example.setChecked(True)
        self.auto_example.setToolTip("When μ or the family changes, find a launch checked over several reference times at that same μ and initial eccentricity. Manual longitude and eccentricity edits remain available.")
        side.addWidget(self.auto_example)
        self.example_button = QPushButton("Load checked example at this μ")
        side.addWidget(self.example_button)
        self.example_note = note("Changing μ or family loads a checked start when available. Initial conditions can also be edited freely.")
        side.addWidget(self.example_note)
        self.mass_ratio = SliderControl("Mass ratio log₁₀ μ", -5, -3, -3, step=.05, decimals=4)
        side.addWidget(self.mass_ratio)
        side.addWidget(note("μ = mplanet / (mstar + mplanet).\nThe slider uses a logarithmic scale."))
        self.angle = SliderControl("Starting longitude", 20, 85, 40, step=.001, decimals=3, suffix="°")
        side.addWidget(self.angle)
        self.eccentricity = SliderControl("Initial eccentricity e₀", 0, .01, 0, step=.0001, decimals=4)
        self.eccentricity.setToolTip("Initial star-centred osculating eccentricity, from 0 to 0.01. Position and both velocity components are calculated consistently at fixed semimajor axis and eccentric anomaly E₀ = 90°.")
        side.addWidget(self.eccentricity)
        self.eccentricity_note = note("Starting phase: E₀ = 90° (outward). The initial Kepler period matches the planet’s; eccentricity can evolve.")
        side.addWidget(self.eccentricity_note)
        self.epicycle_button = QPushButton("Epicyclic tadpole example")
        side.addWidget(self.epicycle_button)
        self.duration = SliderControl("Integration length / Tref", 1, 3, 2, step=.5, decimals=1)
        self.duration.setToolTip("Tref = 2π / √(27μ/4), with n = 1. This is the small-μ, small-amplitude libration-period estimate, used only as a reference duration.")
        side.addWidget(self.duration)
        self.duration_note = note("")
        side.addWidget(self.duration_note)
        self.stability_note = note("")
        side.addWidget(self.stability_note)
        self.frame_selector = QComboBox()
        self.frame_selector.addItems(["Corotating with planet", "Inertial · centre of mass"])
        self.frame_selector.setAccessibleName("Reference frame")
        side.addWidget(self.frame_selector)
        self.progress = SliderControl("Time through integration", 0, 100, 0, step=.1, decimals=1, suffix="%")
        side.addWidget(self.progress)
        self.speed = SliderControl("Playback speed", .05, 2, 1, step=.05, decimals=2, suffix="×")
        side.addWidget(self.speed)
        buttons = QHBoxLayout()
        self.start_button = QPushButton("Start animation")
        self.start_button.setObjectName("primary")
        self.reset_button = QPushButton("Reset")
        buttons.addWidget(self.start_button, 1)
        buttons.addWidget(self.reset_button)
        side.addLayout(buttons)
        self.show_contours = QCheckBox("Show constant rotating-speed lines")
        side.addWidget(self.show_contours)
        self.contour_speed = SliderControl("Contour speed v / (na)", 0, .15, .02, step=.001, decimals=3)
        self.contour_speed.setEnabled(False)
        side.addWidget(self.contour_speed)
        side.addWidget(note("Orange: zero speed. Purple: chosen speed. Grey: forbidden at this orbit’s Jacobi constant. These lines are not particle paths; they specify speed, not direction."))
        self.readout = QLabel()
        self.readout.setWordWrap(True)
        self.readout.setTextFormat(Qt.TextFormat.RichText)
        side.addWidget(self.readout)
        self.status = note("")
        side.addWidget(self.status)
        side.addWidget(section_title("Reading the diagram"))
        side.addWidget(note("e₀ specifies the initial osculating Kepler ellipse about the star. Its semimajor axis is a₀ = (1 − μ)^(1/3), so its initial Kepler mean motion is n = 1. E₀ = 90° fixes the outward phase. Starting longitude measures the actual star-to-particle direction from the star–planet line."))
        side.addWidget(note("The planet perturbs the particle’s eccentricity during motion. Even e₀ = 0 describes an initially circular osculating orbit, not an exact circular CR3BP trajectory or an exact Lagrange-point equilibrium."))
        side.addWidget(note("Changing initial conditions can change the orbit family. A family selection supplies starting conditions; it does not guarantee the subsequent motion."))
        side.addWidget(note("At 1×: one reference time Tref in 12 s in the corotating view; one planet period in 6 s in the inertial view. Use the time slider to explore the full history."))
        side.addWidget(note("Tadpoles librate about L4 or L5. Horseshoes pass around L3, L4 and L5, turning back before the planet. The lower panel measures the particle’s polar longitude about the star relative to the planet."))
        side.addWidget(note("Both frames are centred on the barycentre (+). The star also moves in the inertial frame. Light blue shows the total integrated path; the blue dot is the current position. Inertial labels stay in the fixed legend; distinct shapes identify L1–L5."))
        side.addWidget(note("Units: separation a = 1, mean motion n = 1; one planet period is 2π. Tref = 2π / √(27μ/4) estimates a small-amplitude libration period only at small μ. It remains a reference duration when that approximation fails."))
        side.addWidget(note("Murray & Dermott · §§3.2–3.3, 3.6–3.10\nTremaine · §§3.1–3.2"))
        side.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(controls)
        scroll.setMinimumWidth(315)
        scroll.setMaximumWidth(325)
        layout.addWidget(scroll)

        self.plot = PlotPanel()
        self.plot.figure.clear()
        self.plot.figure.set_layout_engine(None)
        grid = self.plot.figure.add_gridspec(2, 1, height_ratios=(4.5, 1), hspace=.50)
        self.axes = self.plot.figure.add_subplot(grid[0])
        self.angle_axes = self.plot.figure.add_subplot(grid[1])
        self.plot.axes = self.axes
        self.plot.figure.subplots_adjust(left=.10, right=.97, bottom=.08, top=.92)
        layout.addWidget(self.plot, 1)
        self._create_artists()

        self.timer = QTimer(self)
        self.timer.setInterval(33)
        self.timer.timeout.connect(self._tick)
        self.recompute_timer = QTimer(self)
        self.recompute_timer.setSingleShot(True)
        self.recompute_timer.setInterval(150)
        self.recompute_timer.timeout.connect(self._recompute)
        self.orbit_selector.currentIndexChanged.connect(self._family_changed)
        self.mass_ratio.valueChanged.connect(self._mass_changed)
        for control in (self.angle, self.eccentricity):
            control.valueChanged.connect(self._initial_conditions_changed)
        self.duration.valueChanged.connect(self._schedule_recompute)
        self.centre_selector.currentIndexChanged.connect(self._centre_changed)
        self.frame_selector.currentIndexChanged.connect(self._redraw)
        self.progress.valueChanged.connect(self._progress_changed)
        self.show_contours.toggled.connect(self._contours_changed)
        self.contour_speed.valueChanged.connect(self._contours_changed)
        self.start_button.clicked.connect(self._toggle_animation)
        self.reset_button.clicked.connect(self.reset)
        self.epicycle_button.clicked.connect(self._epicyclic_example)
        self.auto_example.toggled.connect(self._auto_example_changed)
        self.example_button.clicked.connect(self._request_example)
        self._recompute()

    @property
    def mu(self):
        return 10.0 ** self.mass_ratio.value()

    def _create_artists(self):
        for ax in (self.axes, self.angle_axes):
            ax.tick_params(labelsize=8, colors=MUTED)
            ax.grid(True, color="#e8edf3", linewidth=.65)
            for spine in ax.spines.values():
                spine.set_color("#d5dfe8")
        self.axes.set_aspect("equal", adjustable="box")
        self.axes.set(xlim=(-1.65, 1.65), ylim=(-1.45, 1.45), xlabel="x / a", ylabel="y / a")
        self._lines = {}
        for key, kwargs in (
            ("reference", dict(color=MUTED, lw=.8, ls=":")),
            ("path", dict(color="#92b9dc", lw=1, alpha=.8)),
            ("star", dict(color=ORANGE, marker="o", ms=11, zorder=8)),
            ("planet", dict(color=GREEN, marker="o", ms=8, zorder=8)),
            ("particle", dict(color=BLUE, marker="o", ms=6, zorder=9)),
            ("barycentre", dict(color=TEXT, marker="+", ms=16, mew=1.2, zorder=9)),
        ):
            self._lines[key], = self.axes.plot([], [], **kwargs)
        for key, marker in zip(("L1", "L2", "L3", "L4", "L5"), ("s", "D", "v", "^", "P")):
            self._lines[key], = self.axes.plot([], [], color=PURPLE, marker=marker,
                                              ms=5, ls="none", zorder=7)
        self._labels = {}
        for key, label, offset in (
            ("star", "Star", (-20, -19)), ("planet", "Planet", (9, -14)),
            ("L1", "L1", (-14, 13)), ("L2", "L2", (5, 13)),
            ("L3", "L3", (-9, 12)), ("L4", "L4", (8, 9)),
            ("L5", "L5", (8, -15)),
        ):
            self._labels[key] = self.axes.annotate(
                label, (0, 0), xytext=offset, textcoords="offset points",
                fontsize=9, color=TEXT if key in ("star", "planet") else PURPLE,
                bbox=dict(facecolor="white", edgecolor="none", alpha=.8, pad=.6), zorder=10,
            )
        self.contour_caption = self.axes.text(.5, 1.04, "", transform=self.axes.transAxes,
                                              ha="center", fontsize=8, color=MUTED)
        names = ("star", "planet", "particle", "L1", "L2", "L3", "L4", "L5", "barycentre")
        self._legend = self.axes.legend(
            handles=[Line2D([], [], color=self._lines[key].get_color(),
                            marker=self._lines[key].get_marker(), ls="none", ms=6,
                            label=key.capitalize() if not key.startswith("L") else key)
                     for key in names],
            loc="upper center", bbox_to_anchor=(.5, -.10), ncol=3,
            frameon=False, fontsize=8, columnspacing=1.5,
        )
        self.angle_axes.set(xlabel="Time / planet period", ylabel="Longitude (°)", ylim=(0, 360))
        self.angle_axes.set_yticks([0, 60, 180, 300, 360])
        for y in (60, 180, 300):
            self.angle_axes.axhline(y, color=PURPLE, lw=.6, ls=":", alpha=.5)
        self._angle_line, = self.angle_axes.plot([], [], color=BLUE, lw=1.1)
        self._angle_point, = self.angle_axes.plot([], [], "o", color=BLUE, ms=4)
        self._time_line = self.angle_axes.axvline(0, color=MUTED, lw=.8)

    def _family_changed(self, *_):
        horse = self.orbit_selector.currentIndex() == 1
        self.centre_selector.setEnabled(not horse)
        minimum, maximum = recommended_angle_range(self.mu, "horseshoe" if horse else "tadpole")
        self._set_angle_range(minimum, maximum, (minimum+maximum)/2 if horse else 40)
        self._queue_auto_example()
        self._schedule_recompute()

    def _set_angle_range(self, minimum, maximum, value):
        self.angle.blockSignals(True)
        self.angle.minimum, self.angle.maximum = minimum, maximum
        self.angle.spin.setRange(minimum, maximum)
        self.angle.slider.setRange(0, round((maximum - minimum) / self.angle.step))
        self.angle.set_value(min(maximum, max(minimum, value)))
        self.angle.blockSignals(False)

    def _mass_changed(self, *_):
        family = "horseshoe" if self.orbit_selector.currentIndex() else "tadpole"
        minimum, maximum = recommended_angle_range(self.mu, family)
        self._set_angle_range(minimum, maximum, self.angle.value())
        self._queue_auto_example()
        self._schedule_recompute()

    def _queue_auto_example(self):
        self._checked_example = None
        self._example_pending = self.auto_example.isChecked()
        self.example_note.setText("Checking a family start at this μ…" if self._example_pending
                                  else "Free initial conditions: the selected family is not guaranteed.")

    def _centre_changed(self, *_):
        self._queue_auto_example()
        self._schedule_recompute()

    def _initial_conditions_changed(self, *_):
        self._example_pending = False
        self._checked_example = None
        self.example_note.setText("Manually edited initial conditions. Use ‘Load checked example’ to restore a family example at this μ.")
        self._schedule_recompute()

    def _auto_example_changed(self, enabled):
        if enabled:
            self._request_example()
        else:
            self._example_pending = False
            self._checked_example = None
            self.example_note.setText("Free initial conditions: the selected family is not guaranteed.")
            self._update_duration_note()

    def _request_example(self, *_):
        self._example_pending = True
        self._checked_example = None
        self.example_note.setText("Checking a family start at this μ…")
        self._schedule_recompute()

    def _load_example(self, family):
        self._example_pending = False
        centre = "L5" if family == "tadpole" and self.centre_selector.currentIndex() else "L4"
        example = checked_example(self.mu, family, centre=centre, eccentricity=self.eccentricity.value())
        self._checked_example = example
        if example is None:
            explanation = (" L4/L5 are linearly unstable here." if family == "tadpole" and self.mu >= ROUTH_MU else "")
            self.example_note.setText(
                f"No checked {family} example is available at μ = {self.mu:.4g}."
                + explanation + " The current launch is exploratory; μ is unchanged."
            )
            return
        for control, value in ((self.angle, abs(example.angle_deg)), (self.eccentricity, example.eccentricity)):
            blocked = control.blockSignals(True)
            control.set_value(value)
            control.blockSignals(blocked)
        self.example_note.setText(
            f"Checked {example.classification} at μ = {self.mu:.4g}, e₀ = {example.eccentricity:.4f}, over {example.checked_periods:g} Tref. "
            "This finite check does not establish permanent stability."
        )

    def _schedule_recompute(self, *_):
        self._pause()
        self._update_duration_note()
        self.status.setText("Computing orbit…")
        self.recompute_timer.start()

    def _update_duration_note(self):
        reference_periods = np.sqrt(4/(27*self.mu))
        self.duration_note.setText(
            f"Tref = {reference_periods:.2f} planet periods. "
            f"Requested duration = {self.duration.value()*reference_periods:.2f} planet periods. "
            "Tref is a reference, not a measured cycle."
        )
        if self.mu >= ROUTH_MU:
            self.stability_note.setText("L4 and L5 are linearly unstable at this μ (threshold ≈ 0.03852). This is an exploration of the CR3BP, not a stable-tadpole preset.")
        elif self.mu > .001 and self._checked_example is None:
            self.stability_note.setText("Exploratory mass ratio: stable tadpole or horseshoe motion is not guaranteed by the starting conditions.")
        else:
            self.stability_note.setText("")
        self.stability_note.setVisible(bool(self.stability_note.text()))

    def _recompute(self):
        self.recompute_timer.stop()
        self._pause()
        horse = self.orbit_selector.currentIndex() == 1
        family = "horseshoe" if horse else "tadpole"
        if self._example_pending:
            self._load_example(family)
        self._update_duration_note()
        angle = self.angle.value() * (-1 if not horse and self.centre_selector.currentIndex() else 1)
        key = (self.mu, family, angle, self.duration.value(), self.eccentricity.value())
        try:
            if key not in self._cache:
                self._cache[key] = integrate_orbit(self.mu, family, angle, periods=self.duration.value(), eccentricity=self.eccentricity.value())
                if len(self._cache) > 6:
                    self._cache.popitem(last=False)
            self.trajectory = self._cache[key]
        except (ValueError, RuntimeError, FloatingPointError) as error:
            self.trajectory = None
            for key in ("path", "particle"):
                self._lines[key].set_data([], [])
            self.readout.setText("")
            self.status.setText(f"Integration unavailable: {error}")
            self.plot.canvas.draw_idle()
            return
        self._orbit_mu = self.mu
        self._lagrange = lagrange_points(self._orbit_mu)
        self._inertial_path = rotating_to_inertial(self.trajectory.states[:, :2], self.trajectory.times)
        theta = np.linspace(0, 2*np.pi, 721)
        self._reference = np.column_stack((np.cos(theta) - self._orbit_mu, np.sin(theta)))
        states = self.trajectory.states
        self._eccentricities = osculating_eccentricity(states, self._orbit_mu)
        self._extent = max(1.65, 1.05*np.max(np.linalg.norm(states[:, :2], axis=1)))
        self._angles = np.rad2deg(np.arctan2(states[:, 1], states[:, 0] + self._orbit_mu)) % 360
        wraps = np.concatenate(([False], np.abs(np.diff(self._angles)) > 180))
        self._angle_line.set_data(self.trajectory.times / (2*np.pi), np.ma.array(self._angles, mask=wraps))
        self.angle_axes.set_xlim(0, self.trajectory.times[-1] / (2*np.pi))
        self._progress = 0
        self.progress.blockSignals(True)
        self.progress.set_value(0)
        self.progress.blockSignals(False)
        self._prepare_contours()
        self._redraw()

    def _prepare_contours(self):
        for contour in self._contours:
            contour.remove()
        self._contours.clear()
        if self.trajectory is None or not self.show_contours.isChecked():
            return
        mu = self._orbit_mu
        if self._grid_mu != mu:
            # A curvilinear grid resolves the narrow co-orbital zone at small μ.
            width = max(.01, 3*np.sqrt(mu))
            radius = np.concatenate((np.linspace(.025, 1-width, 200, endpoint=False),
                                     np.linspace(1-width, 1+width, 801),
                                     np.linspace(1+width, 2.5, 200)[1:]))
            radius[600] = 1.0  # Include the triangular-point radius exactly.
            theta = np.linspace(0, 2*np.pi, 901)
            self._grid_x = radius[:, None] * np.cos(theta) - mu
            self._grid_y = radius[:, None] * np.sin(theta)
            self._grid_u = np.ma.masked_invalid(2 * effective_potential(self._grid_x, self._grid_y, mu))
            self._grid_u = np.ma.masked_where(
                np.hypot(self._grid_x-1+mu, self._grid_y) < 1e-6, self._grid_u,
            )
            self._grid_mu = mu
        c0 = float(np.ravel(self.trajectory.jacobi)[0])
        minimum, maximum = float(np.nanmin(self._grid_u)), float(np.nanmax(self._grid_u))
        if minimum < c0:
            self._contours.append(self.axes.contourf(
                self._grid_x, self._grid_y, self._grid_u, levels=[minimum-1, c0],
                colors=["#dfe3e9"], alpha=.6, zorder=0,
            ))
        levels = [(c0, ORANGE, "-")]
        if self.contour_speed.value() > 0:
            levels.append((c0 + self.contour_speed.value()**2, PURPLE, "--"))
        for level, color, style in levels:
            if minimum < level < maximum:
                self._contours.append(self.axes.contour(
                    self._grid_x, self._grid_y, self._grid_u, levels=[level],
                    colors=[color], linewidths=.9, linestyles=style, zorder=2,
                ))

    def _contours_changed(self, *_):
        self.contour_speed.setEnabled(self.show_contours.isChecked())
        self._prepare_contours()
        self._redraw()

    def _set_line(self, key, points):
        points = np.asarray(points).reshape(-1, 2)
        self._lines[key].set_data(points[:, 0], points[:, 1])

    def _redraw(self, *_):
        if self.trajectory is None:
            return
        trajectory = self.trajectory
        index = min(round(self._progress * (len(trajectory.times)-1)), len(trajectory.times)-1)
        time = trajectory.times[index]
        inertial = self.frame_selector.currentIndex() == 1
        display = (lambda points: rotating_to_inertial(np.asarray(points), time)) if inertial else np.asarray
        path = self._inertial_path if inertial else trajectory.states[:, :2]
        self._set_line("path", path)
        self._set_line("particle", path[index])
        self.axes.set(xlim=(-self._extent, self._extent), ylim=(-self._extent, self._extent))
        self._set_line("reference", display(self._reference))
        self._set_line("barycentre", [[0, 0]])
        positions = {"star": [-self._orbit_mu, 0], "planet": [1-self._orbit_mu, 0], **self._lagrange}
        for key in ("star", "planet"):
            self._set_line(key, display(positions[key]))
        for key, position in self._lagrange.items():
            self._set_line(key, display(position))
        for key, label in self._labels.items():
            label.xy = display(positions[key])
            label.set_visible(not inertial)
        for contour in self._contours:
            contour.set_transform(Affine2D().rotate(time if inertial else 0) + self.axes.transData)
        motion = trajectory.classification.replace(" (L4/L5 unstable)", "").replace(" (linearly unstable)", "")
        self.axes.set_title(f"{'Inertial' if inertial else 'Corotating'} frame · {motion}", fontsize=12, color=TEXT, pad=30)
        caption = "a = 1 · n = 1 · star and planet are point masses"
        if self.show_contours.isChecked():
            c0 = float(trajectory.jacobi[0])
            minimum_speed = np.sqrt(max(0., 2*effective_potential(*self._lagrange["L4"], self._orbit_mu)-c0))
            if not self._contours:
                caption = f"No curves at chosen speeds · minimum rotating speed {minimum_speed:.3f} na"
            elif minimum_speed > 0:
                caption = f"v = {self.contour_speed.value():.3f} na · no zero-velocity curve"
            else:
                caption = (f"Speed contours at C₀; v = 0 and {self.contour_speed.value():.3f} na"
                           if self.contour_speed.value() > 0 else "Zero-velocity curve at C₀")
            if inertial:
                caption += " · instantaneous rotating-speed field"
        self.contour_caption.set_text(caption)
        self._angle_point.set_data([time/(2*np.pi)], [self._angles[index]])
        self._time_line.set_xdata([time/(2*np.pi)]*2)
        jacobi = np.ravel(trajectory.jacobi)
        drift = np.max(np.abs(jacobi - jacobi[0]))
        speed = np.linalg.norm(trajectory.states[index, 2:])
        self.readout.setText(
            f"<b>μ = {self._orbit_mu:.6g}</b><br>"
            f"Time = {time/(2*np.pi):.2f} planet periods<br>"
            f"Rotating speed = {speed:.5f} na<br>"
            f"Initial e₀ = {self._eccentricities[0]:.5f}<br>"
            f"Current osculating e = {self._eccentricities[index]:.5f}<br>"
            f"Jacobi C₀ = {jacobi[0]:.8f}<br>Max |ΔC| = {drift:.2e}"
        )
        self.status.setText(f"Measured motion: {trajectory.classification}. {trajectory.message}")
        self.plot.canvas.draw_idle()

    def _progress_changed(self, value):
        self._progress = value / 100
        self._last_tick = perf_counter()
        self._redraw()

    def _toggle_animation(self):
        if self.timer.isActive():
            self._pause()
        elif self.trajectory is not None and not self.recompute_timer.isActive():
            if self._progress >= 1:
                self._progress = 0
            self._last_tick = perf_counter()
            self.timer.start()
            self.start_button.setText("Pause")

    def _pause(self):
        self.timer.stop()
        self.start_button.setText("Start animation")

    def _tick(self):
        now = perf_counter()
        # Resolve prograde orbital motion in the inertial animation even at
        # small μ, where a libration spans hundreds of planet revolutions.
        if self.frame_selector.currentIndex() == 1:
            rate = (2*np.pi/6) / self.trajectory.times[-1]
        else:
            rate = 1 / (12*self.duration.value())
        self._progress = min(1., self._progress + (now-self._last_tick) * self.speed.value() * rate)
        self._last_tick = now
        self.progress.blockSignals(True)
        self.progress.set_value(100*self._progress)
        self.progress.blockSignals(False)
        self._redraw()
        if self._progress >= 1:
            self._pause()

    def on_leave(self):
        self._pause()

    def on_enter(self):
        pass

    def reset(self):
        self._pause()
        self.recompute_timer.stop()
        controls = (self.orbit_selector, self.centre_selector, self.frame_selector,
                    self.mass_ratio, self.angle, self.eccentricity, self.duration, self.speed,
                    self.show_contours, self.contour_speed, self.auto_example)
        for control in controls:
            control.blockSignals(True)
        self.orbit_selector.setCurrentIndex(0)
        self.centre_selector.setCurrentIndex(0)
        self.centre_selector.setEnabled(True)
        self.frame_selector.setCurrentIndex(0)
        self.mass_ratio.set_value(-3)
        self._set_angle_range(20, 85, 40)
        self.eccentricity.set_value(0)
        self.duration.set_value(2)
        self.speed.set_value(1)
        self.show_contours.setChecked(False)
        self.contour_speed.set_value(.02)
        self.contour_speed.setEnabled(False)
        self.auto_example.setChecked(True)
        self._example_pending = False
        self._checked_example = None
        self.example_note.setText("Changing μ or family loads a checked start when available. Initial conditions can also be edited freely.")
        for control in controls:
            control.blockSignals(False)
        self._recompute()

    def _epicyclic_example(self):
        self.reset()
        self.angle.set_value(60)
        self.eccentricity.set_value(.01)
        self.duration.set_value(3)
        self.contour_speed.set_value(.02)
        self._recompute()
        self.example_note.setText("Epicyclic tadpole example with e₀ = 0.01 checked over 3 Tref at μ = 0.001. This is a finite-duration example.")
