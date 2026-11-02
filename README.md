# Planetary System Dynamics

This is a Python tool for the Part III course on "Planetary System Dynamics" at the University of Cambridge.

Available visualisations (will be expanded throughout the course):
- **Orbital elements:** explore the effects of the six orbital elements on a 3D orbit
- **Guiding centre:** explore how the guiding-centre approximation works and compares to the exact solution.
- **Averaging sin I:** see where uniformly drawn orbit orientations, i.e., angular-momentum directions fall on a sphere
## Run from source

Requires Python 3.11+ and a graphical desktop.

1. Install [Python](https://www.python.org/downloads/) if needed. 
2. Download the source from [GitHub](https://github.com/michael-kreuziger/PSD-Visualiser) (**Code → Download ZIP**) and extract the whole ZIP file.
3. Open Terminal (Linux/macOS) or PowerShell (Windows). Replace the example path below with the extracted folder containing `main.py` and `requirements.txt`. Check that the version command reports Python 3.11 or later, then run the remaining commands.

**Linux or macOS:**

```bash
cd "/path/to/PSD-Visualiser"
python3 --version
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py
```

**Windows PowerShell:**

```powershell
cd "C:\path\to\PSD-Visualiser"
py -3 --version
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

On later runs, open a terminal in the same folder and run only the final command for your platform. The `.venv` folder contains the installed dependencies; no environment activation is needed.

In PyCharm or VScode, select `.venv` as the project interpreter and run `main.py`.

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
```
## Add a teaching module

1. Add calculations under `psd_visualiser/models/` and numerical tests under `tests/`.
2. Add a `QWidget` page under `psd_visualiser/pages/`; shared controls are in `widgets.py`.
3. Implement `on_enter()` and `on_leave()`. Stop timers in `on_leave()`; static pages can use empty methods.
4. Register a factory returning the page with `ModuleSpec(key, title, description, factory)` in `app.py`’s `MODULES`. This adds it to Home and the toolbar.

## References

- Carl D. Murray and Stanley F. Dermott (1999). *Solar System Dynamics*. Cambridge University Press. [DOI: 10.1017/CBO9781139174817](https://doi.org/10.1017/CBO9781139174817).
- Scott Tremaine (2023). *Dynamics of Planetary Systems*. Princeton University Press. ISBN 9780691207117. [Publisher](https://press.princeton.edu/books/paperback/9780691207117/dynamics-of-planetary-systems).
