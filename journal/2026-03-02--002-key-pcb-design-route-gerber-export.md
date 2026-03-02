## 2026-03-02 — Key PCB: Design, Route, Gerber Export

### What was done
Created the Key PCB from scratch using `gen_pcb.py` (programmatic KiCad S-expression generator), routed via FreeRouting autoroute, and exported Gerbers. Board is fully routed with 0 errors and 0 unconnected items.

### Board specs
- **Dimensions:** 72 × 80 mm, 2-layer (originally 72×72, extended to 80mm to fit MCP23017 in bottom strip)
- **Components (67):** 16 Kailh CHOC hotswap sockets, 16 WS2812B-2020 NeoPixels, 16 NeoPixel decoupling caps (0603), 16 1N4148 anti-ghosting diodes (SOD-123), 1 MCP23017 GPIO expander (SOIC-28), 1 MCP decoupling cap, 1 JST-PH 6-pin connector
- **Nets (45):** GND, 5V, SDA, SCL, INT, NEO_DIN, NEO_D0–D14, COL0–3, ROW0–3, SW1_D–SW16_D
- **GND zone:** B.Cu full pour

### Layout
- 4×4 switch grid at 18mm pitch, centered in upper 72×72 area
- NeoPixels + caps below each switch center (3.5mm offset)
- Diodes to the right of each switch (rightmost column rotated 90° to avoid board edge)
- MCP23017 (U1) in bottom 8mm strip at (36, 73) rotated 90°
- JST-PH connector (J1) at (5, 75)
- NeoPixel chain: serpentine order [1,2,3,4,8,7,6,5,9,10,11,12,16,15,14,13]

### Pipeline
1. **gen_pcb.py** → generates `.kicad_pcb`, `.kicad_pro`, `fp-lib-table`
2. **pcbnew Python** → `ExportSpecctraDSN()`
3. **DSN patch** → split `kicad_default` into `Default` (0.2mm trace, 0.21mm clearance) and `Power` (0.4mm trace)
4. **FreeRouting** → autoroute (139/139 connections, 8.4 seconds)
5. **pcbnew Python** → `ImportSpecctraSES()`
6. **kicadmixelpixx MCP** → `open_project`, `refill_zones`, `save_project`
7. **kicad-cli** → DRC, Gerber + drill export

### Bugs found and fixed

**1. KiCad pad `(size)` is NOT rotated by footprint rotation**

When MCP23017 was placed at 90° rotation, pads defined as `(size 1.55 0.6)` stayed 1.55mm in board X — but pins were now spaced 1.27mm in board X. Adjacent pads overlapped by 0.28mm (10 shorts, 14 clearance violations, 24 solder mask bridge errors).

Verified via pcbnew Python: `pad.GetBoundingBox()` showed 1.55mm width in board X regardless of footprint rotation. `pad.GetOrientationDegrees()` returned 0° (absolute), not 90°.

Fix: swap pad size to `(size 0.6 1.55)` when footprint rotation is 90°/270°. The `(size)` in `.kicad_pcb` S-expressions is in **board coordinates**, not the footprint's local frame — pad positions `(at)` DO transform with rotation, but `(size)` does NOT.

**2. MCP23017 placement collisions (3 iterations)**

Initially placed U1 at board center (36, 36) — pins overlapped with SW10, D10, C7. Extended board from 72×72 to 72×80mm and moved U1 to bottom strip at (36, 73) rotated 90° (pins along X axis).

**3. LED/cap placement near board edge**

Bottom row LEDs at y=70.5 (switch y=63 + 7.5mm offset) too close to y=72 edge. Reduced LED_OFFSET from (0, 7.5) to (0, 3.5).

**4. FreeRouting clearance rounding**

First FreeRouting run with 0.2mm DSN clearance produced one trace at 0.198mm from SW14 pad (0.002mm under DRC threshold). Bumped DSN clearance to 0.21mm for margin — second run passed cleanly.

### DRC breakdown (post-route)

| Type | Count | Notes |
|------|-------|-------|
| **Errors** | **0** | (1 starved_thermal on J1 GND, cosmetic) |
| **Unconnected** | **0** | All 139 connections routed |
| text_height | 49 | Generated ref text sizes |
| lib_footprint_mismatch | 35 | Custom vs library footprints |
| lib_footprint_issues | 32 | Custom lib path resolution |
| silk_over_copper | 9 | Silk on exposed pads |
| silk_overlap | 2 | Adjacent component silk |
| silk_edge_clearance | 1 | Edge silk proximity |

### Files produced
- `hardware/kicad/mixtee-key-pcb/gen_pcb.py` — PCB generator script
- `hardware/kicad/mixtee-key-pcb/mixtee-key-pcb.kicad_pcb` — routed PCB
- `hardware/kicad/mixtee-key-pcb/mixtee-key-pcb.kicad_pro` — project file
- `hardware/kicad/mixtee-key-pcb/mixtee-key-pcb.dsn` — Specctra DSN
- `hardware/kicad/mixtee-key-pcb/mixtee-key-pcb.ses` — FreeRouting session
- `hardware/kicad/mixtee-key-pcb/gerbers/` — 29 Gerber layers + drill file

### Next steps
- Add NPTH mounting holes back to CHOC socket footprints (omitted for routing)
- Consider adding courtyard outlines and silkscreen labels to custom footprints
- Review NeoPixel chain signal integrity (serpentine path lengths)

---

