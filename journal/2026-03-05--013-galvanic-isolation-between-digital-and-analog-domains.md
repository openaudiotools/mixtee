## 2026-03-05 — Galvanic Isolation Between Digital and Analog Domains

Added galvanic isolation at the FFC boundary between Main Board (digital domain) and Input Mother Boards (analog domain). No shared copper between domains.

### Isolation Components (per FFC, ×2)

| Component | Purpose | Key Spec |
|-----------|---------|----------|
| Murata MEJ2S0505SC | Isolated DC-DC 5V→5V_ISO | 2W (400 mA), 5.2 kV, SIP-7 TH |
| Si8662BB-B-IS1 | 6-ch digital isolator (TDM) | 150 Mbps, 4 fwd + 2 rev, SOIC-16W |
| ISO1541DR | Isolated bidirectional I2C | 1 MHz, SOIC-8 |

**BOM addition:** ~$30 total (including passives and upgraded FFC connectors).

### Key Changes

| Change | Details |
|--------|---------|
| FFC 16→20 pin | 7× GND_ISO pins for low-impedance isolated return paths |
| TS5A3159 moved to Board 1-top | Output mute stays in isolated analog domain |
| MCP23008 added to Board 1-top | Controls mute (GP0-3), codec PDN (GP4-5), headphone detect (GP6); address 0x21 |
| HP Board (NEW) | Standalone headphone amp in isolated domain, powered from Board 1-top via 4-pin cable |
| HP amp removed from IO Board | IO Board now digital-only (USB hub, MIDI, Ethernet) |
| 5 Teensy GPIO pins freed | 30, 35, 37, 38 (mute), 39 (headphone detect) — now spare |
| XMOS TDM tap unchanged | Pre-isolator tap on Main Board digital side |

### Files Updated (27 files)

**Primary:** `input-mother/connections.md`, `main/connections.md`, `main/architecture.md`, `input-mother/architecture.md`, `io/architecture.md`, `io/connections.md`, `io/README.md`, `pin-mapping.md`, `hardware.md`, `system-topology.md`, `bom.csv`

**New:** `hp/README.md`, `hp/connections.md`, `hp/architecture.md`, `hp/CLAUDE.md`

**Secondary:** `pcb-design-rules.md`, `firmware.md`, `usb-audio.md`, `ak4619-wiring.md`, `enclosure.md`, `connector-parts.md`, `daughter-output/connections.md`

**CLAUDE.md files:** Root `CLAUDE.md`, `main/CLAUDE.md`, `input-mother/CLAUDE.md`, `io/CLAUDE.md`, `main/README.md`, `input-mother/README.md`

### Timing Check

BCLK = 24.576 MHz → 40.7 ns period. Si8662BB propagation ~7.5 ns. Round-trip (BCLK out + SDOUT back) ~25 ns including codec delay. Within 40.7 ns period — BB (high-speed) grade mandatory.
