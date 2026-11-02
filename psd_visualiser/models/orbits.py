"""Keplerian orbital geometry (Tremaine §1.3.2; Murray & Dermott §2.8)."""

import numpy as np


def _validate_ellipse(a: float, e: float) -> None:
    if not np.isfinite(a) or a <= 0:
        raise ValueError("The semi-major axis must be finite and positive.")
    if not np.isfinite(e) or not 0 <= e < 1:
        raise ValueError("Elliptical eccentricity must satisfy 0 ≤ e < 1.")


def orbital_rotation(
    inclination: float, longitude_node: float, argument_periapsis: float
) -> np.ndarray:
    """Return Rz(Ω) Rx(I) Rz(ω), mapping orbital to reference coordinates.

    The reference plane is z=0. The positive x direction defines zero
    longitude, and the orbital angular momentum points along the rotated +z.
    At coplanar inclinations Ω remains a coordinate convention.
    """
    angles = np.asarray([inclination, longitude_node, argument_periapsis], dtype=float)
    if not np.all(np.isfinite(angles)):
        raise ValueError("Orbital orientation angles must be finite.")
    c_i, c_o, c_w = np.cos(angles)
    s_i, s_o, s_w = np.sin(angles)
    return np.array(
        [
            [c_o * c_w - s_o * s_w * c_i, -c_o * s_w - s_o * c_w * c_i, s_o * s_i],
            [s_o * c_w + c_o * s_w * c_i, -s_o * s_w + c_o * c_w * c_i, -c_o * s_i],
            [s_w * s_i, c_w * s_i, c_i],
        ]
    )


def orbital_position(
    a: float,
    e: float,
    inclination: float,
    longitude_node: float,
    argument_periapsis: float,
    true_anomaly,
) -> np.ndarray:
    """Return reference-frame position(s), shape (..., 3), for true anomaly f.

    A circular orbit is well-defined even though its periapsis direction and
    the separate ω and f values are conventional.
    """
    _validate_ellipse(a, e)
    anomaly = np.asarray(true_anomaly, dtype=float)
    if not np.all(np.isfinite(anomaly)):
        raise ValueError("True anomaly must be finite.")
    radius = a * (1 - e * e) / (1 + e * np.cos(anomaly))
    orbital = np.stack(
        (radius * np.cos(anomaly), radius * np.sin(anomaly), np.zeros_like(anomaly)),
        axis=-1,
    )
    return orbital @ orbital_rotation(inclination, longitude_node, argument_periapsis).T


def orbital_curve(
    a: float,
    e: float,
    inclination: float,
    longitude_node: float,
    argument_periapsis: float,
    count: int = 501,
) -> np.ndarray:
    """Return a closed orbit curve, shape (count, 3), for display.

    Uniform eccentric-anomaly sampling resolves highly eccentric ellipses
    smoothly without concentrating points near periapsis as uniform true
    anomaly does. This samples geometry, rather than equal time intervals.
    The default odd count includes both periapsis and apoapsis exactly.
    """
    _validate_ellipse(a, e)
    rotation = orbital_rotation(inclination, longitude_node, argument_periapsis)
    if isinstance(count, bool) or not isinstance(count, (int, np.integer)) or count < 5:
        raise ValueError("An orbit curve needs an integer count of at least five points.")
    eccentric_anomaly = np.linspace(0, 2 * np.pi, count)
    orbital = a * np.stack(
        (np.cos(eccentric_anomaly) - e,
         np.sqrt(1 - e * e) * np.sin(eccentric_anomaly),
         np.zeros_like(eccentric_anomaly)),
        axis=-1,
    )
    curve = orbital @ rotation.T
    curve[-1] = curve[0]
    return curve
