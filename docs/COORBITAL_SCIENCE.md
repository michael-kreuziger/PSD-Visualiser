# Tadpole and horseshoe orbits: scientific conventions

This module describes the **planar circular restricted three-body problem**
(CR3BP). The star and planet are point masses in circular orbits about their
common centre of mass. The particle has zero mass, feels both gravitational
forces, and does not affect either primary. The model includes no eccentricity
of the primaries, inclination, dissipation, or other planets.

## Units, origin, and reference frames

Let `mu = m_planet / (m_star + m_planet)`. The distance between the primaries
is the length unit, their total gravitational parameter is one, and their
angular frequency is one. One planetary orbital period is therefore `2*pi`
time units. Mass ratio `mu` is not the planet-to-star ratio; the latter is
`mu / (1 - mu)`.

The origin is the barycentre in both frames. In coordinates rotating
counterclockwise with the planet, the star and planet are stationary at
`(-mu, 0)` and `(1 - mu, 0)`. For a rotating-frame position `r(t)`, the
barycentric inertial position and velocity are

```text
r_inertial(t) = R(t) r(t)
v_inertial(t) = R(t) [v_rotating(t) + (-y(t), x(t))].
```

Here `R(t)` is the usual counterclockwise planar rotation. Every historical
point in an inertial trajectory uses its **own** time in this transformation.
The star describes a circle of radius `mu` and the planet one of radius
`1 - mu`; the star is not fixed at the origin when `mu > 0`. Lagrange points
and speed-contour patterns rotate with the primaries in an inertial view.

## Equations and Jacobi constant

With `r1 = hypot(x + mu, y)` and `r2 = hypot(x - 1 + mu, y)`, define the
positive celestial-mechanics pseudopotential

```text
U(x,y) = (x*x + y*y)/2 + (1 - mu)/r1 + mu/r2.
```

The exact planar equations integrated by the module are

```text
x'' = 2*y' + x - (1 - mu)*(x + mu)/r1**3
                  - mu*(x - 1 + mu)/r2**3
y'' = -2*x' + y - (1 - mu)*y/r1**3 - mu*y/r2**3.
```

The Coriolis terms do no work. Consequently

```text
C = 2*U - (x'**2 + y'**2)
```

is an integral of motion. This is Murray & Dermott's Jacobi-constant
convention. Tremaine instead uses an effective potential `Phi_eff = -U`
and Jacobi energy `E_J = v_rotating**2/2 + Phi_eff = -C/2`. Neither the
particle's barycentric inertial energy nor its angular momentum is conserved
separately.

## Lagrange points and stability

All five points satisfy `grad(U) = 0` and have zero velocity in the rotating
frame. The triangular points are exactly

```text
L4 = (1/2 - mu, +sqrt(3)/2)
L5 = (1/2 - mu, -sqrt(3)/2).
```

They form equilateral triangles with the primaries. L4 leads the planet by
60 degrees as seen from the star; L5 trails it by 60 degrees. The collinear
points satisfy

```text
x - (1 - mu)*(x + mu)/abs(x + mu)**3
  - mu*(x - 1 + mu)/abs(x - 1 + mu)**3 = 0.
```

There is one root in each of the intervals to the left of the star (L3),
between the primaries (L1), and to the right of the planet (L2). These points
must be recomputed as `mu` changes rather than placed at fixed schematic
positions.

The collinear equilibria are unstable. The triangular equilibria have
oscillatory planar linear modes when

```text
27*mu*(1 - mu) < 1,
mu < (1 - sqrt(23/27))/2 = 0.0385208965...
```

The equality is degenerate and is not a guarantee of bounded perturbations.
The strict inequality is a **linear** result near an equilibrium; it does
not establish nonlinear stability for every mass ratio or guarantee stable
finite-amplitude tadpole or horseshoe trajectories. For small `mu`, the
slow small-amplitude frequency is approximately `sqrt(27*mu/4)` and the
libration period in planetary periods is approximately `sqrt(4/(27*mu))`.
There is also a faster epicyclic mode with frequency close to one.

