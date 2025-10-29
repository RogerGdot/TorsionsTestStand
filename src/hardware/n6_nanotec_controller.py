"""
N6 Nanotec Stepper Motor Controller mit SSI Encoder
====================================================
Closed-Loop Position Control via NanoLib (Modbus TCP) mit SSI Drehwinkel-Sensor.

Hardware:
- N6 Nanotec Schrittmotor Controller
- SSI Absolutwert-Encoder für Positionsfeedback
- Modbus TCP Kommunikation über Ethernet
- Closed-Loop Betrieb

Der N6 liest die Position direkt vom SSI-Encoder und regelt die Position intern.
Die Software steuert den Motor über Velocity Mode und liest die Position via NanoLib.
"""

import time

try:
    from nanotec_nanolib import BusHardwareId, Nanolib, OdIndex

    NANOLIB_AVAILABLE = True
except ImportError:
    NANOLIB_AVAILABLE = False

from .motor_controller_base import MotorControllerBase


class N6NanotecController(MotorControllerBase):
    """
    N6 Nanotec Stepper Motor Controller via NanoLib (Modbus TCP).
    Closed-Loop Control mit SSI-Encoder für präzise Positionsmessung.
    """

    # Object Dictionary Indizes (CANopen Standard CiA 402)
    # Diese werden als OdIndex(index, subindex) verwendet
    OD_CONTROL_WORD = 0x6040  # Control Word (Steuerung: Enable, Start, Stop)
    OD_STATUS_WORD = 0x6041  # Status Word (Zustand: Ready, Enabled, Error)
    OD_MODE_OF_OPERATION = 0x6060  # Modes of Operation (z.B. 3 = Velocity Mode)
    OD_TARGET_VELOCITY = 0x60FF  # Target Velocity (Soll-Geschwindigkeit)
    OD_VELOCITY_ACTUAL = 0x606C  # Velocity Actual Value (Ist-Geschwindigkeit)
    OD_POSITION_ACTUAL = 0x6064  # Position Actual Value (Ist-Position vom SSI-Encoder)

    # Control Word Bit-Definitionen (CiA 402 State Machine)
    CTRL_SHUTDOWN = 0x0006  # Shutdown
    CTRL_SWITCH_ON = 0x0007  # Switch On
    CTRL_ENABLE_OPERATION = 0x000F  # Enable Operation (Motor bereit)
    CTRL_QUICK_STOP = 0x0002  # Quick Stop (Schnell-Stopp)
    CTRL_DISABLE_VOLTAGE = 0x0000  # Disable Voltage

    # Mode of Operation Values
    MODE_PROFILE_VELOCITY = 3  # Profile Velocity Mode (Geschwindigkeits-Modus)

    def __init__(
        self,
        ip_address: str = "192.168.0.100",
        port: int = 502,
        slave_id: int = 1,
        demo_mode: bool = True,
        encoder_resolution: int = 8192,  # SSI-Encoder Auflösung (z.B. 13-bit = 8192 counts/rev)
    ):
        """
        Initialisiert den N6 Nanotec Controller mit SSI-Encoder über NanoLib.

        Args:
            ip_address (str): IP-Adresse des N6 Controllers
            port (int): Modbus TCP Port (Standard: 502)
            slave_id (int): Modbus Slave ID (Standard: 1)
            demo_mode (bool): Demo-Modus für Simulation ohne Hardware
            encoder_resolution (int): SSI-Encoder Auflösung in Counts pro Umdrehung
        """
        super().__init__(demo_mode)
        self.ip_address = ip_address
        self.port = port
        self.slave_id = slave_id
        self.encoder_resolution = encoder_resolution

        # NanoLib Objekte
        self.nanolib = None
        self.accessor = None
        self.device_handle = None
        self.bus_hw_id = None

        # Umrechnungsfaktor: Encoder-Counts → Grad
        # Beispiel: 8192 counts = 360°  →  1 count = 360/8192 Grad
        self.counts_to_degrees = 360.0 / encoder_resolution

        # Demo-Mode Simulation
        self.demo_start_time = None
        self.demo_start_position = 0.0

    def connect(self) -> bool:
        """
        Verbindet mit dem N6 Controller über NanoLib und initialisiert den Motor.
        Aktiviert den Motor und setzt Velocity Mode.

        NanoLib Workflow:
        1. listAvailableBusHardware() - Verfügbare Bus-Hardware auflisten
        2. openBusHardwareWithProtocol() - Bus-Hardware mit Modbus TCP öffnen
        3. scanDevices() - Nach Geräten auf dem Bus suchen
        4. addDevice() - Gerät zur Device-Liste hinzufügen
        5. connectDevice() - Mit Gerät verbinden
        """
        if self.demo_mode:
            print("[DEMO] N6 Nanotec Controller - Simulation aktiv")
            self.is_connected = True
            self.current_position = 0.0
            return True

        if not NANOLIB_AVAILABLE:
            print("NanoLib nicht verfügbar - N6 Steuerung nicht möglich")
            print("Installation: pip install nanotec-nanolib")
            return False

        try:
            # 1. NanoLib initialisieren
            self.nanolib = Nanolib()
            self.accessor = self.nanolib.getNanoLibAccessor()

            print("NanoLib initialisiert")

            # 2. Verfügbare Bus-Hardware auflisten
            bus_hw_ids = self.accessor.listAvailableBusHardware()
            if not bus_hw_ids:
                print("Keine Bus-Hardware gefunden")
                return False

            # 3. Modbus TCP Bus-Hardware finden oder erste Hardware verwenden
            # BusHardwareId.IXXAT_CAN_ADAPTER für CAN-Bus
            # BusHardwareId.MODBUS_TCP_ADAPTER für Modbus TCP
            self.bus_hw_id = None
            for hw_id in bus_hw_ids:
                # NanoLib unterstützt Modbus TCP über generische Ethernet-Adapter
                # Wir öffnen die Hardware mit Modbus TCP Protokoll
                if hw_id.getBusHardware() == BusHardwareId.ETHERNET_ADAPTER:
                    self.bus_hw_id = hw_id
                    break

            if self.bus_hw_id is None:
                # Fallback: Erste verfügbare Hardware verwenden
                self.bus_hw_id = bus_hw_ids[0]

            print(f"Bus-Hardware ausgewählt: {self.bus_hw_id.getName()}")

            # 4. Bus-Hardware mit Modbus TCP öffnen
            # Protokoll: "modbus-tcp" mit IP:Port
            bus_hw_options = self.nanolib.createBusHardwareOptions(self.bus_hw_id)
            bus_hw_options.setOpenBusHardwareParameter(f"{self.ip_address}:{self.port}")

            result = self.accessor.openBusHardwareWithProtocol(self.bus_hw_id, "modbus-tcp", bus_hw_options)

            if result.hasError():
                print(f"Fehler beim Öffnen der Bus-Hardware: {result.getError()}")
                return False

            print(f"Bus-Hardware geöffnet: Modbus TCP {self.ip_address}:{self.port}")

            # 5. Nach Geräten scannen
            device_ids = self.accessor.scanDevices(self.bus_hw_id)
            if not device_ids:
                print("Keine Geräte auf dem Bus gefunden")
                self.accessor.closeBusHardware(self.bus_hw_id)
                return False

            print(f"{len(device_ids)} Gerät(e) gefunden")

            # 6. Erstes Gerät auswählen (oder nach Slave-ID filtern)
            device_id = None
            for dev_id in device_ids:
                # Optional: Nach Slave-ID filtern
                # if dev_id.getDeviceId() == self.slave_id:
                device_id = dev_id
                break

            if device_id is None:
                print(f"Gerät mit Slave-ID {self.slave_id} nicht gefunden")
                self.accessor.closeBusHardware(self.bus_hw_id)
                return False

            # 7. Gerät hinzufügen und verbinden
            self.device_handle = self.accessor.addDevice(device_id)
            result = self.accessor.connectDevice(self.device_handle)

            if result.hasError():
                print(f"Fehler beim Verbinden mit Gerät: {result.getError()}")
                self.accessor.closeBusHardware(self.bus_hw_id)
                return False

            print(f"N6 Nanotec verbunden: Device ID {device_id.getDeviceId()}")

            # 8. Motor initialisieren: State Machine durchlaufen
            # 1. Shutdown → 2. Switch On → 3. Enable Operation
            time.sleep(0.1)
            self._write_od(self.OD_CONTROL_WORD, self.CTRL_SHUTDOWN)
            time.sleep(0.1)
            self._write_od(self.OD_CONTROL_WORD, self.CTRL_SWITCH_ON)
            time.sleep(0.1)
            self._write_od(self.OD_CONTROL_WORD, self.CTRL_ENABLE_OPERATION)
            time.sleep(0.1)

            # 9. Velocity Mode aktivieren
            self._write_od(self.OD_MODE_OF_OPERATION, self.MODE_PROFILE_VELOCITY)
            time.sleep(0.1)

            self.is_connected = True
            print("N6 Nanotec initialisiert: Velocity Mode aktiv, Motor enabled")
            return True

        except Exception as e:
            print(f"N6 Nanotec Verbindungsfehler: {e}")
            if self.accessor and self.bus_hw_id:
                try:
                    self.accessor.closeBusHardware(self.bus_hw_id)
                except Exception:
                    pass
            return False

    def disconnect(self) -> None:
        """
        Trennt die Verbindung zum N6 Controller.
        Stoppt den Motor und deaktiviert ihn vor dem Trennen.
        """
        if self.demo_mode:
            self.is_connected = False
            return

        if self.accessor and self.is_connected:
            try:
                # Motor stoppen und deaktivieren
                self.stop_movement()
                time.sleep(0.1)
                self._write_od(self.OD_CONTROL_WORD, self.CTRL_DISABLE_VOLTAGE)
                time.sleep(0.1)

                # Gerät trennen
                if self.device_handle:
                    self.accessor.disconnectDevice(self.device_handle)
                    self.device_handle = None

                # Bus-Hardware schließen
                if self.bus_hw_id:
                    self.accessor.closeBusHardware(self.bus_hw_id)
                    self.bus_hw_id = None

                self.is_connected = False
                print("N6 Nanotec getrennt")
            except Exception as e:
                print(f"Fehler beim Trennen: {e}")
                self.is_connected = False

    def home_position(self) -> bool:
        """
        Setzt die aktuelle Position als Home-Position (0°).

        HINWEIS: Dies setzt nur die Software-Referenz auf 0°.
        Der SSI-Encoder behält seine absolute Position.
        Für echtes Homing müsste ein Referenzfahrt-Modus verwendet werden.
        """
        if not self.is_connected:
            print("N6 nicht verbunden")
            return False

        if self.demo_mode:
            print("[DEMO] N6 fährt in Home-Position (0°)")
            self.current_position = 0.0
            self.is_moving = False
            return True

        try:
            # Aktuelle Position auslesen und als Referenz speichern
            # Alternative: Homing-Modus aktivieren (OD 0x6098)
            current_pos = self.get_position()
            self.current_position = 0.0  # Software-Referenz auf 0 setzen

            print(f"N6: Home-Position gesetzt (Encoder-Position: {current_pos:.2f}°)")
            return True

        except Exception as e:
            print(f"N6 Homing-Fehler: {e}")
            return False

    def move_continuous(self, velocity: float) -> bool:
        """
        Startet kontinuierliche Bewegung mit konstanter Geschwindigkeit.
        Der Motor läuft kontinuierlich bis stop_movement() aufgerufen wird.

        Args:
            velocity (float): Geschwindigkeit in Grad/s
                             (+ = Uhrzeigersinn, - = Gegen Uhrzeigersinn)

        Returns:
            bool: True wenn erfolgreich gestartet
        """
        if not self.is_connected:
            print("N6 nicht verbunden")
            return False

        self.velocity = velocity
        self.is_moving = True

        if self.demo_mode:
            self.demo_start_time = time.time()
            self.demo_start_position = self.current_position
            print(f"[DEMO] N6 startet Bewegung mit {velocity:.2f}°/s")
            return True

        try:
            # Geschwindigkeit in Motor-Einheiten konvertieren
            # Typische Einheit für N6: rpm (Umdrehungen pro Minute)
            # velocity [°/s] → rpm = (velocity / 360) * 60
            velocity_rpm = (velocity / 360.0) * 60.0

            # N6 verwendet oft interne Einheiten (z.B. 0.1 rpm oder counts/s)
            # HINWEIS: Diese Umrechnung muss ggf. an die N6-Konfiguration angepasst werden!
            # Prüfen Sie die OD-Dokumentation für 0x60FF (Target Velocity)
            velocity_units = int(velocity_rpm)

            # Target Velocity setzen (OD 0x60FF)
            self._write_od(self.OD_TARGET_VELOCITY, velocity_units)
            time.sleep(0.05)

            # Motor starten: Control Word mit Enable Operation
            self._write_od(self.OD_CONTROL_WORD, self.CTRL_ENABLE_OPERATION)

            print(f"N6: Kontinuierliche Bewegung mit {velocity:.2f}°/s ({velocity_rpm:.2f} rpm) gestartet")
            return True

        except Exception as e:
            print(f"N6 Bewegungsfehler: {e}")
            self.is_moving = False
            return False

    def stop_movement(self) -> bool:
        """
        Stoppt die aktuelle Bewegung sofort via Quick Stop.
        """
        if not self.is_connected:
            return False

        self.is_moving = False
        self.velocity = 0.0

        if self.demo_mode:
            # Position beim Stoppen aktualisieren
            if self.demo_start_time is not None:
                elapsed_time = time.time() - self.demo_start_time
                self.current_position = self.demo_start_position + (self.velocity * elapsed_time)
            print(f"[DEMO] N6 gestoppt bei Position {self.current_position:.2f}°")
            return True

        try:
            # Geschwindigkeit auf 0 setzen
            self._write_od(self.OD_TARGET_VELOCITY, 0)
            time.sleep(0.05)

            # Quick Stop via Control Word
            self._write_od(self.OD_CONTROL_WORD, self.CTRL_QUICK_STOP)
            time.sleep(0.1)

            # Motor wieder aktivieren für nächste Bewegung
            self._write_od(self.OD_CONTROL_WORD, self.CTRL_ENABLE_OPERATION)

            print("N6: Bewegung gestoppt")
            return True

        except Exception as e:
            print(f"N6 Stop-Fehler: {e}")
            return False

    def get_position(self) -> float:
        """
        Liest die aktuelle Position vom SSI-Encoder via NanoLib.
        Der N6 liest den SSI-Encoder intern und stellt die Position
        über das Object Dictionary bereit.

        Returns:
            float: Aktuelle Position in Grad (0° - 360° oder darüber bei multi-turn)
        """
        if not self.is_connected:
            return 0.0

        if self.demo_mode:
            # Simuliere Bewegung basierend auf Geschwindigkeit und Zeit
            if self.is_moving and self.demo_start_time is not None:
                elapsed_time = time.time() - self.demo_start_time
                self.current_position = self.demo_start_position + (self.velocity * elapsed_time)
            return self.current_position

        try:
            # Position vom SSI-Encoder über Object Dictionary auslesen
            # OD 0x6064:0x00 - Position Actual Value
            position_counts = self._read_od(self.OD_POSITION_ACTUAL)

            # Umrechnung: Encoder-Counts → Grad
            # HINWEIS: Vorzeichen und Offset müssen ggf. angepasst werden!
            position_degrees = position_counts * self.counts_to_degrees

            self.current_position = position_degrees
            return position_degrees

        except Exception as e:
            print(f"N6 Positionsabfrage-Fehler: {e}")
            return self.current_position

    def is_motor_moving(self) -> bool:
        """
        Prüft, ob der Motor sich bewegt.
        Im echten Modus könnte dies über das Status Word oder Velocity Actual geprüft werden.
        """
        if self.demo_mode:
            return self.is_moving

        try:
            # Optional: Ist-Geschwindigkeit auslesen und prüfen ob > 0
            # velocity_actual = self._read_od(self.OD_VELOCITY_ACTUAL)
            # return abs(velocity_actual) > 0
            return self.is_moving
        except Exception:
            return False

    # --- Private Hilfsmethoden für NanoLib Object Dictionary Zugriff ---

    def _write_od(self, od_index: int, value: int, subindex: int = 0x00) -> bool:
        """
        Schreibt einen Wert in das Object Dictionary via NanoLib.

        Args:
            od_index (int): Object Dictionary Index (z.B. 0x6040)
            value (int): Zu schreibender Wert
            subindex (int): Sub-Index (Standard: 0x00)

        Returns:
            bool: True wenn erfolgreich
        """
        if not self.accessor or not self.device_handle:
            return False

        try:
            od = OdIndex(od_index, subindex)
            result = self.accessor.writeNumber(self.device_handle, od, value, 16)

            if result.hasError():
                print(f"NanoLib Write Error: OD 0x{od_index:04X}:{subindex:02X}, Value {value}")
                print(f"  Fehler: {result.getError()}")
                return False
            return True

        except Exception as e:
            print(f"Exception beim Schreiben von OD 0x{od_index:04X}: {e}")
            return False

    def _read_od(self, od_index: int, subindex: int = 0x00) -> int:
        """
        Liest einen Wert aus dem Object Dictionary via NanoLib.

        Args:
            od_index (int): Object Dictionary Index (z.B. 0x6064)
            subindex (int): Sub-Index (Standard: 0x00)

        Returns:
            int: Gelesener Wert (oder 0 bei Fehler)
        """
        if not self.accessor or not self.device_handle:
            return 0

        try:
            od = OdIndex(od_index, subindex)
            result = self.accessor.readNumber(self.device_handle, od)

            if result.hasError():
                print(f"NanoLib Read Error: OD 0x{od_index:04X}:{subindex:02X}")
                print(f"  Fehler: {result.getError()}")
                return 0

            return result.getResult()

        except Exception as e:
            print(f"Exception beim Lesen von OD 0x{od_index:04X}: {e}")
            return 0
