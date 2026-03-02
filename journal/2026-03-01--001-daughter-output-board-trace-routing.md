## 2026-03-01 — Daughter/Output Board Trace Routing

### What was done
Added programmatic trace routing to `hardware/pcbs/daughter-output/gen_pcb.py`. The board has 6 nets (AIN1–4, +5VA, GND) across 10 components on an 80×20mm 2-layer PCB.

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

