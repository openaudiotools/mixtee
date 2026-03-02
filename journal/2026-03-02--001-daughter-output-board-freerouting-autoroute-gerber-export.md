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
- `hardware/pcbs/daughter-output/mixtee-daughter-output.dsn` — Specctra DSN with net classes
- `hardware/pcbs/daughter-output/mixtee-daughter-output.ses` — FreeRouting session
- `hardware/pcbs/daughter-output/gerbers/` — 7 Gerber + drill + job (9 files)

---

