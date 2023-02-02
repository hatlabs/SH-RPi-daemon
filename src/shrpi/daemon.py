import argparse
import signal
import sys
import time
from subprocess import check_call

from loguru import logger

from shrpi.const import (
    DEFAULT_BLACKOUT_TIME_LIMIT,
    DEFAULT_BLACKOUT_VOLTAGE_LIMIT,
    I2C_ADDR,
    I2C_BUS,
)
from shrpi.i2c import SHRPiDevice


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--i2c-bus", type=int, default=I2C_BUS, help="I2C bus number")
    parser.add_argument("--i2c-addr", type=int, default=I2C_ADDR, help="I2C address")
    parser.add_argument(
        "--blackout-time-limit",
        type=float,
        default=DEFAULT_BLACKOUT_TIME_LIMIT,
        help="The device will initiate shutdown after this many seconds of blackout",
    )
    parser.add_argument(
        "--blackout-voltage-limit",
        type=float,
        default=DEFAULT_BLACKOUT_VOLTAGE_LIMIT,
        help="The device will initiate shutdown if the input voltage drops below this value",
    )
    parser.add_argument(
        "-n", default=False, action="store_true", help="Dry run (no shutdown)"
    )

    return parser.parse_args()


def run_state_machine(
    logger, dev, blackout_time_limit, blackout_voltage_limit, dry_run=False
):
    state = "START"
    blackout_time = 0.0

    # Poll hardware and firmware versions. This will set SHRPiDevice in the
    # correct mode.
    hw_version = dev.hardware_version()
    fw_version = dev.firmware_version()

    logger.info(
        "SH-RPi device detected; HW version %s, FW version %s", hw_version, fw_version
    )

    while True:
        # TODO: Provide facilities for reporting the states and voltages
        # en5v_state = dev.en5v_state()
        # dev_state = dev.state()
        dcin_voltage = dev.dcin_voltage()
        # supercap_voltage = dev.supercap_voltage()

        if state == "START":
            dev.set_watchdog_timeout(10)
            if dcin_voltage < blackout_voltage_limit:
                logger.warn("Detected blackout on startup, ignoring")
            state = "OK"
        elif state == "OK":
            if dcin_voltage < blackout_voltage_limit:
                logger.warn("Detected blackout")
                blackout_time = time.time()
                state = "BLACKOUT"
        elif state == "BLACKOUT":
            if dcin_voltage > blackout_voltage_limit:
                logger.info("Power resumed")
                state = "OK"
            elif time.time() - blackout_time > blackout_time_limit:
                # didn't get power back in time
                logger.warn(f"Blacked out for {blackout_time_limit} s, shutting down")
                state = "SHUTDOWN"
        elif state == "SHUTDOWN":
            if dry_run:
                logger.warn("Would execute /sbin/poweroff")
            else:
                # inform the hat about this sad state of affairs
                dev.request_shutdown()
                check_call(["sudo", "/sbin/poweroff"])
            state = "DEAD"
        elif state == "DEAD":
            # just wait for the inevitable
            pass
        time.sleep(0.1)


def main():
    args = parse_arguments()

    i2c_bus = args.i2c_bus
    i2c_addr = args.i2c_addr

    # TODO: should test that the device is responding and has correct firmware

    dev = SHRPiDevice(i2c_bus, i2c_addr)

    blackout_time_limit = args.blackout_time_limit
    blackout_voltage_limit = args.blackout_voltage_limit

    def cleanup(signum, frame):
        logger.info("Disabling SH-RPi watchdog")
        dev.set_watchdog_timeout(0)
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    run_state_machine(logger, dev, blackout_time_limit, blackout_voltage_limit)


if __name__ == "__main__":
    main()
