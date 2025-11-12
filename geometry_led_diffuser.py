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
    "DIFFUSER_LAYER_HEIGHT_MM": 0.2,
    "DIFFUSER_BASE_LAYERS": 2,
    "DIFFUSER_GRID_WALL_THICKNESS_MM": 1.0,
    "DIFFUSER_GRID_HEIGHT_MM": 6.0,
    "DIFFUSER_OUTER_WALL_THICKNESS_MM": 1.0,
    "DIFFUSER_OUTER_WALL_EXTRA_HEIGHT_MM": 1.5,  # how much higher than grid
    "DIFFUSER_LED_MATRIX_X": 8,
    "DIFFUSER_LED_MATRIX_Y": 8,
    "DIFFUSER_RESISTOR_HEIGHT_MM": 1.0,
    "DIFFUSER_RESISTOR_WIDTH_MM": 3.0,
    "DIFFUSER_RESISTOR_ORIENTATION": "horizontal",  # options: "horizontal", "vertical", "none"
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
    outer_wall_extra_height = PARAMS["DIFFUSER_OUTER_WALL_EXTRA_HEIGHT_MM"]
    led_matrix_x = PARAMS["DIFFUSER_LED_MATRIX_X"]
    led_matrix_y = PARAMS["DIFFUSER_LED_MATRIX_Y"]
    resistor_height = PARAMS["DIFFUSER_RESISTOR_HEIGHT_MM"]
    resistor_width = PARAMS["DIFFUSER_RESISTOR_WIDTH_MM"]
    resistor_orientation = PARAMS["DIFFUSER_RESISTOR_ORIENTATION"].lower()
    # mounting posts removed
    
    # Calculate dimensions
    base_thickness = max(layer_height * base_layers, 0.01)
    outer_wall_height = grid_height + outer_wall_extra_height
    total_size_x = panel_size_x + 2 * outer_wall_thickness
    total_size_y = panel_size_y + 2 * outer_wall_thickness
    
    # mounting posts removed

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
    
    # Calculate cell dimensions
    cell_width_x = (panel_size_x - (led_matrix_x + 1) * grid_wall_thickness) / led_matrix_x
    cell_width_y = (panel_size_y - (led_matrix_y + 1) * grid_wall_thickness) / led_matrix_y
    
    # Create vertical walls (parallel to Y axis)
    for i in range(led_matrix_x + 1):
        x_pos = outer_wall_thickness + i * (cell_width_x + grid_wall_thickness)
        wall = Part.makeBox(
            grid_wall_thickness,
            panel_size_y,
            grid_height
        )
        wall.translate(App.Vector(x_pos, outer_wall_thickness, base_thickness))
        grid_shapes.append(wall)
    
    # Create horizontal walls (parallel to X axis)
    for j in range(led_matrix_y + 1):
        y_pos = outer_wall_thickness + j * (cell_width_y + grid_wall_thickness)
        wall = Part.makeBox(
            panel_size_x,
            grid_wall_thickness,
            grid_height
        )
        wall.translate(App.Vector(outer_wall_thickness, y_pos, base_thickness))
        grid_shapes.append(wall)
    
    # Fuse all grid shapes together
    grid_shape = grid_shapes[0]
    for s in grid_shapes[1:]:
        grid_shape = grid_shape.fuse(s)
    
    # Cut out resistor slots based on orientation
    resistor_cutouts = []
    
    if resistor_orientation == "horizontal":
        # Cut from horizontal walls (parallel to X axis), excluding first and last
        for j in range(1, led_matrix_y):  # Exclude first (0) and last (led_matrix_y) wall
            y_pos = outer_wall_thickness + j * (cell_width_y + grid_wall_thickness)
            # For each cell in X direction, create a cutout in the middle of the wall
            for i in range(led_matrix_x):
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
        for i in range(1, led_matrix_x):  # Exclude first (0) and last (led_matrix_x) wall
            x_pos = outer_wall_thickness + i * (cell_width_x + grid_wall_thickness)
            # For each cell in Y direction, create a cutout in the middle of the wall
            for j in range(led_matrix_y):
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
    for cutout in resistor_cutouts:
        grid_shape = grid_shape.cut(cutout)
    
    # mounting posts removed

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
    inner_cutout = Part.makeBox(panel_size_x, panel_size_y, outer_wall_height)
    inner_cutout.translate(App.Vector(outer_wall_thickness, outer_wall_thickness, base_thickness))
    
    # Cut out the inner part to create wall
    outer_wall_shape = outer_shell.cut(inner_cutout)
    
    # Add outer wall to document
    outer_wall_obj = doc.addObject("Part::Feature", "OuterWall")
    outer_wall_obj.Label = f"OuterWall"
    outer_wall_obj.Shape = outer_wall_shape
    
    # Set appearance for outer wall (dark gray)
    if hasattr(outer_wall_obj, 'ViewObject') and outer_wall_obj.ViewObject:
        outer_wall_obj.ViewObject.ShapeColor = (0.3, 0.3, 0.3)  # RGB: dark gray
        outer_wall_obj.ViewObject.Transparency = 0

    return [base_obj, grid_obj, outer_wall_obj]