"""
Motor Controller Base Class
============================
Abstract Base Class für verschiedene Motor-Controller.

Definiert die gemeinsame Schnittstelle für:
- Nanotec Stepper Motor (NanoLib)
- Trinamic Stepper Motor (PyTrinamic)
"""

from abc import ABC, abstractmethod


class MotorControllerBase(ABC):
    """
    Abstrakte Basisklasse für Motor-Controller.
    Alle Motor-Controller müssen diese Methoden implementieren.
    """

    def __init__(self, demo_mode: bool = True):
        """
        Initialisiert den Motor-Controller.

        Args:
            demo_mode (bool): Demo-Modus für Simulation
        """
        self.demo_mode = demo_mode
        self.is_connected = False
        self.is_moving = False
        self.current_position = 0.0  # Position in Grad
        self.velocity = 0.0  # Geschwindigkeit in Grad/s

    @abstractmethod
    def connect(self) -> bool:
        """
        Verbindet mit dem Motor-Controller.

        Returns:
            bool: True wenn erfolgreich verbunden
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Trennt die Verbindung zum Motor-Controller."""
        pass

    @abstractmethod
    def home_position(self) -> bool:
        """
        Fährt den Motor in die Home-Position (0°).

        Returns:
            bool: True wenn erfolgreich
        """
        pass

    @abstractmethod
    def move_continuous(self, velocity: float) -> bool:
        """
        Startet kontinuierliche Bewegung mit konstanter Geschwindigkeit.
        Motor läuft bis zum Stop-Befehl.

        Args:
            velocity (float): Geschwindigkeit in Grad/s (+ = Uhrzeiger, - = Gegen Uhrzeiger)

        Returns:
            bool: True wenn erfolgreich gestartet
        """
        pass

    @abstractmethod
    def stop_movement(self) -> bool:
        """
        Stoppt die aktuelle Bewegung sofort.

        Returns:
            bool: True wenn erfolgreich gestoppt
        """
        pass

    @abstractmethod
    def get_position(self) -> float:
        """
        Liest die aktuelle Position vom Motor-Controller.

        Returns:
            float: Aktuelle Position in Grad
        """
        pass

    @abstractmethod
    def is_motor_moving(self) -> bool:
        """
        Prüft, ob der Motor sich bewegt.

        Returns:
            bool: True wenn Motor in Bewegung
        """
        pass

    def get_velocity(self) -> float:
        """
        Gibt die aktuelle Geschwindigkeit zurück.

        Returns:
            float: Geschwindigkeit in Grad/s
        """
        return self.velocity
