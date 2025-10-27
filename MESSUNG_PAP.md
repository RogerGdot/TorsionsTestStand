# Programmablaufplan (PAP) - Torsionsmessung

## Überblick
Dieser PAP beschreibt den vollständigen Ablauf einer automatischen Torsionsmessung im TorsionsTestStand V2.0.

---

## 1. Programmstart & Initialisierung

```mermaid
flowchart TD
    Start([Programm Start]) --> InitGUI[GUI laden und initialisieren]
    InitGUI --> InitVars[Klassenvariablen initialisieren]
    InitVars --> SetupLogger[Logger-System einrichten]
    SetupLogger --> CheckDemo{DEMO_MODE?}
    CheckDemo -->|True| DemoLED[Demo-LED: GRÜN]
    CheckDemo -->|False| HardwareLED[Demo-LED: ROT]
    DemoLED --> ConnectEvents[Button-Events verbinden]
    HardwareLED --> ConnectEvents
    ConnectEvents --> SetupGraph[Graph-Widget erstellen]
    SetupGraph --> InitParams[Parameter laden]
    InitParams --> Ready([Bereit für Benutzung])
```

**Funktionen:**
- `__init__()` - Hauptkonstruktor
- `init_class_attributes()` - Variablen-Initialisierung
- `setup_Logger()` - Logging-System
- `connectEvents()` - Button-Verbindungen
- `setup_torque_graph_widget()` - Graph-Darstellung
- `init_parameters()` - Standardwerte setzen

---

## 2. Hardware-Aktivierung

```mermaid
flowchart TD
    Start([Button: Activate Hardware]) --> CheckInit{Bereits<br/>initialisiert?}
    CheckInit -->|Ja| Warning[Warnung ausgeben]
    Warning --> End1([Ende])
    
    CheckInit -->|Nein| WaitCursor[Warte-Cursor setzen]
    WaitCursor --> InitDAQ[NI-6000 DAQ initialisieren]
    
    InitDAQ --> DAQSuccess{DAQ OK?}
    DAQSuccess -->|Ja| DAQLEDGreen[DAQ-LED: GRÜN]
    DAQSuccess -->|Nein| DAQLEDRed[DAQ-LED: ROT]
    
    DAQLEDGreen --> InitMotor[Motor-Controller initialisieren]
    DAQLEDRed --> InitMotor
    
    InitMotor --> CheckMotorType{Motor-Typ?}
    CheckMotorType -->|Nanotec| ConnectNanotec[Nanotec N5 verbinden<br/>CAN-Bus]
    CheckMotorType -->|Trinamic| ConnectTrinamic[Trinamic verbinden<br/>RS485]
    
    ConnectNanotec --> MotorSuccess{Motor OK?}
    ConnectTrinamic --> MotorSuccess
    
    MotorSuccess -->|Ja| MotorLEDGreen[Motor-LED: GRÜN]
    MotorSuccess -->|Nein| MotorLEDRed[Motor-LED: ROT]
    
    MotorLEDGreen --> AllOK{Beide OK?}
    MotorLEDRed --> AllOK
    
    AllOK -->|Ja| SetFlag[are_instruments_initialized = True]
    AllOK -->|Nein| ErrorDialog[Fehler-Dialog anzeigen]
    
    SetFlag --> SuccessDialog[Erfolgs-Dialog anzeigen]
    SuccessDialog --> RestoreCursor[Normal-Cursor]
    ErrorDialog --> RestoreCursor
    RestoreCursor --> End2([Ende])
```

**Funktionen:**
- `activate_hardware()` - Hauptfunktion
- `DAQmxTask.create_nidaqmx_task()` - DAQ-Initialisierung
- `NanotecMotorController.connect()` / `TrinamicMotorController.connect()` - Motor-Verbindung

---

## 3. Home Position & Kalibrierung

```mermaid
flowchart TD
    Start([Button: Home Position]) --> CheckHW{Hardware<br/>initialisiert?}
    CheckHW -->|Nein| ErrorHW[Fehlermeldung]
    ErrorHW --> End1([Ende])
    
    CheckHW -->|Ja| CheckRun{Messung<br/>läuft?}
    CheckRun -->|Ja| ErrorRun[Fehlermeldung]
    ErrorRun --> End2([Ende])
    
    CheckRun -->|Nein| HomeMotor[Motor auf 0° fahren]
    HomeMotor --> MotorSuccess{Erfolgreich?}
    
    MotorSuccess -->|Nein| ErrorMotor[Motor-Fehler melden]
    ErrorMotor --> End3([Ende])
    
    MotorSuccess -->|Ja| CalibrateTorque[Torque-Nullpunkt kalibrieren]
    CalibrateTorque --> ResetUnwrap[Unwrap-Logik zurücksetzen]
    
    ResetUnwrap --> SetVars[turn_counter = 0<br/>prev_angle_deg = 0<br/>angle_continuous_deg = 0]
    
    SetVars --> Success[Erfolg loggen]
    Success --> End4([Ende])
```

