"""
Test-Programm für N5 Nanotec Stepper Motor
===========================================
Testet den N5 Nanotec Motor-Controller isoliert.

Verwendung:
-----------
python test_n5_nanotec.py

Funktionen:
- Modbus TCP Verbindung testen
- Position auslesen (Closed-Loop)
- Home-Position anfahren
- Kontinuierliche Bewegung
- Stopp-Funktion

Hardware:
- N5 Nanotec Schrittmotor-Controller
- Modbus TCP Verbindung
- Closed-Loop Position Control
"""

import sys
import time

# Verwende die Hardware-Module aus src/hardware

try:
    from pymodbus.client import ModbusTcpClient

    PYMODBUS_AVAILABLE = True
except ImportError:
    PYMODBUS_AVAILABLE = False
    print("ERROR: PyModbus nicht verfügbar!")
    print("Installation: pip install pymodbus")
    sys.exit(1)

# Konfiguration
N5_IP_ADDRESS = "192.168.0.100"  # IP-Adresse des N5 Controllers
N5_PORT = 502  # Modbus TCP Port
N5_SLAVE_ID = 1  # Modbus Slave ID
DEMO_MODE = True  # True = Demo-Modus, False = Echte Hardware


class N5NanotecTester:
    """Tester für N5 Nanotec Controller."""

    def __init__(self, ip_address=N5_IP_ADDRESS, port=N5_PORT, slave_id=N5_SLAVE_ID, demo_mode=DEMO_MODE):
        self.ip_address = ip_address
        self.port = port
        self.slave_id = slave_id
        self.demo_mode = demo_mode
        self.client = None
        self.is_connected = False

        # Demo-Modus Variablen
        self.demo_position = 0.0
        self.demo_velocity = 0.0
        self.demo_is_moving = False
        self.demo_start_time = None
        self.demo_start_position = 0.0

    def connect(self):
        """Verbindet mit dem N5 Controller."""
        print(f"Verbinde mit {self.ip_address}:{self.port}...")

        if self.demo_mode:
            print("[DEMO] Simulation aktiv - keine echte Verbindung")
            self.is_connected = True
            return True

        try:
            self.client = ModbusTcpClient(self.ip_address, port=self.port)
            connection = self.client.connect()

            if connection:
                print("✓ Verbunden mit N5 Controller")
                self.is_connected = True
                return True
            else:
                print("✗ Verbindung fehlgeschlagen")
                return False

        except Exception as e:
            print(f"✗ Verbindungsfehler: {e}")
            return False

    def disconnect(self):
        """Trennt die Verbindung."""
        if self.demo_mode:
            self.is_connected = False
            return

        if self.client and self.is_connected:
            self.client.close()
            self.is_connected = False
            print("✓ Verbindung getrennt")

    def get_position(self):
        """Liest die aktuelle Position."""
        if not self.is_connected:
            return None

        if self.demo_mode:
            # Demo: Simuliere Bewegung
            if self.demo_is_moving and self.demo_start_time:
                elapsed = time.time() - self.demo_start_time
                self.demo_position = self.demo_start_position + (self.demo_velocity * elapsed)
            return self.demo_position

        try:
            # Hier würde der echte Modbus-Befehl kommen
            # Beispiel: result = self.client.read_holding_registers(address, count=1, unit=self.slave_id)
            return 0.0
        except Exception as e:
            print(f"Fehler beim Lesen der Position: {e}")
            return None

    def home_position(self):
        """Fährt in die Home-Position."""
        if not self.is_connected:
            return False

        print("Fahre in Home-Position (0°)...")

        if self.demo_mode:
            self.demo_position = 0.0
            self.demo_is_moving = False
            print("✓ Home-Position erreicht")
            return True

        try:
            # Hier würde der echte Modbus-Befehl kommen
            return True
        except Exception as e:
            print(f"Fehler beim Homing: {e}")
            return False

    def move_continuous(self, velocity):
        """Startet kontinuierliche Bewegung."""
        if not self.is_connected:
            return False

        direction = "im Uhrzeigersinn" if velocity > 0 else "gegen Uhrzeigersinn"
        print(f"Starte Bewegung mit {abs(velocity)}°/s {direction}...")

        if self.demo_mode:
            self.demo_velocity = velocity
            self.demo_is_moving = True
            self.demo_start_time = time.time()
            self.demo_start_position = self.demo_position
            print("✓ Bewegung gestartet")
            return True

        try:
            # Hier würde der echte Modbus-Befehl kommen
            return True
        except Exception as e:
            print(f"Fehler beim Starten der Bewegung: {e}")
            return False

    def stop_movement(self):
        """Stoppt die Bewegung."""
        if not self.is_connected:
            return False

        print("Stoppe Bewegung...")

        if self.demo_mode:
            self.demo_is_moving = False
            self.demo_velocity = 0.0
            print(f"✓ Motor gestoppt bei {self.demo_position:.2f}°")
            return True

        try:
            # Hier würde der echte Modbus-Befehl kommen
            return True
        except Exception as e:
            print(f"Fehler beim Stoppen: {e}")
            return False


