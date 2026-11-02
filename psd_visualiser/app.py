"""Application shell and the explicit registry of teaching modules."""

import sys
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from html import escape

import matplotlib
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QActionGroup, QColor, QFont, QPalette
from PySide6.QtWidgets import (
    QApplication, QFrame, QLabel, QMainWindow, QPushButton,
    QScrollArea, QStackedWidget, QToolBar, QVBoxLayout, QWidget,
)

DISCLAIMER = (
    "This visualisation tool was created by Michael Kreuziger for the course Part III "
    "Planetary System Dynamics (lecturer: Mark Wyatt) at the University of Cambridge. "
    "Please feel free to add your own modules to your local installation. "
    "If you find any issues or have any questions, please feel free to contact me "
    "“mk2205@cam.ac.uk”. Codex 6.1 Sol was used to create the initial code, which was "
    "then checked and tested."
)


@dataclass(frozen=True)
class ModuleSpec:
    key: str
    title: str
    description: str
    factory: Callable[[], QWidget]


def _orbital_page():
    from .pages.orbital import OrbitalPage
    return OrbitalPage()


def _guiding_page():
    from .pages.guiding import GuidingPage
    return GuidingPage()


def _inclinations_page():
    from .pages.inclinations import InclinationsPage
    return InclinationsPage()


# Add a ModuleSpec here to expose a new module on Home and the toolbar.
MODULES = (
    ModuleSpec("orbital", "Orbital elements", "Explore the six elements that describe an orbit in three dimensions.", _orbital_page),
    ModuleSpec("guiding", "Guiding centre", "Compare an elliptical orbit with its circular guiding centre and epicycle.", _guiding_page),
    ModuleSpec("inclinations", "Averaging sin I", "Sample random orbital orientations and connect geometry to probability.", _inclinations_page),
)


STYLE = """
QMainWindow, QWidget { background: white; color: black; border-radius: 0; }
QLabel { background: transparent; }
QLabel#sectionTitle { color: black; font-size: 14px; font-weight: 600; }
QLabel#note { color: #444444; font-size: 12px; }
QToolBar { border: none; border-bottom: 1px solid #b0b0b0; padding: 4px 8px; spacing: 4px; }
QToolButton { padding: 6px 12px; border: 1px solid transparent; color: black; background: white; }
QToolButton:hover { background: #eeeeee; }
QToolButton:checked { border-color: #808080; background: #eeeeee; }
QToolButton:focus { border: 1px dotted black; }
QPushButton { background: white; color: black; border: 1px solid #999999; padding: 6px 10px; }
QPushButton:hover { border-color: black; background: #eeeeee; }
QPushButton:pressed { background: #dddddd; }
QPushButton:focus { border: 1px dotted black; }
QPushButton#moduleLink { text-align: left; background: white; border: 1px solid transparent; padding: 4px 0; }
QPushButton#moduleLink:hover { color: black; background: #eeeeee; }
QPushButton#moduleLink:focus { border: 1px dotted black; }
QDoubleSpinBox, QComboBox { background: white; color: black; border: 1px solid #999999; padding: 4px; }
QDoubleSpinBox:focus, QComboBox:focus { border-color: black; }
QComboBox QAbstractItemView { background: white; color: black; selection-background-color: black; selection-color: white; }
QSlider::groove:horizontal { height: 3px; background: #bbbbbb; }
QSlider::sub-page:horizontal { background: black; }
QSlider::handle:horizontal { background: black; border: 1px solid black; width: 11px; margin: -5px 0; }
QSlider:focus { border: 1px dotted #777777; }
QScrollArea { border: none; background: transparent; }
QCheckBox { spacing: 6px; }
QToolTip { color: black; background: white; border: 1px solid #999999; }
"""


