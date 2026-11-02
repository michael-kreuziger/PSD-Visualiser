"""Three-dimensional geometry of the six orbital elements."""

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QScrollArea, QVBoxLayout, QWidget
from matplotlib.text import Annotation
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from mpl_toolkits.mplot3d import proj3d

from ..camera import OrbitCamera
from ..models.orbits import orbital_curve, orbital_position, orbital_rotation
from ..widgets import (
    BLUE, GREEN, MUTED, ORANGE, PURPLE, TEXT, PlotPanel, SliderControl,
    note, section_title, style_3d,
)


class NodeLabel(Annotation):
    """Keep a screen-offset label attached to a crossing as the camera turns."""

    def __init__(self, text, position, offset):
        self.position_3d = np.asarray(position)
        super().__init__(
            text, xy=(0, 0), xytext=offset, textcoords="offset points",
            ha="left" if offset[0] > 0 else "right", va="center",
            color=MUTED, fontsize=9, annotation_clip=False,
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.85, "pad": 1},
            arrowprops={"arrowstyle": "-", "color": MUTED, "linewidth": 0.8},
        )

    def draw(self, renderer):
        x, y, _ = proj3d.proj_transform(*self.position_3d, self.axes.get_proj())
        self.xy = (x, y)
        super().draw(renderer)


class OrbitalPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(18)
        controls = QWidget()
        side = QVBoxLayout(controls)
        side.setContentsMargins(2, 0, 12, 8)
        side.setSpacing(13)
        side.addWidget(section_title("The six orbital elements"))
        side.addWidget(note("Change the shape, orientation, and position. Left-drag horizontally to turn, vertically to tilt. Scroll to zoom."))
        specs = [
            ("a", "a · semi-major axis", 0.5, 3, 1, 0.01, 2, ""),
            ("e", "e · eccentricity", 0, 0.99, 0.3, 0.01, 2, ""),
            ("I", "I · inclination", 0, 180, 30, 1, 0, "°"),
            ("Omega", "Ω · longitude of node", 0, 360, 40, 1, 0, "°"),
            ("omega", "ω · argument of periapsis", 0, 360, 60, 1, 0, "°"),
            ("f", "f · true anomaly", 0, 360, 45, 1, 0, "°"),
        ]
        self.sliders = {}
        for key, title, lo, hi, default, step, decimals, suffix in specs:
            control = SliderControl(title, lo, hi, default, step, decimals, suffix)
            self.sliders[key] = control
            side.addWidget(control)
            control.valueChanged.connect(self.render)
        row = QHBoxLayout()
        self.fit_button, self.reset_button = QPushButton("Fit view"), QPushButton("Reset")
        self.fit_button.clicked.connect(self.fit_view)
        self.reset_button.clicked.connect(self.reset)
        row.addWidget(self.fit_button)
        row.addWidget(self.reset_button)
        side.addLayout(row)
        self.status, self.degeneracy = note(""), note("")
        side.addWidget(self.status)
        side.addWidget(self.degeneracy)
        side.addWidget(note("Ω: reference direction → ascending node, in the reference plane.\nω: ascending node → periapsis, in the orbital plane.\nf: periapsis → particle, in the orbital plane.\nI: +z → h; I > 90° denotes retrograde motion.\nAscending: below → above z = 0.\nDescending: above → below z = 0."))
        side.addStretch()
        side.addWidget(note("Relative length units.\nTremaine §1.3.2, Fig. 1.2; Murray & Dermott §2.8."))
        scroll = QScrollArea()
        scroll.setWidget(controls)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setMinimumWidth(285)
        scroll.setMaximumWidth(320)
        layout.addWidget(scroll)
        self.plot = PlotPanel(projection="3d")
        layout.addWidget(self.plot, 1)
        self.extent, self._drawn = 1.6, False
        self.plot.axes.view_init(elev=26, azim=-110, roll=0)
        self.camera = OrbitCamera(self.plot.axes)
        self.render()

    def values(self):
        values = {key: slider.value() for key, slider in self.sliders.items()}
        return values["a"], values["e"], *np.deg2rad([values[k] for k in ("I", "Omega", "omega", "f")])

    def _line(self, points, **kwargs):
        self.plot.axes.plot(*np.asarray(points).T, **kwargs)

    def _label(self, position, text, color=TEXT):
        self.plot.axes.text(*position, text, color=color, fontsize=10,
                            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.72, "pad": 1})

    def _arc(self, u, v, start, sweep, radius, label, color):
        if abs(sweep) < 1e-8:
            return
        angles = np.linspace(start, start+sweep, max(24, int(abs(sweep)*30)))
        points = radius*(np.cos(angles)[:, None]*u + np.sin(angles)[:, None]*v)
        self._line(points, color=color, linewidth=2)
        tangent = points[-1]-points[-3]
        tangent /= np.linalg.norm(tangent)
        self.plot.axes.quiver(*points[-1], *tangent, length=0.075*radius,
                              color=color, arrow_length_ratio=0.9, linewidth=1.5)
        mid = start+0.5*sweep
        self._label(radius*1.13*(np.cos(mid)*u+np.sin(mid)*v), label, color)

    def render(self, *_):
        a, e, inc, node, peri, anomaly = self.values()
        ax = self.plot.axes
        camera = (float(np.clip(ax.elev, -89, 89)), ax.azim, 0)
        old_limits = (ax.get_xlim(), ax.get_ylim(), ax.get_zlim())
        required = 1.12*max(1.35*a, a*(1+e))
        expand = required > self.extent
        self.extent = max(self.extent, required)
        ax.clear()
        self.camera.disable_native_controls()
        style_3d(ax, self.extent)
        if self._drawn and not expand:
            ax.set_xlim(*old_limits[0])
            ax.set_ylim(*old_limits[1])
            ax.set_zlim(*old_limits[2])
        ax.view_init(*camera)
        size = min(1.3*a, self.extent*0.83)
        plane = [[-size,-size,0], [size,-size,0], [size,size,0], [-size,size,0]]
        ax.add_collection3d(Poly3DCollection([plane], facecolor=BLUE, alpha=0.045,
                                           edgecolor=MUTED, linewidth=0.5))
        rotation = orbital_rotation(inc, node, peri)
        p, q, h = rotation[:,0], rotation[:,1], rotation[:,2]
        n = np.array([np.cos(node), np.sin(node), 0])
        s = np.array([-np.sin(node)*np.cos(inc), np.cos(node)*np.cos(inc), np.sin(inc)])
        z = np.array([0.,0.,1.])
        x, y = np.array([1.,0.,0.]), np.array([0.,1.,0.])
        body = orbital_position(a,e,inc,node,peri,anomaly)
        curve = orbital_curve(a,e,inc,node,peri)
        self._line(curve, color=BLUE, linewidth=2.5, label="Orbit")
        ascending_radius = a*(1-e*e)/(1+e*np.cos(peri))
        descending_radius = a*(1-e*e)/(1-e*np.cos(peri))
        self._line([-max(1.3*a,1.05*descending_radius)*n,
                    max(1.3*a,1.05*ascending_radius)*n],
                   color=MUTED, linestyle="--", linewidth=1)
        for vector,color,label in [(1.32*a*x,MUTED,"+x · reference"),
                                   (1.28*a*z,GREEN,"+z"), (1.28*a*h,GREEN,"h")]:
            ax.quiver(0,0,0,*vector,color=color,arrow_length_ratio=0.07,linewidth=1.5)
            self._label(vector*1.03,label,color)
        self._line([np.zeros(3),body],color=ORANGE,linewidth=1.2)
        self._line([np.zeros(3),a*(1-e)*p],color=PURPLE,linestyle=":",linewidth=1.3)
        ax.scatter(0,0,0,s=105,color=ORANGE,edgecolor="white",zorder=5)
        ax.scatter(*body,s=65,color=BLUE,edgecolor="white",zorder=6)
        ax.scatter(*(a*(1-e)*p),s=30,color=PURPLE)
        self.node_markers, self.node_labels = {}, {}
        self.motion_arrow, self.motion_segment = None, None
        if 1e-8 < inc < np.pi-1e-8:
            positions = {"ascending": ascending_radius*n, "descending": -descending_radius*n}
            for key, title, offset in (("ascending", "Ascending node", (22, 38)),
                                       ("descending", "Descending node", (-22, -24))):
                point = positions[key]
                marker, = ax.plot(*point, marker="o", markersize=4,
                                  linestyle="none", color=MUTED, zorder=8)
                self.node_markers[key] = marker
                label = NodeLabel(title, point, offset)
                ax.add_artist(label)
                self.node_labels[key] = label
            # Kepler velocity is proportional to (-sin f, e + cos f) in
            # periapsis coordinates. Its direction crosses this node upwards
            # for every 0 < I < pi, including retrograde inclinations.
            f_node = -peri
            direction = -np.sin(f_node)*p+(e+np.cos(f_node))*q
            direction /= np.linalg.norm(direction)
            tail = positions["ascending"]-0.09*a*direction
            tip = positions["ascending"]+0.09*a*direction
            self.motion_segment = np.stack((tail, tip))
            self.motion_arrow = ax.quiver(*tail, *direction, length=0.18*a,
                                          color=ORANGE, linewidth=2.2,
                                          arrow_length_ratio=0.3, zorder=9)
        self._label(body+0.06*a*z,"P",BLUE)
        self._label(a*(1-e)*p+0.06*a*z,"Periapsis" if e > 0 else "Periapsis convention",PURPLE)
        centre = -a*e*p
        self._line([centre,a*(1-e)*p],color=PURPLE,linewidth=1,alpha=0.6)
        self._label(centre+0.5*a*p-0.08*a*q,"a",PURPLE)
        self._arc(x,y,0,node,0.42*a,"Ω",ORANGE)
        self._arc(n,s,0,peri,0.62*a,"ω",PURPLE)
        self._arc(p,q,0,anomaly,0.83*a,"f",BLUE)
        self._arc(z,np.array([np.sin(node),-np.cos(node),0]),0,inc,0.98*a,"I",GREEN)
        ax.set_title("Orbital elements",loc="left",fontsize=15,color=TEXT,pad=12)
        ax.text2D(0.01,0.01,"Focus at origin  ·  shaded reference plane z = 0",
                  transform=ax.transAxes,color=MUTED,fontsize=9)
        self.status.setText(f"Periapsis distance: {a*(1-e):.2f}\nApoapsis distance: {a*(1+e):.2f}")
        notices = []
        if e<1e-10:
            notices.append("Circular orbit: periapsis is arbitrary; ω and f retain a coordinate convention.")
        if inc<1e-10 or abs(inc-np.pi)<1e-10:
            notices.append("Coplanar orbit: the ascending node is undefined; Ω retains a coordinate convention.")
        self.degeneracy.setText("\n".join(notices))
        self.degeneracy.setVisible(bool(notices))
        self._drawn = True
        self.plot.canvas.draw_idle()

    def fit_view(self):
        self.camera.cancel_drag()
        a,e,*_ = self.values()
        self.extent = 1.12*max(1.35*a,a*(1+e))
        self._drawn = False
        self.render()

    def reset(self):
        self.camera.cancel_drag()
        for control in self.sliders.values():
            control.blockSignals(True)
            control.set_value(control.default)
            control.blockSignals(False)
        self.plot.axes.view_init(elev=26,azim=-110,roll=0)
        self.extent,self._drawn = 1.6,False
        self.render()

    def on_enter(self):
        pass

    def on_leave(self):
        self.camera.cancel_drag()
