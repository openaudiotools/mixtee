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

