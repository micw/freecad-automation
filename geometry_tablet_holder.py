import os
import Part
import FreeCAD as App
from FreeCAD import Base


DEFAULTS_HUAWEI_MEDIAPAD_M5_LITE_10 = {
    "TABLET_THICKNESS": 9.0,
    "WALL_THICKNESS": 2.4,
    "HOLDER_WIDTH": 23.0,
    "HOLDER_HEIGHT": 150.0,
    "SIDE_FLANGE_WIDTH": 13.0,
    "BOTTOM_FLANGE_WIDTH": 13.0,
    "CLIP_WIDTH": 12.0,
    "CLIP_LENGTH": 20.0,
    "CLIP_NUB_RADIUS": 2,   # Radius des Zylinder-Nubs an den Clips
    "GUSSET_SIZE": 2.0,
    "BOTTOM_EXTENSION": 60.0,  # Verlängerung am Boden nach innen (L-Form)
    "BEAM_WIDTH": 10.0,        # Balken: Breite (X-Richtung)
    "BEAM_HEIGHT_FRONT": 13.0,  # Balken: Höhe vorne (Y-Richtung)
    "BEAM_LENGTH": 80.0,       # Balken: Länge (Z-Richtung, nach hinten)
    "BEAM_TILT_ANGLE": 15.0,   # Balken: Neigungswinkel in Grad
    "CUTOUT_LEFT_Y": 20.0,     # Cutout links (von vorne): Y-Position ab Flansch
    "CUTOUT_LEFT_HEIGHT": 14.0, # Cutout links: Höhe
    "CUTOUT_LEFT_THROUGH_FLANGE": 1,  # Cutout links: auch durch Flansch schneiden (1=ja, 0=nein)
    "CUTOUT_RIGHT_Y": 85.0,    # Cutout rechts (von vorne): Y-Position ab Flansch
    "CUTOUT_RIGHT_HEIGHT": 50.0, # Cutout rechts: Höhe
    "CUTOUT_RIGHT_THROUGH_FLANGE": 0,  # Cutout rechts: auch durch Flansch schneiden (1=ja, 0=nein)
}
DEFAULTS_SAMSUNG_GALAXY_TAB_S__SM_T700 = {
    "TABLET_THICKNESS": 8.0,
    "WALL_THICKNESS": 2.4,
    "HOLDER_WIDTH": 23.0,
    "HOLDER_HEIGHT": 130.0,
    "SIDE_FLANGE_WIDTH": 9.0,
    "BOTTOM_FLANGE_WIDTH": 20.0,
    "CLIP_WIDTH": 12.0,
    "CLIP_LENGTH": 20.0,
    "CLIP_NUB_RADIUS": 2,   # Radius des Zylinder-Nubs an den Clips
    "GUSSET_SIZE": 2.0,
    "BOTTOM_EXTENSION": 60.0,  # Verlängerung am Boden nach innen (L-Form)
    "BEAM_WIDTH": 10.0,        # Balken: Breite (X-Richtung)
    "BEAM_HEIGHT_FRONT": 13.0,  # Balken: Höhe vorne (Y-Richtung)
    "BEAM_LENGTH": 80.0,       # Balken: Länge (Z-Richtung, nach hinten)
    "BEAM_TILT_ANGLE": 15.0,   # Balken: Neigungswinkel in Grad
    "CUTOUT_LEFT_Y": 0.0,     # Cutout links (von vorne): Y-Position ab Flansch
    "CUTOUT_LEFT_HEIGHT": 0.0, # Cutout links: Höhe
    "CUTOUT_LEFT_THROUGH_FLANGE": 0,  # Cutout links: auch durch Flansch schneiden (1=ja, 0=nein)
    "CUTOUT_RIGHT_Y": 55.0,    # Cutout rechts (von vorne): Y-Position ab Flansch
    "CUTOUT_RIGHT_HEIGHT": 15.0, # Cutout rechts: Höhe
    "CUTOUT_RIGHT_THROUGH_FLANGE": 1,  # Cutout rechts: auch durch Flansch schneiden (1=ja, 0=nein)
}


DEFAULTS = DEFAULTS_SAMSUNG_GALAXY_TAB_S__SM_T700

PARAMS = DEFAULTS.copy()
for key, default in DEFAULTS.items():
    env = os.environ.get(key)
    if env is not None:
        PARAMS[key] = type(default)(env)

