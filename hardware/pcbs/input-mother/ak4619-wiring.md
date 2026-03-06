# MIXTEE: AK4619VN Codec Wiring

*← Back to [README](README.md) | See also: [Connections](connections.md) · [Architecture](architecture.md)*

------

## AK4619VN Quick Reference

| Parameter | Value |
|-----------|-------|
| **Package** | 32-pin QFN (5 mm × 5 mm, 0.5 mm pitch) + exposed pad |
| **ADC** | 4-channel, 24-bit, 106 dB S/N (differential, 0 dB gain, 48 kHz) |
| **DAC** | 4-channel, 32-bit, 108 dB S/N (48 kHz) |
| **Sample rate** | 8–192 kHz (MIXTEE: 48 kHz) |
| **AVDD** | 3.0–3.6 V (analog supply) |
| **TVDD** | 1.7–3.6 V (digital I/F & internal LDO input) |
| **Internal LDO** | 1.2 V on AVDRV pin (digital core) |
| **Control** | I2C (400 kHz fast mode) or SPI — MIXTEE uses I2C |
| **Audio I/F** | I2S / TDM slave (MIXTEE: TDM128, BICK = 128fs) |
| **Quantity in MIXTEE** | 4 (U1–U4) |

------

## Pin Table (32-pin QFN)

### Audio Data Interface

| Pin | Name | I/O | MIXTEE Usage |
|-----|------|-----|-------------|
| 1 | SDIN1 | I | TDM data in (Teensy → codec). Connected to SAI TX_DATA0 via FFC |
| 2 | SDIN2 | I | Unused in TDM mode — tie to VSS2 |
| 6 | LRCK | I | Frame sync from Teensy. 48 kHz, shared on TDM bus |
| 7 | BICK | I | Bit clock from Teensy. 128fs = 6.144 MHz at 48 kHz |
| 8 | MCLK | I | Master clock from Teensy. 256fs = 12.288 MHz |
| 31 | SDOUT1 | O | TDM data out (codec → Teensy). Connected to SAI RX_DATA0 via FFC |
| 32 | SDOUT2 | O | Unused in TDM mode — goes low automatically. Leave open |

### Control Interface (I2C mode)

| Pin | Name | I/O | MIXTEE Usage |
|-----|------|-----|-------------|
| 27 | CAD | I | I2C address select. VSS2 = 0x10, TVDD = 0x11 |
| 28 | SCL | I | I2C clock — shared bus, 4.7 kΩ pull-up to 3.3 V on main board |
| 29 | SI | I | SPI data in — unused in I2C mode. Tie to VSS2 |
| 30 | SDA | I/O | I2C data — shared bus, 4.7 kΩ pull-up to 3.3 V on main board |

### Power & Ground

| Pin | Name | I/O | MIXTEE Usage |
|-----|------|-----|-------------|
| 3 | TVDD | — | Digital I/F & LDO supply. Connect to 3.3 V_A (from ADP7118 LDO) |
| 4 | VSS2 | — | Digital ground |
| 5 | AVDRV | O | Internal LDO 1.2 V output. Decouple with 2.2 µF (±50%) to VSS2. Do NOT load |
| 17 | VCOM | O | Internal AVDD/2 reference. Decouple with 2.2 µF (±50%) to VSS1. Do NOT connect to other devices |
| 18 | AVDD | — | Analog supply. Connect to 3.3 V_A (from ADP7118 LDO) |
| 19 | VSS1 | — | Analog ground |
| 20 | VREFL | I | Low reference voltage. Connect to VSS1 |
| 21 | VREFH | I | High reference voltage. Connect to AVDD |
| — | Exposed Pad | — | Connect to VSS1 (recommended) or leave open |

### Analog Inputs (single-ended mode for MIXTEE)

| Pin | Name (SE mode) | I/O | MIXTEE Usage |
|-----|----------------|-----|-------------|
| 16 | AIN1L | I | ADC1 Lch — mixer input (see per-codec tables below) |
| 15 | AIN2L | I | ADC1 Lch alternate (via 2:1 MUX, register-selected) — leave open |
| 14 | AIN1R | I | ADC1 Rch — mixer input |
| 13 | AIN2R | I | ADC1 Rch alternate — leave open |
| 12 | AIN4L | I | ADC2 Lch — mixer input |
| 11 | AIN5L | I | ADC2 Lch alternate — leave open |
| 10 | AIN4R | I | ADC2 Rch — mixer input |
| 9 | AIN5R | I | ADC2 Rch alternate — leave open |

