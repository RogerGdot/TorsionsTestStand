"""
Torsions Test Stand - Software für Torsionsprüfstand
====================================================
Projekt:    Torsions Test Stand
Datei:      main.py
Autor:      [Technikergruppe]
Version:    2.0
Python:     3.13
------------------------------------------------------------------------------

Beschreibung:
-------------
Diese Software steuert einen Torsionsprüfstand zur Erfassung von Drehmoment
und Winkel für eine Techniker-Abschlussarbeit.

Hardware:
- DF-30 Drehmoment-Sensor (±20 Nm)
- Messverstärker (±10V Ausgang)
- NI-6000 DAQ (±10V Eingang)
- N5 Nanotec Schrittmotor (Modbus TCP, Closed-Loop)

Features:
- Demo-Modus für Tests ohne Hardware
- Live-Visualisierung mit pyqtgraph
- Automatische Stopbedingungen (Max Torque/Angle)
- Home-Position und Nullpunkt-Kalibrierung
- Bidirektionale Motor-Steuerung
"""

import logging
import os
import random
import sys
import time
from datetime import datetime

# Hardware-spezifische Imports
try:
    import nidaqmx
    from nidaqmx.constants import TerminalConfiguration

    NIDAQMX_AVAILABLE = True
except ImportError:
    NIDAQMX_AVAILABLE = False
    print("NI DAQmx nicht verfügbar - Demo-Modus wird verwendet")

try:
    from pymodbus.client import ModbusTcpClient
    from pymodbus.exceptions import ModbusException

    PYMODBUS_AVAILABLE = True
except ImportError:
    PYMODBUS_AVAILABLE = False
    print("PyModbus nicht verfügbar - Demo-Modus wird verwendet")

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

from src.gui.stylesheet import get_dark_stylesheet
from src.utils.framework_helper import GuiLogger, WrappingFormatter

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
DAQ_VOLTAGE_RANGE = 10.0  # ±10V Messbereich

# Mess-Konfiguration
MEASUREMENT_INTERVAL = 100  # Messintervall in Millisekunden (10 Hz = 100ms)
DEFAULT_SAMPLE_NAME = "TorsionTest"  # Standard-Probenname

# N5 Nanotec Schrittmotor-Konfiguration
N5_IP_ADDRESS = "192.168.0.100"  # IP-Adresse des N5 Controllers
N5_MODBUS_PORT = 502  # Standard Modbus TCP Port
N5_SLAVE_ID = 1  # Modbus Slave ID
MOTOR_TYPE = "N5_NANOTEC"  # Motor-Typ
MOTOR_ENABLED = True  # Motor-Steuerung aktiviert

# Motor-Parameter (Standardwerte)
DEFAULT_MAX_ANGLE = 360.0  # Standard maximaler Winkel [Grad]
DEFAULT_MAX_TORQUE = 15.0  # Standard maximales Drehmoment [Nm]
DEFAULT_MAX_VELOCITY = 10.0  # Standard Geschwindigkeit [Grad/s] (+ = Uhrzeiger, - = Gegen Uhrzeiger)

# GUI-Konfiguration
SYSTEM_NAME = "Torsions Test Stand - DF-30 Sensor"

# ===========================================================================================


