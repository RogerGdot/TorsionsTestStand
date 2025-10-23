"""
Test-Programm für NI-6000 DAQ
==============================
Testet die NI-6000 DAQ-Hardware isoliert.

Verwendung:
-----------
python test_ni6000.py

Funktionen:
- Verbindung zur DAQ testen
- Spannungen auslesen (±10V)
- Kontinuierliche Messung
- Nullpunkt-Kalibrierung

Hardware:
- NI-6000 DAQ
- DF-30 Drehmoment-Sensor (±20 Nm)
- Messverstärker (±10V)
"""

import sys
import time

# Verwende die Hardware-Module aus src/hardware

try:
    import nidaqmx
    from nidaqmx.constants import TerminalConfiguration

    NIDAQMX_AVAILABLE = True
except ImportError:
    NIDAQMX_AVAILABLE = False
    print("ERROR: NI DAQmx nicht verfügbar!")
    print("Installation: pip install nidaqmx")
    sys.exit(1)

# Konfiguration
DAQ_CHANNEL = "Dev1/ai0"  # DAQ-Kanal für Drehmomentmessung
VOLTAGE_RANGE = 10.0  # ±10V
TORQUE_SCALE = 2.0  # 20 Nm / 10 V = 2.0 Nm/V
SAMPLE_RATE = 10  # Hz
DURATION = 10  # Sekunden


def test_connection():
    """Testet die Verbindung zur DAQ."""
    print("\n" + "=" * 60)
    print("TEST 1: Verbindung zur NI-6000 DAQ")
    print("=" * 60)

    try:
        # System-Info abrufen
        system = nidaqmx.system.System.local()
        print(f"✓ NI DAQmx Driver Version: {system.driver_version}")

        # Geräte auflisten
        devices = system.devices
        if not devices:
            print("✗ Keine DAQ-Geräte gefunden!")
            return False

        print(f"\n✓ Gefundene Geräte ({len(devices)}):")
        for device in devices:
            print(f"  - {device.name}: {device.product_type}")
            print(f"    Analog Inputs: {len(device.ai_physical_chans)}")

        return True

    except Exception as e:
        print(f"✗ Fehler: {e}")
        return False


def test_single_read():
    """Testet eine einzelne Spannungsmessung."""
    print("\n" + "=" * 60)
    print("TEST 2: Einzelne Spannungsmessung")
    print("=" * 60)

    try:
        task = nidaqmx.Task()
        task.ai_channels.add_ai_voltage_chan(DAQ_CHANNEL, terminal_config=TerminalConfiguration.DEFAULT, min_val=-VOLTAGE_RANGE, max_val=VOLTAGE_RANGE)

        print(f"Kanal: {DAQ_CHANNEL}")
        print(f"Bereich: ±{VOLTAGE_RANGE}V")
        print("\nMesse...")

        voltage = task.read()
        torque = voltage * TORQUE_SCALE

        print(f"✓ Spannung: {voltage:.6f} V")
        print(f"✓ Drehmoment: {torque:.6f} Nm")

        task.close()
        return True

    except Exception as e:
        print(f"✗ Fehler: {e}")
        return False


def test_continuous_read():
    """Testet kontinuierliche Messung."""
    print("\n" + "=" * 60)
    print(f"TEST 3: Kontinuierliche Messung ({DURATION}s)")
    print("=" * 60)

    try:
        task = nidaqmx.Task()
        task.ai_channels.add_ai_voltage_chan(DAQ_CHANNEL, terminal_config=TerminalConfiguration.DEFAULT, min_val=-VOLTAGE_RANGE, max_val=VOLTAGE_RANGE)

        print(f"Kanal: {DAQ_CHANNEL}")
        print(f"Abtastrate: {SAMPLE_RATE} Hz")
        print(f"Dauer: {DURATION} Sekunden")
        print("\nDrücken Sie CTRL+C zum Abbrechen\n")

        start_time = time.time()
        sample_count = 0

        try:
            while (time.time() - start_time) < DURATION:
                voltage = task.read()
                torque = voltage * TORQUE_SCALE

                elapsed = time.time() - start_time
                print(f"[{elapsed:6.2f}s] V={voltage:+8.6f}V  T={torque:+8.6f}Nm", end="\r")

                sample_count += 1
                time.sleep(1.0 / SAMPLE_RATE)

        except KeyboardInterrupt:
            print("\n\n✓ Messung abgebrochen durch Benutzer")

        print(f"\n✓ {sample_count} Messungen durchgeführt")

        task.close()
        return True

    except Exception as e:
        print(f"✗ Fehler: {e}")
        return False


def test_calibration():
    """Testet die Nullpunkt-Kalibrierung."""
    print("\n" + "=" * 60)
    print("TEST 4: Nullpunkt-Kalibrierung")
    print("=" * 60)

    try:
        task = nidaqmx.Task()
        task.ai_channels.add_ai_voltage_chan(DAQ_CHANNEL, terminal_config=TerminalConfiguration.DEFAULT, min_val=-VOLTAGE_RANGE, max_val=VOLTAGE_RANGE)

        print("Messe Nullpunkt (10 Samples)...")

        # Mehrere Messungen für Mittelwert
        voltages = []
        for i in range(10):
            voltage = task.read()
            voltages.append(voltage)
            print(f"  Sample {i + 1}: {voltage:.6f} V")
            time.sleep(0.1)

        offset = sum(voltages) / len(voltages)
        print(f"\n✓ Nullpunkt-Offset: {offset:.6f} V")
        print(f"✓ Entspricht: {offset * TORQUE_SCALE:.6f} Nm")
        print("\nHinweis: Dieser Offset sollte beim Start abgezogen werden")

        task.close()
        return True

    except Exception as e:
        print(f"✗ Fehler: {e}")
        return False


def main():
    """Hauptfunktion - führt alle Tests aus."""
    print("\n" + "=" * 60)
    print("NI-6000 DAQ Test-Programm")
    print("=" * 60)
    print("Testet die NI-6000 DAQ-Hardware für Drehmomentmessung")
    print("Konfiguration:")
    print(f"  - Kanal: {DAQ_CHANNEL}")
    print(f"  - Spannungsbereich: ±{VOLTAGE_RANGE}V")
    print(f"  - Torque-Skalierung: {TORQUE_SCALE} Nm/V")

    # Tests ausführen
    tests = [
        ("Verbindung", test_connection),
        ("Einzelmessung", test_single_read),
        ("Kontinuierliche Messung", test_continuous_read),
        ("Kalibrierung", test_calibration),
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
