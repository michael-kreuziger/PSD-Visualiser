"""Qt integration checks for navigation and the interactive teaching controls.

Run headlessly with unittest; no desktop session or additional test framework
is required. Numerical accuracy is covered separately in test_models.py.
"""

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from numpy.testing import assert_allclose
from PySide6.QtGui import QFont, QTextDocument
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QScrollArea

from psd_visualiser.app import DISCLAIMER, MODULES, MainWindow


class TeachingInterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyle("Fusion")
        cls.app.setFont(QFont("DejaVu Sans", 10))

    def setUp(self):
        self.window = MainWindow()
        self.window.show()
        self.app.processEvents()

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()

    def open_page(self, key):
        self.window.show_page(key)
        self.app.processEvents()
        return self.window.pages[key]

    def assert_finite_axes(self, axes):
        for line in axes.lines:
            coordinates = line.get_data_3d() if hasattr(line, "get_data_3d") else line.get_data()
            for coordinate in coordinates:
                self.assertTrue(np.all(np.isfinite(np.asarray(coordinate, dtype=float))))
        limits = [axes.get_xlim(), axes.get_ylim()]
        if hasattr(axes, "get_zlim"):
            limits.append(axes.get_zlim())
        self.assertTrue(np.all(np.isfinite(limits)))

    @staticmethod
    def point(artist):
        return np.asarray(artist.get_data(), dtype=float).T[0]

    def test_home_disclaimer_module_list_and_toolbar_navigation(self):
        expected = (
            "This visualisation tool was created by Michael Kreuziger for the course Part III "
            "Planetary System Dynamics (lecturer: Mark Wyatt) at the University of Cambridge. "
            "Please feel free to change the source code (also on Moodle) or add your own modules. "
            "If you find any issues or have any questions, please feel free to contact me "
            "“mk2205@cam.ac.uk”. Codex 6.1 Sol was used to create the initial code, which was "
            "then checked and tested."
        )
        self.assertEqual(DISCLAIMER, expected)
        self.assertEqual(self.window.current_key, "home")
        self.assertEqual(set(self.window.pages), {"home"})  # Modules load on demand.
        home = self.window.pages["home"]
        document = QTextDocument()
        document.setHtml(home.disclaimer_label.text())
        self.assertEqual(document.toPlainText(), expected)
        self.assertIn('href="mailto:mk2205@cam.ac.uk"', home.disclaimer_label.text())
        self.assertTrue(home.disclaimer_label.openExternalLinks())
        headings = [label.text() for label in home.findChildren(QLabel)
                    if label.objectName() == "sectionTitle"]
        self.assertEqual(headings, ["About", "Available modules"])
        buttons = home.findChildren(QPushButton)
        self.assertEqual([button.text() for button in buttons], [spec.title for spec in MODULES])
        for button, spec in zip(buttons, MODULES):
            button.click()
            self.app.processEvents()
            self.assertEqual(self.window.current_key, spec.key)
            self.assertIs(self.window.stack.currentWidget(), self.window.pages[spec.key])
            self.assertTrue(self.window.actions[spec.key].isChecked())
            self.window.actions["home"].trigger()
            self.assertEqual(self.window.current_key, "home")
            self.assertTrue(self.window.actions["home"].isChecked())

    def test_orbital_controls_and_degenerate_limits(self):
        page = self.open_page("orbital")
        # The physical slider and editable numerical value must stay in sync.
        page.sliders["a"].slider.setValue(page.sliders["a"].slider.maximum())
        self.assertEqual(page.sliders["a"].value(), 3)
        page.sliders["a"].spin.setValue(0.5)
        self.assertEqual(page.sliders["a"].slider.value(), 0)
        cases = (
            {"a": 0.5, "e": 0, "I": 0, "Omega": 0, "omega": 0, "f": 0},
            {"a": 3, "e": 0.99, "I": 180, "Omega": 360, "omega": 360, "f": 360},
        )
        for values in cases:
            for key, value in values.items():
                page.sliders[key].set_value(value)
            page.plot.canvas.draw()
            self.assert_finite_axes(page.plot.axes)
            self.assertIn("ascending node is undefined", page.degeneracy.text())
            if values["e"] == 0:
                self.assertIn("periapsis is arbitrary", page.degeneracy.text())
        page.reset_button.click()
        for control in page.sliders.values():
            self.assertEqual(control.value(), control.default)
        self.assertFalse(page.degeneracy.isVisible())

    def test_controls_fit_at_minimum_window_size(self):
        self.window.resize(1024, 720)
        for key in ("orbital", "guiding", "inclinations"):
            page = self.open_page(key)
            scroll = page.findChild(QScrollArea)
            self.assertEqual(scroll.horizontalScrollBar().maximum(), 0, key)
            self.assertLessEqual(scroll.widget().width(), scroll.viewport().width(), key)
            scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum())
            self.app.processEvents()
            self.assertTrue(page.isVisible())

    def test_orbital_camera_state_and_fit_view(self):
        page = self.open_page("orbital")
        axes = page.plot.axes
        axes.view_init(elev=41, azim=123, roll=0)
        limits = (axes.get_xlim(), axes.get_ylim(), axes.get_zlim())
        page.sliders["f"].set_value(180)
        assert_allclose([axes.elev, axes.azim, axes.roll], [41, 123, 0])
        assert_allclose([axes.get_xlim(), axes.get_ylim(), axes.get_zlim()], limits)
        self.window.actions["home"].trigger()
        self.window.actions["orbital"].trigger()
        self.assertIs(self.window.pages["orbital"], page)
        self.assertEqual(page.sliders["f"].value(), 180)
        assert_allclose([axes.elev, axes.azim, axes.roll], [41, 123, 0])
        page.sliders["a"].set_value(3)
        expanded = axes.get_xlim()[1]
        page.sliders["a"].set_value(0.5)
        page.fit_button.click()
        self.assertLess(axes.get_xlim()[1], expanded)
        assert_allclose([axes.get_xlim(), axes.get_ylim(), axes.get_zlim()],
                        np.tile(axes.get_xlim(), (3, 1)))

    def test_guiding_animation_advances_and_pauses_on_navigation(self):
        page = self.open_page("guiding")
        page.phase.set_value(100)
        page.start_button.click()
        self.assertTrue(page.timer.isActive())
        QTest.qWait(180)
        self.assertGreater(page.phase.value(), 100)
        page.start_button.click()
        self.assertFalse(page.timer.isActive())
        paused = page.phase.value()
        QTest.qWait(80)
        self.assertEqual(page.phase.value(), paused)
        page.start_button.click()
        self.window.actions["home"].trigger()
        self.assertFalse(page.timer.isActive())
        left_at = page.phase.value()
        QTest.qWait(80)
        self.window.actions["guiding"].trigger()
        self.assertEqual(page.phase.value(), left_at)
        self.assertFalse(page.timer.isActive())
        page.reset_button.click()
        self.assertEqual(page.phase.value(), page.DEFAULT_PHASE)
        self.assertEqual(page.eccentricity.value(), 0.2)

    def test_guiding_frame_geometry_at_circular_and_eccentric_limits(self):
        page = self.open_page("guiding")
        for eccentricity, phase in ((0, 0), (0, 360), (0.5, 0), (0.5, 360), (0.5, 135)):
            page.eccentricity.set_value(eccentricity)
            page.phase.set_value(phase)
            for rotating in (False, True):
                page.rotating.setChecked(rotating)
                page.plot.canvas.draw()
                for axes in (page.axes, page.relative_axes):
                    self.assert_finite_axes(axes)
                if rotating:
                    assert_allclose(self.point(page._lines["guiding"]), [0, 0], atol=1e-14)
                    assert_allclose(self.point(page._lines["focus"]), [-1, 0], atol=1e-14)
                else:
                    assert_allclose(self.point(page._lines["focus"]), [0, 0])
                    mean = np.deg2rad(phase)
                    assert_allclose(self.point(page._lines["guiding"]), [np.cos(mean), np.sin(mean)])
                if eccentricity == 0:
                    assert_allclose(self.point(page._lines["particle"]),
                                    self.point(page._lines["guiding"]), atol=1e-14)
                    assert_allclose(self.point(page._lines["relative_p"]), [0, 0], atol=1e-14)

    def test_guiding_optional_construction_and_phase_preservation(self):
        page = self.open_page("guiding")
        page.phase.set_value(220)
        page.eccentricity.set_value(0.5)
        self.assertFalse(page._lines["aux_circle"].get_visible())
        page.show_e.setChecked(True)
        for key in ("aux_circle", "aux_projection", "E", "centre", "aux_point"):
            self.assertTrue(page._lines[key].get_visible())
        page.rotating.setChecked(True)
        self.assertEqual(page.phase.value(), 220)
        self.assertEqual(page.eccentricity.value(), 0.5)
        delta = page._lines["delta"]
        self.assertTrue(delta.get_visible())
        # At M > π the equation of centre sweeps clockwise.
        arc = np.asarray(delta.get_data()).T - np.array([-1, 0])
        self.assertLess(np.linalg.det(np.array([arc[0], arc[1]])), 0)
        page.show_e.setChecked(False)
        self.assertFalse(page._lines["E"].get_visible())
        self.assertFalse(page._labels["E"].get_visible())
        page.reset_button.click()
        self.assertFalse(page.rotating.isChecked())
        self.assertFalse(page.show_e.isChecked())
        self.assertFalse(page.timer.isActive())

    def test_inclinations_randomisation_selection_counts_and_camera(self):
        page = self.open_page("inclinations")
        original = page.vectors.copy()
        page.axes.view_init(elev=35, azim=91, roll=4)
        page.vector_selector.setCurrentIndex(9)
        self.assertIn("h10:", page.selected_label.text())
        page.rng = np.random.default_rng(99)
        page.randomize_button.click()
        self.assertEqual(page.vectors.shape, (10, 3))
        self.assertFalse(np.array_equal(page.vectors, original))
        assert_allclose(np.linalg.norm(page.vectors, axis=1), 1)
        self.assertEqual(page.vector_selector.count(), 10)
        self.assertEqual(page.vector_selector.currentIndex(), 9)
        self.assertEqual(sum(bar.get_height() for bar in page.hist_axes.patches if hasattr(bar, "get_height")), 10)
        expected_mean = np.mean(np.sqrt(1 - page.vectors[:, 2] ** 2))
        self.assertIn(f"{expected_mean:.4f}", page.sample_label.text())
        assert_allclose([page.axes.elev, page.axes.azim, page.axes.roll], [35, 91, 4])
        sample = page.vectors.copy()
        self.window.actions["home"].trigger()
        self.window.actions["inclinations"].trigger()
        assert_allclose(page.vectors, sample)
        assert_allclose([page.axes.elev, page.axes.azim, page.axes.roll], [35, 91, 4])

    def test_inclinations_polar_and_equatorial_planes_render(self):
        page = self.open_page("inclinations")
        # Exercise the selected-plane basis and inclination arc at both poles.
        page.vectors = np.array([[0., 0., 1.], [0., 0., -1.], [1., 0., 0.]] +
                                [[0., 1., 0.]] * 7)
        page._update_selector()
        for index, angle in ((0, "0.0°"), (1, "180.0°"), (2, "90.0°")):
            page.vector_selector.setCurrentIndex(index)
            page.render()
            page.plot.canvas.draw()
            self.assertIn(angle, page.selected_label.text())
            self.assert_finite_axes(page.axes)
            self.assert_finite_axes(page.hist_axes)
        self.assertEqual(sum(bar.get_height() for bar in page.hist_axes.patches if hasattr(bar, "get_height")), 10)


if __name__ == "__main__":
    unittest.main()
