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

# install the daemon build dependencies

apt install -y python3-pip python3-venv


# If an existing venv is present, remove it
if [ -d /usr/local/lib/shrpid ]; then
    rm -rf /usr/local/lib/shrpid
fi

# Create a venv for the daemon
python3 -m venv /usr/local/lib/shrpid
source /usr/local/lib/shrpid/bin/activate

# install the daemon itself

pip3 install .

# Create symlinks to the daemon and the CLI utility
ln -sf /usr/local/lib/shrpid/bin/shrpid /usr/local/bin/shrpid
ln -sf /usr/local/lib/shrpid/bin/shrpi /usr/local/bin/shrpi

# copy the service definition file in place

install -o root shrpid.service /lib/systemd/system
systemctl daemon-reload
systemctl enable shrpid

echo "Installation complete. Please reboot the system."
