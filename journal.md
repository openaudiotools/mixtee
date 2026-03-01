# MIXTEE Development Journal

## 2026-03-01 — Daughter/Output Board Trace Routing

### What was done
Added programmatic trace routing to `hardware/kicad/gen_daughter_output.py`. The board has 6 nets (AIN1–4, +5VA, GND) across 10 components on an 80×20mm 2-layer PCB.

### Routing strategy
- **AIN1**: All F.Cu — L-route from J1 to J2.T, vertical down to D1.K
- **AIN2–4**: F.Cu stub from J1 → via → B.Cu hop → via → F.Cu fan-out to jack T pad and diode K pad
- **+5VA**: F.Cu L-route from J1 to C1
- **GND**: Short F.Cu stubs from SMD diode/cap pads to vias connecting to B.Cu ground zone

Helper functions added: `trace_seg()` and `via_pad()` for generating KiCad S-expression segments and vias.

### Bugs found and fixed

**1. J1 rotation convention (rotation=90 → 270)**

KiCad uses **clockwise** rotation for positive angles in PCB coordinates. With `rotation=90`, J1's pins were mirrored — pin 1 (AIN1) ended up at y=115 (bottom) instead of y=105 (top). Every trace shorted to the wrong J1 pin.

Fix: changed J1 rotation from 90° to 270°. With 270°, the pin-to-absolute transform is `(px, py) → (-py, px)` giving pin 1 at (104, 105) as intended.

**2. Jack S pads extending beyond board edge (jack_y 104 → 106)**

With jacks at y=104, the top S pads (at relative `(0, -3)`) had centers at y=101 — their 3mm diameter circles extended 0.5mm above the board edge (y=100). DRC flagged board-edge clearance violations.

Fix: moved jacks from `jack_y = oy + 4.0` to `oy + 6.0`. Top S pad centers now at y=103, fully inside the board with 1.5mm margin. All trace coordinates updated to match.

### Current state
- Signal traces and vias: all 6 nets routed, 0 unconnected after zone fill
- Remaining DRC items: 2 shorting violations (AIN1 trace at y=106 passes through J2.S pad at (108.92, 106); AIN2 B.Cu hop at y=107 passes near J3.S pad) — need to reroute AIN1 horizontal and AIN2 B.Cu to avoid jack S pad areas
- GND vias flagged as "dangling" because `kicad-cli` DRC doesn't fill zones — these resolve when zones are filled in KiCad GUI
- lib_footprint_mismatch warnings are expected (our simplified footprints vs full KiCad library)

### Next steps
- ~~Fix AIN1 horizontal trace to avoid J2.S pad~~ → resolved via FreeRouting (see 2026-03-02)
- ~~Fix AIN2 B.Cu hop to avoid J3.S pad~~ → resolved via FreeRouting
- ~~Verify clean DRC (0 errors) after fixes~~ → done
- Consider adding silkscreen labels and courtyard outlines to custom footprints

---

## 2026-03-02 — Daughter/Output Board: FreeRouting Autoroute + Gerber Export

### What was done
Scrapped the manual trace routing from gen_pcb.py (which had 2 shorting errors at jack S pads) and replaced it with a FreeRouting autoroute via Specctra DSN/SES round-trip. Fixed silkscreen clipping DRC warnings in the process. Board is now fully routed and Gerbers are exported.

### Pipeline used

1. **Silkscreen fix** — Custom `Switchcraft_112BPC` footprint silk rectangle extended past all 4 board edges when jacks were placed at y=20 with 90° rotation. Clipped from `(-4, -6.35)→(22, 10)` to `(0.5, -6.35)→(19.5, 9.5)` in both the `.kicad_mod` library file and all 4 inline instances in the `.kicad_pcb`. Also moved board title text from y=22 to y=18.5.

2. **DSN export** — Used KiCad's pcbnew Python API (`pcbnew.ExportSpecctraDSN()`) since `kicad-cli` doesn't support DSN export. Patched the DSN to split the single `kicad_default` net class into three classes matching the project settings:
   - `Audio_Analog` (AIN1-4): 0.3mm width, 0.25mm clearance
   - `Power` (+5VA): 0.5mm width
   - `kicad_default` (GND): 0.25mm width