def create_box(l, w, h, x=0, y=0, z=0):
    return Part.makeBox(l, w, h, Base.Vector(x, y, z))

def create_geometry(doc):
    t = PARAMS["WALL_THICKNESS"]
    spacer_h = PARAMS["TABLET_THICKNESS"]  # Genau so hoch wie das Tablet
    
    # Basis-Struktur
    flange = create_box(PARAMS["SIDE_FLANGE_WIDTH"], PARAMS["HOLDER_HEIGHT"], t,
                        x=-PARAMS["SIDE_FLANGE_WIDTH"] - t, y=0, z=0)
    
    side_wall = create_box(t, PARAMS["HOLDER_HEIGHT"], spacer_h + t,
                           x=-t, y=0, z=0)
    
    back_plate = create_box(PARAMS["HOLDER_WIDTH"], PARAMS["HOLDER_HEIGHT"], t,
                            x=0, y=0, z=spacer_h)
    
    total_w = PARAMS["SIDE_FLANGE_WIDTH"] + t + PARAMS["HOLDER_WIDTH"]
    bottom = create_box(total_w, t, spacer_h + t,
                        x=-PARAMS["SIDE_FLANGE_WIDTH"] - t, y=0, z=0)
    
    part = flange.fuse(side_wall).fuse(back_plate).fuse(bottom)
    
    # Verlängerung am Boden nach innen (L-Form für mehr Auflagefläche)
    bottom_ext = PARAMS["BOTTOM_EXTENSION"]
    if bottom_ext > 0:
        # Verlängerung des Bodens nach innen (+X Richtung)
        bottom_ext_part = create_box(bottom_ext, t, spacer_h + t,
                                     x=PARAMS["HOLDER_WIDTH"], y=0, z=0)
        part = part.fuse(bottom_ext_part)
        
        # Rückwand für die untere Verlängerung - gleiche Tiefe wie HOLDER_WIDTH
        back_plate_bottom = create_box(bottom_ext, PARAMS["HOLDER_WIDTH"], t,
                                       x=PARAMS["HOLDER_WIDTH"], y=0, z=spacer_h)
        part = part.fuse(back_plate_bottom)
    
    # Unterer Flansch (bei Z=0, wie der seitliche Flansch, zum Anschrauben)
    total_bottom_width = PARAMS["HOLDER_WIDTH"] + bottom_ext
    bottom_flange = create_box(total_bottom_width, PARAMS["BOTTOM_FLANGE_WIDTH"], t,
                               x=0, y=-PARAMS["BOTTOM_FLANGE_WIDTH"], z=0)
    part = part.fuse(bottom_flange)
    
    # Balken zur Tablet-Stützung
    # Koordinaten: X=Breite, Y=Höhe (oben+), Z=Länge (hinten+)
    # Der Balken wird in Y-Richtung mit steigendem Z dünner (Keil-Form)
    # Bündig mit der unteren Kante des Flanschs (bei y=-FLANGE_WIDTH)
    # Rechte Kante des Balkens bündig mit innerer Kante der Seitenwand (bei x=HOLDER_WIDTH)
    import math
    beam_width = PARAMS["BEAM_WIDTH"]
    beam_start_x = PARAMS["HOLDER_WIDTH"] - beam_width  # Linke Kante, so dass rechte bei HOLDER_WIDTH
    beam_height_front = PARAMS["BEAM_HEIGHT_FRONT"]
    beam_height_back = t      # Y-Richtung (Höhe hinten = WALL_THICKNESS)
    beam_length = PARAMS["BEAM_LENGTH"]
    tilt_angle = PARAMS["BEAM_TILT_ANGLE"]
    tilt_offset = beam_length * math.tan(math.radians(tilt_angle))  # Y-Verschiebung hinten
    
    # Trapez-Profil in YZ-Ebene erstellen (vorne hoch, hinten schmal und nach oben geneigt)
    # Untere Kante bei y=-BOTTOM_FLANGE_WIDTH (bündig mit Flansch-Unterkante)
    p1 = Base.Vector(beam_start_x, -PARAMS["BOTTOM_FLANGE_WIDTH"], 0)
    p2 = Base.Vector(beam_start_x, -PARAMS["BOTTOM_FLANGE_WIDTH"] + beam_height_front, 0)
    p3 = Base.Vector(beam_start_x, -PARAMS["BOTTOM_FLANGE_WIDTH"] + beam_height_back + tilt_offset, beam_length)
    p4 = Base.Vector(beam_start_x, -PARAMS["BOTTOM_FLANGE_WIDTH"] + tilt_offset, beam_length)
    wire_beam = Part.makePolygon([p1, p2, p3, p4, p1])
    face_beam = Part.Face(wire_beam)
    beam_shape = face_beam.extrude(Base.Vector(beam_width, 0, 0))
    
    # Diagonale Verstrebung: sitzt auf der Oberseite des Balkens auf, geht zur Rückwand hoch
    # Untere Kante = Oberseite des Balkens (folgt der 15° Neigung)
    # Kurze Seite = vorne an der Rückwand (z = spacer_h + t), 15mm hoch
    # Extrusion in X-Richtung: vorne breit (beam_width), hinten schmal (t)
    diag_front_z = spacer_h + t  # Vordere Position (Rückseite der Rückwand)
    diag_back_z = beam_length    # Hintere Position (Ende des Balkens)
    diag_short_side = 15.0       # Länge der kurzen Seite (Y-Richtung)
    diag_width_front = beam_width  # Breite vorne (Klebefläche an Rückwand)
    diag_width_back = t            # Breite hinten (nur Wandstärke)
    
    # Y-Position auf Balken-Oberseite bei gegebenem Z
    def beam_top_y_at_z(z):
        t_param = z / beam_length
        y_front = -PARAMS["BOTTOM_FLANGE_WIDTH"] + beam_height_front
        y_back = -PARAMS["BOTTOM_FLANGE_WIDTH"] + beam_height_back + tilt_offset
        return y_front + t_param * (y_back - y_front)
    
    diag_bottom_y_front = beam_top_y_at_z(diag_front_z)  # Unterseite Diagonale vorne (auf Balken)
    diag_bottom_y_back = beam_top_y_at_z(diag_back_z)    # Unterseite Diagonale hinten (auf Balken)
    diag_top_y_front = diag_bottom_y_front + diag_short_side  # Oberseite vorne (kurze Seite)
    
    # Keil-Form in X-Richtung: vorne breit, hinten schmal
    # 6 Eckpunkte für das 3D-Profil
    diag_x_right = beam_start_x + beam_width  # Rechte Kante (bündig mit Balken)
    diag_x_left_front = beam_start_x          # Linke Kante vorne (volle Balkenbreite)
    diag_x_left_back = beam_start_x + beam_width - t  # Linke Kante hinten (nur Wandstärke)
    
    # Vordere Fläche (bei Rückwand) - Rechteck
    f1 = Base.Vector(diag_x_left_front, diag_bottom_y_front, diag_front_z)
    f2 = Base.Vector(diag_x_right, diag_bottom_y_front, diag_front_z)
    f3 = Base.Vector(diag_x_right, diag_top_y_front, diag_front_z)
    f4 = Base.Vector(diag_x_left_front, diag_top_y_front, diag_front_z)
    
    # Hintere Kante (am Balkenende) - Linie
    b1 = Base.Vector(diag_x_left_back, diag_bottom_y_back, diag_back_z)
    b2 = Base.Vector(diag_x_right, diag_bottom_y_back, diag_back_z)
    
    # Loft zwischen vorderer Fläche und hinterer Kante
    wire_front = Part.makePolygon([f1, f2, f3, f4, f1])
    wire_back = Part.makePolygon([b1, b2, b1])  # Degenerierte Linie
    # Stattdessen: Solid aus einzelnen Flächen bauen
    # Einfacher: Zwei Dreiecke extrudieren und vereinigen
    
    # Teil 1: Schmale Diagonale (wie vorher, über volle Länge)
    d1 = Base.Vector(diag_x_left_back, diag_bottom_y_front, diag_front_z)
    d2 = Base.Vector(diag_x_left_back, diag_bottom_y_back, diag_back_z)
    d3 = Base.Vector(diag_x_left_back, diag_top_y_front, diag_front_z)
    wire_diag = Part.makePolygon([d1, d2, d3, d1])
    face_diag = Part.Face(wire_diag)
    diagonal_narrow = face_diag.extrude(Base.Vector(t, 0, 0))
    
    # Teil 2: Klebeflächen-Verbreiterung vorne (an Rückseite der Rückwand)
    # Geht von z=0 bis z=diag_front_z+t
    # In Y-Richtung verlängert um halbe Balkenhöhe nach unten (wegen Schräge)
    glue_width = beam_width  # Volle Breite des Balkens
    glue_depth = diag_front_z + t  # Von z=0 bis hinter die Rückwand
    glue_height = diag_short_side + beam_height_front / 2  # 15mm + halbe Balkenhöhe
    glue_y_start = diag_bottom_y_front - beam_height_front / 2  # Um halbe Balkenhöhe nach unten verschoben
    glue_box = create_box(glue_width, glue_height, glue_depth,
                          x=beam_start_x, y=glue_y_start, z=0)
    
    diagonal = diagonal_narrow.fuse(glue_box)
    
    # Balken + Diagonale als kombiniertes separates Teil
    beam_complete = beam_shape.fuse(diagonal)
    
    # Verstärkungsdreiecke (Gussets) - durchgehend entlang der gesamten Höhe
    gusset_size = PARAMS["GUSSET_SIZE"]
    
    # Gusset 1: Flansch zu Seitenwand (durchgehend über HOLDER_HEIGHT)
    # Dreieck-Profil in XZ-Ebene, auf der Oberseite des Flanschs (Z=t)
    p1 = Base.Vector(-t, 0, t)
    p2 = Base.Vector(-t - gusset_size, 0, t)
    p3 = Base.Vector(-t, 0, t + gusset_size)
    wire1 = Part.makePolygon([p1, p2, p3, p1])
    face1 = Part.Face(wire1)
    gusset1 = face1.extrude(Base.Vector(0, PARAMS["HOLDER_HEIGHT"], 0))
    part = part.fuse(gusset1)
    
    # Gusset 2: Seitenwand zu Rückwand (durchgehend über HOLDER_HEIGHT)
    # Dreieck-Profil: Ecke bei (0, spacer_h), nach +X und nach -Z (ins Innere)
    p1 = Base.Vector(0, 0, spacer_h)
    p2 = Base.Vector(gusset_size, 0, spacer_h)
    p3 = Base.Vector(0, 0, spacer_h - gusset_size)
    wire2 = Part.makePolygon([p1, p2, p3, p1])
    face2 = Part.Face(wire2)
    gusset2 = face2.extrude(Base.Vector(0, PARAMS["HOLDER_HEIGHT"], 0))
    part = part.fuse(gusset2)
    
    # Gussets am unteren Flansch (entlang der X-Richtung)
    bottom_ext = PARAMS["BOTTOM_EXTENSION"]
    total_bottom_width = PARAMS["HOLDER_WIDTH"] + bottom_ext
    
    # Gusset 3: Unterer Flansch zu Boden (durchgehend über volle Bodenbreite)
    # Dreieck-Profil in YZ-Ebene, auf der Oberseite des Flanschs (Z=t)
    p1 = Base.Vector(0, 0, t)
    p2 = Base.Vector(0, -gusset_size, t)
    p3 = Base.Vector(0, 0, t + gusset_size)
    wire3 = Part.makePolygon([p1, p2, p3, p1])
    face3 = Part.Face(wire3)
    gusset3 = face3.extrude(Base.Vector(total_bottom_width, 0, 0))
    part = part.fuse(gusset3)
    
    # Gusset 4: Untere Seitenwand zu unterer Rückwand (von x=0 bis x=HOLDER_WIDTH+bottom_ext)
    # Dreieck-Profil in YZ-Ebene, Ecke bei (z=spacer_h, y=t)
    # Geht nach +Y (in die Rückwand rein) und nach -Z (in den Boden rein)
    p1 = Base.Vector(0, t, spacer_h)
    p2 = Base.Vector(0, t + gusset_size, spacer_h)
    p3 = Base.Vector(0, t, spacer_h - gusset_size)
    wire4 = Part.makePolygon([p1, p2, p3, p1])
    face4 = Part.Face(wire4)
    gusset4 = face4.extrude(Base.Vector(total_bottom_width, 0, 0))
    part = part.fuse(gusset4)
    
    # Querschnitt des Hauptteils aus dem Balken ausschneiden
    # (für exakte Klebeflächen - Flansch und Gusset werden abgeschnitten)
    # Rahmen in -Z Richtung verlängern um loses Material vor dem Rahmen zu entfernen
    part_extended = part.copy()
    extension_faces = []
    for face in part_extended.Faces:
        # Nur Flächen die in -Z Richtung zeigen (normale hat Z-Komponente < 0)
        if face.normalAt(0, 0).z < -0.1:
            extension_faces.append(face)
    if extension_faces:
        for face in extension_faces:
            extension = face.extrude(Base.Vector(0, 0, -(spacer_h + t)))
            part_extended = part_extended.fuse(extension)
    
    beam_complete = beam_complete.cut(part_extended)
    
    # Löcher in die Rückwand schneiden (Material sparen)
    grid_size = 8.0
    grid_spacing = 4.0
    margin = 5.0
    
    # Clip-Bereiche aussparen
    clip_w = PARAMS["CLIP_WIDTH"]
    clip_l = PARAMS["CLIP_LENGTH"]
    clip_x = PARAMS["HOLDER_WIDTH"] / 2 - clip_w / 2
    y_top = PARAMS["HOLDER_HEIGHT"] * 0.70
    y_bot = PARAMS["HOLDER_HEIGHT"] * 0.30
    
    y = margin
    while y + grid_size <= PARAMS["HOLDER_HEIGHT"] - margin:
        x = margin
        while x + grid_size <= PARAMS["HOLDER_WIDTH"] - margin:
            # Prüfen ob im Clip-Bereich (mit größerem Sicherheitsabstand)
            clip_margin = 5.0  # Sicherheitsabstand um die Clips
            in_clip_top = (x < clip_x + clip_w + clip_margin and x + grid_size > clip_x - clip_margin and
                          y < y_top + clip_l + clip_margin and y + grid_size > y_top - clip_margin)
            in_clip_bot = (x < clip_x + clip_w + clip_margin and x + grid_size > clip_x - clip_margin and
                          y < y_bot + clip_margin and y + grid_size > y_bot - clip_l - clip_margin)
            
            if not in_clip_top and not in_clip_bot:
                cutout = create_box(grid_size, grid_size, t * 3,
                                   x=x, y=y, z=spacer_h - t)
                part = part.cut(cutout)
            
            x += grid_size + grid_spacing
        y += grid_size + grid_spacing
    
    # Löcher in die untere Rückwand schneiden (Material sparen)
    if bottom_ext > 0:
        y = margin
        while y + grid_size <= PARAMS["HOLDER_WIDTH"] - margin:
            x = margin
            while x + grid_size <= bottom_ext - margin:
                cutout = create_box(grid_size, grid_size, t * 3,
                                   x=PARAMS["HOLDER_WIDTH"] + x, y=y, z=spacer_h - t)
                part = part.cut(cutout)
                x += grid_size + grid_spacing
            y += grid_size + grid_spacing
    
    # Zwei flache Clips (oben zeigt nach oben, unten zeigt nach unten)
    clip_w = PARAMS["CLIP_WIDTH"]
    clip_l = PARAMS["CLIP_LENGTH"]
    clip_x = PARAMS["HOLDER_WIDTH"] / 2 - clip_w / 2
    gap = 1.0
    nub_r = PARAMS["CLIP_NUB_RADIUS"]
    
    # Oberer Clip: Anker bei 70%, zeigt nach oben
    y_top = PARAMS["HOLDER_HEIGHT"] * 0.70
    hole_top = create_box(clip_w + 2*gap, clip_l + gap, t * 3,
                          x=clip_x - gap, y=y_top + gap, z=spacer_h - t)
    part = part.cut(hole_top)
    clip_top = create_box(clip_w, clip_l, t,
                          x=clip_x, y=y_top, z=spacer_h)
    # Halbzylinder-Nub: zeigt nach vorne (Z+)
    nub_top = Part.makeCylinder(nub_r, clip_w,
                                Base.Vector(clip_x, y_top + clip_l - nub_r, spacer_h),
                                Base.Vector(1, 0, 0), 180)
    nub_top.rotate(Base.Vector(clip_x, y_top + clip_l - nub_r, spacer_h), Base.Vector(1, 0, 0), 90)
    clip_top = clip_top.fuse(nub_top)
    part = part.fuse(clip_top)
    
    # Unterer Clip: Anker bei 30%, zeigt nach unten
    y_bot = PARAMS["HOLDER_HEIGHT"] * 0.30
    hole_bot = create_box(clip_w + 2*gap, clip_l + gap, t * 3,
                          x=clip_x - gap, y=y_bot - clip_l - gap, z=spacer_h - t)
    part = part.cut(hole_bot)
    clip_bot = create_box(clip_w, clip_l, t,
                          x=clip_x, y=y_bot - clip_l, z=spacer_h)
    # Halbzylinder-Nub: zeigt nach vorne (Z+)
    nub_bot = Part.makeCylinder(nub_r, clip_w,
                                Base.Vector(clip_x, y_bot - clip_l + nub_r, spacer_h),
                                Base.Vector(1, 0, 0), 180)
    nub_bot.rotate(Base.Vector(clip_x, y_bot - clip_l + nub_r, spacer_h), Base.Vector(1, 0, 0), 90)
    clip_bot = clip_bot.fuse(nub_bot)
    part = part.fuse(clip_bot)
    
    # Spiegelpunkt: Mitte der Gesamt-Bodenbreite (inkl. Extension)
    total_bottom_width = PARAMS["HOLDER_WIDTH"] + PARAMS["BOTTOM_EXTENSION"]
    mirror_x = total_bottom_width / 2
    part_right = part.mirror(Base.Vector(mirror_x, 0, 0), Base.Vector(1, 0, 0))
    
    # Cutout nur im linken Teil (von vorne gesehen) - das ist TabletHolder_Right im Code
    # Position: linke Seitenwand, y=CUTOUT_LEFT_Y ab Flansch
    # In Z-Achse: optional ab Flansch (z=0) oder erst danach (z=t)
    # In X-Achse: Seitenwand + Gussets, optional auch durch Flansch
    if PARAMS["CUTOUT_LEFT_HEIGHT"] > 0:
        cutout_z = 0 if PARAMS["CUTOUT_LEFT_THROUGH_FLANGE"] else t
        cutout_x_extra = PARAMS["SIDE_FLANGE_WIDTH"] if PARAMS["CUTOUT_LEFT_THROUGH_FLANGE"] else 0
        cutout_right = create_box(t + gusset_size + gusset_size + cutout_x_extra, PARAMS["CUTOUT_LEFT_HEIGHT"], spacer_h + t + t - cutout_z,
                                  x=total_bottom_width - gusset_size, y=t + PARAMS["CUTOUT_LEFT_Y"], z=cutout_z)
        part_right = part_right.cut(cutout_right)
    
    # Cutout nur im rechten Teil (von vorne gesehen) - das ist TabletHolder_Left im Code
    # Position: rechte Seitenwand, y=CUTOUT_RIGHT_Y ab Flansch
    # In X-Achse: Seitenwand + Gussets, optional auch durch Flansch
    if PARAMS["CUTOUT_RIGHT_HEIGHT"] > 0:
        cutout_z = 0 if PARAMS["CUTOUT_RIGHT_THROUGH_FLANGE"] else t
        cutout_x_extra = PARAMS["SIDE_FLANGE_WIDTH"] if PARAMS["CUTOUT_RIGHT_THROUGH_FLANGE"] else 0
        cutout_left = create_box(t + gusset_size + gusset_size + cutout_x_extra, PARAMS["CUTOUT_RIGHT_HEIGHT"], spacer_h + t + t - cutout_z,
                                 x=-t - gusset_size - cutout_x_extra, y=t + PARAMS["CUTOUT_RIGHT_Y"], z=cutout_z)
        part = part.cut(cutout_left)
    
    obj_left = doc.addObject("Part::Feature", "TabletHolder_Left")
    obj_left.Shape = part
    
    obj_right = doc.addObject("Part::Feature", "TabletHolder_Right")
    obj_right.Shape = part_right
    obj_right.Placement.Base = Base.Vector(100, 0, 0)
    
    # Balken als separate Teile (zum extra Drucken und Ankleben)
    obj_beam_left = doc.addObject("Part::Feature", "Beam_Left")
    obj_beam_left.Shape = beam_complete
    obj_beam_left.Placement.Base = Base.Vector(0, -50, 0)
    
    beam_right = beam_complete.mirror(Base.Vector(mirror_x, 0, 0), Base.Vector(1, 0, 0))
    obj_beam_right = doc.addObject("Part::Feature", "Beam_Right")
    obj_beam_right.Shape = beam_right
    obj_beam_right.Placement.Base = Base.Vector(100, -50, 0)
    
    return [obj_left, obj_right, obj_beam_left, obj_beam_right]
