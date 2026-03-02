# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Important: do NOT cd into the current doc when calling commands.

## Project Overview

MIXTEE is an open-source 16-input / 8-output digital mixer built around the Teensy 4.1. This is a **hardware-first project** currently in the design/documentation phase — no firmware code exists yet. The `firmware/` directory is a placeholder.

## Repository Structure

- `docs/` — Design specifications (the core of the project right now)
- `hardware/` — BOM (`bom.csv`), panel layout SVGs/images, reference schematics
- `firmware/` — Empty; will contain Arduino/Teensyduino code when Phase 1 begins

## Architecture at a Glance

**Audio path:** 16 analog inputs → 4× AK4619VN codecs (2 per TDM bus) → Teensy 4.1 DSP → 8 analog outputs

**I2C bus topology:** Teensy Wire (pins 18/19) → TCA9548A mux (0x70, main board) splits to codec boards; MCP23017 (0x20, Key PCB) sits upstream for key scanning.

**Key hardware ICs:** AK4619VN (codec), TCA9548A (I2C mux), MCP23017 (GPIO expander), RA8875 (TFT controller), FE1.1s (USB hub, IO Board), STUSB4500 (USB PD sink), TPS22965 (load switch). **Off-the-shelf modules:** STUSB4500 breakout (power), TPA6132/MAX97220 breakout (headphone amp).

**Connectivity:** Native Ethernet (DP83825I PHY on Teensy) via RJ45 MagJack on IO Board. USB MIDI host via FE1.1s hub (IO Board). MIDI IN/OUT via 3.5mm TRS Type A (IO Board).

**PCB architecture:** 6 unique PCB designs, 10 physical boards + 2 off-the-shelf modules — Main Board, 1× IO Board (left side of top panel), 2× Input Mother, 2× Input Daughter, 2× Output, 1× Key PCB, 1× STUSB4500 breakout (purchased), 1× HP amp breakout (purchased). PC USB-C on top panel (Main Board). PWR USB-C + POWER button on back panel. See `docs/pcb-architecture.md`.

## Key Documentation Cross-References

These docs are tightly coupled — changes in one often require updates in others:

| Topic | Primary doc | Also update |
|-------|------------|-------------|
| Pin assignments | `pin-mapping.md` | `pcb-architecture.md` (FFC pinouts), `ak4619-wiring.md` |
| Component changes | `hardware.md` (BOM tables) | `hardware/bom.csv`, `pcb-architecture.md` |
| Key PCB / UI controls | `enclosure.md`, `pin-mapping.md` | `features.md`, `hardware.md`, `pcb-architecture.md` |
| Codec wiring / I2C | `ak4619-wiring.md` | `pin-mapping.md`, `hardware.md` |
| Power budget | `hardware.md` | `bom.csv`, `enclosure.md` |

## When Editing Documentation

- **Always check cross-references.** Component quantities, pin counts, connector specs, and power figures appear in multiple files. Use grep to find all occurrences before considering a change complete.
- **`hardware/bom.csv`** and the markdown BOM tables in `hardware.md` must stay in sync.
- Vendor reference material (AK4619VN datasheets, Teensy reference cards) lives in `.reffs/` — not part of the project docs. Do not modify or reference those files directly; use `docs/ak4619-wiring.md` for codec details and `docs/pin-mapping.md` for Teensy pin info.

## Firmware (When It Exists)

- **Platform:** Arduino/Teensyduino with PJRC Audio Library
- **Audio:** Block-based DSP (128 samples @ 48 kHz = 2.67 ms blocks), runs in timer interrupt
- **Real-time constraint:** Audio callback preempts everything. No blocking operations, no long SPI transactions, no malloc in the audio path.
- **UI framework:** Hierarchical View → Page → Module → Component → Parameter model (see `docs/ui-architecture.md`)
- **Key libraries:** PJRC Audio, RA8875_t4, Adafruit NeoPixel, USBHost_t36, SdFat, Bounce, Encoder

## Licensing

Triple-licensed: MIT (firmware), CERN-OHL-P v2 (hardware), CC BY 4.0 (docs).
