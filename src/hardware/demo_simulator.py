"""
Demo Hardware Simulator
========================
Simuliert DF-30 Sensor und N5 Nanotec Motor für Tests ohne echte Hardware.

Features:
- Realistische Torque-Simulation basierend auf Winkel
- Nullpunkt-Kalibrierung
- Rauschen für realistische Daten
"""

import random


class DemoHardwareSimulator:
    """
    Demo-Hardware-Simulator für Tests ohne echte Hardware.
    Simuliert DF-30 Sensor und N5 Nanotec Motor.
    """

    def __init__(self, torque_scale: float = 2.0):
        """
        Initialisiert den Demo-Simulator.

        Args:
            torque_scale (float): Skalierungsfaktor Nm/V (Standard: 2.0 für DF-30)
        """
        self.torque_offset = 0.0  # Torque-Nullpunkt nach Kalibrierung
        self.current_angle = 0.0  # Aktueller Winkel
        self.is_running = False
        self.start_time = None
        self.torque_scale = torque_scale

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
        voltage = torque / self.torque_scale
        return voltage

    def calibrate_zero(self) -> None:
        """Kalibriert den Nullpunkt (aktuelles Drehmoment = 0)."""
        current_torque = self.get_simulated_torque(self.current_angle)
        self.torque_offset = -current_torque
        print(f"[DEMO] Torque kalibriert (Offset: {self.torque_offset:.3f} Nm)")
