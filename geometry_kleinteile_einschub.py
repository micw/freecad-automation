# geometry_kleinteile_einschub.py
# Einschub für Kleinteile-Boxen
#
# Usage:
#   ./freecad_headless.py test geometry_kleinteile_einschub.py
#   ./freecad_headless.py export-stl geometry_kleinteile_einschub.py einschub.stl

import os
import Part
import FreeCAD as App

# Default parameters - can be overridden via environment variables with same name
DEFAULTS = {
    "EINSCHUB_WIDTH_MM": 52.0,      # Breite (X)
    "EINSCHUB_HEIGHT_MM": 46.0,     # Höhe (Y)
    "EINSCHUB_THICKNESS_MM": 1.0,   # Dicke (Z)
    "EINSCHUB_CORNER_RADIUS_MM": 6.0,  # Radius der unteren Ecken
    # Verstärkte Ränder (auf Oberseite)
    "EINSCHUB_RIM_THICKNESS_MM": 2.5,  # Dicke der verstärkten Ränder
    "EINSCHUB_RIM_WIDTH_MM": 0.6,      # Breite der verstärkten Ränder
    "EINSCHUB_RIM_TOP": 1,             # Oberer Rand an (1) / aus (0)
    "EINSCHUB_RIM_SIDES_PERCENT": 50.0,  # Seitliche Ränder: wie weit von oben (in %)
}

# Load parameters (clone defaults and override from environment)
PARAMS = DEFAULTS.copy()
for key, default_value in DEFAULTS.items():
    env_value = os.environ.get(key)
    if env_value is not None:
        if isinstance(default_value, int):
            PARAMS[key] = int(env_value)
        elif isinstance(default_value, float):
            PARAMS[key] = float(env_value)
        else:
            PARAMS[key] = env_value


