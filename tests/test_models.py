"""Scientific invariants for the teaching visualisations (no GUI required)."""

import unittest

import numpy as np
from numpy.testing import assert_allclose

from psd_visualiser.models.orbits import orbital_curve, orbital_position, orbital_rotation
from psd_visualiser.models.guiding import (
    first_order_relative, from_guiding_frame, guiding_centre, kepler_position,
    signed_angle, solve_kepler, to_guiding_frame, true_anomaly,
)
from psd_visualiser.models.inclinations import (
    inclination_bin_probabilities, inclinations, sample_directions,
)


class OrbitalGeometryTests(unittest.TestCase):
    def test_periapsis_apoapsis_and_planarity(self):
        a, e = 2.3, 0.65
        rotation = orbital_rotation(0.7, 1.2, 0.9)
        points = orbital_position(a, e, 0.7, 1.2, 0.9, np.array([0, np.pi]))
        assert_allclose(np.linalg.norm(points, axis=-1), [a * (1 - e), a * (1 + e)])
        assert_allclose(points @ rotation[:, 2], 0, atol=1e-14)

    def test_rotation_is_right_handed_and_correct_order(self):
        identity = orbital_rotation(0, 0, 0)
        assert_allclose(identity, np.eye(3))
        rotation = orbital_rotation(np.pi / 2, np.pi / 2, 0)
        assert_allclose(rotation[:, 0], [0, 1, 0], atol=1e-15)
        assert_allclose(rotation[:, 1], [0, 0, 1], atol=1e-15)
        assert_allclose(rotation.T @ rotation, np.eye(3), atol=1e-15)
        self.assertAlmostEqual(np.linalg.det(rotation), 1)

    def test_both_nodes_keep_their_crossing_sense_through_retrograde_inclinations(self):
        for degrees in (1, 30, 89, 90, 91, 150, 179):
            inclination = np.deg2rad(degrees)
            for e in (0, 0.3, 0.99):
                for node in (0, 1.2):
                    for periapsis in (0, np.pi / 3, np.pi - 0.03, np.pi):
                        normal = orbital_rotation(inclination, node, periapsis)[:, 2]
                        self.assertAlmostEqual(normal[2], np.cos(inclination))
                        if degrees < 90:
                            self.assertGreater(normal[2], 0)
                        elif degrees > 90:
                            self.assertLess(normal[2], 0)
                        for ascending in (True, False):
                            with self.subTest(I=degrees, e=e, node=node, periapsis=periapsis,
                                              ascending=ascending):
                                f_node = -periapsis + (0 if ascending else np.pi)
                                positions = orbital_position(
                                    1, e, inclination, node, periapsis,
                                    f_node + np.array([-1e-6, 0, 1e-6]),
                                )
                                sense = 1 if ascending else -1
                                self.assertLess(sense * positions[0, 2], 0)
                                self.assertGreater(sense * positions[2, 2], 0)
                                self.assertAlmostEqual(positions[1, 2], 0, delta=1e-13)
                                assert_allclose(
                                    positions[1] / np.linalg.norm(positions[1]),
                                    sense * np.array([np.cos(node), np.sin(node), 0]),
                                    atol=1e-13,
                                )
                                # Increasing f is physical forward motion for
                                # both prograde and retrograde inclinations.
                                angular_momentum = np.cross(positions[1], positions[2] - positions[0])
                                angular_momentum /= np.linalg.norm(angular_momentum)
                                assert_allclose(angular_momentum, normal, atol=2e-9)

    def test_high_eccentricity_curve_is_closed_planar_and_an_exact_ellipse(self):
        a, e = 2.3, 0.99
        rotation = orbital_rotation(0.7, 1.2, 0.9)
        curve = orbital_curve(a, e, 0.7, 1.2, 0.9)
        self.assertEqual(curve.shape, (501, 3))
        self.assertTrue(np.array_equal(curve[0], curve[-1]))
        local = curve @ rotation
        assert_allclose(local[:, 2], 0, atol=2e-15)
        ellipse_constraint = ((local[:, 0] + a * e) / a) ** 2 + (
            local[:, 1] / (a * np.sqrt(1 - e * e))
        ) ** 2
        assert_allclose(ellipse_constraint, 1, atol=2e-14, rtol=0)
        distances = np.linalg.norm(curve, axis=-1)
        self.assertAlmostEqual(float(distances.min()), 0.01 * a)
        self.assertAlmostEqual(float(distances.max()), 1.99 * a)

    def test_high_eccentricity_curve_chord_error_decreases_quadratically(self):
        a, e = 2.3, 0.99
        errors = []
        for count in (251, 501):
            curve = orbital_curve(a, e, 0.7, 1.2, 0.9, count)
            eccentric = np.linspace(0, 2 * np.pi, count)
            # Independently obtain exact chord-midpoint targets through the
            # true-anomaly/radius model used for the interactive particle.
            midpoints_f = true_anomaly((eccentric[:-1] + eccentric[1:]) / 2, e)
            targets = orbital_position(a, e, 0.7, 1.2, 0.9, midpoints_f)
            errors.append(float(np.max(np.linalg.norm(targets - (curve[:-1] + curve[1:]) / 2,
                                                      axis=-1))))
        self.assertLess(errors[1] / a, 2.1e-5)
        self.assertAlmostEqual(errors[0] / errors[1], 4, delta=0.01)

    def test_curve_circular_coplanar_limits_and_count_validation(self):
        for inclination in (0, np.pi):
            curve = orbital_curve(2, 0, inclination, 1.1, 2.2)
            self.assertTrue(np.all(np.isfinite(curve)))
            assert_allclose(np.linalg.norm(curve, axis=-1), 2)
            assert_allclose(curve[:, 2], 0, atol=1e-14)
        for count in (4, 5.5, True):
            with self.assertRaises(ValueError):
                orbital_curve(1, 0.3, 0, 0, 0, count)
        with self.assertRaises(ValueError):
            orbital_curve(1, 1, 0, 0, 0)
        with self.assertRaises(ValueError):
            orbital_curve(1, 0.3, np.nan, 0, 0)

    def test_circular_and_coplanar_limits_are_finite(self):
        anomaly = np.linspace(0, 2 * np.pi, 31)
        for inclination in (0, np.pi):
            positions = orbital_position(2, 0, inclination, 1.1, 2.2, anomaly)
            self.assertTrue(np.all(np.isfinite(positions)))
            assert_allclose(np.linalg.norm(positions, axis=-1), 2)
            assert_allclose(positions[:, 2], 0, atol=1e-14)

    def test_invalid_inputs_rejected(self):
        for a, e in ((0, 0), (-1, 0.2), (1, 1), (1, -0.1), (np.nan, 0.1)):
            with self.assertRaises(ValueError):
                orbital_position(a, e, 0, 0, 0, 0)
        with self.assertRaises(ValueError):
            orbital_rotation(0, np.inf, 0)


