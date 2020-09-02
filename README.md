# Sailor Hat for Raspberry Pi: Daemon

## Introduction

[Sailor Hat for Raspberry Pi](https://github.com/mairas/sailor-hat-hardware)
is a Raspberry Pi power management and CAN bus
controller board for marine and automotive use. The main features are:

- Power management for 2.7V supercapacitors that provide so-called last gasp energy for shutting down the device in a controlled fashion after the system power is cut.
- Peak power management: The same supercapacitor circuitry is able to provide peak current for power-hungry devices such as the Raspberry Pi 4B+, allowing those devices to be powered using current-limited subcircuits such as the NMEA2000 bus power wires.
- Protection circuitry: The board is protected against noisy 12V voltages commonly present on vehicles or marine vessels.
- One isolated CAN bus controller, allowing for safe connectivity to a CAN bus such as the NMEA 2000 bus commonly used on boats, or an automotive CAN bus on a vehicle.
- A battery-powered real-time clock circuit, allowing for the device to keep time even in the absence of GPS or networking.
  
`sailor-hat-daemon` is a power monitor and watchdog for Sailor Hat for Raspberry Pi. It communicates to the Sailor Hat over I2C using a pre-configured I2C address. Supported features include:

- Blackout reporting if input voltage falls below a defined threshold
- Triggering of device shutdown if power isn't restored
- Supercap voltage reporting
- Watchdog functionality: if the Sailor Hat receives no communication for 3 seconds, the Sailor Hat will hard reset the device.

The main use case for the script is to have the board powered via a super-capacitor. If the power for the board is disconnected, the supercap is able to supply sufficient power that the device is able to shut itself down in a controlled fashion.

## Installation

The daemon script can be installed by issuing the following command:

    sudo python3 setup.py install

It is assumed that the daemon can call `poweroff` using `sudo` without a password prompt. This is normally the case on the Raspberry Pi if the `pi` user is used. If not, give your preferred user permissions to call `poweroff` without a password by running `sudo visudo` and adding the following line:

    pi ALL = NOPASSWD: /sbin/poweroff

Finally, to run the script automatically as a service, copy
`sailor-hat-daemon.service` to `/lib/systemd/system`. Once the file is in place, issue the following commands:

    systemctl daemon-reload
    systemctl enable sailor-hat-daemon
    systemctl start sailor-hat-daemon
