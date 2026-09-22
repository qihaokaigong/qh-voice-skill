# Complete reference wiring

Read this before identifying or wiring the only supported hardware Profile,
`qh.voice-kit.breadboard.n16r8.v1`. This table describes the reference assembly
used by the current firmware; a different module, board revision, pin mapping,
or display timing is not automatically compatible.

Disconnect USB and every other power source before changing wires. Use the PCB
labels, not jumper-wire colors, to identify pins. All modules share ESP32 GND.

| Module | Module pin | Destination | Purpose / constraint |
| --- | --- | --- | --- |
| INMP441 | `VDD` | `3V3` | 3.3 V only; do not use 5 V |
| INMP441 | `GND` | `GND` | Common ground |
| INMP441 | `SCK` | `GPIO4` | I²S bit clock |
| INMP441 | `WS` | `GPIO5` | I²S word select |
| INMP441 | `SD` | `GPIO6` | Microphone data to ESP32 |
| INMP441 | `L/R` | `GND` | Select left slot; firmware reads the left slot |
| Three-pin button | `VCC` | `3V3` | Module power |
| Three-pin button | `OUT` | `GPIO8` | Hold to talk; released LOW, pressed HIGH on the reference module |
| Three-pin button | `GND` | `GND` | Common ground |
| GMT130-V1.0 ST7789 | `GND` | `GND` | Common ground |
| GMT130-V1.0 ST7789 | `VCC` | `3V3` | Display power |
| GMT130-V1.0 ST7789 | `SCK` | `GPIO9` | SPI clock |
| GMT130-V1.0 ST7789 | `SDA` | `GPIO10` | SPI MOSI; this is not I²C SDA |
| GMT130-V1.0 ST7789 | `RES` | `GPIO11` | Display reset |
| GMT130-V1.0 ST7789 | `DC` | `GPIO12` | Command/data select |
| GMT130-V1.0 ST7789 | `BLK` | `3V3` | Backlight always on |
| GMT130-V1.0 ST7789 | no `CS` pin | not connected | Firmware uses CS = -1 and hardware SPI Mode 3 |
| MAX98357A | `VIN` | `3V3` | Amplifier power used by the verified assembly |
| MAX98357A | `GND` | `GND` | Common ground |
| MAX98357A | `BCLK` | `GPIO16` | I²S bit clock |
| MAX98357A | `LRC` | `GPIO17` | I²S word select |
| MAX98357A | `DIN` | `GPIO18` | PCM data from ESP32 |
| MAX98357A | `GAIN` | not connected | Use the module default gain |
| MAX98357A | `SD` | not connected | Reference module operates with this pin floating |
| MAX98357A | `SPK+` | 喇叭正端 | Differential speaker output |
| MAX98357A | `SPK-` | 喇叭负端 | Differential speaker output; never connect either speaker lead to GND |

The reference speaker is a passive 4 Ω / 3 W unit. Its two leads connect only
to `SPK+` and `SPK-`. The recorded red-to-plus and black-to-minus colors apply
only to that particular speaker lead and must not be generalized to other
hardware.
