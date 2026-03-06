# HP Board — Agent Context Guide

## Required Reading
- `README.md` — board concept, components, isolation context
- `connections.md` — 4-pin input cable, headphone jack, volume pot
- `architecture.md` — amp circuit, power, headphone detect routing
- `docs/system-topology.md` — system overview and board summary

## On Demand
- `hardware/pcbs/input-mother/connections.md` — Board 1-top HP cable pinout (source end)
- `hardware/pcbs/input-mother/architecture.md` — MCP23008 GPIO assignments (headphone detect)
- `docs/pcb-design-rules.md` — when doing layout/routing/DRC

## Do NOT Read (irrelevant to this board)
- `hardware/pcbs/main/architecture.md` — Main Board circuits
- `hardware/pcbs/io/architecture.md` — IO Board circuits
- `hardware/pcbs/key/architecture.md` — Key PCB matrix design
- `docs/ui-architecture.md` — display/UI hierarchy
- `docs/usb-audio.md` — USB audio details
- `docs/firmware.md` — software architecture

## Key Context
- This board is in the **galvanically isolated analog domain** (GND_ISO)
- Power and signal come from Board 1-top (Input Mother TDM1) via 4-pin JST-PH cable
- Headphone detect is read via MCP23008 on Board 1-top, NOT a direct Teensy GPIO