The exact squared frequencies in the linearly oscillatory regime are

```text
omega_slow**2 = [1 - sqrt(1 - 27*mu*(1 - mu))]/2
omega_fast**2 = [1 + sqrt(1 - 27*mu*(1 - mu))]/2.
```

Their ratio and the allowed perturbation amplitudes change with `mu`.
Murray & Dermott also discuss nonlinear resonances between these modes
(§3.7, printed p. 94); the linear inequality alone must not be interpreted
as a guarantee of nonlinear stability for every nearby initial condition.

The current mass-ratio control uses `1e-5 <= mu <= 1e-3`, safely below
this linear threshold. The more general numerical model and its tests also
cover larger mass ratios; those are not selectable in the interface. The
equations and all five equilibrium locations remain valid above the
threshold, where a precisely unperturbed L4 or L5 is still an equilibrium
but nearby generic perturbations can grow.

## Orbit families

A tadpole trajectory librates about one triangular point. A horseshoe
trajectory visits the neighbourhoods of L4, L3, and L5 and reverses its
relative angular drift before passing the planet. These names describe the
paths in the rotating frame. In the inertial frame the particle continues
orbiting the system; a horseshoe is not a gravitationally bound orbit about
the planet. A particle inside the planet's orbit advances relative to it;
one outside falls behind. Planetary torques can change the particle's
orbital size and reverse this relative drift.

The selected family supplies initial conditions; the full CR3BP equations
then determine the motion. Small epicyclic loops and changes in osculating
eccentricity are legitimate features of the exact solution. A finite
integration is an illustration and cannot prove stability for all time.

The initial-condition construction places the particle at unit distance
from the star at a selectable longitude `phi0`. The radial-speed control
adds an outward velocity `vr` from 0 to 0.01 along the star-to-particle
direction, in units of `n*a`:

```text
(x0, y0) = (cos(phi0) - mu, sin(phi0))
(vx0, vy0) = vr * (cos(phi0), sin(phi0)).
```

The underlying numerical model accepts signed radial speeds, including
inward launches, but the current interface permits only `0 <= vr <= 0.01`.
At `vr = 0`, the particle initially
corotates with the primaries; at nonzero `vr` it has that same angular
velocity plus a radial component. This is not zero inertial velocity or
a claim of an exact circular particle orbit. At the initial instant the
star-relative tangential speed is one. Using `G*m_star = 1 - mu`, its
two-body osculating eccentricity about the star is
`sqrt(mu*mu + vr*vr)/(1 - mu)`. Thus for small `mu` and small radial kick,
`e0` is approximately `abs(vr)`. This is an instantaneous two-body element,
not a conserved eccentricity of the perturbed CR3BP orbit.

The kick excites the faster epicyclic motion, allowing visible loops
superposed on the slow tadpole libration. Near a triangular equilibrium,
there are two linear normal modes; in the small-mass, small-eccentricity
limit the fast epicycle approaches the familiar 2:1 tangential/radial
ellipse. At larger kicks the two motions couple and a trajectory can leave
the selected family. The radial-speed control therefore changes the
initial state rather than drawing a decorative epicycle around a fixed
path. Changing the starting longitude also changes the Jacobi constant
and subsequent motion; a starting longitude is not itself the measured
libration amplitude.

A leading epicyclic tadpole example uses `mu = 0.001`,
`phi0 = 60 degrees`, `vr = 0.01`, and three reference times. Its selected
speed contour is 0.02. Over that finite interval its star-relative radius
ranges approximately from 0.98877 to 1.01127. This is a numerical example,
not a proof of permanent stability.

The interface uses `-5 <= log10(mu) <= -3` and `0 <= vr <= 0.01`.
Its horseshoe starting-longitude interval was checked with zero radial kick
to provide useful bounded examples. Manually edited tadpole angles and
nonzero kicks are exploratory. These control ranges are not
analytic stability boundaries or a complete catalogue of co-orbital
solutions. The integrated path can show the selected family, a different
family, circulation, transitions, or encounters. The readout reports a
finite-window geometric description.

