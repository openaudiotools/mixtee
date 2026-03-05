# Main Board — Agent Context Guide

## Required Reading
- `README.md` — board concept, dimensions, key ICs
- `connections.md` — all connector interfaces (FFC, JST, USB-C, display, SD)
- `architecture.md` — soft-latch, power distribution, I2C mux, XMOS XU216 USB audio bridge, pop suppression, pin assignments
- `docs/system-topology.md` — system overview and board summary

## On Demand
- `docs/pcb-design-rules.md` — when doing layout/routing/DRC
- `docs/pcbs-workflow.md` — when running the design pipeline
- `docs/hardware.md` — BOM tables, power budget, target specs
- `docs/pin-mapping.md` — detailed Teensy pin reference
- `hardware/pcbs/input-mother/connections.md` — FFC pinout to codec boards
- `hardware/pcbs/io/connections.md` — FFC pinout to IO Board

## Do NOT Read (irrelevant to this board)
- `hardware/pcbs/input-mother/architecture.md` — analog stage design (codec board detail)
- `hardware/pcbs/input-mother/ak4619-wiring.md` — codec register config
- `hardware/pcbs/io/architecture.md` — IO Board circuits
- `hardware/pcbs/key/architecture.md` — key matrix wiring
- `docs/ui-architecture.md` — display/UI hierarchy (firmware concern)

## On Demand (XMOS-specific)
- `docs/usb-audio.md` — XMOS XU216 USB audio bridge architecture (hardware on this board)

## Design Files
No design files yet — board design not started.
