# USB Audio Interface

*← Back to [README](../README.md) | See also: [Hardware](hardware.md) · [Firmware](firmware.md) · [System Topology](system-topology.md)*

------

## Architecture: XMOS XU216 USB Audio Bridge

MIXTEE uses a dedicated **XMOS XU216** chip as a USB Audio Class 2 bridge, providing **24-in / 8-out multichannel audio** to any DAW over a single USB-C connection. This is the same approach used by commercial interfaces (Focusrite, MOTU, SSL, Behringer). The Teensy handles all DSP; the XMOS acts purely as a USB↔TDM bridge.

### Channel Layout

**To PC (24 input channels):**

| USB Ch | Source | TDM bus | Data line |
|--------|--------|---------|-----------|
| 1–4 | ADC inputs 1–4 (codec U1) | SAI1 | RX_DATA0 (pin 8) |
| 5–8 | ADC inputs 5–8 (codec U2) | SAI1 | RX_DATA1 (pin 32) |
| 9–12 | ADC inputs 9–12 (codec U3) | SAI2 | RX_DATA0 (pin 5) |
| 13–16 | ADC inputs 13–16 (codec U4) | SAI2 | RX_DATA1 (pin 34) |
| 17–24 | Bus outputs 1–8 (post-mixer) | SAI1 | TX_DATA0 (pin 7) |

**From PC (8 return channels):** DAW playback routed into the mixer. Return data line and SAI assignment TBD — requires iMXRT1062 IOMUX validation during breadboard phase (candidates: SAI1_RX_DATA2 on pin 9, SAI3, or SPI DMA transfer).

### How It Works

The XMOS runs as a **TDM slave**, passively listening to the existing TDM bus signals. It adds no load to the audio path — the same BCLK, LRCLK, and data lines that connect Teensy to the AK4619VN codecs are simply tapped by high-impedance CMOS inputs on the XMOS.

```
  AK4619 codecs ←── TDM Bus 1 (SAI1) ──→ Teensy 4.1 ←── TDM Bus 2 (SAI2) ──→ AK4619 codecs
  (inputs 1-8,       BCLK/LRCLK/DATA            │          BCLK/LRCLK/DATA      (inputs 9-16)
   outputs 1-8)                                   │
                                                  │  passive TDM tap (all data lines)
                                                  │  + SPI control bus (MIDI forwarding)
                                                  │  + return audio data line (TBD)
                                                  ↓
                                            XMOS XU216
                                                  │
                                              USB 2.0 HS
                                                  │
                                          PC USB-C port
                                     (24-in / 8-out audio + MIDI)
```

### USB Device Identity

The XMOS presents as a **USB Audio Class 2 composite device**:

- **Audio:** 24-in / 8-out, 24-bit, 48 kHz
- **MIDI:** 1 port (MIDI messages forwarded between PC ↔ Teensy via SPI)
- **Format:** UAC2, asynchronous/adaptive mode

### OS Compatibility

| OS | Driver | ASIO | Notes |
|----|--------|------|-------|
| macOS | Native (class-compliant) | Core Audio | Plug and play, all 24+8 channels |
| Linux | Native (snd-usb-audio) | ALSA/JACK | Plug and play, all 24+8 channels |
| Windows | Thesycon (bundled with XMOS ref design) | ASIO 2.3.1 | Full multichannel ASIO, low latency |

