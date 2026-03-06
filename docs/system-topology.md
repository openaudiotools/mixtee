# MIXTEE: System Topology

*← Back to [README](../README.md) | See also: [Hardware](hardware.md) · [Enclosure](enclosure.md)*

------

## Overview

MIXTEE uses a modular multi-board design with **galvanic isolation** between the digital and analog domains. The main board sits horizontally under the top panel and contains the isolation boundary (Si8662BB, ISO1541, MEJ2S0505SC). Six back-panel boards (three mother+daughter pairs) carry all audio I/O in the isolated analog domain. A dedicated IO board on the left side of the top panel handles Ethernet, USB MIDI host, and MIDI IN/OUT. A standalone HP Board carries the headphone amp in the isolated analog domain (powered from Board 1-top). A key PCB handles the illuminated switch grid. An off-the-shelf STUSB4500 breakout module on the back panel provides USB PD power input.

Total: **7 unique PCB designs**, 11 physical boards + 1 off-the-shelf power module.

For detailed per-board documentation, see each board's directory under `hardware/pcbs/`.

------

## Board Summary

| ID | Name | Unique design | Instances | Layers | Active components | Domain | Details |
|----|------|--------------|-----------|--------|-------------------|--------|---------|
| M | Main Board | Yes | 1 | 4 | Teensy, XMOS XU216, 2× Si8662BB + 2× ISO1541 + 2× MEJ2S0505SC (isolation), 74LVC1G00 soft-latch, ADP7118 LDO | Digital | [README](../hardware/pcbs/main/README.md) |
| IO | IO Board | Yes | 1 | 2 | FE1.1s hub, 6N138 MIDI, 2× TPS2051, RJ45 MagJack | Digital | [README](../hardware/pcbs/io/README.md) |
| P | Power Module | Off-the-shelf | 1 | — | STUSB4500 USB PD breakout (purchased) | Digital | [README](../hardware/pcbs/power/README.md) |
| HP | HP Board | Yes | 1 | 2 | TPA6132/MAX97220 breakout, volume pot, TRS jack | Analog (isolated) | [README](../hardware/pcbs/hp/README.md) |
| 1-top | Input Mother (TDM1) | Shared w/ 2-top | 1 | 4 | ADP7118 LDO, 2× AK4619VN, 8× input analog, 4× output analog, MCP23008, 4× TS5A3159 | Analog (isolated) | [README](../hardware/pcbs/input-mother/README.md) |
| 2-top | Input Mother (TDM2) | Shared w/ 1-top | 1 | 4 | ADP7118 LDO, 2× AK4619VN, 8× input analog | Analog (isolated) | [README](../hardware/pcbs/input-mother/README.md) |
| 1-bot | Input Daughter (TDM1) | Shared w/ all daughters | 1 | 2 | ESD diodes only | Analog (isolated) | [README](../hardware/pcbs/daughter-output/README.md) |
| 2-bot | Input Daughter (TDM2) | Shared | 1 | 2 | ESD diodes only | Analog (isolated) | [README](../hardware/pcbs/daughter-output/README.md) |
| O-top | Output Top | Shared (or near-identical) | 1 | 2 | ESD diodes only | Analog (isolated) | [README](../hardware/pcbs/daughter-output/README.md) |
| O-bot | Output Bottom | Shared | 1 | 2 | ESD diodes only | Analog (isolated) | [README](../hardware/pcbs/daughter-output/README.md) |
| K | Key PCB | Yes | 1 | 2 | 16× NeoPixel, 16× CHOC socket, MCP23017 | Digital | [README](../hardware/pcbs/key/README.md) |

**Unique PCB designs:** 7 (Main, IO, HP, Input Mother, Daughter/Output, Key, plus possibly a separate Output Top if connector differs) + 1 off-the-shelf power module

**Galvanic isolation boundary:** FFC cables between Main Board and Input Mother Boards. All boards downstream of the FFC (Mother, Daughter, Output, HP) run on GND_ISO with no copper connection to system GND.

------

## Connector Summary

| Connection | Type | Pitch | Pins | Cable length | Domain boundary | Pinout |
|------------|------|-------|------|-------------|----------------|--------|
| Mother ↔ Daughter (×3) | JST-PH wire harness | 2.0 mm | 6 | ~15–20 mm | — (both analog) | [daughter-output](../hardware/pcbs/daughter-output/connections.md) |
| Main ↔ Input Mother (×2) | FFC + ZIF | 1.0 mm | **20** | ~40–50 mm | **Isolation boundary** | [input-mother](../hardware/pcbs/input-mother/connections.md) |
| Main ↔ IO Board | FFC + ZIF | 1.0 mm | 12 | ~100–120 mm | — (both digital) | [io](../hardware/pcbs/io/connections.md) |
| Power Board → Main | JST-PH or screw terminal | 2.0 mm | 2 | ~60–80 mm | — | [power](../hardware/pcbs/power/connections.md) |
| 1-top → O-top | JST-PH or FFC | 2.0 / 1.0 mm | 10 | ~80 mm | — (both analog) | [input-mother](../hardware/pcbs/input-mother/connections.md) |
| 1-top → HP Board | JST-PH | 2.0 mm | 4 | ~40–60 mm | — (both analog) | [hp](../hardware/pcbs/hp/connections.md) |
| Main ↔ Key PCB | JST-PH | 2.0 mm | 6 | ~30–40 mm | — (both digital) | [key](../hardware/pcbs/key/connections.md) |
| Main ↔ Display | Per module | Varies | 8–10 | ~20 mm | — | [main](../hardware/pcbs/main/connections.md) |

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

1. **Input mother boards (1-top, 2-top):** Same PCB. Codec I2C addresses set by solder jumpers. Output analog section + MCP23008 + TS5A3159 on Board 1-top populated; on Board 2-top left empty.
2. **All daughter/output boards (1-bot, 2-bot, O-top, O-bot):** Potentially same PCB if connector placement and jack spacing match. All are 4× TS jacks + ESD + one connector. Worth investigating during schematic phase — could reduce unique designs from 7 to 5 (Main, IO, HP, Input Mother, Universal Daughter, Key).
3. **Key PCB**, **IO Board**, and **HP Board** are standalone custom designs with no reuse opportunities. The **Power Module** is an off-the-shelf STUSB4500 breakout (no custom PCB). The **headphone amp** uses an off-the-shelf TPA6132 or MAX97220 breakout module mounted on the HP Board.

------

## Mechanical Mounting

- **Main Board:** Screwed to top panel via standoffs (M3 or M2.5). Board hangs below top panel, components protrude through panel cutouts.
- **IO Board:** Screwed to top panel via standoffs (M3 or M2.5), left side. Panel-mount components (USB-A, RJ45, MIDI jacks) protrude through top panel cutouts. Connected to main board via 12-pin FFC + 6-pin Ethernet ribbon cable.
- **HP Board:** Panel-mount via headphone jack nut (top panel, left zone). Receives audio + power from Board 1-top via 4-pin JST-PH cable. Optional standoff.
- **I/O Boards (Mother, Daughter, Output):** Mechanically held by panel-mount jack nuts — the 1/4" TS jacks thread through back panel holes and their nuts clamp the boards to the panel. No additional standoffs needed.
- **Power Module:** Off-the-shelf STUSB4500 breakout, secured to back panel by USB-C jack nut or adhesive standoff.
- **Key PCB:** Mounted to top panel via standoffs or snap-fit clips. CHOC switches protrude through top panel cutouts, keycaps sit flush with panel surface.
