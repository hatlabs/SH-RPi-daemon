import asyncio
import pathlib
from enum import Enum
from typing import Any, Dict

import typer
from aiohttp import ClientSession, UnixConnector

"""SH-RPi command line interface communicates with the shrpid daemon and
allows the user to observe and control the device."""

app = typer.Typer(
    name="shrpi",
    help=__doc__,
    add_completion=False,
)

# dictionary of state variables
state: Dict[str, Any] = {}


class Ansi(Enum):
    BLACK = 0
    RED = 1
    GREEN = 2
    YELLOW = 3
    BLUE = 4
    MAGENTA = 5
    CYAN = 6
    WHITE = 7
    DEFAULT = 9

    def __str__(self) -> str:
        return f"\x1b[3{self.value}m"


def print_colored(*text: str, color: Ansi = Ansi.WHITE):
    print(color, *text, "\x1b[0m")


async def get_json(session: ClientSession, url: str) -> Any:
    """Get JSON data from the given URL."""
    async with session.get(url) as resp:
        return await resp.json()


async def post_json(session: ClientSession, url: str, data: Dict[Any, Any]) -> int:
    """Post JSON data to the given URL."""
    async with session.post(url, json=data) as resp:
        return resp.status


async def put_json(session: ClientSession, url: str, data: Any) -> int:
    """Put JSON data to the given URL."""
    async with session.put(url, json=data) as resp:
        return resp.status


async def async_print_all(socket_path: pathlib.Path) -> None:
    """Print all data from the device."""
    connector = UnixConnector(path=str(socket_path))
    async with ClientSession(connector=connector) as session:
        coro1 = get_json(session, "http://localhost:8080/version")
        coro2 = get_json(session, "http://localhost:8080/state")
        coro3 = get_json(session, "http://localhost:8080/config")
        coro4 = get_json(session, "http://localhost:8080/values")
        version, state, config, values = await asyncio.gather(
            coro1, coro2, coro3, coro4
        )

        # Print all gathered data in a neat table

        table = []

        table.append(("Hardware version", str(version["hardware_version"]), ""))
        table.append(("Firmware version", str(version["firmware_version"]), ""))
        table.append(("Daemon version", str(version["daemon_version"]), ""))

        table.append(("State", str(state["state"]), ""))
        table.append(("5V output", str(state["5v_output_enabled"]), ""))
        table.append(("Watchdog enabled", str(state["watchdog_enabled"]), ""))

        table.append(("Watchdog timeout", f"{config['watchdog_timeout']:.1f}", "s"))
        table.append(("Power-on threshold", f"{config['power_on_threshold']:.1f}", "V"))
        table.append(
            ("Power-off threshold", f"{config['power_off_threshold']:.1f}", "V")
        )
        if config["led_brightness"] is not None:
            table.append(
                ("LED brightness", f"{100 * config['led_brightness'] / 255:.1f}", "%")
            )

        table.append(("Voltage in", f"{values['V_in']:.1f}", "V"))
        if values["I_in"] is not None:
            table.append(("Current in", f"{values['I_in']:.2f}", "A"))
        table.append(("Supercap voltage", f"{values['V_supercap']:.2f}", "V"))
        if values["T_mcu"] is not None:
            table.append(("MCU temperature", f"{values['T_mcu'] - 273.15:.1f}", "°C"))

        keys, values, _ = zip(*table)
        klen = max(*keys, key=len)
        vlen = max(*values, key=len)
        for key, val, unit in table:
            print(f"{key:<{klen}}  {val:>{vlen}}  {unit}")


@app.command("print")
def print_all() -> None:
    """Print all data from the device."""
    asyncio.run(async_print_all(state["socket"]))


async def async_shutdown(socket_path: pathlib.Path) -> None:
    """Tell the device to wait for shutdown."""
    connector = UnixConnector(path=str(socket_path))
    async with ClientSession(connector=connector) as session:
        response = await post_json(session, "http://localhost:8080/shutdown", {})
        if response != 204:
            print_colored(f"Error: Received HTTP status {response}", color=Ansi.RED)


@app.command("shutdown")
def shutdown() -> None:
    """Tell the device to shutdown."""
    asyncio.run(async_shutdown(state["socket"]))


