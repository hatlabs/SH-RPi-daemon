#!/usr/bin/env bash

set -euo pipefail
shopt -s inherit_errexit

#
: <<'EOF'
The MIT License (MIT)

Installer for SH-RPi daemon and Raspberry config files
  Matti Airas, matti.airas@hatlabs.fi
Copyright (C) 2021, 2023  Hat Labs Ltd

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
EOF

_DEBUG=0

CONFIG=/boot/config.txt
SCRIPT_HWCLOCK_SET=/lib/udev/hwclock-set
CAN_INTERFACE_FILE=/etc/network/interfaces.d/can0
if [ $_DEBUG -ne 0 ]; then
  CONFIG=debug/config.txt
  SCRIPT_HWCLOCK_SET=debug/hwclock-set
  CAN_INTERFACE_FILE=debug/can0
fi

set_config_var() {
  lua - "$1" "$2" "$3" <<EOF >"$3.bak"
local key=assert(arg[1])
local value=assert(arg[2])
local fn=assert(arg[3])
local file=assert(io.open(fn))
local made_change=false
for line in file:lines() do
  if line:match("^#?%s*"..key.."=.*$") then
    line=key.."="..value
    made_change=true
  end
  print(line)
end

if not made_change then
  print(key.."="..value)
end
EOF
  mv "$3.bak" "$3"
}

detect_i2c_device() {
  bus=1
  device="$1"

  i2cdetect -y $bus | cut -f 2- -d "" | egrep -q "$device"
}

get_i2c() {
  if grep -q -E "^(device_tree_param|dtparam)=([^,]*,)*i2c(_arm)?(=(on|true|yes|1))?(,.*)?$" $CONFIG; then
    echo 0
  else
    echo 1
  fi
}

do_i2c() {
  DEFAULT=--defaultno
  if [ $(get_i2c) -eq 0 ]; then
    DEFAULT=
  fi
  RET=$1
  if [ $RET -eq 0 ]; then
    SETTING=on
    STATUS=enabled
  elif [ $RET -eq 1 ]; then
    SETTING=off
    STATUS=disabled
  else
    return $RET
  fi

  set_config_var dtparam=i2c_arm $SETTING $CONFIG &&
    sed /etc/modules -i -e "s/^#[[:space:]]*\(i2c[-_]dev\)/\1/"
  if ! grep -q "^i2c[-_]dev" /etc/modules; then
    printf "i2c-dev\n" >>/etc/modules
  fi
  # Enable I2C right away to avoid rebooting
  dtparam i2c_arm=$SETTING
  modprobe i2c-dev
  if ! command -v i2cdetect &>/dev/null; then
    apt-get -y install i2c-tools
  fi
}

get_overlay() {
  ov=$1
  if grep -q -E "^dtoverlay=$ov" $CONFIG; then
    echo 0
  else
    echo 1
  fi
}

do_overlay() {
  ov=$1
  RET=$2
  DEFAULT=--defaultno
  CURRENT=0
  if [ $(get_overlay $ov) -eq 0 ]; then
    DEFAULT=
    CURRENT=1
  fi
  if [ $RET -eq $CURRENT ]; then
    ASK_TO_REBOOT=1
  fi
  if [ $RET -eq 0 ]; then
    sed $CONFIG -i -e "s/^#dtoverlay=$ov/dtoverlay=$ov/"
    if ! grep -q -E "^dtoverlay=$ov" $CONFIG; then
      printf "dtoverlay=$ov\n" >>$CONFIG
    fi
    STATUS=enabled
  elif [ $RET -eq 1 ]; then
    sed $CONFIG -i -e "s/^dtoverlay=$ov/#dtoverlay=$ov/"
    STATUS=disabled
  else
    return $RET
  fi
}

rtc_install() {
  apt-get -y remove fake-hwclock
  update-rc.d -f fake-hwclock remove
  systemctl disable fake-hwclock
  sed -i -e "s,^\(if \[ \-e /run/systemd/system \] ; then\),if false; then  #\1," $SCRIPT_HWCLOCK_SET
}

rtc_uninstall() {
  apt-get -y install fake-hwclock
  sed -i -e "s,^\(if false; then  #\),," $SCRIPT_HWCLOCK_SET
  systemctl enable fake-hwclock
}

