# PDF Exports for All Existing Boards

### What was done
Generated multi-layer PDF exports for all 4 completed boards using `kicad-cli pcb export pdf`. These sit next to each `.kicad_pcb` file so contributors can review layouts on GitHub without KiCad.

### Exports

| Board | Layers | Size |
|---|---|---|
| Daughter/Output (2L) | F.Cu, B.Cu, F.SilkS, B.SilkS, F.Mask, B.Mask, Edge.Cuts | 28 KB |
| Key PCB (2L) | same 7 layers | 128 KB |
| IO Board (2L) | same 7 layers | 107 KB |
| Input Mother (4L) | + In1.Cu, In2.Cu (9 layers) | 244 KB |

All exports used `--drill-shape-opt 2` (small drill marks).
