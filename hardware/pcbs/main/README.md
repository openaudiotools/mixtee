# Main Board

**Dimensions:** ~260 x 85 mm | **Layers:** 4 | **Orientation:** Horizontal, under top panel | **Instances:** 1

Central hub connecting all other boards. Houses the Teensy 4.1, XMOS XU216 USB audio bridge, galvanic isolation boundary, power management, I2C mux, and display interface. Panel-mount components (encoders, SD card, PC USB-C) protrude through top panel cutouts.

## Key ICs

- Teensy 4.1 on socket headers (+ PSRAM)
- XMOS XU216-256-TQ128 — 24-in/8-out USB Audio Class 2 bridge (passive TDM tap + SPI MIDI)
- TCA9548A I2C mux (0x70) — isolates codec buses via FFC
- 2× Si8662BB-B-IS1 — 6-channel digital isolators (TDM signal isolation, 150 Mbps)
- 2× ISO1541DR — isolated bidirectional I2C (1 MHz)
- 2× Murata MEJ2S0505SC — isolated DC-DC 5V→5V_ISO (2W, 5.2 kV)
- 74LVC1G00 NAND soft-latch power circuit
- TPS22965 load switch (5A, soft-start)
- ADP7118 LDO (virtual ground buffer)
- OPA1678 (2.5V virtual ground buffer)

## See Also

- [`connections.md`](connections.md) — all connector interfaces (FFC, JST, USB-C, display, SD, Ethernet ribbon)
- [`architecture.md`](architecture.md) — soft-latch, power distribution, I2C mux, galvanic isolation, pin assignments

## Status

Not started. Waiting on finalized pinout and input mother board validation.
