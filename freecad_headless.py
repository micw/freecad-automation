#!/usr/bin/FreeCADCmd
# freecad_headless.py
import sys
import os
import importlib.util
import FreeCAD as App
import Mesh

def process_geometry(geometry_script_path, command, output_filename=None):
    """
    Lädt ein Geometrie-Skript und führt verschiedene Operationen aus.
    
    Args:
        geometry_script_path: Pfad zum Geometrie-Skript
        command: 'test', 'export-stl', oder 'export-3mf'
        output_filename: Name der Ausgabedatei (für export)
    """
    if not os.path.exists(geometry_script_path):
        App.Console.PrintError(f"Fehler: Geometrie-Skript nicht gefunden unter: {geometry_script_path}\n")
        sys.exit(1)

    # Dokument erstellen
    doc = App.newDocument("ProcessDoc")

    try:
        # Lade das Geometrie-Modul dynamisch
        spec = importlib.util.spec_from_file_location("geometry_module", geometry_script_path)
        geometry_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(geometry_module)

        # Prüfen, ob die create_geometry Funktion existiert
        if not hasattr(geometry_module, 'create_geometry'):
            App.Console.PrintError(f"Fehler: Die Funktion 'create_geometry(doc)' ist im Skript '{geometry_script_path}' nicht definiert.\n")
            sys.exit(1)

        # Geometrie erstellen lassen
        App.Console.PrintMessage(f"Erzeuge Geometrie aus '{os.path.basename(geometry_script_path)}'...\n")
        geometry_module.create_geometry(doc)

        # Dokument neu berechnen, um die Geometrie zu finalisieren
        doc.recompute()

        # Sicherstellen, dass Objekte vorhanden sind
        objects = doc.Objects
        if not objects:
            App.Console.PrintWarning("Warnung: Das Geometrie-Skript hat keine Objekte zum Dokument hinzugefügt.\n")
            return

        # Führe Befehl aus
        if command == 'test':
            # Test-Modus: Zeige nur Informationen
            App.Console.PrintMessage(f"\n=== TEST MODE ===\n")
            App.Console.PrintMessage(f"Anzahl Objekte: {len(objects)}\n")
            for obj in objects:
                App.Console.PrintMessage(f"  - {obj.Label} ({obj.TypeId})\n")
                if hasattr(obj, 'Shape') and obj.Shape:
                    shape = obj.Shape
                    bbox = shape.BoundBox
                    App.Console.PrintMessage(f"    Bounding Box: {bbox.XLength:.2f} x {bbox.YLength:.2f} x {bbox.ZLength:.2f} mm\n")
                    App.Console.PrintMessage(f"    Volume: {shape.Volume:.2f} mm³\n")
                    App.Console.PrintMessage(f"    Vertices: {len(shape.Vertexes)}, Faces: {len(shape.Faces)}\n")
            App.Console.PrintMessage(f"Test erfolgreich.\n")
            
        elif command == 'export-stl':
            # STL Export
            output_path = os.path.abspath(output_filename)
            App.Console.PrintMessage(f"Exportiere {len(objects)} Objekt(e) als STL nach '{output_path}'...\n")
            Mesh.export(objects, output_path)
            App.Console.PrintMessage("STL Export erfolgreich abgeschlossen.\n")
            
        elif command == 'export-3mf':
            # 3MF Export - ensure labels are set correctly
            output_path = os.path.abspath(output_filename or "export.3mf")
            if not output_path.lower().endswith(".3mf"):
                output_path = output_path + ".3mf"

            App.Console.PrintMessage(f"Exportiere {len(objects)} Objekt(e) als 3MF nach '{output_path}'...\n")

            # Labels eindeutig machen (einige Exporter verwenden diese für Bauteilnamen)
            seen_labels = set()
            for obj in objects:
                base = obj.Label if getattr(obj, "Label", None) else obj.Name
                name = base
                i = 1
                while name in seen_labels:
                    i += 1
                    name = f"{base}_{i}"
                try:
                    if obj.Label != name:
                        obj.Label = name
                except Exception:
                    # Falls Label nicht gesetzt werden kann, ignorieren
                    pass
                seen_labels.add(name)

            # Export versuchen: zuerst über Mesh.export (benötigt 3MF-Unterstützung/lib3mf)
            try:
                Mesh.export(objects, output_path)
                App.Console.PrintMessage("3MF Export erfolgreich abgeschlossen.\n")
            except Exception as e_primary:
                App.Console.PrintWarning(f"Mesh.export fehlgeschlagen ({e_primary}). Versuche generischen Exporter...\n")
                try:
                    import Import  # type: ignore
                    Import.export(objects, output_path)
                    App.Console.PrintMessage("3MF Export (Import.export) erfolgreich abgeschlossen.\n")
                except Exception as e_fallback:
                    App.Console.PrintError(
                        "3MF Export fehlgeschlagen. Prüfe, ob FreeCAD mit 3MF-Unterstützung (lib3mf) gebaut ist oder installiere den 3MF-Exporter.\n"
                    )
                    App.Console.PrintError(f"Fehler Mesh.export: {e_primary}\n")
                    App.Console.PrintError(f"Fehler Import.export: {e_fallback}\n")
                    sys.exit(2)
            

    finally:
        # Dokument schließen
        App.closeDocument(doc.Name)

import argparse

def main():
    parser = argparse.ArgumentParser(
        description="FreeCAD Headless Tool - Lädt ein Geometrie-Skript und führt verschiedene Operationen aus."
    )
    parser.add_argument(
        "command",
        choices=["test", "export-stl", "export-3mf"],
        help="Aktion: test (nur prüfen), export-stl (als STL exportieren), export-3mf (als 3MF exportieren)"
    )
    parser.add_argument(
        "geometry_script",
        help="Pfad zum Python-Skript, das eine 'create_geometry(doc)'-Funktion definiert."
    )
    parser.add_argument(
        "output_file",
        nargs="?",
        help="Name der Ausgabedatei (erforderlich für export-stl und export-3mf)"
    )

    # Da FreeCADCmd das Skript ausführt, sind die ersten beiden Argumente
    # der Interpreter und der Skriptname. Wir parsen nur die restlichen.
    args = parser.parse_args(sys.argv[2:])

    # Sicherheitsprüfung: Verhindern, dass das Skript sich selbst importiert.
    if os.path.abspath(args.geometry_script) == os.path.abspath(__file__):
        App.Console.PrintError("Fehler: Das Skript kann sich nicht selbst als Geometrie-Modul laden.\n")
        sys.exit(1)

    # Prüfe ob output_file für export benötigt wird
    if args.command in ['export-stl', 'export-3mf'] and not args.output_file:
        App.Console.PrintError(f"Fehler: {args.command} benötigt einen output_file Parameter.\n")
        sys.exit(1)

    process_geometry(args.geometry_script, args.command, args.output_file)

main()