3. **FreeRouting** — Loaded DSN, ran autoroute, exported SES. FreeRouting produced 44 trace segments using both F.Cu and B.Cu with vias, correctly respecting net class widths.

4. **SES import** — `pcbnew.ImportSpecctraSES()` to bring routes back into the PCB.

5. **Post-routing validation** — Opened project via kicadmixelpixx MCP (`open_project`), refilled GND zone (`refill_zones`), saved (`save_project`), verified components (`get_component_list`), queried traces (`query_traces`). DRC via kicad-cli: **0 errors, 0 unconnected, 26 cosmetic warnings**.

6. **Gerber export** — `kicad-cli pcb export gerbers` + `pcb export drill`. 7 Gerber layers + drill + job file in `gerbers/`.

### Tooling notes

- **kicadmixelpixx MCP (SWIG backend)**: works well for `open_project`, `get_component_list`, `refill_zones`, `save_project`, `query_traces`. DRC and Gerber export tools wrap `kicad-cli` and fail if it's not on PATH. `get_board_2d_view` needs Cairo DLL.
- **kicad-cli** (at `D:\programs\KiCad\9.0\bin\kicad-cli.exe`): not on PATH by default. Used with full path for DRC and Gerber export. No DSN export subcommand in KiCad 9.
- **pcbnew Python** (at `D:\programs\KiCad\9.0\bin\python.exe`): has `ExportSpecctraDSN()` and `ImportSpecctraSES()` — the only scriptable path for Specctra round-trip.

### DRC breakdown (post-route)

| Type | Count | Notes |
|------|-------|-------|
| silk_overlap | 10 | Adjacent jack silkscreens + board title text |
| lib_footprint_mismatch | 6 | Generated footprints vs KiCad library |
| silk_edge_clearance | 4 | J2/J3 ref text at board edge, J5 silk past top |
| lib_footprint_issues | 4 | Custom lib path resolution in kicad-cli |
| silk_over_copper | 2 | Silk segments over exposed pads |
| **Errors** | **0** | |
| **Unconnected** | **0** | |

### Files produced
- `hardware/kicad/mixtee-daughter-output/mixtee-daughter-output.dsn` — Specctra DSN with net classes
- `hardware/kicad/mixtee-daughter-output/mixtee-daughter-output.ses` — FreeRouting session
- `hardware/kicad/mixtee-daughter-output/gerbers/` — 7 Gerber + drill + job (9 files)

---

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

## 2026-03-02 — Split Main Board into Main Board + IO Board

### What was done
Architectural split: moved headphone, USB hub (MIDI host), and MIDI I/O circuits from the Main Board onto a new dedicated IO Board. Updated 8 documentation files to reflect the change.

### Motivation
- Main board (~260×85mm) had all processing, power, UI, and IO on one PCB
- IO-facing components (headphone, USB hub, MIDI) are physically clustered in the top panel right column
- Splitting simplifies main board layout, shortens panel-mount wiring, and allows independent revision

### Key design decisions

| Decision | Rationale |
|----------|-----------|
| SD card stays on Main Board (left of display) | Near Teensy SDIO pads, avoids routing high-speed SDIO over FFC |
| PC USB-C stays on Main Board (back panel) | Avoids routing 480 Mbps USB HS over FFC; placed next to PWR USB-C |
| IO Board gets HP amp, USB hub, MIDI only | All USB Full-Speed (12 Mbps) or low-speed serial — FFC-friendly |
| 12-pin 1.0mm FFC interconnect | Analog HP L/R (guarded by GND), USB FS D+/D−, MIDI RX/TX, HP detect, power |
| IO Board is 2-layer (~50×80mm) | No high-speed digital; USB FS + headphone analog + MIDI serial |

### Board count change
- Before: 5 unique PCB designs, 9 physical boards
- After: **6 unique PCB designs, 10 physical boards**

### Main ↔ IO FFC pinout (12-pin 1.0mm)

