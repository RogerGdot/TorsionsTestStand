"""
NI-6000 DAQ Controller
======================
Hardware-abstrakte Klasse für Datenerfassung mit NI-6000.
Unterstützt ±10V Messbereich für DF-30 Sensor.

Hardware:
- NI-6000 DAQ
- ±10V Analog Input
- DF-30 Drehmoment-Sensor (±20 Nm)
"""

try:
    import nidaqmx
    from nidaqmx.constants import TerminalConfiguration

    NIDAQMX_AVAILABLE = True
except ImportError:
    NIDAQMX_AVAILABLE = False

from .demo_simulator import DemoHardwareSimulator


class DAQmxTask:
    """
    Hardware-abstrakte Klasse für Datenerfassung mit NI-6000.
    Unterstützt ±10V Messbereich für DF-30 Sensor.
    """

    def __init__(
        self,
        torque_channel: str = "Dev1/ai0",
        angle_channel: str = "Dev1/ai1",
        voltage_range: float = 10.0,
        torque_scale: float = 2.0,
        angle_voltage_min: float = 0.0,
        angle_voltage_max: float = 10.0,
        angle_min_deg: float = 0.0,
        angle_max_deg: float = 360.0,
        demo_mode: bool = True,
    ):
        """
        Initialisiert eine DAQ Task für die Messung von Drehmoment und Winkel.

        Args:
            torque_channel (str): DAQ-Kanal für Drehmomentmessung (z.B. "Dev1/ai0")
            angle_channel (str): DAQ-Kanal für Winkelmessung (z.B. "Dev1/ai1")
            voltage_range (float): Spannungsbereich in V (±10V für Torque)
            torque_scale (float): Skalierung Nm/V (Standard: 2.0 für DF-30)
            angle_voltage_min (float): Minimale Winkelspannung [V] (Standard: 0.0)
            angle_voltage_max (float): Maximale Winkelspannung [V] (Standard: 10.0)
            angle_min_deg (float): Minimaler Winkel [Grad] (Standard: 0.0)
            angle_max_deg (float): Maximaler Winkel [Grad] (Standard: 360.0)
            demo_mode (bool): Demo-Modus für Simulation
        """
        self.nidaqmx_task = None
        self.torque_channel = torque_channel
        self.angle_channel = angle_channel
        self.voltage_range = voltage_range
        self.torque_scale = torque_scale
        self.angle_voltage_min = angle_voltage_min
        self.angle_voltage_max = angle_voltage_max
        self.angle_min_deg = angle_min_deg
        self.angle_max_deg = angle_max_deg
        self.demo_mode = demo_mode
        self.is_task_created = False
        self.demo_simulator = DemoHardwareSimulator(torque_scale=torque_scale) if demo_mode else None

    def create_nidaqmx_task(self):
        """
        Erzeugt eine NI DAQmx Task für die konfigurierten AI-Kanäle (Torque + Angle).
        """
        if self.demo_mode:
            print("[DEMO] NI-6000 DAQ - Simulation aktiv (Torque + Angle)")
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
                self.torque_channel,
                terminal_config=TerminalConfiguration.DEFAULT,
                min_val=-self.voltage_range,
                max_val=self.voltage_range,
            )

            # Angle-Kanal mit 0-10V Range hinzufügen (Motrona Analog-Ausgang)
            task.ai_channels.add_ai_voltage_chan(
                self.angle_channel,
                terminal_config=TerminalConfiguration.RSE,
                min_val=self.angle_voltage_min,
                max_val=self.angle_voltage_max,
            )

            self.nidaqmx_task = task
            self.is_task_created = True
            print(
                f"NIDAQmx task erstellt: {self.torque_channel} (±{self.voltage_range}V), {self.angle_channel} ({self.angle_voltage_min}-{self.angle_voltage_max}V)"
            )
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

        # Echte Hardware: Lese Spannung von DAQ (nur Torque-Kanal = Index 0)
        values = task.read(number_of_samples_per_channel=1)
        if isinstance(values, list) and len(values) > 0:
            # Bei Multi-Channel Task: values ist Liste von Listen [[torque], [angle]]
            if isinstance(values[0], list):
                return float(values[0][0])
            else:
                return float(values[0])
        else:
            return float(values)

    def read_angle_voltage(self) -> float:
        """
        Liest die Spannung vom Winkel-Sensor (SSI Encoder via Motrona Konverter).

        Returns:
            float: Spannung in V (0-10V entspricht 0-360°)
        """
        if self.demo_mode:
            # Demo-Modus: Simuliere Winkelspannung basierend auf aktuellem Demo-Winkel
            angle = self.demo_simulator.current_angle if self.demo_simulator else 0.0
            voltage = self.scale_angle_to_voltage(angle)
            return voltage

        task = self.nidaqmx_task
        if task is None:
            raise RuntimeError("Task ist nicht initialisiert")

        # Echte Hardware: Lese Spannung von DAQ (Angle-Kanal = Index 1)
        values = task.read(number_of_samples_per_channel=1)
        if isinstance(values, list) and len(values) > 1:
            # Bei Multi-Channel Task: values ist Liste von Listen [[torque], [angle]]
            if isinstance(values[1], list):
                return float(values[1][0])
            else:
                return float(values[1])
        else:
            return 0.0

    def scale_voltage_to_angle(self, voltage: float) -> float:
        """
        Skaliert Spannung zu Winkel (0-10V → 0-360°).

        Args:
            voltage (float): Gemessene Spannung [V]

        Returns:
            float: Winkel in Grad [0-360°]
        """
        voltage_range = self.angle_voltage_max - self.angle_voltage_min
        angle_range = self.angle_max_deg - self.angle_min_deg

        if voltage_range == 0:
            return self.angle_min_deg

        angle = ((voltage - self.angle_voltage_min) / voltage_range) * angle_range + self.angle_min_deg

        # Begrenze auf gültigen Bereich
        angle = max(self.angle_min_deg, min(self.angle_max_deg, angle))

        return angle

    def scale_angle_to_voltage(self, angle: float) -> float:
        """
        Skaliert Winkel zu Spannung (0-360° → 0-10V) - für Demo-Modus.

        Args:
            angle (float): Winkel in Grad

        Returns:
            float: Spannung [V]
        """
        angle_range = self.angle_max_deg - self.angle_min_deg
        voltage_range = self.angle_voltage_max - self.angle_voltage_min

        if angle_range == 0:
            return self.angle_voltage_min

        # Normalisiere Winkel auf 0-360° Bereich
        normalized_angle = angle % self.angle_max_deg

        voltage = ((normalized_angle - self.angle_min_deg) / angle_range) * voltage_range + self.angle_voltage_min

        return voltage

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