class N5NanotecController:
    """
    N5 Nanotec Stepper Motor Controller via Modbus TCP.
    Closed-Loop Position Control mit Positionsabfrage.
    """

    def __init__(self, ip_address: str = N5_IP_ADDRESS, port: int = N5_MODBUS_PORT, slave_id: int = N5_SLAVE_ID, demo_mode: bool = DEMO_MODE):
        """
        Initialisiert den N5 Nanotec Controller.

        Args:
            ip_address (str): IP-Adresse des N5 Controllers
            port (int): Modbus TCP Port
            slave_id (int): Modbus Slave ID
            demo_mode (bool): Demo-Modus für Simulation
        """
        self.ip_address = ip_address
        self.port = port
        self.slave_id = slave_id
        self.demo_mode = demo_mode
        self.is_connected = False
        self.client = None

        # Position und Bewegung
        self.current_position = 0.0  # Aktuelle Position in Grad
        self.target_position = 0.0  # Zielposition in Grad
        self.is_moving = False  # Bewegungsstatus
        self.velocity = 0.0  # Geschwindigkeit in Grad/s

        # Demo-Mode Simulation
        self.demo_start_time = None
        self.demo_start_position = 0.0

    def connect(self) -> bool:
        """Verbindet mit dem N5 Controller."""
        if self.demo_mode:
            print("[DEMO] N5 Nanotec Controller - Simulation aktiv")
            self.is_connected = True
            self.current_position = 0.0
            return True

        if not PYMODBUS_AVAILABLE:
            print("PyModbus nicht verfügbar - N5 Steuerung nicht möglich")
            return False

        try:
            self.client = ModbusTcpClient(self.ip_address, port=self.port)
            connection = self.client.connect()
            if connection:
                self.is_connected = True
                print(f"N5 Nanotec verbunden: {self.ip_address}:{self.port}")
                return True
            else:
                print(f"N5 Nanotec Verbindung fehlgeschlagen: {self.ip_address}:{self.port}")
                return False
        except Exception as e:
            print(f"N5 Nanotec Verbindungsfehler: {e}")
            return False

    def disconnect(self) -> None:
        """Trennt die Verbindung zum N5 Controller."""
        if self.demo_mode:
            self.is_connected = False
            return

        if self.client and self.is_connected:
            self.client.close()
            self.is_connected = False
            print("N5 Nanotec getrennt")

    def home_position(self) -> bool:
        """Fährt den Motor in die Home-Position (0°)."""
        if not self.is_connected:
            print("N5 nicht verbunden")
            return False

        if self.demo_mode:
            print("[DEMO] N5 fährt in Home-Position (0°)")
            self.current_position = 0.0
            self.target_position = 0.0
            self.is_moving = False
            return True

        # Hier würde der echte Modbus-Befehl kommen
        # Beispiel: self.client.write_register(address, value, unit=self.slave_id)
        self.target_position = 0.0
        self.current_position = 0.0
        return True

    def move_continuous(self, velocity: float) -> bool:
        """
        Startet kontinuierliche Bewegung mit gegebener Geschwindigkeit.

        Args:
            velocity (float): Geschwindigkeit in Grad/s (+ = Uhrzeiger, - = Gegen Uhrzeiger)

        Returns:
            bool: True wenn erfolgreich
        """
        if not self.is_connected:
            print("N5 nicht verbunden")
            return False

        self.velocity = velocity
        self.is_moving = True

        if self.demo_mode:
            self.demo_start_time = time.time()
            self.demo_start_position = self.current_position
            print(f"[DEMO] N5 startet Bewegung mit {velocity:.2f}°/s")
            return True

        # Hier würde der echte Modbus-Befehl für kontinuierliche Bewegung kommen
        return True

    def stop_movement(self) -> bool:
        """Stoppt die aktuelle Bewegung sofort."""
        if not self.is_connected:
            return False

        self.is_moving = False
        self.velocity = 0.0

        if self.demo_mode:
            print(f"[DEMO] N5 gestoppt bei Position {self.current_position:.2f}°")
            return True

        # Hier würde der echte Modbus-Stop-Befehl kommen
        return True

    def get_position(self) -> float:
        """
        Liest die aktuelle Position vom N5 Controller (Closed-Loop).

        Returns:
            float: Aktuelle Position in Grad
        """
        if not self.is_connected:
            return 0.0

        if self.demo_mode:
            # Simuliere Bewegung basierend auf Geschwindigkeit und Zeit
            if self.is_moving and self.demo_start_time is not None:
                elapsed_time = time.time() - self.demo_start_time
                self.current_position = self.demo_start_position + (self.velocity * elapsed_time)
            return self.current_position

        # Hier würde die echte Positionsabfrage via Modbus kommen
        # Beispiel: result = self.client.read_holding_registers(address, count=1, unit=self.slave_id)
        return self.current_position


