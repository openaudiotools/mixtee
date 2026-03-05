# MIXTEE Enclosure

## Back Panel — Inputs + Outputs + Power

All 24 audio jacks (12 stereo pairs) on the back panel, evenly spaced in 2 rows (L top, R bottom). No physical gaps between groups — separation is by labeling only.

**PWR — USB-C (power only, USB PD):** Located on the back panel (right side, looking at back), on a dedicated **Power Board**. 5V/5A via USB PD (fallback 5V/3A), no data lines. Plug-and-forget connection to PD-capable power supply. 2-pin cable carries 5V + GND to Main Board.

**POWER button (momentary):** Off-the-shelf screw-collar panel-mount push button, located next to PWR USB-C on the back panel. Wired to Main Board soft-latch circuit (pins 40/41). Press to power on; press to cleanly shut down; long-press (>4s) for hardware failsafe power-off.

### Jack order (left to right, looking at back)

1. Master, 2. AUX1, 3. AUX2, 4. AUX3, 5. 15/16, 6. 13/14, 7. 11/12, 8. 9/10, 9. 7/8, 10. 5/6, 11. 3/4, 12. 1/2

Jack centers at x = 20, 40, 60, 80, 100, 120, 140, 160, 180, 200, 220, 240 mm from left panel edge.

### Spacing

- Jack center-to-center: **20 mm** (uniform, all 12 pairs)
- 12 pairs → 11 gaps → 11 × 20 = **220 mm** span
- End margins: **20 mm** each side
- Total width: 220 + 20 + 20 = **260 mm**

### Width conclusion

Enclosure: **260 × 100 × 50 mm** (W × D × H).

## Top Panel

Dimensions: **260 mm** wide × **84.6 mm** deep (front to back). Outputs moved to back panel — top panel is now entirely controls.

### Left zone — PC USB-C + SD + Display + Encoders (Main Board)

**PC — USB-C (data only):**
- PCB-mount USB-C receptacle on Main Board, protrudes through top panel cutout
- USB Audio Class 2 (24-in/8-out via XMOS XU216) + USB MIDI composite device
- Labeled "PC" on top panel

**SD card slot** (left of display, vertically aligned with bottom edge of screen):
- Full-size SD card socket, slot opens upward through top panel
- SDIO routed from Teensy bottom pads 42–47

**Display** (upper left, right of SD slot):
- TFT 93 × 56 mm visible area

**Encoder section** (below display, horizontal row):
- NavX encoder (left) — horizontal navigation
- NavY encoder (center) — vertical navigation
- Edit encoder (right) — value editing
- Arranged in a horizontal row beneath the display

### Center — Keys (Key PCB)

**4×4 CHOC key grid**:
- Row 1 (channel controls): Mute, Solo, Rec, (assignable)
- Row 2: (assignable), (assignable), (assignable), (assignable)
- Row 3: (assignable), (assignable), (assignable), (assignable)
- Row 4 (navigation): Home, Back, Page, Shift

- Custom PCB with CHOC hotswap sockets + WS2812B-2020 per key + MCP23017 I2C GPIO expander + 100nF decoupling caps

### Left column — Connectivity + Monitoring (IO Board)

All left-column panel-mount components sit on the IO Board, connected to the main board via 12-pin FFC + 6-pin Ethernet ribbon cable.

- MIDI HOST dual USB-A (stacked)
- ETH RJ45 (Ethernet, with integrated magnetics)
- MIDI IN + MIDI OUT (3.5mm TRS Type A)
- Headphone output (from off-the-shelf HP amp breakout module mounted nearby)
- PHONES label + VOL pot (10kΩ log)

## Keys — Custom PCB

All 16 CHOC key switches mount on custom PCB(s) instead of individual NeoKey breakout boards.

Per switch position:
- Kailh CHOC hotswap socket
- WS2812B-2020 NeoPixel (daisy-chained DOUT→DIN, single data pin)
- 100nF ceramic decoupling cap

All 16 LEDs share one data line. Switches are scanned via a MCP23017 I2C GPIO expander (address 0x20) on the Key PCB, using a 4×4 matrix with 1N4148 anti-ghosting diodes.
