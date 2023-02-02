# Sailor Hat for Raspberry Pi: Daemon

<div class="warning" style='background-color:#BDBA58; color: #000000; border-left: solid #716e14 4px; border-radius: 4px; padding:0.7em;'>
<span>
<p style='margin-top:1em; text-align:center'>
<b>Notice about different versions</b></p>
<p style='margin-left:1em;'>
There are two different versions of SH-RPi. Version 1 was released in 2021 and includes an integrated CAN controller for connecting to the NMEA 2000 bus. It uses different daemon software than version 2. Version 1 software is archived to the <a href="https://github.com/hatlabs/SH-RPi-daemon/tree/v1" style='color: #6d131e;'><b>v1</b> branch</a> of this repository.
</p>

<p style='margin-left:1em;'>
The description below applies to the current version 2 of SH-RPi. Version 2 is available for purchase at <a href="https://hatlabs.fi/" style='color: #6d131e;'><b>hatlabs.fi</b></a>.
</p>
</span>
</div>

## Introduction

[SH-RPi](https://shop.hatlabs.fi/products/sh-rpi), formally known as Sailor Hat for Raspberry Pi,
is a Raspberry Pi smart power management board. The main features are:

- Power management with a 60F supercapacitor that provides so-called last gasp energy for shutting down the device in a controlled fashion after the system power is cut.
- Peak power management: The same supercapacitor circuitry is able to provide peak current for power-hungry devices such as the Raspberry Pi 4B, allowing those devices to be powered using current-limited subcircuits such as the NMEA2000 bus power wires.
- Protection circuitry: The board is protected against noisy 12V/24V voltages commonly present on vehicles or marine vessels.
- A battery-powered real-time clock circuit, allowing for the device to keep time even in the absence of GPS or networking.
  
`sh-rpi-daemon` is a power monitor and watchdog for the SH-RPi. It communicates with the SH-RPi device, providing the "smart" aspects of the operation. Supported features include:

- Blackout reporting if input voltage falls below a defined threshold
- Triggering of device shutdown if power isn't restored
- Supercap voltage reporting
- Watchdog functionality: if the SH-RPi receives no communication for 10 seconds, the SH-RPi will hard reset the device.

The main use case for the script is to have the board powered via a supercapacitor. If the power for the board is disconnected, the supercap is able to supply sufficient power that the device is able to shut itself down in a controlled fashion.

## Installation

**Installation script for SH-RPi v2 is not yet available.**

## SH-RPi documentation

For a more detailed SH-RPi documentation, please visit the [documentation website](https://docs.hatlabs.fi/sh-rpi).

## Getting the hardware

Sh-RPi devices are available for purchase at [shop.hatlabs.fi](https://shop.hatlabs.fi/).