async def async_sleep(socket_path: pathlib.Path, time: Dict[str, str]) -> None:
    """Tell the device to sleep."""

    connector = UnixConnector(path=str(socket_path))
    async with ClientSession(connector=connector) as session:
        response = await post_json(session, "http://localhost:8080/sleep", time)
        if response != 204:
            print_colored(f"Error: Received HTTP status {response}", color=Ansi.RED)


@app.command("sleep")
def sleep(
    time: str = typer.Argument(
        ...,
        help="Wakeup time, either as an absolute date and time, or a delay in seconds.",
    ),
) -> None:
    """Tell the device to sleep."""

    time_dict = {}
    # test if time is an integer
    try:
        int(time)
        time_dict = {"delay": time}
    except ValueError:
        # assume time is an absolute time
        time_dict = {"datetime": time}

    asyncio.run(async_sleep(state["socket"], time_dict))


set_app = typer.Typer(help="Set configuration values.")


async def async_set_watchdog(socket_path: pathlib.Path, timeout: float) -> None:
    """Set watchdog timeout in seconds. Value 0 disables the watchdog."""
    connector = UnixConnector(path=str(socket_path))
    async with ClientSession(connector=connector) as session:
        response = await put_json(
            session, "http://localhost:8080/config/watchdog_timeout", timeout
        )
        if response != 204:
            print_colored(f"Error: Received HTTP status {response}", color=Ansi.RED)


@set_app.command("watchdog")
def set_watchdog(timeout: float) -> None:
    """
    Set watchdog timeout in seconds. Value 0 disables the watchdog.
    """
    asyncio.run(async_set_watchdog(state["socket"], timeout))


async def async_set_power_on_threshold(
    socket_path: pathlib.Path, threshold: float
) -> None:
    """Set power-on threshold in volts."""
    connector = UnixConnector(path=str(socket_path))
    async with ClientSession(connector=connector) as session:
        response = await put_json(
            session, "http://localhost:8080/config/power_on_threshold", threshold
        )
        if response != 204:
            print_colored(f"Error: Received HTTP status {response}", color=Ansi.RED)


@set_app.command("power-on-threshold")
def set_power_on_threshold(threshold: float) -> None:
    """
    Set power-on threshold in volts.
    """
    asyncio.run(async_set_power_on_threshold(state["socket"], threshold))


async def async_set_power_off_threshold(
    socket_path: pathlib.Path, threshold: float
) -> None:
    """Set power-off threshold in volts."""
    connector = UnixConnector(path=str(socket_path))
    async with ClientSession(connector=connector) as session:
        response = await put_json(
            session, "http://localhost:8080/config/power_off_threshold", threshold
        )
        if response != 204:
            print_colored(f"Error: Received HTTP status {response}", color=Ansi.RED)


@set_app.command("power-off-threshold")
def set_power_off_threshold(threshold: float) -> None:
    """
    Set power-off threshold in volts.
    """
    asyncio.run(async_set_power_off_threshold(state["socket"], threshold))


async def async_set_led_brightness(
    socket_path: pathlib.Path, brightness: float
) -> None:
    """Set LED brightness in percent."""
    brightness_byte = int(brightness * 255 / 100)
    connector = UnixConnector(path=str(socket_path))
    async with ClientSession(connector=connector) as session:
        response = await put_json(
            session, "http://localhost:8080/config/led_brightness", brightness_byte
        )
        if response != 204:
            print_colored(f"Error: Received HTTP status {response}", color=Ansi.RED)


@set_app.command("led")
def set_led_brightness(brightness: float) -> None:
    """
    Set LED brightness in percent.
    """
    asyncio.run(async_set_led_brightness(state["socket"], brightness))


@app.callback()
def callback(
    socket: pathlib.Path = typer.Option(
        pathlib.Path("/var/run/shrpid.sock"), "--socket", "-s"
    ),
) -> None:
    """SH-RPi command line interface communicates with the shrpid daemon and
    allows the user to observe and control the device."""
    state["socket"] = socket


app.add_typer(set_app, name="set")


def main():
    app()


if __name__ == "__main__":
    main()
