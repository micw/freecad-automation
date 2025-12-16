import os
import Part
import FreeCAD as App
import math

DEFAULTS = {
    "HEX_FLAT_TO_FLAT_MM": 59.6,   # Abstand gegenüberliegende Seiten
    "THICKNESS_MM": 2.0,           # Dicke der Platte
    "ARM_WIDTH_MM": 10.0,          # Breite der Arme
    "OVERHANG_MM": 2.0,            # Überstand über die Kante
    "LEG_HEIGHT_MM": 10.0,         # Länge der Beine nach unten
    "HOOK_HEIGHT_MM": 2.0,         # Höhe der Rastnase
    "HOOK_DEPTH_MM": 2.0,          # Tiefe der Rastnase (nach innen)
    "CONSOLE_HEIGHT_MM": 2.0,      # Höhe der oberen Konsole
    "CONSOLE_DEPTH_MM": 4.0,       # Tiefe der oberen Konsole
    "HOOK_CONSOLE_GAP_MM": 9.0,    # Abstand zwischen Rastnase und Konsole
    "CONE_BASE_DIA_MM": 10.0,      # Durchmesser Kegelbasis
    "CONE_TOP_DIA_MM": 5.0,        # Durchmesser Kegelspitze
    "CONE_HEIGHT_MM": 3.0,         # Höhe des Kegels
    "CONE_EXTENSION_MM": 10.0,     # Verlängerung des Kegels (Zylinder)
    "ENABLE_CONSOLE": 0,           # Konsole aktivieren (0=Nein, 1=Ja)
    "CORNER_CHAMFER_MM": 2.5,      # Größe der Fase am Knick (Außen und Innen)
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

def create_geometry(doc):
    """
    Erstellt einen 3-Arm Clip für ein Sechseck.
    """
    hex_width = PARAMS["HEX_FLAT_TO_FLAT_MM"]
    thickness = PARAMS["THICKNESS_MM"]
    arm_width = PARAMS["ARM_WIDTH_MM"]
    overhang = PARAMS["OVERHANG_MM"]
    leg_height = PARAMS["LEG_HEIGHT_MM"]
    hook_height = PARAMS["HOOK_HEIGHT_MM"]
    hook_depth = PARAMS["HOOK_DEPTH_MM"]
    console_height = PARAMS["CONSOLE_HEIGHT_MM"]
    console_depth = PARAMS["CONSOLE_DEPTH_MM"]
    gap = PARAMS["HOOK_CONSOLE_GAP_MM"]
    cone_r1 = PARAMS["CONE_BASE_DIA_MM"] / 2.0
    cone_r2 = PARAMS["CONE_TOP_DIA_MM"] / 2.0
    cone_h = PARAMS["CONE_HEIGHT_MM"]
    chamfer_size = PARAMS["CORNER_CHAMFER_MM"]
    
    # Abstand vom Zentrum zur Fläche
    dist_to_flat = hex_width / 2.0
    
    # Basis-Objekt für Fuse
    base = None
    
    # Wir erstellen 3 Arme im Winkel von 120 Grad
    # Winkel: 0, 120, 240 (entspricht 3 Seiten des Sechsecks, wenn eine Seite rechts ist)
    for angle in [0, 120, 240]:
        # Arm erstellen (Box)
        # Länge reicht vom Zentrum bis etwas über die Kante
        arm_len = dist_to_flat + overhang
        
        # Box erstellen: Länge x Breite x Höhe
        # Wir positionieren sie so, dass sie vom Zentrum nach außen zeigt
        arm = Part.makeBox(arm_len, arm_width, thickness)
        
        # Zentrieren in Y (Breite) und Z (Höhe ist egal, da Box bei 0 startet)
        # Verschieben, damit sie im Zentrum startet (oder leicht überlappt)
        # Wir schieben sie in X um 0, in Y um -arm_width/2
        arm.translate(App.Vector(0, -arm_width/2, 0))
        
        # Bein nach unten (Rechteck)
        # Maße: Dicke (radial) x Breite (tangential) x Höhe
        leg = Part.makeBox(thickness, arm_width, leg_height)
        
        # Positionieren:
        # X: Startet bei dist_to_flat (Innenseite am Sechseck)
        # Y: Zentriert wie der Arm
        # Z: Geht von 0 nach unten (-leg_height)
        leg.translate(App.Vector(dist_to_flat, -arm_width/2, -leg_height))
        
        # Rastnase (Dreieck)
        # Wir erstellen ein Prisma mit dreieckigem Querschnitt
        # Punkte im X-Z-Schnitt (lokal zum Bein)
        # P1: Unten am Bein (Innenseite)
        # P2: hook_height weiter oben am Bein (Innenseite)
        # P3: hook_height/2 oben, hook_depth nach innen (Spitze)
        
        p1 = App.Vector(dist_to_flat, 0, -leg_height)
        p2 = App.Vector(dist_to_flat, 0, -leg_height + hook_height)
        p3 = App.Vector(dist_to_flat - hook_depth, 0, -leg_height + (hook_height / 2.0))
        
        # Polygon erstellen
        # Wir bauen das Dreieck als Face und extrudieren es.
        wire = Part.makePolygon([p1, p2, p3, p1])
        face = Part.Face(wire)
        hook = face.extrude(App.Vector(0, arm_width, 0))
        
        # Das Hook-Prisma startet bei Y=0. Wir müssen es auf Y = -arm_width/2 schieben
        hook.translate(App.Vector(0, -arm_width/2, 0))
        
        # Konsole (Rechtwinkliges Dreieck weiter oben)
        if PARAMS["ENABLE_CONSOLE"]:
            # Z-Position berechnen
            # Hook geht von -leg_height bis -leg_height + hook_height
            z_hook_top = -leg_height + hook_height
            z_console_bottom = z_hook_top + gap
            
            # Punkte für Konsole
            # c1: Wall, Bottom (Innenseite am Bein)
            # c2: Tip, Bottom (nach innen ragend)
            # c3: Wall, Top (Innenseite am Bein)
            
            c1 = App.Vector(dist_to_flat, 0, z_console_bottom)
            c2 = App.Vector(dist_to_flat - console_depth, 0, z_console_bottom)
            c3 = App.Vector(dist_to_flat, 0, z_console_bottom + console_height)
            
            wire_console = Part.makePolygon([c1, c2, c3, c1])
            face_console = Part.Face(wire_console)
            console = face_console.extrude(App.Vector(0, arm_width, 0))
            console.translate(App.Vector(0, -arm_width/2, 0))
            
            # Arm, Bein, Haken und Konsole verbinden
            full_arm = arm.fuse(leg).fuse(hook).fuse(console)
        else:
            # Arm, Bein und Haken verbinden
            full_arm = arm.fuse(leg).fuse(hook)
            
        # Fase am Knick (Außen und Innen)
        if chamfer_size > 0:
            # Außen: Cut
            # Ecke: X = dist_to_flat + thickness, Z = thickness
            # Wir gehen davon aus, dass overhang >= thickness ist, sonst ist die Ecke woanders.
            # Aber hier nehmen wir die theoretische Ecke des L-Profils.
            # Da arm_len = dist_to_flat + overhang.
            # Wenn overhang < thickness, ist die Ecke bei dist_to_flat + overhang.
            # Wir nehmen das Minimum.
            corner_x = dist_to_flat + min(overhang, thickness)
            # Eigentlich ist die Außenkante des Beins bei dist_to_flat + thickness.
            # Wenn der Arm kürzer ist, gibt es keine Ecke dort.
            # Wir nehmen an overhang >= thickness (2.0 >= 2.0).
            corner_x = dist_to_flat + thickness
            corner_z = thickness
            
            p_out_1 = App.Vector(corner_x, 0, corner_z)
            p_out_2 = App.Vector(corner_x - chamfer_size, 0, corner_z)
            p_out_3 = App.Vector(corner_x, 0, corner_z - chamfer_size)
            
            wire_cut = Part.makePolygon([p_out_1, p_out_2, p_out_3, p_out_1])
            face_cut = Part.Face(wire_cut)
            cut_prism = face_cut.extrude(App.Vector(0, arm_width, 0))
            cut_prism.translate(App.Vector(0, -arm_width/2, 0))
            
            full_arm = full_arm.cut(cut_prism)
            
            # Innen: Fuse (Gusset)
            # Ecke: X = dist_to_flat, Z = 0
            p_in_1 = App.Vector(dist_to_flat, 0, 0)
            p_in_2 = App.Vector(dist_to_flat - chamfer_size, 0, 0)
            p_in_3 = App.Vector(dist_to_flat, 0, -chamfer_size)
            
            wire_add = Part.makePolygon([p_in_1, p_in_2, p_in_3, p_in_1])
            face_add = Part.Face(wire_add)
            add_prism = face_add.extrude(App.Vector(0, arm_width, 0))
            add_prism.translate(App.Vector(0, -arm_width/2, 0))
            
            full_arm = full_arm.fuse(add_prism)
        
        # Rotieren um Z-Achse
        full_arm.rotate(App.Vector(0,0,0), App.Vector(0,0,1), angle)
        
        if base is None:
            base = full_arm
        else:
            base = base.fuse(full_arm)
            
    # Optional: Zentrum füllen, damit die Arme verbunden sind
    # Ein kleiner Zylinder oder Sechseck im Zentrum
    center_radius = arm_width 
    center = Part.makeCylinder(center_radius, thickness)
    base = base.fuse(center)
    
    # Zentrierkegel mit Verlängerung (nach unten)
    ext_h = PARAMS["CONE_EXTENSION_MM"]
    
    # 1. Zylinder (Verlängerung an der Basis)
    if ext_h > 0:
        # Zylinder mit Basis-Radius
        cyl = Part.makeCylinder(cone_r1, ext_h)
        # Verschieben nach unten (von 0 bis -ext_h)
        cyl.translate(App.Vector(0, 0, -ext_h))
        base = base.fuse(cyl)
        
    # 2. Kegel (an der Spitze des Zylinders bzw. bei 0 wenn keine Verlängerung)
    # makeCone(r1, r2, height) -> Z=0 to Z=height
    # Wir wollen ihn umdrehen und ggf. nach unten schieben
    cone = Part.makeCone(cone_r1, cone_r2, cone_h)
    cone.rotate(App.Vector(0,0,0), App.Vector(1,0,0), 180)
    # Jetzt ist er von 0 bis -cone_h
    # Wir schieben ihn um ext_h nach unten
    cone.translate(App.Vector(0, 0, -ext_h))
    
    base = base.fuse(cone)

    # Objekt erstellen
    obj = doc.addObject("Part::Feature", "GravitraxLiftClip")
    obj.Shape = base
    
    return [obj]
