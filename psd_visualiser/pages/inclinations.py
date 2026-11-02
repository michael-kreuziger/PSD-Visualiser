"""Isotropic orbit orientations and the inclination averaging factor."""

from __future__ import annotations

import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from psd_visualiser.models.inclinations import (
    inclination_bin_probabilities,
    inclinations,
    sample_directions,
)
from psd_visualiser.widgets import (
    BLUE,
    GREEN,
    MUTED,
    ORANGE,
    TEXT,
    PlotPanel,
    note,
    section_title,
)


class InclinationsPage(QWidget):
    """Show ten independent sphere directions and their orbital inclinations.

    Each draw replaces the previous ten directions.  The theoretical histogram
    uses *bin probabilities*, avoiding a radian/degree density conversion.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.rng = np.random.default_rng()
        self.vectors = sample_directions(10, self.rng)
        self._has_rendered = False
        self.bin_edges = np.arange(0.0, 181.0, 15.0)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(20)

        controls = QWidget()
        controls.setMinimumWidth(260)
        controls.setMaximumWidth(320)
        column = QVBoxLayout(controls)
        column.setContentsMargins(4, 4, 12, 12)
        column.setSpacing(14)
        column.addWidget(section_title("Averaging sin I"))
        column.addWidget(note(
            "Choose a direction at random on a sphere. It is an orbital angular-"
            "momentum direction, h, perpendicular to its orbit plane."
        ))

        self.randomize_button = QPushButton("Randomize")
        self.randomize_button.setObjectName("primary")
        self.randomize_button.setToolTip("Replace all ten h vectors with a new independent sample")
        self.randomize_button.clicked.connect(self.randomize)
        column.addWidget(self.randomize_button)

        column.addWidget(section_title("Inspect an orbit"))
        column.addWidget(note("Highlight one vector and the orbit plane perpendicular to it."))
        self.vector_selector = QComboBox()
        self.vector_selector.setAccessibleName("Angular momentum vector to inspect")
        self.vector_selector.currentIndexChanged.connect(self.render)
        column.addWidget(self.vector_selector)
        self.selected_label = QLabel()
        self.selected_label.setWordWrap(True)
        self.selected_label.setStyleSheet("font-weight: 600;")
        column.addWidget(self.selected_label)

        column.addWidget(note(
            "I is measured from +z to h (0–180°). It is also the inclination of "
            "the orbit plane to the reference plane, including the direction of motion."
        ))
        column.addWidget(section_title("The averaging factor"))
        self.sample_label = QLabel()
        self.sample_label.setWordWrap(True)
        self.sample_label.setStyleSheet("font-weight: 600;")
        column.addWidget(self.sample_label)
        column.addWidget(note("Isotropic mean: ⟨sin I⟩ = π/4 ≈ 0.7854"))
        column.addWidget(note(
            "The ten-vector sample fluctuates. Each click starts a fresh sample; "
            "the blue bars do not accumulate."
        ))
        column.addWidget(section_title("Why sin I?"))
        column.addWidget(note(
            "Equal-width inclination bands cover more sphere area near the "
            "equator. Uniform directions therefore favour I near 90°, with "
            "p(I) = ½ sin I (density per radian)."
        ))
        column.addWidget(note(
            "Sampling: azimuth is uniform on 0–2π and hᶻ is uniform on −1 to 1. "
            "Drawing I uniformly would give the wrong distribution."
        ))
        column.addStretch()
        column.addWidget(note(
            "Orbital-plane convention: Tremaine §1.3.2; Murray & Dermott §2.8. "
            "Drag the sphere to rotate; right-drag to zoom."
        ))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setMinimumWidth(280)
        scroll.setMaximumWidth(340)
        scroll.setWidget(controls)
        layout.addWidget(scroll)

        self.plot = PlotPanel()
        self.plot.figure.clear()
        grid = self.plot.figure.add_gridspec(
            2, 1, height_ratios=(2.5, 1.0), hspace=0.15,
            left=0.10, right=0.96, top=0.97, bottom=0.10,
        )
        self.axes = self.plot.figure.add_subplot(grid[0], projection="3d")
        self.hist_axes = self.plot.figure.add_subplot(grid[1])
        self.plot.axes = self.axes
        layout.addWidget(self.plot, 1)
        self._update_selector()
        self.render()

    def on_enter(self) -> None:
        """Retain the sample and camera when returning to this page."""

    def on_leave(self) -> None:
        """No background computation runs on this page."""

    def randomize(self, _checked: bool = False) -> None:
        """Replace, rather than accumulate, the ten displayed directions."""
        self.vectors = sample_directions(10, self.rng)
        self._update_selector()
        self.render()

    def reset(self) -> None:
        """Start a fresh sample without discarding the camera orientation."""
        self.randomize()

    def _update_selector(self) -> None:
        selected = max(0, self.vector_selector.currentIndex())
        self.vector_selector.blockSignals(True)
        self.vector_selector.clear()
        for index, angle in enumerate(np.rad2deg(inclinations(self.vectors))):
            self.vector_selector.addItem(f"h{index + 1}     I = {angle:.1f}°")
        self.vector_selector.setCurrentIndex(min(selected, len(self.vectors) - 1))
        self.vector_selector.blockSignals(False)

    def render(self, *_args: object) -> None:
        """Redraw the current sample, preserving the 3D view and zoom."""
        angles = inclinations(self.vectors)
        index = max(0, self.vector_selector.currentIndex())
        h = self.vectors[index]
        angle = float(angles[index])
        self.selected_label.setText(f"h{index + 1}: orbital inclination I = {np.rad2deg(angle):.1f}°")
        self.sample_label.setText(f"This sample: mean sin I = {np.mean(np.sin(angles)):.4f}")

        if self._has_rendered:
            view = (self.axes.elev, self.axes.azim, self.axes.roll)
            limits = (self.axes.get_xlim(), self.axes.get_ylim(), self.axes.get_zlim())
        else:
            view = (23, -55, 0)
            limits = ((-1.35, 1.35), (-1.35, 1.35), (-1.35, 1.35))
        ax = self.axes
        ax.clear()

        longitude = np.linspace(0, 2 * np.pi, 36)
        latitude = np.linspace(0, np.pi, 19)
        sx = np.outer(np.cos(longitude), np.sin(latitude))
        sy = np.outer(np.sin(longitude), np.sin(latitude))
        sz = np.outer(np.ones_like(longitude), np.cos(latitude))
        ax.plot_wireframe(sx, sy, sz, color="#bac8d3", linewidth=0.45, alpha=0.55,
                          rstride=3, cstride=3)

        t = np.linspace(0, 2 * np.pi, 100)
        reference = np.column_stack((1.1 * np.cos(t), 1.1 * np.sin(t), np.zeros_like(t)))
        ax.add_collection3d(Poly3DCollection([reference], facecolors=BLUE, alpha=0.055,
                                            edgecolors=BLUE, linewidths=0.8))
        ax.plot(reference[:, 0], reference[:, 1], reference[:, 2], color=BLUE,
                alpha=0.35, linewidth=1.0)

        # An orthonormal basis in the selected orbit plane, including polar h.
        helper = np.array([0.0, 0.0, 1.0]) if abs(h[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
        u = np.cross(h, helper)
        u /= np.linalg.norm(u)
        v = np.cross(h, u)
        orbit = 0.88 * (np.cos(t)[:, None] * u + np.sin(t)[:, None] * v)
        ax.add_collection3d(Poly3DCollection([orbit], facecolors=ORANGE, alpha=0.12,
                                            edgecolors=ORANGE, linewidths=1.2))

        ax.quiver(0, 0, 0, 0, 0, 1.25, color=TEXT, linewidth=1.4, arrow_length_ratio=0.09)
        ax.text(0.04, 0.02, 1.31, "+z", color=TEXT, fontsize=10)
        for j, direction in enumerate(self.vectors):
            selected = j == index
            color = ORANGE if selected else BLUE
            ax.quiver(0, 0, 0, *direction, color=color,
                      linewidth=2.4 if selected else 1.3,
                      alpha=1.0 if selected else 0.65, arrow_length_ratio=0.10)
            endpoint = direction * 1.08
            ax.text(*endpoint, str(j + 1), color=color,
                    fontsize=10 if selected else 8,
                    fontweight="bold" if selected else "normal")

        horizontal = np.array([h[0], h[1], 0.0])
        norm = np.linalg.norm(horizontal)
        horizontal = horizontal / norm if norm > 1e-12 else np.array([1.0, 0.0, 0.0])
        arc_t = np.linspace(0, angle, 70)
        arc = 0.57 * (np.sin(arc_t)[:, None] * horizontal +
                      np.cos(arc_t)[:, None] * np.array([0, 0, 1]))
        ax.plot(arc[:, 0], arc[:, 1], arc[:, 2], color=ORANGE, linewidth=2.0)
        midpoint = 0.70 * (np.sin(angle / 2) * horizontal +
                           np.cos(angle / 2) * np.array([0, 0, 1]))
        ax.text(*midpoint, "I", color=ORANGE, fontsize=12, fontweight="bold")
        ax.scatter([0], [0], [0], color=TEXT, s=12, depthshade=False)

        ax.set(xlim=limits[0], ylim=limits[1], zlim=limits[2])
        # Matplotlib's default 3D projection leaves a wide margin around a
        # tick-free sphere.  Use that room for the teaching diagram itself.
        ax.set_box_aspect((1, 1, 1), zoom=1.45)
        ax.view_init(elev=view[0], azim=view[1], roll=view[2])
        ax.set_axis_off()
        ax.legend(handles=[
            Line2D([], [], color=BLUE, linewidth=2, label="Unit h vectors"),
            Patch(facecolor=BLUE, alpha=0.15, label="Reference plane"),
            Patch(facecolor=ORANGE, alpha=0.25, label="Selected orbit plane"),
        ], loc="upper left", bbox_to_anchor=(-0.04, 1.02), frameon=False, fontsize=8)

        hist = self.hist_axes
        hist.clear()
        counts, _ = np.histogram(np.rad2deg(angles), self.bin_edges)
        expected = len(self.vectors) * inclination_bin_probabilities(np.deg2rad(self.bin_edges))
        centres = (self.bin_edges[:-1] + self.bin_edges[1:]) / 2
        hist.bar(centres, counts, width=12.5, color=BLUE, alpha=0.80,
                 label="Current 10 vectors", zorder=2)
        hist.stairs(expected, self.bin_edges, color=GREEN, linewidth=2.0,
                    label="Isotropic expected count", zorder=3)
        hist.set_xlim(0, 180)
        hist.set_ylim(0, max(3.0, float(counts.max()) + 0.6))
        hist.set_xticks(np.arange(0, 181, 30))
        hist.set_yticks(np.arange(0, int(np.ceil(hist.get_ylim()[1]))))
        hist.set_xlabel("Orbital inclination I (degrees)", color=TEXT, fontsize=10)
        hist.set_ylabel("Count / 15° bin", color=TEXT, fontsize=9)
        hist.set_title("One small sample and its expected distribution", loc="left",
                       color=TEXT, fontsize=10, pad=12)
        hist.tick_params(colors=MUTED, labelsize=8)
        hist.spines[["top", "right"]].set_visible(False)
        hist.spines[["left", "bottom"]].set_color("#d5dee6")
        hist.grid(axis="y", color="#e8edf2", zorder=0)
        hist.legend(loc="upper right", frameon=False, fontsize=8)

        self._has_rendered = True
        self.plot.canvas.draw_idle()