## Choosing an example versus exploring initial conditions

The CR3BP equations remain valid throughout the mass-ratio control range.
The same longitude and radial kick, however, do not represent the same
member of a co-orbital family at every mass ratio. Both the effective
potential and the local normal modes change with `mu`. At a larger mass
ratio, a launch far from 60 degrees or with a substantial radial kick can
be outside the local tadpole region even though infinitesimal perturbations
at L4 and L5 are linearly oscillatory. Reducing the displacement towards
the triangular point can recover a bounded small-amplitude example for
some such mass ratios; increasing integration accuracy alone does not
turn an unsuitable launch into a tadpole.

A checked example means that the particular initial conditions were
numerically integrated and displayed the requested family's motion during
the verification interval: six reference times for tadpoles or ten for
horseshoes. The helper also checks bounded star-relative radius, repeated
angular reversals, completion, and Jacobi conservation. This interval is
longer than the selectable display duration. It is not a proof of indefinite stability, a
complete search of phase space, or evidence that neighbouring settings
will remain in the same family. Free exploration must retain the actual
integrated trajectory and report departures or encounters, rather than
replace them with an idealised closed curve. If a checked example is not
available at the selected mass ratio, this does not establish that no
such orbit exists anywhere in phase space.

The interface can automatically load a checked example at the **current**
mass ratio when the mass ratio, requested family, or tadpole centre changes.
An explicit button reloads that example. Editing the starting longitude
or radial velocity clears its checked-example status and explores the
entered initial conditions. If no checked example is available, the
interface says so prominently and retains the selected mass ratio. The
plot title reports the integrated motion rather than assuming it matches
the requested family.

The current interface range lies within the checked-example catalogue's
mass-ratio range for both families. This choice of control bounds is not
a physical upper bound on all possible horseshoe or tadpole orbits. The
general model retains broader parameter support and independent numerical
benchmarks, including small tadpole launches near the triangular-point
threshold; these do not extend the current controls.

Horseshoes require their own choice of initial conditions and their own
checks. The threshold `mu = 0.0385208965...` is a theorem about the local
triangular equilibria, **not** a horseshoe-stability boundary. In the
small-mass averaged picture, increasing amplitude eventually brings a
horseshoe close enough to the planet that the slow-motion approximation
breaks down (Tremaine §3.2, printed pp. 163–164). No unrestricted stable
horseshoe preset is inferred from that approximation at large `mu`.

An irregular-looking path, fast growth away from an equilibrium, a change
of orbit family, or a close encounter does not by itself diagnose
mathematical chaos. The module does not calculate Lyapunov exponents,
frequency diffusion, or an equivalent chaos diagnostic. Its status text
describes the observed geometry and any encounter stop. A small numerical
Jacobi drift supports integration accuracy; it establishes neither
stability nor regularity of the orbit.

## Duration and playback

The duration control is a multiplier `D` of a **reference** timescale:

```text
T_ref = 2*pi / sqrt(27*mu/4)
T_ref / P_planet = sqrt(4/(27*mu))
requested integration time = D * T_ref.
```

For example, at `mu = 0.001`, one reference timescale is approximately
12.17 planet periods, so `D = 2` requests about 24.34 planet periods.
This formula approximates the slow libration period only for small mass
ratios and small libration amplitudes near a stable triangular equilibrium.
It is not the measured period of every tadpole or horseshoe. Above the
triangular stability threshold there is no corresponding stable slow
libration mode; `T_ref` remains only a convenient reference unit. If an
integration stops at an encounter, the actual integrated duration is
shorter than requested. The readout and time axis use planet periods.

Playback changes the speed at which the already calculated history is
shown, without changing the initial conditions or the integrated physical
time. Lagrange markers and contour patterns rotate with the primaries in
the inertial frame. A fixed legend identifies the distinct point symbols
in that view, while the rotating view labels the points directly. The
legend positions are not physical locations of the equilibria.

