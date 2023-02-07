from enum import Enum

from smbus2 import SMBus

from shrpi.const import DCIN_MAX, I_MAX, TEMP_MAX, VCAP_MAX


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


class SHRPiDevice:
    def __init__(self, bus, addr):
        self.bus = bus
        self.addr = addr
        self._hardware_version = "Unknown"
        self._firmware_version = "Unknown"
        self.read_analog = self.read_analog_byte  # default to v1 protocol

    def i2c_query_byte(self, reg):
        with SMBus(self.bus) as bus:
            # bus.write_byte(self.addr, reg)
            b = bus.read_byte_data(self.addr, reg)
        return b

    def i2c_query_bytes(self, reg, n):
        with SMBus(self.bus) as bus:
            # bus.write_byte(self.addr, reg)
            b = bus.read_i2c_block_data(self.addr, reg, n)
        return b

    def i2c_query_word(self, reg):
        with SMBus(self.bus) as bus:
            # bus.write_byte(self.addr, reg)
            buf = bus.read_i2c_block_data(self.addr, reg, 2)
            w = buf[0] << 8 | buf[1]
        return w

    def i2c_write_byte(self, reg, val):
        with SMBus(self.bus) as bus:
            bus.write_byte_data(self.addr, reg, val)

    def i2c_write_word(self, reg, val):
        with SMBus(self.bus) as bus:
            buf = [(val >> 8), val & 0xFF]
            bus.write_i2c_block_data(self.addr, reg, buf)

    def i2c_write_bytes(self, reg, vals):
        with SMBus(self.bus) as bus:
            bus.write_i2c_block_data(self.addr, reg, vals)

    def _set_hardware_version(self, version):
        self._hardware_version = version

    def _set_firmware_version(self, version):
        self._firmware_version = version
        if version.startswith("2."):
            self.read_analog = self.read_analog_word

    def read_analog_byte(self, reg, scale):
        return scale * self.i2c_query_byte(reg) / 256

    def read_analog_word(self, reg, scale):
        return scale * self.i2c_query_word(reg) / 65536

    def hardware_version(self):
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

    def firmware_version(self):
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

    def en5v_state(self):
        return bool(self.i2c_query_byte(0x10))

    def watchdog_timeout(self):
        """Get the watchdog timeout in seconds. 0 means the watchdog is disabled."""
        if self._firmware_version.startswith("2."):
            return self.i2c_query_word(0x12) / 1000
        else:
            return self.i2c_query_byte(0x12) / 10

    def set_watchdog_timeout(self, timeout):
        """Set the watchdog timeout in seconds. 0 disables the watchdog."""
        if self._firmware_version.startswith("2."):
            self.i2c_write_word(0x12, int(1000 * timeout))
        else:
            self.i2c_write_byte(0x12, int(10 * timeout))

    def power_on_threshold(self):
        return self.read_analog(0x13, VCAP_MAX)

    def power_off_threshold(self):
        return self.read_analog(0x14, VCAP_MAX)

    def state(self):
        return States(self.i2c_query_byte(0x15)).name

    def dcin_voltage(self):
        return self.read_analog(0x20, DCIN_MAX)

    def supercap_voltage(self):
        return self.read_analog(0x21, VCAP_MAX)

    def input_current(self):
        if self._firmware_version.startswith("2."):
            return self.read_analog(0x22, I_MAX)
        else:
            # input current measurement not supported in v1 hardware
            return None

    def temperature(self):
        if self._firmware_version.startswith("2."):
            return self.read_analog(0x23, TEMP_MAX)
        else:
            # temperature measurement not supported in v1 firmware
            return None

    def request_shutdown(self):
        self.i2c_write_byte(0x30, 0x01)

    def request_sleep(self):
        self.i2c_write_byte(0x31, 0x01)

    def watchdog_elapsed(self):
        return 0.1 * self.i2c_query_byte(0x16)
