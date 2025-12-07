# FreeCAD Automation Project

## Setup

- **FreeCAD Version:** 1.0.2
- **Scripting:** Python mit Part-Modul
- **Test:** `./freecad_headless.py test geometry_<name>.py`
- **Export STL:** `./freecad_headless.py export-stl geometry_<name>.py output.stl`
- **Export 3MF:** `./freecad_headless.py export-3mf geometry_<name>.py output.3mf`

## Code-Pattern

### Dateistruktur
```python
# geometry_<name>.py
import os
import Part
import FreeCAD as App

DEFAULTS = {
    "PARAM_NAME_MM": 10.0,  # Beschreibung
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
    """Hauptfunktion - erzeugt Geometrie und gibt Liste von Objekten zurück."""
    shape = Part.makeBox(...)
    obj = doc.addObject("Part::Feature", "Name")
    obj.Shape = shape
    return [obj]
```

### Koordinatensystem
- **X:** Breite (links/rechts)
- **Y:** Höhe (unten/oben)
- **Z:** Dicke (hinten/vorne bzw. Druckrichtung)
- Geometrie zentriert am Ursprung (0, 0, 0)

## FreeCAD-Erkenntnisse

### Fillets (Abrundungen)
- **Schrittweise anwenden** - nicht alle Kanten auf einmal
- **Nur gerade Kanten:** `"Line" in edge.Curve.TypeId`
- **Kanten identifizieren über:**
  - `edge.Length` - Kantenlänge
  - `edge.CenterOfMass` - Schwerpunkt der Kante
  - `edge.Vertexes[0].Point`, `edge.Vertexes[1].Point` - Endpunkte

### Boolean-Operationen
- **Overlap 0.1mm** für stabile Fuse-Operationen
- Komplexe Teile (Pins, Rippen mit Rundungen) **NACH** Fillets hinzufügen
- Reihenfolge: `base.fuse(part1).fuse(part2)` oder `base.cut(cutout)`

### Häufige Fehler
- `BRep_API: command not done` → Fillet auf ungültiger Kante (z.B. bereits gerundet)
- Lösung: Kanten filtern, Reihenfolge ändern, komplexe Teile später hinzufügen

## Beispiel-Dateien

- `geometry_muldenklappe.py` - Komplexes Beispiel mit:
  - Basis-Platte mit Cutout
  - Halter (Holders) mit Dreiecks-Verstärkungen (Gussets)
  - Pins mit Torus und Tip
  - Rippen im Cutout
  - Verschiedene Fillet-Radien für unterschiedliche Kanten

- `geometry_led_diffuser.py` - Einfacheres Beispiel
- `geometry_fidget_pyramid.py` - Weiteres Beispiel

## Workflow für neue Modelle

1. **Grundform erstellen** (Box, Zylinder, etc.)
2. **Aussparungen** mit `cut()` hinzufügen
3. **Zusätzliche Geometrie** mit `fuse()` hinzufügen
4. **Fillets anwenden** (schrittweise, nach Kantentyp gruppiert)
5. **Komplexe Teile** (Pins etc.) zuletzt hinzufügen
6. **Testen** mit `./freecad_headless.py test ...`

## 3D-Druck Hinweise

- **Druckorientierung beachten:** Z ist typischerweise die Druckrichtung
- **Überhänge vermeiden:** 45° Winkel für Stützstrukturen (Gussets)
- **Toleranzen:** 
  - Spielpassung: +0.2mm bis +0.5mm
  - Presspassung: -0.1mm bis 0mm
