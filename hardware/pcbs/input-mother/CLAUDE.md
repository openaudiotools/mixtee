# Input Mother Board — Agent Context Guide

## Required Reading
- `README.md` — board concept, dimensions, key ICs
- `connections.md` — connector interfaces (FFC, JST, jacks)
- `architecture.md` — analog stage design, isolated power (post-filter + ADP7118 LDO), MCP23008 + TS5A3159 mute control (Board 1-top only), I2C addressing, HP amp cable connector
- `ak4619-wiring.md` — AK4619VN codec pin table, I2C, TDM, registers
- `docs/system-topology.md` — system overview and board summary

## On Demand
- `docs/pcb-design-rules.md` — when doing layout/routing/DRC
- `docs/pcbs-workflow.md` — when running the design pipeline

## Do NOT Read (irrelevant to this board)
- `hardware/pcbs/io/architecture.md` — IO Board circuits
- `hardware/pcbs/key/architecture.md` — Key PCB matrix design
- `hardware/pcbs/main/architecture.md` — Main Board power/mux circuits
- `docs/ui-architecture.md` — display/UI hierarchy
- `docs/usb-audio.md` — USB audio details
- `docs/firmware.md` — software architecture

## Key Context
- This board is in the **galvanically isolated analog domain** (GND_ISO). All power comes from MEJ2S0505SC isolated DC-DC on Main Board via FFC.
- **Board 1-top vs 2-top:** Same PCB. Board 1-top is fully populated (output analog + MCP23008 + TS5A3159 + HP cable). Board 2-top leaves output/mute/control section unpopulated.
- FFC is 20-pin (upgraded from 16-pin) with isolated signals and 7× GND_ISO return pins.

## Design Files
All KiCad files, scripts, and gerbers are in `designs/`.
