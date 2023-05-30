from collections.abc import Sequence
from enum import Enum

from smbus2 import SMBus

import shrpi.const


class States(Enum):
    BEGIN = 0
    WAIT_FOR_POWER_ON = 1
    ENTER_POWER_ON_5V_OFF = 2
    POWER_ON_5V_OFF = 3
    ENTER_POWER_ON_5V_ON = 4
    POWER_ON_5V_ON = 5
    ENTER_POWER_OFF_5V_ON = 6
    POWER_OFF_5V_ON = 7
    ENTER_SHUTDOWN = 8
    SHUTDOWN = 9
    ENTER_WATCHDOG_REBOOT = 10
    WATCHDOG_REBOOT = 11
    ENTER_OFF = 12
    OFF = 13
    ENTER_SLEEP_SHUTDOWN = 14
    SLEEP_SHUTDOWN = 15
    ENTER_SLEEP = 16
    SLEEP = 17


class DeviceNotFoundError(Exception):
    pass


class SHRPiDevice:
    def __init__(self, bus: int, addr: int):
        self.bus = bus
        self.addr = addr
        self._hardware_version = "Unknown"
        self._firmware_version = "Unknown"
        self.read_analog = self.read_analog_byte  # default to v1 protocol
        self.write_analog = self.write_analog_byte  # default to v1 protocol

        self.hardware_version()  # force hardware version detection
        self.firmware_version()  # force firmware version detection

        self.vcap_max = 0.0
        self.dcin_max = 0.0
        self.i_max = 0.0
        self.temp_max = 0.0

    @classmethod
    def factory(cls, bus: int, addr: int) -> "SHRPiDevice":
        temp_device = cls(bus, addr)
        hw_ver = temp_device.hardware_version()

        device: SHRPiDevice
        try:
            if hw_ver.startswith("1."):
                device = SHRPiV1Device(bus, addr)
            else:
                device = SHRPiV2Device(bus, addr)
            return device
        except OSError:
            raise DeviceNotFoundError("SH-RPi not found at I2C address %s" % addr)

    def i2c_query_byte(self, reg: int) -> int:
        with SMBus(self.bus) as bus:
            # bus.write_byte(self.addr, reg)
            b = bus.read_byte_data(self.addr, reg)
        return b

    def i2c_query_bytes(self, reg: int, n: int) -> Sequence[int]:
        with SMBus(self.bus) as bus:
            # bus.write_byte(self.addr, reg)
            b = bus.read_i2c_block_data(self.addr, reg, n)
        return b

    def i2c_query_word(self, reg: int) -> int:
        with SMBus(self.bus) as bus:
            # bus.write_byte(self.addr, reg)
            buf = bus.read_i2c_block_data(self.addr, reg, 2)
            w = buf[0] << 8 | buf[1]
        return w

    def i2c_write_byte(self, reg: int, val: int) -> None:
        with SMBus(self.bus) as bus:
            bus.write_byte_data(self.addr, reg, val)

    def i2c_write_word(self, reg: int, val: int) -> None:
        with SMBus(self.bus) as bus:
            buf = [(val >> 8), val & 0xFF]
            bus.write_i2c_block_data(self.addr, reg, buf)

    def i2c_write_bytes(self, reg: int, vals: Sequence[int]) -> None:
        with SMBus(self.bus) as bus:
            bus.write_i2c_block_data(self.addr, reg, vals)

    def _set_hardware_version(self, version: str) -> None:
        self._hardware_version = version

    def _set_firmware_version(self, version: str) -> None:
        self._firmware_version = version
        if version.startswith("2."):
            self.read_analog = self.read_analog_word
            self.write_analog = self.write_analog_word

    def read_analog_byte(self, reg: int, scale: float) -> float:
        return scale * self.i2c_query_byte(reg) / 256

    def write_analog_byte(self, reg: int, val: float, scale: float) -> None:
        self.i2c_write_byte(reg, int(256 * val / scale))

    def read_analog_word(self, reg: int, scale: float) -> float:
        return scale * self.i2c_query_word(reg) / 65536

    def write_analog_word(self, reg: int, val: float, scale: float) -> None:
        self.i2c_write_word(reg, int(65536 * val / scale))

    def hardware_version(self) -> str:
        if self._hardware_version != "Unknown":
            return self._hardware_version

        legacy_version = self.i2c_query_byte(0x01)
        if legacy_version != 0xFF:
            version_string = f"1.0.{legacy_version}"
        else:
            bytes = self.i2c_query_bytes(0x03, 4)
            version_string = f"{bytes[0]}.{bytes[1]}.{bytes[2]}"
            if bytes[3] != 0xFF:
                version_string += f"-{bytes[3]}"
        self._set_hardware_version(version_string)
        return version_string

    def firmware_version(self) -> str:
        if self._firmware_version != "Unknown":
            return self._firmware_version

        legacy_version = self.i2c_query_byte(0x02)
        if legacy_version != 0xFF:
            version_string = f"1.0.{legacy_version}"
        else:
            bytes = self.i2c_query_bytes(0x04, 4)
            version_string = f"{bytes[0]}.{bytes[1]}.{bytes[2]}"
            if bytes[3] != 0xFF:
                version_string += f"-{bytes[3]}"
        self._set_firmware_version(version_string)
        return version_string

    def en5v_state(self) -> bool:
        return bool(self.i2c_query_byte(0x10))

    def watchdog_timeout(self) -> float:
        """Get the watchdog timeout in seconds. 0 means the watchdog is disabled."""
        if self._firmware_version.startswith("2."):
            return self.i2c_query_word(0x12) / 1000
        else:
            return self.i2c_query_byte(0x12) / 10

    def set_watchdog_timeout(self, timeout: float) -> None:
        """Set the watchdog timeout in seconds. 0 disables the watchdog."""
        if self._firmware_version.startswith("2."):
            self.i2c_write_word(0x12, int(1000 * timeout))
        else:
            self.i2c_write_byte(0x12, int(10 * timeout))

    def power_on_threshold(self) -> float:
        return self.read_analog(0x13, self.vcap_max)

    def set_power_on_threshold(self, threshold: float) -> None:
        self.write_analog(0x13, threshold, self.vcap_max)

    def power_off_threshold(self) -> float:
        return self.read_analog(0x14, self.vcap_max)

    def set_power_off_threshold(self, threshold: float) -> None:
        self.write_analog(0x14, threshold, self.vcap_max)

    def state(self) -> str:
        return States(self.i2c_query_byte(0x15)).name

    def dcin_voltage(self) -> float:
        return self.read_analog(0x20, self.dcin_max)

    def supercap_voltage(self) -> float:
        return self.read_analog(0x21, self.vcap_max)

    def request_shutdown(self):
        self.i2c_write_byte(0x30, 0x01)

    def request_sleep(self):
        self.i2c_write_byte(0x31, 0x01)

    def watchdog_elapsed(self):
        return 0.1 * self.i2c_query_byte(0x16)

    def led_brightness(self):
        raise NotImplementedError("LED brightness not implemented in base class")

    def set_led_brightness(self, brightness: int) -> None:
        raise NotImplementedError("LED brightness not implemented in base class")

    def input_current(self):
        raise NotImplementedError("Input current not implemented in base class")

    def temperature(self):
        raise NotImplementedError("Temperature not implemented in base class")


