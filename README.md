# Torsionsprüfstand Software (TorsionsTestStand)

## Beschreibung
Professionelle Software für einen Torsionsprüfstand zur Erfassung von Drehmoment und Verdrehwinkel. Die Anwendung ermöglicht präzise automatisierte Torsionsprüfungen mit SSI-Encoder-basierter Winkelmessung und Live-Visualisierung.

**Version 2.0** - Erweitert mit SSI-Encoder Integration und Single-Turn Unwrap-Logik

**Wichtiger Hinweis**: Diese Software wurde speziell für Techniker-Abschlussarbeiten entwickelt und ist mit ausführlichen deutschen Kommentaren versehen, um das Verständnis für Messtechnik, Hardware-Integration und Programmierung zu fördern.

## Hauptmerkmale
- **SSI-Encoder Integration**: Präzise Winkelmessung über Motrona Konverter (RS Components RSA 58E)
- **Single-Turn Unwrap-Logik**: Kontinuierliche Winkelmessung über 360° mit automatischem Umdrehungszähler
- **Dual-Channel DAQ**: Simultane Erfassung von Drehmoment (±10V) und Winkel (0-10V)
- **Live-Visualisierung**: Torque vs. Angle Diagramm in Echtzeit mit PyQtGraph
- **Automatische Stopbedingungen**: Max Torque oder Max Angle Überschreitung
- **Motor-Controller Integration**: Nanotec N5 (CAN-Bus) oder Trinamic Steprocker (RS485)
- **Demo-Modus**: Vollständige Simulation ohne Hardware für Tests und Entwicklung
- **Umfangreiche Dokumentation**: Über 2000 Zeilen Code mit deutschen Kommentaren
- **Robuste Fehlerbehandlung**: Sichere Hardware-Initialisierung und Cleanup

## Hardware-Anforderungen

### Aktuelle Hardware-Konfiguration

#### 1. Datenerfassung (DAQ)
- **Messkarte**: National Instruments NI-6000 (oder kompatibel)
- **Kanal ai0**: Drehmoment-Messung (±10V Eingang, RSE)
- **Kanal ai1**: Winkel-Messung (0-10V Eingang, RSE)
- **Sampling-Rate**: 10 Hz (100ms Intervall)

#### 2. Drehmoment-Sensor
- **Modell**: DF-30 Drehmoment-Sensor
- **Messbereich**: ±20 Nm
- **Ausgang**: ±10V über Messverstärker
- **Skalierung**: 2.0 Nm/V (20 Nm / 10 V)

#### 3. Winkel-Messung (SSI-Encoder System)
- **Encoder**: RS Components RSA 58E SSI
  - 13-Bit Single-Turn Auflösung (8192 Steps/360°)
  - 12-Bit Multi-Turn (4096 Umdrehungen)
  - SSI Protokoll (synchron seriell)
- **Konverter**: Motrona 7386.5010 (SSI zu Analog)
  - Eingang: SSI Encoder Signal
  - Ausgang: 0-10V Analog (0V = 0°, 10V = 360°)
- **Betriebsmodus**: Single-Turn mit Software-Unwrap (kontinuierliche Winkelmessung)

#### 4. Motor-Controller
**Option A: Nanotec N5** (Standard)
- Closed-Loop Schrittmotor
- Kommunikation: Modbus TCP über CAN-Bus
- Benötigte Hardware: IXXAT CAN-USB Interface (oder ähnlich)
- Bibliothek: NanoLib (NI Nanotec)

**Option B: Trinamic Steprocker** (Alternative)
- Schrittmotor-Controller
- Kommunikation: RS485
- COM-Port: Einstellbar (z.B. COM3)

### Verkabelung

```
┌─────────────────┐         ┌──────────────┐
│  DF-30 Sensor   │──±10V──→│ NI-6000 ai0  │
│  (Drehmoment)   │         │              │
└─────────────────┘         │              │
                            │              │
┌─────────────────┐   SSI   ┌──────────┐   │
│ RSA 58E Encoder │────────→│ Motrona  │   │
│   (Winkel)      │         │ 7386.5010│   │
└─────────────────┘         └────┬─────┘   │
                             0-10V          │
                              ↓             │
                            ai1 ←───────────┘
                            └──────────────┘
```

## Software-Anforderungen
- **Python**: 3.13+ (empfohlen) oder 3.9+
- **PyQt6**: GUI Framework (Benutzeroberfläche)
- **pyqtgraph**: Echtzeit-Diagramme und Visualisierung
- **nidaqmx**: National Instruments DAQ-Treiber (für NI-6000)
- **NanoLib**: Nanotec Motor-Bibliothek (optional, nur bei Nanotec-Motoren)

