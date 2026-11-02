"""Exact and first-order guiding-centre motion (Murray & Dermott §2.6).

The focus is at the inertial origin and periapsis is on +x. Rotating-frame
coordinates are centred on G, with +x radially outward and +y prograde.
"""

import numpy as np

from .orbits import _validate_ellipse


def _finite_angle(angle):
    values = np.asarray(angle, dtype=float)
    if not np.all(np.isfinite(values)):
        raise ValueError("Angles must be finite.")
    return values


def signed_angle(angle):
    """Wrap an angle to [-π, π], preserving the sign of small differences."""
    values = _finite_angle(angle)
    return np.arctan2(np.sin(values), np.cos(values))


def solve_kepler(mean_anomaly, e: float):
    """Solve E − e sin E = M for an ellipse, retaining complete revolutions.

    A bracketed Newton iteration remains stable for eccentricities near one.
    Scalar and array anomalies are supported; e is a scalar.
    """
    _validate_ellipse(1.0, e)
    mean = _finite_angle(mean_anomaly)
    if e == 0:
        return mean.copy()
    reduced = (mean + np.pi) % (2 * np.pi) - np.pi
    lower = np.full_like(reduced, -np.pi)
    upper = np.full_like(reduced, np.pi)
    eccentric = reduced.copy() if e < 0.8 else np.sign(reduced) * np.pi
    for _ in range(80):
        residual = eccentric - e * np.sin(eccentric) - reduced
        if np.all(np.abs(residual) < 4e-15):
            break
        lower = np.where(residual < 0, eccentric, lower)
        upper = np.where(residual >= 0, eccentric, upper)
        proposal = eccentric - residual / (1 - e * np.cos(eccentric))
        in_bracket = (proposal > lower) & (proposal < upper)
        eccentric = np.where(in_bracket, proposal, 0.5 * (lower + upper))
    return eccentric + (mean - reduced)


def true_anomaly(eccentric_anomaly, e: float):
    """Return true anomaly in [0, 2π) from eccentric anomaly."""
    _validate_ellipse(1.0, e)
    eccentric = _finite_angle(eccentric_anomaly)
    result = np.arctan2(np.sqrt(1 - e * e) * np.sin(eccentric), np.cos(eccentric) - e)
    return result % (2 * np.pi)


def kepler_position(mean_anomaly, e: float, a: float = 1.0) -> np.ndarray:
    """Exact inertial particle position(s), shape (..., 2)."""
    _validate_ellipse(a, e)
    eccentric = solve_kepler(mean_anomaly, e)
    return a * np.stack(
        (np.cos(eccentric) - e, np.sqrt(1 - e * e) * np.sin(eccentric)), axis=-1
    )


def guiding_centre(mean_anomaly, a: float = 1.0) -> np.ndarray:
    """Position(s) of G, which circles the focus at uniform mean motion."""
    _validate_ellipse(a, 0.0)
    mean = _finite_angle(mean_anomaly)
    return a * np.stack((np.cos(mean), np.sin(mean)), axis=-1)


def first_order_relative(mean_anomaly, e: float, a: float = 1.0) -> np.ndarray:
    """First-order epicycle (−ae cos M, 2ae sin M), relative to G."""
    _validate_ellipse(a, e)
    mean = _finite_angle(mean_anomaly)
    return a * e * np.stack((-np.cos(mean), 2 * np.sin(mean)), axis=-1)


def _finite_points(points):
    values = np.asarray(points, dtype=float)
    if values.ndim < 1 or values.shape[-1] != 2 or not np.all(np.isfinite(values)):
        raise ValueError("Points must have finite coordinates and shape (..., 2).")
    return values


def to_guiding_frame(points, mean_anomaly, a: float = 1.0) -> np.ndarray:
    """Apply R(−M)(X−G) to inertial point(s), using NumPy broadcasting.

    With a scalar phase, transform any array of points at that instant. With
    an array of phases, transform the corresponding particle positions.
    """
    values = _finite_points(points)
    mean = _finite_angle(mean_anomaly)
    delta = values - guiding_centre(mean, a)
    cosine, sine = np.cos(mean), np.sin(mean)
    return np.stack(
        (cosine * delta[..., 0] + sine * delta[..., 1],
         -sine * delta[..., 0] + cosine * delta[..., 1]),
        axis=-1,
    )


def from_guiding_frame(points, mean_anomaly, a: float = 1.0) -> np.ndarray:
    """Invert the guiding-frame transform: G + R(M) X_rot."""
    values = _finite_points(points)
    mean = _finite_angle(mean_anomaly)
    cosine, sine = np.cos(mean), np.sin(mean)
    rotated = np.stack(
        (cosine * values[..., 0] - sine * values[..., 1],
         sine * values[..., 0] + cosine * values[..., 1]),
        axis=-1,
    )
    return rotated + guiding_centre(mean, a)