class SHRPiV1Device(SHRPiDevice):
    """
    Device interface for SH-RPi v1 hardware.
    """

    def __init__(self, bus=1, addr=0x6D):
        super().__init__(bus, addr)
        self.vcap_max = 2.75
        self.dcin_max = 32.1

    def led_brightness(self):
        return None

    def set_led_brightness(self, brightness: int) -> None:
        raise NotImplementedError("LED brightness not supported in v1 firmware")

    def input_current(self):
        return None

    def temperature(self):
        return None


class SHRPiV2Device(SHRPiDevice):
    """
    Device interface for SH-RPi v2 hardware.
    """

    def __init__(self, bus=1, addr=0x6D):
        super().__init__(bus, addr)
        self.vcap_max = 9.35
        self.dcin_max = 32.1
        self.i_max = 2.5
        self.temp_max = 512.0  # in Kelvin

    def watchdog_timeout(self) -> float:
        return self.i2c_query_word(0x12) / 1000

    def set_watchdog_timeout(self, timeout: float) -> None:
        self.i2c_write_word(0x12, int(1000 * timeout))

    def led_brightness(self) -> int:
        return self.i2c_query_byte(0x17)

    def set_led_brightness(self, brightness: int) -> None:
        self.i2c_write_byte(0x17, brightness)

    def input_current(self) -> float:
        return self.read_analog(0x22, self.i_max)

    def temperature(self) -> float:
        return self.read_analog(0x23, self.temp_max)
