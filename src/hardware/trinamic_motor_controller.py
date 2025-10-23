"""
Trinamic Motor Controller
==========================
Stepper Motor Control mit Trinamic Steprocker via PyTrinamic.

Hardware:
- Trinamic Stepper Motor
- Trinamic Steprocker Board
- PyTrinamic Kommunikation
"""

import time

try:
    from pytrinamic.connections import ConnectionManager
    from pytrinamic.modules import TMCM1240

    PYTRINAMIC_AVAILABLE = True
except ImportError:
    PYTRINAMIC_AVAILABLE = False

from .motor_controller_base import MotorControllerBase


class TrinamicMotorController(MotorControllerBase):
    """
    Trinamic Stepper Motor Controller via PyTrinamic.
    Unterstützt kontinuierliche Bewegung mit konstanter Geschwindigkeit.
    """

    def __init__(
        self,
        port: str = "COM3",
        motor_id: int = 0,
        demo_mode: bool = True,
    ):
        """
        Initialisiert den Trinamic Motor Controller.

        Args:
            port (str): COM-Port des Steprocker (z.B. "COM3")
            motor_id (int): Motor ID (Standard: 0)
            demo_mode (bool): Demo-Modus für Simulation
        """
        super().__init__(demo_mode)
        self.port = port
        self.motor_id = motor_id
        self.connection = None
        self.module = None

        # Demo-Modus Simulation
        self.demo_start_time = None
        self.demo_start_position = 0.0

    def connect(self) -> bool:
        """Verbindet mit dem Trinamic Steprocker."""
        if self.demo_mode:
            print("[DEMO] Trinamic Motor Controller - Simulation aktiv")
            self.is_connected = True
            self.current_position = 0.0
            return True

        if not PYTRINAMIC_AVAILABLE:
            print("PyTrinamic nicht verfügbar - Trinamic Steuerung nicht möglich")
            return False

        try:
            # Verbindung zum Steprocker aufbauen
            self.connection = ConnectionManager(argList=["--port", self.port]).connect()
            self.module = TMCM1240(self.connection)

            self.is_connected = True
            print(f"Trinamic Steprocker verbunden: {self.port}")
            return True

        except Exception as e:
            print(f"Trinamic Verbindungsfehler: {e}")
            return False

    def disconnect(self) -> None:
        """Trennt die Verbindung zum Trinamic Steprocker."""
        if self.demo_mode:
            self.is_connected = False
            return

        if self.connection:
            try:
                self.connection.close()
                self.is_connected = False
                print("Trinamic Steprocker getrennt")
            except Exception as e:
                print(f"Fehler beim Trennen: {e}")

    def home_position(self) -> bool:
        """Fährt den Motor in die Home-Position (0°)."""
        if not self.is_connected:
            print("Trinamic nicht verbunden")
            return False

        if self.demo_mode:
            print("[DEMO] Trinamic fährt in Home-Position (0°)")
            self.current_position = 0.0
            self.is_moving = False
            return True

        try:
            # Homing durchführen (Reference Search)
            self.module.reference_search(self.motor_id)
            self.current_position = 0.0
            print("Trinamic: Homing abgeschlossen")
            return True
        except Exception as e:
            print(f"Homing-Fehler: {e}")
            return False

    def move_continuous(self, velocity: float) -> bool:
        """
        Startet kontinuierliche Bewegung mit konstanter Geschwindigkeit.

        Args:
            velocity (float): Geschwindigkeit in Grad/s (+ = Uhrzeiger, - = Gegen Uhrzeiger)

        Returns:
            bool: True wenn erfolgreich
        """
        if not self.is_connected:
            print("Trinamic nicht verbunden")
            return False

        self.velocity = velocity
        self.is_moving = True

        if self.demo_mode:
            self.demo_start_time = time.time()
            self.demo_start_position = self.current_position
            print(f"[DEMO] Trinamic startet Bewegung mit {velocity:.2f}°/s")
            return True

        try:
            # Geschwindigkeit in Trinamic-Einheiten umrechnen (gerätespezifisch)
            # Beispiel: velocity_units = int(velocity * steps_per_degree)
            velocity_units = int(velocity * 10)  # Placeholder

            # Rotate-Befehl für kontinuierliche Bewegung
            self.module.rotate(self.motor_id, velocity_units)
            print(f"Trinamic: Kontinuierliche Bewegung mit {velocity:.2f}°/s")
            return True
        except Exception as e:
            print(f"Bewegungsfehler: {e}")
            return False

    def stop_movement(self) -> bool:
        """Stoppt die aktuelle Bewegung sofort."""
        if not self.is_connected:
            return False

        self.is_moving = False
        self.velocity = 0.0

        if self.demo_mode:
            print(f"[DEMO] Trinamic gestoppt bei Position {self.current_position:.2f}°")
            return True

        try:
            # Motor stoppen
            self.module.stop(self.motor_id)
            print("Trinamic: Bewegung gestoppt")
            return True
        except Exception as e:
            print(f"Stop-Fehler: {e}")
            return False

    def get_position(self) -> float:
        """Liest die aktuelle Position vom Trinamic Motor."""
        if not self.is_connected:
            return 0.0

        if self.demo_mode:
            # Simuliere Bewegung basierend auf Geschwindigkeit und Zeit
            if self.is_moving and self.demo_start_time is not None:
                elapsed_time = time.time() - self.demo_start_time
                self.current_position = self.demo_start_position + (self.velocity * elapsed_time)
            return self.current_position

        try:
            # Echte Positionsabfrage
            position_units = self.module.get_axis_parameter(self.module.APs.ActualPosition, self.motor_id)
            # Position in Grad umrechnen (gerätespezifisch)
            self.current_position = position_units / 10.0  # Placeholder
            return self.current_position
        except Exception as e:
            print(f"Positionsabfrage-Fehler: {e}")
            return 0.0

    def is_motor_moving(self) -> bool:
        """Prüft, ob der Motor sich bewegt."""
        return self.is_moving
