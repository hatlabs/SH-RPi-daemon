import argparse
import asyncio
import grp
import os
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
        "--socket",
        "-s",
        type=pathlib.PosixPath,
        default=None,
        help="Path to the UNIX socket to listen on",
    )
    parser.add_argument(
        "--socket-group",
        "-g",
        type=str,
        default="adm",
        help="Group to set on the UNIX socket",
    )
    parser.add_argument(
        "-n", default=False, action="store_true", help="Dry run (no shutdown)"
    )
    parser.add_argument(
        "--poweroff",
        type=str,
        default="/sbin/poweroff",
        help="Command to call to power off the system",
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

    socket_path: pathlib.PosixPath
    if args.socket is None:
        # if we're root user, we should be able to write to /var/run/shrpi.sock
        if os.getuid() == 0:
            socket_path = pathlib.PosixPath("/var/run/shrpi.sock")
        else:
            socket_path = pathlib.PosixPath.home() / ".shrpi.sock"
    else:
        socket_path: pathlib.PosixPath = args.socket

    if socket_path.exists():
        # see if it's a socket
        if not socket_path.is_socket():
            logger.error(f"{socket_path} exists and is not a socket, exiting")
            sys.exit(1)
        elif (
            socket_path.stat().st_uid != 0
        ):  # it's a socket, but is it owned by anyone?
            logger.error(
                f"{socket_path} exists and is owned by UID {socket_path.stat().st_uid}, exiting"
            )
            sys.exit(1)
        else:
            # it's a socket and not in use, so delete it
            socket_path.unlink()

    socket_group = 0
    if args.socket_group is not None:
        try:
            socket_group = grp.getgrnam(args.socket_group).gr_gid
        except KeyError:
            logger.error(f"Group {args.socket_group} does not exist, exiting")
            sys.exit(1)
    else:
        # if no group is specified, use the current user's primary group
        socket_group = pathlib.PosixPath.home().stat().st_gid

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

    coro1 = run_state_machine(shrpi_device, blackout_time_limit, blackout_voltage_limit, poweroff=args.poweroff)
    coro2 = run_http_server(shrpi_device, socket_path, socket_group)
    coro3 = wait_forever()

    await asyncio.gather(coro1, coro2, coro3)


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