class GuidingCentreTests(unittest.TestCase):
    def test_kepler_residual_for_arrays_and_unwrapped_phases(self):
        mean = np.linspace(-8 * np.pi, 8 * np.pi, 1001)
        for e in (0, 0.2, 0.5, 0.9, 0.9999):
            eccentric = solve_kepler(mean, e)
            assert_allclose(eccentric - e * np.sin(eccentric), mean, atol=2e-14, rtol=0)
            scalar = solve_kepler(1.4, e)
            self.assertAlmostEqual(float(scalar - e * np.sin(scalar)), 1.4, places=13)

    def test_exact_periodicity_and_orbital_radius(self):
        mean = np.linspace(0, 2 * np.pi, 70)
        eccentricity = 0.4
        points = kepler_position(mean, eccentricity, 2)
        assert_allclose(kepler_position(mean + 4 * np.pi, eccentricity, 2), points, atol=2e-14)
        eccentric = solve_kepler(mean, eccentricity)
        anomaly = true_anomaly(eccentric, eccentricity)
        radius = 2 * (1 - eccentricity ** 2) / (1 + eccentricity * np.cos(anomaly))
        assert_allclose(np.linalg.norm(points, axis=-1), radius)

    def test_transform_inverse_origin_focus_and_distances(self):
        points = np.array([[0.2, -1.4], [2.1, 0.7], [-0.6, 0.8]])
        for mean in (0, 0.8, 4.3):
            relative = to_guiding_frame(points, mean, 1.7)
            assert_allclose(from_guiding_frame(relative, mean, 1.7), points, atol=2e-15)
            assert_allclose(to_guiding_frame(guiding_centre(mean, 1.7), mean, 1.7), [0, 0])
            assert_allclose(to_guiding_frame([0, 0], mean, 1.7), [-1.7, 0], atol=2e-15)
            self.assertAlmostEqual(np.linalg.norm(relative[1] - relative[0]),
                                   np.linalg.norm(points[1] - points[0]))

    def test_vector_phase_frame_transform(self):
        mean = np.linspace(0, 2 * np.pi, 100)
        points = kepler_position(mean, 0.2)
        relative = to_guiding_frame(points, mean)
        assert_allclose(from_guiding_frame(relative, mean), points, atol=1e-15)
        anomaly = true_anomaly(solve_kepler(mean, 0.2), 0.2)
        radii = np.linalg.norm(points, axis=-1)
        assert_allclose(relative[:, 0], radii * np.cos(anomaly - mean) - 1, atol=2e-15)
        assert_allclose(relative[:, 1], radii * np.sin(anomaly - mean), atol=2e-15)

    def test_first_order_error_is_second_order_in_eccentricity(self):
        mean = np.linspace(0, 2 * np.pi, 500)
        errors = []
        for e in (0.02, 0.01):
            exact = to_guiding_frame(kepler_position(mean, e), mean)
            errors.append(np.max(np.linalg.norm(exact - first_order_relative(mean, e), axis=-1)))
        self.assertGreater(errors[0] / errors[1], 3.8)
        self.assertLess(errors[0] / errors[1], 4.2)

    def test_epicycle_axes_and_retrograde_direction(self):
        points = first_order_relative(np.array([0, np.pi / 2, np.pi]), 0.2)
        assert_allclose(points, [[-0.2, 0], [0, 0.4], [0.2, 0]], atol=1e-15)
        # At the leftmost point the motion is upward, hence clockwise.
        self.assertLess(np.linalg.det(np.array([points[0], points[1]])), 0)

    def test_circular_limit_and_signed_equation_of_centre(self):
        mean = np.linspace(0, 2 * np.pi, 41)
        assert_allclose(kepler_position(mean, 0), guiding_centre(mean))
        assert_allclose(first_order_relative(mean, 0), 0)
        assert_allclose(to_guiding_frame(kepler_position(mean, 0), mean), 0)
        anomaly = true_anomaly(solve_kepler(mean, 0.3), 0.3)
        delta = signed_angle(anomaly - mean)
        self.assertTrue(np.all(delta[1:20] > 0))
        self.assertTrue(np.all(delta[21:-1] < 0))
        assert_allclose(delta[[0, 20, 40]], 0, atol=1e-14)
        assert_allclose(signed_angle(np.array([2 * np.pi - 0.1, -2 * np.pi + 0.1])), [-0.1, 0.1])

    def test_invalid_inputs_rejected(self):
        for function in (solve_kepler, kepler_position, first_order_relative):
            with self.assertRaises(ValueError):
                function(0, 1)
        with self.assertRaises(ValueError):
            solve_kepler(np.inf, 0.2)
        with self.assertRaises(ValueError):
            to_guiding_frame([0, np.nan], 0)