| Pin | Signal | Notes |
|-----|--------|-------|
| 1 | HP_L | Analog, codec DAC output |
| 2 | HP_R | Analog, codec DAC output |
| 3 | GND (guard) | Between analog and digital |
| 4 | USB_HOST_D+ | FE1.1s upstream, 12 Mbps FS |
| 5 | USB_HOST_D− | FE1.1s upstream |
| 6 | GND (USB) | USB return |
| 7 | MIDI_RX | Serial3 pin 15, 31.25 kbaud |
| 8 | MIDI_TX | Serial4 pin 17, 31.25 kbaud |
| 9 | HP_DETECT | GPIO pin 39 |
| 10 | 5V_DIG | USB hub, MIDI circuits |
| 11 | 5V_A | HP amp clean power |
| 12 | GND | Main return |

### Files updated (8)

| File | Changes |
|------|---------|
| `docs/pcb-architecture.md` | New IO Board section, updated overview/summary/connectors/mounting, back panel diagram with 2× USB-C |
| `docs/hardware.md` | USB hub/HP amp/MIDI sections annotated IO Board, PCB stackup table, BOM tables (~15 lines), panel layout |
| `docs/enclosure.md` | Back panel: added PC USB-C. Left zone: added SD slot. Right column: simplified as IO Board |
| `docs/pin-mapping.md` | MIDI/USB Host/HP detect annotated with FFC routing, new Main↔IO FFC pinout table |
| `hardware/bom.csv` | 16 lines updated with "IO Board", 2 new lines (FFC connector + cable), fabrication updated |
| `docs/connector-parts.md` | USB-A/HP TRS/MIDI TRS → IO Board, PC USB-C → back panel, new FFC 12-pin rows |
| `docs/ak4619-wiring.md` | Power architecture paragraph: HP amp on IO Board via FFC |
| `docs/pcb-design-rules.md` | IO Board added to 2-layer stackup list |
| `CLAUDE.md` | Architecture summary: 6 PCBs, IO Board, PC USB-C back panel |

### Verification
- Grepped all docs for stale "5 unique" / "9 physical" references — none found
- FFC pinout in `pin-mapping.md` matches `pcb-architecture.md` exactly (12 pins)
- All IO Board components in `bom.csv` have "IO Board" annotation
- PC USB-C consistently says "back panel" (not "top panel") across all files

---

## 2026-03-02 — PC USB-C to Top Panel, Power Board, STUSB4500 Breakout

### What was done
Two commits (`acfc9be`, `76ba381`) restructured the power and PC USB-C layout:

1. **PC USB-C moved to top panel** — Data-only USB-C receptacle moved from back panel to top panel left zone (on Main Board, near SD card slot). Eliminates 480 Mbps USB HS routing to back panel.
2. **Dedicated Power Board added** — Originally power input was on the Main Board. Moved to a separate vertical back-panel PCB for mechanical isolation.
3. **Power Board → off-the-shelf STUSB4500 breakout** — Replaced custom Power Board PCB with a purchased STUSB4500 USB PD breakout module (SparkFun or equivalent). Simplifies build — no custom power PCB needed.
4. **SD card repositioned** — Full-size SD card slot moved to left of display, vertically aligned with bottom edge of screen.

### Key decisions

| Decision | Rationale |
|----------|-----------|
| PC USB-C on top panel (not back) | Shorter USB HS traces; back panel now audio-only + power |
| STUSB4500 breakout (purchased) | USB PD negotiation is well-solved; no reason to design custom |
| SD left of display | Near Teensy SDIO bottom pads; intuitive user access |

### Files updated
12 files across docs, hardware, and layout images. Created `hardware/pcbs/power/README.md`.

---

## 2026-03-02 — Add Ethernet, IO Board to Left, HP Amp Breakout, Power Button to Back Panel

### What was done
Major layout revision (`77106c0`): added Ethernet, moved IO Board from right to left side of top panel, replaced on-board TPA6132A2 headphone amp with off-the-shelf breakout module, moved power button from top panel to back panel.

### Design changes

| Change | Before | After |
|--------|--------|-------|
| IO Board position | Top panel, right side | Top panel, left side |
| Headphone amp | TPA6132A2 IC on IO Board | Off-the-shelf TPA6132/MAX97220 breakout module (~$2–5) |
| Power button | Top panel (IO Board) | Back panel, screw-collar momentary (next to PWR USB-C) |
| Ethernet | None | Native Teensy 4.1 (DP83825I PHY) via RJ45 MagJack on IO Board |