**Funktionen:**
- `home_position()` - Hauptfunktion
- `motor_controller.home_position()` - Motor-Home
- `nidaqmx_task.calibrate_torque_zero()` - Nullpunkt-Kalibrierung
- `reset_angle_unwrap()` - Unwrap zurücksetzen

---

## 4. Messung starten

```mermaid
flowchart TD
    Start([Button: Start Measurement]) --> CheckRun{Messung<br/>läuft bereits?}
    CheckRun -->|Ja| Warning[Warnung ausgeben]
    Warning --> End1([Ende])
    
    CheckRun -->|Nein| CheckHW{Hardware<br/>bereit?}
    CheckHW -->|Nein| ErrorHW[Hardware-Fehler-Dialog]
    ErrorHW --> End2([Ende])
    
    CheckHW -->|Ja| ReadParams[Parameter auslesen:<br/>max_angle, max_torque, max_velocity]
    ReadParams --> SaveStartTime[Startzeit speichern]
    SaveStartTime --> ResetUnwrap2[Unwrap-Logik zurücksetzen]
    
    ResetUnwrap2 --> CreateFolder[Messordner erstellen]
    CreateFolder --> FolderOK{Erfolgreich?}
    
    FolderOK -->|Nein| ErrorFolder[Fehler-Dialog]
    ErrorFolder --> End3([Ende])
    
    FolderOK -->|Ja| CreateFile[Messdatei mit Header erstellen]
    CreateFile --> StartMotor[Motor starten<br/>kontinuierliche Bewegung]
    
    StartMotor --> MotorOK{Motor OK?}
    MotorOK -->|Nein| ErrorMotor[Motor-Fehler-Dialog]
    ErrorMotor --> End4([Ende])
    
    MotorOK -->|Ja| StartTimer[Measurement Timer starten<br/>100ms Intervall]
    StartTimer --> ResetGraph[Graph-Daten löschen]
    ResetGraph --> SetStatus[is_process_running = True]
    
    SetStatus --> SetLED[LED: GRÜN]
    SetLED --> DisableControls[Setup-Controls deaktivieren]
    DisableControls --> LogSuccess[Erfolg loggen]
    LogSuccess --> End5([Ende - Timer läuft])
```

**Funktionen:**
- `start_measurement()` - Hauptfunktion
- `create_measurement_folder()` - Ordner & Datei erstellen
- `motor_controller.move_continuous()` - Motor starten
- `setup_measurement_timer()` - Timer initialisieren
- `reset_graph_data()` - Graph leeren
- `set_setup_controls_enabled(False)` - GUI sperren

---

## 5. Messung durchführen (Timer-Callback)

