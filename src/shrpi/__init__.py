# type: ignore[attr-defined]
"""`shrpid` is a power monitor and watchdog for the SH-RPi. It communicates with the SH-RPi device, providing the "smart" aspects of the operation."""

import sys

if sys.version_info >= (3, 8):
    from importlib import metadata as importlib_metadata
else:
    import importlib_metadata


def get_version() -> str:
    try:
        return importlib_metadata.version(__name__)
    except importlib_metadata.PackageNotFoundError:  # pragma: no cover
        return "unknown"


version: str = get_version()
