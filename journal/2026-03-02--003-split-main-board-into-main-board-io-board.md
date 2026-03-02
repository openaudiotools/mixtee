## 2026-03-02 — Split Main Board into Main Board + IO Board

### What was done
Architectural split: moved headphone, USB hub (MIDI host), and MIDI I/O circuits from the Main Board onto a new dedicated IO Board. Updated 8 documentation files to reflect the change.

### Motivation
- Main board (~260×85mm) had all processing, power, UI, and IO on one PCB
- IO-facing components (headphone, USB hub, MIDI) are physically clustered in the top panel right column
- Splitting simplifies main board layout, shortens panel-mount wiring, and allows independent revision

### Key design decisions

| Decision | Rationale |
|----------|-----------|
| SD card stays on Main Board (left of display) | Near Teensy SDIO pads, avoids routing high-speed SDIO over FFC |
| PC USB-C stays on Main Board (back panel) | Avoids routing 480 Mbps USB HS over FFC; placed next to PWR USB-C |
| IO Board gets HP amp, USB hub, MIDI only | All USB Full-Speed (12 Mbps) or low-speed serial — FFC-friendly |
| 12-pin 1.0mm FFC interconnect | Analog HP L/R (guarded by GND), USB FS D+/D−, MIDI RX/TX, HP detect, power |
| IO Board is 2-layer (~50×80mm) | No high-speed digital; USB FS + headphone analog + MIDI serial |

### Board count change
- Before: 5 unique PCB designs, 9 physical boards
- After: **6 unique PCB designs, 10 physical boards**

### Main ↔ IO FFC pinout (12-pin 1.0mm)

| Pin | Signal | Notes |
|-----|--------|-------|
| 1 | HP_L | Analog, codec DAC output |
| 2 | HP_R | Analog, codec DAC output |
| 3 | GND (guard) | Between analog and digital |
| 4 | USB_HOST_D+ | FE1.1s upstream, 12 Mbps FS |
| 5 | USB_HOST_D− | FE1.1s upstream |
| 6 | GND (USB) | USB return |
| 7 | MIDI_RX | Serial3 pin 15, 31.25 kbaud |
| 8 | MIDI_TX | Serial4 pin 17, 31.25 kbaud |
| 9 | HP_DETECT | GPIO pin 39 |
| 10 | 5V_DIG | USB hub, MIDI circuits |
| 11 | 5V_A | HP amp clean power |
| 12 | GND | Main return |

### Files updated (8)

| File | Changes |
|------|---------|
| `docs/pcb-architecture.md` | New IO Board section, updated overview/summary/connectors/mounting, back panel diagram with 2× USB-C |
| `docs/hardware.md` | USB hub/HP amp/MIDI sections annotated IO Board, PCB stackup table, BOM tables (~15 lines), panel layout |
| `docs/enclosure.md` | Back panel: added PC USB-C. Left zone: added SD slot. Right column: simplified as IO Board |
| `docs/pin-mapping.md` | MIDI/USB Host/HP detect annotated with FFC routing, new Main↔IO FFC pinout table |
| `hardware/bom.csv` | 16 lines updated with "IO Board", 2 new lines (FFC connector + cable), fabrication updated |
| `docs/connector-parts.md` | USB-A/HP TRS/MIDI TRS → IO Board, PC USB-C → back panel, new FFC 12-pin rows |
| `docs/ak4619-wiring.md` | Power architecture paragraph: HP amp on IO Board via FFC |
| `docs/pcb-design-rules.md` | IO Board added to 2-layer stackup list |
| `CLAUDE.md` | Architecture summary: 6 PCBs, IO Board, PC USB-C back panel |

### Verification
- Grepped all docs for stale "5 unique" / "9 physical" references — none found
- FFC pinout in `pin-mapping.md` matches `pcb-architecture.md` exactly (12 pins)
- All IO Board components in `bom.csv` have "IO Board" annotation
- PC USB-C consistently says "back panel" (not "top panel") across all files

---

