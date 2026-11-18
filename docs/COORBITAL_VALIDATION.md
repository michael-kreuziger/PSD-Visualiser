# Co-orbital module validation

Checked on 17 November 2026 using the project's configured Python 3.11.15,
NumPy, Matplotlib, and PySide6 environment. Existing teaching pages and their
tests are unchanged; the application registry adds one lazily loaded page.
No dependencies were added.

The current interface limits are `-5 <= log10(mu) <= -3`
(`1e-5 <= mu <= 1e-3`) and initial outward radial speed from 0 to
0.01 in units of `n*a`. The GUI epicyclic preset uses μ = 0.001,
starting longitude 60°, radial speed 0.01, and three reference times.
The smoke check completed as an L4 tadpole, with star-relative radii
0.98877–1.01127 and Jacobi variation about 1.7 × 10⁻¹².
The general numerical model retains broader parameter support; numerical
benchmarks outside these bounds are identified below and are not current
GUI settings.

## Scientific review

The relevant chapters of both local books were read and cross-checked:
Murray & Dermott, §§3.2–3.10, and Tremaine, §§3.1–3.2.
[COORBITAL_SCIENCE.md](COORBITAL_SCIENCE.md) records equations and exact
printed/PDF page references. An independent review of the model and display
checked Coriolis signs, potential and Jacobi conventions, numerical
integration coefficients, reference-frame transformations, Lagrange-point
positions, speed-contour levels, forbidden shading, and interpretation of
the longitude diagnostic. No unresolved scientific errors were found.

The stability and initial-condition discussion was rechecked against both
books for the broader numerical-model tests. Murray & Dermott,
printed pp. 94 and 97–102, distinguish local oscillatory theory from
finite-amplitude motion and discuss nonlinear resonances and transitions
to circulation. Tremaine, printed pp. 149–150 and 161–164, separates the
linear triangular-point criterion from averaged small-mass co-orbital
theory. A launch that works at one mass ratio is not assumed to work at
every other mass ratio. Neither an irregular trace nor the finite-window
family classifier is a chaos diagnostic; no Lyapunov exponent or frequency
diffusion is calculated. The Routh threshold is not used as a universal
horseshoe-stability boundary.

The numerical method is adaptive Dormand–Prince 5(4), solving the full
planar CR3BP rather than its averaged co-orbital approximation. The default
output spacing is at most 0.1 in units with n = 1, resolving inertial paths.
The interface reports the maximum absolute drift in the Jacobi constant.

## Automated checks

```bash
QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -p 'test_coorbital*.py' -v
```

All 35 targeted tests pass: 22 numerical checks and 13 Qt integration checks.

The model checks all five equilibrium-force residuals, the Coriolis and
potential-gradient relation, barycentric primary positions and velocities,
and inertial acceleration against the direct Newtonian gravitational forces.
It also checks the speed-contour identity, L4/L5 launch symmetry, the
small-amplitude libration period against the exact linear CR3BP frequency,
convergence with tighter numerical tolerances, and honest reporting of
encounters and orbit-family changes. Extended checks cover the radial
velocity launch, its signed direction and reflection symmetry, equilibrium
launches below and above the Routh threshold, and finite integration at
large mass ratios. A broader model benchmark with radial speed 0.08 is
checked for a star-relative radial span above 0.18 and repeated fast
angular-velocity reversals; that speed is outside the current GUI range.

Both orbit families at the original bounded-example longitude endpoints were
integrated for three nominal libration timescales at μ = 10⁻⁵, 10⁻⁴, and
10⁻³. All completed with the expected family and Jacobi variation below
2 × 10⁻¹⁰. Additional development checks sampled nine logarithmically spaced
mass ratios and the shortest permitted duration. These checks establish a
useful teaching envelope, not a mathematical boundary of stability. Those
checks used zero radial kick and do not establish bounded motion over the
manually edited initial conditions.

Broader numerical-model tests retain μ values up to 0.1 and signed
radial kicks outside the current GUI bounds. They verify equilibrium
classification and explicit triangular-point instability reporting above
the Routh threshold, alongside nonzero-kick examples and encounter
handling. These tests do not imply that larger mass ratios or kicks are
currently selectable, or that every trajectory above the triangular-point
threshold is unstable.

