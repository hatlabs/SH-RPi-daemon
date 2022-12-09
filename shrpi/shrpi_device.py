from enum import Enum

from smbus2 import SMBus

VCAP_MAX = 9.35
DCIN_MAX = 32.1
I_MAX = 2.5
TEMP_MAX = 512.

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
        self.hardware_version = None
        self.firmware_version = None
        self.read_analog = self.read_analog_byte  # default to v1 protocol

    def i2c_query_byte(self, reg):
        with SMBus(self.bus) as bus:
            bus.write_byte(self.addr, reg)
            b = bus.read_byte(self.addr)
        return b

    def i2c_query_bytes(self, reg, n):
        with SMBus(self.bus) as bus:
            bus.write_byte(self.addr, reg)
            b = bus.read_i2c_block_data(self.addr, 0, n)
        return b

    def i2c_query_word(self, reg):
        with SMBus(self.bus) as bus:
            bus.write_byte(self.addr, reg)
            w = bus.read_word_data(self.addr, 0)
        return w

    def i2c_write_byte(self, reg, val):
        with SMBus(self.bus) as bus:
            bus.write_byte_data(self.addr, reg, val)

    def set_hardware_version(self, version):
        self.hardware_version = version

    def set_firmware_version(self, version):
        self.firmware_version = version
        if version.startswith("2."):
            self.read_analog = self.read_analog_word

    def read_analog_byte(self, reg, scale):
        return scale*self.i2c_query_byte(reg)/256

    def read_analog_word(self, reg, scale):
        return scale*self.i2c_query_word(reg)/65536

    def hardware_version(self):
        legacy_version = self.i2c_query_byte(0x01)
        if legacy_version != 0xff:
            version_string = f"1.0.{legacy_version}"
        else:
            bytes = self.i2c_query_bytes(0x03, 4)
            version_string = f"{bytes[0]}.{bytes[1]}.{bytes[2]}"
            if bytes[3] != 0xff:
                version_string += f"-{bytes[3]}"
        self.set_hardware_version(version_string)
        return version_string

    def firmware_version(self):
        legacy_version = self.i2c_query_byte(0x02)
        if legacy_version != 0xff:
            version_string = f"1.0.{legacy_version}"
        else:
            bytes = self.i2c_query_bytes(0x04, 4)
            version_string = f"{bytes[0]}.{bytes[1]}.{bytes[2]}"
            if bytes[3] != 0xff:
                version_string += f"-{bytes[3]}"
        self.set_firmware_version(version_string)
        return version_string

    def en5v_state(self):
        return self.i2c_query_byte(0x10)

    def set_watchdog_timeout(self, timeout):
        self.i2c_write_byte(0x12, int(10*timeout))

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
        if self.firmware_version.startswith("2."):
            return self.read_analog(0x22, I_MAX)
        else:
            # input current measurement not supported in v1 hardware
            return None

    def temperature(self):
        if self.firmware_version.startswith("2."):
            return self.read_analog(0x23, TEMP_MAX)
        else:
            # temperature measurement not supported in v1 firmware
            return None

    def request_shutdown(self):
        self.i2c_write_byte(0x30, 0x01)

    def request__sleep(self):
        self.i2c_write_byte(0x31, 0x01)

    def watchdog_elapsed(self):
        return 0.1 * self.i2c_query_byte(0x16)
    

