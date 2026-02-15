# geometry_id7_mobile_holder.py
# ID.7 mobile holder geometry
#
# Usage (FreeCAD):
#   ./freecad_headless.py test geometry_id7_mobile_holder.py
#   ./freecad_headless.py export-stl geometry_id7_mobile_holder.py output.stl
#   ./freecad_headless.py export-3mf geometry_id7_mobile_holder.py output.3mf
#
# Usage (SVG preview, kein FreeCAD noetig):
#   python3 geometry_id7_mobile_holder.py [--corners] [--output FILE]

import os
import math

# Default parameters - can be overridden via environment variables with same name
DEFAULTS = {
    "HOLDER_DEPTH_MM": 40.0,       # Z - Extrusionstiefe
    "Z_FILLET_R_MM": 0.5,         # Rundung an Z-Kanten oben/unten (0 = aus)
    "STEM_LENGTH_MM": 25.0,       # Länge des Zylinder-Stiels
    "STEM_DIAMETER_MM": 10.0,     # Durchmesser des Zylinder-Stiels
    "BALL_DIAMETER_MM": 17.0,     # Durchmesser der Kugel am Ende
    "CUTOUT_DIAMETER_MM": 25.0,   # Durchmesser der Material-Cutouts
    "CUTOUT_CHAMFER_MM": 1.5,     # 45°-Fase an den Cutout-Kanten
}

PARAMS = DEFAULTS.copy()
for key, default_value in DEFAULTS.items():
    env_value = os.environ.get(key)
    if env_value is not None:
        if isinstance(default_value, float):
            PARAMS[key] = float(env_value)
        elif isinstance(default_value, int):
            PARAMS[key] = int(env_value)
        else:
            PARAMS[key] = env_value

# ============================================================
# Kontur als Punktliste: (x, y, radius)
# Jeder Punkt ist eine ideale Ecke, radius > 0 erzeugt einen Fillet-Bogen
# ============================================================
CONTOUR = [
    (  79.7984,  120.5500,  0.50),  # 0
    (  70.4861,  115.7318, 30.00),  # 1
    (  55.1431,  110.6686,  2.00),  # 2
    (  60.1621,   97.6101,  4.64),  # 3
    ( -13.2676,    0.0000, 15.00),  # 4
    (  65.5532,    0.0000,  0.50),  # 5 - auf Linie 4-8
    (  65.5807,   -1.9195,  1.00),  # 6 - 1.9mm Offset nach unten
    (  68.9365,   -1.9195,  1.00),  # 7 - parallel zu 5-8
    (  68.9365,    0.0000,  0.50),  # 8 - auf Linie 4-8
    (  71.2000,    0.0000,  1.00),  # 9
    (  71.2000,    2.5000,  1.00),  # 10
    (  87.0000,    2.5000,  1.00),  # 11
    (  87.0000,    0.0000,  0.10),  # 12
    (  90.0000,    0.0000,  2.00),  # 13
    (  90.0000,    5.0000,  2.00),  # 14
    (  -3.2494,    5.0000, 10.00),  # 15
    (  65.8291,   96.8260,  9.64),  # 16
    (  61.4391,  108.2478,  2.00),  # 17
    (  72.7865,  113.1408, 25.00),  # 18
    (  80.7452,  118.2352,  0.50),  # 19
    (  84.4137,  117.6005,  0.50),  # 20 - auf Linie 19-24
    (  83.9536,  114.9401,  1.00),  # 21 - +0.5mm Richtung 20->21
    (  87.3282,  114.3563,  1.00),  # 22 - +0.5mm Richtung 20->21
    (  87.7883,  117.0167,  0.50),  # 23 - auf Linie 19-24
    (  89.7472,  116.6779,  0.50),  # 24 - +0.5mm Richtung 19->24
    (  89.5504,  115.2708,  0.50),  # 25 - +0.5mm Richtung 19->24, parallel zu 27->26
    (  91.4789,  115.0742,  1.00),  # 26
    (  91.8924,  118.0305,  1.00),  # 27
]


