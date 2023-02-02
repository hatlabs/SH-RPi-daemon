from shrpi.i2c import SHRPiDevice


def main():
    dev = SHRPiDevice(1, 0x6D)

    hw_ver = dev.hardware_version()
    fw_ver = dev.firmware_version()

    print(f"Hardware version: {hw_ver}")
    print(f"Firmware version: {fw_ver}")

    en5v_state = dev.en5v_state()
    print("5V state: {}".format("on" if en5v_state else "off"))

    power_on_threshold = dev.power_on_threshold()
    power_off_threshold = dev.power_off_threshold()

    print(f"Power-on threshold voltage: {power_on_threshold}")
    print(f"Power-off threshold voltage: {power_off_threshold}")

    state = dev.state()

    print(f"Hat state: {state}")

    dcin_voltage = dev.dcin_voltage()

    print(f"DCIN voltage: {dcin_voltage}")

    supercap_voltage = dev.supercap_voltage()

    print(f"Supercap voltage: {supercap_voltage}")

    input_current = dev.input_current()

    print(f"Input current: {input_current}")

    temperature_K = dev.temperature()
    temperature_C = temperature_K - 273.15

    print(f"MCU temperature: {temperature_C}")


if __name__ == "__main__":
    main()
