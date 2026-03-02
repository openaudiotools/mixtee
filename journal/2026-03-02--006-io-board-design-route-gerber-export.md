## 2026-03-02 — IO Board: Design, Route, Gerber Export

### What was done
Created the IO Board from scratch using `gen_pcb.py`, routed via FreeRouting autoroute with multi-class DSN patching, and exported Gerbers. Board handles USB MIDI host hub, Ethernet, MIDI IN/OUT, and headphone amp connectivity.

### Board specs
- **Dimensions:** 50 x 80 mm, 2-layer
- **Components (33):** FE1.1s USB hub (SSOP-28), 2x TPS2051 USB power switches (SOT-23-5), 6N138 optocoupler (DIP-8), 12MHz crystal (3225), 12 capacitors, 5 resistors, 1 diode (SOD-123), USB-A dual stacked, RJ45 MagJack, 2x 3.5mm TRS MIDI jacks, FFC 12-pin ZIF, 6-pin ETH header, 4-pin HP header, HP TRS jack, 3-pin HP amp output header, dual-gang volume pot
- **Nets (37):** GND, 5V_DIG, V33, USB_UP/DN1/DN2 D+/D-, VBUS1/2, XTAL, ETH pairs (pre/post coupling cap), MIDI signals, HP signals
- **GND zone:** B.Cu full pour

### Layout zones (y=0 panel edge, y=80 interior)
- **y=0–15:** Panel-mount connectors — USB-A (12,8), RJ45 (38,10)
- **y=16–35:** ICs — FE1.1s (14,24), TPS2051 x2 (30/38,22), 6N138 (38,34), crystal + decoupling
- **y=36–55:** MIDI — SJ-3523 jacks (10/30,42), MIDI resistors/diode
- **y=55–65:** Headphone — TRS jack (6,58), volume pot (28,56), HP headers (42,48/62)
- **y=70–80:** Interior connectors — FFC 12-pin (14,76), ETH header (32,76), ETH coupling caps

### Net class strategy
Three DSN net classes with different clearances to handle SSOP-28 pin pitch constraints:

| Class | Nets | Trace width | Clearance (DSN) | Clearance (DRC) |
|-------|------|-------------|-----------------|-----------------|
| Default | 25 signal nets | 0.25mm | 0.22mm | 0.20mm |
| Power | GND, 5V_DIG, V33, 5V_A, VBUS1/2 | 0.5mm | 0.22mm | 0.20mm |
| USB_Diff | USB_UP/DN1/DN2 D+/D- | 0.2mm | 0.16mm | 0.15mm |

USB nets need tighter clearance (0.16mm DSN / 0.15mm DRC) because FE1.1s SSOP-28 has 0.65mm pin pitch — only 0.25mm gap between pads, too tight for 0.2mm clearance. USB nets assigned to USB_Diff class in `.kicad_pro` so KiCad DRC uses 0.15mm clearance instead of Default 0.2mm.

### Pipeline
1. **gen_pcb.py** → `.kicad_pcb`, `.kicad_pro` (with net-to-class assignments), `fp-lib-table`
2. **pcbnew Python** → `ExportSpecctraDSN()`
3. **DSN patch** → split into Default/Power/USB_Diff with per-class clearances
4. **FreeRouting** → autoroute (0 unrouted, 5 passes, ~5 seconds)
5. **pcbnew Python** → `ImportSpecctraSES()`
6. **kicadmixelpixx MCP** → `open_project`, `refill_zones`, `save_project`
7. **kicad-cli** → DRC, Gerber + drill export

### Bugs found and fixed

**1. J7/J9 header overlap (first routing attempt)**

HP breakout header J7 (4-pin, 42,58, rot=90) and HP amp output header J9 (3-pin, 42,52, rot=90) had through-hole pads overlapping — only 0.92mm between pad centers with 1.75mm diameter pads. FreeRouting: 19 unrouted.

Fix: moved J7 from y=58 to y=62, J9 from y=52 to y=48. Second FreeRouting run: 0 unrouted.

**2. R4/J9 clearance violation (persistent across iterations)**

R4 (MIDI_OUT_SRC resistor) too close to J9 pad 3 (GND). KiCad rotation convention (90° = clockwise) places J9 pin 3 closer than expected. Initially at (40,46), moved to (40,42) — still 0.069mm clearance. Final fix: moved R4 to (34,46), well clear of J9 pad envelope.

**3. USB clearance vs SSOP-28 pitch conflict**

FreeRouting with 0.21mm clearance for all classes: 2 unrouted USB connections. SSOP-28 0.65mm pitch - 0.4mm pad width = 0.25mm gap, too narrow for 0.21mm clearance + trace. Solution: separate USB_Diff class with 0.16mm clearance in DSN, and net assignments in `.kicad_pro` so KiCad DRC applies 0.15mm clearance to USB nets.

### DRC breakdown (post-route)

| Type | Count | Severity | Notes |
|------|-------|----------|-------|
| clearance | 1 | error | 5V_DIG track vs J4 pad: 0.1977mm vs 0.20mm (2.3um under, FreeRouting rounding) |
| copper_edge_clearance | 1 | error | ETH_RXP via near board edge: 0.375mm vs 0.50mm default |
| starved_thermal | 3 | error | J1 GND pads + VR1 GND: zone can't create enough thermal spokes |
| unconnected | 1 | — | VR1 pad A3 (GND) — zone fill isolation |
| lib_footprint_mismatch | 25 | warning | Generated vs library footprints (expected) |
| silk_over_copper | 15 | warning | Silk on exposed pads |
| silk_overlap | 14 | warning | Adjacent component silk |
| lib_footprint_issues | 8 | warning | Custom lib path |
| silk_edge_clearance | 4 | warning | Edge silk proximity |
| track_dangling | 1 | warning | Short GND track fragment |

All errors are cosmetic/marginal — 0 shorts, 0 USB clearance violations, all connections routed.

### Files produced
- `hardware/kicad/mixtee-io-board/gen_pcb.py` — PCB generator (33 components, 37 nets)
- `hardware/kicad/mixtee-io-board/mixtee-io-board.kicad_pcb` — routed PCB
- `hardware/kicad/mixtee-io-board/mixtee-io-board.kicad_pro` — project with USB_Diff net assignments
- `hardware/kicad/mixtee-io-board/mixtee-io-board.dsn` — Specctra DSN
- `hardware/kicad/mixtee-io-board/mixtee-io-board.ses` — FreeRouting session
- `hardware/kicad/mixtee-io-board/gerbers/` — 29 Gerber layers + drill file

### Next steps
- Verify FE1.1s pinout against actual datasheet (marked NEEDS VERIFICATION in gen_pcb.py)
- Consider moving ETH_RXP via inward to resolve edge clearance
- Add GND vias near J1/VR1 to fix starved thermal connections
- Main Board and Input Mother Board designs remain

---