### Analog Outputs

| Pin | Name | I/O | MIXTEE Usage |
|-----|------|-----|-------------|
| 22 | AOUT1L | O | DAC1 Lch — used on U1/U2 only (see per-codec tables) |
| 23 | AOUT1R | O | DAC1 Rch — used on U1/U2 only |
| 24 | AOUT2L | O | DAC2 Lch — used on U1/U2 only |
| 25 | AOUT2R | O | DAC2 Rch — used on U1/U2 only |

### Other

| Pin | Name | I/O | MIXTEE Usage |
|-----|------|-----|-------------|
| 26 | PDN | I | Power-down control. "L" = power-down, "H" = normal. Connect to FFC spare pin for firmware-controlled reset, or tie to TVDD via 10 kΩ for always-on |

------

## I2C Address Configuration

The AK4619VN has a single CAD pin (pin 27) that sets the least significant bit of the 7-bit I2C slave address. The upper 7 bits are fixed as `0010000`.

| CAD Pin | 7-bit Address | 8-bit Write | 8-bit Read |
|---------|--------------|-------------|------------|
| VSS2 (low) | `0010000` = **0x10** | 0x20 | 0x21 |
| TVDD (high) | `0010001` = **0x11** | 0x22 | 0x23 |

### MIXTEE 4-Codec Addressing

| Codec | Board | TDM Bus | CAD | I2C Address |
|-------|-------|---------|-----|-------------|
| U1 | Input Mother 1-top | TDM1 (SAI1) | Low (VSS2) | **0x10** |
| U2 | Input Mother 1-top | TDM1 (SAI1) | High (TVDD) | **0x11** |
| U3 | Input Mother 2-top | TDM2 (SAI2) | Low (VSS2) | **0x10** |
| U4 | Input Mother 2-top | TDM2 (SAI2) | High (TVDD) | **0x11** |

**Design note — 2-address limitation:** The AK4619VN only provides 2 unique I2C addresses (unlike some codecs with 2 address pins giving 4 addresses). With all four codecs on a single I2C bus (Wire, pins 18/19), U1 and U3 collide at 0x10, and U2 and U4 collide at 0x11.

**Solution — TCA9548A I2C mux:** A TCA9548A I2C bus switch (address 0x70) on the main board isolates each Input Mother Board onto its own mux channel. The Teensy selects a channel before communicating with codecs on that board:

| Mux Channel | FFC Cable | Codecs | Addresses |
|-------------|-----------|--------|-----------|
| Ch 0 | FFC to Board 1-top | U1, U2 | 0x10, 0x11 |
| Ch 1 | FFC to Board 2-top | U3, U4 | 0x10, 0x11 |

This gives full individual register control of all four codecs with zero additional GPIO cost. No address conflicts exist because only one channel is active at a time. The MCP23017 key matrix expander (0x20) and TCA9548A (0x70) sit upstream on the main I2C bus and are always accessible.

------

## TDM Interface Wiring

### TDM Mode Selection

MIXTEE uses **TDM128 mode** (Mode 8 in Table 2 of the datasheet):

| Setting | Value | Notes |
|---------|-------|-------|
| Mode | 8 — TDM128, I2S compatible | |
| TDM bit | 1 | Enables TDM |
| SLOT bit | 1 | Slot-length basis |
| DCF[2:0] | 010 | I2S compatible |
| DSL[1:0] | 11 | 32-bit slot length |
| BICK | 128fs = 6.144 MHz (at 48 kHz) | |
| MCLK | 256fs = 12.288 MHz | |
| LRCK | fs = 48 kHz | |

**In TDM mode:** Only SDIN1 and SDOUT1 are active. SDIN2 input is ignored. SDOUT2 outputs low. Each codec occupies **4 TDM slots (0–3)** on its data line — there is no slot offset configuration in the AK4619VN.

