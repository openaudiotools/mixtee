## PCB Design Agent Instructions

You are assisting with a DIY electronics project consisting of multiple small PCB modules connected by flexible cables. Each module contains an assortment of ports, keys, and chips. Your goal is to produce KiCad-ready PCB files that pass DRC and are ready for fabrication after a human review. Follow this staged pipeline strictly — never skip stages or jump directly to geometry generation.

***

### Your Core Constraint

**Never generate raw `.kicad_pcb` coordinates or geometry directly.** You lack reliable spatial reasoning for constraint satisfaction. Instead, produce structured intermediate representations that deterministic tools finalize. All placement must flow from explicit text constraints you define first.

***

### MCP Server Configuration

Two KiCad MCP servers should be running simultaneously — one for generation, one for analysis. Add both to your `.claude/mcp.json` or `claude_desktop_config.json`:

#### kicadmixelpixx
**mixelpixx/KiCAD-MCP-Server** — generation, placement, routing, DRC, Gerber export (52 tools, requires KiCad 9.0+):
```
https://github.com/mixelpixx/KiCAD-MCP-Server
```

#### kicadseed
**Seeed-Studio/kicad-mcp-server** — schematic analysis, netlist reading, pin tracing, design review:
```
https://github.com/Seeed-Studio/kicad-mcp-server
```

**Prefer MCP tools over raw Python/CLI whenever possible.** MCP calls are visible to the user, easier to review, and keep the workflow reproducible. Only fall back to pcbnew Python or kicad-cli when MCP tools lack the capability (e.g. Specctra DSN export) or fail due to backend limitations (e.g. Gerber export via SWIG).

Use them as follows across the pipeline:
- **Stages 1–3** (spec + SKiDL + ERC): no MCP needed, pure Python
- **Stage 4** (placement): use `mixelpixx` to place components, read board state, verify positions
- **Stage 5** (feedback loop): use `seeed-studio` to trace nets and verify connector pinouts; use `mixelpixx` for DRC, component queries, zone operations
- **Stage 6** (routing): FreeRouting via DSN/SES round-trip (see Stage 6 below). Use `mixelpixx` for post-routing zone refill, trace queries, and validation
- **Stage 7** (Gerber export + DRC): use `mixelpixx` first; fall back to kicad-cli if MCP fails

When MCP tools return errors, always trace the error back to its origin stage and fix there — never patch geometry downstream.

***

### Stage 1: Define Board Modules as Structured Specs

Before writing any code, produce a markdown specification for each board module containing:

- **Board dimensions** (mm) and shape
- **Connector positions**: which edge, distance from corner, orientation (facing in/out/up/down)
- **Functional zones**: e.g. "power block: top-left 10×10mm", "MCU: center", "buttons: bottom row"
- **3D constraints**: clearance from edges, component height limits, any keep-out zones
- **Flex cable interface**: which connector footprint, pin count, pitch

Do not proceed to Stage 2 until this spec is complete and logically consistent. Ask clarifying questions if constraints are ambiguous.

***

### Stage 2: Generate SKiDL Netlists (Not Geometry)

Use **SKiDL** (Python KiCad netlist library) to define each board module. SKiDL maps directly to KiCad footprints and symbols and is text-native — you can reason about it reliably.

For each module:

```python
from skidl import *

# Define components with explicit KiCad footprint references
mcu = Part('MCU_Microchip_ATmega', 'ATmega328P-AU',
           footprint='Package_QFP:TQFP-32_7x7mm_P0.8mm')

# Assign nets explicitly — never leave pins unconnected unless intentional
vcc = Net('VCC')
gnd = Net('GND')

# Connect with named nets, not positional
mcu['VCC'] += vcc
mcu['GND'] += gnd
```

Rules:
- Every power pin must be connected to a named net
- Every connector pin must be named to match its flex cable counterpart on the mating board
- Use `SKIDL` `ERC()` call at the end of every module file to catch errors before export

***

### Stage 3: Run ERC and Fix Before Proceeding

After generating each SKiDL file, run:

```bash
python module_name.py  # runs ERC() internally
```

Feed any ERC errors back to yourself. Fix all errors before exporting the netlist. Do not proceed to layout with a failing ERC. Common errors to watch for:
- Unconnected power pins
- Missing decoupling caps on VCC pins (flag as warning, ask user)
- Mismatched flex connector pinouts between mating boards

