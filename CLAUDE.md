# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Torsions Test Stand** control software for a technical school graduation project. It controls a torsion testing apparatus that measures torque and angle using:
- **DF-30 Torque Sensor** (±20 Nm, ±10V output)
- **NI-6000 DAQ** for analog signal acquisition
- **N5 Nanotec Stepper Motor** with Modbus TCP and closed-loop position control

The software supports a **demo mode** for testing without hardware and provides live visualization, automatic data logging, and safety features.

## Running the Application

### Demo Mode (No Hardware Required)
```powershell
# Ensure DEMO_MODE = True in main.py (line 61)
python main.py
```

### With Real Hardware
```powershell
# Set DEMO_MODE = False in main.py (line 61)
python main.py
```

### Hardware Test Programs
```powershell
# Test NI-6000 DAQ in isolation
python test_ni6000.py

# Test N5 Nanotec motor controller
python test_n5_nanotec.py
```

### Installation
```powershell
pip install -r requirements.txt
```

Note: `nidaqmx` requires NI-DAQmx Runtime drivers for real hardware (download from ni.com).

## Architecture

### Module Structure

```
src/
├── hardware/           # Hardware abstraction layer
│   ├── __init__.py
│   ├── n5_nanotec_controller.py    # Modbus TCP motor control
│   ├── daq_controller.py           # NI-6000 DAQ wrapper
│   └── demo_simulator.py           # Hardware simulation
├── gui/
│   ├── torsions_test_stand.ui      # Qt Designer UI file
│   └── stylesheet.py               # Dark theme stylesheet
└── utils/
    └── logger_helper.py            # GUI logger integration
```

### Key Design Patterns

**Hardware Abstraction:** All hardware controllers (`N5NanotecController`, `DAQmxTask`) support both real and demo modes. Pass `demo_mode=True` to use simulation instead of physical hardware.

**Main Event Flow:**
1. User clicks "Activate Hardware" → Initializes DAQ and motor controller
2. User clicks "Home Position" → Calibrates motor to 0° and torque zero point
3. User clicks "Start Process" → Motor rotates continuously while measuring torque/angle
4. Automatic stop when `Max Angle` or `Max Torque` limit is reached
5. Data is logged to timestamped `.txt` file in project directory

**Measurement Loop:** Driven by `QTimer` at configurable interval (default 100ms = 10 Hz). Each iteration:
- Reads motor position (angle)
- Reads DAQ voltage and converts to torque
- Updates live graph
- Writes data row to file
- Checks stop conditions

**GUI State Management:**
- Setup controls (parameters, hardware buttons) are disabled during active measurement
- Stop button remains enabled at all times for safety
- Hardware must be activated before measurements can begin
- Home position calibration recommended before each measurement session

### Critical Configuration (main.py lines 61-88)

All hardware parameters are defined as constants at the top of `main.py`:
- `DEMO_MODE`: Toggle simulation vs. real hardware
- `TORQUE_SCALE`: Nm/V conversion factor (2.0 for DF-30)
- `DAQ_CHANNEL_TORQUE`: NI DAQ channel name
- `N5_IP_ADDRESS`: Motor controller network address
- `MEASUREMENT_INTERVAL`: Data acquisition rate in milliseconds

### Hardware Controllers

**N5NanotecController** ([n5_nanotec_controller.py](src/hardware/n5_nanotec_controller.py)):
- Communicates via Modbus TCP (pymodbus library)
- Closed-loop position control (motor controller manages position internally)
- Methods: `connect()`, `home_position()`, `move_continuous(velocity)`, `get_position()`, `stop_movement()`
- In demo mode: simulates continuous motion at specified velocity

**DAQmxTask** ([daq_controller.py](src/hardware/daq_controller.py)):
- Wraps NI-DAQmx for voltage measurement
- Integrates with `DemoHardwareSimulator` when `demo_mode=True`
- Methods: `create_nidaqmx_task()`, `read_torque_voltage(angle)`, `calibrate_zero()`, `close_nidaqmx_task()`
- Zero calibration: Calculates offset based on current reading

**DemoHardwareSimulator** ([demo_simulator.py](src/hardware/demo_simulator.py)):
- Simulates realistic torque readings based on angle with noise
- Formula: `torque = 0.05 * angle + random_noise`
- Supports zero-point calibration like real sensor

## Common Development Tasks

### Modifying Hardware Parameters
Edit constants in [main.py](main.py) lines 61-88. These are the single source of truth for all hardware configuration.

### Adding New Hardware
1. Create new controller class in `src/hardware/`
2. Implement `demo_mode` parameter in constructor
3. Add import to `src/hardware/__init__.py`
4. Integrate into `MainWindow.activate_hardware()` in [main.py](main.py)

### Changing Measurement Behavior
The core measurement loop is in `MainWindow.measure()` ([main.py:792](main.py#L792)). This method is called by QTimer every `MEASUREMENT_INTERVAL` milliseconds.

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

### Closed-Loop Position Control
The N5 Nanotec motor manages position internally with encoder feedback. The software only:
- Commands velocity with `move_continuous(velocity)`
- Reads current position with `get_position()`
- Does NOT implement position control loop (handled by motor controller)

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

## Git Workflow

Current branch: `main`

Recent changes include refactoring hardware classes from `main.py` into separate modules (see [REFACTORING_NOTES.md](REFACTORING_NOTES.md)).
- Keep the code simple and use comments to describe the process