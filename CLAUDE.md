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
| Power Board | `hardware/pcbs/power/` | Off-the-shelf module |

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

**Audio path:** 16 analog inputs → 4× AK4619VN codecs (2 per TDM bus) → Teensy 4.1 DSP → 8 analog outputs

**I2C bus topology:** Teensy Wire (pins 18/19) → TCA9548A mux (0x70, main board) splits to codec boards; MCP23017 (0x20, Key PCB) sits upstream for key scanning.

**Key hardware ICs:** AK4619VN (codec), XMOS XU216 (USB audio bridge — 24-in/8-out UAC2, main board), TCA9548A (I2C mux), MCP23017 (GPIO expander), FE1.1s (USB hub, IO Board), STUSB4500 (USB PD sink), TPS22965 (load switch). **Off-the-shelf modules:** STUSB4500 breakout (power), TPA6132/MAX97220 breakout (headphone amp), ESP32-S3 integrated display module (UART link to Teensy, runs LVGL).

**Connectivity:** 24-in/8-out USB Audio Class 2 via XMOS XU216 (PC USB-C on main board). Native Ethernet (DP83825I PHY on Teensy) via RJ45 MagJack on IO Board. USB MIDI host via FE1.1s hub (IO Board). MIDI IN/OUT via 3.5mm TRS Type A (IO Board).

**PCB architecture:** 6 unique PCB designs, 10 physical boards + 2 off-the-shelf modules. See `docs/system-topology.md`.

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
- **Key libraries:** PJRC Audio, Adafruit NeoPixel, USBHost_t36, SdFat, Bounce, Encoder (display handled by ESP32-S3 module via UART)

## Licensing

Triple-licensed: MIT (firmware), CERN-OHL-P v2 (hardware), CC BY 4.0 (docs).