class IsotropicInclinationTests(unittest.TestCase):
    def test_seeded_sphere_statistics(self):
        vectors = sample_directions(100_000, np.random.default_rng(2026))
        assert_allclose(np.linalg.norm(vectors, axis=-1), 1, atol=1e-15)
        assert_allclose(np.mean(vectors, axis=0), 0, atol=0.006)
        assert_allclose(np.mean(vectors ** 2, axis=0), 1 / 3, atol=0.006)
        self.assertAlmostEqual(float(np.mean(np.sin(inclinations(vectors)))), np.pi / 4, delta=0.005)
        # Azimuth remains uniform and independent of z.
        assert_allclose(np.mean(vectors[:, :2] * vectors[:, 2, None], axis=0), 0, atol=0.006)

    def test_standard_angle_and_non_unit_vectors(self):
        vectors = [[0, 0, 3], [0, 4, 0], [0, 0, -2]]
        assert_allclose(inclinations(vectors), [0, np.pi / 2, np.pi])

    def test_probabilities_match_uniform_cosine_and_normalise(self):
        edges = np.deg2rad(np.arange(0, 181, 15))
        probability = inclination_bin_probabilities(edges)
        self.assertAlmostEqual(float(np.sum(probability)), 1)
        assert_allclose(probability, probability[::-1], atol=2e-16)
        self.assertGreater(probability[5], probability[0])
        assert_allclose(inclination_bin_probabilities([0, np.pi / 2, np.pi]), [0.5, 0.5])

    def test_randomise_draw_size_and_reproducibility(self):
        first = sample_directions(10, np.random.default_rng(8))
        second = sample_directions(10, np.random.default_rng(8))
        assert_allclose(first, second)
        self.assertEqual(first.shape, (10, 3))
        self.assertEqual(sample_directions(0).shape, (0, 3))

    def test_invalid_inputs_rejected(self):
        for count in (-1, 1.5, True):
            with self.assertRaises(ValueError):
                sample_directions(count)
        for vector in ([0, 0, 0], [1, np.nan, 0], [1, 2]):
            with self.assertRaises(ValueError):
                inclinations(vector)
        for edges in ([0], [-0.1, 1], [1, 0], [0, 4], [0, np.inf]):
            with self.assertRaises(ValueError):
                inclination_bin_probabilities(edges)


if __name__ == "__main__":
    unittest.main()