### TDM Bus Assignment

| TDM Bus | SAI | Codecs | FFC Cable | Teensy Pins |
|---------|-----|--------|-----------|-------------|
| TDM1 | SAI1 | U1 + U2 | FFC to Board 1-top | MCLK=23, BCLK=21, LRCLK=20, TX=7, RX0=8 (U1), RX1=32 (U2) |
| TDM2 | SAI2 | U3 + U4 | FFC to Board 2-top | MCLK=33, BCLK=4, LRCLK=3, TX=2, RX0=5 (U3), RX1=34 (U4) |

### Clock Distribution

```
Teensy SAI1/SAI2 → [Si8662BB isolator on Main Board] → FFC (isolated side)
    ├── MCLK (256fs = 12.288 MHz) ─── FFC pin 1 ──→ U1 pin 8, U2 pin 8
    ├── BCLK (128fs = 6.144 MHz)  ─── FFC pin 2 ──→ U1 pin 7, U2 pin 7
    └── LRCLK (fs = 48 kHz)      ─── FFC pin 3 ──→ U1 pin 6, U2 pin 6
```

Both codecs on each Input Mother Board share the same MCLK, BICK, and LRCK lines from the FFC cable. The Teensy is the clock master; all codecs are slaves.

### Separate SDOUT Lines (Resolved)

**Problem (resolved):** The AK4619VN always transmits ADC data in TDM slots 0–3. Two codecs on the same SDOUT line would have bus contention.

**Solution:** Each codec gets its own SDOUT → SAI RX data pin. The iMXRT1062 SAI peripherals support multiple RX data lines (RX_DATA0 + RX_DATA1). This requires a PJRC Audio Library modification to enable SAI multi-data-line receive (SAI1_RCR3 / SAI2_RCR3 registers).

| Bus | Codec | SDOUT → FFC Pin | Teensy Pin | SAI Function |
|-----|-------|----------------|------------|-------------|
| SAI1 | U1 | FFC pin 5 (TDM_RX0_ISO) | **8** | SAI1_RX_DATA0 |
| SAI1 | U2 | FFC pin 7 (TDM_RX1_ISO) | **32** | SAI1_RX_DATA1 |
| SAI2 | U3 | FFC pin 5 (TDM_RX0_ISO) | **5** | SAI2_RX_DATA0 |
| SAI2 | U4 | FFC pin 7 (TDM_RX1_ISO) | **34** (bottom pad) | SAI2_RX_DATA1 |

Both codecs on a bus still share the same clock lines (MCLK, BCLK, LRCLK) and the same TX data line (SDIN1). Each codec independently drives TDM slots 0–3 on its own SDOUT line — no bus contention. The Teensy receives 4 channels per data line, 8 channels total per SAI bus.

------

## Per-Codec Connection Tables

### U1 — Input Mother Board 1-top (TDM1, channels 1–4)

