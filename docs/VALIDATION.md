# Validation record

Validated on 2 November 2026 in the workspace's configured Linux/PyCharm environment:

- Python 3.11.15
- NumPy 2.4.6
- Matplotlib 3.11.0
- PySide6 6.11.1

## Automated checks

```bash
python -m unittest discover -s tests -v
```

**45 tests passed:** 21 numerical tests, 9 general Qt integration tests, 8 camera interaction tests, 3 Home-hover tests, and 4 orbital-display tests. No additional test-runner package is needed. GUI tests use Qt's offscreen platform by default, with the application's font and widgets.

The numerical tests check orbital rotation order, handedness, plane membership, periapsis/apoapsis distances, ascending crossings for prograde and retrograde orbits, circular/coplanar limits, and invalid inputs. Guiding-centre checks cover Kepler-equation residuals (including high eccentricity and multiple revolutions), periodicity, forward/inverse reference-frame transforms, exact relative coordinates, the retrograde epicycle, signed anomaly differences, and second-order positional errors. Seeded orientation statistics use 100,000 directions to verify unit norms, isotropy, the averaging factor, and normalised inclination-bin probabilities.

GUI tests cover Home's exact disclaimer and email link, module-list/toolbar navigation, lazy page creation, editable sliders, reset, camera preservation, actual timer advancement, pausing on navigation, frame changes, optional eccentric-anomaly construction, fresh ten-vector samples, histogram totals, and selected-vector planes at polar/equatorial limits. A minimum-size regression check ensures controls have no horizontal overflow at 1024 × 720.

Camera tests send Matplotlib mouse events through the canvas callbacks. They cover horizontal/vertical/diagonal drags, equivalent drags from different starting positions, zero roll, elevation limits, release outside the plot, leaving the figure, ignored outside presses and other buttons, bounded origin-centred wheel zoom, and camera/zoom preservation through redraws and navigation. These controls apply only to the orbital-elements page.

Node checks verify both crossing senses through 90° and retrograde inclinations, including e = 0.99. Display tests compare node markers and label anchors against the actual crossings, check label reprojection when the camera turns, verify the motion arrow follows the angular momentum and crosses upwards, and suppress undefined nodes at I = 0° and 180°. High-eccentricity curve tests check exact ellipse membership, closure, periapsis/apoapsis distances, and quadratic chord-error convergence with uniform eccentric-anomaly sampling. Slider and typed input both reach 0.99.

Home interaction tests check the normal arrow cursor, text-sized module links at both supported window widths, rendered hover shading confined to the link, and activation by mouse and focused Enter.

`git diff --check` also passed.

## Rendering and interaction checks

All four pages were rendered in a graphical desktop session at 1280 × 860 and 1024 × 720. Screenshots were visually inspected for diagram readability, angle labels, and resize behaviour. Additional guiding-centre checks covered 64 combinations of eccentricity, phase, and reference frame, including e = 0, e = 0.5, M = 0°, and M = 360°.

After simplifying the interface, all eight page/size combinations were rendered again using the monochrome Fusion controls. The Home page, square controls, black sliders, preserved plot colours, and minimum-width layouts were inspected. A Qt-level mouse press/move/release check changed both azimuth and elevation in the orbital view while keeping roll at zero.

The updated node markers, leader labels, and orange motion arrow were also inspected on prograde and retrograde orbits, at e = 0.99, and with a crossing at apoapsis. Further 1024 × 720 renders confirmed the node display and Home module list remain usable without horizontal control overflow.

The animation uses elapsed wall time and a 33 ms Qt timer. A short desktop check recorded 69 timer callbacks in approximately 2.2 seconds; performance depends on the computer and window size.

## Limits of validation

Runtime checks were performed on Linux. Windows and macOS source-install instructions are provided, but those platforms were not available for execution. The first-order epicycle is deliberately compared with the exact result through e = 0.5 so its limitations are visible. Ten-vector random samples are illustrative and are not expected to match the analytic distribution on each draw.
