"""Isotropic orbit normals and their standard orbital inclinations."""

import numpy as np


def sample_directions(count: int = 10, rng=None) -> np.ndarray:
    """Draw unit vectors uniformly in solid angle, shape (count, 3).

    Uniform azimuth and uniform z (rather than uniform inclination) give
    p(I)=sin(I)/2 on [0, π]. Supply a Generator for reproducible tests.
    """
    if isinstance(count, bool) or not isinstance(count, (int, np.integer)) or count < 0:
        raise ValueError("The number of directions must be a non-negative integer.")
    if rng is None:
        rng = np.random.default_rng()
    azimuth = rng.uniform(0, 2 * np.pi, count)
    z = rng.uniform(-1, 1, count)
    radial = np.sqrt(np.maximum(0, 1 - z * z))
    return np.column_stack((radial * np.cos(azimuth), radial * np.sin(azimuth), z))


def inclinations(vectors) -> np.ndarray:
    """Angle(s) between orbit normal(s) and +z, in radians on [0, π]."""
    values = np.asarray(vectors, dtype=float)
    if values.ndim < 1 or values.shape[-1] != 3 or not np.all(np.isfinite(values)):
        raise ValueError("Vectors must have finite coordinates and shape (..., 3).")
    lengths = np.linalg.norm(values, axis=-1)
    if np.any(lengths <= 0):
        raise ValueError("A zero vector has no inclination.")
    return np.arccos(np.clip(values[..., 2] / lengths, -1, 1))


def inclination_bin_probabilities(edges_radians) -> np.ndarray:
    """Exact isotropic probability per bin: (cos lower − cos upper)/2."""
    edges = np.asarray(edges_radians, dtype=float)
    if (
        edges.ndim != 1 or edges.size < 2 or not np.all(np.isfinite(edges))
        or np.any(np.diff(edges) <= 0) or edges[0] < 0 or edges[-1] > np.pi
    ):
        raise ValueError("Bin edges must increase within [0, π].")
    return 0.5 * (np.cos(edges[:-1]) - np.cos(edges[1:]))
