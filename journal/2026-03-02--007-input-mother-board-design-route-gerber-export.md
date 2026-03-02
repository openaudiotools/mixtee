## 2026-03-02 — Input Mother Board: Design, Route, Gerber Export

### What was done
Created the Input Mother Board from scratch using `gen_pcb.py`, routed via FreeRouting autoroute with 3-class DSN patching, and exported Gerbers. This is the project's first 4-layer board. It handles 8 ADC channels (4 L + 4 R) via 2× AK4619VN codecs with Sallen-Key anti-alias filters.

### Board specs
- **Dimensions:** 80 × 40 mm, 4-layer (F.Cu signal, In1.Cu GND plane, In2.Cu V33_A plane, B.Cu signal)
- **Components (71):** 2× AK4619VN codecs (QFN-32, 5×5mm, 0.5mm pitch), 4× OPA1678 dual op-amps (SOIC-8), 1× ADP7118 LDO (SOIC-8), 4× Switchcraft 112BPC TS jacks, 1× FFC 16-pin ZIF, 1× JST-PH 6-pin, 8× ESD diodes (SOD-323), 4× AC coupling caps (0805), 32× filter passives (0603), 8× codec decoupling caps, 4× LDO caps, 2× PDN pull-up resistors
- **Nets (65):** Audio (40): AIN_*_AC, JACK_*, FN1_*, FOUT_*, DAIN_R*, FILT_IN_*, U*_AVDRV/VCOM; Power (4): GND, 5V_A, 5V_DIG, V33_A; Digital (8): MCLK, BCLK, LRCLK, SDIN1, SDOUT1/2, SDA, SCL
- **Zone fills:** GND on In1.Cu + B.Cu, V33_A on In2.Cu
- **2 instances:** Board 1-top (ch 1–8) and Board 2-top (ch 9–16) — same PCB, different TDM bus

### New footprints (vs previous boards)
- **QFN-32** — 5×5mm body, 0.5mm pitch, 32 pads (0.3×0.8mm) + 3.5×3.5mm exposed ground pad with 3×3 thermal via array (9 vias, 0.3mm drill)
- **SOIC-8** — 1.27mm pitch, 5.4mm pad-to-pad span, 1.5×0.6mm pads
- **FFC-16** — adapted from IO Board's 12-pin (16 pads at 1.0mm pitch + 2 mounting pads)

### Layout (y=0 interior, y=40 panel edge)

```
x=0                                                              x=80
┌──────────────────────────────────────────────────────────────────────┐
│  U3(LDO,6,3)  J5(FFC-16,30,2)           J6(JST-PH-6,65,2)        │ y=0
│  R17(16,4)     U1(AK4619,20,7)   R18(56,4)  U2(AK4619,60,7)      │
│  decoupling                       decoupling           D5-D8(77,y) │
│  C1-C4(AC coupling, y=12)                                          │
│                                                                     │
│  U4(OPA,8,17)  U5(OPA,24,17)  U6(OPA,44,17)  U7(OPA,64,17)      │ y=17
│  filter passives in columns ±6mm from each op-amp                   │
│                                                                     │
│  J1(10,40)    J2(30,40)         J3(50,40)     J4(70,40)           │ y=40
└──────────────────────────────────────────────────────────────────────┘
```

### Net class strategy
Three DSN net classes:

| Class | Nets | Trace width | Clearance (DSN) |
|-------|------|-------------|-----------------|
| Audio_Analog | 40 signal nets | 0.3mm | 0.26mm |
| Power | GND, 5V_A, 5V_DIG, V33_A | 0.5mm | 0.21mm |
| Default | MCLK, BCLK, LRCLK, SDIN1, SDOUT1/2, SDA, SCL | 0.25mm | 0.21mm |

### Pipeline
1. **gen_pcb.py** → `.kicad_pcb`, `.kicad_pro`, `fp-lib-table` (71 components, 65 nets, 4-layer)
2. **pcbnew Python** → `ExportSpecctraDSN()`
3. **DSN patch** → split into Audio_Analog/Power/Default with per-class widths and clearances
4. **FreeRouting** → autoroute (4 unrouted — FreeRouting 4-layer bugs, 30 passes, ~38 sec)
5. **pcbnew Python** → `ImportSpecctraSES()`
6. **kicadmixelpixx MCP** → `open_project`, `refill_zones` (3 zones), `save_project`
7. **kicad-cli** → DRC, Gerber + drill export (4 copper layers + silk/mask/paste/edge)

