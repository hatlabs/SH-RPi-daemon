#/usr/bin/env bash

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
./install_configs.sh
popd

# install the daemon build dependencies

apt install -y python3-pip

# install the daemon itself

pip3 install .

# copy the service definition file in place

install -o root shrpid.service /lib/systemd/system
systemctl daemon-reload
systemctl enable shrpid
