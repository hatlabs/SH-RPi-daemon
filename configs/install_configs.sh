#!/usr/bin/env bash

set -euo pipefail
shopt -s inherit_errexit

#
: <<'EOF'
The MIT License (MIT)

Installer for SH-RPi daemon and Raspberry Pi config files
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
OVERLAY_DIR=/boot/overlays
SCRIPT_HWCLOCK_SET=/lib/udev/hwclock-set
CAN_INTERFACE_FILE=/etc/network/interfaces.d/can0
if [ $_DEBUG -ne 0 ]; then
  CONFIG=debug/config.txt
  OVERLAY_DIR=debug/overlays
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
  elif [ $RET -eq 1 ]; then
    SETTING=off
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

install_dtb() {
  ovs=$1
  ovb=$2
  dtc -@ -I dts -O dtb -o $2 $1
  install -o root $ovb $OVERLAY_DIR
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
      printf "dtoverlay=$ov\n" >> $CONFIG
    fi
    STATUS=enabled
  elif [ $RET -eq 1 ]; then
    sed $CONFIG -i -e "s/^dtoverlay=$ov/#dtoverlay=$ov/"
    STATUS=disabled
  else
    return $RET
  fi
}

function enable_config_line() {
  local line="$1"
  local file="$2"
  if grep -q "$line" "$file"; then
    if grep -q "^#.*$line" "$file"; then
      sed -i "s/^#\($line\)/\1/" "$file"
    fi
  else
    echo "$line" | tee -a "$file" >/dev/null
  fi
}

