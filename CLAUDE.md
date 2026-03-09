# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Important: do NOT cd into the current doc when calling commands.

## Project Overview

MIXTEE is an open-source 16-input / 8-output digital mixer built around the Teensy 4.1. This is a **hardware-first project** currently in the design/documentation phase — no firmware code exists yet. The `firmware/` directory is a placeholder.

## Repository Structure

- `docs/` — System-level design specifications
- `hardware/pcbs/{board}/` — Per-board documentation + design files
  - `README.md` — Board concept (lightweight, any agent can skim)
  - `connections.md` — Connector pinouts and interface contracts
  - `architecture.md` — Deep implementation detail (circuits, registers, etc.)
  - `CLAUDE.md` — Agent guidance for that board
  - `designs/` — KiCad files, scripts, gerbers
- `hardware/lib/` — Shared KiCad footprint library
- `hardware/` — BOM (`bom.csv`), panel layout SVGs/images
- `firmware/` — Empty; will contain Arduino/Teensyduino code when Phase 1 begins

### Board Directories

| Board | Path | Status |
|-------|------|--------|
| Main Board | `hardware/pcbs/main/` | Not started |
| IO Board | `hardware/pcbs/io/` | Routed, Gerbers exported |
| Input Mother | `hardware/pcbs/input-mother/` | Routed, Gerbers exported |
| Daughter/Output | `hardware/pcbs/daughter-output/` | Routed, Gerbers exported |
| Key PCB | `hardware/pcbs/key/` | Routed, Gerbers exported |
| HP Board | `hardware/pcbs/hp/` | Not started |
| Power Board | `hardware/pcbs/power/` | Off-the-shelf module |

## Common Commands (Windows)

| Tool | Path |
|------|------|
| kicad-cli | `D:\programs\KiCad\9.0\bin\kicad-cli.exe` |
| pcbnew Python | `D:\programs\KiCad\9.0\bin\python.exe` |

```bash
# DRC check (fill zones first via MCP or pcbnew Python — kicad-cli doesn't auto-fill)
"D:\programs\KiCad\9.0\bin\kicad-cli.exe" pcb drc --format json --severity-all --units mm -o drc-report.json module.kicad_pcb

# Gerber export (2-layer board)
"D:\programs\KiCad\9.0\bin\kicad-cli.exe" pcb export gerbers \
  -l "F.Cu,B.Cu,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts" \
  --subtract-soldermask -o ./gerbers/ module.kicad_pcb

# Drill file export
"D:\programs\KiCad\9.0\bin\kicad-cli.exe" pcb export drill -o ./gerbers/ module.kicad_pcb

# PDF export for review
"D:\programs\KiCad\9.0\bin\kicad-cli.exe" pcb export pdf \
  -l "F.Cu,B.Cu,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts" \
  --drill-shape-opt 2 -o ./module.pdf module.kicad_pcb

# DSN export for FreeRouting (no CLI support — must use pcbnew Python)
"D:\programs\KiCad\9.0\bin\python.exe" -c "import pcbnew; b=pcbnew.LoadBoard('module.kicad_pcb'); pcbnew.ExportSpecctraDSN(b,'module.dsn')"
```

## MCP Servers

Two KiCad MCP servers are configured:
- **kicadmixelpixx** — generation, placement, routing, DRC, Gerber export (SWIG backend, requires KiCad 9.0+). Gerber export via MCP may produce empty files — use kicad-cli instead.
- **kicadseed** — schematic analysis, netlist reading, pin tracing, design review.

Prefer MCP tools over raw Python/CLI when possible. See `docs/pcbs-workflow.md` for the full 8-stage pipeline (spec → SKiDL → ERC → placement → feedback → routing → Gerber → PDF).

## Documentation Loading Guide

**PCB work on a specific board:**
1. Read `docs/system-topology.md` — system overview, board summary, connector summary
2. Read the target board's `README.md`, `connections.md`, `architecture.md`
3. Read `docs/pcb-design-rules.md` + `docs/pcbs-workflow.md` if doing layout/routing
4. Do NOT read other boards' `architecture.md` files

**Cross-board interface check:**
- Read the target board's `connections.md` only (~2KB) — contains the full interface contract

**Firmware work:**
- Read `docs/firmware.md` + `docs/features.md` + `docs/ui-architecture.md`
- Read `docs/hardware.md` for BOM tables and target specs
- Read `docs/pin-mapping.md` for Teensy pin assignments

**System-level hardware review:**
- Read `docs/system-topology.md` + `docs/hardware.md`

## Architecture at a Glance

**Audio path:** 16 analog inputs → 4× AK4619VN codecs (2 per TDM bus) → [galvanic isolation boundary] → Teensy 4.1 DSP → [galvanic isolation boundary] → 8 analog outputs

**Galvanic isolation:** Si8662BB digital isolators (TDM), ISO1541 isolated I2C, MEJ2S0505SC isolated DC-DC. Boundary at FFC cables between Main Board and Input Mother Boards. Digital domain (Main, IO, Key) and analog domain (Mother Boards, Daughter/Output, HP Board) share no copper.

