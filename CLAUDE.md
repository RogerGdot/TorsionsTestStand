# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Torsions Test Stand** control software for a technical school graduation project. It controls a torsion testing apparatus that measures torque and angle using:
- **DF-30 Torque Sensor** (±20 Nm, ±10V output) connected to **NI-6000 DAQ** analog input
- **N6 Nanotec Stepper Motor** with NanoLib (Modbus TCP) and closed-loop position control
- **SSI Encoder** (13-bit, 8192 counts/rev) read directly by N6 controller for angle measurement

The software supports a **demo mode** for testing without hardware and provides live visualization, automatic data logging, and safety features.

## Running the Application

### Demo Mode (No Hardware Required)
```powershell
# Ensure DEMO_MODE = True in main.py (line 133)
python main.py
```

### With Real Hardware
```powershell
# Set DEMO_MODE = False in main.py (line 133)
python main.py
```

Note: Hardware test programs have been removed. Use demo mode for testing without hardware, or use the "Activate Hardware" button in the GUI to validate real hardware connectivity.

### Installation
```powershell
pip install -r requirements.txt
```

Required dependencies:
- `nidaqmx`: Requires NI-DAQmx Runtime drivers for real hardware (download from ni.com)
- `nanotec-nanolib`: NanoLib Python library for N6 Nanotec controller communication
- `PyQt6`, `pyqtgraph`: GUI and visualization
- `numpy`: Data processing

## Architecture

### Module Structure

```
src/
├── hardware/           # Hardware abstraction layer
│   ├── __init__.py
│   ├── motor_controller_base.py    # Abstract base class for motor controllers
│   ├── n6_nanotec_controller.py    # N6 Nanotec with NanoLib (Modbus TCP)
│   ├── daq_controller.py           # NI-6000 DAQ wrapper (torque sensor only)
│   └── demo_simulator.py           # Hardware simulation
├── gui/
│   ├── torsions_test_stand.ui      # Qt Designer UI file
│   └── stylesheet.py               # Dark theme stylesheet
└── utils/
    └── logger_helper.py            # GUI logger integration
```

### Key Design Patterns

**Hardware Abstraction:** All hardware controllers (`N6NanotecController`, `DAQmxTask`) support both real and demo modes. Pass `demo_mode=True` to use simulation instead of physical hardware. Motor controllers inherit from `MotorControllerBase` abstract class.

**Main Event Flow:**
1. User clicks "Activate Hardware" → Initializes DAQ and motor controller
2. User clicks "Home Position" → Calibrates motor to 0° and torque zero point
3. User clicks "Start Process" → Motor rotates continuously while measuring torque/angle
4. Automatic stop when `Max Angle` or `Max Torque` limit is reached
5. Data is logged to timestamped `.txt` file in project directory

**Measurement Loop:** Driven by `QTimer` at configurable interval (default 100ms = 10 Hz). Each iteration:
- Reads motor position from N6 controller (angle from SSI encoder)
- Reads torque voltage from DAQ and converts to torque (Nm)
- Updates live graph
- Writes data row to file
- Checks stop conditions

**GUI State Management:**
- Setup controls (parameters, hardware buttons) are disabled during active measurement
- Stop button remains enabled at all times for safety
- Hardware must be activated before measurements can begin
- Home position calibration recommended before each measurement session

### Critical Configuration (main.py lines 135-175)

All hardware parameters are defined as constants at the top of `main.py`:

**General Settings:**
- `DEMO_MODE`: Toggle simulation vs. real hardware (line 133)
- `MEASUREMENT_INTERVAL`: Data acquisition rate in milliseconds (line 135)

**Torque Sensor (DF-30):**
- `TORQUE_SENSOR_MAX_NM`: Maximum torque rating (20.0 Nm)
- `TORQUE_SENSOR_MAX_VOLTAGE`: Maximum voltage output (±10V)
- `TORQUE_SCALE`: Nm/V conversion factor (2.0 for DF-30)
- `DAQ_CHANNEL_TORQUE`: NI DAQ channel name (`Dev1/ai0`)

**N6 Nanotec Motor Controller:**
- `N6_IP_ADDRESS`: Motor controller IP address (192.168.0.100)
- `N6_MODBUS_PORT`: Modbus TCP port (502)
- `N6_SLAVE_ID`: Modbus slave ID (1)
- `N6_ENCODER_RESOLUTION`: SSI encoder resolution (8192 counts/rev, 13-bit)

### Hardware Controllers

**MotorControllerBase** ([motor_controller_base.py](src/hardware/motor_controller_base.py)):
- Abstract base class defining motor controller interface
- Ensures consistent API across different motor controller types
- Abstract methods: `connect()`, `disconnect()`, `home_position()`, `move_continuous()`, `stop_movement()`, `get_position()`, `is_motor_moving()`

**N6NanotecController** ([n6_nanotec_controller.py](src/hardware/n6_nanotec_controller.py)):
- Communicates via **NanoLib** library (`nanotec-nanolib`) using Modbus TCP protocol
- Implements CANopen Object Dictionary (CiA 402) for motor control
- **Connection workflow:**
  1. `listAvailableBusHardware()` - Detects Ethernet adapter
  2. `openBusHardwareWithProtocol()` - Opens Modbus TCP connection
  3. `scanDevices()` - Discovers N6 controller on network
  4. `addDevice()` and `connectDevice()` - Establishes device connection
  5. CiA 402 state machine: Shutdown → Switch On → Enable Operation
  6. Set to Velocity Mode (MODE_PROFILE_VELOCITY = 3)
