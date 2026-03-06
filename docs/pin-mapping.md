# MIXTEE: Teensy 4.1 Pin Mapping

*← Back to [README](../README.md) | See also: [Hardware](hardware.md) · [System Topology](system-topology.md) · [AK4619VN Wiring](../hardware/pcbs/input-mother/ak4619-wiring.md)*

------

## Pin Reference Source

All assignments verified against the official [PJRC Teensy 4.1 reference cards](https://www.pjrc.com/store/teensy41.html) (card11a/card11b rev4) and the PJRC Audio Library source code (output_tdm.cpp, input_tdm.cpp, output_tdm2.cpp, input_tdm2.cpp).

------

## Peripheral Pin Assignments (Fixed)

These pins are consumed by dedicated hardware peripherals and cannot be reassigned.

### SAI1 — TDM Bus 1 (Codecs U1 + U2)

| Teensy Pin | Function | Card Label | iMXRT1062 Pad | Direction |
|-----------|----------|------------|---------------|-----------|
| **23** | SAI1 MCLK | MCLK1 | AD_B1_09 | Output (master clock) |
| **21** | SAI1 BCLK | BCLK1 | AD_B1_11 | Output (bit clock) |
| **20** | SAI1 LRCLK | LRCLK1 | AD_B1_10 | Output (frame sync) |
| **7** | SAI1 TX_DATA0 | OUT1A | B1_00 | Output (Teensy → codec) |
| **8** | SAI1 RX_DATA0 | IN1 | B1_01 | Input (U1 SDOUT → Teensy) |
| **32** | SAI1 RX_DATA1 | OUT1B | B0_10 | Input (U2 SDOUT → Teensy) |

BCLK = 48 kHz × 16 slots × 32 bits = **24.576 MHz**. MCLK = 256×fs = **12.288 MHz**.

**Note:** Pin 23 is also the built-in LED — LED unavailable when audio is active.

### SAI2 — TDM Bus 2 (Codecs U3 + U4)

| Teensy Pin | Function | Card Label | iMXRT1062 Pad | Direction |
|-----------|----------|------------|---------------|-----------|
| **33** | SAI2 MCLK | MCLK2 | EMC_07 | Output (master clock) |
| **4** | SAI2 BCLK | BCLK2 | EMC_06 | Output (bit clock) |
| **3** | SAI2 LRCLK | LRCLK2 | EMC_05 | Output (frame sync) |
| **2** | SAI2 TX_DATA0 | OUT2 | EMC_04 | Output (Teensy → codec) |
| **5** | SAI2 RX_DATA0 | IN2 | EMC_08 | Input (U3 SDOUT → Teensy) |
| **34** | SAI2 RX_DATA1 | — | B0_12 | Input (U4 SDOUT → Teensy), **bottom pad** |

**Critical:** Pin 33 is a **bottom pad** — not accessible from the breadboard edge. On the custom PCB, route this from a via or bottom-side pad to the FFC connector for TDM2.

### I2C — Codec Control Bus

| Teensy Pin | Function | Card Label | Bus |
|-----------|----------|------------|-----|
| **18** | SDA | SDA | Wire (I2C0) |
| **19** | SCL | SCL | Wire (I2C0) |

All four AK4619VN codecs share one I2C bus via a **TCA9548A I2C mux** (address 0x70) on the main board. The mux isolates each Input Mother Board onto its own channel (Ch 0 for U1/U2, Ch 1 for U3/U4), resolving the AK4619VN 2-address limitation. A **MCP23017 I2C GPIO expander** (address 0x20) on the Key PCB handles the 4×4 key scan matrix over the same bus. SDA and SCL routed on both FFC cables and the Key PCB cable. External pull-ups: 4.7kΩ to 3.3V on the main board (upstream of mux). Each Input Mother Board has its own downstream pull-ups. See [AK4619VN Wiring](../hardware/pcbs/input-mother/ak4619-wiring.md) for addressing details.

### SPI0 — XMOS XU216 Control Bus (MIDI Forwarding)

SPI0 pins (10, 11, 12, 13) connect to the XMOS XU216 USB audio bridge for MIDI message forwarding between Teensy and PC. USB MIDI arrives at the XMOS over USB; the Teensy exchanges MIDI data via SPI at ~1 kHz polling rate.

| Teensy Pin | Function | Card Label | Direction |
|-----------|----------|------------|-----------|
| **10** | SPI0 CS → XMOS | CS | Output (Teensy selects XMOS) |
| **11** | SPI0 MOSI → XMOS | MOSI | Output (MIDI TX: Teensy → PC) |
| **12** | SPI0 MISO ← XMOS | MISO | Input (MIDI RX: PC → Teensy) |
| **13** | SPI0 SCK | SCK | Output (SPI clock) |

### Serial3 — MIDI IN (6N138 Output)

| Teensy Pin | Function | Card Label |
|-----------|----------|------------|
| **15** | RX (MIDI data in) | S/PDIF IN, RX3 |
| (14) | TX (unused, see note) | S/PDIF OUT, TX3 |

MIDI IN is receive-only at 31,250 baud. Pin 15 configured as Serial3 RX. **Routes via Main↔IO FFC pin 7 (MIDI_RX) to 6N138 optocoupler circuit on IO Board.**

**Pin 14 note:** `Serial3.begin(31250)` claims both TX (pin 14) and RX (pin 15). Pin 14 is reclaimed as GPIO in firmware by overriding the IOMUX after Serial3 initialization. Now spare (was RA8875 RESET, freed by ESP32-S3 display offload).

### Serial4 — MIDI OUT

| Teensy Pin | Function | Card Label |
|-----------|----------|------------|
| **17** | TX (MIDI data out) | SDA1, TX4 |

MIDI OUT is transmit-only at 31,250 baud. Pin 17 configured as Serial4 TX. **Routes via Main↔IO FFC pin 8 (MIDI_TX) to MIDI OUT circuit on IO Board.** Standard MIDI current-loop output via 3.5mm TRS Type A jack on IO Board. Software handles pass-through of MIDI IN messages and/or Teensy-generated MIDI output.

### USB Host (Bottom Pads)

| Pad | Signal |
|-----|--------|
| +5V | VBUS out (to FE1.1s upstream) |
| D- | USB data minus |
| D+ | USB data plus |
| GND | Ground (×2 pads) |

These are dedicated USB2 PHY pads on the bottom of the Teensy 4.1 — not GPIO pins. **Routes via Main↔IO FFC pins 4–5 (USB_HOST_D+/D-) to FE1.1s USB hub IC upstream port on IO Board.** USB Full-Speed only (12 Mbps for MIDI host). Use `USBHost_t36` library for USB MIDI host.

### Ethernet (Bottom Pads)

| Pad | Signal | Notes |
|-----|--------|-------|
| TX+ | Ethernet transmit positive | Differential pair, post-PHY analog |
| TX- | Ethernet transmit negative | Differential pair |
| RX+ | Ethernet receive positive | Differential pair |
| RX- | Ethernet receive negative | Differential pair |
| LED | Activity LED (optional) | Active-low, accent LED driver |
| GND | Ground | Shield/return |

These are dedicated Ethernet PHY pads on the bottom of the Teensy 4.1 (DP83825I PHY). **Routes via 6-pin ribbon cable from Main Board header to IO Board header, then through 0.1µF coupling caps to RJ45 MagJack with integrated magnetics.** Post-PHY analog signals — cable-tolerant, no impedance-controlled routing required. Use `QNEthernet` or `NativeEthernet` library for TCP/IP stack.

### SDIO — External Full-Size SD Card Socket

| Teensy Bottom Pad | Signal | Connection |
|-------------------|--------|------------|
| 42 | SD_DAT3 | Routed to external full-size SD socket on Main Board |
| 43 | SD_DAT2 | Routed to external full-size SD socket on Main Board |
| 44 | SD_DAT1 | Routed to external full-size SD socket on Main Board |
| 45 | SD_DAT0 | Routed to external full-size SD socket on Main Board |
| 46 | SD_CLK | Routed to external full-size SD socket on Main Board |
| 47 | SD_CMD | Routed to external full-size SD socket on Main Board |

The Teensy 4.1's SDIO bottom pads (pins 42–47) are routed from the Teensy underside directly to a panel-mount full-size SD card socket on the Main Board. The Teensy's built-in micro-SD slot is left physically empty. Access via `SD.begin(BUILTIN_SDCARD)` — the SDIO peripheral is the same whether using the onboard slot or external routing. Native 4-bit SDIO provides 20–30 MB/s sustained write — well above the 2.3 MB/s needed for 16-channel recording.

### QSPI — PSRAM (Bottom Pads)

Pins 49, 50, 52, 53, 54 (plus CS on 48 or 51) are consumed by the 8 MB PSRAM soldered to the bottom QSPI pads. Unavailable for GPIO.

------

## Peripheral Pin Summary

| Pin | Peripheral | Unavailable alternates |
|-----|-----------|----------------------|
| 2 | SAI2 TX_DATA0 | CRX2, CTX2 |
| 3 | SAI2 TX_SYNC | — |
| 4 | SAI2 TX_BCLK | — |
| 5 | SAI2 RX_DATA0 | — |
| 7 | SAI1 TX_DATA0 | RX2 (Serial2 blocked) |
| 8 | SAI1 RX_DATA0 | TX2 (Serial2 blocked) |
| 10 | SPI0 CS (XMOS control) | — |
| 11 | SPI0 MOSI (XMOS control) | CTX1 |
| 12 | SPI0 MISO (XMOS control) | — |
| 13 | SPI0 SCK (XMOS control) | (LED) |
| 15 | Serial3 RX (MIDI IN) | S/PDIF IN, RX4 |
| 17 | Serial4 TX (MIDI OUT) | SDA1 |
| 18 | Wire SDA | A4 |
| 19 | Wire SCL | A5 |
| 20 | SAI1 TX_SYNC | TX5, RX5 (Serial5 blocked) |
| 21 | SAI1 TX_BCLK | TX5, RX5 (Serial5 blocked) |
| 23 | SAI1 MCLK | CRX1, CTX1, A9, (LED) |
| 32 | SAI1 RX_DATA1 | OUT1B (SAI1_DATA1) |
| 33 | SAI2 MCLK | Bottom pad |
| 34 | SAI2 RX_DATA1 | Bottom pad |

**Total edge pins consumed: 20** (plus bottom pads for USB Host, SDIO, QSPI). SPI0 pins 10–13 reassigned to XMOS XU216 control bus (MIDI forwarding).

------

## GPIO Budget

Total Teensy 4.1 edge pins: **42** (pins 0–41)
Consumed by peripherals: **22** (SAI1 ×6, SAI2 ×6, SPI0/XMOS ×4, I2C ×2, Serial1/ESP32 ×2, Serial3 RX ×1, Serial4 TX ×1)
Available for GPIO: **20**

### GPIO Requirements

| Function | Pins needed | Notes |
|----------|------------|-------|
| Encoder 1 (NavX) | **3** | A, B, push switch — horizontal navigation |
| Encoder 2 (NavY) | **3** | A, B, push switch — vertical navigation |
| Encoder 3 (Edit) | **3** | A, B, push switch — value editing |
| NeoPixel data | **1** | Single data line to 16× WS2812B |
| Power button sense | **1** | Soft-latch button state (back panel button, wired to Main Board) |
| KEEP_ALIVE | **1** | Hold soft-latch set during operation |
| MCP23017 INT (optional) | **1** | Interrupt-driven key scan; can be omitted if polling |
| MIDI OUT | **1** | Serial4 TX (pin 17) |
| XMOS return audio (candidate) | **(1)** | Pin 9 — SAI1_RX_DATA2 if IOMUX validates; may remain spare |
| **Total** | **14** (+1 candidate) | |

**Remaining spare: 6 pins** (14, 30, 35, 37, 38, 39). Pins 30/35/37/38 freed by moving TS5A3159 mute control to MCP23008 on Board 1-top (isolated analog domain). Pin 39 freed by routing headphone detect via MCP23008 GP6 on Board 1-top instead of direct GPIO. Pin 9 is a candidate for XMOS return audio but requires iMXRT1062 IOMUX validation — if not usable as SAI1_RX_DATA2, it remains spare (7 spare total).

### Key Matrix via MCP23017

The 4×4 key matrix (16 keys) is handled entirely by a **MCP23017 I2C GPIO expander** (address 0x20) on the Key PCB. This frees 7 Teensy GPIO pins compared to a direct-wired matrix:

- MCP23017 Port A (GPA0–3): 4 column inputs with internal pull-ups
- MCP23017 Port B (GPB0–3): 4 row outputs (active-low scan)
- 16× 1N4148 diodes per switch (cathode toward row) prevent ghosting
- Scan rate: polled via I2C at ~1 kHz, or interrupt-driven via INTA/INTB pin
- Only I2C (SDA/SCL) + optional INT needed in the Key↔Main cable (6 pins total)

------

## GPIO Pin Assignments

| Teensy Pin | Assignment | Direction | Notes |
|-----------|-----------|-----------|-------|
| **0** | Serial1 RX — ESP32-S3 display UART | Input | ESP32-S3 TX → Teensy (touch events) |
| **1** | Serial1 TX — ESP32-S3 display UART | Output | Teensy → ESP32-S3 (meter data + param state) |
| **6** | NeoPixel data out | Output | 300–500Ω series resistor; also has OUT1D (SAI1_DATA3) alternate — not used |
| **9** | *(candidate: XMOS return audio)* | Input | SAI1_RX_DATA2 alternate — 8ch PC return; requires IOMUX validation; also OUT1C (SAI1_DATA2) |
| **14** | *(spare — was RA8875 RESET)* | — | Freed by ESP32-S3 display offload; IOMUX reclaimed from Serial3 TX after `Serial3.begin()` |
| **16** | Encoder 3 (Edit) — Push | Input (pull-up) | Also SCL1/RX4 alternate |
| **17** | MIDI OUT (Serial4 TX) | Output | 31.25 kbaud MIDI output; also SDA1/TX4 alternate |
| **22** | MCP23017 INT (optional) | Input (pull-up) | Key scan interrupt from Key PCB; also A8 |
| **24** | Encoder 1 (NavX) — A | Input (pull-up) | Interrupt-capable; horizontal navigation; also SCL2/A10 |
| **25** | Encoder 1 (NavX) — B | Input (pull-up) | Interrupt-capable; also SDA2/A11 |
| **26** | Encoder 3 (Edit) — A | Input (pull-up) | Interrupt-capable; also A12 |
| **27** | Encoder 3 (Edit) — B | Input (pull-up) | Interrupt-capable; also A13/SCK1 |
| **28** | Encoder 1 (NavX) — Push | Input (pull-up) | Also RX7 |
| **29** | Encoder 2 (NavY) — A | Input (pull-up) | Interrupt-capable; vertical navigation; also CRX3 |
| **30** | *(spare — was TS5A3159 mute Main L/R, moved to MCP23008 on Board 1-top)* | — | Freed by galvanic isolation; mute now via I2C |
| **31** | Encoder 2 (NavY) — B | Input (pull-up) | Relocated from pin 32 (now SAI1_RX_DATA1); interrupt-capable |
| **35** | *(spare — was TS5A3159 mute AUX1, moved to MCP23008 on Board 1-top)* | — | **Bottom pad**; freed by galvanic isolation |
| **36** | Encoder 2 (NavY) — Push | Input (pull-up) | |
| **37** | *(spare — was TS5A3159 mute AUX2, moved to MCP23008 on Board 1-top)* | — | Freed by galvanic isolation |
| **38** | *(spare — was TS5A3159 mute AUX3, moved to MCP23008 on Board 1-top)* | — | Also A14; freed by galvanic isolation |
| **39** | *(spare — was headphone detect, now via MCP23008 GP6 on Board 1-top)* | — | Also A15; freed by galvanic isolation |
| **40** | Power button sense | Input (pull-up) | Back panel button wired to Main Board soft-latch; also A16 |
| **41** | KEEP_ALIVE | Output | Holds soft-latch set; release to shut down; also A17 |

*Key matrix wiring and key-switch mapping moved to [Key PCB architecture](../hardware/pcbs/key/architecture.md).*

------

## Alternate Functions Lost

Using certain pins as GPIO makes their alternate peripheral functions unavailable:

| Pins | Lost alternate | Impact |
|------|---------------|--------|
| 24, 25 | Wire2 (I2C2), Serial6 | Not needed |
| 28 | Serial7 RX | Not needed — MIDI uses Serial3 |
| 29 | CAN3 RX | Not needed |
| 0, 1 | SPI1 CS/MISO, CAN2 | Used as Serial1 for ESP32-S3 UART; SPI1/CAN2 not needed |

**Note:** Pin 16 (Wire1 SCL / Serial4 RX) remains spare. Pin 17 is used as Serial4 TX for MIDI OUT — its Wire1 SDA alternate is unavailable.

------

## Conflict Warnings

1. **Serial2 (pins 7/8) is BLOCKED** — these pins are SAI1 audio data lines
2. **Serial5 (pins 20/21) is BLOCKED** — these pins are SAI1 BCLK/LRCLK
3. **Pin 23 = LED** — built-in LED unavailable during audio playback
4. **Pin 14 dual-use** — Serial3 TX alternate; must override IOMUX in firmware to use as GPIO
5. **Pins 34, 35 are bottom pads** — require PCB traces from Teensy underside; not breadboard accessible
6. **Pin 33 is a bottom pad** — SAI2 MCLK must be routed from Teensy underside to FFC connector
7. **Pin 32 is now SAI1_RX_DATA1** — no longer available as GPIO (was Encoder 2 B, moved to pin 31)
8. **Pin 34 is now SAI2_RX_DATA1** — no longer available as GPIO (was TS5A3159 mute Main, moved to pin 30)
9. **Pin 6 has SAI1 DATA3 alternate** — used as GPIO (NeoPixel); safe because the Audio Library multi-data-line mode only uses DATA0 + DATA1
10. **Pin 9 has SAI1 DATA2 alternate** — candidate for XMOS return audio (SAI1_RX_DATA2). Requires IOMUX validation during breadboard phase. If not usable, remains spare GPIO.
11. **XMOS XU216 passively taps TDM bus signals** — BCLK, LRCLK, and data lines on both SAI1 and SAI2 are shared with high-Z CMOS inputs on the XMOS. No bus contention — XMOS is receive-only on all audio data lines.
12. **SPI0 (pins 10–13) reassigned to XMOS control bus** — no longer spare. Used for MIDI forwarding between Teensy and XMOS (USB MIDI composite device on PC USB-C).

------

*FFC cable pinouts moved to per-board connections.md files. See [input-mother](../hardware/pcbs/input-mother/connections.md), [io](../hardware/pcbs/io/connections.md), [key](../hardware/pcbs/key/connections.md), [main](../hardware/pcbs/main/connections.md).*

------

*Power sequencing moved to [Main Board architecture](../hardware/pcbs/main/architecture.md).*

------

## Verification Checklist

- [ ] Confirm SAI1/SAI2 pin assignments match PJRC Audio Library `output_tdm.cpp` / `input_tdm2.cpp`
- [ ] Verify SAI1_RX_DATA1 (pin 32) and SAI2_RX_DATA1 (pin 34) work with modified Audio Library for multi-data-line RX
- [ ] Verify pin 33 (bottom pad) can be routed on custom PCB to FFC connector
- [ ] Confirm pins 6, 9 are not claimed by Audio Library in TDM mode (DATA2/DATA3 alternates unused)
- [ ] Test Serial3 RX-only operation with pin 14 reclaimed as GPIO
- [ ] Verify MCP23017 I2C key matrix scan works at 0x20 (no bus conflicts with TCA9548A at 0x70)
- [ ] Check encoder interrupt latency on pins 24/25/26/27/29/31 (all interrupt-capable ✓)
- [ ] Validate FE1.1s upstream D+/D- connects to Teensy USB Host bottom pads (not USB Device)
- [ ] Print 1:1 Teensy 4.1 footprint, verify bottom pad access for pins 33, 34, 35, 42–47
- [ ] Verify external SD card socket SDIO routing from Teensy bottom pads 42–47
- [ ] Validate pin 9 IOMUX for SAI1_RX_DATA2 (XMOS return audio) — check iMXRT1062 reference manual pad mux options
- [ ] Verify SPI0 (pins 10–13) XMOS communication works at required polling rate (~1 kHz MIDI)
- [ ] Verify XMOS passive TDM tap does not affect signal integrity on existing bus (measure eye diagrams if possible)
