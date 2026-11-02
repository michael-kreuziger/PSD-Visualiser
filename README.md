# Planetary System Dynamics

A Python desktop teaching tool for Part III Planetary System Dynamics at the University of Cambridge. The Home page contains an About section and a list of modules. Use the list or the top toolbar to open a visualisation:

- **Orbital elements:** rotate a 3D orbit and change its six elements with sliders or typed values, including eccentricity up to 0.99. The reference plane, both node crossings, periapsis, angular-momentum vector, and angle arcs show how the elements define the orbit. Labels follow the actual ascending and descending nodes; an orange arrow shows motion through the ascending node, including on retrograde orbits. Nodes are undefined at inclinations 0° and 180°. **Fit view** adjusts the framing; **Reset** restores the starting configuration.
- **Guiding centre:** compare exact Kepler motion with the first-order guiding-centre approximation. Change eccentricity, scrub mean anomaly, or start the animation. Switch to the frame rotating with G, and optionally show the exact eccentric-anomaly construction. The smaller panel keeps the relative epicycle visible.
- **Averaging sin I:** draw ten independent angular-momentum directions uniformly on a sphere. **Randomize** replaces the sample. Select a vector to see its orbit plane and inclination, then compare the sample histogram and mean sin I with their isotropic expectations.

In the orbital-elements diagram, left-drag horizontally to turn the view and vertically to tilt it. The camera stays upright; scroll to zoom about the focus. In the inclination diagram, drag to rotate and right-drag to zoom. Page changes retain controls and camera settings. Leaving the guiding-centre page pauses its animation. The controls use a plain black-and-white interface; the diagrams retain their explanatory colours.

On Home, module names keep the normal arrow cursor and show a subtle grey highlight on hover. Click a name, or focus it with Tab and press Enter, to open that module.

## Run from source

Use **Python 3.11 or later** with NumPy ≥1.26, Matplotlib ≥3.8, and PySide6 ≥6.6. The dependency files include upper major-version bounds. No web server, online service, or GPU-specific package is required. A graphical desktop session is required for normal use.

The configured PyCharm environment in this workspace already contains the required packages: open `main.py` and run it with the configured interpreter. No installation is needed there.

For another computer, open a terminal in the project directory and create an isolated environment.

**Linux or macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

**Windows PowerShell:**

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Using the environment’s Python directly avoids requiring PowerShell activation. In PyCharm, select `.venv` as the project interpreter and run `main.py`.

From the project directory, the module entry point also works:

```bash
python -m psd_visualiser
```

Optionally install the project in editable mode to make the launcher available from other directories. Use the environment’s Python for this command:

```bash
python -m pip install -e .
psd-visualiser
```

On Windows without activation, use `.\.venv\Scripts\python.exe -m pip install -e .` and then `.\.venv\Scripts\psd-visualiser.exe`.

## Source layout

```text
main.py                    Simple source launcher
psd_visualiser/
    app.py                 Home page, window, navigation, module registry
    widgets.py             Shared plotting canvas, sliders, and styling
    camera.py              Turn-and-tilt mouse controls for the orbital view
    models/                GUI-independent numerical calculations
    pages/                 Orbital, guiding-centre, and inclination interfaces
tests/                     Numerical tests and GUI smoke tests
docs/
    SCIENCE.md             Equations, conventions, and textbook references
    VALIDATION.md          Checks performed and their limits
Books/                     Supplied reference PDFs; not runtime dependencies
```

The scientific calculations use radians internally; interface controls display degrees. Lengths use relative units. The guiding-centre page fixes a = 1 and uses an illustrative 12-second animation period. These are teaching constructions rather than a real-system orbit integrator.

## Tests

With the dependencies installed, run:

```bash
python -m unittest discover -s tests -v
```

The test suite uses Python’s standard-library `unittest`; no separate test runner is required. GUI smoke tests default to Qt’s offscreen platform so they can run without a desktop display. For a visual check, launch the app normally and inspect all pages and the rotating-frame animation. See [the validation record](docs/VALIDATION.md).

## Add a teaching module

1. Put numerical calculations in a new module under `psd_visualiser/models/`, with tests independent of the GUI.
2. Create a `QWidget` page under `psd_visualiser/pages/`. Reuse `PlotPanel`, `SliderControl`, `note`, and `section_title` from `widgets.py` for consistent presentation.
3. Implement `on_enter()` and `on_leave()` on the page. Stop timers or background work in `on_leave()`; preserve page state when the user navigates away. A static page can use empty methods.
4. Add a factory and a `ModuleSpec(key, title, description, factory)` to `MODULES` in `psd_visualiser/app.py`. Use a unique key and a factory returning a new page instance. The registry supplies the Home module list and toolbar entry; pages are created on first use and retained thereafter. The description is available as module metadata and is not displayed on Home.

The course disclaimer invites changes to the source and additional modules. Questions or issues can be sent to [Michael Kreuziger](mailto:mk2205@cam.ac.uk).

## Scientific basis

The supplied PDFs are Murray & Dermott’s *Solar System Dynamics* and Scott Tremaine’s *Dynamics of Planetary Systems*. The Murray & Dermott file is named `Planetary_System_Dynamics.pdf` in this workspace. Relevant chapters, page numbers, formulas, and limiting cases are listed in [SCIENCE.md](docs/SCIENCE.md).
