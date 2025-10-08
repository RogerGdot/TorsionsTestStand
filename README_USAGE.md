# Torsions Test Stand - Software

Software zur Steuerung eines Torsionsprüfstands für eine Techniker-Abschlussarbeit.

## Hardware-Komponenten

### DF-30 Drehmoment-Sensor
- **Messbereich:** ±20 Nm
- **Signal:** Analog über Messverstärker
- **Ausgangssignal:** ±10V (entspricht ±20 Nm)
- **Skalierung:** 2.0 Nm/V

### NI-6000 DAQ (National Instruments)
- **Funktion:** Erfassung des Drehmoment-Signals
- **Eingangsbereich:** ±10V
- **Kanal:** Dev1/ai0 (konfigurierbar)
- **Abtastrate:** 10 Hz (100ms Intervall)

### N5 Nanotec Schrittmotor
- **Steuerung:** Modbus TCP
- **Betriebsart:** Closed-Loop (Position wird vom Controller verwaltet)
- **Geschwindigkeit:** Konfigurierbar (Standard: 10°/s)
- **Richtung:** Bidirektional (+ = Uhrzeiger, - = gegen Uhrzeiger)
- **Netzwerk:** 192.168.0.100:502 (konfigurierbar)

## Software-Features

### Demo-Modus ✨
- **Funktion:** Vollständige Simulation ohne echte Hardware
- **Aktivierung:** `DEMO_MODE = True` in `main.py` (Zeile 73)
- **Simulation:**
  - Realistische Torque-Berechnung basierend auf Winkel
  - Kontinuierliche Motor-Bewegung
  - Zufälliges Rauschen für realistische Daten
  - Alle GUI-Funktionen verfügbar

### Haupt-Funktionen

#### 1. Hardware Aktivierung
- **Button:** "Activate Hardware"
- **Funktion:** 
  - Initialisiert NI-6000 DAQ
  - Verbindet mit N5 Nanotec Controller
  - Zeigt Status mit grünen/roten LEDs an
- **Erfolg:** Popup-Meldung + grüne LEDs
- **Fehler:** Detaillierte Fehlermeldung mit Popup

#### 2. Home-Position & Kalibrierung
- **Button:** "Home Position"
- **Voraussetzung:** Hardware aktiviert, IDLE-Modus
- **Funktion:**
  - Fährt Motor in 0°-Position
  - Kalibriert Torque-Nullpunkt
  - Muss vor jeder Messung durchgeführt werden!
- **Status:** Erfolgs-Popup nach Abschluss

#### 3. Messung Starten
- **Button:** "Start Process"
- **Voraussetzung:** Hardware aktiviert, Projektordner gewählt
- **Parameter:**
  - **Max Angle [°]:** Maximaler Drehwinkel (Stopbedingung)
  - **Max Torque [Nm]:** Maximales Drehmoment (Stopbedingung)
  - **Max Velocity [°/s]:** Geschwindigkeit
    - Positiv → Im Uhrzeigersinn
    - Negativ → Gegen Uhrzeigersinn
    
- **Ablauf:**
  1. Motor startet mit eingestellter Geschwindigkeit
  2. Kontinuierliche Datenerfassung (Torque, Angle)
  3. Live-Graph-Aktualisierung
  4. Automatischer Stopp bei Erreichen der Limits
  5. Alle Daten werden in TXT-Datei geschrieben

#### 4. Messung Stoppen
- **Button:** "Stop Process"
- **Funktion:**
  - Stoppt Motor sofort
  - Beendet Datenerfassung
  - Schließt Messdatei
- **Verfügbar:** Jederzeit während Messung

#### 5. Manuelle Messung
- **Button:** "Trigger NIDAQ"
- **Funktion:** Einzelmessung für Test-Zwecke
- **Zeigt:** Aktueller Torque, Angle, Voltage

### Daten-Speicherung

#### Ordner-Struktur
```
Projektverzeichnis/
└── 20251008_143025_TorsionTest/
    └── 20251008_143025_TorsionTest_DATA.txt
```