**I2C bus topology:** Teensy Wire (pins 18/19) → TCA9548A mux (0x70, main board) → ISO1541 (per channel) → codec boards; MCP23008 (0x21, Board 1-top) controls TS5A3159 mute + codec PDN + headphone detect; MCP23017 (0x20, Key PCB) sits upstream for key scanning.

**Key hardware ICs:** AK4619VN (codec), TCA9548A (I2C mux), Si8662BB-B-IS1 (TDM isolator), ISO1541 (I2C isolator), MEJ2S0505SC (isolated DC-DC), MCP23008 (mute/PDN/HP detect, Board 1-top), MCP23017 (key matrix, Key PCB), FE1.1s (USB hub, IO Board), STUSB4500 (USB PD sink), TPS22965 (load switch). **Off-the-shelf modules:** STUSB4500 breakout (power), TPA6132/MAX97220 breakout (headphone amp, on HP Board). **Custom PCBs:** ESP32-S3 custom display PCB (WROOM-1-N16R8 + bare 4.3" 800×480 LCD; 6-pin header: UART + EN + GPIO0 boot control; runs device-agnostic LVGL display engine).

**Display engine:** ESP32-S3 custom display PCB (WROOM-1-N16R8 + bare 4.3" 800×480 LCD) is a generic widget renderer — no device-specific knowledge. Teensy loads UI layout from `ui.json` on SD card, streams binary widget commands (COBS-encoded, CRC16) over Serial1 at 921600 baud. Widget types: Container, Label, Meter, Knob, Slider, Bar, Button, Icon, Rect, Page. Touch events forwarded as coordinates. See `docs/display/protocol.md`.

**SD card update:** Single update mechanism for all firmware (Teensy + ESP32 + UI layout). User copies `/UPDATE/` folder to SD card → power on → auto-update. FlasherX for Teensy self-programming, esp-serial-flasher for ESP32 reflash via UART (pins 9/10 control EN/GPIO0). See `docs/sd-update.md`.

**Connectivity:** 16-in/8-out AES67 network audio via Ethernet (DP83825I PHY on Teensy, RJ45 MagJack on IO Board). USB MIDI host via FE1.1s hub (IO Board). MIDI IN/OUT via 3.5mm TRS Type A (IO Board). See `docs/network-connectivity.md` §9 for DAW integration.

**PCB architecture:** 7 unique PCB designs, 11 physical boards + 1 off-the-shelf power module. See `docs/system-topology.md`.

## Key Documentation Cross-References

| Topic | Primary doc | Also update |
|-------|------------|-------------|
| Pin assignments | `docs/pin-mapping.md` | Board `connections.md` files, `ak4619-wiring.md` |
| Component changes | `docs/hardware.md` (BOM tables) | `hardware/bom.csv`, board `architecture.md` |
| Key PCB / UI controls | `docs/enclosure.md`, `docs/pin-mapping.md` | `docs/features.md`, board READMEs |
| Codec wiring / I2C | `hardware/pcbs/input-mother/ak4619-wiring.md` | `docs/pin-mapping.md`, `docs/hardware.md` |
| Power budget | `docs/hardware.md` | `hardware/bom.csv`, `docs/enclosure.md` |
| Connector pinouts | Board `connections.md` files | `docs/system-topology.md` (connector summary) |
| Board definitions | Board `README.md` files | `docs/system-topology.md` (board summary) |
| Display protocol | `docs/display/protocol.md` | `docs/ui-architecture.md`, `docs/firmware.md` |
| SD card update | `docs/sd-update.md` | `docs/features.md`, `docs/firmware.md` |

## When Editing Documentation

- **Always check cross-references.** Component quantities, pin counts, connector specs, and power figures appear in multiple files. Use grep to find all occurrences before considering a change complete.
- **`hardware/bom.csv`** and the markdown BOM tables in `hardware.md` must stay in sync.
- Vendor reference material (AK4619VN datasheets, Teensy reference cards) lives in `.reffs/` — not part of the project docs. Do not modify or reference those files directly; use `hardware/pcbs/input-mother/ak4619-wiring.md` for codec details and `docs/pin-mapping.md` for Teensy pin info.
- **Per-board CLAUDE.md files** provide agent-specific guidance for each board — read them before starting board work.

## Firmware (When It Exists)

- **Platform:** Arduino/Teensyduino with PJRC Audio Library
- **Audio:** Block-based DSP (128 samples @ 48 kHz = 2.67 ms blocks), runs in timer interrupt
- **Real-time constraint:** Audio callback preempts everything. No blocking operations, no long SPI transactions, no malloc in the audio path.
- **UI framework:** Hierarchical View → Page → Module → Component → Parameter model (see `docs/ui-architecture.md`)
- **Key libraries:** PJRC Audio, Adafruit NeoPixel, USBHost_t36, SdFat, Bounce, Encoder, FlasherX (Teensy self-update), esp-serial-flasher (ESP32 reflash), ArduinoJson (ui.json parsing)

## Licensing

Triple-licensed: MIT (firmware), CERN-OHL-P v2 (hardware), CC BY 4.0 (docs).
