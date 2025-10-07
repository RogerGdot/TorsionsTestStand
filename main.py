"""
Torsions Test Stand - Software für Torsionsprüfstand
====================================================
Projekt:    Torsions Test Stand
Datei:      main.py
Autor:      [Technikergruppe]
Version:    1.0
Lizenz:     [Lizenztyp, z.B. MIT, GPL, etc.]
Python:     3.13
------------------------------------------------------------------------------

Beschreibung:
-------------
Diese Software steuert einen Torsionsprüfstand zur Erfassung von Kraft und Weg
für eine Techniker-Abschlussarbeit. Die Anwendung bietet eine einfache
grafische Benutzeroberfläche (PyQt6) für die Datenerfassung und Visualisierung.

Wichtige Features:
- Live-Erfassung und Visualisierung von Kraft und Weg mit pyqtgraph
- Flexible Hardware-Unterstützung (NI DAQmx oder andere Messkarten)
- Einfache Konfiguration durch Konstanten (kein JSON-Parameter-System)
- Ausführliche Kommentierung für Lernzwecke
- Logging und Fehlerbehandlung

Abhängigkeiten (requirements.txt):
"""

import logging
import os
import sys

# Hardware-spezifische Imports - flexibel für verschiedene Messkarten
try:
    import nidaqmx
    from nidaqmx.constants import TerminalConfiguration

    NIDAQMX_AVAILABLE = True
except ImportError:
    NIDAQMX_AVAILABLE = False
    print("NI DAQmx nicht verfügbar - andere Messkarten-Implementierung erforderlich")

import pyqtgraph as pg
from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import Qt
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

from src.gui.stylesheet import get_dark_stylesheet  # Importiere das Stylesheet
from src.utils.framework_helper import GuiLogger, WrappingFormatter  # Importiere den WrappingFormatter für Logs

# ===========================================================================================
# KONFIGURATION - Alle wichtigen Parameter für den Torsionsprüfstand
# ===========================================================================================
# Diese Konstanten ersetzen das komplexe JSON-Parameter-System für einfache Konfiguration

# Hardware-Konfiguration Messkarte
FORCE_SCALE = 1.0  # Skalierungsfaktor für Kraftmessung [N/V]
DISTANCE_SCALE = 1.0  # Skalierungsfaktor für Distanzmessung [mm/V]
DAQ_CHANNEL_FORCE = "Dev1/ai0"  # DAQ-Kanal für Kraftmessung
DAQ_CHANNEL_DISTANCE = "Dev1/ai1"  # DAQ-Kanal für Distanzmessung

# Mess-Konfiguration
MEASUREMENT_INTERVAL = 100  # Messintervall in Millisekunden (10 Hz = 100ms)
DEFAULT_SAMPLE_NAME = "TorsionTest"  # Standard-Probenname

# Motor-Konfiguration (für zukünftige Erweiterung)
MOTOR_TYPE = "UNKNOWN"  # "STEPPER", "SERVO", "DC" oder "UNKNOWN"
MOTOR_ENABLED = False  # Motor-Steuerung aktiviert (noch nicht implementiert)

# GUI-Konfiguration
SYSTEM_NAME = "Torsions Test Stand"

# ===========================================================================================


class MotorController:
    """
    Abstrakte Motorsteuerung für den Torsionsprüfstand.
    Kann für verschiedene Motortypen erweitert werden (Stepper, Servo, DC).
    """

    def __init__(self, motor_type: str = MOTOR_TYPE):
        """
        Initialisiert den Motor-Controller.

        Args:
            motor_type (str): Typ des Motors ("STEPPER", "SERVO", "DC", "UNKNOWN")
        """
        self.motor_type = motor_type
        self.is_connected = False
        self.is_enabled = MOTOR_ENABLED
        self.current_position = 0.0  # Aktuelle Position in Grad
        self.target_position = 0.0  # Zielposition in Grad

    def connect(self) -> bool:
        """
        Verbindet mit dem Motor.
        Muss in der konkreten Implementierung überschrieben werden.
        """
        if not self.is_enabled:
            print("Motor-Steuerung ist deaktiviert (MOTOR_ENABLED = False)")
            return False

        if self.motor_type == "UNKNOWN":
            print("Motor-Typ noch nicht definiert - Implementierung erforderlich")
            return False

        # Hier würde die konkrete Motor-Verbindung implementiert
        print(f"Motor-Controller ({self.motor_type}) - Simulation aktiv")
        self.is_connected = True
        return True

    def disconnect(self) -> None:
        """Trennt die Verbindung zum Motor."""
        self.is_connected = False
        print("Motor-Controller getrennt")

    def move_to_position(self, position_degrees: float) -> bool:
        """
        Bewegt den Motor zu einer bestimmten Position.

        Args:
            position_degrees (float): Zielposition in Grad

        Returns:
            bool: True wenn erfolgreich
        """
        if not self.is_connected:
            print("Motor nicht verbunden")
            return False

        self.target_position = position_degrees
        # Hier würde die konkrete Motor-Bewegung implementiert
        print(f"Motor bewegt sich zu Position: {position_degrees}°")
        self.current_position = position_degrees  # Simulation
        return True

    def get_current_position(self) -> float:
        """Gibt die aktuelle Motor-Position zurück."""
        return self.current_position