# ============================================================
# Kontur-Segmente mit Fillet-Boegen berechnen
# ============================================================
def build_contour_segments(contour):
    """Erzeuge Linien- und Bogensegmente aus Kontur mit Fillet-Radien."""
    n = len(contour)

    # Fuer jede Ecke: Tangentenpunkte und Arc-Info berechnen
    corners = []
    for i in range(n):
        x, y, r = contour[i]
        px, py, _ = contour[(i - 1) % n]
        nx, ny, _ = contour[(i + 1) % n]

        if r <= 0:
            corners.append({'tp_in': (x, y), 'tp_out': (x, y), 'tdist': 0, 'arc': None})
            continue

        # Richtungsvektoren von Ecke zu Vorgaenger und Nachfolger
        v1x, v1y = px - x, py - y
        v2x, v2y = nx - x, ny - y
        len1 = math.hypot(v1x, v1y)
        len2 = math.hypot(v2x, v2y)
        v1x, v1y = v1x / len1, v1y / len1
        v2x, v2y = v2x / len2, v2y / len2

        # Winkel zwischen den beiden Richtungen
        dot_val = max(-1.0, min(1.0, v1x * v2x + v1y * v2y))
        theta = math.acos(dot_val)

        # Tangenten-Abstand von Ecke
        t = r / math.tan(theta / 2)

        # Tangentenpunkte
        tp_in = (x + t * v1x, y + t * v1y)
        tp_out = (x + t * v2x, y + t * v2y)

        # Arc-Zentrum (auf Winkelhalbierender)
        bx = v1x + v2x
        by = v1y + v2y
        bl = math.hypot(bx, by)
        bx, by = bx / bl, by / bl
        cd = r / math.sin(theta / 2)
        cx = x + cd * bx
        cy = y + cd * by

        corners.append({'tp_in': tp_in, 'tp_out': tp_out, 'tdist': t,
                         'arc': (cx, cy, r, tp_in, tp_out)})

    # Linienlaengen pruefen
    for i in range(n):
        j = (i + 1) % n
        xi, yi, _ = contour[i]
        xj, yj, _ = contour[j]
        line_full = math.hypot(xj - xi, yj - yi)
        used = corners[i]['tdist'] + corners[j]['tdist']
        remaining = line_full - used
        if remaining < -0.01:
            print("WARNUNG: Linie {}->{} zu kurz! Verfuegbar: {:.2f}, benoetigt: {:.2f}".format(
                i, j, line_full, used))

    # Segmente erzeugen
    segments = []
    for i in range(n):
        j = (i + 1) % n

        # Arc an Ecke i
        arc = corners[i]['arc']
        if arc:
            segments.append(("arc", arc))

        # Linie von tp_out[i] zu tp_in[j]
        x1, y1 = corners[i]['tp_out']
        x2, y2 = corners[j]['tp_in']
        line_len = math.hypot(x2 - x1, y2 - y1)
        if line_len > 0.001:
            segments.append(("line", (x1, y1, x2, y2)))

    return segments


# ============================================================
# SVG-Export
# ============================================================
def contour_to_svg(contour, show_corners=False):
    """Erzeuge SVG-String aus Kontur mit Fillet-Radien.

    Args:
        contour: Liste von (x, y, radius) Tupeln
        show_corners: Wenn True, blaue Eckpunkte und Nummern anzeigen
    """
    segments = build_contour_segments(contour)

    # BoundingBox aus Kontur-Punkten
    xs = [p[0] for p in contour]
    ys = [p[1] for p in contour]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    margin = 5.0
    w = xmax - xmin + 2 * margin
    h = ymax - ymin + 2 * margin

    svg = '<?xml version="1.0" encoding="UTF-8"?>\n'
    svg += '<svg xmlns="http://www.w3.org/2000/svg" width="{:.2f}mm" height="{:.2f}mm" viewBox="{:.3f} {:.3f} {:.3f} {:.3f}">\n'.format(
        w, h, xmin - margin, -ymax - margin, w, h)

    # Weisser Hintergrund
    svg += '<rect x="{:.3f}" y="{:.3f}" width="{:.3f}" height="{:.3f}" fill="white"/>\n'.format(
        xmin - margin, -ymax - margin, w, h)

    # Kontur-Segmente (rot)
    svg += '<!-- === Kontur-Segmente ({}) === -->\n'.format(len(segments))
    for seg in segments:
        if seg[0] == "line":
            x1, y1, x2, y2 = seg[1]
            svg += '<line x1="{:.4f}" y1="{:.4f}" x2="{:.4f}" y2="{:.4f}" stroke="red" stroke-width="0.3"/>\n'.format(
                x1, -y1, x2, -y2)
        elif seg[0] == "arc":
            cx, cy, r, (sx, sy), (ex, ey) = seg[1]
            cross = (ex - cx) * (sy - cy) - (sx - cx) * (ey - cy)
            sweep_flag = 1 if cross > 0 else 0
            svg += '<path d="M{:.4f},{:.4f} A{:.4f},{:.4f} 0 0 {} {:.4f},{:.4f}" fill="none" stroke="red" stroke-width="0.3"/>\n'.format(
                sx, -sy, r, r, sweep_flag, ex, -ey)

    # Optionale Eckpunkte und Nummern
    if show_corners:
        svg += '<!-- === Kontur-Eckpunkte === -->\n'
        dot_r = max(0.3, min(w, h) * 0.004)
        font_size = max(1.5, min(w, h) * 0.02)
        for i, (cx, cy, r) in enumerate(contour):
            svg += '<circle cx="{:.4f}" cy="{:.4f}" r="{:.2f}" fill="blue" opacity="0.6"/>\n'.format(
                cx, -cy, dot_r)
            svg += '<text x="{:.4f}" y="{:.4f}" font-size="{:.1f}" fill="blue" opacity="0.7">{}</text>\n'.format(
                cx + dot_r * 2, -cy + font_size * 0.35, font_size, i)

    svg += '</svg>\n'
    return svg