## Installation

### 1. Repository klonen
```bash
git clone [repository-url]
cd TorsionsTestStand
```

### 2. Python-Abhängigkeiten installieren
```bash
pip install -r requirements.txt
```

### 3. Hardware-Treiber installieren

#### NI-DAQmx Treiber
- Download von [ni.com](https://www.ni.com/de-de/support/downloads/drivers/download.ni-daqmx.html)
- Installation der NI-DAQmx Runtime oder vollständiger Suite
- Teste Installation mit NI MAX (Measurement & Automation Explorer)

#### Nanotec NanoLib (falls Nanotec-Motor verwendet wird)
- Download von Nanotec Website
- Installation gemäß Nanotec Dokumentation
- CAN-Bus Hardware-Treiber (z.B. IXXAT)

### 4. Hardware-Konfiguration anpassen

Öffne `main.py` und passe die Konstanten an deine Hardware an:

```python
# ===== DEMO-MODUS =====
DEMO_MODE = True  # Für Tests ohne Hardware auf True lassen

# ===== DREHMOMENT-SENSOR =====
TORQUE_SENSOR_MAX_NM = 20.0        # Max. Drehmoment deines Sensors [Nm]
TORQUE_SENSOR_MAX_VOLTAGE = 10.0   # Max. Spannung deines Sensors [V]
DAQ_CHANNEL_TORQUE = "Dev1/ai0"    # DAQ-Kanal für Drehmoment

# ===== WINKEL-MESSUNG (SSI-Encoder) =====
ANGLE_MEASUREMENT_SOURCE = "daq"    # "daq" = über NI-6000, "motor" = über Motor-Controller
ANGLE_ENCODER_MODE = "single_turn"  # "single_turn" = 0-360° mit Unwrap
DAQ_CHANNEL_ANGLE = "Dev1/ai1"      # DAQ-Kanal für Winkel
ANGLE_VOLTAGE_MIN = 0.0             # Motrona Ausgang Min [V]
ANGLE_VOLTAGE_MAX = 10.0            # Motrona Ausgang Max [V]
ANGLE_MAX_DEG = 360.0               # Encoder Max Winkel [°]

# ===== MOTOR-CONTROLLER =====
MOTOR_TYPE = "nanotec"              # "nanotec" oder "trinamic"
NANOTEC_BUS_HARDWARE = "ixxat"      # CAN-Bus Interface

# ===== MESS-PARAMETER =====
MEASUREMENT_INTERVAL = 100          # Messintervall [ms] (10 Hz)
DEFAULT_MAX_ANGLE = 360.0           # Standard Max Winkel [°]
DEFAULT_MAX_TORQUE = 15.0           # Standard Max Drehmoment [Nm]
DEFAULT_MAX_VELOCITY = 10.0         # Standard Geschwindigkeit [°/s]
```

## Verwendung

### 1. Hardware aktivieren
- Button "Activate Hardware" klicken
- Prüfen ob LED grün wird (Hardware erfolgreich initialisiert)

### 2. Parameter einstellen
- **Force Scale**: Umrechnungsfaktor Volt zu Newton
- **Distance Scale**: Umrechnungsfaktor Volt zu Millimeter  
- **Interval**: Messintervall in Millisekunden
- **Sample Name**: Name der Probe für die Dateiablage

### 3. Projektordner wählen
- "Select Project Directory" klicken
- Ordner für Messdaten auswählen

### 5. Programm starten
```bash
python main.py
```

## Verwendung

### Demo-Modus vs. Hardware-Modus

**Demo-Modus (DEMO_MODE = True)**
- ✓ Keine Hardware erforderlich
- ✓ Simulierte Daten für Tests
- ✓ Ideal für Code-Entwicklung
- 🟢 Demo-LED leuchtet GRÜN

**Hardware-Modus (DEMO_MODE = False)**
- ⚠ Alle Hardware muss verbunden sein
- ⚠ Motor bewegt sich real!
- ⚠ Sensoren müssen kalibriert sein
- 🔴 Demo-LED leuchtet ROT

### Schritt-für-Schritt Anleitung

#### 1. Projektordner wählen
- Button **"Select Project Directory"** klicken
- Ordner für Messdaten auswählen
- Alle Messungen werden hier gespeichert

#### 2. Hardware aktivieren
- Button **"Activate Hardware"** klicken
- Warten bis LEDs sich ändern:
  - 🟢 **DMM LED** (GRÜN) = NI-6000 DAQ erfolgreich verbunden
  - 🟢 **Controller LED** (GRÜN) = Motor-Controller verbunden
  - 🔴 (ROT) = Fehler bei Initialisierung
- Im Log-Fenster werden Details angezeigt

#### 3. Home-Position (Optional aber empfohlen)
- Button **"Home Position"** klicken
- Motor fährt auf 0° Position
- Unwrap-Zähler wird zurückgesetzt
- Wichtig für Reproduzierbarkeit!

#### 4. Parameter einstellen
- **Sample Name**: Probenbezeichnung (z.B. "Probe_001")
- **Max Angle**: Maximaler Verdrehwinkel in Grad (z.B. 360°)
- **Max Torque**: Abbruch-Drehmoment in Nm (z.B. 15 Nm)
- **Max Velocity**: Drehgeschwindigkeit in °/s (z.B. 10°/s)
  - Positiv = Im Uhrzeigersinn
  - Negativ = Gegen Uhrzeigersinn

#### 5. Messung durchführen
- Button **"Start Measurement"** klicken
- Motor beginnt mit konstanter Geschwindigkeit zu drehen
- Live-Daten erscheinen im **Torque vs. Angle** Graphen
- Messung stoppt automatisch bei:
  - Max Angle erreicht ODER
  - Max Torque überschritten
- Manueller Stopp: Button **"Stop Measurement"**

#### 6. Daten auswerten
Messdaten werden automatisch gespeichert in:
```
Projektordner/
└── YYYYMMDD_HHMMSS_Probenname/
    └── YYYYMMDD_HHMMSS_Probenname_DATA.txt
```

**Dateiformat**: Tab-getrennte Textdatei
```
Time            Voltage_Torque  Voltage_Angle  Torque  Angle  Turn_Counter
14:23:15.123    2.5            3.8            5.0     136.8  0
14:23:15.223    2.6            3.9            5.2     140.4  0
14:23:15.323    2.7            4.0            5.4     144.0  0
...
```

**Spalten**:
- **Time**: Zeitstempel [HH:mm:ss.fff]
- **Voltage_Torque**: Rohe Spannung vom Drehmomentsensor [V]
- **Voltage_Angle**: Rohe Spannung vom Motrona Konverter [V]
- **Torque**: Berechnetes Drehmoment [Nm]
- **Angle**: Berechneter Winkel (kontinuierlich) [°]
- **Turn_Counter**: Anzahl der Umdrehungen (± ganze Zahl)

### Manuelle Einzelmessung
- Button **"Measure"** klicken
- Liest einmalig aktuelle Werte aus
- Nützlich für:
  - Hardware-Tests
  - Sensor-Kalibrierung
  - Nullpunkt-Überprüfung

## SSI-Encoder und Unwrap-Logik

### Problem: Single-Turn Encoder (0-360°)
Der RS Components RSA 58E Encoder gibt im Single-Turn Modus nur Werte von 0° bis 360° aus. Bei einer kompletten Umdrehung springt der Wert von 360° zurück auf 0° (oder umgekehrt bei Rückwärtsdrehung).

**Beispiel ohne Unwrap:**
```
Zeit   | Rohwinkel | Problem
-------|-----------|----------------------------------
0.0s   | 350°      | OK
0.1s   | 358°      | OK
0.2s   | 5°        | SPRUNG! (Motor hat nicht rückwärts gedreht!)
0.3s   | 12°       | Eigentlich bei 372° (360° + 12°)
```

### Lösung: Unwrap-Algorithmus
Die Software erkennt diese Sprünge automatisch und berechnet den kontinuierlichen Winkel:

**Mit Unwrap:**
```
Zeit   | Rohwinkel | Delta  | Turn_Counter | Kontinuierlicher Winkel
-------|-----------|--------|--------------|------------------------
0.0s   | 350°      | -      | 0            | 350°
0.1s   | 358°      | +8°    | 0            | 358°
0.2s   | 5°        | -353°  | +1 (erkannt!)| 365° (5° + 360×1)
0.3s   | 12°       | +7°    | 1            | 372° (12° + 360×1)
0.4s   | 355°      | -17°   | 0 (Rückwärts!)| 355° (355° + 360×0)
```

**Erkennung:**
- Wenn Delta < -180° → Vorwärts-Wrap → Turn_Counter +1
- Wenn Delta > +180° → Rückwärts-Wrap → Turn_Counter -1
- Kontinuierlicher Winkel = Rohwinkel + (360° × Turn_Counter)

**Wichtige Bedingung:**
- Sampling-Rate muss hoch genug sein (Standard: 10 Hz = 100ms)
- Bei zu niedriger Rate können Wraps verpasst werden!

Siehe auch: **SSI_ENCODER_INTEGRATION.md** für detaillierte PAPs (Programmablaufpläne)

## GUI-Übersicht

```
┌─────────────────────────────────────────────────────────┐
│  Torsions Test Stand - DF-30 Sensor                     │
├──────────────────┬──────────────────────────────────────┤
│ Control Panel    │  Log Output                          │
│                  │  ┌────────────────────────────────┐  │
│ 🟢 Demo LED      │  │ 14:23:15 INFO  MAIN  ...       │  │
│ 🔴 DMM LED       │  │ 14:23:16 INFO  DAQ   ...       │  │
│ 🔴 Controller LED│  │ 14:23:17 WARNING Motor ...     │  │
│                  │  └────────────────────────────────┘  │
│ [Select Dir]     │                                      │
│ [Activate HW]    │  Torque vs. Angle Graph             │
│ [Home Position]  │  ┌────────────────────────────────┐  │
│ [Start Meas.]    │  │        Torque [Nm]             │  │
│ [Stop Meas.]     │  │ 20  ╱───                       │  │
│ [Measure]        │  │    ╱                           │  │
│                  │  │ 10╱                            │  │
│ Sample: _______  │  │  ╱                             │  │
│ Max Angle: ___   │  │ 0└──────────────────────>      │  │
│ Max Torque: __   │  │  0   90   180  270  360        │  │
│ Max Velocity: _  │  │        Angle [°]               │  │
│                  │  └────────────────────────────────┘  │
└──────────────────┴──────────────────────────────────────┘
```

## Projektstruktur

```
TorsionsTestStand/
├── main.py                          # Hauptprogramm (2150+ Zeilen, umfangreich kommentiert)
├── requirements.txt                 # Python-Abhängigkeiten
├── README.md                        # Diese Datei
├── README_USAGE.md                  # Erweiterte Benutzungshinweise
├── SSI_ENCODER_INTEGRATION.md       # Detaillierte SSI-Encoder Dokumentation mit PAPs
├── MOTOR_CONTROLLER_DOCS.md         # Motor-Controller Dokumentation
├── REFACTORING_NOTES.md             # Entwicklungs-Notizen
│
├── src/
│   ├── gui/
│   │   ├── torsions_test_stand.ui   # Qt Designer GUI-Layout
│   │   └── stylesheet.py            # Dark-Mode Stylesheet
│   │
│   ├── hardware/
│   │   ├── __init__.py
│   │   ├── daq_controller.py        # DAQmxTask Klasse (NI-6000 Steuerung)
│   │   ├── motor_controller_base.py # Basis-Klasse für Motor-Controller
│   │   ├── n5_nanotec_controller.py # Nanotec N5 Implementation
│   │   ├── nanotec_motor_controller.py
│   │   ├── trinamic_motor_controller.py # Trinamic Steprocker Implementation
│   │   └── demo_simulator.py        # Hardware-Simulator für Demo-Modus
│   │
│   └── utils/
│       └── logger_helper.py         # GuiLogger für Log-Fenster
│
├── test/
│   ├── test_motor_controller.py     # Unit-Tests Motor-Controller
│   ├── test_n5_nanotec.py           # Unit-Tests Nanotec
│   └── test_ni6000.py               # Unit-Tests NI-6000 DAQ
│
└── Docs/
    └── NanoLib-Python_User_Manual_V1.3.4.pdf  # Nanotec Dokumentation
```

## Für Techniker-Abschlussarbeiten

### Lernziele
Diese Software demonstriert professionell:
- **Messtechnik**: 
  - Analoge Signalerfassung mit NI-DAQmx
  - SSI-Encoder Integration über Konverter
  - Single-Turn Unwrap-Algorithmus
  - Dual-Channel Datenerfassung
  
- **Hardware-Integration**:
  - CAN-Bus Kommunikation (Nanotec)
  - RS485 Kommunikation (Trinamic)
  - DAQ-Hardware Abstraktion
  - Fehlerbehandlung bei Hardware-Ausfall
  
- **Programmierung**:
  - Objektorientierte Programmierung (Python)
  - Design Patterns (Factory, Strategy)
  - Event-driven GUI (PyQt6)
  - Threading und Timer
  
- **Datenanalyse**:
  - Echtzeit-Visualisierung mit PyQtGraph
  - Datenaufzeichnung und -export
  - Signalverarbeitung (Unwrap)

### Code-Qualität
- ✓ **2150+ Zeilen** ausführlich kommentierter Code
- ✓ **Deutsche Kommentare** für alle Funktionen
- ✓ **PAPs (Programmablaufpläne)** in Mermaid-Format
- ✓ **Visuelles Design**: Box-Diagramme, Tabellen, Beispiele
- ✓ **Unit-Tests** für kritische Komponenten
- ✓ **Vollständige Dokumentation** (4 separate MD-Dateien)

### Verständnis fördern
Jede Funktion in `main.py` enthält:
- **╔═══╗ Visual Header**: Sofort erkennbare Abschnitte
- **FUNKTION**: Was macht die Funktion?
- **WARUM WICHTIG**: Kontext und Bedeutung
- **BEISPIEL**: Praktische Anwendungsfälle
- **PARAMETER/RÜCKGABE**: Ein/Ausgabe-Dokumentation
- **HINWEIS FÜR TECHNIKER**: Besondere Anmerkungen
- **Inline-Kommentare**: Schritt-für-Schritt Erklärung

### Erweiterungsmöglichkeiten
Für weiterführende Arbeiten und Projekte:
- ✓ **Multi-Turn Modus** implementieren (Vorbereitung vorhanden)
- ✓ **Automatische Testsequenzen** (z.B. Rampe, Sinus, Zyklisch)
- ✓ **Erweiterte Auswertung** (Hysterese, E-Modul, Torsionssteifigkeit)
- ✓ **Kalibrierungs-Assistent** für Sensoren
- ✓ **Excel/CSV Export** mit Diagrammen
- ✓ **Grenzwert-Alarme** mit akustischer Warnung
- ✓ **Datenbank-Integration** für Langzeit-Archivierung
- ✓ **Remote-Zugriff** über Netzwerk
- ✓ **SPS-Integration** für industrielle Umgebung

## Fehlerbehebung

### Hardware nicht erkannt
**Problem**: LEDs bleiben ROT nach "Activate Hardware"

**Lösungen**:
- ✓ Prüfe ob DEMO_MODE = False gesetzt ist
- ✓ NI-DAQmx Treiber installiert? → NI MAX öffnen und Gerät suchen
- ✓ DAQ-Kanal-Namen korrekt? → In NI MAX Device-Namen prüfen (Dev1, Dev2, etc.)
- ✓ USB-Kabel fest verbunden?
- ✓ Im Log-Fenster nach Fehlerdetails suchen

### Keine Winkelwerte / Angle bleibt bei 0°
**Problem**: Torque-Werte OK, aber Angle = 0.0°

**Lösungen**:
- ✓ Motrona 7386.5010 eingeschaltet und konfiguriert?
- ✓ SSI-Encoder Verkabelung zum Motrona prüfen
- ✓ Motrona Ausgang (0-10V) mit NI-6000 ai1 verbunden?
- ✓ DAQ_CHANNEL_ANGLE = "Dev1/ai1" korrekt gesetzt?
- ✓ ANGLE_MEASUREMENT_SOURCE = "daq" gesetzt?
- ✓ Teste mit "Measure" Button → Voltage_Angle sollte 0-10V zeigen

### Falsche Wrap-Erkennung
**Problem**: Turn_Counter erhöht sich unerwartet

**Ursachen**:
- ⚠ Sampling-Rate zu niedrig (Messintervall zu groß)
- ⚠ Motor dreht zu schnell

**Lösungen**:
- ✓ MEASUREMENT_INTERVAL verringern (z.B. von 100ms auf 50ms)
- ✓ MAX_VELOCITY reduzieren (z.B. von 20°/s auf 10°/s)
- ✓ Formel: Max Velocity < (180° / Intervall_in_Sekunden)
  - Beispiel: 100ms → Max 1800°/s theoretisch, praktisch < 50°/s empfohlen

### Motor reagiert nicht
**Problem**: Motor bewegt sich nicht bei "Start Measurement"

**Lösungen bei Nanotec**:
- ✓ CAN-Bus Interface (IXXAT) verbunden?
- ✓ NanoLib installiert?
- ✓ NANOTEC_BUS_HARDWARE = "ixxat" korrekt?
- ✓ Motor eingeschaltet und im Idle-Modus?
- ✓ Im Log: "Motor initialized" sichtbar?

**Lösungen bei Trinamic**:
- ✓ RS485-Kabel korrekt verbunden (A, B, GND)?
- ✓ TRINAMIC_COM_PORT stimmt? (z.B. "COM3")
- ✓ Baudrate und Motor-ID korrekt?
- ✓ Teste mit Trinamic TMCL-IDE Software

### Programm startet nicht
**Problem**: Fehler beim Start

**Lösungen**:
- ✓ Python 3.9+ installiert? → `python --version`
- ✓ Alle Abhängigkeiten installiert? → `pip install -r requirements.txt`
- ✓ PyQt6 korrekt installiert? → `pip list | grep PyQt6`
- ✓ GUI-Datei vorhanden? → `src/gui/torsions_test_stand.ui`
- ✓ Starte im Demo-Modus: DEMO_MODE = True

### Messwerte schwanken stark
**Problem**: Torque oder Angle Werte "springen"

**Lösungen**:
- ✓ Sensor-Verkabelung prüfen (Abschirmung, Masseverbindung)
- ✓ Sensor-Spannungsversorgung stabil?
- ✓ Elektromagnetische Störungen (EMI) von Motorsteuerung?
  - Abstand zwischen Sensor-Kabel und Motor-Kabel vergrößern
  - Geschirmte Kabel verwenden
- ✓ Optional: Software-Filter in measure() implementieren (Moving Average)

## Bekannte Einschränkungen

- **Single-Turn Unwrap**: Erfordert kontinuierliche Sampling (keine Lücken!)
- **Multi-Turn Modus**: Noch nicht vollständig implementiert (Vorbereitung vorhanden)
- **CAN-Bus**: Erfordert zusätzliche Hardware (IXXAT, Kvaser, etc.)
- **Kalibrierung**: Aktuell manuelle Skalierungs-Faktoren (kein Assistenten)

## Dokumentation

### Haupt-Dokumentation
- **README.md** (diese Datei): Übersicht, Installation, Verwendung
- **README_USAGE.md**: Erweiterte Nutzungshinweise
- **SSI_ENCODER_INTEGRATION.md**: 
  - Detaillierte SSI-Encoder Dokumentation
  - 5 Programmablaufpläne (PAPs) in Mermaid
  - Unwrap-Algorithmus mit visuellen Beispielen
  - Hardware-Konfiguration Motrona 7386.5010
  - Validierungs- und Test-Szenarien
- **MOTOR_CONTROLLER_DOCS.md**: Motor-Controller Implementierung
- **REFACTORING_NOTES.md**: Entwicklungs-Historie

### Code-Kommentare
- **main.py**: Jede Funktion mit 50-100 Zeilen deutscher Kommentare
- **daq_controller.py**: Hardware-Abstraktion mit Erklärungen
- **motor_controller_*.py**: Spezifische Motor-Implementierungen

### Tests
- **test/test_motor_controller.py**: Unit-Tests für Motor-Controller-Basis
- **test/test_n5_nanotec.py**: Nanotec-spezifische Tests
- **test/test_ni6000.py**: DAQ-Hardware Tests

## Changelog

### Version 2.0 (Oktober 2025)
- ✅ SSI-Encoder Integration (RS Components RSA 58E)
- ✅ Motrona 7386.5010 Konverter-Unterstützung
- ✅ Single-Turn Unwrap-Algorithmus mit Turn Counter
- ✅ Dual-Channel DAQ (ai0: Torque, ai1: Angle)
- ✅ Umfangreiche deutsche Kommentare (2150+ Zeilen)
- ✅ PAPs (Programmablaufpläne) in Mermaid-Format
- ✅ Demo-Modus für hardwarelose Tests
- ✅ GUI-Logger mit Farb-Codierung
- ✅ Home-Position Funktionalität
- ✅ Kontinuierliche Winkelmessung über 360°

### Version 1.0
- Basis-Implementation mit Motor-Controller
- Einfache Winkelmessung über Motor
- Drehmoment-Erfassung
- Grundlegende GUI

## Lizenz
Entwickelt für Techniker-Abschlussarbeiten und Ausbildungszwecke.
Frei verwendbar für akademische und Ausbildungs-Projekte.

## Kontakt & Support
Bei Fragen zur:
- **Hardware-Integration**: Issues erstellen mit Hardware-Details
- **Code-Erweiterungen**: Pull Requests willkommen
- **Dokumentation**: Verbesserungsvorschläge als Issues

---
**Entwickelt mit ❤️ für die Technikergruppe Abschlussarbeit 2025**
