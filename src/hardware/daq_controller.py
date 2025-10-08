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
        voltage_range: float = 10.0,
        torque_scale: float = 2.0,
        demo_mode: bool = True,
    ):
        """
        Initialisiert eine DAQ Task für die Messung von Drehmoment.

        Args:
            torque_channel (str): DAQ-Kanal für Drehmomentmessung (z.B. "Dev1/ai0")
            voltage_range (float): Spannungsbereich in V (±10V)
            torque_scale (float): Skalierung Nm/V (Standard: 2.0 für DF-30)
            demo_mode (bool): Demo-Modus für Simulation
        """
        self.nidaqmx_task = None
        self.torque_channel = torque_channel
        self.voltage_range = voltage_range
        self.torque_scale = torque_scale
        self.demo_mode = demo_mode
        self.is_task_created = False
        self.demo_simulator = DemoHardwareSimulator(torque_scale=torque_scale) if demo_mode else None

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
                self.torque_channel,
                terminal_config=TerminalConfiguration.DEFAULT,
                min_val=-self.voltage_range,
                max_val=self.voltage_range,
            )
            self.nidaqmx_task = task
            self.is_task_created = True
            print(f"NIDAQmx task erstellt: {self.torque_channel} (±{self.voltage_range}V)")
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
