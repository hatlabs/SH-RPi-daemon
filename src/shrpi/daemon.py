import argparse
import asyncio
import pathlib
import signal
import sys

from loguru import logger

from shrpi.const import (
    DEFAULT_BLACKOUT_TIME_LIMIT,
    DEFAULT_BLACKOUT_VOLTAGE_LIMIT,
    I2C_ADDR,
    I2C_BUS,
)
from shrpi.i2c import SHRPiDevice
from shrpi.server import run_http_server
from shrpi.state_machine import run_state_machine


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
        "--socket", "-s",
        type=pathlib.Path,
        default=pathlib.Path("./shrpid.sock"),
        help="Path to the UNIX socket to listen on",
    )
    parser.add_argument(
        "-n", default=False, action="store_true", help="Dry run (no shutdown)"
    )

    return parser.parse_args()


async def wait_forever():
    while True:
        await asyncio.sleep(1)


async def async_main():
    args = parse_arguments()

    i2c_bus = args.i2c_bus
    i2c_addr = args.i2c_addr

    # TODO: should test that the device is responding and has correct firmware

    shrpi_device = SHRPiDevice(i2c_bus, i2c_addr)

    blackout_time_limit = args.blackout_time_limit
    blackout_voltage_limit = args.blackout_voltage_limit
    socket_path = args.socket

    if socket_path.exists():
        logger.error(f"Socket {socket_path} already exists, exiting")
        sys.exit(1)

    def cleanup(signum, frame):
        logger.info("Disabling SH-RPi watchdog")
        shrpi_device.set_watchdog_timeout(0)
        # delete the socket file
        if socket_path.exists():
            socket_path.unlink()
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    # run these with asyncio:

    coro1 = run_state_machine(shrpi_device, blackout_time_limit, blackout_voltage_limit)
    coro2 = run_http_server(shrpi_device, socket_path)
    coro3 = wait_forever()

    await asyncio.gather(coro1, coro2, coro3)


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