| AK4619 Pin | Pin Name | Connection | Signal |
|-----------|----------|------------|--------|
| 1 | SDIN1 | FFC pin 4 (TDM_TX_ISO) → Teensy pin 7 | TDM TX data (Teensy → U1 DAC, via Si8662BB) |
| 2 | SDIN2 | VSS2 | Unused in TDM |
| 3 | TVDD | 3.3 V_A | Digital supply |
| 4 | VSS2 | GND | Digital ground |
| 5 | AVDRV | 2.2 µF cap to VSS2 | Internal LDO output |
| 6 | LRCK | FFC pin 3 (LRCLK_ISO) → Teensy pin 20 | Frame sync (via Si8662BB) |
| 7 | BICK | FFC pin 2 (BCLK_ISO) → Teensy pin 21 | Bit clock (via Si8662BB) |
| 8 | MCLK | FFC pin 1 (MCLK_ISO) → Teensy pin 23 | Master clock (via Si8662BB) |
| 9 | AIN5R | Open | Unused analog input |
| 10 | AIN4R | Input buffer → Ch 2R jack | ADC2 Rch = mixer channel 2 |
| 11 | AIN5L | Open | Unused analog input |
| 12 | AIN4L | Input buffer → Ch 2L jack | ADC2 Lch = mixer channel 1 |
| 13 | AIN2R | Open | Unused analog input |
| 14 | AIN1R | Input buffer → Ch 1R jack | ADC1 Rch = mixer channel 4 |
| 15 | AIN2L | Open | Unused analog input |
| 16 | AIN1L | Input buffer → Ch 1L jack | ADC1 Lch = mixer channel 3 |
| 17 | VCOM | 2.2 µF cap to VSS1 | Internal AVDD/2 reference |
| 18 | AVDD | 3.3 V_A | Analog supply |
| 19 | VSS1 | GND | Analog ground |
| 20 | VREFL | VSS1 | Low voltage reference |
| 21 | VREFH | AVDD | High voltage reference |
| 22 | AOUT1L | Reconstruction filter → Main L | DAC1 Lch output |
| 23 | AOUT1R | Reconstruction filter → Main R | DAC1 Rch output |
| 24 | AOUT2L | Reconstruction filter → AUX1 L | DAC2 Lch output |
| 25 | AOUT2R | Reconstruction filter → AUX1 R | DAC2 Rch output |
| 26 | PDN | TVDD via 10 kΩ (or FFC spare) | Power-down control |
| 27 | CAD | VSS2 | I2C address = 0x10 |
| 28 | SCL | FFC pin 10 (I2C_SCL_ISO) → ISO1541 → TCA9548A Ch 0 → Teensy pin 19 | I2C clock (via isolator + mux) |
| 29 | SI | VSS2 | Unused (I2C mode) |
| 30 | SDA | FFC pin 9 (I2C_SDA_ISO) → ISO1541 → TCA9548A Ch 0 → Teensy pin 18 | I2C data (via isolator + mux) |
| 31 | SDOUT1 | FFC pin 5 (TDM_RX0_ISO) → Si8662BB → Teensy pin 8 | TDM RX data (U1 ADC → Teensy) |
| 32 | SDOUT2 | Open | Goes low in TDM mode |
| — | Exposed Pad | VSS1 | Thermal/ground pad |

### U2 — Input Mother Board 1-top (TDM1, channels 5–8)

Identical to U1 except:

| Difference | U1 | U2 |
|-----------|----|----|
| CAD (pin 27) | VSS2 → 0x10 | TVDD → **0x11** |
| ADC1 L (pin 16, AIN1L) | Ch 3 input | **Ch 7** input |
| ADC1 R (pin 14, AIN1R) | Ch 4 input | **Ch 8** input |
| ADC2 L (pin 12, AIN4L) | Ch 1 input | **Ch 5** input |
| ADC2 R (pin 10, AIN4R) | Ch 2 input | **Ch 6** input |
| DAC1 L (pin 22) | Main L | **AUX2 L** |
| DAC1 R (pin 23) | Main R | **AUX2 R** |
| DAC2 L (pin 24) | AUX1 L | **AUX3 L** |
| DAC2 R (pin 25) | AUX1 R | **AUX3 R** |
| SDOUT1 (pin 31) | FFC pin 7 (TDM_RX1_ISO) → Si8662BB → Teensy pin 32 | **SAI1_RX_DATA1** (separate from U1) |

All other pins (power, clocks, I2C, unused inputs) are wired identically to U1.

### U3 — Input Mother Board 2-top (TDM2, channels 9–12)

Same physical wiring pattern as U1, with these differences:

| Difference | U1 | U3 |
|-----------|----|----|
| TDM bus | TDM1 (SAI1) | **TDM2 (SAI2)** |
| MCLK (pin 8) | Teensy pin 23 | Teensy pin **33** |
| BICK (pin 7) | Teensy pin 21 | Teensy pin **4** |
| LRCK (pin 6) | Teensy pin 20 | Teensy pin **3** |
| SDIN1 (pin 1) | Teensy pin 7 | Teensy pin **2** |
| SDOUT1 (pin 31) | FFC pin 5 → Teensy pin 8 (SAI1_RX_DATA0) | FFC pin 5 → Teensy pin **5** (SAI2_RX_DATA0) |
| CAD (pin 27) | VSS2 → 0x10 | VSS2 → **0x10** (same address, isolated via TCA9548A Ch 1) |
| ADC inputs | Ch 1–4 | **Ch 9–12** |
| DAC outputs (pins 22–25) | Used (Main + AUX1) | **Unused — leave open** |

