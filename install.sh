#/usr/bin/env bash

# This installation script is intended for installing SH-RPi-daemon on
# a new Raspberry Pi computer with a one-line copy-paste command.
#
# The script can be run locally but it does _not_ install the daemon
# from the local source directory but fetches a new copy from GitHub.

set -euo pipefail
shopt -s inherit_errexit

# Allow customization of the repository URL and branch

REPOURL=$1
BRANCH=$2

if [ -z "$REPOURL" ] ; then
    REPOURL="https://github.com/hatlabs/SH-RPi-daemon"
fi

if [ -z "$BRANCH" ] ; then
    BRANCH="master"
fi

# create a temporary directory for the installation

tmp_dir=$(mktemp -d -t SH-RPi-daemon-XXXXXXXX)
cd $tmp_dir

curl -L \
    ${REPOURL}/archive/refs/heads/${BRANCH}.zip \
    -o SH-RPi-daemon-${BRANCH}.zip

unzip SH-RPi-daemon-${BRANCH}.zip
cd SH-RPi-daemon-${BRANCH}

# install the daemon build dependencies

apt install -y python3-setuptools

# install the daemon itself

python3 setup.py install

# copy the service definition file in place

install -o root sh-rpi-daemon.service /lib/systemd/system
systemctl daemon-reload
systemctl enable sh-rpi-daemon

# install the device tree overlay and other configuration files

cd overlays
make install

# report the results

echo "*** ***"
echo "Installation finished. If you have any rejected patches"
echo "in the above output, you need to check that I2C and SPI are"
echo "enabled and that /boot/config.txt has a section specific"
echo "for SH-RPi-daemon."
