"""
Torsions Test Stand - Software für Torsionsprüfstand
====================================================
Projekt:    Torsions Test Stand
Datei:      main.py
Autor:      [Technikergruppe]
Version:    2.0
Python:     3.13
Datum:      Oktober 2025
------------------------------------------------------------------------------

ÜBERSICHT:
----------
Diese Software steuert einen Torsionsprüfstand zur präzisen Erfassung von
Drehmoment und Winkel. Die Anwendung wurde speziell für eine Techniker-
Abschlussarbeit entwickelt und ermöglicht automatisierte Torsionsprüfungen
mit Live-Visualisierung.

HARDWARE-KOMPONENTEN:
---------------------
1. Drehmoment-Messung:
   - DF-30 Drehmoment-Sensor (Messbereich: ±20 Nm)
   - Messverstärker (Ausgang: ±10V)
   - NI-6000 DAQ, Kanal ai0 (Eingang: ±10V)

2. Winkel-Messung:
   - SSI-Encoder: RS Components RSA 58E (13-Bit Single-Turn, 12-Bit Multi-Turn)
   - Motrona 7386.5010 SSI-zu-Analog Konverter (0-10V Ausgang)
   - NI-6000 DAQ, Kanal ai1 (Eingang: 0-10V)
   - Skalierung: 0V = 0°, 10V = 360°

3. Motor-Steuerung:
   - N5 Nanotec Schrittmotor (Closed-Loop, Modbus TCP)
   - Alternative: Trinamic Steprocker
   - Bidirektionale Steuerung (Geschwindigkeit ± Grad/s)

HAUPTFUNKTIONEN:
----------------
✓ Demo-Modus für Tests ohne Hardware
✓ Live-Visualisierung (Torque vs. Angle Graph)
✓ Automatische Stopbedingungen (Max Torque/Max Angle)
✓ Home-Position und Nullpunkt-Kalibrierung
✓ Single-Turn Unwrap-Logik (kontinuierliche Winkelmessung über 360°)
✓ Umdrehungszähler (vorwärts/rückwärts)
✓ Datenaufzeichnung in Textdatei mit Zeitstempel
✓ GUI mit Dark-Mode Theme

MESSABLAUF:
-----------
1. Hardware aktivieren → NI-6000 DAQ + Motor-Controller initialisieren
2. Home-Position → Motor auf 0° fahren, Sensoren kalibrieren
3. Parameter setzen → Max Angle, Max Torque, Max Velocity
4. Messung starten → Motor dreht mit konstanter Geschwindigkeit
5. Datenerfassung → Timer liest alle 100ms Torque und Angle
6. Unwrap-Logik → Software zählt Umdrehungen bei Single-Turn Encoder
7. Stopbedingung → Automatischer Stopp bei Max Angle oder Max Torque
8. Daten speichern → Zeitstempel, Spannung, Torque, Angle in Datei

WINKEL-MESSUNG (NEU in V2.0):
-----------------------------
Single-Turn Modus (Standard):
  - Encoder gibt 0-360° aus (wiederholt bei jeder Umdrehung)
  - Software erkennt Übergang 360°→0° oder 0°→360°
  - Umdrehungszähler wird automatisch erhöht/verringert
  - Kontinuierlicher Winkel = Rohwinkel + (360° × Umdrehungen)

Multi-Turn Modus (Vorbereitet):
  - Absolute Positionierung über mehrere Umdrehungen
  - Keine Unwrap-Logik erforderlich

KONFIGURATION:
--------------
Alle wichtigen Parameter können am Anfang dieser Datei angepasst werden:
- DEMO_MODE: True/False für Simulation
- ANGLE_MEASUREMENT_SOURCE: "daq" oder "motor"
- ANGLE_ENCODER_MODE: "single_turn" oder "multi_turn"
- DAQ-Kanäle, Skalierung, Messintervall, etc.

BEDIENUNG:
----------
1. Programm starten → python main.py
2. Demo-LED prüfen → GRÜN=Demo, ROT=Echte Hardware
3. Projektordner wählen → Button "Select Project Directory"
4. Hardware aktivieren → Button "Activate Hardware"
5. Optional: Home Position → Button "Home Position"
6. Parameter einstellen → Max Angle, Max Torque, Max Velocity
7. Messung starten → Button "Start Measurement"
8. Messung läuft → Graph zeigt Live-Daten
9. Messung stoppt automatisch oder manuell → Button "Stop Measurement"

DATEISTRUKTUR:
--------------
Messdaten werden gespeichert in:
Projektordner/YYYYMMDD_HHMMSS_Probenname/
  ├─ YYYYMMDD_HHMMSS_Probenname_DATA.txt  (Messdaten)
  └─ (Weitere Dateien/Bilder können hinzugefügt werden)

FEHLERBEHEBUNG:
---------------
- Hardware-Fehler → Prüfe Verkabelung und DAQ-Konfiguration
- Keine Winkelwerte → Prüfe DAQ_CHANNEL_ANGLE und Motrona-Verbindung
- Falsche Wraps → Erhöhe Sampling-Rate (verringere MEASUREMENT_INTERVAL)
- Motor reagiert nicht → Prüfe Motor-Controller Verbindung und Typ

WEITERE DOKUMENTATION:
----------------------
Siehe: SSI_ENCODER_INTEGRATION.md für detaillierte Informationen zu:
- Systemarchitektur
- Programmablaufpläne (PAP)
- Unwrap-Algorithmus
- Validierung und Testing
"""

import logging
import os
import sys
from datetime import datetime

# PyQt6 Imports
import pyqtgraph as pg
from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QTextCursor
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
)

# Project Imports
from src.gui.stylesheet import get_dark_stylesheet
from src.hardware import (
    DAQmxTask,
    MotorControllerBase,
    NanotecMotorController,
    TrinamicMotorController,
)
from src.utils.logger_helper import GuiLogger, WrappingFormatter

# ===========================================================================================
# KONFIGURATION - Alle wichtigen Parameter für den Torsionsprüfstand
# ===========================================================================================

# DEMO-MODUS (True = Simulation ohne Hardware, False = Echte Hardware)
DEMO_MODE = True

# DF-30 Drehmoment-Sensor Konfiguration
# Messbereich: ±20 Nm
# Messverstärker Ausgang: ±10V
TORQUE_SENSOR_MAX_NM = 20.0  # Maximales Drehmoment [Nm]
TORQUE_SENSOR_MAX_VOLTAGE = 10.0  # Maximale Spannung [V]
TORQUE_SCALE = TORQUE_SENSOR_MAX_NM / TORQUE_SENSOR_MAX_VOLTAGE  # 2.0 Nm/V

# NI-6000 DAQ-Konfiguration
DAQ_CHANNEL_TORQUE = "Dev1/ai0"  # DAQ-Kanal für Drehmomentmessung
DAQ_CHANNEL_ANGLE = "Dev1/ai1"  # DAQ-Kanal für Winkelmessung (SSI-Encoder via Motrona)
DAQ_VOLTAGE_RANGE = 10.0  # ±10V Messbereich

# SSI-Encoder & Motrona Konverter Konfiguration
# Encoder: RS Components RSA 58E SSI (13 Bit Single-Turn, 12 Bit Multi-Turn)
# Konverter: motrona 7386.5010 (SSI zu 0-10V Analog)
ANGLE_MEASUREMENT_SOURCE = "daq"  # "daq" = NI-6000 Messung, "motor" = Motor-Controller (Legacy)
ANGLE_ENCODER_MODE = "single_turn"  # "single_turn" = 0-360° mit Software-Unwrap, "multi_turn" = Multi-Turn (falls verfügbar)

# Motrona Analog-Ausgang Mapping: 0V = 0°, 10V = 360°
ANGLE_VOLTAGE_MIN = 0.0  # Minimale Spannung [V]
ANGLE_VOLTAGE_MAX = 10.0  # Maximale Spannung [V]
ANGLE_MIN_DEG = 0.0  # Minimaler Winkel [Grad]
ANGLE_MAX_DEG = 360.0  # Maximaler Winkel [Grad]
ANGLE_WRAP_THRESHOLD = 180.0  # Schwellwert für Wrap-Detection [Grad]

# Mess-Konfiguration
MEASUREMENT_INTERVAL = 100  # Messintervall in Millisekunden (10 Hz = 100ms)
DEFAULT_SAMPLE_NAME = "TorsionTest"  # Standard-Probenname

# Motor-Controller Konfiguration
# Wähle Motor-Typ: "nanotec" oder "trinamic"
MOTOR_TYPE = "nanotec"  # "nanotec" = Nanotec mit NanoLib, "trinamic" = Trinamic Steprocker

# Nanotec-spezifische Konfiguration
NANOTEC_BUS_HARDWARE = "ixxat"  # Bus-Hardware: "ixxat", "kvaser", "socketcan"

# Trinamic-spezifische Konfiguration
TRINAMIC_COM_PORT = "COM3"  # COM-Port des Trinamic Steprocker
TRINAMIC_MOTOR_ID = 0  # Motor ID

# Motor-Parameter (Standardwerte)
DEFAULT_MAX_ANGLE = 360.0  # Standard maximaler Winkel [Grad]
DEFAULT_MAX_TORQUE = 15.0  # Standard maximales Drehmoment [Nm]
DEFAULT_MAX_VELOCITY = 10.0  # Standard Geschwindigkeit [Grad/s] (+ = Uhrzeiger, - = Gegen Uhrzeiger)

# GUI-Konfiguration
SYSTEM_NAME = "Torsions Test Stand - DF-30 Sensor"

# ===========================================================================================
# HAUPTPROGRAMM - GUI und Steuerungslogik
# ===========================================================================================