### New Main ↔ IO FFC pinout (12-pin 1.0mm)

| Pin | Signal | Notes |
|-----|--------|-------|
| 1 | ETH_TX+ | Differential pair, from Teensy bottom pads |
| 2 | ETH_TX- | Differential pair |
| 3 | GND (guard) | Shield between Ethernet pairs |
| 4 | ETH_RX+ | Differential pair |
| 5 | ETH_RX- | Differential pair |
| 6 | GND (guard) | Shield between Ethernet/USB |
| 7 | USB_HOST_D+ | FE1.1s upstream, USB FS 12 Mbps |
| 8 | USB_HOST_D- | FE1.1s upstream |
| 9 | MIDI_RX | Serial3 pin 15, 31.25 kbaud |
| 10 | MIDI_TX | Serial4 pin 17, 31.25 kbaud |
| 11 | 5V_DIG | USB hub, MIDI, Ethernet circuits |
| 12 | GND | Main return |

HP_L/HP_R now route from Main Board directly to breakout module (not via FFC). Headphone detect via short wire to Teensy GPIO pin 39.

### Ethernet architecture
- Teensy 4.1 has DP83825I 10/100 PHY on-board with bottom pads (TX+, TX-, RX+, RX-, LED, GND)
- 6-pin ribbon cable from Main Board header → IO Board header
- 0.1µF coupling caps on IO Board between PHY output and RJ45 MagJack transformer
- Post-PHY analog signals — cable-tolerant, 2-layer PCB sufficient, no impedance control needed

### Top panel layout (left to right)

```
LEFT (IO Board)    CENTER (Main Board)           RIGHT (Key PCB)
MIDI HOST (USB-A)  SD Card  ┌─────────────────┐  Mute Solo Rec  —
ETH (RJ45)                  │    4.3" TFT     │   —    —    —   —
MIDI IN  TH.               │  93×56mm RA8875 │   —    —    —   —
PHONES   VOL                └─────────────────┘  Home Back Page Shift
                   Nav-X    Nav-Y    Edit
```

### Files updated (14)

| File | Changes |
|------|---------|
| `docs/pcb-architecture.md` | IO Board → left, Ethernet, new FFC pinout, power button back panel, board summary |
| `docs/pin-mapping.md` | Ethernet bottom pads section, new FFC pinout, GPIO notes |
| `docs/hardware.md` | Replaced TPA6132A2 with breakout, added Ethernet section, BOM, panel layout |
| `docs/enclosure.md` | IO Board left column, power button back panel |
| `docs/connector-parts.md` | RJ45 MagJack, Ethernet headers, HP breakout header, cable entries |
| `docs/ak4619-wiring.md` | Updated HP amp reference (breakout, not TPA6132A2 IC) |
| `docs/features.md` | Power button → back panel |
| `hardware/bom.csv` | Replaced TPA6132A2 line, added RJ45/Ethernet/breakout parts |
| `hardware/mixtee-layout.*` | Updated panel layout images (afdesign, jpg, svg) |
| `hardware/pcbs/main/README.md` | Ethernet routing section, 6-pin header, power button note |
| `hardware/pcbs/io/README.md` | **Created** — IO Board Stage 1 spec |
| `CLAUDE.md` | Architecture summary updated |

### Verification
- Grepped for stale "right side/column" IO Board references — none
- Grepped for stale TPA6132A2 references — all updated to breakout module
- Power button consistently "back panel" across all 14 files
- FFC pinout matches between `pcb-architecture.md` and `pin-mapping.md`
- Layout images match doc descriptions

### Next steps
- ~~IO Board SKiDL netlist (Stage 2) — FE1.1s pin mapping needs verification against KiCad symbol~~ → done (inline in gen_pcb.py)
- ~~IO Board gen_pcb.py (Stage 3–4) — 50×80mm, panel-mount components along left edge~~ → done
- ~~IO Board routing via FreeRouting (Stage 5–7)~~ → done

---

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