class DemoHardwareSimulator:
    """
    Demo-Hardware-Simulator für Tests ohne echte Hardware.
    Simuliert DF-30 Sensor und N5 Nanotec Motor.
    """

    def __init__(self):
        self.torque_offset = 0.0  # Torque-Nullpunkt nach Kalibrierung
        self.current_angle = 0.0  # Aktueller Winkel
        self.is_running = False
        self.start_time = None

    def get_simulated_torque(self, angle: float) -> float:
        """
        Simuliert Drehmoment basierend auf Winkel.
        Einfaches lineares Modell: Torque steigt mit Winkel.

        Args:
            angle (float): Aktueller Winkel in Grad

        Returns:
            float: Simuliertes Drehmoment in Nm
        """
        # Simuliere elastisches Torsionsverhalten
        # Drehmoment steigt linear mit Winkel, plus kleines Rauschen
        base_torque = angle * 0.05  # 0.05 Nm pro Grad
        noise = random.uniform(-0.1, 0.1)  # Kleines Rauschen
        torque = base_torque + noise + self.torque_offset

        # Begrenze auf ±20 Nm (DF-30 Sensor Bereich)
        torque = max(-20.0, min(20.0, torque))
        return torque

    def get_simulated_voltage(self, torque: float) -> float:
        """
        Konvertiert Drehmoment zu Spannung (Messverstärker-Ausgang).

        Args:
            torque (float): Drehmoment in Nm

        Returns:
            float: Spannung in V (±10V)
        """
        # ±20 Nm → ±10V
        voltage = torque / TORQUE_SCALE
        return voltage

    def calibrate_zero(self) -> None:
        """Kalibriert den Nullpunkt (aktuelles Drehmoment = 0)."""
        current_torque = self.get_simulated_torque(self.current_angle)
        self.torque_offset = -current_torque
        print(f"[DEMO] Torque kalibriert (Offset: {self.torque_offset:.3f} Nm)")


