import asyncio
import pathlib
import aiohttp
import typer
from rich.console import Console
from rich.table import Table

"""SH-RPi command line interface communicates with the shrpid daemon and
allows the user to observe and control the device."""

app = typer.Typer(
    name="shrpi",
    help=__doc__,
    add_completion=False,
)
console = Console()


async def get_json(session: aiohttp.ClientSession, url: str) -> dict:
    """Get JSON data from the given URL."""
    async with session.get(url) as resp:
        return await resp.json()


async def post_json(session: aiohttp.ClientSession, url: str, data: dict) -> None:
    """Post JSON data to the given URL."""
    async with session.post(url, json=data) as resp:
        return await resp.json()


async def async_print_all(socket_path: pathlib.Path):
    """Print all data from the device."""
    connector = aiohttp.UnixConnector(path=str(socket_path))
    async with aiohttp.ClientSession(connector=connector) as session:
        coro1 = get_json(session, "http://localhost:8080/version")
        coro2 = get_json(session, "http://localhost:8080/state")
        coro3 = get_json(session, "http://localhost:8080/config")
        coro4 = get_json(session, "http://localhost:8080/values")
        version, state, config, values = await asyncio.gather(coro1, coro2, coro3, coro4)

        # Print all gathered data in a neat table

        table = Table(show_header=False, box=None)
        table.add_column("Key", style="bold")
        table.add_column("Value", justify="right")
        table.add_column("Unit")

        table.add_row("Hardware version", str(version["hardware_version"]), "")
        table.add_row("Firmware version", str(version["firmware_version"]), "")
        table.add_row("Daemon version", str(version["daemon_version"]), "")
        table.add_section()

        table.add_row("State", str(state["state"]), "")
        table.add_row("5V output", str(state["5v_output_enabled"]), "")
        table.add_row("Watchdog enabled", str(state["watchdog_enabled"]), "")
        table.add_section()

        table.add_row("Watchdog timeout", f'{config["watchdog_timeout"]:.1f}', "s")
        table.add_row("Power-on threshold", f'{config["power_on_threshold"]:.1f}', "V")
        table.add_row("Power-off threshold", f'{config["power_off_threshold"]:.1f}', "V")
        table.add_section()

        table.add_row("Voltage in", f'{values["V_in"]:.1f}', "V")
        table.add_row("Current in", f'{values["I_in"]:.2f}', "A")
        table.add_row("Supercap voltage", f'{values["V_supercap"]:.2f}', "V")
        table.add_row("MCU temperature", f'{values["T_mcu"]-273.15:.1f}', "°C")

        console.print(table)


@app.command("print")
def print_all(socket: pathlib.Path = typer.Option(pathlib.Path("/var/run/shrpid.sock"), "--socket", "-s")):
    """Print all data from the device."""
    asyncio.run(async_print_all(socket))


def main():
    app()


if __name__ == "__main__":
    main()