#### Datei-Format
```
# Measurement started: 2025-10-08 14:30:25 - Sample: TorsionTest
# Max Angle: 360° | Max Torque: 15 Nm | Max Velocity: 10°/s
# Torque Scale: 2.0 Nm/V | Interval: 100ms
Time            Voltage         Torque          Angle
[HH:mm:ss.f]    [V]             [Nm]            [°]
00:00:00.0      0.000000        0.000000        0.000000
00:00:00.1      0.025000        0.050000        1.000000
...
```

## Installation

### 1. Python-Abhängigkeiten
```powershell
pip install -r requirements.txt
```

**Benötigte Pakete:**
- PyQt6
- pyqtgraph
- nidaqmx (für NI-6000 DAQ)
- pymodbus (für N5 Nanotec)

### 2. NI DAQmx Treiber (nur für echte Hardware)
- Download: https://www.ni.com/de-de/support/downloads/drivers/download.ni-daqmx.html
- Installation: NI-DAQmx Runtime
- Version: 2023 oder neuer

### 3. Netzwerk-Konfiguration (N5 Nanotec)
- IP-Adresse prüfen/einstellen: `main.py` Zeile 96
- Firewall-Regel für Port 502 (Modbus TCP)
- Netzwerk-Kabel oder WLAN-Verbindung

## Verwendung

### Demo-Modus (ohne Hardware)

1. **Programm starten:**
   ```powershell
   python main.py
   ```

2. **GUI verwenden:**
   - "Activate Hardware" → Simuliert Hardware-Verbindung
   - "Home Position" → Setzt Simulation zurück
   - Projektordner wählen
   - Parameter einstellen (z.B. Max Angle: 360, Max Torque: 15, Velocity: 10)
   - "Start Process" → Beginnt Demo-Messung
   - Beobachten: Live-Graph, Messwerte, automatischer Stopp

3. **Daten überprüfen:**
   - Ordner öffnen
   - TXT-Datei mit Messdaten prüfen

### Echte Hardware

1. **DEMO_MODE deaktivieren:**
   ```python
   # In main.py Zeile 73:
   DEMO_MODE = False
   ```

2. **Hardware verbinden:**
   - NI-6000 DAQ über USB
   - N5 Nanotec über Ethernet
   - Sensor anschließen

3. **Hardware testen:**
   ```powershell
   # NI-6000 DAQ Test
   python test_ni6000.py
   
   # N5 Nanotec Test
   python test_n5_nanotec.py
   ```

4. **Hauptprogramm starten:**
   ```powershell
   python main.py
   ```

5. **Workflow:**
   - Hardware aktivieren
   - Probe einbauen
   - Home Position anfahren (kalibriert Nullpunkt!)
   - Parameter einstellen
   - Messung starten
   - Bei Bedarf stoppen
   - Daten auswerten

## Testprogramme

### test_ni6000.py
Testet die NI-6000 DAQ isoliert:
- ✓ Verbindung
- ✓ Einzelmessung
- ✓ Kontinuierliche Messung (10s)
- ✓ Nullpunkt-Kalibrierung

**Verwendung:**
```powershell
python test_ni6000.py
```

### test_n5_nanotec.py
Testet den N5 Nanotec Motor isoliert:
- ✓ Modbus TCP Verbindung
- ✓ Position auslesen
- ✓ Home-Position anfahren
- ✓ Kontinuierliche Bewegung
- ✓ Bidirektionale Bewegung

**Verwendung:**
```powershell
python test_n5_nanotec.py
```

## Konfiguration

Alle wichtigen Parameter in `main.py` (Zeilen 73-108):

```python
# Demo-Modus
DEMO_MODE = True  # True = Simulation, False = Echte Hardware

# DF-30 Sensor
TORQUE_SENSOR_MAX_NM = 20.0  # ±20 Nm
TORQUE_SENSOR_MAX_VOLTAGE = 10.0  # ±10V
TORQUE_SCALE = 2.0  # Nm/V

# NI-6000 DAQ
DAQ_CHANNEL_TORQUE = "Dev1/ai0"
DAQ_VOLTAGE_RANGE = 10.0  # ±10V

# Messung
MEASUREMENT_INTERVAL = 100  # ms (10 Hz)
DEFAULT_SAMPLE_NAME = "TorsionTest"

# N5 Nanotec
N5_IP_ADDRESS = "192.168.0.100"
N5_MODBUS_PORT = 502
N5_SLAVE_ID = 1

# Standard-Parameter
DEFAULT_MAX_ANGLE = 360.0  # °
DEFAULT_MAX_TORQUE = 15.0  # Nm
DEFAULT_MAX_VELOCITY = 10.0  # °/s
```