### U4 — Input Mother Board 2-top (TDM2, channels 13–16)

Same as U3 except:

| Difference | U3 | U4 |
|-----------|----|----|
| CAD (pin 27) | VSS2 → 0x10 | TVDD → **0x11** |
| SDOUT1 (pin 31) | FFC pin 5 → Teensy pin 5 (SAI2_RX_DATA0) | FFC pin 7 → Teensy pin **34** (**SAI2_RX_DATA1**, bottom pad) |
| ADC inputs | Ch 9–12 | **Ch 13–16** |
| DAC outputs | Unused | **Unused — leave open** |

------

## Power Supply Connections

Each AK4619VN codec requires the following power connections:

| Pin | Name | Rail | Decoupling |
|-----|------|------|-----------|
| 18 | AVDD | 3.3 V_A | 100 nF ceramic to VSS1, close to pin |
| 3 | TVDD | 3.3 V_A | 100 nF ceramic to VSS2, close to pin |
| 19 | VSS1 | GND (analog) | — |
| 4 | VSS2 | GND (digital) | — |
| 5 | AVDRV | (LDO output) | 2.2 µF ceramic (±50%) to VSS2 |
| 17 | VCOM | (AVDD/2 output) | 2.2 µF ceramic (±50%) to VSS1 |
| 20 | VREFL | VSS1 | Direct connection |
| 21 | VREFH | AVDD | Direct connection |
| — | Exposed Pad | VSS1 | Solder to ground pour |

**Power architecture relationship:**

```
PWR USB-C (5V, Power Board) → cable → TPS22965 → Main Board 5V rail
                                                        ↓
                                              MEJ2S0505SC isolated DC-DC (×2, on Main Board)
                                                        ↓
                                              FFC pins 12-13 (5V_ISO, paralleled)
                                                        ↓
                                      Ferrite bead (600Ω) → 10 µF ceramic (post-filter)
                                                        ↓
                                    ADP7118 LDO (on each Input Mother Board) → 3.3V_A
                                                                                  ↓
                                                              AVDD (pin 18) + TVDD (pin 3) on each codec
```

Each Input Mother Board has its own ADP7118 LDO, converting the galvanically isolated 5V_ISO supply to a clean 3.3V_A rail for its two codecs. A ferrite bead + ceramic cap post-filter between the FFC and ADP7118 input attenuates DC-DC switching ripple. Combined with ADP7118 PSRR (>60 dB), total rejection at the DC-DC switching frequency exceeds 100 dB.

A third ADP7118 on the Main Board provides 3.3V_A for the virtual ground buffer (digital domain). The HP amp receives 5V_ISO and Master L/R audio from Board 1-top via a dedicated 4-pin JST-PH cable.

VSS1 and VSS2 connect to a common GND_ISO plane on each Mother Board — galvanically isolated from the digital domain's GND.

**Critical notes:**
- AVDRV (pin 5) is the internal 1.2 V LDO output. Do NOT connect to any other device or load — decoupling cap only.
- VCOM (pin 17) outputs AVDD/2 (~1.65 V). Do NOT connect to other devices — decoupling cap only.
- Place decoupling caps as close to the codec pins as possible (< 5 mm trace length).

------

## Analog I/O Configuration

### Input Mode: Single-Ended

MIXTEE uses **single-ended 1** input mode for all channels. This is configured via register 0Bh (ADC Analog Input Setting):

| ADC Channel | Register Bits | Value | Active Pin |
|------------|--------------|-------|-----------|
| ADC1 Lch | AD1LSEL[1:0] | 01 | AIN1L (pin 16) |
| ADC1 Rch | AD1RSEL[1:0] | 01 | AIN1R (pin 14) |
| ADC2 Lch | AD2LSEL[1:0] | 01 | AIN4L (pin 12) |
| ADC2 Rch | AD2RSEL[1:0] | 01 | AIN4R (pin 10) |

Register 0Bh value: **0x55** (all channels = single-ended 1).

