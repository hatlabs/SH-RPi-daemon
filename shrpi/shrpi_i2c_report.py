#!/usr/bin/env python3

from shrpi.shrpi_device import SHRPiDevice


def main():
    dev = SHRPiDevice(1, 0x6d)

    hw_ver = dev.hardware_version()
    fw_ver = dev.firmware_version()

    print("Hardware version: {}".format(hw_ver))
    print("Firmware version: {}".format(fw_ver))

    en5v_state = dev.en5v_state()
    print("5V state: {}".format("on" if en5v_state else "off"))

    power_on_threshold = dev.power_on_threshold()
    power_off_threshold = dev.power_off_threshold()

    print("Power-on threshold voltage: {}".format(power_on_threshold))
    print("Power-off threshold voltage: {}".format(power_off_threshold))

    state = dev.state()

    print("Hat state: {}".format(state))

    dcin_voltage = dev.dcin_voltage()
    
    print("DCIN voltage: {}".format(dcin_voltage))
    
    supercap_voltage = dev.supercap_voltage()

    print("Supercap voltage: {}".format(supercap_voltage))
    
    input_current = dev.input_current()

    print("Input current: {}".format(input_current))

    temperature_K = dev.temperature()
    temperature_C = temperature_K - 273.15

    print("MCU temperature: {}".format(temperature_C))

if __name__ == '__main__':
    main()
