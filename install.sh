#!/usr/bin/env bash

# This installation script is intended for installing shrpid on
# a new Raspberry Pi computer with a one-line copy-paste command.
#
# The script needs root privileges to work properly.

set -euo pipefail
shopt -s inherit_errexit

# Bail out if not running as root
if [ "$(id -u)" != "0" ]; then
    echo "This script must be run as root" 1>&2
    exit 1
fi

# install the device tree overlay and other configuration files

pushd configs
./install_configs.sh "$@"
popd

# install uv, which manages venv for installing the daemon
if ! [[ $(type -P "$cmd") ]]; then
    curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="/usr/local/bin" sh
fi

# If a legacy venv is present, remove it
if [ -d /usr/local/lib/shrpid ]; then
    rm -rf /usr/local/lib/shrpid
fi

# If existing binaries are present, remove them
if [ -f /usr/local/bin/shrpid ]; then
    rm /usr/local/bin/shrpid
fi
if [ -f /usr/local/bin/shrpi ]; then
    rm /usr/local/bin/shrpi
fi

# install the daemon itself
UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_TOOL_BIN_DIR=/usr/local/bin UV_TOOL_DIR=/opt/uv uv tool install --force .

# copy the service definition file in place
install -o root shrpid.service /lib/systemd/system
systemctl daemon-reload
systemctl enable shrpid

echo "Installation complete. Please reboot the system."
