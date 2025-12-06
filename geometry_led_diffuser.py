# geometry_led_diffuser.py
# Parameterized LED diffuser geometry
# Iteration 2: base layer with grid structure for LED compartments
#
# Usage with export script:
#   FreeCADCmd export_to_stl.py geometry_led_diffuser.py diffuser_with_grid.stl
#
# Parameters can be adjusted via environment variables (see DEFAULTS below)
#
# Notes:
# - STL doesn't carry colors; "white" is a print setting.
# - Coordinate system: X=length, Y=width, Z=height.

import os
import Part
import FreeCAD as App

# Default parameters - can be overridden via environment variables with same name
DEFAULTS = {
    "DIFFUSER_PANEL_SIZE_X_MM": 66.0,  # LED panel size (grid is built inside this)
    "DIFFUSER_PANEL_SIZE_Y_MM": 67.0,
    "DIFFUSER_LAYER_HEIGHT_MM": 0.16,
    "DIFFUSER_BASE_LAYERS": 2,
    "DIFFUSER_GRID_WALL_THICKNESS_MM": 1.0,
    "DIFFUSER_GRID_HEIGHT_MM": 6.0,
    "DIFFUSER_OUTER_WALL_THICKNESS_MM": 1.0,
    "DIFFUSER_PCB_THICKNESS_MM": 1.6,
    "DIFFUSER_PCB_CLIP_HEIGHT_MM": 1.0,
    "DIFFUSER_PCB_CLIP_WIDTH_MM": 5.0,
    "DIFFUSER_PCB_CLIP_DEPTH_MM": 0.5,
    "DIFFUSER_PCB_CLIP_COUNT_X": 4,  # Clips on X-parallel sides (top/bottom) - distributed along X axis
    "DIFFUSER_PCB_CLIP_COUNT_Y": 0,  # Clips on Y-parallel sides (left/right) - distributed along Y axis
    "DIFFUSER_LED_MATRIX_X": 8,
    "DIFFUSER_LED_MATRIX_Y": 8,
    "DIFFUSER_MODULES_X": 4,
    "DIFFUSER_MODULES_Y": 1,
    "DIFFUSER_RESISTOR_HEIGHT_MM": 1.0,
    "DIFFUSER_RESISTOR_WIDTH_MM": 3.0,
    "DIFFUSER_RESISTOR_ORIENTATION": "horizontal",  # options: "horizontal", "vertical", "none"
    "DIFFUSER_EYELET_RADIUS_MM": 4.0,
    "DIFFUSER_EYELET_HOLE_RADIUS_MM": 1.6,
    "DIFFUSER_EYELET_HEIGHT_MM": 3.0,
    "DIFFUSER_EYELET_FLAT_OFFSET_MM": 2.0,
    "DIFFUSER_EYELET_COUNT_X": 2,
    "DIFFUSER_EYELET_COUNT_Y": 0,
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
    Create LED diffuser with base plate and grid structure as separate objects.

    Args:
        doc: Active FreeCAD document.

    Returns:
        List of created FreeCAD objects [base, grid, outer_wall].
    """
    # Load parameters
    panel_size_x = PARAMS["DIFFUSER_PANEL_SIZE_X_MM"]
    panel_size_y = PARAMS["DIFFUSER_PANEL_SIZE_Y_MM"]
    layer_height = PARAMS["DIFFUSER_LAYER_HEIGHT_MM"]
    base_layers = PARAMS["DIFFUSER_BASE_LAYERS"]
    grid_wall_thickness = PARAMS["DIFFUSER_GRID_WALL_THICKNESS_MM"]
    grid_height = PARAMS["DIFFUSER_GRID_HEIGHT_MM"]
    outer_wall_thickness = PARAMS["DIFFUSER_OUTER_WALL_THICKNESS_MM"]
    pcb_thickness = PARAMS["DIFFUSER_PCB_THICKNESS_MM"]
    pcb_clip_height = PARAMS["DIFFUSER_PCB_CLIP_HEIGHT_MM"]
    pcb_clip_width = PARAMS["DIFFUSER_PCB_CLIP_WIDTH_MM"]
    pcb_clip_depth = PARAMS["DIFFUSER_PCB_CLIP_DEPTH_MM"]
    pcb_clip_count_x = PARAMS["DIFFUSER_PCB_CLIP_COUNT_X"]
    pcb_clip_count_y = PARAMS["DIFFUSER_PCB_CLIP_COUNT_Y"]
    led_matrix_x = PARAMS["DIFFUSER_LED_MATRIX_X"]
    led_matrix_y = PARAMS["DIFFUSER_LED_MATRIX_Y"]
    modules_x = PARAMS["DIFFUSER_MODULES_X"]
    modules_y = PARAMS["DIFFUSER_MODULES_Y"]
    resistor_height = PARAMS["DIFFUSER_RESISTOR_HEIGHT_MM"]
    resistor_width = PARAMS["DIFFUSER_RESISTOR_WIDTH_MM"]
    resistor_orientation = PARAMS["DIFFUSER_RESISTOR_ORIENTATION"].lower()
    eyelet_radius = PARAMS["DIFFUSER_EYELET_RADIUS_MM"]
    eyelet_hole_radius = PARAMS["DIFFUSER_EYELET_HOLE_RADIUS_MM"]
    eyelet_height = PARAMS["DIFFUSER_EYELET_HEIGHT_MM"]
    eyelet_flat_offset = PARAMS["DIFFUSER_EYELET_FLAT_OFFSET_MM"]
    eyelet_count_x = PARAMS["DIFFUSER_EYELET_COUNT_X"]
    eyelet_count_y = PARAMS["DIFFUSER_EYELET_COUNT_Y"]
    
    # Calculate dimensions
    base_thickness = max(layer_height * base_layers, 0.01)
    outer_wall_height = grid_height + pcb_thickness + pcb_clip_height
    pcb_support_height = grid_height + pcb_thickness  # Height where PCB rests
    
    # Calculate total panel size (multiple modules)
    total_panel_x = modules_x * panel_size_x
    total_panel_y = modules_y * panel_size_y
    total_size_x = total_panel_x + 2 * outer_wall_thickness
    total_size_y = total_panel_y + 2 * outer_wall_thickness
    
    # Calculate total LED counts across all modules
    total_leds_x = led_matrix_x * modules_x
    total_leds_y = led_matrix_y * modules_y

    # Create base plate (diffuser) - larger to accommodate outer wall
    base_shape = Part.makeBox(total_size_x, total_size_y, base_thickness)
    base_obj = doc.addObject("Part::Feature", "Diffuser")
    base_obj.Label = f"Diffuser"
    base_obj.Shape = base_shape
    
    # Set appearance for diffuser (white)
    if hasattr(base_obj, 'ViewObject') and base_obj.ViewObject:
        base_obj.ViewObject.ShapeColor = (1.0, 1.0, 1.0)  # RGB: white
        base_obj.ViewObject.Transparency = 0
    
    # Create grid structure (inside the panel area)
    grid_shapes = []
    
    # Calculate cell dimensions (uniform across all modules)
    cell_width_x = (total_panel_x - (total_leds_x + 1) * grid_wall_thickness) / total_leds_x
    cell_width_y = (total_panel_y - (total_leds_y + 1) * grid_wall_thickness) / total_leds_y
    
    # Create vertical walls (parallel to Y axis)
    for i in range(total_leds_x + 1):
        x_pos = outer_wall_thickness + i * (cell_width_x + grid_wall_thickness)
        wall = Part.makeBox(
            grid_wall_thickness,
            total_panel_y,
            grid_height
        )
        wall.translate(App.Vector(x_pos, outer_wall_thickness, base_thickness))
        grid_shapes.append(wall)
    
    # Create horizontal walls (parallel to X axis)
    for j in range(total_leds_y + 1):
        y_pos = outer_wall_thickness + j * (cell_width_y + grid_wall_thickness)
        wall = Part.makeBox(
            total_panel_x,
            grid_wall_thickness,
            grid_height
        )
        wall.translate(App.Vector(outer_wall_thickness, y_pos, base_thickness))
        grid_shapes.append(wall)
    
    # Fuse all grid shapes together (efficient batch operation)
    grid_shape = grid_shapes[0].multiFuse(grid_shapes[1:])
    
    # Cut out resistor slots based on orientation
    resistor_cutouts = []
    
    if resistor_orientation == "horizontal":
        # Cut from horizontal walls (parallel to X axis), excluding first and last
        for j in range(1, total_leds_y):  # Exclude first (0) and last wall
            # Skip walls at module boundaries
            if j % led_matrix_y == 0:
                continue
            
            y_pos = outer_wall_thickness + j * (cell_width_y + grid_wall_thickness)
            # For each cell in X direction, create a cutout in the middle of the wall
            for i in range(total_leds_x):
                # Calculate center of wall segment between two LEDs
                x_center = outer_wall_thickness + (i + 0.5) * (cell_width_x + grid_wall_thickness) + grid_wall_thickness / 2
                # Create cutout box
                cutout = Part.makeBox(
                    resistor_width,
                    grid_wall_thickness,  # full wall thickness
                    resistor_height
                )
                # Position cutout: centered in X, at wall position in Y, at top of grid
                cutout.translate(App.Vector(
                    x_center - resistor_width / 2,
                    y_pos,
                    base_thickness + grid_height - resistor_height
                ))
                resistor_cutouts.append(cutout)
    
    elif resistor_orientation == "vertical":
        # Cut from vertical walls (parallel to Y axis), excluding first and last
        for i in range(1, total_leds_x):  # Exclude first (0) and last wall
            # Skip walls at module boundaries
            if i % led_matrix_x == 0:
                continue
            
            x_pos = outer_wall_thickness + i * (cell_width_x + grid_wall_thickness)
            # For each cell in Y direction, create a cutout in the middle of the wall
            for j in range(total_leds_y):
                # Calculate center of wall segment between two LEDs
                y_center = outer_wall_thickness + (j + 0.5) * (cell_width_y + grid_wall_thickness) + grid_wall_thickness / 2
                # Create cutout box
                cutout = Part.makeBox(
                    grid_wall_thickness,  # full wall thickness
                    resistor_width,
                    resistor_height
                )
                # Position cutout: at wall position in X, centered in Y, at top of grid
                cutout.translate(App.Vector(
                    x_pos,
                    y_center - resistor_width / 2,
                    base_thickness + grid_height - resistor_height
                ))
                resistor_cutouts.append(cutout)
    
    # else: resistor_orientation == "none" or invalid -> no cutouts
    
    # Cut all resistor slots from the grid
    if resistor_cutouts:
        # Combine all cutouts into one shape, then do single cut operation
        combined_cutouts = resistor_cutouts[0].multiFuse(resistor_cutouts[1:]) if len(resistor_cutouts) > 1 else resistor_cutouts[0]
        grid_shape = grid_shape.cut(combined_cutouts)

    # Add grid to document
    grid_obj = doc.addObject("Part::Feature", "Grid")
    grid_obj.Label = f"Grid"
    grid_obj.Shape = grid_shape
    
    # Set appearance for grid (dark gray)
    if hasattr(grid_obj, 'ViewObject') and grid_obj.ViewObject:
        grid_obj.ViewObject.ShapeColor = (0.3, 0.3, 0.3)  # RGB: dark gray
        grid_obj.ViewObject.Transparency = 0

    # Create outer wall around the panel
    # Outer shell
    outer_shell = Part.makeBox(total_size_x, total_size_y, outer_wall_height)
    outer_shell.translate(App.Vector(0, 0, base_thickness))
    
    # Inner cutout (hollow it out)
    inner_cutout = Part.makeBox(total_panel_x, total_panel_y, outer_wall_height)
    inner_cutout.translate(App.Vector(outer_wall_thickness, outer_wall_thickness, base_thickness))
    
    # Cut out the inner part to create wall
    outer_wall_shape = outer_shell.cut(inner_cutout)
    
    # Create clip slots (vertical cuts from top down to grid height)
    clip_slots = []
    slot_depth = outer_wall_height - grid_height  # From top to top of grid walls
    
    # Slots on Y-parallel sides (left and right)
    if pcb_clip_count_y > 0:
        for side in [0, 1]:  # 0 = left, 1 = right
            x_pos = 0 if side == 0 else total_size_x - outer_wall_thickness
            for i in range(pcb_clip_count_y):
                # Center position of clip i
                clip_center_y = outer_wall_thickness + (i + 0.5) * total_panel_y / pcb_clip_count_y
                
                # Create 2 slots per clip (left and right of clip)
                # Slots are positioned to create a tongue of width pcb_clip_width
                for offset in [-(pcb_clip_width / 2 + grid_wall_thickness / 2), (pcb_clip_width / 2 + grid_wall_thickness / 2)]:
                    slot = Part.makeBox(
                        outer_wall_thickness,
                        grid_wall_thickness,
                        slot_depth
                    )
                    slot.translate(App.Vector(
                        x_pos,
                        clip_center_y + offset - grid_wall_thickness / 2,
                        base_thickness + grid_height
                    ))
                    clip_slots.append(slot)
    
    # Slots on X-parallel sides (top and bottom)
    if pcb_clip_count_x > 0:
        for side in [0, 1]:  # 0 = bottom, 1 = top
            y_pos = 0 if side == 0 else total_size_y - outer_wall_thickness
            for i in range(pcb_clip_count_x):
                # Center position of clip i
                clip_center_x = outer_wall_thickness + (i + 0.5) * total_panel_x / pcb_clip_count_x
                
                # Create 2 slots per clip (left and right of clip)
                # Slots are positioned to create a tongue of width pcb_clip_width
                for offset in [-(pcb_clip_width / 2 + grid_wall_thickness / 2), (pcb_clip_width / 2 + grid_wall_thickness / 2)]:
                    slot = Part.makeBox(
                        grid_wall_thickness,
                        outer_wall_thickness,
                        slot_depth
                    )
                    slot.translate(App.Vector(
                        clip_center_x + offset - grid_wall_thickness / 2,
                        y_pos,
                        base_thickness + grid_height
                    ))
                    clip_slots.append(slot)
    
        # Cut slots from outer wall to create spring tongues
    if clip_slots:
        combined_slots = clip_slots[0].multiFuse(clip_slots[1:]) if len(clip_slots) > 1 else clip_slots[0]
        outer_wall_shape = outer_wall_shape.cut(combined_slots)
    
    # Add wedges to clips (45° ramps pointing inward)
    clip_wedges = []
    wedge_depth = pcb_clip_depth
    # For 45° angle: height = 2 * depth (since we have two slopes: up and down)
    # Position: 50% of lower slope at PCB top, top of triangle at tongue top
    z_pcb_top = base_thickness + grid_height + pcb_thickness
    z_top = base_thickness + outer_wall_height
    # The middle (peak) should be at z_pcb_top
    # From z_base to z_middle is one slope (wedge_depth vertical for 45°)
    # So z_middle = z_base + wedge_depth, therefore z_base = z_pcb_top - wedge_depth
    z_base = z_pcb_top - wedge_depth

    # Wedges on Y-parallel sides (left and right)
    if wedge_depth > 0 and pcb_clip_count_y > 0:
        for side in [0, 1]:  # 0 = left, 1 = right
            x_wall_inner = outer_wall_thickness if side == 0 else outer_wall_thickness + total_panel_x
            for i in range(pcb_clip_count_y):
                clip_center_y = outer_wall_thickness + (i + 0.5) * total_panel_y / pcb_clip_count_y
                y_start = clip_center_y - pcb_clip_width / 2
                z_middle = (z_base + z_top) / 2

                if side == 0:
                    tri = Part.makePolygon([
                        App.Vector(x_wall_inner, 0, z_base),
                        App.Vector(x_wall_inner + wedge_depth, 0, z_middle),
                        App.Vector(x_wall_inner, 0, z_top),
                        App.Vector(x_wall_inner, 0, z_base)
                    ])
                else:
                    tri = Part.makePolygon([
                        App.Vector(x_wall_inner, 0, z_base),
                        App.Vector(x_wall_inner - wedge_depth, 0, z_middle),
                        App.Vector(x_wall_inner, 0, z_top),
                        App.Vector(x_wall_inner, 0, z_base)
                    ])

                tri_face = Part.Face(tri)
                wedge = tri_face.extrude(App.Vector(0, pcb_clip_width, 0))
                wedge.translate(App.Vector(0, y_start, 0))
                clip_wedges.append(wedge)

    # Wedges on X-parallel sides (top and bottom)
    if wedge_depth > 0 and pcb_clip_count_x > 0:
        for side in [0, 1]:  # 0 = bottom, 1 = top
            y_wall_inner = outer_wall_thickness if side == 0 else outer_wall_thickness + total_panel_y
            for i in range(pcb_clip_count_x):
                clip_center_x = outer_wall_thickness + (i + 0.5) * total_panel_x / pcb_clip_count_x
                x_start = clip_center_x - pcb_clip_width / 2
                z_middle = (z_base + z_top) / 2

                if side == 0:
                    tri = Part.makePolygon([
                        App.Vector(0, y_wall_inner, z_base),
                        App.Vector(0, y_wall_inner + wedge_depth, z_middle),
                        App.Vector(0, y_wall_inner, z_top),
                        App.Vector(0, y_wall_inner, z_base)
                    ])
                else:
                    tri = Part.makePolygon([
                        App.Vector(0, y_wall_inner, z_base),
                        App.Vector(0, y_wall_inner - wedge_depth, z_middle),
                        App.Vector(0, y_wall_inner, z_top),
                        App.Vector(0, y_wall_inner, z_base)
                    ])

                tri_face = Part.Face(tri)
                wedge = tri_face.extrude(App.Vector(pcb_clip_width, 0, 0))
                wedge.translate(App.Vector(x_start, 0, 0))
                clip_wedges.append(wedge)

    if clip_wedges:
        combined_wedges = clip_wedges[0].multiFuse(clip_wedges[1:]) if len(clip_wedges) > 1 else clip_wedges[0]
        outer_wall_shape = outer_wall_shape.fuse(combined_wedges)
    
    def build_eyelet_template(height):
        """Create a D-shaped eyelet with its flat face on plane X=0 and centered on Y=0."""
        rect_length = eyelet_radius + eyelet_flat_offset
        rectangle = Part.makeBox(rect_length, 2 * eyelet_radius, height)
        rectangle.translate(App.Vector(0, -eyelet_radius, 0))

        circle = Part.makeCylinder(eyelet_radius, height)
        circle.translate(App.Vector(rect_length, 0, 0))

        shape = rectangle.fuse(circle)

        hole = Part.makeCylinder(eyelet_hole_radius, height)
        hole.translate(App.Vector(rect_length, 0, 0))

        return shape.cut(hole)

    eyelet_template = None
    eyelet_instances = []

    if eyelet_radius > 0 and eyelet_hole_radius > 0 and eyelet_hole_radius < eyelet_radius and eyelet_height > 0:
        eyelet_template = build_eyelet_template(eyelet_height)
        eyelet_top_z = base_thickness + outer_wall_height
        eyelet_bottom_z = eyelet_top_z - eyelet_height

        def distribute_eyelets(count, is_x_axis):
            if count <= 0:
                return []
            span = total_panel_x if is_x_axis else total_panel_y
            positions = [
                outer_wall_thickness + (i + 0.5) * span / count
                for i in range(count)
            ]
            return positions

        # Eyelets on left/right (Y sides)
        positions_y = distribute_eyelets(eyelet_count_y, is_x_axis=False)
        for side in ["left", "right"]:
            if not positions_y:
                break
            rotation = 180 if side == "left" else 0
            attach_x = 0 if side == "left" else total_size_x
            for center_y in positions_y:
                eyelet = eyelet_template.copy()
                if rotation != 0:
                    eyelet.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), rotation)
                eyelet.translate(App.Vector(attach_x, center_y, eyelet_bottom_z))
                eyelet_instances.append(eyelet)

        # Eyelets on top/bottom (X sides)
        positions_x = distribute_eyelets(eyelet_count_x, is_x_axis=True)
        for side in ["bottom", "top"]:
            if not positions_x:
                break
            rotation = -90 if side == "bottom" else 90
            attach_y = 0 if side == "bottom" else total_size_y
            for center_x in positions_x:
                eyelet = eyelet_template.copy()
                eyelet.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), rotation)
                eyelet.translate(App.Vector(center_x, attach_y, eyelet_bottom_z))
                eyelet_instances.append(eyelet)

        if eyelet_instances:
            combined_eyelets = eyelet_instances[0]
            if len(eyelet_instances) > 1:
                combined_eyelets = combined_eyelets.multiFuse(eyelet_instances[1:])
            outer_wall_shape = outer_wall_shape.fuse(combined_eyelets)

    # Add outer wall to document
    outer_wall_obj = doc.addObject("Part::Feature", "OuterWall")
    outer_wall_obj.Label = f"OuterWall"
    outer_wall_obj.Shape = outer_wall_shape
    
    # Set appearance for outer wall (dark gray)
    if hasattr(outer_wall_obj, 'ViewObject') and outer_wall_obj.ViewObject:
        outer_wall_obj.ViewObject.ShapeColor = (0.3, 0.3, 0.3)  # RGB: dark gray
        outer_wall_obj.ViewObject.Transparency = 0

    return [base_obj, grid_obj, outer_wall_obj]