```mermaid
flowchart TD
    Start([Timer: 100ms Intervall]) --> CheckRun{is_process_running?}
    CheckRun -->|Nein| End1([Ende])
    
    CheckRun -->|Ja| CalcTime[Zeitstempel berechnen<br/>seit Messstart]
    
    CalcTime --> CheckMode{DEMO_MODE?}
    
    CheckMode -->|Ja| SimAngle[Winkel simulieren:<br/>Velocity × Zeit]
    SimAngle --> UpdateSim[Demo-Simulator aktualisieren]
    UpdateSim --> CheckEncoder{Encoder-<br/>Modus?}
    
    CheckEncoder -->|Single-Turn| WrapSim[Wrap auf 0-360°]
    CheckEncoder -->|Multi-Turn| DirectSim[Direkter Winkel]
    
    WrapSim --> UnwrapSim[Unwrap-Logik anwenden]
    UnwrapSim --> ReadTorqueDemo[Simuliertes Torque lesen]
    DirectSim --> ReadTorqueDemo
    
    CheckMode -->|Nein| CheckSource{Angle-<br/>Quelle?}
    
    CheckSource -->|DAQ| ReadAngleDAQ[Angle-Spannung von ai1 lesen]
    CheckSource -->|Motor| ReadAngleMotor[Position vom Motor lesen]
    
    ReadAngleDAQ --> ScaleAngle[Spannung zu Winkel skalieren<br/>0-10V → 0-360°]
    ScaleAngle --> UnwrapAngle[Unwrap-Logik anwenden]
    UnwrapAngle --> ReadTorqueDAQ[Torque-Spannung von ai0 lesen]
    
    ReadAngleMotor --> ReadTorqueDAQ
    ReadTorqueDemo --> CalcTorque[Drehmoment berechnen<br/>Voltage × TORQUE_SCALE]
    ReadTorqueDAQ --> CalcTorque
    
    CalcTorque --> AppendData[Daten zu Listen hinzufügen:<br/>torque_data, angle_data]
    AppendData --> UpdateGraph[Graph aktualisieren<br/>torque_curve.setData]
    
    UpdateGraph --> WriteFile[Daten in Datei schreiben<br/>Tab-getrennt]
    WriteFile --> UpdateGUI[GUI-Felder aktualisieren:<br/>Voltage, Torque, Angle]
    
    UpdateGUI --> CheckAngle{|angle| >=<br/>max_angle?}
    CheckAngle -->|Ja| StopAngle[STOPP:<br/>Max Angle erreicht]
    CheckAngle -->|Nein| CheckTorque{|torque| >=<br/>max_torque?}
    
    CheckTorque -->|Ja| StopTorque[STOPP:<br/>Max Torque erreicht]
    CheckTorque -->|Nein| End2([Ende - Weiter messen])
    
    StopAngle --> CallStop[stop_measurement aufrufen]
    StopTorque --> CallStop
    CallStop --> End3([Ende])
```

**Funktionen:**
- `measure()` - Hauptfunktion (Timer-Callback)
- `unwrap_angle()` - Kontinuierlichen Winkel berechnen
- `nidaqmx_task.read_angle_voltage()` - Winkel-Spannung lesen
- `nidaqmx_task.read_torque_voltage()` - Torque-Spannung lesen
- `write_measurement_data()` - Daten speichern
- `update_measurement_gui()` - GUI aktualisieren
- `stop_measurement()` - Bei Grenzwert stoppen

---

## 6. Unwrap-Logik (Single-Turn Encoder)

```mermaid
flowchart TD
    Start([unwrap_angle aufrufen]) --> CheckMode{Encoder-<br/>Modus?}
    
    CheckMode -->|Multi-Turn| ReturnDirect[Direkten Winkel zurückgeben]
    ReturnDirect --> End1([Ende])
    
    CheckMode -->|Single-Turn| CalcDelta[Delta berechnen:<br/>angle_now - prev_angle_deg]
    
    CalcDelta --> CheckForward{Delta <<br/>-180°?}
    
    CheckForward -->|Ja| IncrementCounter[turn_counter += 1<br/>Vorwärts-Wrap: 360° → 0°]
    CheckForward -->|Nein| CheckBackward{Delta ><br/>+180°?}
    
    CheckBackward -->|Ja| DecrementCounter[turn_counter -= 1<br/>Rückwärts-Wrap: 0° → 360°]
    CheckBackward -->|Nein| NoWrap[Normale Bewegung<br/>kein Wrap]
    
    IncrementCounter --> CalcContinuous[angle_continuous_deg =<br/>angle_now + 360° × turn_counter]
    DecrementCounter --> CalcContinuous
    NoWrap --> CalcContinuous
    
    CalcContinuous --> SavePrev[prev_angle_deg = angle_now]
    SavePrev --> Return[Kontinuierlichen Winkel zurückgeben]
    Return --> End2([Ende])
```

**Beispiel:**
- **Zeit 0s:** angle_now=0°, prev=0°, turn_counter=0 → Result: 0°
- **Zeit 35s:** angle_now=350°, prev=340°, delta=+10° → Result: 350° (kein Wrap)
- **Zeit 36s:** angle_now=10°, prev=350°, delta=-340° (< -180°) → turn_counter=1 → Result: 370°
- **Zeit 72s:** angle_now=10°, prev=350°, delta=-340° → turn_counter=2 → Result: 730°

**Funktionen:**
- `unwrap_angle()` - Hauptfunktion
- Verwendet: `turn_counter`, `prev_angle_deg`, `angle_continuous_deg`

---

## 7. Messung stoppen

