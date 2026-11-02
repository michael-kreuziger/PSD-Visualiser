"""Regression checks for displayed nodes and very eccentric orbital geometry."""

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from mpl_toolkits.mplot3d import proj3d
from numpy.testing import assert_allclose
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from psd_visualiser.app import MainWindow
from psd_visualiser.models.orbits import orbital_position, orbital_rotation


class OrbitalDisplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyle("Fusion")
        cls.app.setFont(QFont("DejaVu Sans", 10))

    def setUp(self):
        self.window = MainWindow()
        self.window.show()
        self.window.show_page("orbital")
        self.page = self.window.pages["orbital"]
        self.app.processEvents()

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()

    def set_controls(self, **values):
        for key, value in values.items():
            self.page.sliders[key].set_value(value)

    @staticmethod
    def coordinates(line):
        return np.asarray(line.get_data_3d(), dtype=float).T

    def test_eccentricity_control_reaches_point_99_and_draws_the_complete_ellipse(self):
        eccentricity = self.page.sliders["e"]
        self.assertEqual(eccentricity.slider.maximum(), 99)
        eccentricity.slider.setValue(99)
        self.assertEqual(eccentricity.value(), 0.99)
        eccentricity.spin.setValue(0.98)
        self.assertEqual(eccentricity.slider.value(), 98)
        eccentricity.spin.setValue(0.99)
        self.assertEqual(eccentricity.slider.value(), 99)
        self.set_controls(a=3, I=150, Omega=360, omega=360)
        for anomaly in (0, 360):
            self.set_controls(f=anomaly)
            self.page.plot.canvas.draw()
            orbit = next(line for line in self.page.plot.axes.lines if line.get_label() == "Orbit")
            positions = self.coordinates(orbit)
            self.assertTrue(np.all(np.isfinite(positions)))
            assert_allclose(positions[0], positions[-1], atol=0)
            radii = np.linalg.norm(positions, axis=1)
            self.assertAlmostEqual(float(radii.min()), 3 * 0.01)
            self.assertAlmostEqual(float(radii.max()), 3 * 1.99)
            limits = [self.page.plot.axes.get_xlim(), self.page.plot.axes.get_ylim(),
                      self.page.plot.axes.get_zlim()]
            self.assertTrue(np.all(np.isfinite(limits)))

    def test_both_node_markers_and_labels_follow_the_actual_crossings(self):
        self.set_controls(e=0.99, Omega=40)
        for inclination in (89, 90, 91, 150):
            for periapsis in (0, 60, 180):
                with self.subTest(I=inclination, omega=periapsis):
                    self.set_controls(I=inclination, omega=periapsis)
                    a, e, inc, node, peri, _ = self.page.values()
                    for key, anomaly in (("ascending", -peri), ("descending", np.pi - peri)):
                        expected = orbital_position(a, e, inc, node, peri, anomaly)
                        displayed = self.coordinates(self.page.node_markers[key])
                        assert_allclose(displayed, expected[None, :], atol=2e-13)
                        assert_allclose(self.page.node_labels[key].position_3d, expected, atol=2e-13)
                        self.assertAlmostEqual(float(displayed[0, 2]), 0, delta=2e-13)
        # Leader lines must still end at the same physical points after the
        # user turns the camera, rather than remaining at a stale projection.
        axes = self.page.plot.axes
        for elevation, azimuth in ((26, -110), (41, 110)):
            axes.view_init(elev=elevation, azim=azimuth, roll=0)
            self.page.plot.canvas.draw()
            for key, label in self.page.node_labels.items():
                crossing = self.coordinates(self.page.node_markers[key])[0]
                projected = proj3d.proj_transform(*crossing, axes.get_proj())
                assert_allclose(label.xy, projected[:2])

    def test_motion_arrow_crosses_upwards_and_follows_angular_momentum(self):
        for inclination, periapsis in ((89, 60), (90, 60), (91, 180), (150, 0)):
            with self.subTest(I=inclination, omega=periapsis):
                self.set_controls(e=0.99, I=inclination, omega=periapsis)
                a, e, inc, node, peri, _ = self.page.values()
                tail, tip = self.page.motion_segment
                self.assertGreater(tip[2], tail[2])
                crossing = self.coordinates(self.page.node_markers["ascending"])[0]
                assert_allclose((tail + tip) / 2, crossing, atol=1e-15)
                displayed_h = np.cross(crossing, tip - tail)
                displayed_h /= np.linalg.norm(displayed_h)
                expected_h = orbital_rotation(inc, node, peri)[:, 2]
                assert_allclose(displayed_h, expected_h, atol=1e-13)
                if inclination > 90:
                    self.assertLess(displayed_h[2], 0)

    def test_coplanar_endpoints_remove_undefined_crossing_markers_and_labels(self):
        for inclination, eccentricity in ((0, 0.99), (180, 0)):
            self.set_controls(I=inclination, e=eccentricity)
            self.page.plot.canvas.draw()
            self.assertEqual(self.page.node_markers, {})
            self.assertEqual(self.page.node_labels, {})
            self.assertIsNone(self.page.motion_segment)
            self.assertIsNone(self.page.motion_arrow)
            self.assertIn("ascending node is undefined", self.page.degeneracy.text())
            self.assertTrue(self.page.degeneracy.isVisible())
            if eccentricity == 0:
                self.assertIn("periapsis is arbitrary", self.page.degeneracy.text())


if __name__ == "__main__":
    unittest.main()
