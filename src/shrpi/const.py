# Config file for SH-RPi daemon
CONFIG_FILE_LOCATION = "/etc/shrpid.conf"

# Default I2C bus for Raspberry Pi
I2C_BUS = 1

# Default I2C address for SH-RPi
I2C_ADDR = 0x6D

# After this many seconds of blackout, the daemon will shut down the Pi
DEFAULT_BLACKOUT_TIME_LIMIT = 3.0

# This is the input voltage limit that counts as a blackout
DEFAULT_BLACKOUT_VOLTAGE_LIMIT = 9.0

# Daemon version

VERSION = "2.2.3"