Tremaine's approximate, slowly varying, nearly circular co-orbital theory
provides useful intuition. If `phi` is the relative azimuth, its first
integral has the form

```text
Ec = a*a*phi_dot**2/2
     - 3*G*m_planet/a * [cos(phi) - 1/(2*abs(sin(phi/2)))].
```

The separatrix of this **averaged approximation** passes through
`phi = pi`; its other angular turning point is approximately 23.906 degrees.
`Ec` is not the exact Jacobi constant, and this separatrix is not a universal
boundary for arbitrary full-CR3BP initial conditions. The approximation also
fails near sufficiently close planetary encounters. The displayed
trajectories should come from the full equations above, not from contours
of this approximate first integral.

## Constant-speed and zero-velocity curves

For the Jacobi constant `C` of the chosen trajectory, the speed permitted
at a given location in the **rotating** frame obeys

```text
v_rotating(x,y)**2 = 2*U(x,y) - C.
```

An optional line labelled by speed `v0` is the level set
`2*U = C + v0*v0`. The zero-speed case `2*U = C` is the zero-velocity
curve. Regions with `2*U < C` are forbidden to that trajectory. A nonzero
speed contour does not specify a velocity direction, and these contours
are not particle trajectories. A particle need not visit all allowed
locations. If `C` lies below the minimum of `2*U`, there is no zero-velocity
curve in the plane and no forbidden region. That minimum is attained at
L4 and L5 and equals `3 - mu + mu*mu`.

For example, launching at exactly 60 degrees with a nonzero radial kick
gives `C = C(L4) - vr*vr`. Since the triangular points minimise `2*U`,
there is then no zero-velocity curve anywhere in the plane. Speeds smaller
than `abs(vr)` also have no contour for that Jacobi constant. Thus the
epicyclic example with `vr = 0.01` legitimately shows no zero-speed
curve and no contour at speed 0.005. Its selected speed 0.02 can display
a constant-speed contour. Missing zero-velocity
curves do not imply that the particle must escape.

The contour geometry depends on `mu`; speed labels also depend on the
chosen orbit through `C`. In the inertial view these remain contours of
**rotating-frame speed**, carried around with the primaries. The inertial
speed is different and is not given by `sqrt(2*U - C)`.

## Textbook cross-checks

Printed page numbers and one-based PDF page numbers differ by 15 in both
local files. The equations and interpretations above were checked directly
against the following passages in both supplied books.

| Topic | Book section | Printed pages | PDF pages |
| --- | --- | --- | --- |
| Units, barycentric rotating coordinates, and equations | Murray & Dermott, *Solar System Dynamics*, §3.2, Eqs. 3.1–3.22 | 64–67 | 79–82 |
| Jacobi constant and forbidden regions | Murray & Dermott, §3.3, Eqs. 3.27–3.29 | 68–71 | 83–86 |
| Locations of all five equilibria | Murray & Dermott, §3.6, especially Eq. 3.71 and Fig. 3.7 | 77–81 | 92–96 |
| Linear triangular-point stability and two frequencies | Murray & Dermott, §§3.7–3.8, Eqs. 3.145–3.151 | 93–96 | 108–111 |
| Exact numerical tadpole and horseshoe examples; distinction from contours | Murray & Dermott, §§3.9–3.10, Figs. 3.16–3.21 | 97–106 | 112–121 |
| Barycentre, rotating equations, opposite potential/Jacobi convention | Tremaine, *Dynamics of Planetary Systems*, §3.1, Eqs. 3.8–3.15 | 139–141 | 154–156 |
| Lagrange points and stability | Tremaine, §3.1.1, especially Eqs. 3.33–3.35 | 141–150 | 156–165 |
| Averaged co-orbital theory, families, separatrix, and approximation limits | Tremaine, §3.2, Eqs. 3.48–3.53 and Fig. 3.5 | 159–164 | 174–179 |

Local source PDFs: [Murray & Dermott](../Books/Planetary_System_Dynamics.pdf)
and [Tremaine](../Books/Dynamics_of_Planetary_Systems.pdf).
