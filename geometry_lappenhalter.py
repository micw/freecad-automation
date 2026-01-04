# geometry_lappenhalter.py
import os
import Part
import FreeCAD as App

DEFAULTS = {
    "PIPE_DIAMETER_MM": 26.3,       # Rohrdurchmesser des Wasserhahns
    "WALL_THICKNESS_MM": 3.0,       # Wandstärke des Halters
    "HEIGHT_MM": 35.0,              # Höhe des Zylinders
    "TOLERANCE_MM": 0.3,            # Toleranz für Snap-Passung
    "SNAP_OPENING_MM": 24.0,        # Öffnungsbreite in mm (etwas kleiner als Rohrdurchmesser)
    "CHAMFER_MM": 1.0,              # Fase an den Außenkanten
    "BAR_WIDTH_MM": 5.0,            # Breite der Stange (X)
    "BAR_HEIGHT_MM": 10.0,          # Höhe der Stange (Z)
    "BAR_LENGTH_MM": 120.0,         # Länge der Stange (-Y)
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

import math

def create_geometry(doc):
    """Erzeugt einen Lappenhalter zum Aufsnappen auf einen Wasserhahn."""
    
    pipe_diameter = PARAMS["PIPE_DIAMETER_MM"]
    wall_thickness = PARAMS["WALL_THICKNESS_MM"]
    height = PARAMS["HEIGHT_MM"]
    tolerance = PARAMS["TOLERANCE_MM"]
    snap_opening_mm = PARAMS["SNAP_OPENING_MM"]
    
    # Innendurchmesser = Rohrdurchmesser + Toleranz
    inner_radius = (pipe_diameter + tolerance) / 2
    # Außendurchmesser = Innendurchmesser + Wandstärke
    outer_radius = inner_radius + wall_thickness
    
    # Öffnungswinkel berechnen aus Öffnungsbreite am Innenradius
    # Bogenlänge = Winkel * Radius -> Winkel = Bogenlänge / Radius
    # Öffnung basiert auf Innendurchmesser (wo das Rohr durchmuss)
    opening_angle_rad = snap_opening_mm / inner_radius
    opening_angle_deg = math.degrees(opening_angle_rad)
    
    # Äußerer Zylinder
    outer_cylinder = Part.makeCylinder(outer_radius, height)
    
    # Innerer Zylinder zum Ausschneiden (für das Rohr)
    inner_cylinder = Part.makeCylinder(inner_radius, height)
    
    # Ausschneiden des inneren Zylinders
    ring = outer_cylinder.cut(inner_cylinder)
    
    # Snap-Öffnung: Keilförmig vom Mittelpunkt ausgehend
    # Winkel von -opening_angle/2 bis +opening_angle/2, zentriert bei +Y (90°)
    half_angle = opening_angle_deg / 2
    start_angle = 90 - half_angle  # Startwinkel
    
    # Zwei radiale Schnittlinien als dünne Boxen vom Zentrum nach außen
    cut_length = outer_radius + 1
    cut_width = 0.1  # Sehr dünn
    
    # Erste Schnittlinie
    cut1 = Part.makeBox(cut_length, cut_width, height)
    cut1.translate(App.Vector(0, -cut_width / 2, 0))
    cut1.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), start_angle)
    
    # Zweite Schnittlinie
    end_angle = 90 + half_angle
    cut2 = Part.makeBox(cut_length, cut_width, height)
    cut2.translate(App.Vector(0, -cut_width / 2, 0))
    cut2.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), end_angle)
    
    # Keilförmigen Bereich ausschneiden (Zylindersegment)
    # Erzeuge einen Vollzylinder und schneide das Segment heraus
    wedge_cylinder = Part.makeCylinder(
        outer_radius + 1,  # Etwas größer als Außenradius
        height,
        App.Vector(0, 0, 0),
        App.Vector(0, 0, 1),
        opening_angle_deg
    )
    # Rotieren, sodass die Öffnung bei +Y zentriert ist
    wedge_cylinder.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), start_angle)
    
    # Öffnung ausschneiden
    ring = ring.cut(wedge_cylinder)
    
    # Fasen an den Außenkanten (oben und unten am Außenradius)
    chamfer_size = PARAMS["CHAMFER_MM"]
    
    # Finde die kreisförmigen Kanten (Außen- und Cutout-Kanten)
    edges_to_chamfer = []
    for edge in ring.Edges:
        # Prüfe ob es ein Kreisbogen ist
        if hasattr(edge.Curve, 'Radius'):
            # Außenkante (Außenradius) oder Cutout-Kante (Öffnung am Außenradius)
            if abs(edge.Curve.Radius - outer_radius) < 0.01:
                edges_to_chamfer.append(edge)
    
    # Finde auch die geraden Kanten am Cutout (die radialen Schnittkanten)
    for edge in ring.Edges:
        if "Line" in edge.Curve.TypeId:
            # Gerade Kanten, die auf der Oberseite (Z=height) oder Unterseite (Z=0) liegen
            z_coords = [v.Point.z for v in edge.Vertexes]
            if all(abs(z - height) < 0.01 for z in z_coords) or all(abs(z) < 0.01 for z in z_coords):
                edges_to_chamfer.append(edge)
    
    if edges_to_chamfer:
        ring = ring.makeChamfer(chamfer_size, edges_to_chamfer)
    
    # Zweiter Durchgang: Fasen an den senkrechten Kanten des Cutouts
    vertical_edges = []
    for edge in ring.Edges:
        if "Line" in edge.Curve.TypeId:
            # Senkrechte Kanten: Z-Koordinaten sind unterschiedlich, X/Y bleiben gleich
            v0, v1 = edge.Vertexes[0].Point, edge.Vertexes[1].Point
            if abs(v0.x - v1.x) < 0.01 and abs(v0.y - v1.y) < 0.01:
                # Das ist eine senkrechte Kante
                # Prüfe ob sie am Außenrand liegt (nicht am Innenradius)
                radius = math.sqrt(v0.x**2 + v0.y**2)
                if radius > inner_radius + 0.01:
                    vertical_edges.append(edge)
    
    if vertical_edges:
        ring = ring.makeChamfer(chamfer_size, vertical_edges)
    
    # Stange (Quader) gegenüber vom Cutout (Richtung -Y)
    bar_width = PARAMS["BAR_WIDTH_MM"]
    bar_height = PARAMS["BAR_HEIGHT_MM"]
    bar_length = PARAMS["BAR_LENGTH_MM"]
    
    # Stange erstellen (noch nicht positioniert)
    bar = Part.makeBox(bar_width, bar_length, bar_height)
    
    # Dreieck als Runterfall-Schutz am äußeren Ende der Stange
    # Höhe 5mm, 45° Winkel -> Tiefe auch 5mm
    stopper_height = 5.0
    stopper_depth = stopper_height  # 45° -> gleiche Tiefe wie Höhe
    
    # Dreieck-Profil erstellen (in Y-Z Ebene)
    p1 = App.Vector(0, 0, 0)                          # unten vorne
    p2 = App.Vector(0, -stopper_depth, 0)             # unten hinten  
    p3 = App.Vector(0, -stopper_depth, stopper_height) # oben hinten
    
    # Dreieck als Wire erstellen
    edge1 = Part.makeLine(p1, p2)
    edge2 = Part.makeLine(p2, p3)
    edge3 = Part.makeLine(p3, p1)
    wire = Part.Wire([edge1, edge2, edge3])
    face = Part.Face(wire)
    
    # In X-Richtung extrudieren (Breite der Stange)
    stopper = face.extrude(App.Vector(bar_width, 0, 0))
    
    # Dreieck positionieren: am Ende der Stange (Y=0), oben (Z=bar_height)
    stopper.translate(App.Vector(
        0,                    # X: gleich wie Stange (beginnt bei 0)
        stopper_depth,        # Y: Dreieck endet bei Y=0 (Stangenende)
        bar_height            # Z: oben auf der Stange
    ))
    
    # Stange und Dreieck zusammenfügen
    halter = bar.fuse(stopper)
    halter = halter.removeSplitter()
    
    # Halter positionieren: zentriert in X, tangiert Innenradius
    bar_start_y = -inner_radius - bar_length
    halter.translate(App.Vector(
        -bar_width / 2,           # X: zentriert
        bar_start_y,              # Y: von Innenradius nach -Y
        0                         # Z: beginnt bei 0
    ))
    
    ring = ring.fuse(halter)
    
    # Fasen an der Stange (oben/unten, senkrechte am äußeren Ende, Schräge)
    # Dies muss NACH dem Fuse passieren, damit die Kanten korrekt am Zylinder enden
    bar_chamfer_edges = []
    
    for edge in ring.Edges:
        if "Line" in edge.Curve.TypeId:
            v0, v1 = edge.Vertexes[0].Point, edge.Vertexes[1].Point
            
            # Prüfen ob Kante zur Stange gehört (X-Position)
            is_bar_x = (abs(v0.x - (-bar_width/2)) < 0.01 or abs(v0.x - (bar_width/2)) < 0.01) and abs(v0.x - v1.x) < 0.01
            
            if is_bar_x:
                # Längskanten (parallel zu Y)
                if abs(v0.z - v1.z) < 0.01:
                    # Nur Oben (Z=bar_height) - Unten wird NICHT gefasst
                    if abs(v0.z - bar_height) < 0.01:
                        # Oben: Stopper beachten (Y > bar_start_y + stopper_depth)
                        max_y = max(v0.y, v1.y)
                        min_y = min(v0.y, v1.y)
                        # Kante muss "draußen" sein (Y < -outer_radius)
                        if max_y < -outer_radius + 1.0:
                            if min_y > bar_start_y + stopper_depth - 0.1:
                                bar_chamfer_edges.append(edge)
                
                # Schräge Kanten am Stopper (Seitenflächen)
                # X konstant, Y und Z ändern sich
                elif abs(v0.y - v1.y) > 0.01 and abs(v0.z - v1.z) > 0.01:
                    # Bereich prüfen: Stopper-Bereich
                    min_y, max_y = min(v0.y, v1.y), max(v0.y, v1.y)
                    min_z = min(v0.z, v1.z)
                    
                    if min_y >= bar_start_y - 0.1 and max_y <= bar_start_y + stopper_depth + 0.1:
                        if min_z >= bar_height - 0.1:
                            bar_chamfer_edges.append(edge)

            # Senkrechte Kanten am äußeren Ende (Y = bar_start_y)
            if abs(v0.x - v1.x) < 0.01 and abs(v0.y - v1.y) < 0.01:
                if abs(v0.y - bar_start_y) < 0.01:
                     # Senkrechte Kante am Ende (kann bis Z=15 gehen)
                     if min(v0.z, v1.z) < 0.01:
                         bar_chamfer_edges.append(edge)
            
            # Waagerechte Kante am äußeren Ende unten (Y = bar_start_y, Z = 0)
            if abs(v0.y - v1.y) < 0.01 and abs(v0.z - v1.z) < 0.01:
                if abs(v0.y - bar_start_y) < 0.01 and abs(v0.z) < 0.01:
                    bar_chamfer_edges.append(edge)

    if bar_chamfer_edges:
        ring = ring.makeChamfer(chamfer_size, bar_chamfer_edges)

    # Spitze des Dreiecks abfasen (ganz am Ende)
    stopper_tip_chamfer = 1.0
    tip_edges = []
    for edge in ring.Edges:
        if "Line" in edge.Curve.TypeId:
            v0, v1 = edge.Vertexes[0].Point, edge.Vertexes[1].Point
            # Die Spitzenkante verläuft in X-Richtung (Y und Z gleich)
            if abs(v0.y - v1.y) < 0.01 and abs(v0.z - v1.z) < 0.01:
                # Und ist an der höchsten Z-Position (Spitze des Dreiecks)
                if v0.z > bar_height + stopper_height - 0.1:
                    # Und am Ende der Stange
                    if abs(v0.y - bar_start_y) < 0.01:
                        tip_edges.append(edge)
    
    if tip_edges:
        ring = ring.makeChamfer(stopper_tip_chamfer, tip_edges)    # Zentrieren am Ursprung (Z-Achse)
    ring.translate(App.Vector(0, 0, -height / 2))
    
    obj = doc.addObject("Part::Feature", "Lappenhalter")
    obj.Shape = ring
    
    return [obj]
