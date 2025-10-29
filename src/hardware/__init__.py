"""
Hardware Module für Torsions Test Stand
========================================
Enthält alle Hardware-Controller-Klassen:
- N6 Nanotec Motor Controller (mit SSI-Encoder über Modbus TCP)
- NI-6000 DAQ Controller (nur Drehmoment)
- Demo Hardware Simulator
"""

from .daq_controller import DAQmxTask
from .demo_simulator import DemoHardwareSimulator
from .motor_controller_base import MotorControllerBase
from .n6_nanotec_controller import N6NanotecController

__all__ = [
    "DAQmxTask",
    "DemoHardwareSimulator",
    "MotorControllerBase",
    "N6NanotecController",
]
