# HP Board — Architecture

*← Back to [README](README.md)*

------

## Headphone Amplifier

- Off-the-shelf TPA6132 or MAX97220 breakout module (~$2–5)
- Ground-referenced output (no AC coupling caps needed on jack)
- 25 mW into 32 ohm, 0.01% THD+N typical
- Single 3.3–5V supply (from 5V_ISO via Board 1-top cable)
- Output through 10k ohm log pot (volume) to headphone TRS jack

------

## Power

- **Input:** 5V_ISO from Board 1-top via 4-pin JST-PH cable pin 3
- **Ground:** GND_ISO — entire board on isolated ground, no connection to system GND
- **Consumption:** ~50 mA (amp module + minimal passives)
- Decoupling: 10 µF + 0.1 µF ceramic near amp module power input

------

## Headphone Detect

The TRS jack includes a detect switch (normally closed to GND_ISO, open when plug inserted). The detect signal is routed back to Board 1-top where it connects to **MCP23008 GP6** (I2C GPIO expander at address 0x21). Teensy reads the detect state via I2C polling (~100 Hz).

This eliminates the need for a dedicated Teensy GPIO pin (pin 39 freed) and avoids routing a detect signal across the isolation barrier.

------

## Design Notes

- 2-layer PCB, minimal routing
- Entire ground plane is GND_ISO
- No high-speed digital signals on this board
- Mounting: panel-mount via headphone jack nut (top panel, left zone). Optional standoff.
- Keep analog signal traces short — breakout module placed near JST-PH connector

------

[Back to README](README.md)