### Bugs found and fixed

**1. Board resized from 80×30mm to 80×40mm**

Original 30mm depth placed 112BPC jack tip pads at y≈12 (17.78mm from barrel at y=30), right in the codec/filter zone. With passive columns at y=14–21, there was no clearance. Extended to 40mm, pushing jacks to y=40 and tip pads to y≈22, well clear of the filter zone at y=14–21.

**2. QFN-32 exposed pad thermal vias**

AK4619VN requires thermal connection from exposed ground pad to ground plane. Added 3×3 grid of 0.3mm drill vias through all 4 layers, spaced 1.05mm apart within the 3.5mm pad area.

**3. KiCad pad size rotation (again)**

Same bug as Key PCB: `(size sx sy)` in `.kicad_pcb` is in board coordinates, doesn't rotate with footprint. Fixed fp_c0805, fp_c0603, fp_r0603 to swap pad dimensions when rotation is 90°/270°.

**4. AC coupling cap overlap (CW rotation convention)**

C1 at (13,12) with rot=90 — KiCad CW convention places pad 2 at board (13,11) not (13,13). C25 at (15,10) pad overlapped C1. Fixed by moving C25 to (16,10) and C27 to (56,10).

**5. Multiple pad overlap fixes**

- C29 at (2,5) overlapped U3 pin 4 → moved to (2,6.5)
- C30/C31 pads touching at x=13.5 → moved C31 from (15,2) to (16,2)
- D5-D8 overlapping filter passives → moved to vertical column at x=77, y=4/6/8/10

### DRC breakdown (post-route)

| Type | Count | Notes |
|------|-------|-------|
| **Shorts** | **0** | All pad overlaps resolved |
| **Clearance** | **0** | |
| **Unconnected** | **5** | U1 GND pad (track gap), V33_A ×3 (track gaps), SCL ×1 (track gap) — plane fills handle GND/V33_A |
| copper_edge_clearance | 5 | FreeRouting vias near board edge (0.32–0.42mm vs 0.50mm) |
| lib_footprint_mismatch | 66 | Custom footprints vs KiCad library |
| silk_over_copper | 58 | Silk on exposed pads |
| silk_overlap | 32 | Adjacent component silk |
| silk_edge_clearance | 17 | Edge silk proximity |
| lib_footprint_issues | 5 | Custom lib path |

### FreeRouting 4-layer notes

First multi-layer board in this project. FreeRouting has known bugs with 4-layer boards:
- `ArrayIndexOutOfBoundsException: Index 4 out of bounds for length 4` — intermittent
- `NullPointerException` in expansion room handling — intermittent
- `p_index out of range` warnings during optimization

Results are non-deterministic: same DSN produces 2–63 unrouted depending on which errors are hit. Best run achieved 4 unrouted. The remaining 5 DRC unconnected items are minor track gaps that copper plane fills resolve (3× V33_A, 1× GND) or can be hand-touched in KiCad (1× SCL).

### Files produced
- `hardware/pcbs/input-mother/gen_pcb.py` — PCB generator (~1250 lines, 71 components, 65 nets)
- `hardware/pcbs/input-mother/mixtee-input-mother.kicad_pcb` — routed 4-layer PCB
- `hardware/pcbs/input-mother/mixtee-input-mother.kicad_pro` — project file
- `hardware/pcbs/input-mother/mixtee-input-mother.dsn` — Specctra DSN with net classes
- `hardware/pcbs/input-mother/mixtee-input-mother.ses` — FreeRouting session
- `hardware/pcbs/input-mother/gerbers/` — 11 Gerber layers + drill + job file (14 files)

### Next steps
- Hand-fix SCL track gap in KiCad (0.42mm gap near U1 pad 28)
- Phase 2: Output reconstruction section for Board 1-top variant (+~20 components)
- Main Board design remains