Each active input pin connects through the Sallen-Key anti-alias filter and OPA1678 input buffer on the Input Mother Board. Unused alternate input pins (AIN2L, AIN2R, AIN5L, AIN5R on pins 15, 13, 11, 9) are left open per datasheet section 5.3.

### Input Pin Assignments

| Codec | ADC1L (pin 16) | ADC1R (pin 14) | ADC2L (pin 12) | ADC2R (pin 10) |
|-------|---------------|---------------|---------------|---------------|
| U1 | Ch 3 | Ch 4 | Ch 1 | Ch 2 |
| U2 | Ch 7 | Ch 8 | Ch 5 | Ch 6 |
| U3 | Ch 11 | Ch 12 | Ch 9 | Ch 10 |
| U4 | Ch 15 | Ch 16 | Ch 13 | Ch 14 |

### Output Pin Assignments

DAC outputs are used on **U1 and U2 only** (Board 1-top). U3/U4 DAC sections are powered down and outputs left open.

| Codec | AOUT1L (pin 22) | AOUT1R (pin 23) | AOUT2L (pin 24) | AOUT2R (pin 25) |
|-------|----------------|----------------|----------------|----------------|
| U1 | Main L | Main R | AUX1 L | AUX1 R |
| U2 | AUX2 L | AUX2 R | AUX3 L | AUX3 R |
| U3 | Open (unused) | Open (unused) | Open (unused) | Open (unused) |
| U4 | Open (unused) | Open (unused) | Open (unused) | Open (unused) |

------

## Register Initialization Sequence

### Power-Up Timing

1. Apply AVDD and TVDD with PDN pin held **low**
2. After power supplies are stable, set PDN pin **high**
3. Wait **≥ 10 ms** for internal LDO and reference to stabilize
4. Registers are now accessible via I2C
5. Write configuration registers (steps below)
6. Supply MCLK, BICK, LRCK clocks from Teensy SAI
7. Set power management bits to start ADC/DAC

### Register Configuration (per codec)

```
// Step 0: Select TCA9548A mux channel for the target codec board
//   Ch 0 = Board 1-top (U1, U2), Ch 1 = Board 2-top (U3, U4)
Wire.beginTransmission(0x70);      // TCA9548A address
Wire.write(1 << mux_channel);      // 0x01 for Ch 0, 0x02 for Ch 1
Wire.endTransmission();

// Step 1: Set audio interface format — TDM128, I2S compatible, 32-bit slots
//   TDM=1, DCF[2:0]=010, DSL[1:0]=11, BCKP=0, SDOPH=0
Wire.beginTransmission(i2c_addr);  // 0x10 or 0x11
Wire.write(0x01);                  // Register 01h
Wire.write(0xAC);                  // 1_010_11_0_0 = 0xAC
Wire.endTransmission();

// Step 2: Set slot/word length — SLOT=1, DIDL=32-bit, DODL=24-bit
Wire.beginTransmission(i2c_addr);
Wire.write(0x02);                  // Register 02h
Wire.write(0x1C);                  // 000_1_11_00 = 0x1C
Wire.endTransmission();

// Step 3: Set system clock — FS[2:0]=000 (MCLK=256fs, fs≤48kHz)
Wire.beginTransmission(i2c_addr);
Wire.write(0x03);                  // Register 03h
Wire.write(0x00);                  // 00000_000 = 0x00
Wire.endTransmission();

// Step 4: Set analog input mode — all channels single-ended 1
Wire.beginTransmission(i2c_addr);
Wire.write(0x0B);                  // Register 0Bh
Wire.write(0x55);                  // AD1LSEL=01, AD1RSEL=01, AD2LSEL=01, AD2RSEL=01
Wire.endTransmission();

// Step 5: Set MIC gain — 0 dB for all channels (default 0x22 per register)
//   Registers 04h, 05h — default values are fine, skip unless gain needed

// Step 6: Power up ADCs and DACs, release reset
//   For U1/U2 (ADC + DAC): PMAD2=1, PMAD1=1, PMDA2=1, PMDA1=1, RSTN=1
Wire.beginTransmission(i2c_addr);
Wire.write(0x00);                  // Register 00h
Wire.write(0x37);                  // 00_11_0_11_1 = 0x37
Wire.endTransmission();

//   For U3/U4 (ADC only): PMAD2=1, PMAD1=1, PMDA2=0, PMDA1=0, RSTN=1
Wire.beginTransmission(i2c_addr);
Wire.write(0x00);                  // Register 00h
Wire.write(0x31);                  // 00_11_0_00_1 = 0x31
Wire.endTransmission();

// Step 7: Wait for ADC initialization (1056/fs = ~22 ms at 48 kHz)
delay(25);

// Codec is now operational
```