function disable_config_line() {
  local line="$1"
  local file="$2"
  if grep -q "$line" "$file"; then
    if ! grep -q "^#.*$line" "$file"; then
      sed -i "s/^\($line\)/#\1/" "$file"
    fi
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

do_dialog_rtc() {
  do_dialog --backtitle "Hat Labs Ltd" \
    --title "RTC" \
    --radiolist "Would you like to enable the on-board Real-time Clock? \
This will allow the Pi to keep time even when it is not connected to the internet. \n\
\n\
Normally, you would want to always enable this. \
Only disable the RTC if your board doesn't have an RTC or if you are \
using your own baseboard with built-in RTC. \
\n\
Press SPACE to select, ENTER to accept selection and ESC to cancel." 20 75 3 \
    "Enable" "Enable the on-board Real-time Clock" ON \
    "Disable" "Disable the on-board Real-time Clock" off \
    "Skip" "Do not change the RTC setting" off
}

do_dialog_can() {
  do_dialog --backtitle "Hat Labs Ltd" \
    --title "CAN" \
    --radiolist "Would you like to enable the CAN interface? \n\
Select this option if you got the Waveshare 2-Channel Isolated CAN HAT. \
This will allow the Pi to communicate with a CAN network such as \
NMEA 2000 or J1939. \n\
\n\
NOTE: Enabling the interface without the hardware present will significantly \
degrade the Pi performance. \n\
\n\
Press SPACE to select, ENTER to accept selection and ESC to cancel." 20 75 3 \
    "Enable" "Enable the CAN interface" off \
    "Disable" "Disable the CAN interface" off \
    "Skip" "Do not change the CAN setting" ON
}

do_dialog_rs485() {
  do_dialog --backtitle "Hat Labs Ltd" \
    --title "RS485" \
    --radiolist "Would you like to enable the RS485 interface? \
Select this option if you got the Waveshare 2-Channel Isolated RS485 HAT. \
This will allow the Pi to communicate with compatible devices such as \
NMEA 0183 or Modbus RTU. \n\
\n\
Press SPACE to select, ENTER to accept selection and ESC to cancel." 20 75 3 \
    "Enable" "Enable the RS485 interface" off \
    "Disable" "Disable the RS485 interface" off \
    "Skip" "Do not change the RS485 setting" ON
}

do_dialog_maxm8q() {
  do_dialog --backtitle "Hat Labs Ltd" \
    --title "MAX-M8Q GNSS HAT" \
    --radiolist "Would you like to enable the MAX-M8Q GNSS (GPS) HAT? \
Select this option if you got the MAX-M8Q GNSS HAT. \
This will allow the Pi to communicate with the GNSS receiver. \n\
\n\
Press SPACE to select, ENTER to accept selection and ESC to cancel." 20 75 3 \
    "Enable" "Enable the MAX-M8Q GNSS HAT" off \
    "Disable" "Disable the MAX-M8Q GNSS HAT" off \
    "Skip" "Do not change the MAX-M8Q GNSS HAT setting" ON
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

  $DIALOG "$@" 2>$tempfile

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

INSTALL_RTC=0
UNINSTALL_RTC=0
INSTALL_MCP2515=0
UNINSTALL_MCP2515=0
INSTALL_RS485=0
UNINSTALL_RS485=0
INSTALL_MAXM8Q=0
UNINSTALL_MAXM8Q=0
INSTALL_SC16IS752=0
UNINSTALL_SC16IS752=0

function do_dialogs() {
  # Ask about RTC
  do_dialog_rtc

  if [[ $dialog_result == *"Enable"* ]]; then
    INSTALL_RTC=1
    UNINSTALL_RTC=0
  elif [[ $dialog_result == *"Disable"* ]]; then
    INSTALL_RTC=0
    UNINSTALL_RTC=1
  else
    INSTALL_RTC=0
    UNINSTALL_RTC=0
  fi

  # Ask about CAN

  do_dialog_can

  if [[ $dialog_result == *"Enable"* ]]; then
    INSTALL_MCP2515=1
    UNINSTALL_MCP2515=0
  elif [[ $dialog_result == *"Disable"* ]]; then
    INSTALL_MCP2515=0
    UNINSTALL_MCP2515=1
  else
    INSTALL_MCP2515=0
    UNINSTALL_MCP2515=0
  fi

  # Ask about RS485

  do_dialog_rs485

  if [[ $dialog_result == *"Enable"* ]]; then
    INSTALL_SC16IS752=1
    UNINSTALL_SC16IS752=0
  elif [[ $dialog_result == *"Disable"* ]]; then
    INSTALL_SC16IS752=0
    UNINSTALL_SC16IS752=1
  else
    INSTALL_SC16IS752=0
    UNINSTALL_SC16IS752=0
  fi

  # Ask about MAX-M8Q GNSS HAT

  do_dialog_maxm8q

  if [[ $dialog_result == *"Enable"* ]]; then
    INSTALL_MAXM8Q=1
    UNINSTALL_MAXM8Q=0
  elif [[ $dialog_result == *"Disable"* ]]; then
    INSTALL_MAXM8Q=0
    UNINSTALL_MAXM8Q=1
  else
    INSTALL_MAXM8Q=0
    UNINSTALL_MAXM8Q=0
  fi
}

function parse_enable_disable_args() {
  if [ ! -z "$ENABLE_MODULES" ]; then
    # Split the comma-separated list into an array
    ENABLE_MODULES=(${ENABLE_MODULES//,/ })

    # Check if the user wants to enable the RTC
    if [[ " ${ENABLE_MODULES[@]} " =~ " RTC " ]]; then
      INSTALL_RTC=1
    fi

    # Check if the user wants to enable the CAN controller
    if [[ " ${ENABLE_MODULES[@]} " =~ " CAN " ]]; then
      INSTALL_MCP2515=1
    fi

    # Check if the user wants to enable the RS485 interface
    if [[ " ${ENABLE_MODULES[@]} " =~ " RS485 " ]]; then
      INSTALL_SC16IS752=1
    fi

    # Check if the user wants to enable the MAX-M8Q GNSS HAT
    if [[ " ${ENABLE_MODULES[@]} " =~ " MAX-M8Q " ]]; then
      INSTALL_MAXM8Q=1
    fi
  fi

  if [ ! -z "$DISABLE_MODULES" ]; then
    # Split the comma-separated list into an array
    DISABLE_MODULES=(${DISABLE_MODULES//,/ })

    # Check if the user wants to disable the RTC
    if [[ " ${DISABLE_MODULES[@]} " =~ " RTC " ]]; then
      UNINSTALL_RTC=1
    fi

    # Check if the user wants to disable the CAN controller
    if [[ " ${DISABLE_MODULES[@]} " =~ " CAN " ]]; then
      UNINSTALL_MCP2515=1
    fi

    # Check if the user wants to disable the RS485 interface
    if [[ " ${DISABLE_MODULES[@]} " =~ " RS485 " ]]; then
      UNINSTALL_SC16IS752=1
    fi

    # Check if the user wants to disable the MAX-M8Q GNSS HAT
    if [[ " ${DISABLE_MODULES[@]} " =~ " MAX-M8Q " ]]; then
      UNINSTALL_MAXM8Q=1
    fi
  fi
}

function usage() {
  echo "Usage: $0 [options]"
  echo "Options:"
  echo "  -h, --help"
  echo "    Print this help message"
  echo "  -y, --non-interactive"
  echo "    Run in non-interactive mode"
  echo "  --enable <module1,module2,...>"
  echo "    Enable the specified modules"
  echo "  --disable <module1,module2,...>"
  echo "    Disable the specified modules"
  echo ""
  echo "Valid module names:"
  echo "  RTC"
  echo "  CAN"
  echo "  RS485"
  echo "  MAX-M8Q"
  echo ""
}

# Everything else needs to be run as root
if [ $(id -u) -ne 0 ]; then
  printf "Script must be run as root. Try 'sudo $0'\n"
  exit 1
fi

INTERACTIVE=1
VERSION=2
ENABLE_MODULES=""
DISABLE_MODULES=""

# parse command line arguments
while [ $# -gt 0 ]; do
  case "$1" in
  -h | --help)
    usage
    exit 1
    ;;
  -y | --non-interactive)
    INTERACTIVE=0
    shift
    ;;
  --enable)
    ENABLE_MODULES="$2"
    shift
    shift
    ;;
  --disable)
    DISABLE_MODULES="$2"
    shift
    shift
    ;;
  *)
    echo "Unknown argument: $1"
    usage
    exit 1
    ;;
  esac
done

if [ $INTERACTIVE -eq 0 ] || [ ! -z "$ENABLE_MODULES" ] || [ ! -z "$DISABLE_MODULES" ] ; then
  # Non-interactive mode is requested
  parse_enable_disable_args
else
  # If interactive mode is enabled, we need to ask the user

  # Make sure "dialog" is installed
  if ! command -v dialog &>/dev/null; then
    apt-get -y install dialog
  fi

  do_dialogs
fi

# I2C is needed for SH-RPi - enable unconditionally
echo "Enabling I2C"
do_i2c 0

# Check if the SH-RPi device is present and determine the hardware version
if detect_i2c_device '(6d)'; then
  echo "SH-RPi device detected"
  REPORTED_VERSION=$(i2cget -f -y 1 0x6d 0x01)
  # REPORTED_VERSION is "0xff" for version 2 hardware
  if [ "$REPORTED_VERSION" = "0xff" ]; then
    echo "SH-RPi version 2 detected"
    VERSION=2
  else
    echo "SH-RPi version 1 detected"
    VERSION=1
  fi
else
  echo "SH-RPi device not detected. Aborting."
  exit 1
fi

# This is required for proper SH-RPi operation
echo "Installing the GPIO poweroff detection overlay"
enable_config_line "dtoverlay=gpio-poweroff,gpiopin=2,input,active_low=17" $CONFIG

if [ $INSTALL_RTC -eq 1 ]; then
  if [ $VERSION -eq 1 ]; then
    # Version 1 boards have a DS3231 real-time clock chip.
    # Only install the ds3231 configuration if the device is detected.
    if detect_i2c_device '(68)'; then
      echo "Installing DS3231 real-time clock device overlay"
      enable_config_line "dtoverlay=i2c-rtc,ds3231" $CONFIG
      rtc_install
    else
      echo "DS3231 real-time clock device not detected. Skipping."
    fi
  else
    # only install the pcf8563 configuration if the device is detected
    if detect_i2c_device '(51)|(50: -- UU)'; then
      echo "Installing PCF8563 real-time clock device overlay"
      enable_config_line "dtoverlay=i2c-rtc,pcf8563" $CONFIG
      rtc_install
    else
      echo "PCF8563 real-time clock device not detected or already installed. Skipping."
    fi
  fi
elif [ $UNINSTALL_RTC -eq 1 ]; then
  if [ $VERSION -eq 1 ]; then
    echo "Disabling DS3231 real-time clock device overlay"
    disable_config_line "dtoverlay=i2c-rtc,ds3231" $CONFIG
    rtc_uninstall
  else
    echo "Disabling PCF8563 real-time clock device overlay"
    disable_config_line "dtoverlay=i2c-rtc,pcf8563" $CONFIG
    rtc_uninstall
  fi
fi

# Enable SPI only if either the MCP2515 or the SC16IS752 are enabled
if [ $INSTALL_MCP2515 -eq 1 ] || [ $INSTALL_SC16IS752 -eq 1 ]; then
  echo "Enabling SPI"
  set_config_var dtparam=spi on $CONFIG
elif [ $UNINSTALL_MCP2515 -eq 1 ] && [ $UNINSTALL_SC16IS752 -eq 1 ]; then
  echo "Disabling SPI"
  set_config_var dtparam=spi off $CONFIG
fi

if [ $INSTALL_MCP2515 -eq 1 ]; then
  if [ $VERSION -eq 1 ]; then
    if [ -d $OVERLAY_DIR ]; then
      echo "Installing DTBs for SPI and MCP2515"
      # these are safe to do unconditionally
      install_dtb spi0-3cs-overlay.dts spi0-3cs.dtbo
      install_dtb mcp2515-can2-overlay.dts mcp2515-can2.dtbo
    fi
    echo "Installing extra SPI channel and MCP2515 overlays"
    do_overlay mcp2515-can2,oscillator=16000000,interrupt=5,cs2=6 0
  else # not version 1
    echo "Installing the MCP2515 overlay"
    enable_config_line "dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=23" $CONFIG
  fi
  if [ ! -f $CAN_INTERFACE_FILE ]; then
    echo "Installing CAN interface file"
    install -o root can0.interface $CAN_INTERFACE_FILE
  fi
elif [ $UNINSTALL_MCP2515 -eq 1 ]; then
  if [ $VERSION -eq 1 ]; then
    echo "Disabling extra SPI channel and MCP2515 overlays"
    disable_overlay mcp2515-can2,oscillator=16000000,interrupt=5,cs2=6 0
  else # not version 1
    echo "Disabling the MCP2515 overlay"
    disable_config_line "dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=23" $CONFIG
  fi
  if [ -f $CAN_INTERFACE_FILE ]; then
    echo "Removing CAN interface file"
    rm $CAN_INTERFACE_FILE
  fi
fi

# Enable the SC16IS752 overlay if requested
if [ $INSTALL_SC16IS752 -eq 1 ]; then
  echo "Installing the SC16IS752 overlay"
  enable_config_line "dtoverlay=sc16is752-spi1,int_pin=24" $CONFIG
elif [ $UNINSTALL_SC16IS752 -eq 1 ]; then
  echo "Disabling the SC16IS752 overlay"
  disable_config_line "dtoverlay=sc16is752-spi1,int_pin=24" $CONFIG
fi

# Enable the MAX-M8Q GNSS HAT settings if requested
if [ $INSTALL_MAXM8Q -eq 1 ]; then
  echo "Enabling UART"
  enable_config_line "enable_uart=1" $CONFIG
  echo Disabling Bluetooth
  enable_config_line "dtoverlay=disable-bt" $CONFIG
  systemctl disable hciuart
  echo Disabling serial console

  # Check if console=serial0,115200 is already removed
  if grep -q "console=serial0,115200 " /boot/cmdline.txt; then
    # Remove console=serial0,115200
    sed -i 's/console=serial0,115200 //g' /boot/cmdline.txt
  fi

elif [ $UNINSTALL_MAXM8Q -eq 1 ]; then
  echo "Disabling UART"
  disable_config_line "enable_uart=1" $CONFIG
  echo Enabling Bluetooth
  disable_config_line "dtoverlay=disable-bt" $CONFIG
  systemctl enable hciuart
  # We are not re-enabling serial console here...
fi

echo "DONE. Reboot the apply the new settings."
