"""
Nanotec Motor Controller
=========================
Stepper Motor Control mit Nanotec Driver via NanoLib.

Hardware:
- Nanotec Schrittmotor
- Nanotec Driver (z.B. C5-E, N5)
- NanoLib Kommunikation
"""

import time

try:
    from nanotec_nanolib import Nanolib, NanolibHelper

    NANOLIB_AVAILABLE = True
except ImportError:
    NANOLIB_AVAILABLE = False

from .motor_controller_base import MotorControllerBase


class NanotecMotorController(MotorControllerBase):
    """
    Nanotec Stepper Motor Controller via NanoLib.
    Unterstützt kontinuierliche Bewegung mit konstanter Geschwindigkeit.
    """

    def __init__(self, bus_hardware: str = "ixxat", demo_mode: bool = True):
        """
        Initialisiert den Nanotec Motor Controller.

        Args:
            bus_hardware (str): Bus-Hardware ("ixxat", "kvaser", "socketcan")
            demo_mode (bool): Demo-Modus für Simulation
        """
        super().__init__(demo_mode)
        self.bus_hardware = bus_hardware
        self.nanolib_accessor = None
        self.device_handle = None

        # Demo-Modus Simulation
        self.demo_start_time = None
        self.demo_start_position = 0.0

    def connect(self) -> bool:
        """Verbindet mit dem Nanotec Motor via NanoLib."""
        if self.demo_mode:
            print("[DEMO] Nanotec Motor Controller - Simulation aktiv")
            self.is_connected = True
            self.current_position = 0.0
            return True

        if not NANOLIB_AVAILABLE:
            print("NanoLib nicht verfügbar - Nanotec Steuerung nicht möglich")
            return False

        try:
            # NanoLib Helper verwenden für einfachere Initialisierung
            helper = NanolibHelper()
            helper.setup()

            # Geräte scannen
            device_ids = helper.scan_devices()
            if not device_ids:
                print("Keine Nanotec-Geräte gefunden")
                return False

            # Erstes Gerät öffnen
            device_id = device_ids[0]
            device_handle = helper.create_device(device_id)
            helper.connect_device(device_handle)

            # Motor aktivieren (Enable)
            helper.enable_device(device_handle)

            self.nanolib_accessor = helper
            self.device_handle = device_handle
            self.is_connected = True

            print(f"Nanotec Motor verbunden: {device_id.get_device_name()}")
            return True

        except Exception as e:
            print(f"Nanotec Verbindungsfehler: {e}")
            return False

    def disconnect(self) -> None:
        """Trennt die Verbindung zum Nanotec Motor."""
        if self.demo_mode:
            self.is_connected = False
            return

        if self.nanolib_accessor and self.device_handle:
            try:
                # Motor deaktivieren (Disable)
                self.nanolib_accessor.disable_device(self.device_handle)
                # Verbindung trennen
                self.nanolib_accessor.disconnect_device(self.device_handle)
                self.is_connected = False
                print("Nanotec Motor getrennt")
            except Exception as e:
                print(f"Fehler beim Trennen: {e}")

    def home_position(self) -> bool:
        """Fährt den Motor in die Home-Position (0°)."""
        if not self.is_connected:
            print("Nanotec nicht verbunden")
            return False

        if self.demo_mode:
            print("[DEMO] Nanotec fährt in Home-Position (0°)")
            self.current_position = 0.0
            self.is_moving = False
            return True

        try:
            # Position auf 0 setzen (aktuelle Position als Referenz)
            self.nanolib_accessor.write_number(
                self.device_handle,
                0,  # Position = 0
                NanolibHelper.OD_POSITION_ACTUAL_VALUE,
            )
            self.current_position = 0.0
            self.is_moving = False
            print("Nanotec: Home-Position gesetzt")
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
            print("Nanotec nicht verbunden")
            return False

        self.velocity = velocity
        self.is_moving = True

        if self.demo_mode:
            self.demo_start_time = time.time()
            self.demo_start_position = self.current_position
            print(f"[DEMO] Nanotec startet Bewegung mit {velocity:.2f}°/s")
            return True

        try:
            # Velocity Mode (Profile Velocity Mode) setzen
            # OdIndex für Mode of Operation: 0x6060
            self.nanolib_accessor.write_number(
                self.device_handle,
                3,  # 3 = Profile Velocity Mode
                NanolibHelper.OD_MODES_OF_OPERATION,
            )

            # Geschwindigkeit setzen (in RPM oder motor-spezifischen Einheiten konvertieren)
            # TODO: Umrechnung von Grad/s zu Motor-Einheiten (abhängig von Getriebe/Auflösung)
            velocity_units = int(velocity * 10)  # Placeholder - muss angepasst werden!

            self.nanolib_accessor.write_number(self.device_handle, velocity_units, NanolibHelper.OD_TARGET_VELOCITY)

            # Motor starten (Control Word setzen)
            # Bit 4 setzen für "New Set-Point"
            self.nanolib_accessor.write_number(
                self.device_handle,
                0x000F,  # Enable Operation
                NanolibHelper.OD_CONTROL_WORD,
            )

            print(f"Nanotec: Kontinuierliche Bewegung mit {velocity:.2f}°/s gestartet")
            return True
        except Exception as e:
            print(f"Bewegungsfehler: {e}")
            self.is_moving = False
            return False

    def stop_movement(self) -> bool:
        """Stoppt die aktuelle Bewegung sofort."""
        if not self.is_connected:
            return False

        self.is_moving = False
        self.velocity = 0.0

        if self.demo_mode:
            print(f"[DEMO] Nanotec gestoppt bei Position {self.current_position:.2f}°")
            return True

        try:
            # Quick Stop ausführen (Control Word Bit 2 = 0)
            # Control Word: 0x0006 = Quick Stop
            self.nanolib_accessor.write_number(
                self.device_handle,
                0x0006,  # Quick Stop
                NanolibHelper.OD_CONTROL_WORD,
            )

            # Danach wieder Enable setzen
            time.sleep(0.1)
            self.nanolib_accessor.write_number(
                self.device_handle,
                0x000F,  # Enable Operation
                NanolibHelper.OD_CONTROL_WORD,
            )

            print("Nanotec: Bewegung gestoppt")
            return True
        except Exception as e:
            print(f"Stop-Fehler: {e}")
            return False

    def get_position(self) -> float:
        """Liest die aktuelle Position vom Nanotec Motor."""
        if not self.is_connected:
            return 0.0

        if self.demo_mode:
            # Simuliere Bewegung basierend auf Geschwindigkeit und Zeit
            if self.is_moving and self.demo_start_time is not None:
                elapsed_time = time.time() - self.demo_start_time
                self.current_position = self.demo_start_position + (self.velocity * elapsed_time)
            return self.current_position

        try:
            # Position auslesen (OD_POSITION_ACTUAL_VALUE)
            position_units = self.nanolib_accessor.read_number(self.device_handle, NanolibHelper.OD_POSITION_ACTUAL_VALUE)

            # Position in Grad umrechnen (abhängig von Motor-Auflösung)
            # TODO: Umrechnung von Motor-Einheiten zu Grad (muss kalibriert werden)
            self.current_position = position_units / 10.0  # Placeholder

            return self.current_position
        except Exception as e:
            print(f"Positionsabfrage-Fehler: {e}")
            return 0.0

    def is_motor_moving(self) -> bool:
        """Prüft, ob der Motor sich bewegt."""
        return self.is_moving