### Key Register Summary

| Addr | Register | MIXTEE Value | Default | Purpose |
|------|----------|-------------|---------|---------|
| 00h | Power Management | 0x37 (U1/U2) or 0x31 (U3/U4) | 0x00 | Enable ADCs, DACs, release reset |
| 01h | Audio I/F Format | 0xAC | 0x0C | TDM128, I2S compatible, 32-bit slots |
| 02h | Slot/Word Length | 0x1C | 0x0C | SLOT=1, DIDL=32-bit, DODL=24-bit |
| 03h | System Clock | 0x00 | 0x00 | MCLK=256fs, fs ≤ 48 kHz (default OK) |
| 04h | MIC Gain (ADC1) | 0x22 | 0x22 | 0 dB L+R (default OK) |
| 05h | MIC Gain (ADC2) | 0x22 | 0x22 | 0 dB L+R (default OK) |
| 0Bh | Analog Input Mode | 0x55 | 0x00 | All channels single-ended 1 |

------

## Unused Pin Handling

Per datasheet section 5.3:

| Classification | Pins | Handling |
|---------------|------|---------|
| Unused analog inputs | AIN2L (15), AIN2R (13), AIN5L (11), AIN5R (9) | **Leave open** |
| Unused analog outputs (U3/U4) | AOUT1L (22), AOUT1R (23), AOUT2L (24), AOUT2R (25) | **Leave open** |
| Unused digital inputs | SDIN2 (2), SI (29) | **Connect to VSS2** |
| Unused digital outputs | SDOUT2 (32) | **Leave open** |

------

## Design Investigation Items

The following items require validation during Phase 1 breadboard bring-up:

### 1. TDM Multi-Codec Bus Sharing

**Status:** Resolved — separate SDOUT lines per codec.

Each codec gets its own SDOUT → SAI RX data pin (U1→pin 8 RX_DATA0, U2→pin 32 RX_DATA1, U3→pin 5 RX_DATA0, U4→pin 34 RX_DATA1). Requires PJRC Audio Library modification to enable SAI multi-data-line receive (SAI_RCR3 register). FFC pin 5 carries codec 1 SDOUT and FFC pin 7 carries codec 2 SDOUT on each cable (via Si8662BB reverse channels). See "Separate SDOUT Lines" section above and pin-mapping.md for full details.

### 2. Clock Compatibility with PJRC TDM Library

**Status:** Needs verification.

The PJRC TDM library generates BCLK at 24.576 MHz (16 slots × 32 bits × 48 kHz), but the AK4619VN in TDM128 mode expects BICK = 128fs = 6.144 MHz (4 slots × 32 bits × 48 kHz). Verify that the Teensy SAI peripheral can be configured for 128fs BCLK instead of the library's default 512fs, or confirm that the codec can tolerate the faster clock with only 4 of 16 slots populated.

### 3. SDOUT Pin Drive Strength

**Status:** Low risk.

Verify that the AK4619VN SDOUT1 can drive the FFC cable trace (40–50 mm) at 6.144 MHz without signal integrity issues. The pin has a 50 kΩ pull-down in power-down state — confirm it drives adequately in normal operation.

### 4. PDN Pin Control Strategy

**Status:** Resolved.

- **Board 1-top:** PDN controlled via MCP23008 GPIO (GP4 for U1, GP5 for U2) on the isolated I2C bus. Allows firmware-controlled reset/power-down during boot sequencing and debugging.
- **Board 2-top:** PDN tied to TVDD via 10 kΩ (always-on when powered). MCP23008 footprint present but unpopulated on Board 2-top.
