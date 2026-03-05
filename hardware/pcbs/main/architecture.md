# Main Board — Architecture

---

## Soft-Latch Power Circuit

- **74LVC1G00** NAND gate (SOT-23-5) wired as SR latch
- **Power on:** button press sets latch → TPS22965 EN → 5V rail on → Teensy boots
- **Power off (clean):** Teensy detects button (pin 40) → saves state → releases KEEP_ALIVE (pin 41) → latch resets → TPS22965 off
- **Power off (hard):** long-press >4s → RC timeout resets latch directly (hardware failsafe)
- Debounce cap on button input
- Teensy KEEP_ALIVE GPIO holds latch set during normal operation

---

## Power Distribution

### 5V Rail Partitioning

- **5V_DIG:** USB hub VBUS + NeoPixels + TFT backlight (noisy loads)
- **5V_A:** Dedicated low-noise LDO for audio analog stages

### TPS22965 Load Switch

- 5A continuous, soft-start / inrush limiting
- Input from Power Board (post-polyfuse)
- Controlled slew rate limits inrush from bulk cap charging

### Protection

- Input polyfuse (2.5A hold / 5A trip) on Power Board
- Per-port current limiting for USB host (TPS2051 on IO Board)
- Bulk capacitor (1000–2200 uF) near NeoPixel power entry
- 10 mohm shunt resistor test point for current measurement

### ADP7118 LDO (Main Board instance)

- 5V → 3.3V_A for virtual ground buffer
- 5V_A also powers HP amp breakout module via short wire

### 2.5V Virtual Ground

- Precision resistor divider (2x 10k ohm 0.1%) buffered by one OPA1678 section
- Provides stable mid-rail reference for AC-coupled signal paths
- OPA1678 rail-to-rail output gives ~3.5Vpp usable swing

### PC USB-C Ground

- GND connected to system GND through ferrite bead to reduce computer-injected noise

---

## XMOS XU216 USB Audio Bridge

Dedicated USB Audio Class 2 bridge providing 24-in / 8-out multichannel audio + USB MIDI to the PC over a single USB-C connection. See [usb-audio.md](../../docs/usb-audio.md) for full architecture.

### Chip