- **Object Dictionary access:**
  - Read position: OD 0x6064 (Position Actual Value) - returns SSI encoder multi-turn position
  - Write velocity: OD 0x60FF (Target Velocity)
  - Control/Status: OD 0x6040/0x6041 (Control Word/Status Word)
- **SSI Encoder integration:**
  - 13-bit encoder (8192 counts/rev) read directly by N6 controller
  - Multi-turn tracking handled internally by controller
  - Continuous angle measurement (0°, 361°, 720°, etc.)
- Methods: `connect()`, `home_position()`, `move_continuous(velocity)`, `get_position()`, `stop_movement()`
- In demo mode: simulates continuous motion at specified velocity

**DAQmxTask** ([daq_controller.py](src/hardware/daq_controller.py)):
- Wraps NI-DAQmx for voltage measurement (torque sensor only)
- **Note:** Angle measurement is now performed by N6 controller, not DAQ
- Integrates with `DemoHardwareSimulator` when `demo_mode=True`
- Methods: `create_nidaqmx_task()`, `read_torque_voltage(angle)`, `calibrate_zero()`, `close_nidaqmx_task()`
- Zero calibration: Calculates offset based on current reading

**DemoHardwareSimulator** ([demo_simulator.py](src/hardware/demo_simulator.py)):
- Simulates realistic torque readings based on angle with noise
- Formula: `torque = 0.05 * angle + random_noise`
- Supports zero-point calibration like real sensor

## Common Development Tasks

### Modifying Hardware Parameters
Edit constants in [main.py](main.py) lines 135-175. These are the single source of truth for all hardware configuration.

### Adding New Hardware
1. Create new controller class in `src/hardware/`
2. Implement `demo_mode` parameter in constructor
3. Add import to `src/hardware/__init__.py`
4. Integrate into `MainWindow.activate_hardware()` in [main.py](main.py)

### Changing Measurement Behavior
The core measurement loop is in `MainWindow.measure()` (main.py:2756). This method is called by QTimer every `MEASUREMENT_INTERVAL` milliseconds. Key operations:
- Reads angle from N6 controller via `get_position()`
- Reads torque from DAQ via `read_torque_voltage()`
- Updates GUI graph and data logging

### Adjusting UI
The UI is designed in Qt Designer and saved as [torsions_test_stand.ui](src/gui/torsions_test_stand.ui). After modifying:
- Widgets are accessed by their `objectName` (e.g., `self.start_meas_btn`)
- No UI compilation step needed - `uic.loadUi()` loads at runtime

### Data File Format
Measurement data is saved as tab-delimited text files with:
- Header: measurement metadata (timestamp, sample name, parameters)
- Columns: `Time`, `Voltage`, `Torque`, `Angle`
- Units: `[HH:mm:ss.f]`, `[V]`, `[Nm]`, `[°]`
- Files are named: `YYYYMMDD_HHMMSS_<SampleName>_DATA.txt`
- Location: Stored in user-selected project directory (selected via "Select Project Directory" button)

## Important Notes

### Thread Safety
All operations run on the Qt GUI thread. Do not add threading without careful consideration of Qt's threading model.

### Motor Direction Convention
- Positive velocity → Clockwise rotation
- Negative velocity → Counter-clockwise rotation
- This is configured in the motor controller settings

### Safety Features
- Hardware controls are disabled during measurement (`set_setup_controls_enabled(False)`)
- Stop button remains always enabled
- Automatic stop on limit violations (torque or angle)
- Home position must be executed before each measurement for proper calibration

### Closed-Loop Position Control & SSI Encoder
The N6 Nanotec motor manages position internally with SSI encoder feedback. The software only:
- Commands velocity with `move_continuous(velocity)` → writes to OD 0x60FF
- Reads current position with `get_position()` → reads from OD 0x6064
- Does NOT implement position control loop (handled by motor controller)
- Does NOT perform multi-turn tracking (N6 controller handles this internally)

**SSI Encoder Details:**
- 13-bit absolute encoder: 8192 counts per revolution
- Connected directly to N6 controller (not via DAQ)
- N6 performs multi-turn tracking internally
- Position reading includes continuous angle over multiple rotations
- No unwrap logic needed in software (legacy approach removed)

### Demo Mode Implementation
When `DEMO_MODE = True`:
- Hardware initialization succeeds without real devices
- `DemoHardwareSimulator` generates realistic sensor data
- Motor position is simulated by integrating velocity over time
- All GUI features work identically to real hardware mode

## Code Style

This codebase was developed for educational purposes with extensive German comments. Key conventions:
- German variable names for domain concepts (e.g., `Drehmoment`, `Winkel`)
- English for code structure (class names, methods)
- Comprehensive docstrings with type hints
- Educational comments explaining hardware concepts
- Logging at INFO level for user-facing operations

## Hardware Documentation

Technical documentation is available in the `Docs/` directory:
- **N6_ModbusTCP_Technisches-Handbuch_V1.1.0.pdf**: N6 controller technical manual (Modbus TCP registers)
- **N6_MODBUS_TCP_DE_LEAFLET_V1.0.0.pdf**: Quick reference for N6 Modbus TCP
- **NanoLib-Python_User_Manual_V1.3.4.pdf**: NanoLib Python API documentation

Key references:
- CANopen CiA 402 Drive Profile for motor control state machine
- Object Dictionary (OD) indices for position (0x6064), velocity (0x60FF), control/status (0x6040/0x6041)

## Git Workflow

Current branch: `main`

Recent changes include refactoring hardware classes from `main.py` into separate modules (see [REFACTORING_NOTES.md](REFACTORING_NOTES.md)).
- Keep the code simple and use comments to describe the process