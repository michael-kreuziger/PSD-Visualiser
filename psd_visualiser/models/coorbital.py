"""Planar circular restricted three-body dynamics in barycentric units.

The primary separation, G(m_star + m_planet), and binary angular speed are
one.  The primaries sit at (-mu, 0) and (1-mu, 0).  ``effective_potential``
uses the positive convention Omega; Tremaine's Phi_eff = -Omega and
E_J = -C_J/2.  Trajectories solve the full equations, not a coorbital average.

References: Murray & Dermott, Solar System Dynamics, §§3.2–3.10;
Tremaine, Dynamics of Planetary Systems, §§3.1–3.2.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import math

import numpy as np


MIN_MU = 1e-5
MAX_MU = 0.1
ROUTH_MU = (1 - np.sqrt(23/27)) / 2
TADPOLE_ANGLE_RANGE = (20.0, 85.0)
VALIDATED_TADPOLE_ANGLE_RANGE = (30.0, 55.0)
HORSESHOE_ANGLE_RANGE = (12.0, 23.0)


def recommended_angle_range(mu, orbit):
    """UI ranges, including exploratory launches outside the checked envelope.

    The smaller horseshoe range at mu<=.001 was checked for the legacy
    unit-radius, zero-rotating-velocity launch. Changed osculating elements,
    wider tadpole angles, higher mu, or radial kicks may leave the requested
    family. ``checked_example`` verifies the actual launch separately.
    These are not stability boundaries.
    """
    _validate_mu(mu)
    if orbit == "tadpole":
        return TADPOLE_ANGLE_RANGE
    if orbit != "horseshoe":
        raise ValueError("orbit must be 'tadpole' or 'horseshoe'")
    if mu > .001:
        return 12., 80.
    minimum = max(HORSESHOE_ANGLE_RANGE[0], 10 + 12*np.sqrt(mu/.001))
    return math.ceil(minimum*10 - 1e-10)/10, HORSESHOE_ANGLE_RANGE[1]


def _validate_mu(mu):
    if not np.isfinite(mu) or not 0 < mu <= 0.5:
        raise ValueError("mu must satisfy 0 < mu <= 0.5")


def effective_potential(x, y, mu):
    """Positive Omega = (x²+y²)/2 + (1-mu)/r_star + mu/r_planet.

    Point-mass singularities are infinite and should be masked for plotting.
    """
    _validate_mu(mu)
    x, y = np.asarray(x), np.asarray(y)
    with np.errstate(divide="ignore", invalid="ignore"):
        return ((x*x + y*y) / 2 + (1-mu) / np.hypot(x+mu, y)
                + mu / np.hypot(x-1+mu, y))


def jacobi_constant(states, mu):
    """C_J = 2 Omega - |v_rot|² for (..., 4) states [x,y,vx,vy]."""
    states = np.asarray(states, dtype=float)
    return (2 * effective_potential(states[..., 0], states[..., 1], mu)
            - np.sum(states[..., 2:4]**2, axis=-1))


def derivatives(t, state, mu):
    """Autonomous rotating-frame CR3BP right-hand side (n=1)."""
    x, y, vx, vy = state
    r1 = math.hypot(x+mu, y)
    r2 = math.hypot(x-1+mu, y)
    g1, g2 = (1-mu) / r1**3, mu / r2**3
    return np.array([vx, vy, 2*vy + x - g1*(x+mu) - g2*(x-1+mu),
                     -2*vx + y - (g1+g2)*y])


def lagrange_points(mu):
    """All five equilibria; collinear points are solved by bisection."""
    _validate_mu(mu)

    def force(x):
        r1, r2 = x+mu, x-1+mu
        return x - (1-mu)*r1/abs(r1)**3 - mu*r2/abs(r2)**3

    def root(a, b):
        fa = force(a)
        for _ in range(100):
            middle = (a+b)/2
            fm = force(middle)
            if fa * fm > 0:
                a, fa = middle, fm
            else:
                b = middle
        return (a+b)/2

    eps = 1e-12
    return {
        "L1": np.array([root(-mu+eps, 1-mu-eps), 0.]),
        "L2": np.array([root(1-mu+eps, 3.), 0.]),
        "L3": np.array([root(-3., -mu-eps), 0.]),
        "L4": np.array([0.5-mu, np.sqrt(3)/2]),
        "L5": np.array([0.5-mu, -np.sqrt(3)/2]),
    }


def rotating_to_inertial(points, time):
    """Rotate barycentric points by +nt; each history sample uses its own t."""
    points = np.asarray(points, dtype=float)
    c, s = np.cos(time), np.sin(time)
    return np.stack((c*points[..., 0] - s*points[..., 1],
                     s*points[..., 0] + c*points[..., 1]), axis=-1)


def rotating_velocity_to_inertial(positions, velocities, time):
    """v_inertial = R(t) [v_rot + zhat cross r_rot]."""
    positions, velocities = np.asarray(positions), np.asarray(velocities)
    transport = np.stack((-positions[..., 1], positions[..., 0]), axis=-1)
    return rotating_to_inertial(velocities + transport, time)


def initial_state(mu, orbit, angle_deg, *, radial_speed=0.):
    """Start at r_star=1 with zero angular speed and a radial velocity.

    The angle is an initial condition, not a promise of the eventual family.
    ``radial_speed`` is in units n*a, directed outwards from the star.
    It excites epicyclic motion but is not an eccentricity control. For a
    time-reversed reflected L5 counterpart negate both angle and kick.
    """
    _validate_mu(mu)
    if orbit not in ("tadpole", "horseshoe"):
        raise ValueError("orbit must be 'tadpole' or 'horseshoe'")
    if not np.isfinite(angle_deg) or not 0 < abs(angle_deg) < 180:
        raise ValueError("starting longitude must have 0 < |angle| < 180 degrees")
    if not np.isfinite(radial_speed):
        raise ValueError("radial_speed must be finite")
    angle = np.deg2rad(angle_deg)
    return np.array([np.cos(angle)-mu, np.sin(angle),
                     radial_speed*np.cos(angle), radial_speed*np.sin(angle)])


def _validate_eccentricity(eccentricity):
    if not np.isfinite(eccentricity) or not 0 <= eccentricity < 1:
        raise ValueError("eccentricity must satisfy 0 <= eccentricity < 1")


def initial_state_from_eccentricity(mu, orbit, angle_deg, eccentricity):
    """Exact star-centred osculating Kepler elements for an outward launch.

    The fixed osculating semimajor axis a0=(1-mu)^(1/3) gives initial Kepler
    mean motion sqrt((1-mu)/a0^3)=1.  E0=pi/2 fixes the eccentric phase:
    r=a0, v_r=a0*e0, v_t=a0*sqrt(1-e0^2). The polar longitude is angle_deg;
    its periapse direction is therefore angle_deg-acos(-e0). Velocities are
    converted from star-relative inertial components to the rotating frame.
    These osculating elements evolve under the planet's gravity.
    """
    initial_state(mu, orbit, angle_deg)  # Shared mu/family/longitude validation.
    _validate_eccentricity(eccentricity)
    angle = np.deg2rad(angle_deg)
    radial = np.array([np.cos(angle), np.sin(angle)])
    tangential = np.array([-radial[1], radial[0]])
    a0 = np.cbrt(1-mu)
    position = a0*radial - [mu, 0.]
    velocity = a0*(eccentricity*radial + (np.sqrt(1-eccentricity**2)-1)*tangential)
    return np.concatenate((position, velocity))


def osculating_eccentricity(states, mu):
    """Instantaneous star-centred two-body eccentricity of (...,4) states.

    The inertial star-relative velocity, in rotating components, is
    v_rot + zhat cross (r_particle-r_star).  The planet perturbs these
    osculating elements; neither eccentricity nor Kepler energy is conserved.
    """
    _validate_mu(mu)
    states = np.asarray(states, dtype=float)
    x, y = states[..., 0]+mu, states[..., 1]
    vx, vy = states[..., 2]-y, states[..., 3]+x
    radius = np.hypot(x, y)
    h = x*vy-y*vx
    ex, ey = vy*h/(1-mu)-x/radius, -vx*h/(1-mu)-y/radius
    return np.hypot(ex, ey)


@dataclass(frozen=True)
class Trajectory:
    times: np.ndarray
    states: np.ndarray
    jacobi: np.ndarray
    classification: str
    completed: bool
    message: str


@dataclass(frozen=True)
class CheckedExample:
    """Launch whose full CR3BP trajectory passed a finite-window check."""
    angle_deg: float
    radial_speed: float
    classification: str
    checked_periods: float
    jacobi_drift: float
    eccentricity: float | None = None


def _classify(states, mu):
    """Finite-window geometric classification; does not claim stability."""
    if np.linalg.norm(derivatives(0, states[0], mu)) < 1e-10 and np.max(np.abs(states-states[0])) < 1e-8:
        name = "L4" if states[0, 1] > 0 else "L5"
        return name + (" equilibrium (linearly unstable)" if mu >= ROUTH_MU else " equilibrium")
    if mu >= ROUTH_MU:
        return "exploratory (L4/L5 unstable)"
    radius = np.hypot(states[:, 0]+mu, states[:, 1])
    if np.min(radius) < 0.5 or np.max(radius) > 1.6:
        return "non-coorbital / transition"
    theta = np.unwrap(np.arctan2(states[:, 1], states[:, 0]+mu))
    if np.ptp(theta) >= 2*np.pi:
        return "circulating / transition"
    theta = theta - 2*np.pi*np.floor(np.mean(theta) / (2*np.pi))
    low, high = np.min(theta), np.max(theta)
    if low > 0 and low < np.pi/3 < high and high < np.pi:
        return "tadpole L4"
    if low > np.pi and low < 5*np.pi/3 < high and high < 2*np.pi:
        return "tadpole L5"
    if low > 0 and high < 2*np.pi and low < np.pi < high:
        return "horseshoe"
    return "unresolved / transition"


def integrate_orbit(mu, orbit, angle_deg, periods=2., samples=None,
                    *, radial_speed=0., eccentricity=None, rtol=2e-10, atol=2e-12):
    """Integrate using adaptive Dormand–Prince 5(4), with sampled output.

    ``periods`` counts the reference timescale T_ref=2pi/sqrt(27mu/4).
    This is a small-mu, small-amplitude libration estimate only; it is not
    a physical libration period at large mu or above the stability limit.
    An explicit ``eccentricity`` selects the exact osculating-element launch
    at fixed semimajor axis and E0=pi/2. ``None`` retains the earlier unit-
    radius radial-speed launch for numerical reference checks.
    With ``samples=None``, output spacing is at most 0.1 time units (at
    least 63 vertices per binary orbit), resolving inertial-frame loops.
    Each output state is an accepted integration endpoint, so no low-order
    interpolation error is introduced into the Jacobi diagnostic.
    A close approach within 0.1 times the nominal Hill scale (mu/3)^(1/3)
    or r_star<0.02 stops integration. This is a numerical guard, not an
    exact encounter boundary at large mass ratio.
    """
    if eccentricity is None:
        state = initial_state(mu, orbit, angle_deg, radial_speed=radial_speed)
    else:
        if radial_speed != 0:
            raise ValueError("select eccentricity or a legacy radial_speed, not both")
        state = initial_state_from_eccentricity(mu, orbit, angle_deg, eccentricity)
    if not np.isfinite(periods) or not 0 < periods <= 10:
        raise ValueError("periods must satisfy 0 < periods <= 10")
    if not np.isfinite(rtol) or not np.isfinite(atol) or rtol <= 0 or atol <= 0:
        raise ValueError("integration tolerances must be positive and finite")
    duration = periods * 2*np.pi / np.sqrt(27*mu/4)
    if samples is None:
        samples = max(4001, math.ceil(duration/0.1)+1)
    if not isinstance(samples, (int, np.integer)) or samples < 3:
        raise ValueError("samples must be an integer >= 3")
    requested = np.linspace(0., duration, samples)
    states, times = [state.copy()], [0.]
    t, h = 0., min(0.1, requested[1])
    hill_cutoff = 0.1 * (mu/3)**(1/3)
    message, completed = "Finite integration; long-term stability is not established.", True
    # Dormand–Prince tableau (FSAL; retain k7 after accepting a step).
    k1 = derivatives(t, state, mu)
    attempts = 0
    for target in requested[1:]:
        while t < target:
            h = min(h, target-t, 0.5)
            k2 = derivatives(t+h/5, state+h*(k1/5), mu)
            k3 = derivatives(t+3*h/10, state+h*(3*k1/40+9*k2/40), mu)
            k4 = derivatives(t+4*h/5, state+h*(44*k1/45-56*k2/15+32*k3/9), mu)
            k5 = derivatives(t+8*h/9, state+h*(19372*k1/6561-25360*k2/2187+64448*k3/6561-212*k4/729), mu)
            k6 = derivatives(t+h, state+h*(9017*k1/3168-355*k2/33+46732*k3/5247+49*k4/176-5103*k5/18656), mu)
            candidate = state+h*(35*k1/384+500*k3/1113+125*k4/192-2187*k5/6784+11*k6/84)
            k7 = derivatives(t+h, candidate, mu)
            error = h*(71*k1/57600-71*k3/16695+71*k4/1920-17253*k5/339200+22*k6/525-k7/40)
            scale = atol + rtol*np.maximum(np.abs(state), np.abs(candidate))
            norm = np.max(np.abs(error)/scale)
            attempts += 1
            if not np.isfinite(norm) or h < 1e-11 or attempts > 500000:
                completed, message = False, "Integration stopped: required numerical resolution exceeded."
                break
            if norm <= 1:
                t, state, k1 = t+h, candidate, k7
                # Snap floating-point endpoint to the requested sample epoch.
                if abs(t-target) < 1e-12*max(1., abs(target)):
                    t = target
                r1, r2 = math.hypot(state[0]+mu, state[1]), math.hypot(state[0]-1+mu, state[1])
                if r1 < 0.02 or r2 < hill_cutoff or r1 > 5:
                    completed, message = False, "Integration stopped at a close encounter or departure from the coorbital region."
                    break
            h *= 5. if norm == 0 else min(5., max(0.2, 0.9*norm**(-0.2)))
        if not completed:
            if t > times[-1]:
                times.append(t)
                states.append(state.copy())
            break
        times.append(t)
        states.append(state.copy())
    states, times = np.asarray(states), np.asarray(times)
    jacobi = jacobi_constant(states, mu)
    classification = _classify(states, mu) if completed else "encounter / transition"
    if not classification.startswith(orbit):
        message = "The selected family is not established by this finite integration. " + message
    if mu >= ROUTH_MU:
        message += (f" L4 and L5 are linearly unstable for mu >= {ROUTH_MU:.7f}; "
                    "the selected family is only a launch preset.")
    elif (mu > .001 or radial_speed != 0 or eccentricity is not None or
          (orbit == "tadpole" and not VALIDATED_TADPOLE_ANGLE_RANGE[0] <= abs(angle_deg) <= VALIDATED_TADPOLE_ANGLE_RANGE[1])):
        message += " Exploratory initial conditions do not guarantee the selected orbit family."
    return Trajectory(times, states, jacobi, classification, completed, message)


@lru_cache(maxsize=128)
def checked_example(mu, orbit, centre="L4", *, eccentricity=None):
    """Find and check a launch at exactly ``mu``, or return ``None``.

    This is a finite six-reference-timescale tadpole check (ten for
    horseshoes), not a claim of regularity
    or long-term stability.  The test requires bounded coorbital radius,
    conserved Jacobi constant, the selected geometric family, and repeated
    crossings demonstrating both longitude reversals.  Tadpole examples
    narrow towards L4/L5 as mu approaches the linear stability boundary.

    Above Routh's limit no tadpole example is supplied. Horseshoe candidate
    searches are restricted to mu<=.001; a missing checked example makes no
    assertion that other horseshoe solutions do not exist.  Free exploration
    uses ``integrate_orbit`` at every allowed mass ratio.

    Passing eccentricity explicitly (including zero) checks the fixed-a0,
    E0=pi/2 launch at that exact requested eccentricity. ``None`` checks the
    legacy unit-radius launch; those profiles cannot validate the newer ICs.
    """
    _validate_mu(mu)
    if eccentricity is not None:
        _validate_eccentricity(eccentricity)
    if orbit not in ("tadpole", "horseshoe"):
        raise ValueError("orbit must be 'tadpole' or 'horseshoe'")
    if centre not in ("L4", "L5"):
        raise ValueError("centre must be 'L4' or 'L5'")
    if not MIN_MU <= mu <= MAX_MU:
        return None
    if orbit == "tadpole":
        if mu >= ROUTH_MU:
            return None
        preferred = next(angle for upper, angle in (
            (.003, 40.), (.01, 50.), (.02, 55.), (.03, 58.),
            (.035, 59.), (.038, 59.5), (.0384, 59.9),
            (.0385, 59.99), (ROUTH_MU, 59.999),
        ) if mu <= upper)
        candidates = tuple(dict.fromkeys([preferred, (60+preferred)/2, 59.99, 59.999]))
        sign = -1 if centre == "L5" else 1
        checked_periods = 6.
    else:
        if mu > .001:
            return None
        preferred = 20. if mu <= .0005 else 23.
        candidates = tuple(dict.fromkeys([preferred, 23., 22.5, 22.]))
        sign = 1
        checked_periods = 10.

    # Match the editable control before integrating; otherwise a fallback
    # such as 59.9995 degrees could be checked but displayed as exactly L4.
    candidates = tuple(angle for angle in dict.fromkeys(round(float(a), 3) for a in candidates)
                       if orbit != "tadpole" or angle < 60.)
    for angle in candidates:
        result = integrate_orbit(mu, orbit, sign*angle, periods=checked_periods, samples=3001,
                                 eccentricity=eccentricity)
        if not result.completed or not result.classification.startswith(orbit):
            continue
        radius = np.hypot(result.states[:, 0]+mu, result.states[:, 1])
        drift = float(np.max(np.abs(result.jacobi-result.jacobi[0])))
        if radius.min() < .65 or radius.max() > 1.35 or drift > 5e-9:
            continue
        theta = np.unwrap(np.arctan2(result.states[:, 1], result.states[:, 0]+mu))
        if orbit == "tadpole":
            theta *= sign
            displacement = theta - np.pi/3
            enough_reversals = np.count_nonzero(displacement[1:]*displacement[:-1] < 0) >= 6
        else:
            displacement = theta - np.pi
            enough_reversals = (theta.min() < np.pi/3 and theta.max() > 5*np.pi/3
                                and np.count_nonzero(displacement[1:]*displacement[:-1] < 0) >= 3)
        if enough_reversals:
            return CheckedExample(sign*angle, 0., result.classification, checked_periods, drift,
                                  eccentricity=eccentricity)
    return None
