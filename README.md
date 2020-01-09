# Sailor Hat for Raspberry Pi: Daemon

## Introduction

`sailor-hat-daemon` is a power monitor and watchdog for 
[Sailor Hat for Raspberry Pi](https://github.com/mairas/sailor-hat-hardware).
It communicates to the Sailor Hat over I2C using a pre-configured
I2C address. Supported features include:

- Blackout reporting if input voltage falls below a defined threshold
- Triggering of device shutdown if power isn't restored
- Supercap voltage reporting
- Watchdog functionality: if the Sailor Hat receives no communication
  for 10 seconds, the Sailor Hat will hard reset the device.

The main use case for the script is to have the board powered via
a super-capacitor. In the case power for the board is
disconnected, the supercap is able to supply sufficient power
that the device is able to shut itself down in a controlled fashion.



## Installation

The monitor script can be installed by issuing the following command:

    sudo python3 setup.py install

At this point, you
should already be able to run the script. However, since calling
`poweroff` requires elevated privileges, it is done using `sudo`.
Give your preferred user permissions to call `poweroff` without a
password by running `sudo visudo` and adding the following line:

    pi ALL = NOPASSWD: /sbin/poweroff

Finally, to run the script automatically as a service, copy
`sailor-hat.service` to `/etc/systemd/system`.

## Usage

To configure the monitor behavior, directly edit the script or service 
files.