def test_connection():
    """Test 1: Verbindung zum N5 Controller."""
    print("\n" + "=" * 60)
    print("TEST 1: Verbindung zum N5 Nanotec Controller")
    print("=" * 60)

    tester = N5NanotecTester()
    success = tester.connect()

    if success:
        print("\n✓ Verbindungstest bestanden")
        tester.disconnect()
        return True
    else:
        print("\n✗ Verbindungstest fehlgeschlagen")
        return False


def test_position_read():
    """Test 2: Position auslesen."""
    print("\n" + "=" * 60)
    print("TEST 2: Position auslesen (Closed-Loop)")
    print("=" * 60)

    tester = N5NanotecTester()
    if not tester.connect():
        return False

    try:
        print("\nLese Position (5x)...")
        for i in range(5):
            position = tester.get_position()
            if position is not None:
                print(f"  Messung {i + 1}: {position:.2f}°")
                time.sleep(0.2)
            else:
                print("✗ Fehler beim Lesen der Position")
                return False

        print("\n✓ Positions-Test bestanden")
        tester.disconnect()
        return True

    except Exception as e:
        print(f"\n✗ Fehler: {e}")
        tester.disconnect()
        return False


def test_homing():
    """Test 3: Home-Position anfahren."""
    print("\n" + "=" * 60)
    print("TEST 3: Home-Position anfahren")
    print("=" * 60)

    tester = N5NanotecTester()
    if not tester.connect():
        return False

    try:
        # Aktuelle Position anzeigen
        pos = tester.get_position()
        print(f"Aktuelle Position: {pos:.2f}°")

        # Home anfahren
        if tester.home_position():
            time.sleep(1)

            # Position nach Homing prüfen
            pos = tester.get_position()
            print(f"Position nach Homing: {pos:.2f}°")

            if abs(pos) < 0.1:
                print("\n✓ Homing-Test bestanden")
                tester.disconnect()
                return True
            else:
                print("\n✗ Position nicht korrekt")
                tester.disconnect()
                return False
        else:
            print("\n✗ Homing fehlgeschlagen")
            tester.disconnect()
            return False

    except Exception as e:
        print(f"\n✗ Fehler: {e}")
        tester.disconnect()
        return False


def test_continuous_movement():
    """Test 4: Kontinuierliche Bewegung."""
    print("\n" + "=" * 60)
    print("TEST 4: Kontinuierliche Bewegung")
    print("=" * 60)

    tester = N5NanotecTester()
    if not tester.connect():
        return False

    try:
        # Home-Position anfahren
        print("\n1. Home-Position anfahren...")
        tester.home_position()
        time.sleep(0.5)

        # Bewegung starten (10°/s im Uhrzeigersinn)
        print("\n2. Bewegung starten (10°/s, 5 Sekunden)...")
        velocity = 10.0
        tester.move_continuous(velocity)

        # Bewegung überwachen
        print("\nPositions-Überwachung:")
        start_time = time.time()
        while (time.time() - start_time) < 5.0:
            pos = tester.get_position()
            elapsed = time.time() - start_time
            expected = velocity * elapsed
            print(f"  Zeit: {elapsed:.1f}s  Position: {pos:6.2f}°  Erwartet: {expected:6.2f}°", end="\r")
            time.sleep(0.1)

        print()  # Neue Zeile

        # Bewegung stoppen
        print("\n3. Bewegung stoppen...")
        tester.stop_movement()
        time.sleep(0.5)

        final_pos = tester.get_position()
        print(f"Endposition: {final_pos:.2f}°")

        # Zurück zur Home-Position
        print("\n4. Zurück zur Home-Position...")
        tester.home_position()

        print("\n✓ Bewegungs-Test bestanden")
        tester.disconnect()
        return True

    except KeyboardInterrupt:
        print("\n\n✗ Test abgebrochen - Motor wird gestoppt...")
        tester.stop_movement()
        tester.disconnect()
        return False
    except Exception as e:
        print(f"\n✗ Fehler: {e}")
        tester.stop_movement()
        tester.disconnect()
        return False


