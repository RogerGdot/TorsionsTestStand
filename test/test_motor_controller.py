"""
Test-Programm für Motor-Controller
===================================
Testet Nanotec und Trinamic Motor-Controller isoliert.

Verwendung:
-----------
python test_motor_controller.py

Hardware:
- Nanotec Stepper Motor mit NanoLib
- Trinamic Steprocker mit PyTrinamic
"""

import sys
import time

from src.hardware import NanotecMotorController, TrinamicMotorController

# Konfiguration - HIER Motor-Typ wählen!
MOTOR_TYPE = "nanotec"  # "nanotec" oder "trinamic"
DEMO_MODE = True  # True = Demo-Modus, False = Echte Hardware

# Nanotec Konfiguration
NANOTEC_BUS_HARDWARE = "ixxat"

# Trinamic Konfiguration
TRINAMIC_COM_PORT = "COM3"
TRINAMIC_MOTOR_ID = 0


def test_connection(controller, motor_name):
    """Testet die Verbindung zum Motor-Controller."""
    print("\n" + "=" * 60)
    print(f"TEST 1: Verbindung zum {motor_name}")
    print("=" * 60)

    try:
        if controller.connect():
            print(f"✓ {motor_name} erfolgreich verbunden")
            print(f"  Demo-Modus: {controller.demo_mode}")
            return True
        else:
            print(f"✗ {motor_name} Verbindung fehlgeschlagen")
            return False
    except Exception as e:
        print(f"✗ Fehler beim Verbinden: {e}")
        return False


def test_home_position(controller, motor_name):
    """Testet die Home-Position Funktion."""
    print("\n" + "=" * 60)
    print(f"TEST 2: Home-Position für {motor_name}")
    print("=" * 60)

    try:
        print("Fahre in Home-Position (0°)...")
        if controller.home_position():
            print("✓ Home-Position erfolgreich angefahren")
            time.sleep(1)
            position = controller.get_position()
            print(f"  Aktuelle Position: {position:.2f}°")
            return True
        else:
            print("✗ Home-Position Fehler")
            return False
    except Exception as e:
        print(f"✗ Fehler: {e}")
        return False


def test_continuous_movement(controller, motor_name):
    """Testet kontinuierliche Bewegung."""
    print("\n" + "=" * 60)
    print(f"TEST 3: Kontinuierliche Bewegung für {motor_name}")
    print("=" * 60)

    try:
        velocity = 10.0  # 10°/s
        duration = 5  # 5 Sekunden

        print(f"Starte Bewegung mit {velocity}°/s für {duration} Sekunden...")
        if controller.move_continuous(velocity):
            print("✓ Bewegung gestartet")

            # Beobachte Position während der Bewegung
            for i in range(duration):
                time.sleep(1)
                position = controller.get_position()
                is_moving = controller.is_motor_moving()
                print(f"  t={i + 1}s: Position = {position:.2f}°, Moving = {is_moving}")

            # Stoppe Bewegung
            print("\nStoppe Bewegung...")
            if controller.stop_movement():
                print("✓ Bewegung gestoppt")
                final_position = controller.get_position()
                print(f"  Endposition: {final_position:.2f}°")
                return True
            else:
                print("✗ Stop-Befehl fehlgeschlagen")
                return False
        else:
            print("✗ Bewegung konnte nicht gestartet werden")
            return False
    except Exception as e:
        print(f"✗ Fehler: {e}")
        return False


def test_bidirectional_movement(controller, motor_name):
    """Testet bidirektionale Bewegung."""
    print("\n" + "=" * 60)
    print(f"TEST 4: Bidirektionale Bewegung für {motor_name}")
    print("=" * 60)

    try:
        # Uhrzeigersinn
        print("\n1) Bewegung im Uhrzeigersinn (+10°/s)...")
        controller.move_continuous(10.0)
        time.sleep(2)
        pos1 = controller.get_position()
        controller.stop_movement()
        print(f"   Position nach 2s: {pos1:.2f}°")

        time.sleep(1)

        # Gegen Uhrzeigersinn
        print("\n2) Bewegung gegen Uhrzeigersinn (-10°/s)...")
        controller.move_continuous(-10.0)
        time.sleep(2)
        pos2 = controller.get_position()
        controller.stop_movement()
        print(f"   Position nach 2s: {pos2:.2f}°")

        print("\n✓ Bidirektionale Bewegung erfolgreich getestet")
        return True

    except Exception as e:
        print(f"✗ Fehler: {e}")
        return False


def main():
    """Hauptfunktion zum Ausführen aller Tests."""
    print("\n" + "=" * 60)
    print("MOTOR-CONTROLLER TEST")
    print("=" * 60)
    print(f"Motor-Typ: {MOTOR_TYPE.upper()}")
    print(f"Demo-Modus: {DEMO_MODE}")

    # Motor-Controller erstellen
    if MOTOR_TYPE.lower() == "nanotec":
        controller = NanotecMotorController(bus_hardware=NANOTEC_BUS_HARDWARE, demo_mode=DEMO_MODE)
        motor_name = "Nanotec Motor"
    elif MOTOR_TYPE.lower() == "trinamic":
        controller = TrinamicMotorController(port=TRINAMIC_COM_PORT, motor_id=TRINAMIC_MOTOR_ID, demo_mode=DEMO_MODE)
        motor_name = "Trinamic Steprocker"
    else:
        print(f"\n✗ ERROR: Unbekannter Motor-Typ '{MOTOR_TYPE}'")
        print("Bitte 'nanotec' oder 'trinamic' wählen!")
        sys.exit(1)

    # Tests ausführen
    results = []

    # Test 1: Verbindung
    results.append(("Verbindung", test_connection(controller, motor_name)))

    if results[0][1]:  # Nur weitermachen wenn Verbindung erfolgreich
        # Test 2: Home-Position
        results.append(("Home-Position", test_home_position(controller, motor_name)))

        # Test 3: Kontinuierliche Bewegung
        results.append(("Kontinuierliche Bewegung", test_continuous_movement(controller, motor_name)))

        # Test 4: Bidirektionale Bewegung
        results.append(("Bidirektionale Bewegung", test_bidirectional_movement(controller, motor_name)))

        # Trennen
        print("\n" + "=" * 60)
        print("Trenne Verbindung...")
        controller.disconnect()
        print("✓ Verbindung getrennt")

    # Zusammenfassung
    print("\n" + "=" * 60)
    print("TEST-ZUSAMMENFASSUNG")
    print("=" * 60)
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:30s}: {status}")

    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nErgebnis: {passed}/{total} Tests bestanden")

    if passed == total:
        print("\n🎉 Alle Tests erfolgreich!")
        return 0
    else:
        print("\n⚠️  Einige Tests fehlgeschlagen")
        return 1


if __name__ == "__main__":
    sys.exit(main())
