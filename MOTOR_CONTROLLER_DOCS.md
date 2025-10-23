# Motor-Controller Integration - Dokumentation

## 🎯 Übersicht

Das Torsionsprüfstand-System unterstützt jetzt **zwei verschiedene Motor-Controller**:
1. **Nanotec Stepper Motor** (NanoLib)
2. **Trinamic Steprocker** (PyTrinamic)

Die Auswahl erfolgt über eine **Konstante** am Anfang von `main.py`.

---

## ⚙️ Konfiguration

### In `main.py` (Zeilen 78-90):

```python
# Motor-Controller Konfiguration
# Wähle Motor-Typ: "nanotec" oder "trinamic"
MOTOR_TYPE = "nanotec"  # ← HIER ändern!

# Nanotec-spezifische Konfiguration
NANOTEC_BUS_HARDWARE = "ixxat"  # "ixxat", "kvaser", "socketcan"

# Trinamic-spezifische Konfiguration
TRINAMIC_COM_PORT = "COM3"  # COM-Port des Steprocker
TRINAMIC_MOTOR_ID = 0  # Motor ID
```

---

## 🏗️ Architektur

### Klassendiagramm:

```
MotorControllerBase (Abstract)
       ↑
       |
    ┌──┴──┐
    |      |
Nanotec  Trinamic
```

### Dateien:

```
src/hardware/
├── motor_controller_base.py       # Abstract Base Class
├── nanotec_motor_controller.py    # Nanotec Implementation
└── trinamic_motor_controller.py   # Trinamic Implementation
```

---

## 🔌 Motor-Controller Methoden

Beide Controller implementieren dieselbe Schnittstelle:

### 1. `connect() -> bool`
Verbindet mit dem Motor-Controller.

```python
if controller.connect():
    print("Verbunden!")
```

### 2. `disconnect() -> None`
Trennt die Verbindung.

```python
controller.disconnect()
```

### 3. `home_position() -> bool`
Fährt Motor in Home-Position (0°).

```python
controller.home_position()
```

### 4. `move_continuous(velocity: float) -> bool`
Startet kontinuierliche Bewegung mit konstanter Geschwindigkeit.

**Wichtig:** Motor läuft bis `stop_movement()` aufgerufen wird!

```python
controller.move_continuous(10.0)  # 10°/s im Uhrzeigersinn
controller.move_continuous(-10.0) # 10°/s gegen Uhrzeigersinn
```

### 5. `stop_movement() -> bool`
Stoppt die Bewegung sofort.

```python
controller.stop_movement()
```

### 6. `get_position() -> float`
Liest aktuelle Position in Grad.

```python
position = controller.get_position()  # z.B. 45.5°
```

### 7. `is_motor_moving() -> bool`
Prüft ob Motor in Bewegung.

```python
if controller.is_motor_moving():
    print("Motor läuft!")
```

---

## 🎮 Verwendung

### A) In main.py automatisch:

```python
# main.py erstellt automatisch den richtigen Controller basierend auf MOTOR_TYPE
if MOTOR_TYPE.lower() == "nanotec":
    controller = NanotecMotorController(...)
elif MOTOR_TYPE.lower() == "trinamic":
    controller = TrinamicMotorController(...)
```

### B) Manuell in eigenem Code:

```python
from src.hardware import NanotecMotorController, TrinamicMotorController

# Nanotec verwenden
controller = NanotecMotorController(
    bus_hardware="ixxat",
    demo_mode=False
)

# ODER Trinamic verwenden
controller = TrinamicMotorController(
    port="COM3",
    motor_id=0,
    demo_mode=False
)

# Gleiche Schnittstelle für beide!
controller.connect()
controller.home_position()
controller.move_continuous(10.0)
time.sleep(5)
controller.stop_movement()
controller.disconnect()
```

---

## 🧪 Testprogramm

**Datei:** `test_motor_controller.py`

### Ausführen:

```powershell
python test_motor_controller.py
```

### Konfiguration im Test:

```python
# In test_motor_controller.py anpassen:
MOTOR_TYPE = "nanotec"  # oder "trinamic"
DEMO_MODE = True        # oder False für echte Hardware
```

### Tests:
1. ✓ Verbindung zum Controller
2. ✓ Home-Position anfahren
3. ✓ Kontinuierliche Bewegung (5s mit Positionsanzeige)
4. ✓ Bidirektionale Bewegung (+/- Richtung)

