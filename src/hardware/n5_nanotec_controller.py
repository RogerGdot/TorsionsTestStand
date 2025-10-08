"""
N5 Nanotec Stepper Motor Controller
====================================
Closed-Loop Position Control via Modbus TCP.

Hardware:
- N5 Nanotec Schrittmotor
- Modbus TCP Kommunikation
- Closed-Loop Position Control
"""

import time

try:
    from pymodbus.client import ModbusTcpClient
    from pymodbus.exceptions import ModbusException

    PYMODBUS_AVAILABLE = True
except ImportError:
    PYMODBUS_AVAILABLE = False


class N5NanotecController:
    """
    N5 Nanotec Stepper Motor Controller via Modbus TCP.
    Closed-Loop Position Control mit Positionsabfrage.
    """

    def __init__(
        self,
        ip_address: str = "192.168.0.100",
        port: int = 502,
        slave_id: int = 1,
        demo_mode: bool = True,
    ):
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