class DAQmxTask:
    """
    Hardware-abstrakte Klasse für Datenerfassung.
    Unterstützt NI DAQmx und kann für andere Messkarten erweitert werden.
    """

    def __init__(self, force_channel="Dev1/ai0", distance_channel="Dev1/ai1"):
        """
        Initialisiert eine DAQ Task für die Messung von Spannungen an den AI-Kanälen.

        Args:
            force_channel (str): DAQ-Kanal für Kraftmessung (z.B. "Dev1/ai0")
            distance_channel (str): DAQ-Kanal für Distanzmessung (z.B. "Dev1/ai1")
        """
        self.nidaqmx_task = None
        self.force_channel = force_channel
        self.distance_channel = distance_channel
        self.channel_names = [force_channel, distance_channel]
        self.is_task_created = False

    def create_nidaqmx_task(self):
        """
        Erzeugt eine NI DAQmx Task für die konfigurierten AI-Kanäle.
        Falls NI DAQmx nicht verfügbar ist, wird eine Warnung ausgegeben.
        """
        if not NIDAQMX_AVAILABLE:
            print("NI DAQmx nicht verfügbar - Simulation oder alternative Hardware erforderlich")
            # Hier könnte eine andere Messkarten-Implementierung eingesetzt werden
            self.is_task_created = False
            return

        try:
            task = nidaqmx.Task()
            # Force-Kanal hinzufügen
            task.ai_channels.add_ai_voltage_chan(self.force_channel, terminal_config=TerminalConfiguration.DEFAULT)
            # Distance-Kanal hinzufügen
            task.ai_channels.add_ai_voltage_chan(self.distance_channel, terminal_config=TerminalConfiguration.DEFAULT)
            self.nidaqmx_task = task
            self.is_task_created = True
            print(f"NIDAQmx task created successfully with channels: {self.force_channel}, {self.distance_channel}")
        except Exception as e:
            print(f"Error creating NIDAQmx task: {e}")
            self.is_task_created = False

    def read_task_voltages(self) -> tuple[float, float]:
        """
        Liest eine Probe von den Kanaelen ai0 und ai1 aus der uebergebenen Task
        und gibt beide Spannungen als Tupel zurueck.
        """
        task = self.nidaqmx_task
        if task is None:
            raise RuntimeError("Task ist nicht initialisiert")
        # liefert eine Liste mit zwei Werten [ai0, ai1]
        values = task.read(number_of_samples_per_channel=1)
        # NIDAQmx gibt verschachtelte Listen zurück: [[wert1], [wert2]]
        if isinstance(values, list) and len(values) >= 2:
            # Extrahiere die Werte aus den verschachtelten Listen
            force_volt = float(values[0][0]) if isinstance(values[0], list) else float(values[0])
            distance_volt = float(values[1][0]) if isinstance(values[1], list) else float(values[1])
            return force_volt, distance_volt
        else:
            raise RuntimeError(f"Unexpected DAQmx read result: {values}")

    def close_nidaqmx_task(self) -> None:
        """
        Schliesst die Task und gibt alle Ressourcen frei.
        """
        task = self.nidaqmx_task
        if task is None:
            return
        task.close()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        # --- Basisverzeichnisse und GUI laden ---
        self.base_dir = os.getcwd()  # Projektbasisverzeichnis
        ui_file = r"src/gui/torsions_test_stand.ui"
        uic.loadUi(ui_file, self)

        # --- Stylesheet für GUI laden ---
        self.setStyleSheet(get_dark_stylesheet())

        # --- Fenster und Tabs konfigurieren ---
        self.move(self.screen().geometry().center() - self.frameGeometry().center())
        self.tabWidget.setCurrentIndex(0)
        # Verwende Konstanten für Fenstertitel und Systemname
        self.setWindowTitle(SYSTEM_NAME)
        self.labelSystemName.setText(SYSTEM_NAME)
        # Initialisiere Klassenvariablen
        self.init_class_attributes()
        # --- Logger initialisieren ---
        self.setup_Logger()
        self.logger.info("Application started")
        # --- GUI-Elemente und Events verbinden ---
        self.connectEvents()
        # --- Graph Widget initialisieren ---
        self.setup_force_graph_widget()
        # --- DAQmx Channel ComboBoxes initialisieren ---
        self.setup_daqmx_channel_combos()
        # --- Einfache Parameter-Initialisierung (ersetzt load_default_parameters) ---
        self.init_simple_parameters()

    def init_class_attributes(self) -> None:
        """
        Initialisiert alle Klassenvariablen für den Torsionsprüfstand.
        Verwendet einfache Werte statt komplexer Parameter-Strukturen.
        """
        # boolsche Flags für Programmzustand
        self.block_parameter_signals = False
        self.grp_box_connected = False
        self.is_process_running = False  # Flag, ob der Messprozess läuft
        self.are_instruments_initialized = False  # Flag, ob die Hardware initialisiert ist

        # Sample-Name aus Konstanten initialisieren
        self.sample_name = DEFAULT_SAMPLE_NAME

        # Dateipfade für Messdaten
        self.project_dir: str = ""  # Projektverzeichnis (wird vom Benutzer gewählt)
        self.measurement_dir: str = ""  # Speicherort für aktuelle Messung
        self.measurement_filename: str = ""  # Name der aktuellen Messdatei

        # Hardware-Objekte
        self.nidaqmx_task: DAQmxTask = None  # DAQ Task für Hardwarezugriff
        self.motor_controller: MotorController = None  # Motor-Controller für Torsionsantrieb
        self.measurement_timer = None  # Timer für die Messung

        # Zeitmessung für Messungen
        self.start_time_timestamp = None  # Startzeit für verstrichene Zeit

        # Graph-Daten für Force vs. Distance Plot
        self.force_data = []  # Liste für Force-Werte in N
        self.distance_data = []  # Liste für Distance-Werte in mm

    def closeEvent(self, event) -> None:
        self.logger.info("HTS-Sigma 2 closed")
        # Stoppe NIDAQmx Task
        if hasattr(self, "daqmx_task") and self.daqmx_task:
            self.logger.info("Closing NIDAQmx Task")
            self.nidaqmx_task.close_nidaqmx_task()
        super().closeEvent(event)

    def connectEvents(self) -> None:
        self.btn_select_proj_folder.clicked.connect(self.select_project_directory)
        self.start_meas_btn.clicked.connect(self.start_measurement)
        self.stop_meas_btn.clicked.connect(self.stop_measurement)
        self.manual_trig_btn.clicked.connect(self.measure_daqmx)
        self.activate_hardware_btn.clicked.connect(self.activate_hardware)
        self.deactivate_hardware_btn.clicked.connect(self.deactivate_hardware)
        self.smp_name.returnPressed.connect(self.update_sample_name)
        self.smp_name.focusOutEvent = lambda event: (self.update_sample_name(), QtWidgets.QLineEdit.focusOutEvent(self.smp_name, event))

    def connect_groupbox_signals(self) -> None:
        """Verbindet alle relevanten Widgets in GroupBoxen mit Überwachungsfunktionen."""
        for group_box in self.findChildren(QGroupBox):  # Sucht alle GroupBoxen im Hauptfenster
            # QLineEdit: Signale verbinden
            for line_edit in group_box.findChildren(QLineEdit):
                line_edit.old_text = line_edit.text()  # Speichere den ursprünglichen Text in ein __dict__ attribute
                line_edit.editingFinished.connect(lambda le=line_edit: self.check_parameter_change(le))
            # QComboBox: Signale verbinden
            for combo_box in group_box.findChildren(QComboBox):
                combo_box.currentTextChanged.connect(self.accept_parameter)
            for check_box in group_box.findChildren(QtWidgets.QCheckBox):
                check_box.stateChanged.connect(self.accept_parameter)
        self.grp_box_connected = True

    def safe_float(self, text: str, default: float = 0.0) -> float:
        """
        Sichere Konvertierung von String zu Float für Messgeräte.
        Behandelt deutsche Dezimalkommas und ungültige Eingaben.

        Args:
            text (str): Der zu konvertierende Text
            default (float): Standardwert bei Fehlern

        Returns:
            float: Konvertierter Wert oder Standardwert
        """
        try:
            # Deutsche Kommas in Punkte umwandeln
            clean_text = text.strip().replace(",", ".")
            return float(clean_text)
        except (ValueError, TypeError):
            self.logger.warning(f"Konvertierung zu Float fehlgeschlagen: '{text}' -> Standard: {default}")
            return default

    def safe_int(self, text: str, default: int = 0) -> int:
        """
        Sichere Konvertierung von String zu Integer für Einstellungen.
        Behandelt deutsche Dezimalkommas und ungültige Eingaben.

        Args:
            text (str): Der zu konvertierende Text
            default (int): Standardwert bei Fehlern

        Returns:
            int: Konvertierter Wert oder Standardwert
        """
        try:
            # Deutsche Kommas in Punkte umwandeln, dann über float zu int
            clean_text = text.strip().replace(",", ".")
            return int(float(clean_text))  # Über float für Dezimalzahlen-Eingaben
        except (ValueError, TypeError):
            self.logger.warning(f"Konvertierung zu Integer fehlgeschlagen: '{text}' -> Standard: {default}")
            return default

    def check_parameter_change(self, source):
        """
        Vereinfachte Eingabeverarbeitung für QLineEdit-Felder.
        Für einen Techniker-Torsionsprüfstand - einfach und robust.

        Args:
            source: Das QLineEdit-Widget, das geändert wurde
        """
        if not isinstance(source, QtWidgets.QLineEdit):
            return

        # Grundlegende Informationen für das Log
        sender_name = self.sender().objectName() if self.sender() else "Unknown"
        current_text = source.text().strip()

        self.logger.info(f"Parameter '{sender_name}' geändert zu: '{current_text}'")

        # Sehr einfache Validierung: Nur prüfen ob leer, dann auf "0" setzen
        if not current_text:
            source.setText("0")
            self.logger.info(f"Leeres Feld '{sender_name}' auf '0' gesetzt")

        # Komma durch Punkt ersetzen für deutsche Eingaben
        if "," in current_text:
            corrected_text = current_text.replace(",", ".")
            source.setText(corrected_text)
            self.logger.info(f"Komma in '{sender_name}' durch Punkt ersetzt")

        # Parameter-Update triggern (einfach)
        self.accept_parameter()

    def setup_Logger(self) -> None:
        """
        Initialisiert den Logger nur für GUI-Anzeige.
        Keine Datei-Speicherung - alles wird nur in der GUI angezeigt.
        """
        # Logger erstellen
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)  # Einheitliches Logging-Level

        # Formatter für GUI-Anzeige definieren
        formatter = WrappingFormatter("%(asctime)-32.24s  %(levelname)-16.16s %(name)-16.16s %(message)s")

        # Nur GUI-Handler (keine Datei-Speicherung)
        self.gui_handler = GuiLogger()
        self.gui_handler.logger_signal.connect(self.msg)
        self.gui_handler.setLevel(logging.INFO)
        self.gui_handler.setFormatter(formatter)
        root_logger.addHandler(self.gui_handler)

        # Logger für diese Klasse erstellen
        self.logger = logging.getLogger("MAIN")
        self.logger.info("Logger initialized - GUI only (keine Datei-Speicherung)")

    def msg(self, msg="No message included", level=logging.INFO, name="Unknown") -> None:
        # Farben je nach Log-Level setzen
        if level == logging.DEBUG:
            color = "blue"  # Mildes Blau für DEBUG
        elif level == logging.INFO:
            color = "white"  # Weiß für INFO
        elif level == logging.WARNING:
            color = "#E6CF6A"  # Mildes Orange für WARNUNG
        elif level == logging.ERROR:
            color = "#FF5555"  # Helles Rot für FEHLER (besser lesbar auf dunklem Hintergrund)
        elif level == logging.CRITICAL:
            color = "purple"  # Lila für KRITISCH
        else:
            color = "black"  # Standardfarbe
        # Farbe und Stil anwenden

        self.plainLog.setTextColor(QColor(color))
        self.plainLog.setFontWeight(QFont.Weight.Bold if level >= logging.WARNING else QFont.Weight.Normal)
        # Nachricht anzeigen
        self.plainLog.append(msg)
        self.plainLog.moveCursor(QTextCursor.MoveOperation.End)

    def setup_force_graph_widget(self):
        """Embed a PyQtGraph for Force vs. Displacement (N vs. mm) plot."""
        graph_layout = QVBoxLayout(self.force_graph_frame)
        self.graph_widget = pg.PlotWidget()
        # Configure axes
        self.graph_widget.setLabel("left", "Force", units="N", color="white", **{"font-size": "10pt"})
        self.graph_widget.setLabel("bottom", "Displacement", units="mm", color="white", **{"font-size": "10pt"})
        self.graph_widget.setBackground("#262a32")
        self.graph_widget.showGrid(x=True, y=True)
        # Only one curve for Force vs. Displacement
        self.force_curve = self.graph_widget.plot(
            pen=pg.mkPen(color="#0077FF", width=2), symbol="o", symbolBrush="#0077FF", symbolSize=4, name="Force vs. Displacement"
        )
        # Axis styling
        self.graph_widget.getAxis("left").setStyle(tickFont=QFont("Arial", 10))
        self.graph_widget.getAxis("bottom").setStyle(tickFont=QFont("Arial", 10))
        self.graph_widget.getAxis("left").setTextPen("w")
        self.graph_widget.getAxis("bottom").setTextPen("w")
        graph_layout.addWidget(self.graph_widget)

    # ----------Business Logic-------------------

    def init_simple_parameters(self) -> None:
        """
        Einfache Parameter-Initialisierung mit Konstanten.
        Ersetzt das komplexe JSON-Parameter-System.
        """
        # GUI-Elemente mit Konstanten-Werten initialisieren
        self.force_scale.setText(str(FORCE_SCALE))
        self.distance_scale.setText(str(DISTANCE_SCALE))

        # DAQ-Kanäle setzen
        force_index = self.daq_ch_force.findText(DAQ_CHANNEL_FORCE)
        if force_index >= 0:
            self.daq_ch_force.setCurrentIndex(force_index)

        distance_index = self.daq_ch_distance.findText(DAQ_CHANNEL_DISTANCE)
        if distance_index >= 0:
            self.daq_ch_distance.setCurrentIndex(distance_index)

        # Messintervall setzen
        self.interval.setText(str(MEASUREMENT_INTERVAL))

        # Sample-Name setzen
        self.smp_name.setText(self.sample_name)

        # GUI-Signale verbinden (falls noch nicht geschehen)
        if not self.grp_box_connected:
            self.connect_groupbox_signals()

        self.logger.info("Parameter mit Konstanten initialisiert (JSON-System ersetzt)")

    def get_current_force_scale(self) -> float:
        """Liest den aktuellen Force-Scale-Wert aus der GUI."""
        return self.safe_float(self.force_scale.text(), FORCE_SCALE)

    def get_current_distance_scale(self) -> float:
        """Liest den aktuellen Distance-Scale-Wert aus der GUI."""
        return self.safe_float(self.distance_scale.text(), DISTANCE_SCALE)

    def get_current_force_channel(self) -> str:
        """Liest den aktuellen Force-Kanal aus der GUI."""
        return self.daq_ch_force.currentText()

    def get_current_distance_channel(self) -> str:
        """Liest den aktuellen Distance-Kanal aus der GUI."""
        return self.daq_ch_distance.currentText()

    def get_current_interval(self) -> int:
        """Liest das aktuelle Messintervall aus der GUI."""
        return self.safe_int(self.interval.text(), MEASUREMENT_INTERVAL)

    def accept_parameter(self) -> None:
        """
        Vereinfachte Parameter-Akzeptierung ohne JSON-Speicherung.
        Werte werden nur in lokalen Variablen gespeichert.
        """
        if getattr(self, "block_parameter_signals", False):
            return  # Während des Ladens nichts tun

        # Lokale Werte aktualisieren (kein komplexes Parameter-System mehr)
        # Die Werte werden direkt aus der GUI gelesen, wenn sie benötigt werden
        self.logger.debug("Parameter akzeptiert (vereinfachtes System)")

    def update_sample_name(self) -> None:
        """
        Aktualisiert den Sample-Namen (vereinfacht, ohne Parameter-Speicherung).
        """
        if not self.is_process_running:
            self.sample_name = self.smp_name.text().strip()
            self.logger.info(f"Sample-Name aktualisiert: {self.sample_name}")

            if self.project_dir:
                self.update_measurement_directory()

    def select_project_directory(self) -> None:
        """
        Ordnerauswahl für Projektverzeichnis (vereinfacht ohne Parameter-System).
        """
        dialog = QFileDialog()
        options = dialog.options()

        # Standard-Startpfad für die Suche festlegen
        if self.project_dir:
            start_path = self.project_dir
        else:
            start_path = os.getcwd()  # Aktuelles Arbeitsverzeichnis als Fallback

        # Ordner auswählen statt Datei speichern
        folder = QFileDialog.getExistingDirectory(self, "Select Project Directory", start_path, options=options)

        if folder:
            self.project_dir = folder
            self.proj_dir.setText(self.project_dir)
            self.logger.info(f"Project directory '{self.project_dir}' selected")

            # Festplattenspeicher bei Projekt-Ordner-Auswahl aktualisieren (falls Funktion existiert)
            if hasattr(self, "update_disk_space_display"):
                self.update_disk_space_display()

            if self.sample_name:
                # Wenn ein Sample-Name gesetzt ist, aktualisiere das Messverzeichnis
                self.update_measurement_directory()
        else:
            self.logger.warning("No project directory selected")

    def setup_measurement_timer(self) -> None:
        """
        Initialisiert und startet den Measurement Timer.
        """
        from PyQt6.QtCore import QTimer

        if self.measurement_timer is not None:
            self.measurement_timer.stop()

        self.measurement_timer = QTimer()
        self.measurement_timer.timeout.connect(self.measure)
        # Verwende das Intervall aus der GUI
        interval_ms = self.get_current_interval()
        self.measurement_timer.start(interval_ms)
        self.logger.info(f"Measurement timer started with interval: {interval_ms}ms")

    def update_measurement_directory(self) -> None:
        """
        Aktualisiert das Messverzeichnis basierend auf Projektpfad und Sample-Name.
        Da meas_dir GUI-Element entfernt wurde, wird nur noch geloggt.
        """
        proj_dir = self.project_dir
        sample_name = self.sample_name.strip()
        measurement_dir = os.path.join(proj_dir, sample_name)
        if measurement_dir:
            self.logger.info(f"Measurement directory updated to: {measurement_dir}")

    # --- Instrument Funktionen ---

    def setup_daqmx_channel_combos(self):
        """
        Befüllt die DAQmx-Kanal ComboBoxen mit den verfügbaren analogen Eingangskanälen des USB-6001.
        Der USB-6001 hat 8 analoge Eingänge: ai0 bis ai7.
        """
        # USB-6001 analoge Eingangskanäle definieren (8 differentielle/16 single-ended Kanäle)
        channels = [
            "Dev1/ai0",  # Analog Input 0
            "Dev1/ai1",  # Analog Input 1
            "Dev1/ai2",  # Analog Input 2
            "Dev1/ai3",  # Analog Input 3
            "Dev1/ai4",  # Analog Input 4
            "Dev1/ai5",  # Analog Input 5
            "Dev1/ai6",  # Analog Input 6
            "Dev1/ai7",  # Analog Input 7
        ]

        # DAQ Force Channel ComboBox befüllen
        self.daq_ch_force.clear()
        self.daq_ch_force.addItems(channels)
        # Kein Standard-Wert setzen - das macht update_parameter()

        # DAQ Distance Channel ComboBox befüllen
        self.daq_ch_distance.clear()
        self.daq_ch_distance.addItems(channels)
        # Kein Standard-Wert setzen - das macht update_parameter()

        self.logger.info("DAQmx channel combo boxes initialized with USB-6001 analog input channels")

    def set_setup_controls_enabled(self, enabled: bool):
        """
        Aktiviert oder deaktiviert alle Setup-Eingabefelder und -Buttons.
        Während einer Messung sollen nur Stop und Photo Crawler verfügbar sein.

        Args:
            enabled (bool): True = Aktivieren, False = Deaktivieren
        """
        try:
            # Setup GroupBox und alle darin enthaltenen Widgets
            setup_widgets = []

            # Suche nach allen GroupBoxen, die "Setup" im Namen haben
            for group_box in self.findChildren(QGroupBox):
                if "setup" in group_box.objectName().lower() or "Setup" in group_box.title():
                    setup_widgets.append(group_box)
                    # Alle Kinder-Widgets der GroupBox hinzufügen
                    for widget in group_box.findChildren(QtWidgets.QWidget):
                        setup_widgets.append(widget)

            # Spezifische Buttons und Eingabefelder
            control_widgets = [
                # Parameter-Eingabefelder
                getattr(self, "force_scale", None),
                getattr(self, "daq_ch_force", None),
                getattr(self, "distance_scale", None),
                getattr(self, "daq_ch_distance", None),
                getattr(self, "interval", None),
                # Buttons
                getattr(self, "btn_select_proj_folder", None),
                getattr(self, "start_meas_btn", None),
                getattr(self, "manual_trig_btn", None),
                getattr(self, "activate_hardware_btn", None),
                getattr(self, "deactivate_hardware_btn", None),
                # Sample Name Eingabe
                getattr(self, "smp_name", None),
            ]

            # Alle Setup-Widgets deaktivieren/aktivieren
            all_widgets = setup_widgets + control_widgets
            for widget in all_widgets:
                if widget is not None:
                    widget.setEnabled(enabled)

            # Stop Button und Photo Crawler immer verfügbar lassen
            if hasattr(self, "stop_meas_btn"):
                self.stop_meas_btn.setEnabled(True)

            action_text = "enabled" if enabled else "disabled"
            self.logger.info(f"Setup controls {action_text} (measurement running: {not enabled})")

        except Exception as e:
            self.logger.error(f"Error setting setup controls enabled state: {e}")

    def reset_graph_data(self):
        """
        Setzt die Graph-Daten zurück (z.B. bei neuer Messung).
        """
        self.force_data = []
        self.distance_data = []
        # Graph leeren
        if hasattr(self, "force_curve"):
            self.force_curve.setData([], [])
        self.logger.info("Graph data reset")

    def clear_graph_display(self):
        """
        Leert nur die Graph-Anzeige, ohne die Messung zu beeinflussen.
        Nützlich für manuelle Graph-Zurücksetzung.
        """
        if hasattr(self, "force_curve"):
            self.force_curve.clear()
        self.logger.info("Graph display cleared")

    def write_measurement_data(self, timestamp, force_volt, distance_volt, force_value, distance_value):
        """
        Schreibt Messdaten in die Messdatei.
        Reihenfolge: Time, Voltage_Force, Voltage_Distance, Force, Distance
        """
        if not self.measurement_dir or not hasattr(self, "measurement_filename") or not self.measurement_filename:
            return False

        measurement_file = os.path.join(self.measurement_dir, self.measurement_filename)
        try:
            with open(measurement_file, "a", encoding="utf-8") as f:
                # Datenzeile in der gewünschten Reihenfolge zusammenstellen
                data_row = [
                    timestamp,  # Time[HH:mm:ss]
                    f"{force_volt:.6f}",  # Voltage_Force[V]
                    f"{distance_volt:.6f}",  # Voltage_Distance[V]
                    f"{force_value:.6f}",  # Force[N]
                    f"{distance_value:.6f}",  # Distance[mm]
                ]

                f.write("\t".join(data_row) + "\n")
            return True
        except Exception as e:
            self.logger.error(f"Error writing measurement data: {e}")
            return False

    def measure_daqmx(self) -> None:
        """
        Test-Funktion für manuelle DAQmx-Messung.
        Liest die Spannungen von AI0 und AI1 und zeigt sie in der GUI an.
        """
        if self.is_process_running:
            self.logger.warning("Measurement is currently running. Cannot take reference shot.")
            return
        if not self.are_instruments_initialized or not self.nidaqmx_task or not self.nidaqmx_task.is_task_created:
            self.logger.warning("DAQmx Task not initialized or hardware not activated")
            return
        try:
            # NIDAQmx Spannungen lesen
            force_volt, distance_volt = self.nidaqmx_task.read_task_voltages()
            self.logger.info(f"Manual DAQmx reading: Force={force_volt:.6f}V, Distance={distance_volt:.6f}V")

            # Spannungen in physikalische Werte umrechnen (verwendet GUI-Werte)
            force_value = force_volt * self.get_current_force_scale()
            distance_value = distance_volt * self.get_current_distance_scale()

            # GUI-Elemente aktualisieren
            self.volt_force.setText(f"{force_volt:.6f}")
            self.volt_distance.setText(f"{distance_volt:.6f}")
            self.force_meas.setText(f"{force_value:.6f}")
            self.distance_meas.setText(f"{distance_value:.6f}")

            # Optional: Graph-Punkt hinzufügen (nur wenn keine Messung läuft)
            if not self.is_process_running:
                self.force_data.append(force_value)
                self.distance_data.append(distance_value)
                if hasattr(self, "force_curve"):
                    self.force_curve.setData(self.distance_data, self.force_data)
                self.logger.debug("Graph updated with manual measurement point")

            self.logger.info(f"Manual measurement: Force={force_value:.6f}N, Distance={distance_value:.6f}mm")

        except Exception as e:
            self.logger.error(f"Error during manual DAQmx measurement: {e}")
            QMessageBox.critical(self, "Error", f"Failed to read DAQmx values:\n{e}")

    # ----------Measurement-------------------

    def activate_hardware(self) -> None:
        if self.are_instruments_initialized:
            self.logger.warning("Hardware already initialized")
            return
        # Setze den Mauszeiger auf "Warten" (Busy)
        QtWidgets.QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.logger.info("Activating hardware...")

        # DAQmx Task mit den aktuellen GUI-Kanälen erstellen
        force_channel = self.get_current_force_channel()
        distance_channel = self.get_current_distance_channel()
        self.logger.info(f"Initializing DAQmx with channels: Force={force_channel}, Distance={distance_channel}")

        self.nidaqmx_task = DAQmxTask(force_channel, distance_channel)  # Erstelle DAQmx Task mit konfigurierten Kanälen
        self.nidaqmx_task.create_nidaqmx_task()
        if self.nidaqmx_task.is_task_created:
            self.logger.info("DAQmx Task created successfully")
        else:
            self.logger.error("Failed to create DAQmx Task")
            QMessageBox.critical(self, "Error", "Failed to create DAQmx Task. Check your hardware connection.")
            QtWidgets.QApplication.restoreOverrideCursor()
            return

        # Motor-Controller initialisieren (falls aktiviert)
        self.motor_controller = MotorController()
        if self.motor_controller.connect():
            self.logger.info(f"Motor-Controller ({self.motor_controller.motor_type}) initialized")
        else:
            self.logger.info("Motor-Controller nicht aktiviert oder nicht verfügbar")
        self.are_instruments_initialized = True

        # LED-Status aktualisieren (grün = aktiviert)
        if self.nidaqmx_task and self.nidaqmx_task.is_task_created:
            self.nidaq_activ_led.setStyleSheet("background-color: green; border-radius: 12px; border: 2px solid black;")

        QtWidgets.QApplication.restoreOverrideCursor()

    def deactivate_hardware(self) -> None:
        """
        Deaktiviert alle Hardware-Komponenten (DAQmx Task und Kameras).
        """
        if not self.are_instruments_initialized:
            self.logger.warning("Hardware is not initialized")
            return

        # Setze den Mauszeiger auf "Warten" (Busy)
        QtWidgets.QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.logger.info("Deactivating hardware...")

        # DAQmx Task schließen
        if hasattr(self, "nidaqmx_task") and self.nidaqmx_task:
            self.logger.info("Closing DAQmx Task")
            try:
                self.nidaqmx_task.close_nidaqmx_task()
                self.logger.info("DAQmx Task closed successfully")
            except Exception as e:
                self.logger.error(f"Error closing DAQmx Task: {e}")
            self.nidaqmx_task = None

        # Motor-Controller trennen
        if hasattr(self, "motor_controller") and self.motor_controller:
            self.logger.info("Disconnecting Motor Controller")
            try:
                self.motor_controller.disconnect()
                self.logger.info("Motor Controller disconnected successfully")
            except Exception as e:
                self.logger.error(f"Error disconnecting Motor Controller: {e}")
            self.motor_controller = None

        # Flags zurücksetzen
        self.are_instruments_initialized = False
        self.is_process_running = False

        # Setup-Steuerelemente wieder aktivieren (falls durch Messung deaktiviert)
        self.set_setup_controls_enabled(True)

        # LED-Status aktualisieren (rot = deaktiviert)
        self.nidaq_activ_led.setStyleSheet("background-color: red; border-radius: 12px; border: 2px solid black;")

        QtWidgets.QApplication.restoreOverrideCursor()
        self.logger.info("Hardware deactivated successfully")

    def start_measurement(self) -> None:
        # Check if hardware is initialized
        if self.is_process_running:
            self.logger.warning("Measurement is already running.")
            return
        if not self.are_instruments_initialized:
            self.logger.error("Instruments not initialized. Please activate hardware first.")
            QMessageBox.critical(self, "Error", "Instruments not initialized. Please activate hardware first.")
            return
        # Startzeit in GUI anzeigen
        from datetime import datetime

        start_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.start_time.setText(start_timestamp)

        # Startzeit für verstrichene Zeit speichern
        self.start_time_timestamp = datetime.now()

        # Den Messordner erstellen
        if not self.create_measurement_folder():
            self.logger.error("Failed to create measurement folder")
            return

        # Measurement timer starten
        self.setup_measurement_timer()

        # Process Status setzen
        self.is_process_running = True
        self.process_run_led.setStyleSheet("background-color: green; border-radius: 12px; border: 2px solid black;")

        # Setup-Steuerelemente während der Messung deaktivieren
        self.set_setup_controls_enabled(False)

        self.logger.info("Measurement started successfully")

    def stop_measurement(self) -> None:
        """
        Stoppt die laufende Messung.
        """
        if not self.is_process_running:
            self.logger.warning("No measurement is currently running")
            return

        # Measurement timer stoppen
        if hasattr(self, "measurement_timer") and self.measurement_timer:
            self.measurement_timer.stop()
            self.logger.info("Measurement timer stopped")

        # Process Status zurücksetzen
        self.is_process_running = False
        self.process_run_led.setStyleSheet("background-color: red; border-radius: 12px; border: 2px solid black;")

        # Setup-Steuerelemente wieder aktivieren
        self.set_setup_controls_enabled(True)

        # Startzeit zurücksetzen
        self.start_time_timestamp = None
        self.elapsed_time.setText("00:00:00.0")

        self.logger.info("Measurement stopped successfully")

    def create_measurement_folder(self) -> None:
        """
        Erstellt die Ordnerstruktur für eine neue Messung:
        - Hauptordner: Datum_Uhrzeit_Probename
        - Messdatei: Probename.txt mit Header
        """
        if not self.sample_name or not self.project_dir:
            self.logger.error("Sample name or project directory not set. Cannot create measurement folder.")
            return False

        # Datum und Uhrzeit für den Ordnernamen generieren
        from datetime import datetime

        timestamp = datetime.now()
        date_str = timestamp.strftime("%Y%m%d")
        time_str = timestamp.strftime("%H%M%S")

        # Ordnername: Datum_Uhrzeit_Probename
        folder_name = f"{date_str}_{time_str}_{self.sample_name}"
        self.measurement_dir = os.path.join(self.project_dir, folder_name)

        try:
            # Hauptmessordner erstellen
            os.makedirs(self.measurement_dir, exist_ok=True)
            self.logger.info(f"Created measurement directory: {self.measurement_dir}")

            # Messdatei erstellen mit Datum, Zeit und Sample Name
            measurement_filename = f"{date_str}_{time_str}_{self.sample_name}_DATA.txt"
            measurement_file = os.path.join(self.measurement_dir, measurement_filename)
            with open(measurement_file, "w", encoding="utf-8") as f:
                # Header-Zeile 1: Datum und Probenname
                header_date = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"# Measurement started: {header_date} - Sample: {self.sample_name}\n")

                # Header-Zeile 2: Parameter-Informationen (verwendet aktuelle GUI-Werte)
                f.write(
                    f"# Force Scale [N/V]: {self.get_current_force_scale()} | "
                    f"Distance Scale [mm/V]: {self.get_current_distance_scale()} | "
                    f"Interval: {self.get_current_interval()}ms\n"
                )

                # Header-Zeile 4: Spaltenüberschriften (ohne Units)
                header_columns = ["Time", "Voltage_Force", "Voltage_Distance", "Force", "Distance"]

                # Header-Zeile 5: Units
                header_units = ["[HH:mm:ss.f]", "[V]", "[V]", "[N]", "[mm]"]

                # Zeile 4: Spaltenüberschriften schreiben
                f.write("\t".join(header_columns) + "\n")

                # Zeile 5: Units schreiben
                f.write("\t".join(header_units) + "\n")

            self.logger.info(f"Created measurement file: {measurement_file}")

            # Dateiname für späteren Zugriff speichern
            self.measurement_filename = measurement_filename

            # Graph-Daten für neue Messung zurücksetzen
            self.reset_graph_data()

            return True

        except Exception as e:
            self.logger.error(f"Error creating measurement folder: {e}")
            QMessageBox.critical(self, "Error", f"Failed to create measurement folder:\n{e}")
            return False

    def measure(self):
        """
        Zentrale Messfunktion für den Torsionsprüfstand.
        ==============================================

        Diese Funktion wird regelmäßig vom Timer aufgerufen und führt einen kompletten
        Messzyklus durch. Für eine Techniker-Abschlussarbeit ist es wichtig zu verstehen,
        dass diese Funktion das "Herzstück" der Datenerfassung ist.

        Messablauf:
        1. Zeitstempel berechnen (verstrichene Zeit seit Messbeginn)
        2. Spannungen von der Messkarte lesen (Kraft und Distanz)
        3. Spannungen in physikalische Werte umrechnen (Newton und Millimeter)
        4. Daten im Diagramm anzeigen (Force vs. Distance Plot)
        5. Daten in Datei speichern für spätere Auswertung
        6. GUI-Elemente mit aktuellen Werten aktualisieren

        Die Funktion ist robust programmiert und fängt Fehler ab, damit der
        Torsionsprüfstand auch bei Hardware-Problemen nicht abstürzt.
        """
        # Sicherheitscheck: Nur messen wenn eine Messung läuft
        if not self.is_process_running:
            return

        from datetime import datetime

        # === SCHRITT 1: Zeitstempel berechnen ===
        # Verstrichene Zeit seit Messbeginn für die Datenaufzeichnung
        if self.start_time_timestamp:
            elapsed = datetime.now() - self.start_time_timestamp
            total_seconds = elapsed.total_seconds()
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = int(total_seconds % 60)
            milliseconds = int((total_seconds % 1) * 10)  # Zehntelsekunden (100ms Auflösung)
            elapsed_time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds}"
        else:
            elapsed_time_str = "00:00:00.0"

        # === SCHRITT 2: Spannungen von der Messkarte lesen ===
        # Initialisierung mit Standardwerten (wichtig für Fehlerbehandlung)
        force_volt = 0.0  # Spannung vom Kraftsensor in Volt
        distance_volt = 0.0  # Spannung vom Distanzsensor in Volt

        try:
            # Nur lesen wenn die DAQ-Hardware erfolgreich initialisiert wurde
            if self.nidaqmx_task and self.nidaqmx_task.is_task_created:
                force_volt, distance_volt = self.nidaqmx_task.read_task_voltages()
                self.logger.debug(f"Spannungen erfolgreich gelesen: Kraft={force_volt:.6f}V, Distanz={distance_volt:.6f}V")
            else:
                self.logger.warning("DAQmx Task nicht verfügbar - verwende Nullwerte")
        except Exception as e:
            # Fehlerbehandlung: Bei Hardware-Problemen weitermachen statt abzustürzen
            self.logger.warning(f"Fehler beim Lesen der DAQ-Spannungen: {e}")

        # === SCHRITT 3: Spannungen in physikalische Werte umrechnen ===
        # Hier passiert die wichtige Umrechnung von Volt in Newton und Millimeter
        # Die Skalierungsfaktoren kommen aus der GUI oder den Konstanten
        force_value = force_volt * self.get_current_force_scale()  # [V] * [N/V] = [N]
        distance_value = distance_volt * self.get_current_distance_scale()  # [V] * [mm/V] = [mm]

        # === SCHRITT 4: Daten im Diagramm darstellen ===
        # Für die Techniker-Abschlussarbeit: Das Diagramm zeigt Force vs. Distance
        # So kann man sehen, wie sich die Kraft bei steigender Verdrehung verhält
        self.force_data.append(force_value)  # Neue Kraft zur Liste hinzufügen
        self.distance_data.append(distance_value)  # Neue Distanz zur Liste hinzufügen

        # Graph mit den neuen Datenpunkten aktualisieren (nur wenn vorhanden)
        if hasattr(self, "force_curve"):
            self.force_curve.setData(self.distance_data, self.force_data)

        # === SCHRITT 5: Daten in Datei speichern ===
        # Alle Messdaten werden in eine Textdatei geschrieben für spätere Auswertung
        # Format: Zeit, Spannung_Kraft, Spannung_Distanz, Kraft, Distanz
        self.write_measurement_data(elapsed_time_str, force_volt, distance_volt, force_value, distance_value)

        # === SCHRITT 6: GUI aktualisieren ===
        # Zum Schluss werden alle Anzeige-Elemente mit den neuen Werten aktualisiert
        self.update_measurement_gui(force_volt, distance_volt, force_value, distance_value)

    def update_measurement_gui(self, force_volt, distance_volt, force_value, distance_value):
        """
        Aktualisiert die GUI-Anzeigen nach einer Messung.
        ================================================

        Diese Funktion zeigt die gemessenen Werte in der Benutzeroberfläche an.
        Für eine Techniker-Abschlussarbeit wichtig: Die GUI zeigt sowohl die
        rohen Spannungswerte (für Debugging) als auch die umgerechneten
        physikalischen Werte (für die eigentliche Messung).

        Args:
            force_volt (float): Kraftsensor-Spannung in Volt
            distance_volt (float): Distanzsensor-Spannung in Volt
            force_value (float): Umgerechnete Kraft in Newton
            distance_value (float): Umgerechnete Distanz in Millimeter
        """
        # Spannungswerte anzeigen (6 Nachkommastellen für Präzision)
        self.volt_force.setText(f"{force_volt:.6f}")
        self.volt_distance.setText(f"{distance_volt:.6f}")

        # Physikalische Werte anzeigen (6 Nachkommastellen für Präzision)
        self.force_meas.setText(f"{force_value:.6f}")
        self.distance_meas.setText(f"{distance_value:.6f}")


# ==================================================================================
# HAUPTPROGRAMM - Einstiegspunkt für den Torsionsprüfstand
# ==================================================================================


if __name__ == "__main__":
    """
    Haupteinstiegspunkt für den Torsionsprüfstand.
    
    Hier wird die PyQt6-Anwendung gestartet. Für eine Techniker-Abschlussarbeit
    ist es wichtig zu verstehen, dass dies der erste Code ist, der ausgeführt wird,
    wenn das Programm gestartet wird.
    
    Der Ablauf:
    1. QApplication erstellen (verwaltet die gesamte GUI)
    2. MainWindow erstellen (unser Hauptfenster mit allen Funktionen)
    3. Fenster anzeigen
    4. Event-Loop starten (wartet auf Benutzer-Eingaben)
    """
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
