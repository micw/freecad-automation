# LiveGeometryReloader.FCMacro
"""
Dieses Makro überwacht eine Python-Geometriedatei und aktualisiert die
Ansicht in der FreeCAD GUI live, sobald die Datei gespeichert wird.

Workflow:
1. Führe das Makro aus.
2. Wähle die Python-Datei aus, die du bearbeiten möchtest 
   (z.B. 'geometry_sphere.py').
3. Die Datei muss eine Funktion 'create_geometry(doc)' enthalten.
4. Bearbeite und speichere die Python-Datei in einem externen Editor.
5. Die Geometrie im aktiven FreeCAD-Dokument wird automatisch aktualisiert.
"""

import sys
import os
import importlib
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QFileDialog, QMessageBox
import FreeCAD as App
import FreeCADGui as Gui

# --- Globale Variablen zur Zustandsspeicherung ---
monitored_file = None
last_mtime = 0
timer = None
doc_name = None  # Name des Dokuments, in das geladen wird

def _is_doc_open(name: str) -> bool:
    """Prüft, ob ein Dokument mit dem angegebenen Namen noch geöffnet ist."""
    try:
        return bool(name) and name in App.listDocuments()
    except Exception:
        return False


def check_for_update():
    """
    Wird vom QTimer periodisch aufgerufen. Prüft, ob die Datei geändert wurde
    und löst bei Bedarf die Aktualisierung aus.
    """
    global last_mtime, monitored_file, doc_name

    if not monitored_file:
        stop_monitoring()
        return

    try:
        # Beende, wenn das zugehörige Dokument geschlossen wurde
        if not _is_doc_open(doc_name):
            App.Console.PrintMessage("Überwachtes Dokument wurde geschlossen – Live-Reloading wird beendet.\n")
            stop_monitoring()
            return

        if not os.path.exists(monitored_file):
            App.Console.PrintError(f"✗ Fehler: Überwachte Datei '{monitored_file}' nicht mehr gefunden.\n")
            stop_monitoring()
            return
            
        current_mtime = os.path.getmtime(monitored_file)
        if current_mtime > last_mtime:
            App.Console.PrintMessage(f"→ Änderung in '{os.path.basename(monitored_file)}' erkannt. Lade neu...\n")
            last_mtime = current_mtime
            reload_geometry()
    except Exception as e:
        App.Console.PrintError(f"✗ Fehler beim Überwachen der Datei: {e}\n")
        stop_monitoring()

def reload_geometry():
    """
    Löscht alle Objekte im Dokument, lädt das Geometrie-Modul neu
    und lässt es die Szene neu aufbauen.
    """
    global monitored_file, doc_name

    # Greife auf das beim Start ermittelte Dokument zu
    if not _is_doc_open(doc_name):
        App.Console.PrintMessage("Zieldokument ist nicht mehr geöffnet – Live-Reloading wird beendet.\n")
        stop_monitoring()
        return

    doc = App.getDocument(doc_name)

    try:
        # 1. Alle vorhandenen Objekte im Dokument radikal löschen
        App.Console.PrintMessage("Lösche alte Objekte...\n")
        # Wichtig: Wir erstellen eine Kopie der Liste, da wir sie während der Iteration verändern
        for obj in doc.Objects[:]:
            try:
                if obj and hasattr(obj, 'Name') and obj.Name:
                    doc.removeObject(obj.Name)
            except Exception as e:
                obj_name = getattr(obj, 'Name', 'Unknown') if obj else 'None'
                App.Console.PrintWarning(f"Konnte Objekt '{obj_name}' nicht entfernen: {e}\n")
        
        # 2. Modul neu laden
        module_dir = os.path.dirname(monitored_file)
        if module_dir not in sys.path:
            sys.path.insert(0, module_dir)

        module_name = os.path.splitext(os.path.basename(monitored_file))[0]
        importlib.invalidate_caches()
        
        if module_name in sys.modules:
            geometry_module = importlib.reload(sys.modules[module_name])
        else:
            geometry_module = importlib.import_module(module_name)

        # 3. Geometrie-Funktion aufrufen
        if hasattr(geometry_module, 'create_geometry'):
            App.Console.PrintMessage("Führe 'create_geometry' aus...\n")
            geometry_module.create_geometry(doc)
            doc.recompute()
            try:
                # Versuche, die Ansicht des betroffenen Dokuments zu fitten
                if Gui.ActiveDocument and Gui.ActiveDocument.Document.Name == doc_name:
                    Gui.SendMsgToActiveView("ViewFit")
            except Exception:
                pass
            App.Console.PrintMessage("✓ Geometrie erfolgreich aktualisiert.\n")
        else:
            App.Console.PrintError(f"✗ Fehler: Funktion 'create_geometry(doc)' nicht in '{os.path.basename(monitored_file)}' gefunden.\n")

    except Exception as e:
        App.Console.PrintError(f"✗ Fehler beim Neuladen der Geometrie: {e}\n")
        import traceback
        traceback.print_exc(file=sys.stderr)


def stop_monitoring():
    """Stoppt den Timer und räumt den Zustand auf."""
    global timer, monitored_file, doc_name
    try:
        if timer:
            if timer.isActive():
                timer.stop()
            # Verbindungen lösen, um Leaks zu vermeiden
            try:
                timer.timeout.disconnect(check_for_update)
            except Exception:
                pass
    finally:
        timer = None
        monitored_file = None
        doc_name = None
        App.Console.PrintMessage("Live-Reloading gestoppt.\n")

def run():
    """Hauptfunktion des Makros."""
    global monitored_file, last_mtime, timer, doc_name

    # Prüfen, ob ein Dokument geöffnet ist
    if not App.ActiveDocument:
        msg_box = QMessageBox()
        msg_box.setText("Bitte erstelle oder öffne ein Dokument, bevor du das Makro startest.")
        msg_box.setWindowTitle("Kein Dokument")
        msg_box.exec_()
        return

    # Vorherige Überwachung zuverlässig beenden, falls Makro erneut gestartet wird
    if timer is not None:
        stop_monitoring()

    # Dateiauswahldialog
    path, _ = QFileDialog.getOpenFileName(
        None, 
        "Wähle eine Geometrie-Python-Datei zum Überwachen",
        "", # Startverzeichnis
        "Python Files (*.py)"
    )

    if not path:
        App.Console.PrintMessage("Keine Datei ausgewählt. Makro wird beendet.\n")
        return

    monitored_file = path
    last_mtime = os.path.getmtime(monitored_file)
    doc_name = App.ActiveDocument.Name  # Dokument fixieren, in das geladen wird
    
    # Ersten Ladevorgang sofort ausführen
    reload_geometry()

    # Timer starten, der alle 2 Sekunden prüft
    if timer is None:
        timer = QTimer()
        timer.setInterval(2000)  # Millisekunden
        timer.timeout.connect(check_for_update)
    timer.start()
    
    App.Console.PrintMessage(f"Überwache '{os.path.basename(monitored_file)}' auf Änderungen...\n")


# --- Makro starten ---
if __name__ == "__main__":
    run()
