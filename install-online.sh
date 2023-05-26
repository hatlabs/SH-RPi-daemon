#!/usr/bin/env bash

# This installation script is intended for installing shrpid on
# a new Raspberry Pi computer with a one-line copy-paste command.
#
# The script pulls the defined branch from the GitHub repository
# and runs the install.sh script from there.
#
# The script needs root privileges to work properly.

set -euo pipefail
shopt -s inherit_errexit

# Bail out if not running as root
if [ "$(id -u)" != "0" ]; then
    echo "This script must be run as root" 1>&2
    exit 1
fi

# Allow customization of the repository URL and branch

REPOURL="${1-}"
BRANCH="${2-}"

shift
shift

if [ -z "$REPOURL" ] ; then
    REPOURL="https://github.com/hatlabs/SH-RPi-daemon"
fi

if [ -z "$BRANCH" ] ; then
    BRANCH="main"
fi

# create a temporary directory for the installation

tmp_dir=$(mktemp -d -t SH-RPi-daemon-XXXXXXXX)

# set up a hook to clean up the temporary directory on exit
trap 'rm -rf "$tmp_dir"' EXIT

cd $tmp_dir

curl -L \
    ${REPOURL}/archive/refs/heads/${BRANCH}.tar.gz \
    -o SH-RPi-daemon-${BRANCH}.tar.gz

tar zxvf SH-RPi-daemon-${BRANCH}.tar.gz
cd SH-RPi-daemon-${BRANCH}

./install.sh "$@"