```mermaid
flowchart TD
    Start([Button: Stop Measurement<br/>ODER Auto-Stop]) --> CheckRun{Messung<br/>läuft?}
    
    CheckRun -->|Nein| Warning[Warnung ausgeben]
    Warning --> End1([Ende])
    
    CheckRun -->|Ja| LogStop[Stopp-Meldung loggen]
    LogStop --> StopTimer[Measurement Timer stoppen]
    
    StopTimer --> CheckMotor{Motor<br/>verbunden?}
    CheckMotor -->|Ja| StopMotor[Motor stoppen]
    CheckMotor -->|Nein| ResetStatus
    
    StopMotor --> MotorOK{Erfolgreich?}
    MotorOK -->|Ja| ResetStatus[is_process_running = False]
    MotorOK -->|Nein| LogError[Motor-Stop-Fehler loggen]
    LogError --> ResetStatus
    
    ResetStatus --> SetLED[LED: ROT]
    SetLED --> EnableControls[Setup-Controls aktivieren]
    EnableControls --> ResetTime[start_time_timestamp = None]
    ResetTime --> LogSuccess[Erfolg loggen]
    LogSuccess --> End2([Ende])
```

**Funktionen:**
- `stop_measurement()` - Hauptfunktion
- `measurement_timer.stop()` - Timer stoppen
- `motor_controller.stop_movement()` - Motor stoppen
- `set_setup_controls_enabled(True)` - GUI entsperren

---

## 8. Hardware deaktivieren

```mermaid
flowchart TD
    Start([Button: Deactivate Hardware]) --> CheckInit{Hardware<br/>initialisiert?}
    
    CheckInit -->|Nein| Warning[Warnung ausgeben]
    Warning --> End1([Ende])
    
    CheckInit -->|Ja| WaitCursor[Warte-Cursor setzen]
    WaitCursor --> CloseDAQ[NI-6000 DAQ Task schließen]
    
    CloseDAQ --> DAQSuccess{Erfolgreich?}
    DAQSuccess -->|Ja| LogDAQOK[DAQ-Trennung geloggt]
    DAQSuccess -->|Nein| LogDAQError[DAQ-Fehler geloggt]
    
    LogDAQOK --> SetDAQNone[nidaqmx_task = None]
    LogDAQError --> SetDAQNone
    SetDAQNone --> DAQLEDRed[DAQ-LED: ROT]
    
    DAQLEDRed --> CheckMotor{Motor<br/>verbunden?}
    CheckMotor -->|Ja| DisconnectMotor[Motor trennen]
    CheckMotor -->|Nein| SetMotorNone
    
    DisconnectMotor --> MotorSuccess{Erfolgreich?}
    MotorSuccess -->|Ja| LogMotorOK[Motor-Trennung geloggt]
    MotorSuccess -->|Nein| LogMotorError[Motor-Fehler geloggt]
    
    LogMotorOK --> SetMotorNone[motor_controller = None]
    LogMotorError --> SetMotorNone
    SetMotorNone --> MotorLEDRed[Motor-LED: ROT]
    
    MotorLEDRed --> ResetFlag[are_instruments_initialized = False]
    ResetFlag --> EnableControls[Setup-Controls aktivieren]
    EnableControls --> RestoreCursor[Normal-Cursor]
    RestoreCursor --> LogSuccess[Erfolg loggen]
    LogSuccess --> End2([Ende])
```

**Funktionen:**
- `deactivate_hardware()` - Hauptfunktion
- `nidaqmx_task.close()` - DAQ schließen
- `motor_controller.disconnect()` - Motor trennen
- `set_setup_controls_enabled(True)` - GUI entsperren

---

## 9. Programm beenden

```mermaid
flowchart TD
    Start([X-Button / Alt+F4]) --> CheckRun{Messung<br/>läuft?}
    
    CheckRun -->|Ja| LogStop[Stopp-Meldung]
    CheckRun -->|Nein| CheckHW{Hardware<br/>initialisiert?}
    
    LogStop --> CallStop[stop_measurement aufrufen]
    CallStop --> CheckHW
    
    CheckHW -->|Ja| LogDeact[Deaktivierungs-Meldung]
    CheckHW -->|Nein| LogExit[Beendigungs-Meldung]
    
    LogDeact --> CallDeact[deactivate_hardware aufrufen]
    CallDeact --> LogExit
    
    LogExit --> CloseApp[Programm sauber beenden]
    CloseApp --> End([Ende])
```

