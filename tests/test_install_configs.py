"""Exercise CAN removal with temporary config files and simulated I2C hardware."""

import os
import subprocess
from pathlib import Path

import pytest


@pytest.mark.parametrize("version", ["0x01", "0xff"])
@pytest.mark.parametrize("state", ["enabled", "disabled", "absent"])
def test_disable_can(tmp_path, version, state):
    """CAN removal succeeds repeatedly and leaves other interfaces alone."""
    overlay = (
        "mcp2515-can2,oscillator=16000000,interrupt=5,cs2=6"
        if version == "0x01"
        else "mcp2515-can0,oscillator=16000000,interrupt=23"
    )
    can_line = "dtoverlay=" + overlay
    unrelated = "dtoverlay=sc16is752-spi1,int_pin=24\ndtparam=spi=on\n"
    config = tmp_path / "config.txt"
    initial = unrelated
    if state != "absent":
        initial += ("#" if state == "disabled" else "") + can_line + "\n"
    config.write_text(initial)
    interface = tmp_path / "can0"
    interface.write_text("auto can0\n")

    source = (
        Path(__file__).resolve().parents[1] / "configs" / "install_configs.sh"
    ).read_text()
    marker = "# Everything else needs to be run as root"
    assert source.count(marker) == 1
    # Override only host paths and hardware/root detection, before main runs.
    # Keep argument parsing, CAN dispatch, config editing and removal unchanged.
    boundary = """
CONFIG="$TEST_DIR/config.txt"
CAN_INTERFACE_FILE="$TEST_DIR/can0"
OVERLAY_DIR="$TEST_DIR/no-overlays"
id() { echo 0; }
do_i2c() { :; }
detect_i2c_device() { return 0; }
i2cget() { echo "$TEST_VERSION"; }
"""
    source = source.replace(marker, boundary + "\n" + marker)
    env = dict(os.environ, TEST_DIR=str(tmp_path), TEST_VERSION=version)
    for attempt in range(2):
        result = subprocess.run(
            ["bash", "-s", "--", "--disable", "CAN"],
            input=source,
            text=True,
            capture_output=True,
            env=env,
            check=False,
            timeout=10,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "DONE." in result.stdout
        assert not interface.exists()
        contents = config.read_text()
        assert unrelated in contents
        assert can_line not in contents.splitlines()
        assert contents.count("#" + can_line) == (state != "absent")
        if attempt == 0:
            after_first = contents
        else:
            assert contents == after_first
