# Workflow zur programmatischen Erzeugung von 3D-Modellen mit FreeCAD

## Grundkonzept

Die Modelle werden in einer Python-Datei in einer Methode `create_geometry` erzeugt. Diese liefert ein oder mehrere FreeCAD-Objekte zurück. Ein Modell kann entweder in der FreeCAD Gui gerendert und interaktiv angeschaut/bearbeitet werden oder via CLI Headless zum Beispiel nach STL konvertiert werden.


## FreeCAD Gui

Die FreeCAD Gui wird zum Live-Preview der Modelle verwendet. Ein Makro `LiveGeometryReloader.FCMacro.py` lädt eine auswählbare Modell-Datei, überwacht diese auf Änderungen und lädt sie dann neu.


## FreeCAD CLI

Der Wrapper 'freecad_headless.py' verwendet die FreCAD-Python-CLI. Er ermöglicht es, eine Modell zu prüfen und als STL oder 3MF zu exportieren

## Slicer

Das exportierte 3MF Modell kann direkt als Projekt im Anycubic Slicer Next geöffnet werden. Dort können Slicer-Einstellungen manuell gemacht werden.

TODOs:
- Es wäre super, wenn in einem bestehenden Slicer-Projekt die Modelle ersetzt werden können, ohne das Slicing erneut manuell durchzuführen
- Die Bezeichnung der Objekte geht bem Export nach 3MF verloren -> Ticket bei FreeCAD aufmachen, dass die Metadaten exportiert werden können


# Projekte

## Matrix-LED-Diffuser

Ein Diffuser für LED-Matrix PCBs mit adressierbaren RGB-LEDS.

![LED-Matrix ohne Diffuser](img/matrix_led_diffuser1.jpeg)
![Diffuser in FreeCAD](img/matrix_led_diffuser2.jpeg)
![LED-Matrix mit Diffuser](img/matrix_led_diffuser3.jpeg)


* Geometrie-Datei: `geometry_led_diffuser.py`
* Features
    * Größe der Matrix und Anzahl LEDs einstellbar
    * optionale Aussparungen für Widerstände (horizontal/vertikal)
    * optionaler äußerer Rand
* Slicer-Settings
    * Beim Import: "Als ein kombiniertes Objekt importieren"
    * Objekt "Object_1" -> Farbe Weiß wählen; Rest: schwarz
    * Prozess 0.16mm Standard @AC KS1
        * Anzahl der langsamen Schichten: 2 (dadurch werden die 2 Diffusor-Schichten sauberer gedruckt)
        * Multimaterial: Reinigungsturm deaktivieren
* Ideen
    * mehrere LED-Matrix-PCBs in einem Rahmen horizontal und/oder vertikal
    * mehrere Rahmen zusammensteckbar
    * Clip für LED-Matrix-PCB
    * Befestigungs-Ösen
    * Aussparungen für Kabel