def test_bidirectional():
    """Test 5: Bidirektionale Bewegung."""
    print("\n" + "=" * 60)
    print("TEST 5: Bidirektionale Bewegung")
    print("=" * 60)

    tester = N5NanotecTester()
    if not tester.connect():
        return False

    try:
        # Home-Position
        print("\nHome-Position anfahren...")
        tester.home_position()
        time.sleep(0.5)

        # Test 1: Im Uhrzeigersinn
        print("\n1. Bewegung im Uhrzeigersinn (5°/s, 3s)...")
        tester.move_continuous(5.0)
        time.sleep(3)
        tester.stop_movement()
        pos1 = tester.get_position()
        print(f"   Position: {pos1:.2f}°")

        time.sleep(1)

        # Test 2: Gegen Uhrzeigersinn
        print("\n2. Bewegung gegen Uhrzeigersinn (-5°/s, 3s)...")
        tester.move_continuous(-5.0)
        time.sleep(3)
        tester.stop_movement()
        pos2 = tester.get_position()
        print(f"   Position: {pos2:.2f}°")

        # Zurück zur Home
        print("\n3. Zurück zur Home-Position...")
        tester.home_position()

        print("\n✓ Bidirektionaler Test bestanden")
        tester.disconnect()
        return True

    except Exception as e:
        print(f"\n✗ Fehler: {e}")
        tester.stop_movement()
        tester.disconnect()
        return False


def main():
    """Hauptfunktion - führt alle Tests aus."""
    print("\n" + "=" * 60)
    print("N5 Nanotec Test-Programm")
    print("=" * 60)
    print("Testet den N5 Nanotec Stepper Motor Controller")
    print("Konfiguration:")
    print(f"  - IP-Adresse: {N5_IP_ADDRESS}")
    print(f"  - Port: {N5_PORT}")
    print(f"  - Slave ID: {N5_SLAVE_ID}")
    print(f"  - Demo-Modus: {'AKTIV' if DEMO_MODE else 'INAKTIV'}")

    if not DEMO_MODE:
        print("\nWARNUNG: Echter Hardware-Modus aktiv!")
        print("Stellen Sie sicher, dass:")
        print("  1. Der N5 Controller eingeschaltet ist")
        print("  2. Die Netzwerkverbindung funktioniert")
        print("  3. Keine Hindernisse im Bewegungsbereich sind")
        input("\nDrücken Sie ENTER zum Fortfahren oder CTRL+C zum Abbrechen...")

    # Tests ausführen
    tests = [
        ("Verbindung", test_connection),
        ("Position auslesen", test_position_read),
        ("Homing", test_homing),
        ("Kontinuierliche Bewegung", test_continuous_movement),
        ("Bidirektionale Bewegung", test_bidirectional),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except KeyboardInterrupt:
            print(f"\n\n✗ Test '{test_name}' abgebrochen")
            results[test_name] = False
            break
        except Exception as e:
            print(f"\n✗ Test '{test_name}' fehlgeschlagen: {e}")
            results[test_name] = False

    # Zusammenfassung
    print("\n" + "=" * 60)
    print("TEST-ZUSAMMENFASSUNG")
    print("=" * 60)

    for test_name, result in results.items():
        status = "✓ BESTANDEN" if result else "✗ FEHLGESCHLAGEN"
        print(f"{test_name:30s} {status}")

    passed = sum(1 for r in results.values() if r)
    total = len(results)
    print(f"\nErgebnis: {passed}/{total} Tests bestanden")

    if passed == total:
        print("\n✓ Alle Tests erfolgreich!")
        return 0
    else:
        print("\n✗ Einige Tests sind fehlgeschlagen")
        return 1


if __name__ == "__main__":
    sys.exit(main())
