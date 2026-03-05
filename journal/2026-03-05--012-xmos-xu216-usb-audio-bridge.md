# XMOS XU216 USB Audio Bridge — 24ch Multichannel to DAW

**Date:** 2026-03-05

## Summary

Added an XMOS XU216 USB Audio Class 2 bridge to the Main Board design. MIXTEE now provides 24-in / 8-out multichannel audio + USB MIDI over a single USB-C connection to the PC. This replaces the previous plan of stereo-only USB audio (UAC1) via Teensy's native USB.

## Motivation

- All 24 channels (16 pre-mix inputs + 8 bus outputs) needed in DAW for multitrack recording and mixing
- Teensy-only USB audio limited to stereo (UAC1) or max 8ch on Windows (firmware UAC2 + native driver cap)
- XMOS is the industry-standard approach (used by Focusrite, MOTU, SSL, Behringer)
- Cross-platform: class-compliant on macOS/Linux, Thesycon ASIO driver on Windows (included in XMOS reference design)

## Architecture

| Aspect | Detail |
|--------|--------|
| Chip | XU216-256-TQ128-C20 (~$5, 128-pin TQFP, 256KB RAM) |
| Audio to PC | 24ch: 16 ADC inputs + 8 bus outputs via passive TDM tap |
| Audio from PC | 8ch return (data line TBD — pin 9 candidate) |
| MIDI | USB MIDI composite; forwarded to Teensy via SPI0 (pins 10–13) |
| USB port | PC USB-C re-routed from Teensy → XMOS |
| Clocking | Teensy stays TDM master; XMOS runs TDM slave / USB adaptive |
| Firmware | Open-source [xmos/sw_usb_audio](https://github.com/xmos/sw_usb_audio) |
| Total added cost | ~$8 (XU216 + crystals + flash + LDO + caps + ESD) |
| Power impact | +~200 mA on 5V rail (1.0V core + 3.3V I/O) |

## Pin Changes

| Pin(s) | Before | After |
|--------|--------|-------|
| 0, 1 | Spare (Serial1 debug) | Serial1 — ESP32-S3 display UART |
| 9 | Spare (was RA8875 INT) | Candidate: XMOS return audio (SAI1_RX_DATA2) |
| 10–13 | Spare (freed SPI0) | SPI0 — XMOS control bus (MIDI forwarding) |

## Open Items

- [ ] Validate pin 9 IOMUX for SAI1_RX_DATA2 (return audio path)
- [ ] XMOS TDM slave configuration with 2 independent TDM buses (different BCLK sources from SAI1 vs SAI2)
- [ ] SPI MIDI forwarding protocol spec (packet format, error handling)
- [ ] PCB layout: XMOS placement near USB-C connector, crystal routing, power plane partitioning

## Files Updated

- `docs/usb-audio.md` — rewritten as XMOS-primary
- `docs/hardware.md` — BOM tables, power budget, PC USB-C description
- `docs/pin-mapping.md` — pin reassignments, XMOS connections, verification checklist
- `docs/firmware.md` — XMOS communication in priority model
- `docs/system-topology.md` — XMOS added to main board summary
- `hardware/pcbs/main/architecture.md` — XMOS subsystem section
- `hardware/pcbs/main/connections.md` — PC USB-C rerouting, XMOS↔Teensy connections
- `hardware/bom.csv` — XMOS + support components
- `docs/features.md` — USB audio section updated
- `CLAUDE.md` — architecture summary updated