- **XU216-256-TQ128-C20** — 128-pin TQFP, 256 KB RAM, 16 cores, 2000 MIPS
- Open-source firmware: [xmos/sw_usb_audio](https://github.com/xmos/sw_usb_audio)

### TDM Passive Tap

The XMOS listens to both TDM buses as a slave — high-Z CMOS inputs tapping existing signals:

- SAI1: BCLK (pin 21), LRCLK (pin 20), RX_DATA0 (pin 8), RX_DATA1 (pin 32), TX_DATA0 (pin 7)
- SAI2: BCLK (pin 4), LRCLK (pin 3), RX_DATA0 (pin 5), RX_DATA1 (pin 34)
- Total: 9 signals, all receive-only, no bus contention

### SPI Control Bus (MIDI Forwarding)

SPI0 (pins 10–13) connects Teensy ↔ XMOS for USB MIDI message exchange. Teensy is SPI master; XMOS is SPI slave. Polled at ~1 kHz.

### Return Audio (PC → Mixer)

8 channels from DAW playback. Data line TBD — candidates: pin 9 (SAI1_RX_DATA2), SAI3, or SPI DMA. Validate during breadboard Phase 1.

### USB Connection

PC USB-C D+/D- routed to XMOS (not Teensy). Teensy native USB available via debug header for firmware updates.

### Power

- Core: 1.0V LDO (AP2112K-1.0 or equiv.) from 3.3V or 5V rail, ~150 mA
- I/O: 3.3V shared rail, ~50 mA
- Decoupling: 0.1 µF on each VDD/VDDIO pin (~10 caps)

### Clocking

- 24 MHz crystal — XMOS core PLL reference
- 24.576 MHz crystal — audio PLL reference (or derived from Teensy MCLK)
- XMOS runs in TDM slave / USB adaptive mode — locks to Teensy's BCLK

### Firmware Storage

- W25Q32 QSPI flash (4 MB) — stores XMOS application firmware
- Connected via XMOS QSPI port (dedicated pins, not shared with Teensy QSPI)

### ESD Protection

- USBLC6-2 on PC USB-C D+/D- lines (between connector and XMOS)

---

## TCA9548A I2C Mux

- Address **0x70** on main I2C bus (Wire, pins 18/19)
- Isolates each Input Mother Board onto its own channel:
  - **Ch 0** → FFC to Board 1-top (U1 @ 0x10, U2 @ 0x11)
  - **Ch 1** → FFC to Board 2-top (U3 @ 0x10, U4 @ 0x11)
- Resolves AK4619VN 2-address limitation
- MCP23017 (0x20, Key PCB) sits upstream — always accessible
- External pull-ups: 4.7k ohm to 3.3V upstream of mux

---

## TS5A3159 Pop Suppression

- 4x analog switch ICs (SOT-23-5), one per output stereo pair
- GPIO-controlled by Teensy: high = unmuted
- Firmware opens switches during boot/shutdown ramp
- Low Ron (~1 ohm), 5V tolerant
- Pin assignments: Main L/R = pin 30, AUX1 = pin 35, AUX2 = pin 37, AUX3 = pin 38

---

## Teensy Pin Assignments

### Peripheral pins (fixed)

- **SAI1 (TDM1):** pins 7, 8, 20, 21, 23, 32
- **SAI2 (TDM2):** pins 2, 3, 4, 5, 33 (bottom), 34 (bottom)
- **SPI0 (XMOS control):** pins 10, 11, 12, 13
- **I2C (Wire):** pins 18, 19
- **Serial3 RX (MIDI IN):** pin 15
- **Serial4 TX (MIDI OUT):** pin 17
- **SDIO (SD card):** bottom pads 42–47
- **USB Host:** bottom pads (D+, D-, VBUS, GND)
- **Ethernet:** bottom pads (TX+/-, RX+/-, LED, GND)

### GPIO assignments

| Pin | Function |
|-----|----------|
| 0, 1 | Serial1 — ESP32-S3 display UART |
| 6 | NeoPixel data out |
| 9 | *(candidate: XMOS return audio — SAI1_RX_DATA2)* |
| 14 | *(spare — was RA8875 RESET)* |
| 16 | Encoder 3 (Edit) push |
| 22 | MCP23017 INT |
| 24, 25, 28 | Encoder 1 (NavX) A, B, push |
| 26, 27 | Encoder 3 (Edit) A, B |
| 29, 31, 36 | Encoder 2 (NavY) A, B, push |
| 30 | TS5A3159 mute Main L/R |
| 35 | TS5A3159 mute AUX1 (bottom pad) |
| 37 | TS5A3159 mute AUX2 |
| 38 | TS5A3159 mute AUX3 |
| 39 | Headphone detect |
| 40 | Power button sense |
| 41 | KEEP_ALIVE |

**Total edge pins:** 42. **Consumed by peripherals:** 22 (SAI ×12, SPI0/XMOS ×4, I2C ×2, Serial1/ESP32 ×2, Serial3 RX ×1, Serial4 TX ×1). **GPIO:** 19 used + 1 candidate (pin 9), 1 spare (pin 14).

---

## Power Sequencing

```
Button press → SR latch SET → TPS22965 EN → 5V rail on → Teensy boots
                                                            ↓
                                            Teensy asserts KEEP_ALIVE (pin 41)
                                            Teensy reads button via pin 40

Button press → Teensy detects → saves state → releases KEEP_ALIVE
                                                            ↓
                                            SR latch RESET → TPS22965 off
Long-press (>4s) → RC timeout resets latch directly (hardware failsafe)
```

---

[Back to README](README.md)