**Funktionen:**
- `closeEvent()` - Hauptfunktion (PyQt6 Lifecycle)
- Ruft auf: `stop_measurement()`, `deactivate_hardware()`

---

## Zusammenfassung: Haupt-Zustandsmaschine

```mermaid
stateDiagram-v2
    [*] --> Initialisiert: Programmstart
    
    Initialisiert --> HardwareBereit: Activate Hardware
    HardwareBereit --> Kalibriert: Home Position
    Kalibriert --> MessungLäuft: Start Measurement
    
    MessungLäuft --> MessungLäuft: Timer-Callback (measure)\n100ms Intervall
    MessungLäuft --> MessungGestoppt: Stop Measurement\nODER Max erreicht
    
    MessungGestoppt --> Kalibriert: Home Position
    MessungGestoppt --> MessungLäuft: Start Measurement
    
    HardwareBereit --> Initialisiert: Deactivate Hardware
    Kalibriert --> Initialisiert: Deactivate Hardware
    MessungGestoppt --> Initialisiert: Deactivate Hardware
    
    Initialisiert --> [*]: Programm beenden
    HardwareBereit --> [*]: Programm beenden
    Kalibriert --> [*]: Programm beenden
    MessungGestoppt --> [*]: Programm beenden
    
    note right of MessungLäuft
        Daten werden kontinuierlich
        erfasst und gespeichert:
        - Zeitstempel
        - Voltage
        - Torque
        - Angle (unwrapped)
    end note
```

---

## Wichtige Konstanten & Variablen

### Konstanten (in main.py definiert)
```python
DEMO_MODE = True/False              # Demo vs. Hardware-Modus
MEASUREMENT_INTERVAL = 100          # Timer-Intervall [ms]
TORQUE_SCALE = 2.0                  # Nm/V Skalierung
ANGLE_ENCODER_MODE = "single_turn"  # Single-Turn vs. Multi-Turn
ANGLE_MEASUREMENT_SOURCE = "daq"    # DAQ vs. Motor
ANGLE_WRAP_THRESHOLD = 180.0        # Unwrap-Schwellwert [°]
```

### Wichtige Variablen
```python
is_process_running          # Messung läuft
are_instruments_initialized # Hardware bereit
turn_counter               # Umdrehungszähler
prev_angle_deg            # Vorheriger Winkel
angle_continuous_deg      # Kontinuierlicher Winkel
torque_data              # Liste aller Torque-Werte
angle_data               # Liste aller Angle-Werte
start_time_timestamp     # Messstart-Zeitpunkt
```

---

## Dateiformat

### Header
```
# Measurement started: 2025-10-27 14:30:00 - Sample: Probe001
# Max Angle: 360° | Max Torque: 15 Nm | Max Velocity: 10°/s
# Torque Scale: 2 Nm/V | Interval: 100ms
Time            Voltage     Torque      Angle
[HH:mm:ss.f]    [V]         [Nm]        [°]
```

### Datenzeilen (Tab-getrennt)
```
00:00:00.0      0.000000    0.000000    0.000000
00:00:00.1      0.125000    0.250000    1.234567
00:00:00.2      0.250000    0.500000    2.456789
...
```

---

## Fehlerbehandlung

| Fehler | Reaktion | Funktion |
|--------|----------|----------|
| Hardware nicht initialisiert | Fehlerdialog, Abbruch | `start_measurement()` |
| Messung läuft bereits | Warnung, Abbruch | `start_measurement()` |
| Ordner-Erstellung fehlgeschlagen | Fehlerdialog, Abbruch | `create_measurement_folder()` |
| Motor-Start fehlgeschlagen | Fehlerdialog, Abbruch | `start_measurement()` |
| DAQ-Lesefehler während Messung | Warnung, Wert=0.0, weiter | `measure()` |
| Max Angle erreicht | Auto-Stop, Grund loggen | `measure()` |
| Max Torque erreicht | Auto-Stop, Grund loggen | `measure()` |

---

## Performance

- **Mess-Frequenz:** 10 Hz (alle 100ms)
- **Dauer pro measure():** < 5ms
- **CPU-Last:** Gering (non-blocking Timer)
- **Datenpunkte bei 60s Messung:** 600
- **Dateigröße bei 600 Punkten:** ~50 KB

---

**Dokument erstellt:** 2025-10-27  
**Version:** 2.0  
**Autor:** TorsionsTestStand Dokumentation