***

### Stage 4: Placement via KiCad Python API (Not Manual Coordinates)

Do not guess component XY coordinates. Instead, write a KiCad Python placement script that implements your Stage 1 spec programmatically:

```python
import pcbnew

board = pcbnew.LoadBoard("module.kicad_pcb")

# Place by functional group, anchored to board edges
def place_near_edge(ref, edge='bottom', offset_x=5, offset_y=2):
    fp = board.FindFootprintByReference(ref)
    board_bbox = board.GetBoardEdgesBoundingBox()
    if edge == 'bottom':
        y = board_bbox.GetBottom() - pcbnew.FromMM(offset_y)
    x = board_bbox.GetLeft() + pcbnew.FromMM(offset_x)
    fp.SetPosition(pcbnew.VECTOR2I(x, y))

place_near_edge('J1', edge='bottom', offset_x=5, offset_y=3)
pcbnew.Refresh()
board.Save("module_placed.kicad_pcb")
```

Key rules:
- **Always derive positions from `board.GetBoardEdgesBoundingBox()`** — never hardcode absolute coordinates. This is what prevents pads being placed outside the board.
- Place connectors first (they are your fixed anchors), then route functional groups around them
- After placement, run `pcbnew.DRC()` programmatically and output results to a log file

***

### Stage 5: Use the KiCad MCP Server for Feedback Loop

Use the **Seeed-Studio MCP server** to:
- Read back the current board state after each placement script
- Trace pin-level connections and verify nets are intact
- Confirm flex connector pinouts match their mating board counterparts

Use the **mixelpixx MCP server** to:
- Run DRC and receive structured results
- Identify specific footprint references with violations and fix them in the placement script
- Iterate until DRC passes with zero errors (warnings are acceptable if documented)

If MCP is not available, output DRC results as JSON and paste them back to continue the loop.

***

### Stage 6: Routing via FreeRouting (Specctra DSN/SES Round-Trip)

Do not attempt to hand-route traces programmatically — constraint satisfaction over complex pad geometries is error-prone and produced shorting violations on the daughter/output board. Use FreeRouting autoroute instead.

#### 6a. Export Specctra DSN

KiCad 9 CLI does not support DSN export. Use pcbnew Python:

```python
import pcbnew
board = pcbnew.LoadBoard("module_placed.kicad_pcb")
pcbnew.ExportSpecctraDSN(board, "module_placed.dsn")
```

**KiCad Python location (Windows):** `D:\programs\KiCad\9.0\bin\python.exe`

#### 6b. Patch net classes in the DSN

The DSN export puts all nets into a single `kicad_default` class. If you have custom net classes (e.g. Audio_Analog, Power), edit the DSN `(network)` section to split them:

```
(class Audio_Analog AIN1 AIN2 AIN3 AIN4
  (circuit (use_via "Via[0-1]_600:300_um"))
  (rule (width 300) (clearance 250))
)
(class Power +5VA
  (circuit (use_via "Via[0-1]_600:300_um"))
  (rule (width 500) (clearance 200))
)
```

Width/clearance units are micrometers in the DSN format.

#### 6c. Run FreeRouting

1. Open the `.dsn` in FreeRouting
2. Click **Autoroute**
3. **File → Export Specctra Session File** → save as `.ses` in the same directory

#### 6d. Import SES back into KiCad

```python
import pcbnew
board = pcbnew.LoadBoard("module_placed.kicad_pcb")
pcbnew.ImportSpecctraSES(board, "module_placed.ses")
pcbnew.SaveBoard("module_placed.kicad_pcb", board)
```

#### 6e. Post-routing via MCP

Use `kicadmixelpixx` MCP tools (SWIG backend):

1. `open_project` — reload the board
2. `refill_zones` — fill copper zones over new traces
3. `save_project` — write changes
4. `query_traces` — verify trace count and net coverage
5. `get_component_list` — sanity-check component positions

Then run DRC via kicad-cli (full path if not on PATH):

```bash
kicad-cli pcb drc --format json --severity-all --units mm \
  -o drc-report.json module_placed.kicad_pcb
```

Target: **0 errors, 0 unconnected items.** Cosmetic warnings (silk overlap, lib mismatch for generated footprints) are acceptable.

***

### Stage 7: Gerber Export + Pre-Handoff Checklist

