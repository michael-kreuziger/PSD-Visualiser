"""Mouse-event integration tests for the orbital turn-and-tilt camera."""

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from matplotlib.backend_bases import LocationEvent, MouseButton, MouseEvent
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from numpy.testing import assert_allclose
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from psd_visualiser.app import MainWindow
from psd_visualiser.camera import OrbitCamera


def emit(canvas, name, x, y, **kwargs):
    event = MouseEvent(name, canvas, x, y, **kwargs)
    canvas.callbacks.process(name, event)


def position(axes, x=0.5, y=0.5):
    return int(axes.bbox.x0 + axes.bbox.width * x), int(axes.bbox.y0 + axes.bbox.height * y)


def drag(axes, dx=0, dy=0, start=None, button=MouseButton.LEFT):
    canvas = axes.get_figure().canvas
    x, y = position(axes) if start is None else start
    emit(canvas, "button_press_event", x, y, button=button)
    emit(canvas, "motion_notify_event", x + dx, y + dy)
    emit(canvas, "button_release_event", x + dx, y + dy, button=button)


class OrbitCameraEventTests(unittest.TestCase):
    def setUp(self):
        self.figure = Figure(figsize=(5, 5))
        self.canvas = FigureCanvasAgg(self.figure)
        self.axes = self.figure.add_subplot(projection="3d")
        self.axes.set(xlim=(-2, 2), ylim=(-2, 2), zlim=(-2, 2))
        self.axes.set_box_aspect((1, 1, 1))
        self.axes.view_init(elev=26, azim=-110, roll=0)
        self.camera = OrbitCamera(self.axes)
        self.canvas.draw()

    def view(self):
        return self.axes.elev, self.axes.azim, self.axes.roll

    def limits(self):
        return np.array([self.axes.get_xlim(), self.axes.get_ylim(), self.axes.get_zlim()])

    def test_horizontal_vertical_and_diagonal_drag_do_not_roll(self):
        drag(self.axes, dx=40)
        self.assertAlmostEqual(self.axes.elev, 26)
        self.assertLess(self.axes.azim, -110)
        self.assertEqual(self.axes.roll, 0)
        self.axes.view_init(elev=26, azim=-110, roll=0)
        drag(self.axes, dy=30)
        self.assertAlmostEqual(self.axes.azim, -110)
        self.assertLess(self.axes.elev, 26)
        self.assertEqual(self.axes.roll, 0)
        self.axes.view_init(elev=26, azim=-110, roll=0)
        drag(self.axes, dx=40, dy=30)
        self.assertLess(self.axes.azim, -110)
        self.assertLess(self.axes.elev, 26)
        self.assertEqual(self.axes.roll, 0)
        assert_allclose(self.limits(), np.tile([-2, 2], (3, 1)))

    def test_same_pixel_drag_is_independent_of_start_position(self):
        drag(self.axes, dx=35, dy=25, start=position(self.axes, 0.25, 0.3))
        first = self.view()
        self.axes.view_init(elev=26, azim=-110, roll=0)
        drag(self.axes, dx=35, dy=25, start=position(self.axes, 0.65, 0.6))
        assert_allclose(self.view(), first)

    def test_extreme_tilts_stop_before_the_poles(self):
        self.axes.view_init(elev=0, azim=-110, roll=0)
        low = position(self.axes, 0.5, 0.1)
        high = position(self.axes, 0.5, 0.9)
        drag(self.axes, dy=high[1] - low[1], start=low)
        self.assertEqual(self.axes.elev, -89)
        drag(self.axes, dy=low[1] - high[1], start=high)
        self.assertLessEqual(self.axes.elev, 89)
        drag(self.axes, dy=low[1] - high[1], start=high)
        self.assertEqual(self.axes.elev, 89)
        self.assertEqual(self.axes.roll, 0)

    def test_release_outside_and_leaving_figure_cancel_drag(self):
        x, y = position(self.axes)
        emit(self.canvas, "button_press_event", x, y, button=MouseButton.LEFT)
        emit(self.canvas, "motion_notify_event", x + 20, y + 10)
        released_view = self.view()
        emit(self.canvas, "button_release_event", -10, -10, button=MouseButton.LEFT)
        emit(self.canvas, "motion_notify_event", x + 40, y + 30)
        assert_allclose(self.view(), released_view)
        emit(self.canvas, "button_press_event", x, y, button=MouseButton.LEFT)
        event = LocationEvent("figure_leave_event", self.canvas, -1, -1)
        self.canvas.callbacks.process("figure_leave_event", event)
        emit(self.canvas, "motion_notify_event", x + 40, y + 30)
        assert_allclose(self.view(), released_view)

    def test_outside_presses_and_other_buttons_do_not_move_the_camera(self):
        original_view, original_limits = self.view(), self.limits()
        x, y = position(self.axes)
        emit(self.canvas, "button_press_event", -1, -1, button=MouseButton.LEFT)
        emit(self.canvas, "motion_notify_event", x + 30, y + 30)
        emit(self.canvas, "button_release_event", x + 30, y + 30, button=MouseButton.LEFT)
        for button in (MouseButton.MIDDLE, MouseButton.RIGHT):
            drag(self.axes, dx=30, dy=30, button=button)
        assert_allclose(self.view(), original_view)
        assert_allclose(self.limits(), original_limits)

    def test_wheel_zoom_is_origin_centred_equal_and_bounded(self):
        x, y = position(self.axes, 0.3, 0.4)
        original_view = self.view()
        emit(self.canvas, "scroll_event", x, y, step=1)
        zoomed = self.limits()
        self.assertLess(zoomed[0, 1], 2)
        assert_allclose(zoomed, np.tile(zoomed[0], (3, 1)))
        assert_allclose(zoomed[:, 0], -zoomed[:, 1])
        assert_allclose(self.view(), original_view)
        emit(self.canvas, "scroll_event", x, y, step=-1)
        assert_allclose(self.limits(), np.tile([-2, 2], (3, 1)))
        emit(self.canvas, "scroll_event", -1, -1, step=1)
        assert_allclose(self.limits(), np.tile([-2, 2], (3, 1)))
        emit(self.canvas, "scroll_event", x, y, step=1_000_000)
        assert_allclose(self.limits(), np.tile([-0.05, 0.05], (3, 1)))
        emit(self.canvas, "scroll_event", x, y, step=-1_000_000)
        self.assertTrue(np.all(np.isfinite(self.limits())))
        self.assertLessEqual(self.axes.get_xlim()[1], 100)

    def test_native_rotation_stays_disabled_after_axes_clear(self):
        self.axes.clear()
        self.camera.disable_native_controls()
        self.axes.view_init(elev=26, azim=-110, roll=0)
        self.canvas.draw()
        drag(self.axes, dx=30, dy=20)
        self.assertEqual(self.axes.roll, 0)
        self.assertLess(self.axes.elev, 26)
        self.assertLess(self.axes.azim, -110)


class OrbitalPageCameraTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setFont(QFont("DejaVu Sans", 10))

    def test_mouse_view_survives_slider_navigation_and_fit_then_reset(self):
        window = MainWindow()
        try:
            window.show()
            window.show_page("orbital")
            self.app.processEvents()
            page = window.pages["orbital"]
            axes = page.plot.axes
            page.plot.canvas.draw()
            drag(axes, dx=35, dy=20)
            view = (axes.elev, axes.azim, axes.roll)
            x, y = position(axes)
            emit(page.plot.canvas, "scroll_event", x, y, step=1)
            limits = (axes.get_xlim(), axes.get_ylim(), axes.get_zlim())
            page.sliders["f"].set_value(180)
            assert_allclose((axes.elev, axes.azim, axes.roll), view)
            assert_allclose([axes.get_xlim(), axes.get_ylim(), axes.get_zlim()], limits)
            window.show_page("home")
            window.show_page("orbital")
            assert_allclose((axes.elev, axes.azim, axes.roll), view)
            assert_allclose([axes.get_xlim(), axes.get_ylim(), axes.get_zlim()], limits)
            page.fit_button.click()
            assert_allclose((axes.elev, axes.azim, axes.roll), view)
            page.reset_button.click()
            assert_allclose((axes.elev, axes.azim, axes.roll), [26, -110, 0])
            self.assertEqual(page.sliders["f"].value(), 45)
        finally:
            window.close()
            window.deleteLater()
            self.app.processEvents()


if __name__ == "__main__":
    unittest.main()
