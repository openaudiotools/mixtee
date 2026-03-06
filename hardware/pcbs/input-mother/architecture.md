# Input Mother Board — Architecture

*← Back to [README](README.md)*

This document covers the detailed analog circuit design, power regulation, I2C addressing, and BOM variant strategy for the Input Mother Board.

------

## Analog Input Stage (per channel)

- **Input impedance:** 10 kOhm
- **Input voltage range:** +/-5V peak (Eurorack, +4 dBu, -10 dBV)
- **Topology:** Non-inverting buffer with adjustable attenuation
  - Op-amp: OPA1678 (4.5 nV/sqrt(Hz), rail-to-rail output)
  - AC-coupled input (10uF + 10kOhm -> ~1.6 Hz HPF)
- **Anti-alias filter:** 2nd-order Sallen-Key LP, fc ~ 22 kHz, Butterworth
  - Component values: ~3.3 nF + ~6.8 nF, ~1 kOhm + ~1 kOhm
  - ~40 dB/decade rolloff above Nyquist at 48 kHz
- **ESD protection:** Schottky clamp diodes to rails on all input jacks

------

## Output Analog Stage (Board 1-top only, per channel)

- **Topology:** Active reconstruction filter + line driver
  - Op-amp: OPA1678
  - 2nd-order Sallen-Key LP, fc ~ 22 kHz
- **Output impedance:** ~100 Ohm series resistor
- **Output level:** 0 dBu nominal (+4 dBu max)
- **DC blocking:** 47uF AC coupling cap
- **Pop suppression:** TS5A3159 mute switch **on this board** (Board 1-top), post-driver, controlled via MCP23008 I2C GPIO — see below

------

## Op-Amp Selection

| Parameter | OPA1678 (recommended) | NJM4580 (alternate) |
|-----------|----------------------|---------------------|
| Noise density | 4.5 nV/sqrt(Hz) | 8 nV/sqrt(Hz) |
| THD+N | 0.00005% | 0.001% |
| GBW | 24 MHz | 15 MHz |
| Supply range | 4.5–36V | +/-2–18V |
| Package | SOIC-8 / TSSOP-8 | DIP-8 / SOIC-8 |
| Cost | $1.20 | $0.80 |

Op-amps run single-supply on 5V with 2.5V virtual ground biasing (generated on Main Board). OPA1678 rail-to-rail output gives ~3.5Vpp usable swing — sufficient for +4 dBu.

------

## TS5A3159 Pop Suppression + MCP23008 Control (Board 1-top only)

4× TS5A3159 analog switch ICs (SOT-23-5), one per output stereo pair, placed post-reconstruction filter and post-line driver. Controlled by an **MCP23008 I2C GPIO expander** (address 0x21) on the isolated I2C bus.

| MCP23008 GPIO | Function |
|---------------|----------|
| GP0 | TS5A3159 IN — mute Main L/R |
| GP1 | TS5A3159 IN — mute AUX1 L/R |
| GP2 | TS5A3159 IN — mute AUX2 L/R |
| GP3 | TS5A3159 IN — mute AUX3 L/R |
| GP4 | Codec U1 PDN control (optional) |
| GP5 | Codec U2 PDN control (optional) |
| GP6 | Headphone detect input (from HP Board jack detect switch) |
| GP7 | Spare |

- MCP23008 address 0x21 (A0=1, A1=A2=0) — distinct from MCP23017 (0x20) and codecs (0x10/0x11)
- Accessed via TCA9548A Ch 0 → ISO1541 (isolated I2C path)
- Firmware sets mute outputs low during boot, high after DSP stabilizes (~500 ms)
- **Board 2-top:** MCP23008 + TS5A3159 footprints present but **unpopulated**; codec PDN tied to TVDD via 10k

### Headphone Detect via MCP23008

The HP Board's TRS jack detect switch connects to MCP23008 GP6 on Board 1-top. Teensy reads this via I2C polling (~100 Hz) instead of a dedicated GPIO pin. Teensy pin 39 is freed.

------

## Headphone Amp Cable Connector (Board 1-top only)

4-pin JST-PH connector providing Master L/R audio and isolated power to the standalone HP Board. Signals are post-TS5A3159 mute, post-line driver. See [connections.md](connections.md#headphone-amp-cable-4-pin-jst-ph-board-1-top-only) for pinout.

------

## Power: Isolated Supply + ADP7118 LDO

### Isolated Power Input

5V_ISO arrives from the Main Board via FFC pins 12–13 (paralleled). This is galvanically isolated power from a Murata MEJ2S0505SC DC-DC converter on the Main Board.

### Post-Filter

```
FFC 5V_ISO → ferrite bead (600Ω @ 100 MHz) → 10 µF ceramic → ADP7118 input
```

The ferrite bead + ceramic cap attenuates DC-DC switching ripple. ADP7118 PSRR (>60 dB at switching frequency) provides additional rejection — combined >100 dB total rejection at the DC-DC switching frequency.

### ADP7118 LDO

- Each Input Mother Board has its own ADP7118 (5V_ISO → 3.3V_A)
- Ultra-low noise: <10 uV RMS
- Powers both AK4619VN codec AVDD/TVDD pins
- Entire board runs on GND_ISO — no connection to system GND

------

## I2C Address Selection

- Solder jumpers select TCA9548A mux channel (Ch 0 = Board 1-top, Ch 1 = Board 2-top)
- U1/U3: CAD pin low -> 0x10; U2/U4: CAD pin high -> 0x11
- Same PCB design for both instances

------

## BOM Variant

- **Board 1-top:** fully populated (8× input buffers, 8× anti-alias filters, 4× output reconstruction filters, 4× line drivers, 4× TS5A3159 mute, MCP23008, HP amp cable connector)
- **Board 2-top:** output section + mute/control section left unpopulated (DAC sections unused, TS5A3159 and MCP23008 footprints present but not populated; codec PDN tied to TVDD via 10k)