Windows driver is included in the [XMOS sw_usb_audio](https://github.com/xmos/sw_usb_audio) reference design — no licensing cost for open-source projects.

### Clocking

- **Teensy remains TDM clock master** — generates MCLK (12.288 MHz), BCLK (24.576 MHz), LRCLK (48 kHz)
- **XMOS runs in TDM slave / USB adaptive mode** — locks its USB feedback to Teensy's BCLK
- No firmware changes to Teensy's Audio Library clock configuration

------

## XMOS Hardware

### Chip: XU216-256-TQ128-C20

- 128-pin TQFP, 256 KB RAM, 2000 MIPS (16 cores, 2 tiles)
- ~$5 (LCSC/DigiKey)
- Open-source firmware: [xmos/sw_usb_audio](https://github.com/xmos/sw_usb_audio)
- 3 lanes of TDM8 = 24 channels (proven configuration)

### Support Components

| Component | Purpose | Est. cost |
|-----------|---------|-----------|
| 24 MHz crystal + 2× load caps | XMOS core clock | ~$0.50 |
| 24.576 MHz crystal (audio PLL ref) | Audio clock reference | ~$0.50 |
| W25Q32 QSPI flash (4 MB) | XMOS firmware storage | ~$0.50 |
| 1.0V LDO (e.g., AP2112K-1.0) | XMOS core supply | ~$0.30 |
| 3.3V — shared with existing rail | XMOS I/O supply | $0 |
| Decoupling caps (0.1 µF × ~10) | Power filtering | ~$0.50 |
| USBLC6-2 | USB ESD protection | ~$0.20 |
| **Total (excluding XU216)** | | **~$3** |
| **Total (including XU216)** | | **~$8** |

### Power

- Core: 1.0V @ ~150 mA (dedicated LDO)
- I/O: 3.3V @ ~50 mA (shared rail)
- Total: ~200 mA additional on 5V rail (through LDOs)

------

## Communication: XMOS ↔ Teensy

### Audio (TDM passive tap)

9 signals tapped from existing TDM buses — no additional Teensy pins consumed:

| Signal | Source | XMOS pin type |
|--------|--------|--------------|
| SAI1 BCLK (pin 21) | Teensy | Clock input |
| SAI1 LRCLK (pin 20) | Teensy | Frame sync input |
| SAI1 RX_DATA0 (pin 8) | Codec U1 | Data input (ch 1–4) |
| SAI1 RX_DATA1 (pin 32) | Codec U2 | Data input (ch 5–8) |
| SAI1 TX_DATA0 (pin 7) | Teensy | Data input (bus out 1–8) |
| SAI2 BCLK (pin 4) | Teensy | Clock input |
| SAI2 LRCLK (pin 3) | Teensy | Frame sync input |
| SAI2 RX_DATA0 (pin 5) | Codec U3 | Data input (ch 9–12) |
| SAI2 RX_DATA1 (pin 34) | Codec U4 | Data input (ch 13–16) |

### MIDI Forwarding (SPI)

USB MIDI from the PC arrives at the XMOS. MIDI messages are forwarded to/from the Teensy over the freed **SPI0 bus (pins 10–13)**:

| Teensy Pin | SPI Function | Direction |
|-----------|-------------|-----------|
| 10 | CS | Output (Teensy selects XMOS) |
| 11 | MOSI | Teensy → XMOS (MIDI TX to PC) |
| 12 | MISO | XMOS → Teensy (MIDI RX from PC) |
| 13 | SCK | Clock |

Polled at ~1 kHz from main loop. MIDI latency: <1 ms additional vs. native USB.

### Return Audio (PC → Mixer)

8 channels from DAW playback. Data line and Teensy SAI assignment TBD — candidates:

- **Pin 9 as SAI1_RX_DATA2** — uses existing SAI1 clocks, minimal firmware change
- **SAI3** — fully independent bus, requires IOMUX pin mapping validation
- **SPI DMA** — software-defined, no SAI constraints

To be validated during breadboard Phase 1. The XMOS firmware and TDM tap architecture are independent of this choice.

------

## USB Port Reassignment

| Port | Before | After |
|------|--------|-------|
| PC USB-C (top panel) | Teensy USB device (stereo audio + MIDI) | **XMOS USB** (24ch audio + MIDI) |
| Teensy native USB | PC audio/MIDI | Debug/firmware-update only |

The PC USB-C connector on the Main Board is re-routed from Teensy's USB device pads to the XMOS USB pads. Teensy's native USB port remains accessible via a debug header (or optionally a second USB-C on the back panel) for firmware updates.

------

## Fallback / Legacy Options

If the XMOS is omitted (e.g., cost-reduced build), the Teensy's native USB can still provide:

- **UAC1 stereo:** 2-in / 2-out, 16-bit 44.1 kHz (zero cost, firmware only)
- **UAC2 firmware (alex6679):** Up to 8 channels on macOS/Linux; Windows capped at 8ch without commercial driver

See [alex6679/teensy-4-usbAudio](https://github.com/alex6679/teensy-4-usbAudio) for the community UAC2 implementation.
