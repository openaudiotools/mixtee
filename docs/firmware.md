# MIXTEE: Firmware

*← Back to [README](../README.md) | See also: [Features](features.md) · [Hardware](hardware.md) · [UI Architecture](ui-architecture.md)*

------

## Firmware Framework

- **Platform:** Arduino/Teensyduino (PJRC Audio Library)
- **Audio Processing:** Block-based (128 samples @ 48 kHz = 2.67 ms latency)
- **Routing Engine:** 16→8 matrix mixer with per-crosspoint gain

------

## Key Libraries

- **Audio:** PJRC Audio Library (AudioInputTDM, AudioOutputTDM, AudioMixer4)
- **Encoders:** PJRC Encoder Library (quadrature decoding)
- **Buttons:** PJRC Bounce Library (debouncing)
- **Display:** Offloaded to ESP32-S3 integrated display module (LVGL); Teensy sends meter data + parameter state over Serial1 UART (pins 0/1)
- **NeoPixels:** Adafruit NeoPixel or FastLED (level-shifted data output)
- **USB Audio Bridge:** XMOS XU216 handles multichannel USB audio (24-in/8-out); Teensy communicates MIDI via SPI0 (pins 10–13)
- **MIDI:** USBHost_t36 (Teensy USB Host library)
- **SD Card:** SdFat (Bill Greiman) with SDIO support (built into Teensyduino)
- **PSRAM:** extmem allocation (Teensy core EXTMEM keyword for PSRAM-backed buffers)

------

## Audio DSP Chain

### Monolithic ChannelStrip Architecture

Each input channel uses a single `AudioChannelStrip` object that combines the entire per-channel signal path into one `update()` call:

**Per-channel signal path (fixed at compile time):**

Input (TDM ADC) → Gain → Pan/Balance → EQ (3× biquad) → Send taps (Aux1/2/3) → Level → Mute → Main bus summing → Peak/RMS metering

Each `AudioChannelStrip` processes one 128-sample block per channel per audio callback. Gain, pan, 3-band EQ (biquad filters), send taps, level, mute, and peak/RMS metering are all computed inline within a single object — no per-stage AudioStream connections or separate AudioAnalyzePeak/AudioAnalyzeRMS objects.

**Why monolithic:** The PJRC Audio Library dispatches each AudioStream object individually (~270 objects in a naive implementation). Per-object overhead (virtual dispatch, block allocation/release, connection traversal) dominates at this scale. Combining per-channel DSP into ~16 monolithic objects eliminates ~250 object dispatches per audio block.

**Object count:** ~80 total (16× AudioChannelStrip + 40× AudioMixer4 for bus summing + 2× AudioInputTDM + 2× AudioOutputTDM + 16× AudioRecordQueue + misc)

**EQ implementation:**

- 3-band fixed EQ per input channel: Low shelf @ 200 Hz, Mid bell @ 1 kHz (Q ≈ 0.7–1.0), High shelf @ 5 kHz
- 48 total biquad filter instances (3 bands × 16 channels), computed inline within ChannelStrip
- Biquad coefficients pre-computed at fixed frequencies; only gain param changes at runtime
- Coefficient recalculation on gain change: ~1–2 µs per band (sin/cos for shelf/bell formula), negligible vs. 2.67 ms block time
- Spread coefficient updates across successive audio blocks if multiple channels change simultaneously (e.g., MIDI CC burst)

**Metering:** Peak and RMS values computed inline during the ChannelStrip processing loop — no separate analysis objects. The ChannelStrip exposes `peak()` and `rms()` methods that return the most recent block's values.

### CPU Budget Estimate

| Subsystem                          | Estimated CPU |
| ---------------------------------- | ------------- |
| TDM receive (16 ch)               | ~2–3%         |
| TDM transmit (8 ch)               | ~1–2%         |
| ChannelStrip (16 ch, inline DSP)  | ~8–12%        |
| Mixer matrix (16→8 crosspoints)   | ~5–8%         |
| Recording interleave to PSRAM     | ~1–2%         |
| Object dispatch overhead           | ~2–3%         |
| **Total audio DSP**               | **~20–30%**   |

Headroom: ~70% CPU available for non-audio tasks (UART display link, MIDI, SD writes, UI logic). Object dispatch overhead drops from ~50–100% of block time (with ~270 individual objects) to ~2–3% (with ~80 monolithic objects).

Profile with `AudioProcessorUsage` and `AudioProcessorUsageMax` during Phase 1 breadboard bringup to validate estimates.

------

## State Management

- Channel state: gain, pan, mute, solo, sends, EQ band levels, record arm (per channel)
- Pair state: stereo link mode, enabled/disabled (per pair)
- Global state: UI focus (selected channel, nav depth, current view/page/module/component), meter hold
- Recording state: idle/armed/recording, armed channels bitmask, elapsed time, file size, buffer fill level
- Selected channel: global variable set at Page level, persists across nav depth changes; Mute/Solo/Rec buttons always resolve to this channel
- MIDI state: 14-bit mode enable flag (per channel group or per parameter type, default: off/7-bit)

------

## UI Update Loop

- **Audio callback:** 44.1/48 kHz, real-time priority
- **Meter analysis:** Every audio block (peak + RMS computed inline in ChannelStrip)
- **UART meter transmission:** Teensy sends 24 peak/RMS float pairs to ESP32-S3 at 30 Hz (~6 KB/s); parameter state sent on change
- **Input polling:** Encoders (interrupt-driven), buttons (Bounce debounce), MIDI (event-driven)

### Priority Model

The PJRC Audio Library runs on a timer interrupt and preempts all other code. The firmware must be structured so that no non-audio task holds shared resources (memory) long enough to cause audio buffer underruns. Key considerations:

- **Display communication** is handled via Serial1 UART (pins 0/1) to the ESP32-S3 display module — lightweight, non-blocking, DMA-capable. No SPI bus contention with display rendering. The Teensy sends meter data (24 float pairs at 30 Hz) and parameter state changes; the ESP32-S3 handles all rendering independently.
- **SD card writes** use SDIO DMA and run from the main loop at lowest priority. The PSRAM ring buffer decouples recording from real-time audio.
- **NeoPixel updates** are fast (8 pixels, microseconds) and non-blocking.
- **MIDI parsing** is event-driven via USBHost_t36 callbacks (for USB MIDI controllers) — lightweight and non-blocking. The MIDI handler resolves `MIDI channel → channel group` (Ch 1: inputs 1–8, Ch 2: inputs 9–16, Ch 3: outputs), then `CC number → parameter + channel offset`. Uniform parsing, no special cases per group.
- **XMOS MIDI exchange** is polled from the main loop via SPI0 (pins 10–13) at ~1 kHz. USB MIDI messages from the PC arrive at the XMOS and are forwarded to Teensy over SPI; Teensy sends outbound MIDI to XMOS for USB transmission to PC. Adds <1 ms latency vs. native USB MIDI. The same CC parsing logic handles both USB host MIDI (controllers) and PC MIDI (via XMOS SPI).

### Noise Mitigation (Firmware)

- **Cap NeoPixel global brightness** (30% default recommended — reduces noise and power; hardware is sized for uncapped operation)
- **Smooth parameter changes** (no abrupt steps in gain/pan — use ramping over 1-2 audio blocks)
- **USB host power management** (ability to power-cycle ports via software)
- **Pop suppression sequencing:** On boot, hold output mute relay/switch closed until DSP is initialized and stable (~500 ms), then ramp up. On shutdown (voltage drop detected), ramp down and mute before power loss.