---

## 🎨 Demo-Modus

Beide Controller unterstützen Demo-Modus:

```python
controller = NanotecMotorController(demo_mode=True)
```

**Im Demo-Modus:**
- ✅ Keine echte Hardware benötigt
- ✅ Position wird simuliert (basierend auf Zeit + Geschwindigkeit)
- ✅ Alle Methoden funktionieren
- ✅ Perfekt zum Testen der Logik

---

## 📊 Workflow im Hauptprogramm

### 1. Hardware aktivieren:
```
Button: "Activate Hardware"
  → Erstellt Motor-Controller basierend auf MOTOR_TYPE
  → Verbindet (connect())
  → LED wird grün bei Erfolg
```

### 2. Home-Position:
```
Button: "Home Position"
  → controller.home_position()
  → Kalibriert Nullpunkt
```

### 3. Messung starten:
```
Button: "Start Process"
  → velocity = get_max_velocity()  # von GUI
  → controller.move_continuous(velocity)
  → Timer startet für Datenerfassung
```

### 4. Messung stoppen:
```
Button: "Stop Process"
  → controller.stop_movement()
  → Timer stoppt
```

---

## 🔧 Hardware-spezifische Details

### Nanotec (NanoLib):

**Benötigte Hardware:**
- Nanotec Stepper Motor
- Nanotec Driver (C5-E, N5, etc.)
- CAN-Bus Interface (IXXAT, Kvaser, etc.)

**Bibliothek:**
```powershell
pip install nanotec-nanolib-win
```

**Konfiguration:**
- `NANOTEC_BUS_HARDWARE`: "ixxat", "kvaser", "socketcan"

### Trinamic (PyTrinamic):

**Benötigte Hardware:**
- Trinamic Stepper Motor
- Trinamic Steprocker Board (z.B. TMCM-1240)
- USB-Verbindung

**Bibliothek:**
```powershell
pip install pytrinamic
```

**Konfiguration:**
- `TRINAMIC_COM_PORT`: "COM3" (Windows) oder "/dev/ttyUSB0" (Linux)
- `TRINAMIC_MOTOR_ID`: 0 (Standard)

---

## ⚠️ Wichtige Hinweise

### 1. Kontinuierliche Bewegung:
- Motor läuft **eigenständig** bis `stop_movement()` aufgerufen wird
- **Nicht vergessen zu stoppen!**

### 2. Geschwindigkeit:
- Positiv (+) = Uhrzeigersinn
- Negativ (-) = Gegen Uhrzeigersinn
- Einheit: Grad/Sekunde (°/s)

### 3. Position:
- Einheit: Grad (°)
- Closed-Loop: Position wird vom Controller selbst verwaltet

### 4. Demo-Modus:
- Immer erst im Demo-Modus testen!
- Dann `DEMO_MODE = False` setzen für echte Hardware

---

## 🚀 Schnellstart

### Schritt 1: Motor-Typ wählen
```python
# In main.py Zeile 79:
MOTOR_TYPE = "nanotec"  # oder "trinamic"
```

### Schritt 2: Demo-Modus testen
```python
# In main.py Zeile 63:
DEMO_MODE = True
```

### Schritt 3: Programm starten
```powershell
python main.py
```

### Schritt 4: Hardware aktivieren
- Button "Activate Hardware" klicken
- LED wird grün → Erfolgreich!

### Schritt 5: Testen
- "Home Position" klicken
- Geschwindigkeit einstellen (z.B. 10°/s)
- "Start Process" klicken
- Motor bewegt sich kontinuierlich
- "Stop Process" klicken

---

## 📝 Zusammenfassung

✅ **Flexible Architektur:** Einfacher Wechsel zwischen Nanotec und Trinamic
✅ **Einheitliche Schnittstelle:** Gleiche Methoden für beide Controller
✅ **Demo-Modus:** Testen ohne Hardware möglich
✅ **Kontinuierliche Bewegung:** Motor läuft bis Stop-Befehl
✅ **Bidirektional:** +/- Geschwindigkeit für beide Richtungen
✅ **Geschwindigkeit einstellbar:** Beliebige °/s-Werte
✅ **Position-Tracking:** Kontinuierliche Positionsabfrage

**Status:** ✅ Produktionsbereit!