do_dialog() {
  : "${DIALOG=dialog}"

  : "${DIALOG_OK=0}"
  : "${DIALOG_CANCEL=1}"
  : "${DIALOG_ESC=255}"

  : "${SIG_NONE=0}"
  : "${SIG_HUP=1}"
  : "${SIG_INT=2}"
  : "${SIG_QUIT=3}"
  : "${SIG_KILL=9}"
  : "${SIG_TERM=15}"

  tempfile=$( (tempfile) 2>/dev/null) || tempfile=/tmp/test$$
  trap "rm -f $tempfile" 0 $SIG_NONE $SIG_HUP $SIG_INT $SIG_QUIT $SIG_TERM

  $DIALOG --backtitle "Hat Labs Ltd" \
    --title "CHECKLIST BOX" "$@" \
    --checklist "Select the devices you want to enable. \n\
Only select the devices you have connected to your Pi. \n\
Enabling a device that is not connected may cause \n\
significant performance degradation. \n\
\n\
Use the UP/DOWN arrow keys to choose an option. \n\
Press SPACE to toggle an option on/off. \n\
Press ENTER to accept the selected options. \n\
Press ESC to abort the installation.\n\
  Select the overlays to enable:" 20 61 5 \
    "RTC" "Real-time clock. Leave enabled if unsure." on \
    "CAN" "NMEA 2000 or generic CAN bus support." off \
    "RS485" "NMEA 0183 or generic RS485 interface support." off 2>$tempfile

  retval=$?

  case "${returncode:-0}" in
  $DIALOG_OK)
    dialog_result=$(cat "$tempfile")
    ;;
  $DIALOG_CANCEL)
    echo "Cancel pressed."
    ;;
  $DIALOG_ESC)
    echo "Aborting."
    exit 1
    ;;
  *)
    echo "Return code was $returncode"
    ;;
  esac
}

# Everything else needs to be run as root
if [ $(id -u) -ne 0 ]; then
  printf "Script must be run as root. Try 'sudo $0'\n"
  exit 1
fi

# Use Dialog to ask for the user's preferences:
# - Should we enable the PCF8563 real-time clock?
# - Should we enable the MCP2515 CAN controller?
# - Should we enable the SC16IS752 overlay?

# Make sure "dialog" is installed
if ! command -v dialog &>/dev/null; then
  apt-get -y install dialog
fi

do_dialog

# Check if dialog_result includes "RTC"

if [[ $dialog_result == *"RTC"* ]]; then
  INSTALL_RTC=1
else
  INSTALL_RTC=0
fi

# Check if dialog_result includes "CAN"

if [[ $dialog_result == *"CAN"* ]]; then
  INSTALL_MCP2515=1
else
  INSTALL_MCP2515=0
fi

# Check if dialog_result includes "RS485"

if [[ $dialog_result == *"RS485"* ]]; then
  INSTALL_SC16IS752=1
else
  INSTALL_SC16IS752=0
fi

# I2C is needed for SH-RPi - enable unconditionaly
echo "Enabling I2C"
do_i2c 0

# This is required for proper SH-RPi operation
echo "Installing the GPIO poweroff detection overlay"
do_overlay gpio-poweroff,gpiopin=2,input,active_low=17 0

if [ $INSTALL_RTC -eq 1 ]; then
  # only install the pcf8563 configuration if the device is detected
  if detect_i2c_device '(51)|(50: -- UU)'; then
    echo "Installing PCF8563 real-time clock device overlay"
    do_overlay i2c-rtc,pcf8563 0
    rtc_install
  else
    echo "PCF8563 real-time clock device not detected or already installed. Skipping."
  fi
else
  echo "Disabling PCF8563 real-time clock device overlay"
  do_overlay i2c-rtc,pcf8563 1
  rtc_uninstall
fi

# Enable SPI only if either the MCP2515 or the SC16IS752 are enabled
if [ $INSTALL_MCP2515 -eq 1 ] || [ $INSTALL_SC16IS752 -eq 1 ]; then
  echo "Enabling SPI"
  set_config_var dtparam=spi on $CONFIG
else
  echo "Disabling SPI"
  set_config_var dtparam=spi off $CONFIG
fi

if [ $INSTALL_MCP2515 -eq 1 ]; then
  echo "Installing the MCP2515 overlay"
  do_overlay mcp2515-can0,oscillator=16000000,interrupt=23 0

  if [ ! -f $CAN_INTERFACE_FILE ]; then
    echo "Installing CAN interface file"
    install -o root can0.interface $CAN_INTERFACE_FILE
  fi
else
  echo "Disabling the MCP2515 overlay"
  do_overlay mcp2515-can0,oscillator=16000000,interrupt=23 1

  if [ -f $CAN_INTERFACE_FILE ]; then
    echo "Removing CAN interface file"
    rm $CAN_INTERFACE_FILE
  fi
fi

# Enable the SC16IS752 overlay if requested
if [ $INSTALL_SC16IS752 -eq 1 ]; then
  echo "Installing the SC16IS752 overlay"
  do_overlay dtoverlay=sc16is752-spi1,int_pin=24 0
else
  echo "Disabling the SC16IS752 overlay"
  do_overlay dtoverlay=sc16is752-spi1,int_pin=24 1
fi

echo "DONE. Reboot the system to enable the new devices."
