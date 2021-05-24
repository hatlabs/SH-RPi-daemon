#!/usr/bin/env bash

set -euo pipefail
shopt -s inherit_errexit

#
: <<'EOF'
The MIT License (MIT)

Installer for SH-RPi daemon and Raspberry config files
  Matti Airas, matti.airas@hatlabs.fi
Copyright (C) 2021  Hat Labs Ltd

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
OVERLAY_DIR=/boot/overlays
CAN_INTERFACE_FILE=/etc/network/interfaces.d/can0
if [ $_DEBUG -ne 0 ]; then
  CONFIG=debug/config.txt
  SCRIPT_HWCLOCK_SET=debug/hwclock-set
  OVERLAY_DIR=debug/overlays
  CAN_INTERFACE_FILE=debug/can0
fi


set_config_var() {
  lua - "$1" "$2" "$3" <<EOF > "$3.bak"
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
  device=$1
  
  i2cdetect -y $bus | cut -f 2- -d "" | grep -q $device
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
    printf "i2c-dev\n" >> /etc/modules
  fi
  dtparam i2c_arm=$SETTING
  modprobe i2c-dev
  if ! command -v i2cdetect &> /dev/null; then
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

rtc_ds3231_install() {
  apt-get -y remove fake-hwclock
  update-rc.d -f fake-hwclock remove
  systemctl disable fake-hwclock
  sed -i -e "s,^\(if \[ \-e /run/systemd/system \] ; then\),if false; then\n#\1," $SCRIPT_HWCLOCK_SET
}


# Everything else needs to be run as root
if [ $(id -u) -ne 0 ]; then
  printf "Script must be run as root. Try 'sudo $0'\n"
  exit 1
fi


echo "Enabling I2C"
do_i2c 0

# only install the ds3231 configuration if the device is detected
if detect_i2c_device 68 ; then
  echo "Installing DS3231"
  do_overlay i2c-rtc,ds3231 0
  rtc_ds3231_install
fi

echo "Enabling SPI"
set_config_var dtparam=spi on $CONFIG

if [ -d $OVERLAY_DIR ]; then
  echo "Installing DTBs for SPI and MCP2515"
  # these are safe to do unconditionally
  install_dtb spi0-3cs-overlay.dts spi0-3cs.dtbo
  install_dtb mcp2515-can2-overlay.dts mcp2515-can2.dtbo
fi

echo "Installing extra SPI channel and MCP2515 overlays"
do_overlay mcp2515-can2,oscillator=16000000,interrupt=5,cs2=6 0
do_overlay gpio-poweroff,gpiopin=2,input,active_low=17 0

if [ ! -f $CAN_INTERFACE_FILE ] ; then
  echo "Installing CAN interface file"
  install -o root can0.interface $CAN_INTERFACE_FILE
fi

echo "DONE. Reboot the system to enable the new devices."
