from enum import Enum

from smbus2 import SMBus

RATIO_COEFF = 2.8 / 256
DCIN_MAX = 32.0
VCAP_MAX = 2.8

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


class SailorHatDevice:
    def __init__(self, bus, addr):
        self.bus = bus
        self.addr = addr

    def i2c_query_byte(self, reg):
        with SMBus(self.bus) as bus:
            bus.write_byte(self.addr, reg)
            b = bus.read_byte(self.addr)
        return b

    def i2c_write_byte(self, reg, val):
        with SMBus(self.bus) as bus:
            bus.write_byte_data(self.addr, reg, val)

    def hardware_version(self):
        return self.i2c_query_byte(0x01)

    def firmware_version(self):
        return self.i2c_query_byte(0x02)

    def en5v_state(self):
        return self.i2c_query_byte(0x10)

    def power_on_threshold(self):
        return RATIO_COEFF * self.i2c_query_byte(0x13)

    def power_off_threshold(self):
        return RATIO_COEFF * self.i2c_query_byte(0x14)

    def state(self):
        return States(self.i2c_query_byte(0x15)).name

    def dcin_voltage(self):
        return DCIN_MAX*self.i2c_query_byte(0x20)/256

    def supercap_voltage(self):
        return VCAP_MAX*self.i2c_query_byte(0x21)/256

    def request_shutdown(self):
        self.i2c_write_byte(0x30, 0x01)

    def set_watchdog_timeout(self, timeout):
        self.i2c_write_byte(0x12, int(10*timeout))

    def watchdog_elapsed(self):
        return 0.1 * self.i2c_query_byte(0x16)
    