## Sicherheitshinweise

⚠️ **WICHTIG für echte Hardware:**

1. **Vor Messung:**
   - Prüfen Sie die Probe auf festen Sitz
   - Stellen Sie sicher, dass keine Personen im Bewegungsbereich sind
   - Testen Sie den Stopp-Button

2. **Während Messung:**
   - Nicht in den Bewegungsbereich greifen
   - Stopp-Button ist jederzeit verfügbar
   - Bei Problemen: Stopp-Button → Hardware deaktivieren

3. **Max-Werte einstellen:**
   - Max Torque niedriger als Sensor-Limit (20 Nm)
   - Max Angle auf sichere Werte begrenzen
   - Geschwindigkeit angemessen wählen

4. **Nach Messung:**
   - Motor in Home-Position fahren
   - Hardware deaktivieren
   - Probe entfernen

## Troubleshooting

### Problem: "NI DAQmx nicht verfügbar"
**Lösung:**
- NI-DAQmx Treiber installieren
- Python-Paket: `pip install nidaqmx`
- Für Demo-Modus: `DEMO_MODE = True` setzen

### Problem: "PyModbus nicht verfügbar"
**Lösung:**
- Installieren: `pip install pymodbus`
- Für Demo-Modus: `DEMO_MODE = True` setzen

### Problem: "N5 Nanotec Verbindung fehlgeschlagen"
**Lösung:**
- IP-Adresse prüfen (Ping-Test)
- Firewall-Regel für Port 502
- Kabel-Verbindung prüfen
- N5 Controller eingeschaltet?

### Problem: "Messungen unplausibel"
**Lösung:**
- Home Position vor Messung anfahren (kalibriert Nullpunkt!)
- Sensor-Verkabelung prüfen
- Torque Scale überprüfen (2.0 Nm/V für DF-30)

### Problem: GUI-Elemente fehlen
**Lösung:**
- UI-Datei vorhanden? `src/gui/torsions_test_stand.ui`
- Stylesheet vorhanden? `src/gui/stylesheet.py`

## Projekt-Struktur

```
TorsionsTestStand/
├── main.py                      # Hauptprogramm
├── test_ni6000.py              # NI-6000 Testprogramm
├── test_n5_nanotec.py          # N5 Nanotec Testprogramm
├── requirements.txt            # Python-Abhängigkeiten
├── README.md                   # Diese Datei
├── main_backup.py              # Backup der alten Version
├── src/
│   ├── gui/
│   │   ├── torsions_test_stand.ui   # GUI-Design (Qt Designer)
│   │   └── stylesheet.py            # Dark Theme
│   └── utils/
│       └── framework_helper.py      # Logger-Utilities
└── Docs/
    └── N5_ModbusTCP_Technisches-Handbuch_V3.3.0.pdf
```

## Technische Details

### Closed-Loop Position Control
Der N5 Nanotec Controller verwaltet die Position intern:
- Position wird vom Controller gemessen (Encoder)
- Software fragt Position ab (Modbus Register)
- Keine externe Position-Regelung nötig
- Hohe Genauigkeit und Zuverlässigkeit

### Datenerfassung
- **Rate:** 10 Hz (100ms Intervall)
- **Synchronisation:** Timer-basiert (QTimer)
- **Thread-sicher:** GUI-Thread für alle Operationen

### Graph-Darstellung
- **Typ:** Torque vs. Angle (Nm vs. °)
- **Bibliothek:** pyqtgraph (performant)
- **Live-Update:** Bei jeder Messung
- **Zoom/Pan:** Maus-Bedienung möglich

## Lizenz

[Lizenz-Typ einfügen]

## Autoren

Techniker-Abschlussarbeit - [Technikergruppe]

## Kontakt

[Kontakt-Informationen einfügen]

---

**Version:** 2.0
**Datum:** Oktober 2025
**Python:** 3.13
