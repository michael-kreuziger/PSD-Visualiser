# Scientific conventions and references

The visualisations describe unperturbed, bound Kepler orbits and isotropic orientation statistics. Angles are in radians in the models and degrees in the controls. Rotations are right-handed and act on column vectors. Lengths are relative units; the orbital-elements page varies a, while the guiding-centre page fixes a = 1.

## Orbital elements

The reference plane is z = 0, with reference direction +x and reference normal +z. For semi-major axis a, eccentricity e, inclination I, node longitude Ω, argument of periapsis ω, and true anomaly f:

\[
r=\frac{a(1-e^2)}{1+e\cos f},\qquad
\mathbf r=R_z(\Omega)R_x(I)R_z(\omega)
\begin{pmatrix}r\cos f\\r\sin f\\0\end{pmatrix}.
\]

Ω is measured from +x to the ascending node in the reference plane. ω is measured from that node to periapsis in the orbital plane; f is measured from periapsis to the particle in the orbital plane. The unit angular-momentum direction is

\[
\hat{\mathbf h}=(\sin I\sin\Omega,-\sin I\cos\Omega,\cos I).
\]

Thus the directed orbital inclination I equals the angle between h and +z, with 0 ≤ I ≤ π. Values above 90° describe retrograde motion. The angle of h to the reference plane itself is a different, complementary angle.

The ascending node is at f = −ω, and the descending node is at f = π − ω. Since z = r sin I sin(ω + f) and true anomaly advances in the direction of motion, the ascending crossing has ż > 0 for every 0 < I < π. It therefore remains ascending when I passes through 90°. Both crossings are marked and labelled at their actual positions; an orange tangent arrow shows the direction of motion through the ascending crossing. Neither crossing is labelled as a node at I = 0 or π.

The orbital-elements slider extends to e = 0.99. To keep the drawn ellipse smooth near that limit, curve vertices sample eccentric anomaly E uniformly using (a(cos E − e), a√(1 − e²)sin E, 0) before rotating into reference coordinates. The particle and f control still use true anomaly. The guiding-centre comparison retains e ≤ 0.5.

Periapsis and apoapsis distances are a(1 − e) and a(1 + e). At e = 0, periapsis and the split between ω and f are conventional. At I = 0 or π, there is no unique ascending node; Ω and its associated angle construction retain a coordinate convention. The interface explains these limits without using singular inverse formulas.

## Guiding centre

With the focus F at the origin and periapsis along +x, advance mean anomaly uniformly, M = nt, and solve Kepler’s equation:

\[
M=E-e\sin E,\qquad
P=(a(\cos E-e),\;a\sqrt{1-e^2}\sin E),\qquad
G=a(\cos M,\sin M).
\]

G moves on a circle at constant mean motion. True anomaly is the polar angle of P about F. The equation of centre δ is the short signed angle from FG to FP:

\[
\delta=\operatorname{atan2}(\sin(f-M),\cos(f-M)).
\]

M and f are positive full-cycle angles; δ can be negative. In particular, δ changes sign between the two halves of the orbit.

The frame attached to G uses an outward radial x-axis and prograde tangential y-axis. Every object X in the main construction, including curves, reference rays, and angle arcs, transforms by

\[
X'=R(-M)(X-G).
\]

Consequently G′ = (0, 0), F′ = (−a, 0), and the inertially fixed ellipse and periapsis direction rotate in this view. Exact relative particle coordinates are

\[
x=r\cos(f-M)-a,\qquad y=r\sin(f-M).
\]

To first order in small e:

\[
x\simeq-ae\cos M,\qquad y\simeq2ae\sin M.
\]

This gives a retrograde 2:1 epicycle: radial semiaxis ae, tangential semiaxis 2ae, and period equal to the orbital period. The dashed construction and orange particle show this approximation; the blue geometry remains exact. Positional differences are O(e²) for small e. The slider extends to e = 0.5 to make the discrepancy apparent, rather than implying accuracy at that eccentricity. At e = 0 the epicycle collapses and P = G.

The optional eccentric-anomaly construction uses ellipse centre C = (−ae, 0) and auxiliary-circle point Q = C + a(cos E, sin E). E is measured at C to Q, with Q projected onto the ellipse to locate P. The angle from C directly to P is not the exact eccentric anomaly.

## Isotropic orientations and averaging sin I

The displayed h vectors have unit length; only their directions are sampled. Draw z uniformly on [−1, 1] and φ uniformly on [0, 2π), independently:

\[
\hat{\mathbf h}=(\sqrt{1-z^2}\cos\phi,\sqrt{1-z^2}\sin\phi,z),
\qquad I=\arccos z.
\]

Uniform sphere area gives

\[
p(I)=\tfrac12\sin I\quad(0\le I\le\pi),\qquad
\langle\sin I\rangle=\tfrac12\int_0^\pi\sin^2 I\,dI=\frac\pi4.
\]

This density is per radian. Uniform directions favour inclinations near 90°, where equal-width latitude bands have more area. Sampling I uniformly would give a different orientation distribution.

The histogram uses 15° bins and counts rather than a density overlay. The expected count for a bin [I₁, I₂] is

\[
10\int_{I_1}^{I_2}p(I)\,dI=5(\cos I_1-\cos I_2),
\]

with bin edges converted to radians. Each click replaces all ten vectors. The sample mean sin I and histogram fluctuate; neither is an accumulated estimate. Selecting a vector displays the orbit plane perpendicular to it, linking the normal-vector angle to the orbital-plane inclination.

## Textbook references

PDF page numbers below are one-based document pages, including front matter; printed page numbers are those on the textbook pages.

| Topic | Textbook location | Printed pages | PDF pages |
| --- | --- | --- | --- |
| Orbital elements and rotation | Tremaine, *Dynamics of Planetary Systems* (2023), §1.3.2, especially Fig. 1.2 and Eq. 1.70 | 17–20; figure on 18 | 32–35; figure on 33 |
| Orbital elements | Murray & Dermott, *Solar System Dynamics* (1999), §2.8, Figs. 2.13–2.14 | 48–51 | 63–66 |
| Guiding-centre approximation | Murray & Dermott, §2.6, Eqs. 2.96–2.99 and Figs. 2.8–2.10 | 42–45 | 57–60 |
| Epicyclic motion | Tremaine, §1.8.2 | 53–57 | 68–72 |

Local source PDFs: [Murray & Dermott](../Books/Planetary_System_Dynamics.pdf) and [Tremaine](../Books/Dynamics_of_Planetary_Systems.pdf). The sphere-sampling and averaging formulas above follow directly from the isotropic area element; the orbital-angle convention is shared with the orbital-elements chapters.
