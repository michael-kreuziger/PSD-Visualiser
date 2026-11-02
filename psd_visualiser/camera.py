"""Predictable turn-and-tilt controls for the orbital-elements diagram.

The controller deliberately avoids Matplotlib's arcball rotation: horizontal
drags turn about +z, vertical drags tilt, and the camera never rolls or crosses
the poles. All model geometry remains unchanged.
"""

import math

import numpy as np
from matplotlib.backend_bases import MouseButton


class OrbitCamera:
    """Attach a single set of mouse controls to an existing 3D Axes.

    Drag angles are measured from the press position, using the plot's pixel
    size. Thus the same drag gives the same turn anywhere inside the plot.
    Scrolling changes a common, origin-centred extent for all three axes.
    """

    MIN_ELEVATION = -89.0
    MAX_ELEVATION = 89.0
    MIN_EXTENT = 0.05
    MAX_EXTENT = 100.0

    def __init__(self, axes):
        self.axes = axes
        self.canvas = axes.get_figure().canvas
        self._drag = None
        self.disable_native_controls()
        self._connections = tuple(
            self.canvas.mpl_connect(name, handler)
            for name, handler in (
                ("button_press_event", self._press),
                ("motion_notify_event", self._move),
                ("button_release_event", self._release),
                ("figure_leave_event", self._release),
                ("scroll_event", self._scroll),
            )
        )

    def disable_native_controls(self):
        """Disable native rotation, panning, and zooming without private APIs.

        Reapply after clearing the Axes; some Matplotlib releases may restore
        their defaults during a clear. Our canvas connections stay attached.
        """
        self.axes.mouse_init(rotate_btn=[], pan_btn=[], zoom_btn=[])

    def cancel_drag(self):
        """Stop any active drag when resetting or leaving the page."""
        self._drag = None

    def _press(self, event):
        self.cancel_drag()
        if event.button != MouseButton.LEFT or event.inaxes is not self.axes:
            return
        width, height = self.axes.bbox.width, self.axes.bbox.height
        if width <= 0 or height <= 0:
            return
        elevation = float(np.clip(self.axes.elev, self.MIN_ELEVATION, self.MAX_ELEVATION))
        azimuth = float(self.axes.azim)
        self._drag = (event.x, event.y, azimuth, elevation, width, height)
        self.axes.view_init(elev=elevation, azim=azimuth, roll=0)

    def _move(self, event):
        if self._drag is None:
            return
        if event.inaxes is not self.axes:
            self.cancel_drag()
            return
        x, y, azimuth, elevation, width, height = self._drag
        azimuth -= 180.0 * (event.x - x) / width
        elevation -= 180.0 * (event.y - y) / height
        elevation = float(np.clip(elevation, self.MIN_ELEVATION, self.MAX_ELEVATION))
        azimuth = (azimuth + 180.0) % 360.0 - 180.0
        self.axes.view_init(elev=elevation, azim=azimuth, roll=0)
        self.canvas.draw_idle()

    def _release(self, _event):
        self.cancel_drag()

    def _scroll(self, event):
        if event.inaxes is not self.axes or not math.isfinite(event.step) or event.step == 0:
            return
        limits = np.array([self.axes.get_xlim(), self.axes.get_ylim(), self.axes.get_zlim()])
        extent = float(np.max(np.abs(np.diff(limits, axis=1))) / 2)
        if not math.isfinite(extent) or extent <= 0:
            return
        # Limit the exponent as well as the result, including unusually large
        # wheel events from high-resolution input devices.
        extent *= math.exp(-float(np.clip(event.step, -100, 100)) * math.log(1.15))
        extent = float(np.clip(extent, self.MIN_EXTENT, self.MAX_EXTENT))
        self.axes.set(xlim=(-extent, extent), ylim=(-extent, extent), zlim=(-extent, extent))
        self.canvas.draw_idle()
