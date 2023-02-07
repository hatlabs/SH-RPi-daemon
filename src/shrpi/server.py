# Implement an aiohttp server to handle requests from the client.
# The server listens on a unix socket, and the client connects to it.

import asyncio
import pathlib

import arrow
from aiohttp import web

import shrpi.i2c


class RouteHandlers:
    def __init__(self, shrpi_device: shrpi.i2c.SHRPiDevice):
        self.shrpi_device = shrpi_device

    async def get_root(self, request: web.Request):
        return web.Response(text="This is shrpid!\n")

    async def get_version(self, request: web.Request):
        """Get the hardware and firmware version numbers."""
        hw_version = self.shrpi_device.hardware_version()
        fw_version = self.shrpi_device.firmware_version()
        daemon_version = "2.0.0-a2"

        response = {
            "hardware_version": hw_version,
            "firmware_version": fw_version,
            "daemon_version": daemon_version,
        }

        return web.json_response(response)

    async def get_state(self, request: web.Request):
        """Get the current state of the device."""
        state = self.shrpi_device.state()
        en5v_state = self.shrpi_device.en5v_state()
        watchdog_enabled = bool(self.shrpi_device.watchdog_timeout())

        response = {
            "state": state,
            "5v_output_enabled": en5v_state,
            "watchdog_enabled": watchdog_enabled,
        }

        return web.json_response(response)

    async def post_shutdown(self, request: web.Request):
        """Receive a shutdown request from the client."""
        self.shrpi_device.request_shutdown()  # Inform the device about the shutdown
        # call the system shutdown command
        asyncio.create_task(asyncio.create_subprocess_exec("shutdown", "-h", "now"))

        return web.Response(status=204)

    async def post_sleep(self, request: web.Request):
        """Receive a sleep request from the client."""
        now = arrow.utcnow()

        timestamp = 0

        data = await request.json()
        if "datetime" in data:
            try:
                datetime = arrow.get(data["datetime"])
            except arrow.parser.ParserError:
                return web.Response(status=400, text="Invalid datetime format")

            if datetime < now:
                return web.Response(status=400, text="datetime must be in the future")

            timestamp = int(datetime.timestamp())
        elif "delay" in data:
            try:
                delay = int(data["delay"])
            except ValueError:
                return web.Response(status=400, text="delay must be an integer")

            if delay < 0:
                return web.Response(status=400, text="delay must be positive")

            timestamp = int(now.timestamp()) + delay

        # Use rtcwake to set the RTC alarm to wake up the system
        asyncio.create_task(
            asyncio.create_subprocess_exec("rtcwake", "-m", "mem", "-t", str(timestamp))
        )

        self.shrpi_device.request_sleep()

        # From the OS point of view, this is a regular shutdown.
        asyncio.create_task(asyncio.create_subprocess_exec("shutdown", "-h", "now"))

        return web.Response(status=204)

    async def get_config(self, request: web.Request):
        """Get the configuration."""
        watchdog_timeout = self.shrpi_device.watchdog_timeout()
        power_on_threshold = self.shrpi_device.power_on_threshold()
        power_off_threshold = self.shrpi_device.power_off_threshold()

        config = {
            "watchdog_timeout": watchdog_timeout,
            "power_on_threshold": power_on_threshold,
            "power_off_threshold": power_off_threshold,
        }

        return web.json_response(config)

    async def get_config_key(self, request: web.Request):
        """Get a configuration value."""
        key = request.match_info["key"]

        if key == "watchdog_timeout":
            value = self.shrpi_device.watchdog_timeout()
        elif key == "power_on_threshold":
            value = self.shrpi_device.power_on_threshold()
        elif key == "power_off_threshold":
            value = self.shrpi_device.power_off_threshold()
        else:
            return web.Response(status=404)

        return web.json_response(value)

    async def put_config_key(self, request: web.Request):
        """Set a configuration value."""
        key = request.match_info["key"]

        data = await request.json()
        if key not in data:
            return web.Response(status=400, text=f"Missing {key} key in request body")

        value = data[key]

        if key == "watchdog_timeout":
            self.shrpi_device.set_watchdog_timeout(value)
        elif key == "power_on_threshold":
            self.shrpi_device.set_power_on_threshold(value)
        elif key == "power_off_threshold":
            self.shrpi_device.set_power_off_threshold(value)
        else:
            return web.Response(status=404)

        return web.Response(status=204)

    async def get_values(self, request: web.Request):
        """Get measured values."""
        dcin_voltage = self.shrpi_device.dcin_voltage()
        supercap_voltage = self.shrpi_device.supercap_voltage()
        input_current = self.shrpi_device.input_current()
        mcu_temperature = self.shrpi_device.temperature()

        values = {
            "V_in": dcin_voltage,
            "V_supercap": supercap_voltage,
            "I_in": input_current,
            "T_mcu": mcu_temperature,
        }

        return web.json_response(values)

    async def get_values_key(self, request: web.Request):
        """Get a measured value."""
        key = request.match_info["key"]

        if key == "V_in":
            value = self.shrpi_device.dcin_voltage()
        elif key == "V_supercap":
            value = self.shrpi_device.supercap_voltage()
        elif key == "I_in":
            value = self.shrpi_device.input_current()
        elif key == "T_mcu":
            value = self.shrpi_device.temperature()
        else:
            return web.Response(status=404)

        return web.json_response(value)


async def run_http_server(
    shrpi_device: shrpi.i2c.SHRPiDevice, socket_path: pathlib.Path
):
    """Run the HTTP server."""

    handlers = RouteHandlers(shrpi_device)

    app = web.Application()
    app.add_routes(
        [
            web.get("/", handlers.get_root),
            web.get("/version", handlers.get_version),
            web.get("/state", handlers.get_state),
            web.post("/shutdown", handlers.post_shutdown),
            web.post("/sleep", handlers.post_sleep),
            web.get("/config", handlers.get_config),
            web.get("/config/{key}", handlers.get_config_key),
            web.put("/config/{key}", handlers.put_config_key),
            web.get("/values", handlers.get_values),
            web.get("/values/{key}", handlers.get_values_key),
        ]
    )

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.UnixSite(runner, str(socket_path))
    await site.start()

    return runner
