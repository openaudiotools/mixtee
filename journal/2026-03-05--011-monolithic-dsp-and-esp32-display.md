# Monolithic DSP Architecture + ESP32-S3 Display Offload

**Date:** 2026-03-05

## Summary

Research session analyzed Teensy 4.1 RAM usage, audio block pool mechanics, PSRAM speed limitations, and explored alternative platforms. Two concrete architectural decisions emerged:

1. **Monolithic ChannelStrip objects** — replace ~270 individual PJRC Audio Library objects with ~80 custom objects
2. **ESP32-S3 integrated display module** — offload all display rendering from Teensy to an ESP32-S3 module with built-in LCD

## Teensy 4.1 Memory Architecture

| Region | Size | Speed | Use |
|--------|------|-------|-----|
| DTCM (tightly coupled) | 512 KB | 0-wait-state | Audio buffers, stack, hot variables |
| OCRAM (FlexRAM) | 512 KB | ~2 cycle | General heap, large arrays |
| PSRAM (external QSPI) | 8 MB | ~330 cycles random | Recording ring buffer only |

**Key finding:** PSRAM is unsuitable for DSP buffers due to ~330-cycle random access latency. Current spec fits in ~1 MB (DTCM + OCRAM), but the audio object count (~270 in a naive implementation) is the real scalability risk — per-object dispatch overhead (virtual calls, block alloc/free, connection traversal) dominates at that count.

## Monolithic ChannelStrip Approach

Combine gain, pan, 3-band EQ (biquads), send taps, level, mute, and peak/RMS metering into a single `AudioChannelStrip` object per channel. Metering computed inline during processing — no separate AudioAnalyzePeak/AudioAnalyzeRMS objects.

| Metric | Before (naive) | After (monolithic) |
|--------|----------------|-------------------|
| Audio objects | ~270 | ~80 |
| Object dispatch overhead | ~50–100% of block time | ~2–3% |
| Block pool pressure | High (each connection = alloc + free) | Low (internal buffers) |

Object breakdown: 16 ChannelStrip + 40 AudioMixer4 (bus summing) + 2 AudioInputTDM + 2 AudioOutputTDM + 16 AudioRecordQueue + misc.

## ESP32-S3 Display Offload

Replace bare 4.3" TFT + RA8875 controller with an ESP32-S3 integrated display module (e.g., Waveshare ESP32-S3-Touch-LCD-4.3 or Elecrow 4.3" CrowPanel).

**What it frees on Teensy:**
- SPI0 bus (4 pins: CS, MOSI, MISO, SCK)
- 2 GPIO pins (RA8875 INT + RESET)
- 7–27% CPU (display rendering was the most intensive non-audio task)
- SPI bus contention with audio eliminated

**Communication:** UART (2 wires: TX/RX) at 30 Hz for meter data (~6 KB/s). Parameter state sent on change. Lightweight, non-blocking, DMA-capable.

**ESP32-S3 runs LVGL** — a professional embedded UI framework with hardware-accelerated rendering, smooth animations, and anti-aliased fonts. Resolution upgrade possible (800×480 on Waveshare vs. 480×272 on RA8875).

## Platform Comparison (Explored, Not Adopted)

| Platform | Verdict | Blocker |
|----------|---------|---------|
| Raspberry Pi | Rejected | No native TDM/I2S multi-channel; Linux latency |
| STM32H7 | Best upgrade path | Only needed if internal effects required |
| XMOS | Pro/commercial tier | Overkill for current scope |
| Daisy Seed (STM32H750) | Blocked | Only 1 free SAI port (other used by onboard codec) |
| Double-Teensy | Deferred | Effects not in current scope; revisit if needed |

## Decisions

- **Adopt monolithic ChannelStrip DSP objects** for current phase
- **Adopt ESP32-S3 integrated display module** to replace RA8875 TFT
- **External effects only** via aux sends (no internal FX processing)
- **Second Teensy / Daisy Seed deferred** — effects expansion not in current scope
