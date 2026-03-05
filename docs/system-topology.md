# MIXTEE: System Topology

*← Back to [README](../README.md) | See also: [Hardware](hardware.md) · [Enclosure](enclosure.md)*

------

## Overview

MIXTEE uses a modular multi-board design. The main board sits horizontally under the top panel. Six back-panel boards (three mother+daughter pairs) carry all audio I/O. A dedicated IO board on the left side of the top panel handles Ethernet, USB MIDI host, MIDI IN/OUT, and provides a mounting area for an off-the-shelf headphone amp breakout module. A key PCB handles the illuminated switch grid. An off-the-shelf STUSB4500 breakout module on the back panel provides USB PD power input.

Total: **6 unique PCB designs**, 10 physical boards + 1 off-the-shelf power module.

For detailed per-board documentation, see each board's directory under `hardware/pcbs/`.

------

## Board Summary

| ID | Name | Unique design | Instances | Layers | Active components | Details |
|----|------|--------------|-----------|--------|-------------------|---------|
| M | Main Board | Yes | 1 | 4 | Teensy, XMOS XU216 USB audio bridge, power mgmt, TS5A3159 mute, 74LVC1G00 soft-latch, ADP7118 LDO | [README](../hardware/pcbs/main/README.md) |
| IO | IO Board | Yes | 1 | 2 | FE1.1s hub, 6N138 MIDI, 2× TPS2051, RJ45 MagJack | [README](../hardware/pcbs/io/README.md) |
| P | Power Module | Off-the-shelf | 1 | — | STUSB4500 USB PD breakout (purchased) | [README](../hardware/pcbs/power/README.md) |
| 1-top | Input Mother (TDM1) | Shared w/ 2-top | 1 | 4 | ADP7118 LDO, 2× AK4619VN, 8× input analog, 4× output analog | [README](../hardware/pcbs/input-mother/README.md) |
| 2-top | Input Mother (TDM2) | Shared w/ 1-top | 1 | 4 | ADP7118 LDO, 2× AK4619VN, 8× input analog | [README](../hardware/pcbs/input-mother/README.md) |
| 1-bot | Input Daughter (TDM1) | Shared w/ all daughters | 1 | 2 | ESD diodes only | [README](../hardware/pcbs/daughter-output/README.md) |
| 2-bot | Input Daughter (TDM2) | Shared | 1 | 2 | ESD diodes only | [README](../hardware/pcbs/daughter-output/README.md) |
| O-top | Output Top | Shared (or near-identical) | 1 | 2 | ESD diodes only | [README](../hardware/pcbs/daughter-output/README.md) |
| O-bot | Output Bottom | Shared | 1 | 2 | ESD diodes only | [README](../hardware/pcbs/daughter-output/README.md) |
| K | Key PCB | Yes | 1 | 2 | 16× NeoPixel, 16× CHOC socket, MCP23017 | [README](../hardware/pcbs/key/README.md) |

**Unique PCB designs:** 6 (Main, IO, Input Mother, Daughter/Output, Key, plus possibly a separate Output Top if connector differs) + 1 off-the-shelf power module

------

## Connector Summary

| Connection | Type | Pitch | Pins | Cable length | Pinout |
|------------|------|-------|------|-------------|--------|
| Mother ↔ Daughter (×3) | JST-PH wire harness | 2.0 mm | 6 | ~15–20 mm | [daughter-output](../hardware/pcbs/daughter-output/connections.md) |
| Main ↔ Input Mother (×2) | FFC + ZIF | 1.0 mm | 16 | ~40–50 mm | [input-mother](../hardware/pcbs/input-mother/connections.md) |
| Main ↔ IO Board | FFC + ZIF | 1.0 mm | 12 | ~100–120 mm | [io](../hardware/pcbs/io/connections.md) |
| Power Board → Main | JST-PH or screw terminal | 2.0 mm | 2 | ~60–80 mm | [power](../hardware/pcbs/power/connections.md) |
| 1-top → O-top | JST-PH or FFC | 2.0 / 1.0 mm | 10 | ~80 mm | [input-mother](../hardware/pcbs/input-mother/connections.md) |
| Main ↔ Key PCB | JST-PH | 2.0 mm | 6 | ~30–40 mm | [key](../hardware/pcbs/key/connections.md) |
| Main ↔ Display | Per module | Varies | 8–10 | ~20 mm | [main](../hardware/pcbs/main/connections.md) |

------

## Back Panel Board Arrangement

Looking at the back panel (260 mm wide × 50 mm tall):

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  O-top   │         1-top          │         2-top          │ [PWR]  [PWR]  │
│  4 jacks │        4 jacks         │        4 jacks         │ USB-C  BUTTON │
│(Mst,A1-3)│    (L in 1,3,5,7)      │   (L in 9,11,13,15)   │(Pwr Brd)      │
├──────────┼────────────────────────┼────────────────────────┤               │
│  O-bot   │         1-bot          │         2-bot          │               │
│  4 jacks │        4 jacks         │        4 jacks         │               │
│ (R outs) │    (R in 2,4,6,8)      │   (R in 10,12,14,16)  │               │
└─────────────────────────────────────────────────────────────────────────────┘
              ← outputs                    inputs →
```

The PWR USB-C receptacle mounts on the **Power Board** — a small dedicated PCB on the far right of the back panel. Labeled "PWR" (power only, 5V/5A PD). A 2-pin cable carries 5V + GND from the Power Board to the Main Board. An **off-the-shelf screw-collar momentary push button** ("POWER") mounts next to the PWR USB-C on the back panel, wired to the Main Board soft-latch circuit. The **PC USB-C** (data only, 24-in/8-out USB Audio Class 2 + MIDI composite via XMOS XU216) is on the **top panel** (left zone, Main Board mount). The three mother+daughter pairs tile across the remaining back panel width.

------

## Design Reuse Opportunities

1. **Input mother boards (1-top, 2-top):** Same PCB. Codec I2C addresses set by solder jumpers. Output analog section on Board 1-top populated; on Board 2-top left empty.
2. **All daughter/output boards (1-bot, 2-bot, O-top, O-bot):** Potentially same PCB if connector placement and jack spacing match. All are 4× TS jacks + ESD + one connector. Worth investigating during schematic phase — could reduce unique designs from 6 to 4 (Main, IO, Input Mother, Universal Daughter, Key).
3. **Key PCB** and **IO Board** are standalone custom designs with no reuse opportunities. The **Power Module** is an off-the-shelf STUSB4500 breakout (no custom PCB). The **headphone amp** is an off-the-shelf TPA6132 or MAX97220 breakout module.

------

## Mechanical Mounting

- **Main Board:** Screwed to top panel via standoffs (M3 or M2.5). Board hangs below top panel, components protrude through panel cutouts.
- **IO Board:** Screwed to top panel via standoffs (M3 or M2.5), left side. Panel-mount components (USB-A, RJ45, MIDI jacks, headphone output, volume pot) protrude through top panel cutouts. Connected to main board via 12-pin FFC + 6-pin Ethernet ribbon cable.
- **I/O Boards (Mother, Daughter, Output):** Mechanically held by panel-mount jack nuts — the 1/4" TS jacks thread through back panel holes and their nuts clamp the boards to the panel. No additional standoffs needed.
- **Power Module:** Off-the-shelf STUSB4500 breakout, secured to back panel by USB-C jack nut or adhesive standoff.
- **Key PCB:** Mounted to top panel via standoffs or snap-fit clips. CHOC switches protrude through top panel cutouts, keycaps sit flush with panel surface.
