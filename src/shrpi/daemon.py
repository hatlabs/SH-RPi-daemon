import argparse
import asyncio
import grp
import os
import pathlib
import signal
import sys

import yaml
from loguru import logger

from shrpi.const import (
    CONFIG_FILE_LOCATION,
    DEFAULT_BLACKOUT_TIME_LIMIT,
    DEFAULT_BLACKOUT_VOLTAGE_LIMIT,
    I2C_ADDR,
    I2C_BUS,
    VERSION,
)
from shrpi.i2c import SHRPiDevice, DeviceNotFoundError
from shrpi.server import run_http_server
from shrpi.state_machine import run_state_machine


def read_config_files(parser: argparse.ArgumentParser, paths: list[str]):
    """Read the config file."""

    for path in paths:
        try:
            with open(path, "r") as f:
                config = yaml.safe_load(f)
                parser.set_defaults(**config)
        except FileNotFoundError:
            logger.error(f"Config file not found: {path}")
            sys.exit(1)
        except yaml.YAMLError as e:
            logger.error(f"Error parsing config file: {e!s}")
            sys.exit(1)

    return config


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
    parser.add_argument("--conf", action="append", help="Configuration file location")

    args = parser.parse_args()

    if args.conf is not None:
        read_config_files(parser, args.conf)
    elif os.path.exists(CONFIG_FILE_LOCATION):
        read_config_files(parser, [CONFIG_FILE_LOCATION])

    # Reload arguments to override config file values with command line values
    args = parser.parse_args()

    return args


async def wait_forever():
    while True:
        await asyncio.sleep(1)


async def async_main():
    args = parse_arguments()

    i2c_bus = args.i2c_bus
    i2c_addr = args.i2c_addr

    try:
        shrpi_device = SHRPiDevice.factory(i2c_bus, i2c_addr)
    except DeviceNotFoundError as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

    hw_version = shrpi_device.hardware_version()
    fw_version = shrpi_device.firmware_version()
    logger.info(
        f"SH-RPi device detected; HW version {hw_version}, FW version {fw_version}"
    )


    blackout_time_limit = args.blackout_time_limit
    blackout_voltage_limit = args.blackout_voltage_limit

    socket_path: pathlib.PosixPath
    if args.socket is None:
        # if we're root user, we should be able to write to /var/run/shrpid.sock
        if os.getuid() == 0:
            socket_path = pathlib.PosixPath("/var/run/shrpid.sock")
        else:
            socket_path = pathlib.PosixPath.home() / ".shrpid.sock"
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
        logger.info("shrpid exiting")
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    logger.info(f"Starting shrpid version {VERSION} on {socket_path}")

    # run these with asyncio:

    coro1 = run_state_machine(
        shrpi_device,
        blackout_time_limit,
        blackout_voltage_limit,
        poweroff=args.poweroff,
    )
    coro2 = run_http_server(
        shrpi_device, socket_path, socket_group, poweroff=args.poweroff
    )
    coro3 = wait_forever()

    await asyncio.gather(coro1, coro2, coro3)


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