def create_geometry(doc):
    """
    Create Einschub für Kleinteile-Boxen.

    Args:
        doc: Active FreeCAD document.

    Returns:
        List of created FreeCAD objects.
    """
    # Load parameters
    width = PARAMS["EINSCHUB_WIDTH_MM"]
    height = PARAMS["EINSCHUB_HEIGHT_MM"]
    thickness = PARAMS["EINSCHUB_THICKNESS_MM"]
    corner_radius = PARAMS["EINSCHUB_CORNER_RADIUS_MM"]
    rim_thickness = PARAMS["EINSCHUB_RIM_THICKNESS_MM"]
    rim_width = PARAMS["EINSCHUB_RIM_WIDTH_MM"]
    rim_top = PARAMS["EINSCHUB_RIM_TOP"]
    rim_sides_percent = PARAMS["EINSCHUB_RIM_SIDES_PERCENT"]

    # Create 2D profile with rounded bottom corners
    # Start with a wire: bottom left -> bottom right -> top right -> top left -> back
    r = corner_radius
    half_w = width / 2
    half_h = height / 2

    # Points for the profile (counterclockwise from bottom-left after corner arc)
    # Bottom edge with rounded corners at both ends
    points = [
        App.Vector(-half_w + r, -half_h, 0),  # After bottom-left arc
        App.Vector(half_w - r, -half_h, 0),   # Before bottom-right arc
    ]

    # Create edges
    edges = []

    # Bottom edge (straight)
    edges.append(Part.makeLine(points[0], points[1]))

    # Bottom-right corner arc
    arc_br = Part.makeCircle(r, App.Vector(half_w - r, -half_h + r, 0), App.Vector(0, 0, 1), -90, 0)
    edges.append(arc_br)

    # Right edge (straight)
    edges.append(Part.makeLine(App.Vector(half_w, -half_h + r, 0), App.Vector(half_w, half_h, 0)))

    # Top edge (straight, no rounding)
    edges.append(Part.makeLine(App.Vector(half_w, half_h, 0), App.Vector(-half_w, half_h, 0)))

    # Left edge (straight)
    edges.append(Part.makeLine(App.Vector(-half_w, half_h, 0), App.Vector(-half_w, -half_h + r, 0)))

    # Bottom-left corner arc
    arc_bl = Part.makeCircle(r, App.Vector(-half_w + r, -half_h + r, 0), App.Vector(0, 0, 1), 180, 270)
    edges.append(arc_bl)

    # Create wire and face
    wire = Part.Wire(edges)
    face = Part.Face(wire)

    # Extrude to create solid
    base = face.extrude(App.Vector(0, 0, thickness))

    # Center in Z
    base.translate(App.Vector(0, 0, -thickness / 2))

    # Add reinforced rims on top surface
    rim_extra = rim_thickness - thickness  # Additional height above base
    if rim_extra > 0:
        # Top rim (full width)
        if rim_top:
            top_rim = Part.makeBox(width, rim_width, rim_extra)
            top_rim.translate(App.Vector(-width / 2, half_h - rim_width, thickness / 2))
            base = base.fuse(top_rim)

        # Side rims (from top, going down by percentage) with 45° taper at bottom end
        if rim_sides_percent > 0:
            side_length = height * (rim_sides_percent / 100.0)
            z_base = thickness / 2  # Z position of top of base plate

            # Create tapered side rim profile (trapezoid in Y-Z plane)
            # The rim goes from top (Y = half_h) down to (Y = half_h - side_length)
            # Taper is at the bottom of the rim (lower Y values)
            # Profile in local coordinates where Y=0 is at the bottom of the rim

            taper_length = min(rim_extra, side_length)  # 45° means taper length = rim_extra

            # Profile points from bottom to top (Y increasing = going up toward top edge)
            # Y=0 is at bottom of rim, Y=side_length is at top of rim (at the top edge)
            left_profile_points = [
                App.Vector(0, 0, 0),  # bottom-back (tapered to 0)
                App.Vector(0, taper_length, rim_extra),  # after taper (full height)
                App.Vector(0, side_length, rim_extra),  # top-front (full height)
                App.Vector(0, side_length, 0),  # top-back
            ]

            left_wire = Part.makePolygon(left_profile_points + [left_profile_points[0]])
            left_face = Part.Face(left_wire)
            left_rim = left_face.extrude(App.Vector(rim_width, 0, 0))
            # Position: bottom of rim is at Y = half_h - side_length
            left_rim.translate(App.Vector(-half_w, half_h - side_length, z_base))
            base = base.fuse(left_rim)

            # Right side rim - mirror of left
            right_rim = left_face.extrude(App.Vector(rim_width, 0, 0))
            right_rim.translate(App.Vector(half_w - rim_width, half_h - side_length, z_base))
            base = base.fuse(right_rim)

    # Add grip ridges (horizontal raised bars for better grip)
    # 3 ridges from top to bottom: 20mm, 17.5mm, 15mm wide
    # 0.5mm raised, 2.5mm spacing from top
    grip_height = 0.5  # Höhe der Erhöhungen
    grip_widths = [20.0, 17.5, 15.0]  # Breiten von oben nach unten
    grip_thickness = 1.0  # Dicke der Erhöhungen (in Y-Richtung)
    grip_spacing = 2.5  # Abstand von oben und zwischen den Erhöhungen

    z_top = thickness / 2  # Oberseite der Basisplatte
    y_pos = half_h - grip_spacing - grip_thickness  # Startposition für erste Erhöhung

    for grip_w in grip_widths:
        grip = Part.makeBox(grip_w, grip_thickness, grip_height)
        grip.translate(App.Vector(-grip_w / 2, y_pos, z_top))
        base = base.fuse(grip)
        y_pos -= (grip_thickness + grip_spacing)  # Nächste Position

    # Create FreeCAD object
    obj = doc.addObject("Part::Feature", "Einschub")
    obj.Shape = base

    return [obj]
