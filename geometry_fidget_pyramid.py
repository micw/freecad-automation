# geometry_fidget_pyramid.py
# Parameterized hexagonal geometry with V-profile walls
#
# Usage with export script:
#   FreeCADCmd export_to_stl.py geometry_fidget_pyramid.py fidget_pyramid.stl
#
# Parameters can be adjusted via environment variables (see DEFAULTS below)
#
# Notes:
# - Creates a hexagonal shape with V-profile walls (< shape in vertical section)
# - The wall tapers from top and bottom to a sharp edge at mid-height
# - Coordinate system: X=length, Y=width, Z=height.

import os
import math
import Part
import FreeCAD as App

# Default parameters - can be overridden via environment variables with same name
DEFAULTS = {
    "PYRAMID_HEIGHT_MM": 10.0,                      # Height of the pyramid
    "PYRAMID_WALL_THICKNESS_MM": 1.0,               # Wall thickness
    "PYRAMID_DIAMETER_MM": 15.0,                    # Diameter (flat to flat) of hexagon base (innermost ring)
    "PYRAMID_MAX_OVERHANG_ANGLE_DEG": 45.0,         # Maximum overhang angle for 3D printing (0-90°)
    "PYRAMID_NUM_RINGS": 7,                         # Number of concentric rings
    "PYRAMID_MIN_AXIAL_OVERLAP_MM": 1.0,            # Minimum axial overlap to prevent rings from sliding out (determines ring spacing)
    "PYRAMID_ADD_HANDLE": True,                     # Add a handle to the innermost ring
    "PYRAMID_HANDLE_SHAFT_HEIGHT_MM": 20.0,         # Height of the handle shaft (cylinder)
    "PYRAMID_HANDLE_SHAFT_DIAMETER_MM": 3.0,        # Diameter of the handle shaft (cylinder)
    "PYRAMID_HANDLE_BALL_DIAMETER_MM": 5.0,         # Diameter of the ball at the top of the handle
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
    Create hexagonal shapes with V-profile walls (< shape in vertical section).
    The wall tapers from top and bottom to a sharp edge at mid-height.
    Multiple concentric rings can be created.

    Args:
        doc: Active FreeCAD document.

    Returns:
        List of created FreeCAD objects.
    """
    # Load parameters
    height = PARAMS["PYRAMID_HEIGHT_MM"]
    wall_thickness = PARAMS["PYRAMID_WALL_THICKNESS_MM"]
    diameter = PARAMS["PYRAMID_DIAMETER_MM"]
    max_overhang_angle = PARAMS["PYRAMID_MAX_OVERHANG_ANGLE_DEG"]
    num_rings = PARAMS["PYRAMID_NUM_RINGS"]
    min_axial_overlap = PARAMS["PYRAMID_MIN_AXIAL_OVERLAP_MM"]
    add_handle = PARAMS["PYRAMID_ADD_HANDLE"]
    handle_shaft_height = PARAMS["PYRAMID_HANDLE_SHAFT_HEIGHT_MM"]
    handle_shaft_diameter = PARAMS["PYRAMID_HANDLE_SHAFT_DIAMETER_MM"]
    handle_ball_diameter = PARAMS["PYRAMID_HANDLE_BALL_DIAMETER_MM"]
    
    # Mid height is always at half the total height
    mid_height = height / 2.0
    
    # Calculate radial expansion based on max overhang angle
    radial_expansion = mid_height * math.tan(math.radians(max_overhang_angle))
    
    # Constants for rotation lock calculation
    radial_clearance = 0.2  # mm additional clearance for printability
    rotation_lock_margin = 0.5  # mm additional margin to ensure rotation is actually blocked
    wall_thickness_correction = wall_thickness / math.cos(math.radians(30))
    
    # Helper function to calculate required overlap for rotation lock for a given ring
    def calculate_required_overlap_for_ring(outer_radius_mid):
        """
        Calculate the minimum axial overlap needed for rotation lock for a specific ring.
        
        Args:
            outer_radius_mid: The outer radius of the ring at mid-height
            
        Returns:
            Required axial overlap in mm
        """
        # When rotated 30°, corner reaches: outer_radius_mid / cos(30°)
        corner_radius_rotated = outer_radius_mid / math.cos(math.radians(30))
        
        # For rotation lock: next_inner_wall_mid <= corner_radius_rotated
        # Solving for axial_overlap:
        # axial_overlap >= outer_radius_mid + radial_expansion + radial_clearance + rotation_lock_margin - corner_radius_rotated
        required_overlap = outer_radius_mid + radial_expansion + radial_clearance + rotation_lock_margin - corner_radius_rotated
        
        return required_overlap

    
    # Helper function to create a hexagon wire at given radius and z height
    def make_hexagon_wire(radius, z):
        """Helper function to create a hexagon wire at given radius and z height."""
        points = []
        for i in range(6):
            angle = math.radians(60 * i)
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            points.append(App.Vector(x, y, z))
        points.append(points[0])  # Close polygon
        return Part.makePolygon(points)
    
    # Helper function to create a V-profile solid from three hexagon wires
    def make_v_profile_solid(bottom_radius, mid_radius, top_radius, bottom_z, mid_z, top_z):
        """
        Create a V-profile solid by lofting three hexagonal wires.
        The profile tapers from bottom and top to a sharp edge at mid-height.
        
        Args:
            bottom_radius: Hexagon radius at bottom
            mid_radius: Hexagon radius at mid height (widest point)
            top_radius: Hexagon radius at top
            bottom_z: Z-coordinate of bottom
            mid_z: Z-coordinate of mid height
            top_z: Z-coordinate of top
            
        Returns:
            Part.Shape: The V-profile solid
        """
        bottom_wire = make_hexagon_wire(bottom_radius, bottom_z)
        mid_wire = make_hexagon_wire(mid_radius, mid_z)
        top_wire = make_hexagon_wire(top_radius, top_z)
        
        # Create solid in two halves for sharp edge at mid
        bottom_half = Part.makeLoft([bottom_wire, mid_wire], True, False, False)
        top_half = Part.makeLoft([mid_wire, top_wire], True, False, False)
        
        return bottom_half.fuse(top_half)
    
    # Helper function to create one ring
    def create_ring(inner_radius_bottom, ring_index):
        """Create a single ring with V-profile."""
        # Calculate radii for this ring
        outer_radius_mid = inner_radius_bottom + radial_expansion
        
        # Calculate wall thickness correction for hexagon geometry
        wall_thickness_correction = wall_thickness / math.cos(math.radians(30))
        
        # Create outer solid using helper function
        outer_solid = make_v_profile_solid(
            inner_radius_bottom, outer_radius_mid, inner_radius_bottom,
            0, mid_height, height
        )
        
        # Calculate inner radii (offset inward by wall_thickness parameter)
        inner_inner_radius = inner_radius_bottom - wall_thickness_correction
        inner_outer_radius = outer_radius_mid - wall_thickness_correction
        
        # Create inner void using helper function
        inner_void = make_v_profile_solid(
            inner_inner_radius, inner_outer_radius, inner_inner_radius,
            0, mid_height, height
        )
        
        # Cut out the inner void to create hollow shape
        ring_shape = outer_solid.cut(inner_void)
        
        # Calculate info for this ring
        actual_wall_thickness = radial_expansion * math.cos(math.radians(30))
        outer_radius_bottom = inner_radius_bottom
        
        print(f"Ring {ring_index + 1}: inner_radius={inner_radius_bottom:.2f}mm, outer_radius_mid={outer_radius_mid:.2f}mm, wall_thickness_mid={actual_wall_thickness:.2f}mm")
        
        return ring_shape, outer_radius_mid
    
    # Create all rings
    created_objects = []
    
    # Start with the initial diameter (innermost ring)
    current_inner_radius = diameter / math.sqrt(3)
    
    for i in range(num_rings):
        ring_shape, outer_radius_mid = create_ring(current_inner_radius, i)
        
        # Add ring to document
        ring_obj = doc.addObject("Part::Feature", f"Ring{i + 1}")
        ring_obj.Label = f"Ring{i + 1}"
        ring_obj.Shape = ring_shape
        
        # Set appearance with different colors for each ring
        if hasattr(ring_obj, 'ViewObject') and ring_obj.ViewObject:
            # Cycle through colors
            colors = [
                (0.5, 0.8, 1.0),  # light blue
                (1.0, 0.7, 0.5),  # orange
                (0.5, 1.0, 0.5),  # light green
                (1.0, 0.5, 0.8),  # pink
                (0.8, 0.5, 1.0),  # purple
            ]
            ring_obj.ViewObject.ShapeColor = colors[i % len(colors)]
            ring_obj.ViewObject.Transparency = 0
        
        created_objects.append(ring_obj)
        
        # Calculate the required overlap for this specific ring (for next ring positioning)
        # We need to consider two constraints:
        # 1. Rotation lock: corners of inner ring must hit outer ring wall at 30° rotation
        # 2. Lateral shift: when inner ring shifts sideways, we must still have min_axial_overlap
        
        # First, calculate what's needed for rotation lock
        required_overlap_for_rotation_lock = calculate_required_overlap_for_ring(outer_radius_mid)
        
        # For lateral shift constraint, we need to solve:
        # ring_axial_overlap = max_lateral_shift + min_axial_overlap
        # where max_lateral_shift = radial_expansion - ring_axial_overlap
        # Solving: ring_axial_overlap = (radial_expansion + min_axial_overlap) / 2
        required_overlap_for_lateral_shift = (radial_expansion + min_axial_overlap) / 2
        
        # Use the larger of the two requirements
        ring_axial_overlap = max(required_overlap_for_rotation_lock, required_overlap_for_lateral_shift)
        
        # Calculate final next ring position based on chosen overlap
        next_inner_radius_bottom = outer_radius_mid - ring_axial_overlap + wall_thickness_correction
        
        # Calculate final values for verification
        next_outer_radius_mid = next_inner_radius_bottom + radial_expansion
        next_inner_wall_mid = next_outer_radius_mid - wall_thickness_correction
        
        # Rotational clearance for verification
        corner_radius_rotated = outer_radius_mid / math.cos(math.radians(30))
        rotational_clearance = next_inner_wall_mid - corner_radius_rotated
        
        # Lateral shift clearance for verification
        actual_max_lateral_shift = next_inner_wall_mid - outer_radius_mid
        remaining_overlap_after_shift = ring_axial_overlap - actual_max_lateral_shift
        
        if i < num_rings - 1:  # Only report if there's a next ring
            print(f"  Ring-specific axial overlap: {ring_axial_overlap:.2f}mm")
            print(f"    Required for rotation lock: {required_overlap_for_rotation_lock:.2f}mm")
            print(f"    Required for lateral shift: {required_overlap_for_lateral_shift:.2f}mm")
            print(f"  Rotational clearance: {rotational_clearance:.2f}mm (should be < 0 for lock!)")
            print(f"  Max lateral shift: {actual_max_lateral_shift:.2f}mm, remaining overlap after shift: {remaining_overlap_after_shift:.2f}mm (should be >= {min_axial_overlap:.2f}mm)")

            if rotational_clearance >= 0:
                print(f"  WARNING: Rotation lock NOT engaged! Clearance is positive, rings can rotate freely!")
        
        current_inner_radius = next_inner_radius_bottom
    
    # Add handle to innermost ring if requested
    if add_handle:
        # Get the first ring's parameters
        first_inner_radius = diameter / math.sqrt(3)
        first_outer_radius_mid = first_inner_radius + radial_expansion
        wall_thickness_correction = wall_thickness / math.cos(math.radians(30))
        first_inner_wall_radius_bottom = first_inner_radius - wall_thickness_correction
        first_inner_wall_radius_mid = first_outer_radius_mid - wall_thickness_correction
        
        # The walls form a V-shape that continues upward with same angle and wall thickness
        # The walls taper inward at the same rate: radial_expansion over mid_height
        # Starting from the top of the ring at z=height
        
        # Outer pyramid: continues from outer surface of ring top
        # At z=height: outer radius = first_inner_radius (top of ring)
        # Walls taper inward at same angle until they meet at center
        outer_cone_height = (first_inner_radius * mid_height) / radial_expansion
        outer_cone_top_z = height + outer_cone_height
        
        # Create outer pyramid (solid)
        outer_bottom_wire = make_hexagon_wire(first_inner_radius, height)
        outer_top_wire = Part.Wire(Part.makeCircle(0.01, App.Vector(0, 0, outer_cone_top_z)))
        outer_pyramid_shape = Part.makeLoft([outer_bottom_wire, outer_top_wire], True, False, False)
        
        # Inner pyramid: continues from inner surface of ring top
        # At z=height: inner radius = first_inner_wall_radius_bottom
        # Walls taper inward at same angle (parallel to outer walls)
        inner_cone_height = (first_inner_wall_radius_bottom * mid_height) / radial_expansion
        inner_cone_top_z = height + inner_cone_height
        
        # Create inner pyramid (void)
        inner_bottom_wire = make_hexagon_wire(first_inner_wall_radius_bottom, height)
        inner_top_wire = Part.Wire(Part.makeCircle(0.01, App.Vector(0, 0, inner_cone_top_z)))
        inner_pyramid_shape = Part.makeLoft([inner_bottom_wire, inner_top_wire], True, False, False)
        
        # Create hollow pyramid by cutting inner from outer
        pyramid_shape = outer_pyramid_shape.cut(inner_pyramid_shape)
        
        # Create shaft (cylinder) - minimal penetration into pyramid for stability
        shaft_radius = handle_shaft_diameter / 2
        
        # Minimal penetration: just enough for stability (1-2mm) to minimize support needs
        shaft_penetration = 1.5  # mm - small enough to minimize support, large enough for stability
        
        # Shaft starts slightly below the inner cone top
        shaft_start_z = inner_cone_top_z - shaft_penetration
        shaft_total_length = handle_shaft_height + shaft_penetration
        shaft_end_z = shaft_start_z + shaft_total_length
        shaft_shape = Part.makeCylinder(shaft_radius, shaft_total_length, App.Vector(0, 0, shaft_start_z))
        
        # Create ball at top - center at shaft_end_z so ball sits on cylinder
        ball_radius = handle_ball_diameter / 2
        ball_center = App.Vector(0, 0, shaft_end_z)
        ball_shape = Part.makeSphere(ball_radius, ball_center)
        
        # Combine all handle parts
        handle_shape = pyramid_shape.fuse(shaft_shape).fuse(ball_shape)
        
        # Add handle to document
        handle_obj = doc.addObject("Part::Feature", "Handle")
        handle_obj.Label = "Handle"
        handle_obj.Shape = handle_shape
        
        # Set appearance (same color as first ring)
        if hasattr(handle_obj, 'ViewObject') and handle_obj.ViewObject:
            handle_obj.ViewObject.ShapeColor = (0.5, 0.8, 1.0)  # light blue
            handle_obj.ViewObject.Transparency = 0
        
        created_objects.append(handle_obj)
        print(f"Added handle: outer_pyramid_height={outer_cone_height:.2f}mm, inner_pyramid_height={inner_cone_height:.2f}mm, shaft_diameter={handle_shaft_diameter:.2f}mm, shaft_height={handle_shaft_height:.2f}mm, ball_diameter={handle_ball_diameter:.2f}mm")
    
    print(f"Created {num_rings} ring(s), overhang angle={max_overhang_angle:.1f}°")
    
    return created_objects