# ============================================================
# FreeCAD Geometrie
# ============================================================
def contour_to_wire(contour):
    """Erzeuge einen FreeCAD-Wire aus Kontur mit Fillet-Radien."""
    import Part
    import FreeCAD as App

    segments = build_contour_segments(contour)
    edges = []
    for seg in segments:
        if seg[0] == "line":
            x1, y1, x2, y2 = seg[1]
            edges.append(Part.makeLine(App.Vector(x1, y1, 0), App.Vector(x2, y2, 0)))
        elif seg[0] == "arc":
            cx, cy, r, (sx, sy), (ex, ey) = seg[1]
            center = App.Vector(cx, cy, 0)
            start = App.Vector(sx, sy, 0)
            end = App.Vector(ex, ey, 0)
            # Mittelpunkt des Bogens berechnen
            mid_x = (sx + ex) / 2
            mid_y = (sy + ey) / 2
            # Richtung vom Zentrum zum Mittelpunkt, auf Radius normieren
            dx = mid_x - cx
            dy = mid_y - cy
            dist = math.hypot(dx, dy)
            if dist > 0.0001:
                mid_arc = App.Vector(cx + r * dx / dist, cy + r * dy / dist, 0)
            else:
                mid_arc = App.Vector(cx + r, cy, 0)
            edges.append(Part.Arc(start, mid_arc, end).toShape())

    return Part.Wire(edges)


