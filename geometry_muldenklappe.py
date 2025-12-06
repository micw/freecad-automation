# geometry_muldenklappe.py
# Parameterized Muldenklappe (tailgate) for Bruder Kipper-Anhänger
#
# Usage with export script:
#   FreeCADCmd export_to_stl.py geometry_muldenklappe.py muldenklappe.stl
#
# Parameters can be adjusted via environment variables (see DEFAULTS below)
#
# Notes:
# - Coordinate system: X=length, Y=width, Z=height.
# - Orientation: "Unten" (bottom) der Klappe ist bei Y = -height/2 (negative Y-Richtung)
#   Die untere Kante ist die lange Kante entlang X bei Y = -height/2

import os
import Part
import FreeCAD as App

# Default parameters - can be overridden via environment variables with same name
DEFAULTS = {
    "KLAPPE_WIDTH_MM": 132.0,       # Width of the tailgate (X)
    "KLAPPE_HEIGHT_MM": 66.0,       # Height of the tailgate (Y)
    "KLAPPE_THICKNESS_MM": 8.0,     # Thickness of the tailgate (Z)
    "KLAPPE_EDGE_RADIUS_MM": 1.0,   # Radius for long edges (8 edges along X, Y, Z directions)
    "KLAPPE_CORNER_RADIUS_MM": 4.0, # Radius for short corner edges (4 vertical edges at corners)
    "KLAPPE_HOLDER_HEIGHT_MM": 8.0,    # Height of the mounting holders (Zapfen-Halter) in Y direction
    "KLAPPE_HOLDER_THICKNESS_MM": 1.5, # Thickness of the mounting holders (X dimension)
    "KLAPPE_HOLDER_RADIUS_MM": 3.0,    # Rounding radius for the holder tops
    "KLAPPE_PIN_DIAMETER_MM": 5.0,     # Diameter of the mounting pins (Zapfen)
    "KLAPPE_PIN_LENGTH_MM": 6.0,       # Length of the mounting pins
    "KLAPPE_PIN_TIP_DIAMETER_MM": 4.0, # Diameter of the pin tip (smaller cylinder)
    "KLAPPE_PIN_EDGE_RADIUS_MM": 1.0,  # Radius of the rounded edge (torus), also height of tip
    "KLAPPE_CUTOUT_DEPTH_MM": 6.5,     # Depth of the cutout (thickness - 1.5mm remaining)
    "KLAPPE_CUTOUT_TOP_MM": 15.0,      # Distance from top edge (Y = +height/2)
    "KLAPPE_CUTOUT_BOTTOM_MM": 4.0,    # Distance from bottom edge (Y = -height/2)
    "KLAPPE_CUTOUT_SIDES_MM": 10.0,    # Distance from left/right edges
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
    Create Muldenklappe (tailgate) for Bruder Kipper-Anhänger.

    Args:
        doc: Active FreeCAD document.

    Returns:
        List of created FreeCAD objects.
    """
    # Load parameters
    width = PARAMS["KLAPPE_WIDTH_MM"]
    height = PARAMS["KLAPPE_HEIGHT_MM"]
    thickness = PARAMS["KLAPPE_THICKNESS_MM"]
    edge_radius = PARAMS["KLAPPE_EDGE_RADIUS_MM"]
    corner_radius = PARAMS["KLAPPE_CORNER_RADIUS_MM"]
    holder_height = PARAMS["KLAPPE_HOLDER_HEIGHT_MM"]
    holder_thickness = PARAMS["KLAPPE_HOLDER_THICKNESS_MM"]
    holder_radius = PARAMS["KLAPPE_HOLDER_RADIUS_MM"]
    pin_diameter = PARAMS["KLAPPE_PIN_DIAMETER_MM"]
    pin_length = PARAMS["KLAPPE_PIN_LENGTH_MM"]
    pin_tip_diameter = PARAMS["KLAPPE_PIN_TIP_DIAMETER_MM"]
    pin_edge_radius = PARAMS["KLAPPE_PIN_EDGE_RADIUS_MM"]
    cutout_remaining = 1.5  # Remaining thickness after cutout
    cutout_depth = thickness - cutout_remaining
    cutout_top = PARAMS["KLAPPE_CUTOUT_TOP_MM"]
    cutout_bottom = PARAMS["KLAPPE_CUTOUT_BOTTOM_MM"]
    cutout_sides = PARAMS["KLAPPE_CUTOUT_SIDES_MM"]
    rib_width = 10.0  # Width of the ribs (anti-cutout rectangles)
    rib_count = 3     # Number of ribs
    
    # Create base rectangle extruded to thickness
    # Box is centered at origin in X and Y, starts at Z=0
    base_box = Part.makeBox(
        width,      # X dimension
        height,     # Y dimension
        thickness,  # Z dimension
        App.Vector(-width/2, -height/2, 0)  # Centered at origin
    )
    
    # Create cutout on the top surface (Z = thickness, the "outside" when printing lying down)
    # The cutout reduces the thickness to cutout_remaining (1.5mm)
    # Cutout dimensions:
    # - X: from -width/2 + cutout_sides to width/2 - cutout_sides
    # - Y: from -height/2 + cutout_bottom to height/2 - cutout_top
    # - Z: from thickness - cutout_depth to thickness (cutting into the top)
    cutout_width = width - 2 * cutout_sides
    cutout_height = height - cutout_top - cutout_bottom
    cutout_box = Part.makeBox(
        cutout_width,
        cutout_height,
        cutout_depth,
        App.Vector(-cutout_width/2, -height/2 + cutout_bottom, thickness - cutout_depth)
    )
    
    # Cut the cutout from the base
    base_box = base_box.cut(cutout_box)
    
    # Create mounting holders (Zapfen-Halter) at the top corners (Y = +height/2)
    # They extend the short side walls upwards.
    # Orientation: Flat in YZ plane, full plate thickness in Z.
    # Dimensions: Thickness in X, Height in Y, full thickness in Z.
    # This ensures good 3D printability (no overhangs) and clean transitions.
    
    # Overlap for fuse stability
    overlap = 0.1
    
    # Create left holder - flush with left edge, full Z thickness
    left_holder = Part.makeBox(
        holder_thickness,       # X
        holder_height + overlap, # Y (extends upward + overlap into base)
        thickness,              # Z (full plate thickness)
        App.Vector(-width/2, height/2 - overlap, 0)
    )
    
    # Create right holder - flush with right edge, full Z thickness
    right_holder = Part.makeBox(
        holder_thickness,       # X
        holder_height + overlap, # Y
        thickness,              # Z (full plate thickness)
        App.Vector(width/2 - holder_thickness, height/2 - overlap, 0)
    )
    
    # Create triangular support gussets in the corner between plate top and holder
    # These are right triangles extruded to full plate thickness.
    # Triangle: One leg along holder (Y direction), one leg along plate top (X direction)
    # Size: holder_height x holder_height (45 degree angle for good printability)
    
    # Left gusset: sits at inner side of left holder
    # Triangle vertices (in XY plane):
    # - Corner at holder inner edge and plate top: (-width/2 + holder_thickness, height/2)
    # - Along holder upward: (-width/2 + holder_thickness, height/2 + holder_height)
    # - Along plate inward: (-width/2 + holder_thickness + holder_height, height/2)
    left_gusset_points = [
        App.Vector(-width/2 + holder_thickness, height/2 - overlap, 0),
        App.Vector(-width/2 + holder_thickness, height/2 + holder_height, 0),
        App.Vector(-width/2 + holder_thickness + holder_height, height/2 - overlap, 0),
        App.Vector(-width/2 + holder_thickness, height/2 - overlap, 0),  # Close the triangle
    ]
    left_gusset_wire = Part.makePolygon(left_gusset_points)
    left_gusset_face = Part.Face(left_gusset_wire)
    left_gusset = left_gusset_face.extrude(App.Vector(0, 0, thickness))
    
    # Right gusset: sits at inner side of right holder (mirrored)
    right_gusset_points = [
        App.Vector(width/2 - holder_thickness, height/2 - overlap, 0),
        App.Vector(width/2 - holder_thickness, height/2 + holder_height, 0),
        App.Vector(width/2 - holder_thickness - holder_height, height/2 - overlap, 0),
        App.Vector(width/2 - holder_thickness, height/2 - overlap, 0),  # Close the triangle
    ]
    right_gusset_wire = Part.makePolygon(right_gusset_points)
    right_gusset_face = Part.Face(right_gusset_wire)
    right_gusset = right_gusset_face.extrude(App.Vector(0, 0, thickness))
    
    # Create mounting pins (Zapfen) on the holders
    # Pins point outward (in X direction) from the holders
    # Structure: Main cylinder + half-torus for rounded edge + smaller tip cylinder
    # The tip cylinder height equals the torus minor radius (pin_edge_radius)
    pin_radius = pin_diameter / 2.0
    pin_tip_radius = pin_tip_diameter / 2.0
    pin_y = height/2 + holder_height / 2.0  # Centered on holder height
    pin_z = thickness / 2.0  # Centered on plate thickness
    
    def create_pin(start_pos, direction):
        """
        Create a pin with rounded edge and smaller tip.
        start_pos: Starting position (at holder outer edge)
        direction: Direction vector (1 or -1 in X)
        """
        dir_vec = App.Vector(direction, 0, 0)
        
        # Main cylinder (shorter to make room for torus)
        main_length = pin_length - pin_edge_radius
        main_cyl = Part.makeCylinder(
            pin_radius,
            main_length,
            start_pos,
            dir_vec
        )
        
        # Half-torus at the end for rounded edge
        # Torus major radius = pin_radius - pin_edge_radius (center of tube ring)
        # Torus minor radius = pin_edge_radius (tube thickness)
        torus_major_radius = pin_radius - pin_edge_radius
        torus_minor_radius = pin_edge_radius
        
        torus_center = App.Vector(
            start_pos.x + direction * main_length,
            start_pos.y,
            start_pos.z
        )
        
        # Create torus oriented perpendicular to pin direction
        torus = Part.makeTorus(
            torus_major_radius,
            torus_minor_radius,
            torus_center,
            dir_vec  # Axis of the torus ring
        )
        
        # Smaller tip cylinder extending from the torus
        # Height = pin_edge_radius (same as torus minor radius)
        tip_start = App.Vector(
            start_pos.x + direction * main_length,
            start_pos.y,
            start_pos.z
        )
        tip_cyl = Part.makeCylinder(
            pin_tip_radius,
            pin_edge_radius,  # Height = torus radius
            tip_start,
            dir_vec
        )
        
        # Fuse all parts
        pin = main_cyl.fuse(torus)
        pin = pin.fuse(tip_cyl)
        
        return pin
    
    # Left pin: points in -X direction (outward from left holder)
    left_pin = create_pin(App.Vector(-width/2, pin_y, pin_z), -1)
    
    # Right pin: points in +X direction (outward from right holder)
    right_pin = create_pin(App.Vector(width/2, pin_y, pin_z), 1)
    
    # Fuse base geometry first (without pins), then apply fillets
    fused_shape = base_box.fuse(left_holder)
    fused_shape = fused_shape.fuse(right_holder)
    fused_shape = fused_shape.fuse(left_gusset)
    fused_shape = fused_shape.fuse(right_gusset)
    
    # Step 1: Apply corner rounding to the 2 bottom corners (4mm radius)
    # These are edges parallel to Z at the bottom (Y = -height/2)
    if corner_radius > 0:
        corner_edges = []
        for edge in fused_shape.Edges:
            # Only process straight lines
            if "Line" not in edge.Curve.TypeId:
                continue
            edge_length = edge.Length
            # Short edges parallel to Z have length = thickness
            if abs(edge_length - thickness) < 0.01:
                edge_center = edge.CenterOfMass
                # Bottom corners: Y close to -height/2
                if edge_center.y < -height/2 + 1.0:
                    corner_edges.append(edge)
        
        if corner_edges:
            fused_shape = fused_shape.makeFillet(corner_radius, corner_edges)
    
    # Step 2: Apply holder top rounding (3mm radius)
    # These are edges parallel to X at the top of the holders (Y = height/2 + holder_height)
    if holder_radius > 0:
        holder_top_edges = []
        for edge in fused_shape.Edges:
            # Only process straight lines
            if "Line" not in edge.Curve.TypeId:
                continue
            # Check edge length - should be holder_thickness
            if abs(edge.Length - holder_thickness) < 0.01:
                edge_center = edge.CenterOfMass
                # At holder top Y
                if abs(edge_center.y - (height/2 + holder_height)) < 0.1:
                    holder_top_edges.append(edge)
        
        if holder_top_edges:
            fused_shape = fused_shape.makeFillet(holder_radius, holder_top_edges)
    
    # Step 3: Apply edge rounding (1mm) to specific outer edges
    # We apply fillet to each group separately to avoid kernel issues
    if edge_radius > 0:
        # 3a: Bottom horizontal edges (along X at Y=-height/2)
        bottom_edges = []
        for edge in fused_shape.Edges:
            # Only process straight lines
            if "Line" not in edge.Curve.TypeId:
                continue
            if abs(edge.Length - width) < 0.01:  # Full width edges
                edge_center = edge.CenterOfMass
                if abs(edge_center.y - (-height/2)) < 0.1:
                    bottom_edges.append(edge)
        if bottom_edges:
            fused_shape = fused_shape.makeFillet(edge_radius, bottom_edges)
        
        # 3b: Left/right outer vertical edges on holders (parallel to Y)
        side_edges = []
        for edge in fused_shape.Edges:
            # Only process straight lines
            if "Line" not in edge.Curve.TypeId:
                continue
            edge_center = edge.CenterOfMass
            # Outer X position (at plate/holder edges)
            if abs(abs(edge_center.x) - width/2) < 0.1:
                # Only Y-direction edges on holders (above plate top)
                if edge_center.y > height/2 - 0.1:
                    # Check it's a vertical edge (parallel to Y)
                    p1 = edge.Vertexes[0].Point
                    p2 = edge.Vertexes[1].Point
                    if abs(p1.x - p2.x) < 0.01 and abs(p1.z - p2.z) < 0.01:
                        side_edges.append(edge)
        if side_edges:
            fused_shape = fused_shape.makeFillet(edge_radius, side_edges)
        
        # 3c: Z-direction edges at top corners of plate (excluding bottom which has corner_radius)
        top_z_edges = []
        for edge in fused_shape.Edges:
            # Only process straight lines
            if "Line" not in edge.Curve.TypeId:
                continue
            if abs(edge.Length - thickness) < 0.01:
                edge_center = edge.CenterOfMass
                # Top of plate but not at holder positions
                if abs(edge_center.y - height/2) < 0.1:
                    # Exclude holder positions
                    if abs(edge_center.x) < width/2 - holder_thickness - 0.1:
                        top_z_edges.append(edge)
        if top_z_edges:
            fused_shape = fused_shape.makeFillet(edge_radius, top_z_edges)
        
        # 3d: Top horizontal edges of the plate (along X at Y=height/2, between gussets)
        # These are the edges at the top of the base plate, excluding the holder/gusset areas
        top_horizontal_edges = []
        for edge in fused_shape.Edges:
            # Only process straight lines
            if "Line" not in edge.Curve.TypeId:
                continue
            edge_center = edge.CenterOfMass
            # At top of plate Y position
            if abs(edge_center.y - height/2) < 0.1:
                # X-direction edges (check start/end points)
                p1 = edge.Vertexes[0].Point
                p2 = edge.Vertexes[1].Point
                if abs(p1.y - p2.y) < 0.01 and abs(p1.z - p2.z) < 0.01:
                    # Not at holder positions (between gussets, in the middle)
                    if abs(edge_center.x) < width/2 - holder_thickness - holder_height - 0.1:
                        top_horizontal_edges.append(edge)
        if top_horizontal_edges:
            fused_shape = fused_shape.makeFillet(edge_radius, top_horizontal_edges)
        
        # 3e: Diagonal edges of the gussets (the hypotenuse of the triangles)
        # These are diagonal edges with length = sqrt(2) * holder_height
        gusset_diagonal_length = (2 ** 0.5) * holder_height
        gusset_edges = []
        for edge in fused_shape.Edges:
            # Only process straight lines
            if "Line" not in edge.Curve.TypeId:
                continue
            # Check for diagonal length
            if abs(edge.Length - gusset_diagonal_length) < 0.2:
                edge_center = edge.CenterOfMass
                # Should be above plate top
                if edge_center.y > height/2 - 0.1:
                    gusset_edges.append(edge)
        if gusset_edges:
            fused_shape = fused_shape.makeFillet(edge_radius, gusset_edges)
        
        # 3f: Cutout outer edges on top surface (Z = thickness)
        # These are the horizontal edges forming the cutout border at top surface level
        cutout_outer_edges = []
        for edge in fused_shape.Edges:
            # Only process straight lines
            if "Line" not in edge.Curve.TypeId:
                continue
            edge_center = edge.CenterOfMass
            # At top surface Z level
            if abs(edge_center.z - thickness) < 0.1:
                # Long cutout edges (parallel to X)
                if abs(edge.Length - cutout_width) < 0.1:
                    cutout_outer_edges.append(edge)
                # Short cutout edges (parallel to Y)
                elif abs(edge.Length - cutout_height) < 0.1:
                    cutout_outer_edges.append(edge)
        if cutout_outer_edges:
            fused_shape = fused_shape.makeFillet(edge_radius, cutout_outer_edges)

    # Add ribs (anti-cutout rectangles) inside the cutout AFTER fillets
    # 3 ribs evenly spaced across the cutout width
    # Height: from cutout bottom (thickness - cutout_depth) to thickness - edge_radius
    rib_height_z = cutout_depth - edge_radius  # Height of ribs (stop before fillet)
    rib_z_start = thickness - cutout_depth     # Z position where ribs start
    
    # Calculate equal spacing between ribs (and between ribs and cutout edges)
    # Total space = cutout_width - (rib_count * rib_width)
    # Number of gaps = rib_count + 1
    total_rib_width = rib_count * rib_width
    total_gap_space = cutout_width - total_rib_width
    gap_width = total_gap_space / (rib_count + 1)
    cutout_x_start = -cutout_width / 2
    
    # Store rib positions for later filleting
    rib_positions = []
    for i in range(rib_count):
        # Position: start + gap + i * (rib_width + gap)
        rib_left_x = cutout_x_start + gap_width + i * (rib_width + gap_width)
        rib_positions.append(rib_left_x)
        rib_box = Part.makeBox(
            rib_width,
            cutout_height,
            rib_height_z,
            App.Vector(rib_left_x, -height/2 + cutout_bottom, rib_z_start)
        )
        fused_shape = fused_shape.fuse(rib_box)
    
    # Apply fillet to the long edges of the ribs (Y-direction edges at left/right of ribs)
    if edge_radius > 0:
        rib_long_edges = []
        for edge in fused_shape.Edges:
            # Only process straight lines
            if "Line" not in edge.Curve.TypeId:
                continue
            # Check if edge has cutout_height length (Y-direction edge)
            if abs(edge.Length - cutout_height) < 0.1:
                edge_center = edge.CenterOfMass
                # Check Z position is at top of ribs
                rib_top_z = rib_z_start + rib_height_z
                if abs(edge_center.z - rib_top_z) < 0.1:
                    # Check if X is at rib left or right edge
                    for rib_left in rib_positions:
                        rib_right = rib_left + rib_width
                        if abs(edge_center.x - rib_left) < 0.1 or abs(edge_center.x - rib_right) < 0.1:
                            rib_long_edges.append(edge)
                            break
        if rib_long_edges:
            fused_shape = fused_shape.makeFillet(edge_radius, rib_long_edges)

    # Add pins AFTER all fillets are done (to avoid kernel issues with curved edges)
    fused_shape = fused_shape.fuse(left_pin)
    fused_shape = fused_shape.fuse(right_pin)

    base_obj = doc.addObject("Part::Feature", "Muldenklappe")
    base_obj.Shape = fused_shape
    
    return [base_obj]