#### Export Gerbers and drill files

```bash
kicad-cli pcb export gerbers \
  -l "F.Cu,B.Cu,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts" \
  --subtract-soldermask \
  -o ./gerbers/ module_placed.kicad_pcb

kicad-cli pcb export drill \
  -o ./gerbers/ module_placed.kicad_pcb
```

This produces 7 Gerber layers + drill file + job file. The `--subtract-soldermask` flag prevents silk printing over exposed pads.

Note: the `kicadmixelpixx` MCP `export_gerber` tool reports success via SWIG but may produce empty files — use kicad-cli directly for reliable output.

#### Checklist

Before flagging a board as "ready for review," confirm all of the following:

- [ ] ERC passes with 0 errors on SKiDL netlist
- [ ] All pads are within board outline
- [ ] All flex connector footprints match their mating board counterpart (pin-for-pin)
- [ ] DRC passes with 0 errors, 0 unconnected after routing + zone fill
- [ ] 3D clearances noted in Stage 1 spec are respected
- [ ] Gerbers + drill file generated and visually spot-checked
- [ ] PDF exports generated for all copper + silkscreen layers
- [ ] Board README updated with final status

***

### Stage 8: PDF Export for Review

Generate per-layer PDF exports so contributors can review the board without installing KiCad.

```bash
kicad-cli pcb export pdf \
  -l "F.Cu,B.Cu,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts" \
  --drill-shape-opt 2 \
  -o ./module_placed.pdf module_placed.kicad_pcb
```

This produces a multi-page PDF with one page per layer. The `--drill-shape-opt 2` flag renders drill holes at their actual size for accurate visual inspection.

For 4-layer boards, include inner layers:

```bash
kicad-cli pcb export pdf \
  -l "F.Cu,In1.Cu,In2.Cu,B.Cu,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts" \
  --drill-shape-opt 2 \
  -o ./module_placed.pdf module_placed.kicad_pcb
```

Place the PDF in the board's directory alongside the Gerbers (e.g. `hardware/pcbs/key/mixtee-key-pcb.pdf`). Commit it to the repo so reviewers can open it directly on GitHub.

***

### Error Handling Protocol

When any stage produces an error:
1. Parse the error message for the specific reference, net, or coordinate causing it
2. Trace it back to its origin stage (spec → SKiDL → placement script)
3. Fix at the origin, not downstream
4. Re-run all subsequent stages from the fix point forward
5. Never patch geometry errors by adjusting coordinates manually — fix the constraint logic

***

This pipeline applies to every board module independently. Treat flex cable connectors as a shared interface contract — both mating boards must agree on connector footprint, pin assignment, and orientation before either board proceeds past Stage 2.

***

### Appendix: Tooling Reference (Windows)

| Tool | Path | Notes |
|------|------|-------|
| kicad-cli | `D:\programs\KiCad\9.0\bin\kicad-cli.exe` | Not on PATH by default. Used for DRC, Gerber/drill export. No DSN export. |
| pcbnew Python | `D:\programs\KiCad\9.0\bin\python.exe` | Has `pcbnew.ExportSpecctraDSN()` / `ImportSpecctraSES()`. Only scriptable Specctra path. |
| kicadmixelpixx MCP | SWIG backend | Reliable for: `open_project`, `get_component_list`, `refill_zones`, `save_project`, `query_traces`. DRC/Gerber tools wrap kicad-cli (fail if not on PATH). `get_board_2d_view` needs Cairo. |
| kicadseed MCP | — | Schematic analysis, net tracing, design review. |
| FreeRouting | External GUI | Load `.dsn`, autoroute, export `.ses`. |

#### Known gotchas

- **DSN net classes**: `pcbnew.ExportSpecctraDSN()` dumps all nets into one class. Patch the DSN manually before loading into FreeRouting.
- **Silkscreen on edge-mount parts**: Custom footprints for panel-mount jacks need silk clipped to board interior. Calculate global bounds using KiCad's CW rotation: `global_x = origin_x + local_y`, `global_y = origin_y - local_x`.
- **MCP Gerber export**: Reports success but may write empty files via SWIG backend. Always use kicad-cli.
- **Zone fill for DRC**: `kicad-cli drc` does not fill zones before checking. Run `refill_zones` via MCP or pcbnew Python first, save, then run DRC.