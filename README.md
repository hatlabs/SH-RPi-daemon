# Sailor Hat for Raspberry Pi: Daemon

## Introduction

[Sailor Hat for Raspberry Pi](https://hatlabs.github.io/sh-rpi/)
is a Raspberry Pi power management and CAN bus
controller board for marine and automotive use. The main features are:

- Power management with a 60F supercapacitor that provides so-called last gasp energy for shutting down the device in a controlled fashion after the system power is cut.
- Peak power management: The same supercapacitor circuitry is able to provide peak current for power-hungry devices such as the Raspberry Pi 4B, allowing those devices to be powered using current-limited subcircuits such as the NMEA2000 bus power wires.
- Protection circuitry: The board is protected against noisy 12V/24V voltages commonly present on vehicles or marine vessels.
- One isolated CAN bus controller, allowing for safe connectivity to a CAN bus such as the NMEA 2000 bus commonly used on boats, or an automotive CAN bus on a vehicle.
- A battery-powered real-time clock circuit, allowing for the device to keep time even in the absence of GPS or networking.
  
`sh-rpi-daemon` is a power monitor and watchdog for Sailor Hat for Raspberry Pi. It communicates with the Sailor Hat over I2C using a pre-configured I2C address. Supported features include:

- Blackout reporting if input voltage falls below a defined threshold
- Triggering of device shutdown if power isn't restored
- Supercap voltage reporting
- Watchdog functionality: if the SH-RPi receives no communication for 10 seconds, the SH-RPi will hard reset the device.

The main use case for the script is to have the board powered via a supercapacitor. If the power for the board is disconnected, the supercap is able to supply sufficient power that the device is able to shut itself down in a controlled fashion.

SH-RPi includes an MCP2515 can controller that communicates with the Raspberry Pi using SPI. To allow simultaneous use of other SPI-enabled hats, SH-RPi uses custom SPI GPIO pins. These pins need to be enabled using a custom device tree overlay. This is automatically installed using the instructions below.

## Installation

A fully automated installation script is provided. The script is tested on newly flashed Raspberry Pi OS and might fail on a heavily modified system. Installation has not been tested on any other operating systems.

To run the automated installation script, copy-paste the following command onto the Raspberry Pi command prompt:

    curl -L \
        https://raw.githubusercontent.com/hatlabs/SH-RPi-daemon/main/install.sh \
        | sudo bash

The command will fetch the installation script and execute it automatically.

Manual installation is also possible. If you prefer to do that, follow the steps taken in `install.sh` and `overlays/Makefile`.

## Getting the hardware

Sh-RPi devices are available for purchase at [hatlabs.fi](https://hatlabs.fi/).