def interface_palette():
    """Use monochrome native controls without changing plot colours."""
    palette = QPalette()
    for role, colour in (
        (QPalette.ColorRole.Window, "white"),
        (QPalette.ColorRole.WindowText, "black"),
        (QPalette.ColorRole.Base, "white"),
        (QPalette.ColorRole.AlternateBase, "#eeeeee"),
        (QPalette.ColorRole.Text, "black"),
        (QPalette.ColorRole.Button, "white"),
        (QPalette.ColorRole.ButtonText, "black"),
        (QPalette.ColorRole.Light, "white"),
        (QPalette.ColorRole.Midlight, "#eeeeee"),
        (QPalette.ColorRole.Mid, "#999999"),
        (QPalette.ColorRole.Dark, "#666666"),
        (QPalette.ColorRole.Shadow, "black"),
        (QPalette.ColorRole.Highlight, "black"),
        (QPalette.ColorRole.HighlightedText, "white"),
        (QPalette.ColorRole.Link, "black"),
        (QPalette.ColorRole.LinkVisited, "black"),
        (QPalette.ColorRole.ToolTipBase, "white"),
        (QPalette.ColorRole.ToolTipText, "black"),
    ):
        palette.setColor(role, QColor(colour))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor("#777777"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor("#777777"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor("#777777"))
    return palette


class HomePage(QScrollArea):
    def __init__(self, navigate, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        self.setWidget(content)
        outer = QVBoxLayout(content)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(14)
        title = QLabel("About")
        title.setObjectName("sectionTitle")
        outer.addWidget(title)
        html = escape(DISCLAIMER).replace(
            "mk2205@cam.ac.uk",
            '<a style="color: black;" href="mailto:mk2205@cam.ac.uk">mk2205@cam.ac.uk</a>',
        )
        self.disclaimer_label = QLabel(html)
        self.disclaimer_label.setWordWrap(True)
        self.disclaimer_label.setOpenExternalLinks(True)
        self.disclaimer_label.setTextFormat(Qt.TextFormat.RichText)
        self.disclaimer_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        outer.addWidget(self.disclaimer_label)
        outer.addSpacing(12)
        modules_title = QLabel("Available modules")
        modules_title.setObjectName("sectionTitle")
        outer.addWidget(modules_title)
        self.module_buttons = []
        for module in MODULES:
            button = QPushButton(module.title)
            button.setObjectName("moduleLink")
            button.setCursor(Qt.CursorShape.ArrowCursor)
            button.setAutoDefault(True)
            font = button.font()
            font.setUnderline(True)
            button.setFont(font)
            button.clicked.connect(partial(navigate, module.key))
            outer.addWidget(button, 0, Qt.AlignmentFlag.AlignLeft)
            self.module_buttons.append(button)
        outer.addStretch(1)

    def on_enter(self):
        pass

    def on_leave(self):
        pass


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Planetary System Dynamics")
        self.resize(1280, 860)
        self.setMinimumSize(1024, 720)
        self.setPalette(interface_palette())
        self.setStyleSheet(STYLE)
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        toolbar = QToolBar("Visualisations", self)
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.addToolBar(toolbar)
        self.actions = {}
        group = QActionGroup(self)
        group.setExclusive(True)
        for key, name in [("home", "Home"), *((m.key, m.title) for m in MODULES)]:
            action = QAction(name, self)
            action.setCheckable(True)
            action.triggered.connect(partial(self.show_page, key))
            group.addAction(action)
            toolbar.addAction(action)
            self.actions[key] = action
        self.pages = {"home": HomePage(self.show_page)}
        self.stack.addWidget(self.pages["home"])
        self.current_key = "home"
        self.actions["home"].setChecked(True)

    def show_page(self, key, *_):
        if key not in self.pages:
            spec = next(module for module in MODULES if module.key == key)
            self.pages[key] = spec.factory()
            self.stack.addWidget(self.pages[key])
        self.pages[self.current_key].on_leave()
        self.stack.setCurrentWidget(self.pages[key])
        self.current_key = key
        self.actions[key].setChecked(True)
        self.pages[key].on_enter()

    def closeEvent(self, event):
        for page in self.pages.values():
            page.on_leave()
        super().closeEvent(event)


def main():
    matplotlib.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 10,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.labelcolor": "#64748b", "xtick.color": "#64748b", "ytick.color": "#64748b",
        "text.color": "#23364a", "axes.titleweight": "medium",
    })
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setPalette(interface_palette())
    app.setApplicationName("Planetary System Dynamics")
    app.setOrganizationName("PSD Teaching")
    app.setFont(QFont("DejaVu Sans", 10))
    window = MainWindow()
    window.show()
    return app.exec()
