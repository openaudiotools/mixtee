# Consolidate `hardware/kicad/` into `hardware/pcbs/`

### What was done
Eliminated the `hardware/kicad/` directory by merging all KiCad project files into `hardware/pcbs/{board}/` alongside existing README.md files. Each board folder now has everything in one place (docs + design files + gerbers).

### Moves

| Source | Destination |
|---|---|
| `hardware/kicad/lib/` | `hardware/lib/` |
| `hardware/kicad/mixtee-daughter-output/*` | `hardware/pcbs/daughter-output/` |
| `hardware/kicad/mixtee-input-mother/*` | `hardware/pcbs/input-mother/` |
| `hardware/kicad/mixtee-io-board/*` | `hardware/pcbs/io/` |
| `hardware/kicad/mixtee-key-pcb/*` | `hardware/pcbs/key/` |

### Path updates
- **fp-lib-table** (4 files): `${KIPRJMOD}/../lib/` → `${KIPRJMOD}/../../lib/`
- **gen_pcb.py** (4 files): same fp-lib-table path fix in writer code
- **DSN files** (4 files): absolute path on line 1
- **Journal entries** (5 files): all `hardware/kicad/mixtee-*` → `hardware/pcbs/*`

### Removed
- `hardware/kicad/mixtee-power/` (empty placeholder — power board is off-the-shelf, `pcbs/power/README.md` exists)
- `hardware/kicad/` directory entirely