class DAQmxTask:
    """
    Hardware-abstrakte Klasse für Datenerfassung mit NI-6000.
    Unterstützt ±10V Messbereich für DF-30 Sensor.
    """

    def __init__(self, torque_channel: str = DAQ_CHANNEL_TORQUE, demo_mode: bool = DEMO_MODE):
        """
        Initialisiert eine DAQ Task für die Messung von Drehmoment.

        Args:
            torque_channel (str): DAQ-Kanal für Drehmomentmessung (z.B. "Dev1/ai0")
            demo_mode (bool): Demo-Modus für Simulation
        """
        self.nidaqmx_task = None
        self.torque_channel = torque_channel
        self.demo_mode = demo_mode
        self.is_task_created = False
        self.demo_simulator = DemoHardwareSimulator() if demo_mode else None

    def create_nidaqmx_task(self):
        """
        Erzeugt eine NI DAQmx Task für den konfigurierten AI-Kanal.
        """
        if self.demo_mode:
            print("[DEMO] NI-6000 DAQ - Simulation aktiv")
            self.is_task_created = True
            return

        if not NIDAQMX_AVAILABLE:
            print("NI DAQmx nicht verfügbar - Demo-Modus erforderlich")
            self.is_task_created = False
            return

        try:
            task = nidaqmx.Task()
            # Torque-Kanal mit ±10V Range hinzufügen
            task.ai_channels.add_ai_voltage_chan(
                self.torque_channel, terminal_config=TerminalConfiguration.DEFAULT, min_val=-DAQ_VOLTAGE_RANGE, max_val=DAQ_VOLTAGE_RANGE
            )
            self.nidaqmx_task = task
            self.is_task_created = True
            print(f"NIDAQmx task erstellt: {self.torque_channel} (±{DAQ_VOLTAGE_RANGE}V)")
        except Exception as e:
            print(f"Fehler beim Erstellen der NIDAQmx task: {e}")
            self.is_task_created = False

    def read_torque_voltage(self, current_angle: float = 0.0) -> float:
        """
        Liest die Spannung vom Drehmoment-Sensor.

        Args:
            current_angle (float): Aktueller Winkel für Demo-Simulation

        Returns:
            float: Spannung in V
        """
        if self.demo_mode:
            # Demo-Modus: Simuliere Spannung basierend auf Winkel
            torque = self.demo_simulator.get_simulated_torque(current_angle)
            voltage = self.demo_simulator.get_simulated_voltage(torque)
            return voltage

        task = self.nidaqmx_task
        if task is None:
            raise RuntimeError("Task ist nicht initialisiert")

        # Echte Hardware: Lese Spannung von DAQ
        values = task.read(number_of_samples_per_channel=1)
        if isinstance(values, list):
            return float(values[0])
        else:
            return float(values)

    def calibrate_zero(self) -> None:
        """Kalibriert den Nullpunkt des Sensors."""
        if self.demo_mode and self.demo_simulator:
            self.demo_simulator.calibrate_zero()

    def close_nidaqmx_task(self) -> None:
        """
        Schliesst die Task und gibt alle Ressourcen frei.
        """
        if self.demo_mode:
            self.is_task_created = False
            return

        task = self.nidaqmx_task
        if task is None:
            return
        task.close()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        # --- Basisverzeichnisse und GUI laden ---
        self.base_dir = os.getcwd()
        ui_file = r"src/gui/torsions_test_stand.ui"
        uic.loadUi(ui_file, self)

        # --- Stylesheet für GUI laden ---
        self.setStyleSheet(get_dark_stylesheet())

        # --- Fenster konfigurieren ---
        self.move(self.screen().geometry().center() - self.frameGeometry().center())
        self.setWindowTitle(SYSTEM_NAME)
        self.labelSystemName.setText(SYSTEM_NAME)

        # Initialisiere Klassenvariablen
        self.init_class_attributes()

        # --- Logger initialisieren ---
        self.setup_Logger()
        self.logger.info("Application started")
        self.logger.info(f"Demo-Modus: {'AKTIV' if DEMO_MODE else 'INAKTIV'}")

        # --- GUI-Elemente und Events verbinden ---
        self.connectEvents()

        # --- Graph Widget initialisieren ---
        self.setup_torque_graph_widget()

        # --- Parameter initialisieren ---
        self.init_parameters()

    def init_class_attributes(self) -> None:
        """
        Initialisiert alle Klassenvariablen für den Torsionsprüfstand.
        """
        # Flags für Programmzustand
        self.block_parameter_signals = False
        self.grp_box_connected = False
        self.is_process_running = False  # Messung läuft
        self.are_instruments_initialized = False  # Hardware initialisiert

        # Sample-Name
        self.sample_name = DEFAULT_SAMPLE_NAME

        # Dateipfade für Messdaten
        self.project_dir: str = ""
        self.measurement_dir: str = ""
        self.measurement_filename: str = ""

        # Hardware-Objekte
        self.nidaqmx_task: DAQmxTask = None
        self.motor_controller: N5NanotecController = None
        self.measurement_timer: QTimer = None

        # Zeitmessung
        self.start_time_timestamp = None

        # Graph-Daten für Torque vs. Angle Plot
        self.torque_data = []  # Liste für Torque-Werte in Nm
        self.angle_data = []  # Liste für Angle-Werte in Grad

    def closeEvent(self, event) -> None:
        """Wird beim Schließen des Fensters aufgerufen."""
        self.logger.info("Torsions Test Stand wird geschlossen")

        # Stoppe laufende Messung
        if self.is_process_running:
            self.stop_measurement()

        # Deaktiviere Hardware
        if self.are_instruments_initialized:
            self.deactivate_hardware()

        super().closeEvent(event)

    def connectEvents(self) -> None:
        """Verbindet alle Button-Events mit ihren Funktionen."""
        self.btn_select_proj_folder.clicked.connect(self.select_project_directory)
        self.start_meas_btn.clicked.connect(self.start_measurement)
        self.stop_meas_btn.clicked.connect(self.stop_measurement)
        self.manual_trig_btn.clicked.connect(self.measure_manual)
        self.activate_hardware_btn.clicked.connect(self.activate_hardware)
        self.deactivate_hardware_btn.clicked.connect(self.deactivate_hardware)
        self.home_pos_btn.clicked.connect(self.home_position)
        self.smp_name.returnPressed.connect(self.update_sample_name)
        self.smp_name.focusOutEvent = lambda event: (self.update_sample_name(), QtWidgets.QLineEdit.focusOutEvent(self.smp_name, event))

    def connect_groupbox_signals(self) -> None:
        """Verbindet alle relevanten Widgets in GroupBoxen mit Überwachungsfunktionen."""
        for group_box in self.findChildren(QGroupBox):
            # QLineEdit: Signale verbinden
            for line_edit in group_box.findChildren(QLineEdit):
                line_edit.old_text = line_edit.text()
                line_edit.editingFinished.connect(lambda le=line_edit: self.check_parameter_change(le))
            # QComboBox: Signale verbinden
            for combo_box in group_box.findChildren(QComboBox):
                combo_box.currentTextChanged.connect(self.accept_parameter)
            for check_box in group_box.findChildren(QtWidgets.QCheckBox):
                check_box.stateChanged.connect(self.accept_parameter)
        self.grp_box_connected = True

    def safe_float(self, text: str, default: float = 0.0) -> float:
        """
        Sichere Konvertierung von String zu Float.
        """
        try:
            clean_text = text.strip().replace(",", ".")
            return float(clean_text)
        except (ValueError, TypeError):
            self.logger.warning(f"Konvertierung zu Float fehlgeschlagen: '{text}' -> Standard: {default}")
            return default

    def safe_int(self, text: str, default: int = 0) -> int:
        """
        Sichere Konvertierung von String zu Integer.
        """
        try:
            clean_text = text.strip().replace(",", ".")
            return int(float(clean_text))
        except (ValueError, TypeError):
            self.logger.warning(f"Konvertierung zu Integer fehlgeschlagen: '{text}' -> Standard: {default}")
            return default

    def check_parameter_change(self, source):
        """
        Eingabeverarbeitung für QLineEdit-Felder.
        """
        if not isinstance(source, QtWidgets.QLineEdit):
            return

        sender_name = self.sender().objectName() if self.sender() else "Unknown"
        current_text = source.text().strip()

        self.logger.info(f"Parameter '{sender_name}' geändert zu: '{current_text}'")

        # Validierung: Leer = "0"
        if not current_text:
            source.setText("0")
            self.logger.info(f"Leeres Feld '{sender_name}' auf '0' gesetzt")

        # Komma durch Punkt ersetzen
        if "," in current_text:
            corrected_text = current_text.replace(",", ".")
            source.setText(corrected_text)
            self.logger.info(f"Komma in '{sender_name}' durch Punkt ersetzt")

        self.accept_parameter()

    def setup_Logger(self) -> None:
        """
        Initialisiert den Logger nur für GUI-Anzeige.
        """
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        formatter = WrappingFormatter("%(asctime)-32.24s  %(levelname)-16.16s %(name)-16.16s %(message)s")

        self.gui_handler = GuiLogger()
        self.gui_handler.logger_signal.connect(self.msg)
        self.gui_handler.setLevel(logging.INFO)
        self.gui_handler.setFormatter(formatter)
        root_logger.addHandler(self.gui_handler)

        self.logger = logging.getLogger("MAIN")
        self.logger.info("Logger initialized")

    def msg(self, msg="No message included", level=logging.INFO, name="Unknown") -> None:
        """Zeigt Nachrichten im Log-Bereich an."""
        # Farben je nach Log-Level
        if level == logging.DEBUG:
            color = "blue"
        elif level == logging.INFO:
            color = "white"
        elif level == logging.WARNING:
            color = "#E6CF6A"
        elif level == logging.ERROR:
            color = "#FF5555"
        elif level == logging.CRITICAL:
            color = "purple"
        else:
            color = "black"

        self.plainLog.setTextColor(QColor(color))
        self.plainLog.setFontWeight(QFont.Weight.Bold if level >= logging.WARNING else QFont.Weight.Normal)
        self.plainLog.append(msg)
        self.plainLog.moveCursor(QTextCursor.MoveOperation.End)

    def setup_torque_graph_widget(self):
        """Erstellt PyQtGraph für Torque vs. Angle Plot."""
        graph_layout = QVBoxLayout(self.force_graph_frame)
        self.graph_widget = pg.PlotWidget()

        # Achsen konfigurieren
        self.graph_widget.setLabel("left", "Torque", units="Nm", color="white", **{"font-size": "10pt"})
        self.graph_widget.setLabel("bottom", "Angle", units="°", color="white", **{"font-size": "10pt"})
        self.graph_widget.setBackground("#262a32")
        self.graph_widget.showGrid(x=True, y=True)

        # Kurve für Torque vs. Angle
        self.torque_curve = self.graph_widget.plot(
            pen=pg.mkPen(color="#0077FF", width=2), symbol="o", symbolBrush="#0077FF", symbolSize=4, name="Torque vs. Angle"
        )

        # Achsen-Styling
        self.graph_widget.getAxis("left").setStyle(tickFont=QFont("Arial", 10))
        self.graph_widget.getAxis("bottom").setStyle(tickFont=QFont("Arial", 10))
        self.graph_widget.getAxis("left").setTextPen("w")
        self.graph_widget.getAxis("bottom").setTextPen("w")

        graph_layout.addWidget(self.graph_widget)

    # ---------- Parameter Funktionen ----------

    def init_parameters(self) -> None:
        """
        Parameter-Initialisierung mit Standardwerten.
        """
        # Sample-Name setzen
        self.smp_name.setText(self.sample_name)

        # Max-Werte initialisieren
        self.max_angle.setText(str(DEFAULT_MAX_ANGLE))
        self.max_torque.setText(str(DEFAULT_MAX_TORQUE))
        self.max_velocity.setText(str(DEFAULT_MAX_VELOCITY))

        # GUI-Signale verbinden
        if not self.grp_box_connected:
            self.connect_groupbox_signals()

        self.logger.info("Parameter mit Standardwerten initialisiert")

    def get_max_angle(self) -> float:
        """Liest den Max Angle Wert aus der GUI."""
        return self.safe_float(self.max_angle.text(), DEFAULT_MAX_ANGLE)

    def get_max_torque(self) -> float:
        """Liest den Max Torque Wert aus der GUI."""
        return self.safe_float(self.max_torque.text(), DEFAULT_MAX_TORQUE)

    def get_max_velocity(self) -> float:
        """Liest den Max Velocity Wert aus der GUI."""
        return self.safe_float(self.max_velocity.text(), DEFAULT_MAX_VELOCITY)

    def accept_parameter(self) -> None:
        """Parameter-Akzeptierung."""
        if getattr(self, "block_parameter_signals", False):
            return
        self.logger.debug("Parameter akzeptiert")

    def update_sample_name(self) -> None:
        """Aktualisiert den Sample-Namen."""
        if not self.is_process_running:
            self.sample_name = self.smp_name.text().strip()
            self.logger.info(f"Sample-Name aktualisiert: {self.sample_name}")

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
        """Aktiviert die Hardware (NI-6000 und N5 Nanotec)."""
        if self.are_instruments_initialized:
            self.logger.warning("Hardware bereits initialisiert")
            return

        QtWidgets.QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.logger.info("Aktiviere Hardware...")

        success = True
        error_messages = []

        # --- NI-6000 DAQ aktivieren ---
        try:
            self.logger.info(f"Initialisiere NI-6000 DAQ (Kanal: {DAQ_CHANNEL_TORQUE})...")
            self.nidaqmx_task = DAQmxTask(DAQ_CHANNEL_TORQUE, demo_mode=DEMO_MODE)
            self.nidaqmx_task.create_nidaqmx_task()

            if self.nidaqmx_task.is_task_created:
                self.logger.info("✓ NI-6000 DAQ erfolgreich initialisiert")
                self.nidaq_activ_led.setStyleSheet("background-color: green; border-radius: 12px; border: 2px solid black;")
            else:
                error_messages.append("NI-6000 DAQ konnte nicht initialisiert werden")
                success = False
                self.nidaq_activ_led.setStyleSheet("background-color: red; border-radius: 12px; border: 2px solid black;")
        except Exception as e:
            self.logger.error(f"✗ Fehler beim Initialisieren der NI-6000 DAQ: {e}")
            error_messages.append(f"NI-6000 DAQ Fehler: {e}")
            success = False
            self.nidaq_activ_led.setStyleSheet("background-color: red; border-radius: 12px; border: 2px solid black;")

        # --- N5 Nanotec Motor aktivieren ---
        try:
            self.logger.info(f"Initialisiere N5 Nanotec Controller (IP: {N5_IP_ADDRESS})...")
            self.motor_controller = N5NanotecController(demo_mode=DEMO_MODE)

            if self.motor_controller.connect():
                self.logger.info("✓ N5 Nanotec Controller erfolgreich verbunden")
                self.N5_contr_activ_led.setStyleSheet("background-color: green; border-radius: 12px; border: 2px solid black;")
            else:
                error_messages.append("N5 Nanotec Controller konnte nicht verbunden werden")
                success = False
                self.N5_contr_activ_led.setStyleSheet("background-color: red; border-radius: 12px; border: 2px solid black;")
        except Exception as e:
            self.logger.error(f"✗ Fehler beim Verbinden des N5 Nanotec Controllers: {e}")
            error_messages.append(f"N5 Nanotec Fehler: {e}")
            success = False
            self.N5_contr_activ_led.setStyleSheet("background-color: red; border-radius: 12px; border: 2px solid black;")

        QtWidgets.QApplication.restoreOverrideCursor()

        if success:
            self.are_instruments_initialized = True
            self.logger.info("✓ Hardware erfolgreich aktiviert")
            QMessageBox.information(self, "Erfolg", "Hardware erfolgreich aktiviert!\n\n✓ NI-6000 DAQ\n✓ N5 Nanotec Controller")
        else:
            self.are_instruments_initialized = False
            error_text = "\n".join(error_messages)
            self.logger.error(f"✗ Hardware-Aktivierung fehlgeschlagen:\n{error_text}")
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
        self.nidaq_activ_led.setStyleSheet("background-color: red; border-radius: 12px; border: 2px solid black;")
        self.N5_contr_activ_led.setStyleSheet("background-color: red; border-radius: 12px; border: 2px solid black;")

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

        # Motor in Home-Position fahren
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
            # Position vom Motor lesen
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
        max_angle = self.get_max_angle()
        max_torque = self.get_max_torque()
        max_velocity = self.get_max_velocity()

        self.logger.info("=" * 60)
        self.logger.info("MESSUNG STARTEN")
        self.logger.info(f"Max Angle: {max_angle}°")
        self.logger.info(f"Max Torque: {max_torque} Nm")
        self.logger.info(f"Max Velocity: {max_velocity}°/s")
        self.logger.info("=" * 60)

        # Startzeit speichern
        self.start_time_timestamp = datetime.now()
        self.logger.info(f"Startzeit: {self.start_time_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

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
                f.write(f"# Max Angle: {self.get_max_angle()}° | Max Torque: {self.get_max_torque()} Nm | Max Velocity: {self.get_max_velocity()}°/s\n")
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

        # Position vom Motor lesen
        angle = 0.0
        if self.motor_controller and self.motor_controller.is_connected:
            angle = self.motor_controller.get_position()

        # Spannung vom DAQ lesen
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
        max_angle = self.get_max_angle()
        max_torque = self.get_max_torque()

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
