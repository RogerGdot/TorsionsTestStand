# Torsionsprüfstand Software

## Beschreibung
Software für einen Torsionsprüfstand zur Techniker-Abschlussarbeit. Die Anwendung ermöglicht die einfache Erfassung von Kraft- und Distanzmessungen während Torsionsversuchen an Prüfkörpern.

**Wichtiger Hinweis**: Diese Software wurde speziell für Ausbildungszwecke entwickelt und ist mit ausführlichen Kommentaren versehen, um das Verständnis für die Messtechnik und Programmierung zu fördern.

## Features
- **Einfache Konfiguration**: Alle Parameter über Konstanten am Anfang der main.py
- **Flexible Hardware-Unterstützung**: NI DAQmx oder andere Messkarten möglich
- **Live-Datenvisualisierung**: Kraft vs. Distanz Diagramm in Echtzeit
- **Datenaufzeichnung**: Automatische Speicherung aller Messdaten in Textdateien
- **Motor-Vorbereitung**: Struktur für Stepper-, Servo- oder DC-Motoren vorhanden
- **Ausführliche Kommentierung**: Ideal für Lernzwecke und Techniker-Ausbildung
- **Robuste Fehlerbehandlung**: Programm stürzt nicht bei Hardware-Problemen ab

## Hardware-Anforderungen

### Mindestanforderungen
- **Messkarte**: NI USB-6001 oder ähnliche DAQ-Hardware
- **Kraftsensor**: DMS-basierter Kraftaufnehmer mit Verstärker
- **Distanzsensor**: Analoger Sensor (z.B. Potentiometer, LVDT)
- **Motor**: Beliebiger Antrieb (Implementierung nach Bedarf)

### Flexible Hardware-Unterstützung
Die Software ist bewusst flexibel gehalten:
- **Messkarten**: NI DAQmx, aber auch andere Hersteller möglich
- **Motoren**: Vorbereitet für Stepper, Servo oder DC-Motoren
- **Sensoren**: Alle analogen Kraft- und Distanzsensoren

## Software-Anforderungen
- Python 3.13+ (oder 3.9+)
- PyQt6 (Benutzeroberfläche)
- pyqtgraph (Diagramme) 
- NI DAQmx (falls NI-Hardware verwendet wird)

## Installation

### 1. Python-Umgebung vorbereiten
```bash
# Repository klonen
git clone [repository-url]
cd TorsionsTestStand

# Abhängigkeiten installieren  
pip install -r requirements.txt
```

### 2. Hardware-Konfiguration
Passe die Konstanten am Anfang der `main.py` an deine Hardware an:

```python
# Hardware-Konfiguration Messkarte
FORCE_SCALE = 1.0               # Skalierungsfaktor für Kraftmessung [N/V]
DISTANCE_SCALE = 1.0            # Skalierungsfaktor für Distanzmessung [mm/V]  
DAQ_CHANNEL_FORCE = "Dev1/ai0"  # DAQ-Kanal für Kraftmessung
DAQ_CHANNEL_DISTANCE = "Dev1/ai1" # DAQ-Kanal für Distanzmessung

# Motor-Konfiguration (für zukünftige Erweiterung)
MOTOR_TYPE = "STEPPER"          # "STEPPER", "SERVO", "DC" oder "UNKNOWN"
MOTOR_ENABLED = True            # Motor-Steuerung aktivieren
```

### 3. Programm starten
```bash
python main.py
```

## Konfiguration für verschiedene Hardware

### NI DAQmx-Messkarten
- Standard-Konfiguration funktioniert mit NI USB-6001
- Kanäle: Dev1/ai0 bis Dev1/ai7 verfügbar
- Automatische Erkennung ob NI DAQmx verfügbar ist

### Andere Messkarten
Für andere Hersteller (z.B. Advantech, Measurement Computing):
1. `NIDAQMX_AVAILABLE = False` in der imports-Sektion setzen
2. Eigene Hardware-Implementierung in der `DAQmxTask` Klasse ergänzen

### Motor-Integration
Je nach verwendetem Motor:
1. `MOTOR_TYPE` entsprechend setzen ("STEPPER", "SERVO", "DC")
2. `MOTOR_ENABLED = True` setzen  
3. Konkrete Motor-Steuerung in der `MotorController` Klasse implementieren

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

### 4. Messung durchführen
- "Start Measurement" klicken
- Live-Daten im Diagramm beobachten
- "Stop Measurement" zum Beenden

### 5. Daten auswerten
Messdaten werden automatisch gespeichert als:
- **Dateiformat**: Tab-getrennte Textdatei (.txt)
- **Spalten**: Time, Voltage_Force, Voltage_Distance, Force, Distance
- **Einheiten**: [HH:mm:ss.f], [V], [V], [N], [mm]

## Für Techniker-Abschlussarbeiten

### Lernziele
Diese Software demonstriert:
- **Messtechnik**: Analoge Signalerfassung und -verarbeitung
- **Programmierung**: Objektorientierte Programmierung mit Python
- **GUI-Entwicklung**: Benutzeroberflächen mit PyQt6
- **Hardware-Integration**: Kommunikation mit Messgeräten
- **Datenanalyse**: Aufzeichnung und Visualisierung von Messdaten

### Code-Struktur verstehen
- **Konstanten-Bereich**: Alle wichtigen Parameter zentral am Anfang
- **Hardware-Klassen**: `DAQmxTask` und `MotorController` für Hardware-Abstraktion  
- **MainWindow**: Zentrale GUI-Logik und Messablauf
- **measure()**: Herzstück der Datenerfassung mit detaillierten Kommentaren

### Erweiterungsmöglichkeiten
Für weiterführende Arbeiten:
- Automatische Motorsteuerung für definierte Versuche
- Erweiterte Datenauswertung (Statistik, Diagramme)
- Kalibrierung und Nullpunkt-Einstellung
- Export in Excel/CSV-Format
- Grenzwert-Überwachung und Alarme

## Lizenz
Entwickelt für Ausbildungszwecke - frei verwendbar für Techniker-Abschlussarbeiten

## Support
Bei Fragen zur Hardware-Integration oder Code-Erweiterungen können Issues erstellt werden.
