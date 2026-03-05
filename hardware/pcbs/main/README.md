# Main Board

**Dimensions:** ~260 x 85 mm | **Layers:** 4 | **Orientation:** Horizontal, under top panel | **Instances:** 1

Central hub connecting all other boards. Houses the Teensy 4.1, XMOS XU216 USB audio bridge, power management, I2C mux, display interface, and pop suppression switches. Panel-mount components (encoders, SD card, PC USB-C) protrude through top panel cutouts.

## Key ICs

- Teensy 4.1 on socket headers (+ PSRAM)
- XMOS XU216-256-TQ128 — 24-in/8-out USB Audio Class 2 bridge (passive TDM tap + SPI MIDI)
- TCA9548A I2C mux (0x70) — isolates codec buses via FFC
- 4× TS5A3159 analog mute switches (pop suppression)
- 74LVC1G00 NAND soft-latch power circuit
- TPS22965 load switch (5A, soft-start)
- ADP7118 LDO (virtual ground buffer)
- OPA1678 (2.5V virtual ground buffer)

## See Also

- [`connections.md`](connections.md) — all connector interfaces (FFC, JST, USB-C, display, SD, Ethernet ribbon)
- [`architecture.md`](architecture.md) — soft-latch, power distribution, I2C mux, pop suppression, pin assignments

## Status

Not started. Waiting on finalized pinout and input mother board validation.
