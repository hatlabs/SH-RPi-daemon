import asyncio
import time
from subprocess import check_call

from loguru import logger

from shrpi.i2c import SHRPiDevice


async def run_state_machine(
    shrpi_device: SHRPiDevice,
    blackout_time_limit: float,
    blackout_voltage_limit: float,
    dry_run=False,
    poweroff="/sbin/poweroff",
):
    state = "START"
    blackout_time = 0.0

    # Poll hardware and firmware versions. This will set SHRPiDevice in the
    # correct mode.
    hw_version = shrpi_device.hardware_version()
    fw_version = shrpi_device.firmware_version()

    logger.info(
        f"SH-RPi device detected; HW version {hw_version}, FW version {fw_version}"
    )

    while True:
        # TODO: Provide facilities for reporting the states and voltages
        # en5v_state = dev.en5v_state()
        # dev_state = dev.state()
        dcin_voltage = shrpi_device.dcin_voltage()
        # supercap_voltage = dev.supercap_voltage()

        if state == "START":
            shrpi_device.set_watchdog_timeout(10)
            state = "OK"
        elif state == "OK":
            if dcin_voltage < blackout_voltage_limit:
                logger.warning("Detected blackout")
                blackout_time = time.time()
                state = "BLACKOUT"
        elif state == "BLACKOUT":
            if dcin_voltage > blackout_voltage_limit:
                logger.info("Power resumed")
                state = "OK"
            elif time.time() - blackout_time > blackout_time_limit:
                # didn't get power back in time
                logger.warning(
                    f"Blacked out for {blackout_time_limit} s, shutting down"
                )
                state = "SHUTDOWN"
        elif state == "SHUTDOWN":
            if dry_run:
                logger.warning(f"Would execute {poweroff}")
            else:
                # inform the hat about this sad state of affairs
                shrpi_device.request_shutdown()
                logger.info(f"Executing {poweroff}")
                check_call(["sudo", poweroff])
            state = "DEAD"
        elif state == "DEAD":
            # just wait for the inevitable
            pass
        await asyncio.sleep(0.1)