The checked-example helper integrates candidates at the exact selected μ
for six reference times for tadpoles and ten for horseshoes, longer than
the display's maximum duration of three reference times. Acceptance
requires completion, the requested geometric family, star-relative radius
between 0.65 and 1.35, maximum absolute Jacobi drift below 5 × 10⁻⁹, and
repeated angular crossings demonstrating motion in both directions.
Unsuccessful candidates are not presented as checked family examples.
These criteria are practical numerical checks, not a stability theorem.

Additional broader-model checks used zero-kick tadpole launches at μ = 0.03,
0.035, 0.038, 0.0384, and 0.0385 with starting longitudes 58°, 59°, 59.5°,
59.9°, and 59.99°, respectively. They remained in the L4 tadpole region
over ten reference times; tighter-tolerance reintegrations differed by
at most approximately 2 × 10⁻¹¹ in the checked state coordinates. The
smaller displacements are an initial-condition choice; the force law and
selected μ are unchanged. These mass ratios are outside the current UI
range, and the checks are not demonstrations of nonlinear stability for
all time.

The checked horseshoe catalogue covers the current UI mass-ratio range.
Exploratory higher-mass candidates did not provide a sufficiently reliable
basis for extending that catalogue. This is a limit of the supplied
examples, not a proof that horseshoe trajectories cannot exist at higher
mass ratios. An unavailable example must leave μ unchanged and be labelled
as unavailable; it must not silently substitute a different mass ratio.
The general model's forced-fallback regression verifies that every
candidate is rounded to 0.001° precision **before** integration and that
a candidate rounded to the exact 60° equilibrium is discarded. This
retains precision in broader-model examples near the Routh threshold,
while the current UI only exposes the smaller mass ratios stated above.

The GUI checks independently reconstruct Cartesian rotations, the
mass-weighted barycentre, and equilateral L4/L5 geometry. They verify that
historical inertial positions use their own epochs, while primaries, Lagrange
points, and contour patterns use the current epoch. Frame/time changes
preserve the integrated trajectory. Further checks cover contour levels
C₀ and C₀ + v², the narrow forbidden lobe at μ = 10⁻⁵ and starting longitude
55°, zero-speed contour deduplication, both tadpole centres, mass-dependent
horseshoe controls, animation, pause on navigation, reset, and minimum-window
layout. Display checks cover the current mass-ratio and radial-speed
slider and typed-input bounds, conversion of the duration control to planet
periods, the radial-speed preset, removal of the recent-history trail, and
the fixed inertial legend with distinct Lagrange-point markers. For the
epicyclic preset, the contour tests verify that zero speed and speed 0.005
have no curve, the caption explains the minimum speed 0.01, and speed 0.02
produces the selected contour.
Family-selection checks also cover automatic example loading on mass,
family, and centre changes and restoring a checked example after manually
edited initial conditions while retaining the selected μ. The main plot reports the integrated family instead of
assuming that every launch matches the family selector.

The full suite runs 80 tests and reports 79 passes and one pre-existing failure in
`test_gui.TeachingInterfaceTests.test_home_disclaimer_module_list_and_toolbar_navigation`:
the expected Home disclaimer wording differs from the application's current
wording. This same failure occurred before adding the module. The disclaimer
and the existing test were left unchanged. `git diff --check` also passes.

## Display checks and limits

Offscreen Qt renders were visually inspected at 1280 × 860 and 1024 × 720,
including both orbit families, both frames, and enabled speed contours.
The sidebar scrolls vertically at smaller window sizes. L1–L5 are labelled;
the barycentre is marked separately from the star. The entire integrated
path is shown without an additional recent-history trail. A fixed legend
identifies the distinct Lagrange-point symbols in the inertial view; direct
text labels are retained in the corotating view. At 1× playback, a reference timescale takes 12 seconds in the
corotating view; a planet period takes 6 seconds in the inertial view.
This slower inertial playback makes the orbital direction visible at small μ.

Duration uses a multiplier of the reference time `Tref = 2π/√(27μ/4)`.
In planet periods this is `Tref/Pplanet = √(4/(27μ))`; at μ = 0.001,
two reference times request about 24.34 planet periods. Tref approximates
a stable slow libration period only at small μ and small amplitude. Above
μ ≈ 0.03852 it remains a reference time rather than a physical stable
libration period. It is not a measured complete cycle of an arbitrary
large-amplitude orbit. The family readout describes motion over the finite
integration window; neither it nor conservation of the Jacobi constant
proves long-term stability. Contours show rotating-frame speed even in the
inertial view. The primaries are point masses, and the massless particle is
restricted to their orbital plane. Runtime and rendering were checked on
Linux; other operating systems were not available.