class MainWindow(QMainWindow):
    """
    Hauptfenster-Klasse für den Torsionsprüfstand.

    Diese Klasse verwaltet die gesamte GUI, Hardware-Kommunikation und Messlogik.
    Sie erbt von QMainWindow (PyQt6) und lädt die grafische Oberfläche aus einer
    .ui-Datei, die mit dem Qt Designer erstellt wurde.

    Hauptaufgaben:
    --------------
    1. GUI initialisieren und darstellen
    2. Hardware-Objekte erstellen (DAQ, Motor-Controller)
    3. Messungen durchführen und Daten speichern
    4. Live-Graph aktualisieren
    5. Benutzerinteraktionen verarbeiten

    Wichtige Attribute:
    -------------------
    - nidaqmx_task: Verbindung zum NI-6000 DAQ
    - motor_controller: Verbindung zum Schrittmotor
    - is_process_running: Flag ob Messung aktiv ist
    - turn_counter: Zählt Umdrehungen (für Single-Turn Encoder)
    - torque_data, angle_data: Listen für Graph-Darstellung
    """

    def __init__(self) -> None:
        """
        Konstruktor - Wird beim Programmstart automatisch aufgerufen.

        Ablauf:
        -------
        1. GUI-Datei laden (torsions_test_stand.ui)
        2. Dark-Mode Stylesheet anwenden
        3. Fenster zentrieren und Titel setzen
        4. Alle Variablen initialisieren
        5. Logger für Statusmeldungen einrichten
        6. Demo-LED setzen (grün/rot)
        7. Button-Events verbinden
        8. Graph-Widget erstellen
        9. Standardwerte für Parameter laden

        WICHTIG:
        --------
        Diese Funktion sollte NICHT verändert werden, außer Sie wissen
        genau, was Sie tun. Die Reihenfolge der Initialisierung ist wichtig!
        """
        super().__init__()

        # --- Basisverzeichnisse und GUI laden ---
        self.base_dir = os.getcwd()  # Aktuelles Arbeitsverzeichnis
        ui_file = r"src/gui/torsions_test_stand.ui"  # Pfad zur GUI-Datei
        uic.loadUi(ui_file, self)  # Lädt alle Buttons, Labels, etc. aus der .ui-Datei

        # --- Stylesheet für GUI laden ---
        # Erzeugt das dunkle Theme (Dark Mode)
        self.setStyleSheet(get_dark_stylesheet())

        # --- Fenster konfigurieren ---
        # Zentriert das Fenster auf dem Bildschirm
        self.move(self.screen().geometry().center() - self.frameGeometry().center())
        self.setWindowTitle(SYSTEM_NAME)  # Setzt Fenstertitel
        self.labelSystemName.setText(SYSTEM_NAME)  # Zeigt System-Name in GUI

        # Initialisiere Klassenvariablen
        self.init_class_attributes()

        # --- Logger initialisieren ---
        # Richtet das Logging-System ein (Statusmeldungen im Text-Bereich)
        self.setup_Logger()
        self.logger.info("Application started")
        self.logger.info(f"Demo-Modus: {'AKTIV' if DEMO_MODE else 'INAKTIV'}")

        # --- Demo-LED Status setzen ---
        # Zeigt grüne LED im Demo-Modus, rote LED bei echter Hardware
        self.update_demo_led_status()

        # --- GUI-Elemente und Events verbinden ---
        # Verbindet Buttons mit ihren Funktionen (z.B. "Start" → start_measurement)
        self.connectEvents()

        # --- Graph Widget initialisieren ---
        # Erstellt den Live-Graph für Torque vs. Angle
        self.setup_torque_graph_widget()

        # --- Parameter initialisieren ---
        # Lädt Standardwerte in die Eingabefelder
        self.init_parameters()

    def init_class_attributes(self) -> None:
        """
        Initialisiert alle Klassenvariablen für den Torsionsprüfstand.

        Diese Funktion wird VOR der GUI-Initialisierung aufgerufen und erstellt
        alle notwendigen Variablen mit ihren Startwerten.

        Variablen-Kategorien:
        ---------------------
        1. Status-Flags:
           - is_process_running: True während einer Messung läuft
           - are_instruments_initialized: True wenn Hardware bereit ist

        2. Hardware-Objekte:
           - nidaqmx_task: Verbindung zum NI-6000 DAQ (Torque + Angle)
           - motor_controller: Verbindung zum Schrittmotor
           - measurement_timer: Timer für periodische Messungen (alle 100ms)

        3. Mess-Parameter:
           - max_angle_value: Maximaler Winkel bevor Stopp [Grad]
           - max_torque_value: Maximales Drehmoment bevor Stopp [Nm]
           - max_velocity_value: Motor-Geschwindigkeit [Grad/s]

        4. Unwrap-Logik (für Single-Turn Encoder):
           - prev_angle_deg: Vorheriger Winkelwert für Vergleich
           - turn_counter: Anzahl kompletter Umdrehungen
           - angle_continuous_deg: Kontinuierlicher Winkel über 360° hinaus

        5. Datenspeicherung:
           - torque_data: Liste aller gemessenen Drehmomente
           - angle_data: Liste aller gemessenen Winkel
           - project_dir: Hauptordner für Messdaten
           - measurement_dir: Unterordner für aktuelle Messung

        WICHTIG:
        --------
        Diese Variablen werden im gesamten Programm verwendet.
        Änderungen hier können unerwartete Fehler verursachen!
        """
        # --- Status-Flags (zeigen aktuellen Programmzustand) ---
        self.block_parameter_signals = False  # Blockiert Parameter-Updates während Initialisierung
        self.grp_box_connected = False  # Flag ob GUI-Events bereits verbunden sind
        self.is_process_running = False  # True = Messung läuft gerade
        self.are_instruments_initialized = False  # True = Hardware ist bereit

        # --- Proben-Identifikation ---
        self.sample_name = DEFAULT_SAMPLE_NAME  # Name der zu prüfenden Probe (z.B. "TorsionTest_001")

        # --- Dateipfade für Messdaten-Speicherung ---
        self.project_dir: str = ""  # Hauptordner (vom Benutzer gewählt)
        self.measurement_dir: str = ""  # Unterordner für diese Messung (automatisch erstellt)
        self.measurement_filename: str = ""  # Dateiname für Messdaten (.txt)

        # --- Hardware-Objekte (None = noch nicht initialisiert) ---
        self.nidaqmx_task: DAQmxTask = None  # NI-6000 DAQ für Torque + Angle Messung
        self.motor_controller: MotorControllerBase = None  # Schrittmotor (Nanotec oder Trinamic)
        self.measurement_timer: QTimer = None  # Timer für periodische Datenerfassung

        # --- Zeitmessung für Messung ---
        self.start_time_timestamp = None  # Startzeitpunkt der Messung (datetime Objekt)

        # --- Graph-Daten (werden während Messung gefüllt) ---
        self.torque_data = []  # Liste: [0.5, 1.2, 2.3, ...] in Nm
        self.angle_data = []  # Liste: [10, 20, 30, ...] in Grad

        # --- Parameter-Werte (werden bei GUI-Änderung aktualisiert) ---
        # Diese Werte werden in accept_parameter() aus den GUI-Feldern übernommen
        self.max_angle_value = DEFAULT_MAX_ANGLE  # Max Winkel [°] (z.B. 720° = 2 Umdrehungen)
        self.max_torque_value = DEFAULT_MAX_TORQUE  # Max Drehmoment [Nm] (z.B. 15 Nm)
        self.max_velocity_value = DEFAULT_MAX_VELOCITY  # Motor-Geschwindigkeit [°/s] (z.B. 10°/s)

        # --- Unwrap-Logik für Single-Turn Encoder (0-360° mit Umdrehungszähler) ---
        # Der SSI-Encoder gibt nur 0-360° aus. Bei 360° springt er zurück auf 0°.
        # Diese Variablen ermöglichen kontinuierliche Winkelmessung über mehrere Umdrehungen.
        self.prev_angle_deg = 0.0  # Vorheriger Winkelwert (zum Vergleich mit aktuellem)
        self.turn_counter = 0  # Umdrehungszähler: +1 bei 360°→0°, -1 bei 0°→360°
        self.angle_continuous_deg = 0.0  # Kontinuierlicher Winkel: z.B. 361°, 720°, -90° etc.
        self.angle_continuous_deg = 0.0  # Kontinuierlicher Winkel über mehrere Umdrehungen

    def closeEvent(self, event) -> None:
        """
        Wird automatisch aufgerufen, wenn das Programmfenster geschlossen wird.

        FUNKTION:
        ---------
        Sicheres Beenden des Programms mit Aufräumarbeiten:
        1. Stoppt laufende Messungen (falls aktiv)
        2. Deaktiviert Hardware und gibt Ressourcen frei
        3. Schließt alle offenen Verbindungen (DAQ, Motor)

        WARUM WICHTIG:
        --------------
        Ohne diese Funktion würden beim X-Klicken:
        - Laufende Messungen nicht gestoppt (Datenverlust!)
        - Motor weiterlaufen (Gefahr!)
        - DAQ-Verbindungen offen bleiben (blockiert andere Programme)
        - Speicher nicht freigegeben werden

        AUFRUF:
        -------
        Automatisch durch PyQt6 beim Schließen des Fensters
        (X-Button, Alt+F4, Programm beenden)

        HINWEIS FÜR TECHNIKER:
        ----------------------
        Diese Funktion sollte NICHT manuell verändert werden!
        Sie ist Teil des PyQt6-Lebenszyklus und kritisch für
        sicheres Beenden.
        """
        self.logger.info("=" * 60)
        self.logger.info("Programm wird beendet...")
        self.logger.info("=" * 60)

        # Schritt 1: Stoppe laufende Messung (falls aktiv)
        if self.is_process_running:
            self.logger.info("→ Stoppe laufende Messung...")
            self.stop_measurement()

        # Schritt 2: Deaktiviere Hardware (falls initialisiert)
        if self.are_instruments_initialized:
            self.logger.info("→ Deaktiviere Hardware...")
            self.deactivate_hardware()

        self.logger.info("✓ Programm sauber beendet")

        # Rufe Original-closeEvent auf (wichtig für PyQt6!)
        super().closeEvent(event)

    def connectEvents(self) -> None:
        """
        Verbindet GUI-Buttons mit ihren Funktionen (Event-Handling).

        FUNKTION:
        ---------
        Diese Funktion "verkabelt" die Buttons in der GUI mit den
        entsprechenden Python-Funktionen. Wenn ein Button geklickt wird,
        wird die zugewiesene Funktion ausgeführt.

        BUTTON-ZUORDNUNG:
        -----------------
        btn_select_proj_folder → select_project_directory()
          Öffnet Dialog zur Ordnerauswahl

        start_meas_btn → start_measurement()
          Startet eine neue Messung

        stop_meas_btn → stop_measurement()
          Stoppt die laufende Messung

        manual_trig_btn → measure_manual()
          Führt eine einzelne manuelle Messung durch

        activate_hardware_btn → activate_hardware()
          Initialisiert NI-6000 DAQ und Motor

        deactivate_hardware_btn → deactivate_hardware()
          Trennt Verbindungen zur Hardware

        home_pos_btn → home_position()
          Fährt Motor auf 0° und kalibriert

        smp_name (Textfeld) → update_sample_name()
          Aktualisiert Probenname (bei Enter oder Focus-Verlust)

        WICHTIG:
        --------
        Diese Funktion wird nur EINMAL beim Programmstart aufgerufen!
        Danach sind alle Buttons "live" und reagieren auf Klicks.

        SYNTAX:
        -------
        button.clicked.connect(funktion)
          - button: GUI-Element aus der .ui-Datei
          - clicked: Signal (wird bei Klick ausgelöst)
          - connect: Verbindet Signal mit Funktion
          - funktion: Python-Funktion (ohne Klammern!)

        AUFRUF:
        -------
        Automatisch beim Programmstart durch __init__()
        """
        # Projektordner-Auswahl Button
        self.btn_select_proj_folder.clicked.connect(self.select_project_directory)

        # Messungs-Steuerung Buttons
        self.start_meas_btn.clicked.connect(self.start_measurement)
        self.stop_meas_btn.clicked.connect(self.stop_measurement)
        self.manual_trig_btn.clicked.connect(self.measure_manual)

        # Hardware-Steuerung Buttons
        self.activate_hardware_btn.clicked.connect(self.activate_hardware)
        self.deactivate_hardware_btn.clicked.connect(self.deactivate_hardware)
        self.home_pos_btn.clicked.connect(self.home_position)

        # Probenname Eingabefeld (2 Events: Enter-Taste und Focus-Verlust)
        self.smp_name.returnPressed.connect(self.update_sample_name)  # Enter gedrückt
        self.smp_name.focusOutEvent = lambda event: (  # Feld verlassen (Tab, Klick woanders)
            self.update_sample_name(),  # Aktualisiere Namen
            QtWidgets.QLineEdit.focusOutEvent(self.smp_name, event),  # Original-Event aufrufen
        )

    def connect_groupbox_signals(self) -> None:
        """
        Verbindet Parameter-Eingabefelder mit Überwachungsfunktionen.

        FUNKTION:
        ---------
        Sucht automatisch ALLE Eingabefelder in GroupBoxen und verbindet
        sie mit accept_parameter(). Dadurch werden Parameteränderungen
        sofort erkannt und verarbeitet.

        ÜBERWACHTE GUI-ELEMENTE:
        ------------------------
        - QLineEdit: Textfelder (z.B. Max Angle, Max Torque, Max Velocity)
        - QComboBox: Dropdown-Listen
        - QCheckBox: Kontrollkästchen

        WAS PASSIERT BEI ÄNDERUNG:
        --------------------------
        1. Benutzer ändert Wert in Eingabefeld
        2. Signal wird ausgelöst (editingFinished, currentTextChanged, etc.)
        3. check_parameter_change() oder accept_parameter() wird aufgerufen
        4. Wert wird validiert und in Instance-Variablen gespeichert

        BEISPIEL:
        ---------
        Benutzer gibt "500" in Max Angle ein:
          1. Feld verlassen → editingFinished Signal
          2. check_parameter_change() wird aufgerufen
          3. Validierung: Leer? Komma durch Punkt ersetzen?
          4. accept_parameter() wird aufgerufen
          5. self.max_angle_value = 500.0 gespeichert

        WARUM "old_text"?
        -----------------
        Jedes Feld bekommt ein Attribut "old_text" mit dem aktuellen Wert.
        Dadurch kann erkannt werden, ob sich der Wert wirklich geändert hat.

        AUFRUF:
        -------
        Automatisch beim Programmstart durch init_parameters()
        (nur einmal, dann ist self.grp_box_connected = True)
        """
        # Durchsuche alle GroupBox-Widgets in der GUI
        for group_box in self.findChildren(QGroupBox):
            # QLineEdit (Textfelder): Signale verbinden
            for line_edit in group_box.findChildren(QLineEdit):
                line_edit.old_text = line_edit.text()  # Aktuellen Wert speichern
                line_edit.editingFinished.connect(lambda le=line_edit: self.check_parameter_change(le))

            # QComboBox (Dropdown-Listen): Signale verbinden
            for combo_box in group_box.findChildren(QComboBox):
                combo_box.currentTextChanged.connect(self.accept_parameter)

            # QCheckBox (Kontrollkästchen): Signale verbinden
            for check_box in group_box.findChildren(QtWidgets.QCheckBox):
                check_box.stateChanged.connect(self.accept_parameter)

        # Flag setzen: Verbindungen sind hergestellt
        self.grp_box_connected = True

    def safe_float(self, text: str, default: float = 0.0) -> float:
        """
        Sichere Konvertierung von String (Texteingabe) zu Float (Dezimalzahl).

        PROBLEM:
        --------
        Benutzereingaben sind immer Text (String). Für Berechnungen
        brauchen wir aber Zahlen (Float). Einfache Konvertierung kann
        fehlschlagen bei ungültigen Eingaben.

        LÖSUNG:
        -------
        Diese Funktion versucht die Konvertierung und gibt bei Fehler
        einen Standardwert zurück (statt Programm-Absturz).

        FEATURES:
        ---------
        ✓ Entfernt Leerzeichen (z.B. " 123 " → "123")
        ✓ Ersetzt Komma durch Punkt (z.B. "1,5" → "1.5")
        ✓ Bei Fehler: Standardwert + Warnung im Log

        BEISPIELE:
        ----------
        Input         | Output    | Erklärung
        --------------|-----------|--------------------------------
        "123"         | 123.0     | Normale Zahl
        "12.5"        | 12.5      | Dezimalzahl mit Punkt
        "12,5"        | 12.5      | Komma wird zu Punkt
        " 45 "        | 45.0      | Leerzeichen entfernt
        "abc"         | 0.0       | Ungültig → Standard (0.0)
        ""            | 0.0       | Leer → Standard (0.0)

        PARAMETER:
        ----------
        text : str
            Eingabetext vom Benutzer (z.B. aus GUI-Feld)
        default : float
            Wert der zurückgegeben wird bei Fehler (Standard: 0.0)

        RÜCKGABE:
        ---------
        float
            Konvertierte Zahl oder Standardwert bei Fehler

        VERWENDUNG:
        -----------
        angle = self.safe_float(self.max_angle.text(), DEFAULT_MAX_ANGLE)
        """
        try:
            clean_text = text.strip()  # Leerzeichen entfernen
            clean_text = clean_text.replace(",", ".")  # Komma → Punkt
            return float(clean_text)  # String zu Float konvertieren
        except (ValueError, TypeError):
            # ValueError: Text kann nicht zu Zahl konvertiert werden
            # TypeError: text ist None oder falscher Typ
            self.logger.warning(f"⚠ Konvertierung zu Float fehlgeschlagen: '{text}' → Standard: {default}")
            return default

    def safe_int(self, text: str, default: int = 0) -> int:
        """
        Sichere Konvertierung von String (Texteingabe) zu Integer (Ganzzahl).

        ÄHNLICH WIE safe_float(), aber für Ganzzahlen ohne Nachkommastellen.

        UNTERSCHIED ZU safe_float:
        --------------------------
        - Rückgabe ist Integer (keine Nachkommastellen)
        - "12.7" wird zu 12 (Nachkommastelle abgeschnitten)

        BEISPIELE:
        ----------
        Input         | Output    | Erklärung
        --------------|-----------|--------------------------------
        "123"         | 123       | Normale Ganzzahl
        "12.7"        | 12        | Wird zu int (Nachkomma weg)
        "12,7"        | 12        | Komma → Punkt, dann zu int
        " 45 "        | 45        | Leerzeichen entfernt
        "abc"         | 0         | Ungültig → Standard (0)

        PARAMETER:
        ----------
        text : str
            Eingabetext vom Benutzer
        default : int
            Wert der zurückgegeben wird bei Fehler (Standard: 0)

        RÜCKGABE:
        ---------
        int
            Konvertierte Ganzzahl oder Standardwert bei Fehler

        VERWENDUNG:
        -----------
        count = self.safe_int(self.sample_count.text(), 1)
        """
        try:
            clean_text = text.strip()  # Leerzeichen entfernen
            clean_text = clean_text.replace(",", ".")  # Komma → Punkt
            return int(float(clean_text))  # String → Float → Int
        except (ValueError, TypeError):
            self.logger.warning(f"⚠ Konvertierung zu Integer fehlgeschlagen: '{text}' → Standard: {default}")
            return default

    def check_parameter_change(self, source):
        """
        Verarbeitet und validiert Benutzereingaben in Textfeldern.

        FUNKTION:
        ---------
        Diese Funktion wird automatisch aufgerufen, wenn ein Benutzer
        ein Eingabefeld (QLineEdit) verlässt. Sie überprüft die Eingabe
        und korrigiert häufige Fehler automatisch.

        VALIDIERUNGEN:
        --------------
        1. Leeres Feld → Wird auf "0" gesetzt
        2. Komma (,) → Wird durch Punkt (.) ersetzt
        3. Leerzeichen → Werden entfernt (automatisch durch strip())

        ABLAUF:
        -------
        1. Prüfe ob Quelle ein Textfeld ist
        2. Lese aktuellen Text aus
        3. Logge Änderung
        4. Falls leer → Setze auf "0"
        5. Falls Komma → Ersetze durch Punkt
        6. Rufe accept_parameter() auf (speichert Wert)

        BEISPIEL:
        ---------
        Benutzer gibt "12,5" in Max Angle ein und drückt Enter:
          1. check_parameter_change() wird aufgerufen
          2. Erkennt Komma
          3. Ersetzt durch "12.5"
          4. Aktualisiert GUI-Feld
          5. Loggt: "Komma ersetzt"
          6. Ruft accept_parameter() auf
          7. Wert wird in self.max_angle_value gespeichert

        PARAMETER:
        ----------
        source : QLineEdit
            Das Textfeld das geändert wurde

        AUFRUF:
        -------
        Automatisch durch connect_groupbox_signals()
        bei editingFinished Signal (Enter oder Tab)
        """
        # Sicherheitsprüfung: Ist es ein Textfeld?
        if not isinstance(source, QtWidgets.QLineEdit):
            return  # Abbruch wenn falscher Widget-Typ

        # Ermittle Namen des Feldes (für Logging)
        sender_name = self.sender().objectName() if self.sender() else "Unknown"

        # Lese aktuellen Text (ohne Leerzeichen)
        current_text = source.text().strip()

        # Logge Änderung für Nachverfolgung
        self.logger.info(f"Parameter '{sender_name}' geändert zu: '{current_text}'")

        # ─────────────────────────────────────────────
        # VALIDIERUNG 1: Leeres Feld auf "0" setzen
        # ─────────────────────────────────────────────
        if not current_text:  # Leer oder nur Leerzeichen?
            source.setText("0")  # Standardwert einsetzen
            self.logger.info(f"  → Leeres Feld '{sender_name}' auf '0' gesetzt")

        # ─────────────────────────────────────────────
        # VALIDIERUNG 2: Komma durch Punkt ersetzen
        # ─────────────────────────────────────────────
        if "," in current_text:  # Enthält Text ein Komma?
            corrected_text = current_text.replace(",", ".")  # Ersetze durch Punkt
            source.setText(corrected_text)  # Aktualisiere GUI
            self.logger.info(f"  → Komma in '{sender_name}' durch Punkt ersetzt")

        # ─────────────────────────────────────────────
        # PARAMETER SPEICHERN
        # ─────────────────────────────────────────────
        # Rufe accept_parameter() auf, um den validierten
        # Wert in die entsprechende Instance-Variable zu speichern
        self.accept_parameter()

    def setup_Logger(self) -> None:
        """
        ╔═══════════════════════════════════════════════════════════════╗
        ║  LOGGER-SYSTEM INITIALISIERUNG                                ║
        ╚═══════════════════════════════════════════════════════════════╝

        Richtet das Logging-System ein für Anzeige in der GUI.

        FUNKTION:
        ---------
        Erstellt ein zentrales Logging-System das ALLE Programmteile
        nutzen können. Log-Nachrichten erscheinen im GUI-Textfeld
        (QTextEdit-Widget) mit farbiger Kennzeichnung.

        LOGGING-LEVELS (Wichtigkeitsstufen):
        -------------------------------------
        ✓ DEBUG   : Technische Details (normalerweise versteckt)
        ✓ INFO    : Normale Meldungen (z.B. "Hardware aktiviert")
        ✓ WARNING : Warnungen (z.B. "Ungültige Eingabe korrigiert")
        ✓ ERROR   : Fehler (z.B. "Motor nicht verbunden")
        ✓ CRITICAL: Kritische Fehler (Programmabsturz droht)

        WAS WIRD KONFIGURIERT:
        ----------------------
        1. Root Logger: Basis-Logger für gesamtes Programm
           - Level: INFO (zeigt INFO, WARNING, ERROR, CRITICAL)

        2. Formatter: Bestimmt Aussehen der Log-Zeilen
           Format: "Zeit  Level  Modul  Nachricht"
           Beispiel: "2024-10-27 14:23:15  INFO  main  Hardware aktiviert"

        3. GUI Handler: Leitet Logs zur GUI-Anzeige
           - Zeigt Logs im self.logger_textEdit Widget
           - Nutzt Farben (Rot=Error, Gelb=Warning, etc.)

        BEISPIEL LOG-OUTPUT:
        --------------------
        2024-10-27 14:23:15  INFO      main             Programm gestartet
        2024-10-27 14:23:16  INFO      DAQ              NI-6000 verbunden
        2024-10-27 14:23:17  WARNING   Motor            Position ungenau
        2024-10-27 14:23:18  ERROR     DAQ              Kanal ai0 nicht gefunden

        HINWEIS:
        --------
        - Alle Logs landen NUR in der GUI (keine Datei!)
        - Bei Programmstart ist das Log leer
        - Nutze self.logger.info("Text") um zu loggen

        AUFRUF:
        -------
        Einmalig in __init__() beim Programmstart
        """
        # ═════════════════════════════════════════════
        # 1. ROOT LOGGER KONFIGURIEREN
        # ═════════════════════════════════════════════
        root_logger = logging.getLogger()  # Basis-Logger holen
        root_logger.setLevel(logging.INFO)  # Alles ab INFO anzeigen

        # ═════════════════════════════════════════════
        # 2. FORMATTER ERSTELLEN (Format der Log-Zeilen)
        # ═════════════════════════════════════════════
        # WrappingFormatter: Spezielle Klasse für Zeilenumbruch bei langen Texten
        # Format-Elemente:
        #   %(asctime)s      → Zeitstempel (z.B. "2024-10-27 14:23:15")
        #   %(levelname)s    → Level-Name (INFO, WARNING, ERROR)
        #   %(name)s         → Logger-Name (MAIN, DAQ, Motor)
        #   %(message)s      → Die eigentliche Log-Nachricht
        # Zahlen (-32.24s): Spaltenbreite für einheitliche Formatierung
        formatter = WrappingFormatter("%(asctime)-32.24s  %(levelname)-16.16s %(name)-16.16s %(message)s")

        # ═════════════════════════════════════════════
        # 3. GUI HANDLER EINRICHTEN (Logs zur GUI)
        # ═════════════════════════════════════════════
        self.gui_handler = GuiLogger()  # Spezial-Handler für GUI-Anzeige
        self.gui_handler.logger_signal.connect(self.msg)  # Verbinde mit msg() Funktion
        self.gui_handler.setLevel(logging.INFO)  # Nur INFO und höher anzeigen
        self.gui_handler.setFormatter(formatter)  # Nutze definierten Formatter
        root_logger.addHandler(self.gui_handler)  # Handler zum Root-Logger hinzufügen

        # ═════════════════════════════════════════════
        # 4. EIGENEN LOGGER FÜR MAIN.PY ERSTELLEN
        # ═════════════════════════════════════════════
        self.logger = logging.getLogger("MAIN")  # Logger mit Namen "MAIN"
        self.logger.info("✓ Logger initialized")  # Erste Log-Nachricht

    def msg(self, msg="No message included", level=logging.INFO, name="Unknown") -> None:
        """
        ╔═══════════════════════════════════════════════════════════════╗
        ║  LOG-NACHRICHT IN GUI ANZEIGEN                                ║
        ╚═══════════════════════════════════════════════════════════════╝

        Zeigt Log-Nachrichten im GUI-Textfeld mit Farb-Codierung an.

        FUNKTION:
        ---------
        Diese Funktion ist das "Ziel" aller Log-Nachrichten. Sie wird
        automatisch von GuiLogger aufgerufen und zeigt die Nachricht
        im self.logger_textEdit Widget mit passender Farbe an.

        FARB-CODIERUNG:
        ---------------
        Level       | Farbe           | Verwendung
        ------------|-----------------|--------------------------------
        DEBUG       | Blau            | Technische Details
        INFO        | Weiß            | Normale Meldungen
        WARNING     | Gelb (#E6CF6A)  | Warnungen
        ERROR       | Orange (#FFAA00)| Fehler
        CRITICAL    | Rot             | Kritische Fehler

        NACHRICHTEN-FORMAT:
        -------------------
        Jede Log-Zeile enthält:
        - Zeitstempel (z.B. "2024-10-27 14:23:15")
        - Level (z.B. "INFO", "ERROR")
        - Modul-Name (z.B. "MAIN", "DAQ")
        - Nachricht (z.B. "Hardware aktiviert")

        BEISPIELE:
        ----------
        self.logger.info("Motor gestartet")
          → Weiße Nachricht: "14:23:15  INFO  MAIN  Motor gestartet"

        self.logger.warning("Grenzwert erreicht")
          → Gelbe Nachricht: "14:23:16  WARNING  MAIN  Grenzwert erreicht"

        self.logger.error("Verbindung verloren")
          → Orange Nachricht: "14:23:17  ERROR  MAIN  Verbindung verloren"

        PARAMETER:
        ----------
        msg : str
            Die anzuzeigende Nachricht
        level : int
            Log-Level (logging.INFO, logging.WARNING, etc.)
        name : str
            Name des Loggers (z.B. "MAIN", "DAQ")

        AUFRUF:
        -------
        Automatisch durch GuiLogger.emit() Signal
        (wird von logger.info(), logger.warning(), etc. getriggert)

        HINWEIS:
        --------
        - Neue Nachrichten werden UNTEN angefügt
        - Textfeld scrollt automatisch nach unten
        - Alte Nachrichten bleiben sichtbar (keine Auto-Löschung)
        """
        # ─────────────────────────────────────────────
        # FARBE BASIEREND AUF LOG-LEVEL BESTIMMEN
        # ─────────────────────────────────────────────
        if level == logging.DEBUG:
            color = "blue"
        elif level == logging.INFO:
            color = "white"
        elif level == logging.WARNING:
            color = "#E6CF6A"
        elif level == logging.ERROR:
            color = "#FF5555"  # Orange-Rot für Fehler
        elif level == logging.CRITICAL:
            color = "purple"  # Lila für kritische Fehler
        else:
            color = "black"  # Fallback: Schwarz

        # ─────────────────────────────────────────────
        # NACHRICHT MIT FARBE IN GUI-TEXTFELD EINFÜGEN
        # ─────────────────────────────────────────────
        self.plainLog.setTextColor(QColor(color))  # Farbe setzen

        # Schriftgewicht: Fett bei WARNING oder höher, sonst Normal
        self.plainLog.setFontWeight(QFont.Weight.Bold if level >= logging.WARNING else QFont.Weight.Normal)

        self.plainLog.append(msg)  # Text anhängen (neue Zeile)
        self.plainLog.moveCursor(QTextCursor.MoveOperation.End)  # Zum Ende scrollen

    def setup_torque_graph_widget(self):
        """
        ╔═══════════════════════════════════════════════════════════════╗
        ║  GRAPH-WIDGET FÜR TORQUE VS. ANGLE ERSTELLEN                  ║
        ╚═══════════════════════════════════════════════════════════════╝

        Erstellt den Echtzeit-Graphen zur Darstellung von Torque vs. Angle.

        FUNKTION:
        ---------
        Initialisiert ein PyQtGraph-Widget das während der Messung
        live aktualisiert wird. Der Graph zeigt die charakteristische
        Torsions-Kurve (Drehmoment über Verdrehwinkel).

        GRAPH-AUFBAU:
        -------------
        - X-Achse: Angle (Winkel in Grad °)
        - Y-Achse: Torque (Drehmoment in Nm)
        - Kurve: Blaue Linie (#0077FF) mit Punkten
        - Hintergrund: Dunkelgrau (#262a32) für guten Kontrast
        - Gitter: Hilfslinien für bessere Lesbarkeit

        DARSTELLUNGS-ELEMENTE:
        ----------------------
        ✓ Titel: "Torque vs. Angle" (weiß, 12pt, fett)
        ✓ Y-Achse: "Torque [Nm]" (weiß, 13pt)
        ✓ X-Achse: "Angle [°]" (weiß, 13pt)
        ✓ Gitter: Weiße Hilfslinien (x & y)
        ✓ Kurve: Blaue Linie mit Datenpunkten
        ✓ Symbole: Kleine Kreise (4px) an jedem Messpunkt

        VERWENDETE EINSTELLUNGEN:
        -------------------------
        - pen=pg.mkPen(): Stift für Linie (Farbe, Dicke)
        - symbol="o": Kreissymbole an Datenpunkten
        - symbolBrush: Füllfarbe der Symbole
        - symbolSize: Größe der Symbole in Pixeln
        - setBackground(): Hintergrundfarbe
        - showGrid(): Gitter ein/aus

        TYPISCHE TORSIONSKURVE:
        -----------------------
        Torque
        [Nm] │
          20 │         ╱────── Plastische Verformung
             │       ╱
          15 │     ╱
             │   ╱  Elastischer Bereich (linear)
          10 │ ╱
             │╱
           0 └─────────────────────────────> Angle [°]
             0      90      180     270

        AUFRUF:
        -------
        Einmalig in __init__() beim Programmstart

        WICHTIG:
        --------
        - Graph wird in self.force_graph_frame eingebettet
        - Datenpunkte werden in measure() hinzugefügt
        - self.torque_curve.setData() aktualisiert den Graphen
        """
        # ═════════════════════════════════════════════
        # 1. LAYOUT IN FRAME ERSTELLEN
        # ═════════════════════════════════════════════
        graph_layout = QVBoxLayout(self.force_graph_frame)  # Vertikales Layout

        # ═════════════════════════════════════════════
        # 2. PLOT-WIDGET ERSTELLEN
        # ═════════════════════════════════════════════
        self.graph_widget = pg.PlotWidget()  # PyQtGraph Widget

        # ═════════════════════════════════════════════
        # 3. TITEL KONFIGURIEREN
        # ═════════════════════════════════════════════
        self.graph_widget.setTitle(
            "Torque vs. Angle",  # Titel-Text
            color="white",  # Schriftfarbe
            size="12pt",  # Schriftgröße
            bold=True,  # Fettdruck
        )

        # ═════════════════════════════════════════════
        # 4. ACHSEN BESCHRIFTEN UND FORMATIEREN
        # ═════════════════════════════════════════════
        # Y-Achse (vertikal): Torque in Nm
        self.graph_widget.setLabel(
            "left",  # Position (linke Seite)
            "Torque",  # Beschriftung
            units="Nm",  # Einheit
            color="white",  # Textfarbe
            **{"font-size": "13pt"},  # Schriftgröße
        )

        # X-Achse (horizontal): Angle in Grad
        self.graph_widget.setLabel(
            "bottom",  # Position (unten)
            "Angle",  # Beschriftung
            units="°",  # Einheit (Grad-Symbol)
            color="white",  # Textfarbe
            **{"font-size": "13pt"},
        )

        # ═════════════════════════════════════════════
        # 5. DARSTELLUNGS-OPTIONEN
        # ═════════════════════════════════════════════
        self.graph_widget.setBackground("#262a32")  # Dunkelgrauer Hintergrund
        self.graph_widget.showGrid(x=True, y=True)  # Gitter anzeigen

        # ═════════════════════════════════════════════
        # 6. KURVE FÜR MESSDATEN ERSTELLEN
        # ═════════════════════════════════════════════
        self.torque_curve = self.graph_widget.plot(
            pen=pg.mkPen(color="#0077FF", width=2),  # Blaue Linie, 2px dick
            symbol="o",  # Kreissymbole
            symbolBrush="#0077FF",  # Blaue Füllung
            symbolSize=4,  # 4 Pixel Durchmesser
            name="Torque vs. Angle",  # Name für Legende
        )

        # ═════════════════════════════════════════════
        # 7. ACHSEN-STYLING (Schriftart für Zahlen)
        # ═════════════════════════════════════════════
        self.graph_widget.getAxis("left").setStyle(tickFont=QFont("Arial", 10))  # Y-Achse
        self.graph_widget.getAxis("bottom").setStyle(tickFont=QFont("Arial", 10))  # X-Achse
        self.graph_widget.getAxis("left").setTextPen("w")  # Weiße Schrift (Y)
        self.graph_widget.getAxis("bottom").setTextPen("w")  # Weiße Schrift (X)

        # ═════════════════════════════════════════════
        # 8. WIDGET IN LAYOUT EINFÜGEN
        # ═════════════════════════════════════════════
        graph_layout.addWidget(self.graph_widget)  # Graph zum Frame hinzufügen

    # ════════════════════════════════════════════════════════════════════
    # PARAMETER FUNKTIONEN
    # ════════════════════════════════════════════════════════════════════

    def init_parameters(self) -> None:
        """
        ╔═══════════════════════════════════════════════════════════════╗
        ║  PARAMETER-INITIALISIERUNG MIT STANDARDWERTEN                 ║
        ╚═══════════════════════════════════════════════════════════════╝

        Setzt alle GUI-Parameter auf ihre Standardwerte beim Start.

        FUNKTION:
        ---------
        Füllt die GUI-Eingabefelder mit den in den Konstanten
        (DEFAULT_*) definierten Standardwerten. Diese Werte können
        dann vom Benutzer angepasst werden.

        WAS WIRD INITIALISIERT:
        -----------------------
        1. Sample Name (Probenbezeichnung)
           - Feld: self.smp_name
           - Standard: Aus self.sample_name (z.B. "Probe_001")

        2. Max Angle (Maximaler Verdrehwinkel)
           - Feld: self.max_angle
           - Standard: DEFAULT_MAX_ANGLE (z.B. 360°)

        3. Max Torque (Maximales Drehmoment - Abbruchkriterium)
           - Feld: self.max_torque
           - Standard: DEFAULT_MAX_TORQUE (z.B. 20 Nm)

        4. Max Velocity (Drehgeschwindigkeit)
           - Feld: self.max_velocity
           - Standard: DEFAULT_MAX_VELOCITY (z.B. 10°/s)

        ABLAUF:
        -------
        1. Sample-Name in GUI-Feld schreiben
        2. Alle Max-Werte (Angle, Torque, Velocity) in GUI schreiben
        3. Signalverbindungen herstellen (falls noch nicht geschehen)
        4. Erfolg loggen

        WICHTIG:
        --------
        - Diese Funktion setzt NUR die GUI-Felder
        - Die Instance-Variablen (self.max_angle_value, etc.)
          werden bereits in init_class_attributes() gesetzt
        - Signalverbindung erfolgt nur einmal (Flag: grp_box_connected)

        AUFRUF:
        -------
        Einmalig in __init__() nach GUI-Laden
        """
        # ─────────────────────────────────────────────
        # 1. SAMPLE-NAME SETZEN
        # ─────────────────────────────────────────────
        self.smp_name.setText(self.sample_name)  # Probenname in GUI-Feld

        # ─────────────────────────────────────────────
        # 2. MAX-WERTE IN GUI-FELDER SCHREIBEN
        # ─────────────────────────────────────────────
        self.max_angle.setText(str(self.max_angle_value))  # z.B. "360"
        self.max_torque.setText(str(self.max_torque_value))  # z.B. "20"
        self.max_velocity.setText(str(self.max_velocity_value))  # z.B. "10"

        # ─────────────────────────────────────────────
        # 3. GUI-SIGNALE VERBINDEN (falls nötig)
        # ─────────────────────────────────────────────
        if not self.grp_box_connected:
            self.connect_groupbox_signals()  # Verbindet Parameter-Felder mit accept_parameter()

        self.logger.info("✓ Parameter mit Standardwerten initialisiert")

    def update_demo_led_status(self) -> None:
        """
        ╔═══════════════════════════════════════════════════════════════╗
        ║  DEMO-LED STATUS AKTUALISIEREN                                ║
        ╚═══════════════════════════════════════════════════════════════╝

        Zeigt visuell an ob Demo-Modus oder echte Hardware aktiv ist.

        FUNKTION:
        ---------
        Setzt die Farbe der Demo-LED basierend auf der Konstante
        DEMO_MODE (True/False). Diese LED ist als Orientierung für
        den Benutzer gedacht.

        LED-BEDEUTUNG:
        --------------
        Farbe  | Bedeutung              | DEMO_MODE
        -------|------------------------|----------
        GRÜN   | Demo-Modus aktiv       | True
        ROT    | Echte Hardware aktiv   | False

        WARUM WICHTIG:
        --------------
        Im Demo-Modus:
        ✓ Keine echte Hardware nötig
        ✓ Simulierte Werte (für Tests/Entwicklung)
        ✓ Keine Gefahr für Hardware

        Mit echter Hardware:
        ⚠ Motor bewegt sich wirklich!
        ⚠ DAQ muss verbunden sein
        ⚠ Sensor muss kalibriert sein

        BEISPIEL:
        ---------
        Beim Programmstart (DEMO_MODE = True):
          → LED wird GRÜN
          → Log: "Demo-LED: GRÜN (Demo-Modus aktiv)"

        Nach Umstellung auf Hardware (DEMO_MODE = False):
          → LED wird ROT
          → Log: "Demo-LED: ROT (Echte Hardware)"

        AUFRUF:
        -------
        Einmalig in __init__() beim Programmstart

        HINWEIS FÜR TECHNIKER:
        ----------------------
        - DEMO_MODE Konstante steht ganz oben in main.py
        - Zum Ändern: DEMO_MODE = False setzen und neu starten
        - LED ist nur visuelle Anzeige (ändert keine Funktion)
        """
        # ─────────────────────────────────────────────
        # FARBE BASIEREND AUF DEMO_MODE SETZEN
        # ─────────────────────────────────────────────
        if DEMO_MODE:
            # ═════════════════════════════════════════
            # DEMO-MODUS: Grüne LED
            # ═════════════════════════════════════════
            self.demo_led.setStyleSheet(
                "background-color: green; "  # Grüne Füllung
                "border-radius: 12px; "  # Runde Form (24px Durchmesser)
                "border: 2px solid black;"  # Schwarzer Rand
            )
            self.logger.info("🟢 Demo-LED: GRÜN (Demo-Modus aktiv)")
        else:
            # ═════════════════════════════════════════
            # HARDWARE-MODUS: Rote LED
            # ═════════════════════════════════════════
            self.demo_led.setStyleSheet("background-color: red; border-radius: 12px; border: 2px solid black;")
            self.logger.info("🔴 Demo-LED: ROT (Echte Hardware)")

    def accept_parameter(self) -> None:
        """
        ╔═══════════════════════════════════════════════════════════════╗
        ║  PARAMETER AKZEPTIEREN UND ÜBERNEHMEN                         ║
        ╚═══════════════════════════════════════════════════════════════╝

        Übernimmt geänderte GUI-Werte direkt in Instance-Variablen.

        FUNKTION:
        ---------
        Diese Funktion wird automatisch aufgerufen wenn der Benutzer
        einen Parameter in der GUI ändert. Sie liest die Werte aus
        den GUI-Feldern und speichert sie in Instance-Variablen für
        spätere Verwendung (z.B. in measure(), activate_hardware()).

        VERARBEITUNG:
        -------------
        Für jeden Parameter:
        1. GUI-Feld auslesen (als String)
        2. Mit safe_float() zu Zahl konvertieren
        3. In Instance-Variable speichern
        4. Bei Fehler: Standardwert verwenden

        PARAMETER-MAPPING:
        ------------------
        GUI-Feld          | Instance-Variable    | Standard
        ------------------|----------------------|------------------
        max_angle         | max_angle_value      | DEFAULT_MAX_ANGLE
        max_torque        | max_torque_value     | DEFAULT_MAX_TORQUE
        max_velocity      | max_velocity_value   | DEFAULT_MAX_VELOCITY

        BEISPIEL-ABLAUF:
        ----------------
        1. Benutzer ändert "Max Angle" von "360" auf "180"
        2. Drückt Enter → editingFinished Signal
        3. check_parameter_change() validiert Eingabe
        4. accept_parameter() wird aufgerufen:
           - Liest "180" aus self.max_angle.text()
           - Konvertiert zu float: 180.0
           - Speichert in self.max_angle_value
        5. Wert steht für nächste Messung bereit!

        AUFRUF:
        -------
        Automatisch durch:
        - check_parameter_change() (nach Validierung)
        - QComboBox.currentTextChanged Signal
        - QCheckBox.stateChanged Signal

        SIGNAL-BLOCKING:
        ----------------
        Die Funktion prüft self.block_parameter_signals:
        - True: Abbruch (verhindert Rekursion bei programmatischer Änderung)
        - False: Normale Verarbeitung

        WICHTIG:
        --------
        - Diese Funktion speichert nur Werte (keine Hardware-Aktion!)
        - Keine Validierung hier (bereits in check_parameter_change())
        - Debug-Log zeigt alle übernommenen Werte
        """
        # ─────────────────────────────────────────────
        # SIGNAL-BLOCKING PRÜFEN
        # ─────────────────────────────────────────────
        if getattr(self, "block_parameter_signals", False):
            return  # Abbruch wenn Signale blockiert (verhindert Endlos-Schleife)

        # ─────────────────────────────────────────────
        # WERTE AUS GUI-FELDERN LESEN UND SPEICHERN
        # ─────────────────────────────────────────────
        # Max Angle (Maximaler Verdrehwinkel)
        self.max_angle_value = self.safe_float(
            self.max_angle.text(),  # GUI-Feld auslesen
            DEFAULT_MAX_ANGLE,  # Fallback bei Fehler
        )

        # Max Torque (Drehmoment-Grenze)
        self.max_torque_value = self.safe_float(self.max_torque.text(), DEFAULT_MAX_TORQUE)

        # Max Velocity (Drehgeschwindigkeit)
        self.max_velocity_value = self.safe_float(self.max_velocity.text(), DEFAULT_MAX_VELOCITY)

        # ─────────────────────────────────────────────
        # DEBUG-LOG: Alle übernommenen Werte anzeigen
        # ─────────────────────────────────────────────
        self.logger.debug(
            f"✓ Parameter akzeptiert - Angle: {self.max_angle_value}°, Torque: {self.max_torque_value} Nm, Velocity: {self.max_velocity_value}°/s"
        )

    def unwrap_angle(self, angle_now: float) -> float:
        """
        ╔═══════════════════════════════════════════════════════════════════════╗
        ║  UNWRAP-LOGIK für Single-Turn Encoder (0-360°)                        ║
        ║  Erkennt Umdrehungen und berechnet kontinuierlichen Winkel            ║
        ╚═══════════════════════════════════════════════════════════════════════╝

        PROBLEM:
        --------
        Der SSI-Encoder gibt nur 0-360° aus. Bei einer kompletten Umdrehung
        springt der Wert von 360° zurück auf 0° (oder umgekehrt).

        Beispiel:
          Zeit  | Rohwinkel | Problem
          ------|-----------|----------------------------------
          0.0s  | 350°      | Normal
          0.1s  | 358°      | Normal
          0.2s  | 5°        | SPRUNG! (hat nicht rückwärts gedreht!)
          0.3s  | 12°       | Normal (eigentlich bei 372°)

        LÖSUNG:
        -------
        Diese Funktion erkennt den Sprung und zählt die Umdrehungen:
        - Vorwärts (im Uhrzeigersinn): turn_counter erhöhen
        - Rückwärts (gegen Uhrzeigersinn): turn_counter verringern
        - Kontinuierlicher Winkel = Rohwinkel + (360° × Umdrehungen)

        FUNKTIONSWEISE:
        ---------------
        1. Berechne delta = aktueller_winkel - vorheriger_winkel
        2. Wenn delta < -180° → Vorwärts-Wrap erkannt (360°→0°) → counter++
        3. Wenn delta > +180° → Rückwärts-Wrap erkannt (0°→360°) → counter--
        4. Berechne kontinuierlichen Winkel
        5. Speichere aktuellen Winkel für nächsten Vergleich

        BEISPIELE:
        ----------
        Vorwärts (im Uhrzeigersinn):
          prev=359°, now=1°   → delta=-358° (< -180°) → counter: 0→1
          Ergebnis: 1° + (360°×1) = 361°  ✓

        Rückwärts (gegen Uhrzeigersinn):
          prev=1°, now=359°   → delta=+358° (> +180°) → counter: 0→-1
          Ergebnis: 359° + (360°×-1) = -1°  ✓

        Normale Bewegung:
          prev=100°, now=110° → delta=+10° (-180° < delta < +180°)
          Ergebnis: 110° + (360°×0) = 110°  ✓

        PARAMETER:
        ----------
        angle_now : float
            Aktueller Rohwinkel vom Encoder [0-360°]
            Beispiel: 5.2° oder 359.8°

        RÜCKGABE:
        ---------
        float
            Kontinuierlicher Winkel (kann jeden Wert haben)
            Beispiele: 10°, 361°, 720°, -90°, etc.

        WICHTIG:
        --------
        - Diese Funktion muss bei JEDER Messung aufgerufen werden!
        - Funktioniert nur bei kontinuierlicher Abtastung (kein Ausfall)
        - Bei zu schneller Drehung kann Wrap übersehen werden
          (wenn delta > 180° bei normaler Bewegung)
        """
        # Multi-Turn Modus: Encoder gibt bereits absoluten Winkel
        # → Keine Unwrap-Logik nötig
        if ANGLE_ENCODER_MODE == "multi_turn":
            return angle_now

        # ─────────────────────────────────────────────────────────
        # Single-Turn Modus: Wrap-Detection durchführen
        # ─────────────────────────────────────────────────────────

        # Schritt 1: Berechne Differenz zum vorherigen Wert
        delta = angle_now - self.prev_angle_deg

        # Beispiel: prev=359°, now=1° → delta = 1-359 = -358°
        # Beispiel: prev=100°, now=110° → delta = 110-100 = +10°

        # Schritt 2: Prüfe ob VORWÄRTS-Wrap (360° → 0°)
        # Delta ist stark negativ → Drehung im Uhrzeigersinn über 360° hinaus
        if delta < -ANGLE_WRAP_THRESHOLD:  # ANGLE_WRAP_THRESHOLD = 180°
            self.turn_counter += 1  # Eine Umdrehung mehr im Uhrzeigersinn
            self.logger.debug(f"✓ Wrap erkannt: 360°→0° | Umdrehungen: {self.turn_counter} | Delta: {delta:.1f}°")

        # Schritt 3: Prüfe ob RÜCKWÄRTS-Wrap (0° → 360°)
        # Delta ist stark positiv → Drehung gegen Uhrzeigersinn über 0° hinaus
        elif delta > ANGLE_WRAP_THRESHOLD:
            self.turn_counter -= 1  # Eine Umdrehung weniger (rückwärts)
            self.logger.debug(f"✓ Wrap erkannt: 0°→360° | Umdrehungen: {self.turn_counter} | Delta: {delta:.1f}°")

        # Wenn delta zwischen -180° und +180°: Normale Bewegung, kein Wrap

        # Schritt 4: Berechne kontinuierlichen Winkel
        # Formel: aktueller_winkel + (360° pro Umdrehung × Anzahl Umdrehungen)
        self.angle_continuous_deg = angle_now + (360.0 * self.turn_counter)

        # Beispiele:
        #   turn_counter=0, angle_now=45°  → 45° + 0 = 45°
        #   turn_counter=1, angle_now=45°  → 45° + 360° = 405°
        #   turn_counter=2, angle_now=0°   → 0° + 720° = 720°
        #   turn_counter=-1, angle_now=270° → 270° - 360° = -90°

        # Schritt 5: Aktuellen Winkel speichern für nächsten Vergleich
        self.prev_angle_deg = angle_now

        # Schritt 6: Kontinuierlichen Winkel zurückgeben
        return self.angle_continuous_deg

    def reset_angle_unwrap(self) -> None:
        """
        Setzt die Unwrap-Logik zurück auf Startwerte.

        WANN AUFRUFEN:
        --------------
        - Vor jeder neuen Messung (Start Measurement)
        - Nach Home-Position (Kalibrierung)
        - Nach Hardware-Initialisierung

        WAS PASSIERT:
        -------------
        - Umdrehungszähler → 0
        - Vorheriger Winkel → 0°
        - Kontinuierlicher Winkel → 0°

        WARUM WICHTIG:
        --------------
        Ohne Reset würde der Umdrehungszähler von der vorherigen Messung
        weiter gezählt werden, was zu falschen Winkeln führt!

        Beispiel ohne Reset:
          Erste Messung endet bei 720° (2 Umdrehungen, counter=2)
          Zweite Messung startet → counter bleibt bei 2
          Erster Winkel 10° → 10° + 720° = 730° (FALSCH!)

        Beispiel mit Reset:
          Erste Messung endet bei 720° (counter=2)
          Reset → counter=0
          Zweite Messung startet → counter=0
          Erster Winkel 10° → 10° + 0° = 10° (RICHTIG!)
        """
        self.prev_angle_deg = 0.0  # Kein vorheriger Winkel mehr gespeichert
        self.turn_counter = 0  # Umdrehungszähler auf 0 zurücksetzen
        self.angle_continuous_deg = 0.0  # Kontinuierlicher Winkel auf 0
        self.logger.info("✓ Winkel-Unwrap zurückgesetzt (Turns: 0, Angle: 0°)")

    def update_sample_name(self) -> None:
        """
        Aktualisiert den Proben-Namen aus dem GUI-Eingabefeld.

        FUNKTION:
        ---------
        Liest den Text aus dem Eingabefeld "smp_name" und speichert ihn
        in self.sample_name. Dieser Name wird für:
        - Ordnername der Messung (z.B. "20251027_143000_MeinePro be")
        - Dateinamen der Messdaten
        - Header in der Messdatei

        SICHERHEIT:
        -----------
        Kann nur geändert werden, wenn KEINE Messung läuft!
        Verhindert, dass während einer laufenden Messung der Name
        gewechselt wird.

        AUFRUF:
        -------
        - Automatisch wenn Benutzer Enter im Eingabefeld drückt
        - Automatisch wenn Benutzer Eingabefeld verlässt (focusOut)
        """
        if not self.is_process_running:  # Nur wenn keine Messung läuft
            self.sample_name = self.smp_name.text().strip()  # .strip() entfernt Leerzeichen
            self.logger.info(f"Sample-Name aktualisiert: {self.sample_name}")
        # Falls Messung läuft: Keine Änderung, stille Ignorierung

    def select_project_directory(self) -> None:
        """Ordnerauswahl für Projektverzeichnis."""
        dialog = QFileDialog()
        options = dialog.options()

        start_path = self.project_dir if self.project_dir else os.getcwd()
        folder = QFileDialog.getExistingDirectory(self, "Select Project Directory", start_path, options=options)

        if folder:
            self.project_dir = folder
            self.proj_dir.setText(self.project_dir)
            self.logger.info(f"Projektverzeichnis ausgewählt: {self.project_dir}")
        else:
            self.logger.warning("Kein Projektverzeichnis ausgewählt")

    def set_setup_controls_enabled(self, enabled: bool):
        """
        Aktiviert oder deaktiviert Setup-Eingabefelder.
        """
        try:
            setup_widgets = []

            # Suche GroupBoxen mit "setup" im Namen
            for group_box in self.findChildren(QGroupBox):
                if "setup" in group_box.objectName().lower() or "Setup" in group_box.title():
                    setup_widgets.append(group_box)
                    for widget in group_box.findChildren(QtWidgets.QWidget):
                        setup_widgets.append(widget)

            # Spezifische Widgets
            control_widgets = [
                getattr(self, "max_angle", None),
                getattr(self, "max_torque", None),
                getattr(self, "max_velocity", None),
                getattr(self, "btn_select_proj_folder", None),
                getattr(self, "start_meas_btn", None),
                getattr(self, "manual_trig_btn", None),
                getattr(self, "activate_hardware_btn", None),
                getattr(self, "deactivate_hardware_btn", None),
                getattr(self, "home_pos_btn", None),
                getattr(self, "smp_name", None),
            ]

            all_widgets = setup_widgets + control_widgets
            for widget in all_widgets:
                if widget is not None:
                    widget.setEnabled(enabled)

            # Stop Button immer verfügbar
            if hasattr(self, "stop_meas_btn"):
                self.stop_meas_btn.setEnabled(True)

            action_text = "enabled" if enabled else "disabled"
            self.logger.info(f"Setup controls {action_text}")

        except Exception as e:
            self.logger.error(f"Fehler beim Setzen der Control-Zustände: {e}")

    def reset_graph_data(self):
        """Setzt die Graph-Daten zurück."""
        self.torque_data = []
        self.angle_data = []
        if hasattr(self, "torque_curve"):
            self.torque_curve.setData([], [])
        self.logger.info("Graph-Daten zurückgesetzt")

    # ---------- Hardware Funktionen ----------

    def activate_hardware(self) -> None:
        """
        ╔═══════════════════════════════════════════════════════════════════════╗
        ║  HARDWARE AKTIVIEREN - Initialisiert NI-6000 DAQ und Motor           ║
        ║  Dieser Schritt muss VOR jeder Messung durchgeführt werden!          ║
        ╚═══════════════════════════════════════════════════════════════════════╝

        FUNKTION:
        ---------
        Diese Funktion verbindet das Programm mit der echten Hardware:
        1. NI-6000 DAQ → Für Torque- und Winkel-Messung
        2. Motor-Controller → Für Drehbewegung (Nanotec oder Trinamic)

        ABLAUF:
        -------
        Schritt 1: Prüfe ob Hardware bereits initialisiert
        Schritt 2: Setze Warte-Cursor (Sanduhr)
        Schritt 3: Initialisiere NI-6000 DAQ
                   - Kanal ai0: Torque-Spannung (±10V)
                   - Kanal ai1: Angle-Spannung (0-10V)
        Schritt 4: Initialisiere Motor-Controller
                   - Typ: Nanotec (CAN-Bus) oder Trinamic (RS485)
                   - Verbindung herstellen
        Schritt 5: Status-LEDs setzen (grün=OK, rot=Fehler)
        Schritt 6: Erfolgs-/Fehler-Dialog anzeigen

        DEMO-MODUS:
        -----------
        Falls DEMO_MODE = True:
        - Keine echte Hardware erforderlich
        - Alles wird simuliert
        - LEDs zeigen trotzdem grün (Simulation läuft)
        - Nützlich für Tests ohne angeschlossene Geräte

        STATUS-LEDs:
        ------------
        dmm_led (DAQ):
          - GRÜN: NI-6000 erfolgreich verbunden
          - ROT: Verbindungsfehler oder Treiber fehlt

        controller_led (Motor):
          - GRÜN: Motor erfolgreich verbunden
          - ROT: Verbindungsfehler oder Motor aus

        FEHLERBEHANDLUNG:
        -----------------
        Bei Problemen werden detaillierte Fehlermeldungen angezeigt:
        - "NI-6000 DAQ konnte nicht initialisiert werden"
          → Prüfe: NI-DAQmx Treiber installiert? Gerät angeschlossen?
        - "Motor konnte nicht verbunden werden"
          → Prüfe: Motor eingeschaltet? Kabel korrekt? CAN-Bus OK?

        WICHTIG:
        --------
        Diese Funktion muss ERFOLGREICH laufen, bevor eine Messung
        gestartet werden kann! Das Flag 'are_instruments_initialized'
        wird auf True gesetzt und von allen Mess-Funktionen geprüft.

        AUFRUF:
        -------
        - Button "Activate Hardware" in GUI
        - Nur einmal pro Programmsitzung nötig
        - Falls Fehler: "Deactivate Hardware" und erneut versuchen
        """
        # Sicherheitsprüfung: Verhindere doppelte Initialisierung
        if self.are_instruments_initialized:
            self.logger.warning("⚠ Hardware bereits initialisiert - keine Aktion nötig")
            return

        # Warte-Cursor anzeigen (Sanduhr) während Initialisierung läuft
        QtWidgets.QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.logger.info("=" * 60)
        self.logger.info("HARDWARE AKTIVIERUNG GESTARTET")
        self.logger.info("=" * 60)

        # Erfolgs-Tracking
        success = True  # Wird auf False gesetzt bei jedem Fehler
        error_messages = []  # Sammelt alle Fehlermeldungen

        # ═══════════════════════════════════════════════════════════
        # TEIL 1: NI-6000 DAQ INITIALISIEREN
        # ═══════════════════════════════════════════════════════════
        try:
            self.logger.info("→ Initialisiere NI-6000 DAQ...")
            self.logger.info(f"  Torque-Kanal: {DAQ_CHANNEL_TORQUE} (±10V)")
            self.logger.info(f"  Angle-Kanal: {DAQ_CHANNEL_ANGLE} (0-10V)")

            # DAQmxTask Objekt erstellen mit allen Parametern
            self.nidaqmx_task = DAQmxTask(
                torque_channel=DAQ_CHANNEL_TORQUE,  # z.B. "Dev1/ai0"
                angle_channel=DAQ_CHANNEL_ANGLE,  # z.B. "Dev1/ai1"
                voltage_range=DAQ_VOLTAGE_RANGE,  # ±10V
                torque_scale=TORQUE_SCALE,  # 2.0 Nm/V
                angle_voltage_min=ANGLE_VOLTAGE_MIN,  # 0V
                angle_voltage_max=ANGLE_VOLTAGE_MAX,  # 10V
                angle_min_deg=ANGLE_MIN_DEG,  # 0°
                angle_max_deg=ANGLE_MAX_DEG,  # 360°
                demo_mode=DEMO_MODE,  # True/False
            )

            # DAQ-Task tatsächlich erstellen (öffnet Verbindung)
            self.nidaqmx_task.create_nidaqmx_task()

            # Prüfe ob Task erfolgreich erstellt wurde
            if self.nidaqmx_task.is_task_created:
                self.logger.info("✓ NI-6000 DAQ erfolgreich initialisiert")
                self.logger.info(f"  → Torque-Messbereich: ±{TORQUE_SENSOR_MAX_NM} Nm")
                self.logger.info(f"  → Angle-Modus: {ANGLE_ENCODER_MODE.upper()}")
                self.logger.info(f"  → Angle-Quelle: {ANGLE_MEASUREMENT_SOURCE.upper()}")

                # LED auf GRÜN setzen (Erfolg)
                self.dmm_led.setStyleSheet("background-color: green; border-radius: 12px; border: 2px solid black;")
            else:
                # Task wurde erstellt, aber ist nicht bereit
                error_messages.append("NI-6000 DAQ konnte nicht initialisiert werden")
                success = False
                self.dmm_led.setStyleSheet("background-color: red; border-radius: 12px; border: 2px solid black;")

        except Exception as e:
            # Schwerer Fehler beim Initialisieren (z.B. Treiber fehlt, Gerät nicht gefunden)
            self.logger.error("✗ FEHLER beim Initialisieren der NI-6000 DAQ:")
            self.logger.error(f"  {type(e).__name__}: {e}")
            error_messages.append(f"NI-6000 DAQ Fehler: {e}")
            success = False
            self.dmm_led.setStyleSheet("background-color: red; border-radius: 12px; border: 2px solid black;")

        # ═══════════════════════════════════════════════════════════
        # TEIL 2: MOTOR-CONTROLLER INITIALISIEREN
        # ═══════════════════════════════════════════════════════════
        try:
            self.logger.info("→ Initialisiere Motor-Controller...")
            self.logger.info(f"  Typ: {MOTOR_TYPE.upper()}")

            # Motor-Controller Objekt erstellen (abhängig von MOTOR_TYPE)
            if MOTOR_TYPE.lower() == "nanotec":
                # Nanotec N5 mit CAN-Bus (IXXAT, Kvaser, etc.)
                self.motor_controller = NanotecMotorController(
                    bus_hardware=NANOTEC_BUS_HARDWARE,  # z.B. "ixxat"
                    demo_mode=DEMO_MODE,
                )
                motor_name = "Nanotec N5 Motor"

            elif MOTOR_TYPE.lower() == "trinamic":
                # Trinamic Steprocker mit RS485
                self.motor_controller = TrinamicMotorController(
                    port=TRINAMIC_COM_PORT,  # z.B. "COM3"
                    motor_id=TRINAMIC_MOTOR_ID,  # Motor-ID (0-255)
                    demo_mode=DEMO_MODE,
                )
                motor_name = "Trinamic Steprocker"

            else:
                # Unbekannter Motor-Typ in Konfiguration
                raise ValueError(f"Unbekannter Motor-Typ: '{MOTOR_TYPE}' (erwartet: 'nanotec' oder 'trinamic')")

            # Verbindung zum Motor herstellen
            if self.motor_controller.connect():
                self.logger.info(f"✓ {motor_name} erfolgreich verbunden")

                # LED auf GRÜN setzen (Erfolg)
                self.controller_led.setStyleSheet("background-color: green; border-radius: 12px; border: 2px solid black;")
            else:
                # Verbindung fehlgeschlagen (Motor antwortet nicht)
                error_messages.append(f"{motor_name} konnte nicht verbunden werden")
                success = False
                self.controller_led.setStyleSheet("background-color: red; border-radius: 12px; border: 2px solid black;")

        except Exception as e:
            # Schwerer Fehler beim Motor (z.B. COM-Port existiert nicht, CAN-Bus nicht verfügbar)
            self.logger.error("✗ FEHLER beim Verbinden des Motor-Controllers:")
            self.logger.error(f"  {type(e).__name__}: {e}")
            error_messages.append(f"Motor-Controller Fehler: {e}")
            success = False
            self.controller_led.setStyleSheet("background-color: red; border-radius: 12px; border: 2px solid black;")

        # Warte-Cursor zurücksetzen (normaler Cursor)
        QtWidgets.QApplication.restoreOverrideCursor()

        # ═══════════════════════════════════════════════════════════
        # TEIL 3: ERGEBNIS AUSWERTEN UND MELDEN
        # ═══════════════════════════════════════════════════════════

        if success:
            # ✓ ERFOLG - Alle Hardware-Komponenten initialisiert
            self.are_instruments_initialized = True  # Wichtiges Flag setzen!
            self.logger.info("=" * 60)
            self.logger.info("✓ HARDWARE ERFOLGREICH AKTIVIERT")
            self.logger.info("=" * 60)

            # Erfolgs-Dialog zusammenstellen
            success_message = "Hardware erfolgreich aktiviert!\n\n"
            success_message += "✓ NI-6000 DAQ (Torque + Angle)\n"
            success_message += "✓ Motor-Controller\n"
            if ANGLE_MEASUREMENT_SOURCE == "daq":
                success_message += f"✓ SSI Encoder ({ANGLE_ENCODER_MODE} mode)"

            QMessageBox.information(self, "Erfolg", success_message)

        else:
            # ✗ FEHLER - Mindestens eine Komponente fehlgeschlagen
            self.are_instruments_initialized = False  # Flag bleibt False
            self.logger.error("=" * 60)
            self.logger.error("✗ HARDWARE-AKTIVIERUNG FEHLGESCHLAGEN")
            self.logger.error("=" * 60)

            # Alle Fehlermeldungen zusammenfassen
            error_text = "\n".join(error_messages)
            self.logger.error(f"Fehlerdetails:\n{error_text}")

            # Fehler-Dialog anzeigen
            QMessageBox.critical(
                self,
                "Hardware-Fehler",
                f"Hardware-Aktivierung fehlgeschlagen:\n\n{error_text}\n\n"
                "Bitte prüfen Sie:\n"
                "• Sind alle Geräte eingeschaltet?\n"
                "• Sind alle Kabel korrekt angeschlossen?\n"
                "• Sind die Treiber installiert? (NI-DAQmx, CAN-Bus)\n"
                "• Stimmen die Konfigurationen? (DAQ-Kanäle, COM-Ports)",
            )
            QMessageBox.critical(self, "Fehler", f"Hardware-Aktivierung fehlgeschlagen:\n\n{error_text}")

    def deactivate_hardware(self) -> None:
        """Deaktiviert alle Hardware-Komponenten."""
        if not self.are_instruments_initialized:
            self.logger.warning("Hardware ist nicht initialisiert")
            return

        QtWidgets.QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.logger.info("Deaktiviere Hardware...")

        # DAQmx Task schließen
        if hasattr(self, "nidaqmx_task") and self.nidaqmx_task:
            self.logger.info("Schließe NI-6000 DAQ Task")
            try:
                self.nidaqmx_task.close_nidaqmx_task()
                self.logger.info("✓ NI-6000 DAQ Task geschlossen")
            except Exception as e:
                self.logger.error(f"✗ Fehler beim Schließen der DAQ Task: {e}")
            self.nidaqmx_task = None

        # Motor-Controller trennen
        if hasattr(self, "motor_controller") and self.motor_controller:
            self.logger.info("Trenne N5 Nanotec Controller")
            try:
                self.motor_controller.disconnect()
                self.logger.info("✓ N5 Nanotec Controller getrennt")
            except Exception as e:
                self.logger.error(f"✗ Fehler beim Trennen des Controllers: {e}")
            self.motor_controller = None

        # Flags zurücksetzen
        self.are_instruments_initialized = False
        self.is_process_running = False

        # Setup-Steuerelemente wieder aktivieren
        self.set_setup_controls_enabled(True)

        # LED-Status aktualisieren
        self.dmm_led.setStyleSheet("background-color: red; border-radius: 12px; border: 2px solid black;")
        self.controller_led.setStyleSheet("background-color: red; border-radius: 12px; border: 2px solid black;")

        QtWidgets.QApplication.restoreOverrideCursor()
        self.logger.info("✓ Hardware erfolgreich deaktiviert")

    def home_position(self) -> None:
        """Fährt den Motor in die Home-Position und kalibriert Nullpunkt."""
        if not self.are_instruments_initialized:
            self.logger.warning("Hardware nicht initialisiert. Bitte zuerst Hardware aktivieren.")
            QMessageBox.warning(self, "Warnung", "Hardware nicht initialisiert.\nBitte zuerst 'Activate Hardware' drücken.")
            return

        if self.is_process_running:
            self.logger.warning("Home Position nicht möglich während Messung läuft")
            QMessageBox.warning(self, "Warnung", "Home Position nicht möglich während Messung läuft.")
            return

        self.logger.info("Fahre in Home-Position und kalibriere Nullpunkt...")

        # Motor in Home-Position fahren (nur für Motor-Steuerung relevant)
        if self.motor_controller and self.motor_controller.is_connected:
            if self.motor_controller.home_position():
                self.logger.info("✓ Motor in Home-Position (0°)")
            else:
                self.logger.error("✗ Motor-Homing fehlgeschlagen")
                QMessageBox.critical(self, "Fehler", "Motor-Homing fehlgeschlagen")
                return
        else:
            self.logger.warning("Motor-Controller nicht verfügbar")

        # Torque-Nullpunkt kalibrieren
        if self.nidaqmx_task:
            self.nidaqmx_task.calibrate_zero()
            self.logger.info("✓ Torque-Nullpunkt kalibriert")

        # Winkel-Unwrap zurücksetzen (für Single-Turn Modus)
        self.reset_angle_unwrap()

        self.logger.info("✓ Home-Position und Kalibrierung erfolgreich")
        QMessageBox.information(self, "Erfolg", "Home-Position erreicht und Nullpunkt kalibriert!")

    def measure_manual(self) -> None:
        """Manuelle Einzelmessung (Test-Funktion)."""
        if self.is_process_running:
            self.logger.warning("Messung läuft bereits. Manuelle Messung nicht möglich.")
            return

        if not self.are_instruments_initialized or not self.nidaqmx_task or not self.nidaqmx_task.is_task_created:
            self.logger.warning("Hardware nicht initialisiert")
            QMessageBox.warning(self, "Warnung", "Hardware nicht initialisiert.\nBitte zuerst 'Activate Hardware' drücken.")
            return

        try:
            # Winkel messen (abhängig von ANGLE_MEASUREMENT_SOURCE)
            if ANGLE_MEASUREMENT_SOURCE == "daq":
                # Winkel vom NI-6000 DAQ lesen (SSI Encoder via Motrona)
                angle_voltage = self.nidaqmx_task.read_angle_voltage()
                angle_0_360 = self.nidaqmx_task.scale_voltage_to_angle(angle_voltage)
                angle = self.unwrap_angle(angle_0_360)  # Kontinuierlicher Winkel mit Unwrap
                self.logger.debug(f"DAQ Angle: {angle_voltage:.3f}V → {angle_0_360:.2f}° (raw) → {angle:.2f}° (continuous)")
            else:
                # Legacy: Position vom Motor-Controller lesen
                angle = 0.0
                if self.motor_controller and self.motor_controller.is_connected:
                    angle = self.motor_controller.get_position()

            # Spannung lesen
            voltage = self.nidaqmx_task.read_torque_voltage(angle)

            # Torque berechnen
            torque = voltage * TORQUE_SCALE

            self.logger.info(f"Manuelle Messung: Angle={angle:.2f}°, Voltage={voltage:.6f}V, Torque={torque:.6f}Nm")

            # GUI aktualisieren
            self.dmm_voltage.setText(f"{voltage:.6f}")
            self.force_meas.setText(f"{torque:.6f}")
            self.distance_meas.setText(f"{angle:.6f}")

            # Optional: Punkt zum Graph hinzufügen
            if not self.is_process_running:
                self.torque_data.append(torque)
                self.angle_data.append(angle)
                if hasattr(self, "torque_curve"):
                    self.torque_curve.setData(self.angle_data, self.torque_data)

        except Exception as e:
            self.logger.error(f"Fehler bei manueller Messung: {e}")
            QMessageBox.critical(self, "Fehler", f"Fehler bei manueller Messung:\n{e}")

    # ---------- Measurement Funktionen ----------

    def start_measurement(self) -> None:
        """Startet die Messung."""
        if self.is_process_running:
            self.logger.warning("Messung läuft bereits")
            return

        if not self.are_instruments_initialized:
            self.logger.error("Hardware nicht initialisiert")
            QMessageBox.critical(self, "Fehler", "Hardware nicht initialisiert.\nBitte zuerst 'Activate Hardware' drücken.")
            return

        # Parameter auslesen
        max_angle = self.max_angle_value
        max_torque = self.max_torque_value
        max_velocity = self.max_velocity_value

        self.logger.info("=" * 60)
        self.logger.info("MESSUNG STARTEN")
        self.logger.info(f"Max Angle: {max_angle}°")
        self.logger.info(f"Max Torque: {max_torque} Nm")
        self.logger.info(f"Max Velocity: {max_velocity}°/s")
        self.logger.info(f"Angle Source: {ANGLE_MEASUREMENT_SOURCE.upper()}")
        self.logger.info(f"Encoder Mode: {ANGLE_ENCODER_MODE.upper()}")
        self.logger.info("=" * 60)

        # Startzeit speichern
        self.start_time_timestamp = datetime.now()
        self.logger.info(f"Startzeit: {self.start_time_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

        # Winkel-Unwrap zurücksetzen
        self.reset_angle_unwrap()

        # Messordner erstellen
        if not self.create_measurement_folder():
            self.logger.error("Fehler beim Erstellen des Messordners")
            return

        # Motor starten
        if self.motor_controller and self.motor_controller.is_connected:
            if self.motor_controller.move_continuous(max_velocity):
                direction = "im Uhrzeigersinn" if max_velocity > 0 else "gegen Uhrzeigersinn"
                self.logger.info(f"✓ Motor gestartet mit {abs(max_velocity)}°/s {direction}")
            else:
                self.logger.error("✗ Motor-Start fehlgeschlagen")
                QMessageBox.critical(self, "Fehler", "Motor-Start fehlgeschlagen")
                return

        # Measurement Timer starten
        self.setup_measurement_timer()

        # Graph-Daten zurücksetzen
        self.reset_graph_data()

        # Status setzen
        self.is_process_running = True
        self.process_run_led.setStyleSheet("background-color: green; border-radius: 12px; border: 2px solid black;")

        # Setup-Controls deaktivieren
        self.set_setup_controls_enabled(False)

        self.logger.info("✓ Messung erfolgreich gestartet")

    def stop_measurement(self) -> None:
        """Stoppt die laufende Messung."""
        if not self.is_process_running:
            self.logger.warning("Keine Messung läuft")
            return

        self.logger.info("MESSUNG STOPPEN")

        # Measurement Timer stoppen
        if hasattr(self, "measurement_timer") and self.measurement_timer:
            self.measurement_timer.stop()
            self.logger.info("✓ Measurement Timer gestoppt")

        # Motor stoppen
        if self.motor_controller and self.motor_controller.is_connected:
            if self.motor_controller.stop_movement():
                self.logger.info("✓ Motor gestoppt")
            else:
                self.logger.error("✗ Motor-Stop fehlgeschlagen")

        # Status zurücksetzen
        self.is_process_running = False
        self.process_run_led.setStyleSheet("background-color: red; border-radius: 12px; border: 2px solid black;")

        # Setup-Controls wieder aktivieren
        self.set_setup_controls_enabled(True)

        # Startzeit zurücksetzen
        self.start_time_timestamp = None

        self.logger.info("✓ Messung erfolgreich gestoppt")

    def setup_measurement_timer(self) -> None:
        """Initialisiert und startet den Measurement Timer."""
        if self.measurement_timer is not None:
            self.measurement_timer.stop()

        self.measurement_timer = QTimer()
        self.measurement_timer.timeout.connect(self.measure)
        self.measurement_timer.start(MEASUREMENT_INTERVAL)
        self.logger.info(f"✓ Measurement Timer gestartet ({MEASUREMENT_INTERVAL}ms)")

    def create_measurement_folder(self) -> bool:
        """Erstellt die Ordnerstruktur für eine neue Messung."""
        if not self.sample_name or not self.project_dir:
            self.logger.error("Sample-Name oder Projektverzeichnis nicht gesetzt")
            QMessageBox.critical(self, "Fehler", "Sample-Name oder Projektverzeichnis nicht gesetzt.")
            return False

        # Datum und Uhrzeit für Ordnernamen
        timestamp = datetime.now()
        date_str = timestamp.strftime("%Y%m%d")
        time_str = timestamp.strftime("%H%M%S")

        # Ordnername: Datum_Uhrzeit_Probename
        folder_name = f"{date_str}_{time_str}_{self.sample_name}"
        self.measurement_dir = os.path.join(self.project_dir, folder_name)

        try:
            # Hauptmessordner erstellen
            os.makedirs(self.measurement_dir, exist_ok=True)
            self.logger.info(f"✓ Messordner erstellt: {self.measurement_dir}")

            # Messdatei erstellen mit Header
            measurement_filename = f"{date_str}_{time_str}_{self.sample_name}_DATA.txt"
            measurement_file = os.path.join(self.measurement_dir, measurement_filename)

            with open(measurement_file, "w", encoding="utf-8") as f:
                # Header
                header_date = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"# Measurement started: {header_date} - Sample: {self.sample_name}\n")
                f.write(f"# Max Angle: {self.max_angle_value}° | Max Torque: {self.max_torque_value} Nm | Max Velocity: {self.max_velocity_value}°/s\n")
                f.write(f"# Torque Scale: {TORQUE_SCALE} Nm/V | Interval: {MEASUREMENT_INTERVAL}ms\n")

                # Spaltenüberschriften
                header_columns = ["Time", "Voltage", "Torque", "Angle"]
                header_units = ["[HH:mm:ss.f]", "[V]", "[Nm]", "[°]"]

                f.write("\t".join(header_columns) + "\n")
                f.write("\t".join(header_units) + "\n")

            self.logger.info(f"✓ Messdatei erstellt: {measurement_filename}")
            self.measurement_filename = measurement_filename

            return True

        except Exception as e:
            self.logger.error(f"✗ Fehler beim Erstellen des Messordners: {e}")
            QMessageBox.critical(self, "Fehler", f"Fehler beim Erstellen des Messordners:\n{e}")
            return False

    def write_measurement_data(self, timestamp: str, voltage: float, torque: float, angle: float):
        """Schreibt Messdaten in die Messdatei."""
        if not self.measurement_dir or not hasattr(self, "measurement_filename") or not self.measurement_filename:
            return False

        measurement_file = os.path.join(self.measurement_dir, self.measurement_filename)
        try:
            with open(measurement_file, "a", encoding="utf-8") as f:
                data_row = [
                    timestamp,
                    f"{voltage:.6f}",
                    f"{torque:.6f}",
                    f"{angle:.6f}",
                ]
                f.write("\t".join(data_row) + "\n")
            return True
        except Exception as e:
            self.logger.error(f"Fehler beim Schreiben der Messdaten: {e}")
            return False

    def measure(self):
        """
        Zentrale Messfunktion - wird vom Timer aufgerufen.
        """
        if not self.is_process_running:
            return

        # Zeitstempel berechnen
        if self.start_time_timestamp:
            elapsed = datetime.now() - self.start_time_timestamp
            total_seconds = elapsed.total_seconds()
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = int(total_seconds % 60)
            milliseconds = int((total_seconds % 1) * 10)
            elapsed_time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds}"
        else:
            elapsed_time_str = "00:00:00.0"

        # Winkel messen (abhängig von ANGLE_MEASUREMENT_SOURCE)
        angle = 0.0
        if ANGLE_MEASUREMENT_SOURCE == "daq":
            # Winkel vom NI-6000 DAQ lesen (SSI Encoder via Motrona)
            try:
                angle_voltage = self.nidaqmx_task.read_angle_voltage()
                angle_0_360 = self.nidaqmx_task.scale_voltage_to_angle(angle_voltage)
                angle = self.unwrap_angle(angle_0_360)  # Kontinuierlicher Winkel mit Unwrap
            except Exception as e:
                self.logger.warning(f"Fehler beim Lesen der Winkelspannung: {e}")
                angle = 0.0
        else:
            # Legacy: Position vom Motor-Controller lesen
            if self.motor_controller and self.motor_controller.is_connected:
                angle = self.motor_controller.get_position()

        # Spannung vom DAQ lesen (Torque)
        voltage = 0.0
        try:
            if self.nidaqmx_task and self.nidaqmx_task.is_task_created:
                voltage = self.nidaqmx_task.read_torque_voltage(angle)
        except Exception as e:
            self.logger.warning(f"Fehler beim Lesen der DAQ-Spannung: {e}")

        # Torque berechnen
        torque = voltage * TORQUE_SCALE

        # Daten zum Graph hinzufügen
        self.torque_data.append(torque)
        self.angle_data.append(angle)

        if hasattr(self, "torque_curve"):
            self.torque_curve.setData(self.angle_data, self.torque_data)

        # Daten in Datei schreiben
        self.write_measurement_data(elapsed_time_str, voltage, torque, angle)

        # GUI aktualisieren
        self.update_measurement_gui(voltage, torque, angle)

        # Stopbedingungen prüfen
        max_angle = self.max_angle_value
        max_torque = self.max_torque_value

        stop_reason = None

        # Max Angle erreicht?
        if abs(angle) >= abs(max_angle):
            stop_reason = f"Max Angle erreicht ({angle:.2f}° >= {max_angle}°)"

        # Max Torque erreicht?
        if abs(torque) >= abs(max_torque):
            stop_reason = f"Max Torque erreicht ({torque:.2f} Nm >= {max_torque} Nm)"

        if stop_reason:
            self.logger.info(f"STOPP: {stop_reason}")
            self.stop_measurement()

    def update_measurement_gui(self, voltage: float, torque: float, angle: float):
        """Aktualisiert die GUI-Anzeigen nach einer Messung."""
        self.dmm_voltage.setText(f"{voltage:.6f}")
        self.force_meas.setText(f"{torque:.6f}")
        self.distance_meas.setText(f"{angle:.6f}")


# ==================================================================================
# HAUPTPROGRAMM
# ==================================================================================

if __name__ == "__main__":
    """
    Haupteinstiegspunkt für den Torsionsprüfstand.
    """
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