def create_geometry(doc):
    """Hauptfunktion - erzeugt Geometrie und gibt Liste von Objekten zurück."""
    import Part
    import FreeCAD as App

    d = PARAMS["HOLDER_DEPTH_MM"]
    z_fillet_r = PARAMS["Z_FILLET_R_MM"]  # 0 = aus
    stem_len = PARAMS["STEM_LENGTH_MM"]
    stem_r = PARAMS["STEM_DIAMETER_MM"] / 2
    ball_r = PARAMS["BALL_DIAMETER_MM"] / 2
    hole_r = PARAMS["CUTOUT_DIAMETER_MM"] / 2
    chamfer = PARAMS["CUTOUT_CHAMFER_MM"]

    # Wire aus Kontur erzeugen, zu Face machen, extrudieren
    wire = contour_to_wire(CONTOUR)
    face = Part.Face(wire)
    shape = face.extrude(App.Vector(0, 0, d))

    # Fillet an den Z-Kanten (Konturkanten bei Z=0 und Z=d)
    if z_fillet_r > 0:
        z_edges = []
        for edge in shape.Edges:
            verts = edge.Vertexes
            if len(verts) >= 2:
                all_bottom = all(abs(v.Point.z) < 0.01 for v in verts)
                all_top = all(abs(v.Point.z - d) < 0.01 for v in verts)
                if all_bottom or all_top:
                    z_edges.append(edge)
        if z_edges:
            shape = shape.makeFillet(z_fillet_r, z_edges)

    # Zylinder senkrecht auf der Fläche 15->16 (zeigt in -X Richtung)
    p15 = CONTOUR[15]
    p16 = CONTOUR[16]
    # Richtung der Kante
    edge_dx = p16[0] - p15[0]
    edge_dy = p16[1] - p15[1]
    edge_len = math.hypot(edge_dx, edge_dy)
    # Auswärts-Normale (links der Kantenrichtung bei CCW-Kontur)
    nx = -edge_dy / edge_len
    ny = edge_dx / edge_len
    # Position auf 25% der Kante (Richtung Bogen/Punkt 4), auf halber Z-Höhe
    t = 0.25
    mid_x = p15[0] + t * edge_dx
    mid_y = p15[1] + t * edge_dy
    mid_z = d / 2
    # Zylinder + Kugel: Stiel mit Kugelkopf
    cyl_total = stem_len + ball_r
    cyl = Part.makeCylinder(stem_r, cyl_total,
                            App.Vector(mid_x, mid_y, mid_z),
                            App.Vector(nx, ny, 0))
    shape = shape.fuse(cyl)

    sphere_center = App.Vector(mid_x + cyl_total * nx, mid_y + cyl_total * ny, mid_z)
    sphere = Part.makeSphere(ball_r, sphere_center)
    shape = shape.fuse(sphere)

    # Material-Cutouts auf der Fläche 15->16
    hole_depth = 50.0  # lang genug um durch die gesamte Wandstärke zu gehen
    
    for t_hole in [0.45, 0.75]:  # Positionen auf der Kante 15->16, gleichmäßig verteilt (Zylinder bei t=0.25)
        hx = p15[0] + t_hole * edge_dx
        hy = p15[1] + t_hole * edge_dy
        # Start hinter der Fläche (entgegen Normalenrichtung)
        start = App.Vector(hx - 25 * nx, hy - 25 * ny, mid_z)
        hole_cyl = Part.makeCylinder(hole_r, hole_depth, start, App.Vector(nx, ny, 0))
        shape = shape.cut(hole_cyl)
        # 45°-Fase am Cutout
        # Innere Seite (Fläche 15->16, bei hx/hy): Kegel zeigt nach außen (+nx/+ny)
        cone_inner = Part.makeCone(hole_r + chamfer, hole_r, chamfer,
                                   App.Vector(hx, hy, mid_z), App.Vector(nx, ny, 0))
        shape = shape.cut(cone_inner)
        # Äußere Seite (Fläche 3->4, ca. 5mm in +nx/+ny Richtung): Kegel zeigt nach innen (-nx/-ny)
        wall = 5.2
        cone_outer = Part.makeCone(hole_r + chamfer, hole_r, chamfer,
                                   App.Vector(hx + wall * nx, hy + wall * ny, mid_z),
                                   App.Vector(-nx, -ny, 0))
        shape = shape.cut(cone_outer)

    # Material-Cutout auf der Fläche 14->15 (y=5, geht in X-Richtung)
    # Cutout-Zylinder in Y-Richtung (Normale dieser Fläche)
    hole_x_14_15 = 43.0  # ungefähr Mitte der Fläche in X
    hole_start_14_15 = App.Vector(hole_x_14_15, -25, mid_z)
    hole_cyl_14_15 = Part.makeCylinder(hole_r, hole_depth, hole_start_14_15, App.Vector(0, 1, 0))
    shape = shape.cut(hole_cyl_14_15)
    # 45°-Fase am Cutout 14->15 (Flächen bei y≈0 und y≈5)
    for y_surface, dy in [(0, 1), (5, -1)]:
        cone_base = App.Vector(hole_x_14_15, y_surface, mid_z)
        cone = Part.makeCone(hole_r + chamfer, hole_r, chamfer,
                             cone_base, App.Vector(0, dy, 0))
        shape = shape.cut(cone)

    obj = doc.addObject("Part::Feature", "ID7MobileHolder")
    obj.Shape = shape
    return [obj]


# ============================================================
# Standalone: SVG generieren (kein FreeCAD noetig)
# ============================================================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ID.7 Mobile Holder - SVG Preview")
    parser.add_argument("--corners", action="store_true",
                        help="Eckpunkte und Nummern anzeigen (blau)")
    parser.add_argument("--output", "-o", default="id7_mobile_holder.svg",
                        help="Ausgabe-Datei (default: id7_mobile_holder.svg)")
    args = parser.parse_args()

    svg = contour_to_svg(CONTOUR, show_corners=args.corners)
    with open(args.output, "w") as f:
        f.write(svg)
    print("SVG geschrieben: {} ({} Eckpunkte, {} Segmente)".format(
        args.output, len(CONTOUR), len(build_contour_segments(CONTOUR))))
