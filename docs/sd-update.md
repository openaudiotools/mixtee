# MIXTEE: SD Card Update Mechanism

*← Back to [README](../README.md) | See also: [Firmware](firmware.md) · [Display Protocol](display/protocol.md) · [Features](features.md)*

------

## Overview

MIXTEE uses a **single SD card update mechanism** for all firmware components. The user copies an update package to the SD card, inserts it, and powers on — everything updates automatically. No USB flashing tools, no separate processes for Teensy and ESP32.

This mechanism is standardized across all devices in the Open Audio Tools family (MIXTEE, SYNTEE, etc.).

------

## Update Package Format

```
/UPDATE/
  manifest.json     ← versions, checksums, device ID
  teensy.hex        ← Teensy 4.1 firmware (FlasherX format, Intel HEX)
  display.bin       ← ESP32-S3 display engine firmware (app binary)
  ui.json           ← UI layout definition
```

All components are optional — if a file is missing from the package, that component is skipped. This allows UI-only updates (just `manifest.json` + `ui.json`) without reflashing firmware.

### manifest.json

```json
{
  "device": "MIXTEE",
  "versions": {
    "teensy": "1.2.0",
    "display": "1.1.0",
    "ui": "1.0.3"
  },
  "checksums": {
    "teensy.hex": "sha256:a1b2c3d4...",
    "display.bin": "sha256:e5f6a7b8...",
    "ui.json": "sha256:c9d0e1f2..."
  }
}
```

**Fields:**
- `device` — Must match the device ID stored in Teensy EEPROM. Prevents accidentally flashing wrong firmware.
- `versions` — Semantic version strings for each component. Compared against EEPROM-stored current versions.
- `checksums` — SHA-256 hashes for integrity verification before flashing.

------

## Boot Sequence

```
Power on → Teensy boots
  │
  ├─ Check SD for /UPDATE/manifest.json
  │   │
  │   ├─ NOT FOUND → Normal boot (skip to step 7)
  │   │
  │   └─ FOUND → Parse manifest
  │       │
  │       ├─ Verify device ID matches
  │       │   └─ MISMATCH → Log error, skip update, normal boot
  │       │
  │       ├─ Verify checksums for all present files
  │       │   └─ MISMATCH → Log error, skip update, normal boot
  │       │
  │       ├─ Step 1: Teensy self-update (if version differs)
  │       │   └─ FlasherX reads teensy.hex → writes to flash → reboots
  │       │   └─ On reboot: re-enters this sequence, teensy version now matches
  │       │
  │       ├─ Step 2: ESP32 reflash (if version differs)
  │       │   └─ Assert GPIO0 LOW (pin 10)
  │       │   └─ Pulse EN LOW/HIGH (pin 9) → ESP32 enters bootloader
  │       │   └─ Stream display.bin over Serial1 @ 921600 baud
  │       │   └─ ~16 seconds for 1.5 MB binary
  │       │   └─ Reboot ESP32 into normal mode
  │       │
  │       ├─ Step 3: Copy ui.json → /SYSTEM/ui.json (if version differs)
  │       │
  │       ├─ Step 4: Update EEPROM version records
  │       │
  │       └─ Step 5: Rename /UPDATE/ → /UPDATE_DONE/
  │
  └─ Step 7: Normal boot
      ├─ Send HANDSHAKE to ESP32
      ├─ Receive READY + screen capabilities
      ├─ Parse /SYSTEM/ui.json (~5 ms)
      ├─ Stream CREATE_WIDGET commands to ESP32 (~200 ms)
      ├─ Send BOOT_COMPLETE
      └─ Enter normal operation
```

------

## Version Tracking

Teensy EEPROM stores:

| Offset | Size | Content |
|--------|------|---------|
| 0x00 | 4 bytes | Magic number (0x4D495854 = "MIXT") |
| 0x04 | 3 bytes | Teensy firmware version (major.minor.patch) |
| 0x07 | 3 bytes | Display firmware version (major.minor.patch) |
| 0x0A | 3 bytes | UI layout version (major.minor.patch) |
| 0x0D | 16 bytes | Device ID string ("MIXTEE\0...") |

Only components with version mismatches between EEPROM and `manifest.json` are updated. This avoids unnecessary reflash cycles.

------

## Teensy Self-Update (FlasherX)

**Library:** [FlasherX](https://github.com/joepasquariello/FlasherX) (MIT license)

FlasherX enables Teensy 4.x self-programming from an SD card:

1. Reads Intel HEX file (`teensy.hex`) from SD card
2. Writes firmware to upper flash first, then copies to lower flash
3. Writes vector table last — if power is lost mid-write, the previous firmware remains intact
4. Triggers soft reboot to run new firmware

**Safety guarantees:**
- **HalfKay ROM bootloader is never overwritten** — USB recovery via Teensy Loader is always possible even after a failed update
- Upper-flash-first write order means partial writes leave the old firmware runnable
- Checksum verification before write begins

**Flash time:** ~2–3 seconds for a typical Teensy firmware image.

------

## ESP32 Reflash (esp-serial-flasher)

**Library:** [esp-serial-flasher](https://github.com/espressif/esp-serial-flasher) (Apache 2.0 license, by Espressif)

This embedded host library allows a microcontroller (Teensy) to flash an ESP32 target over UART — the same protocol used by `esptool.py`, but running on the Teensy itself.

### Hardware Requirements

| Teensy Pin | Signal | Purpose |
|-----------|--------|---------|
| 9 | ESP32_EN | Reset control (active-high, module has internal pull-up) |
| 10 | ESP32_GPIO0 | Boot mode select (LOW = UART bootloader) |
| 0 | Serial1 RX | ESP32 TX (bootloader responses) |
| 1 | Serial1 TX | ESP32 RX (firmware data) |

These signals are carried on the 6-pin display header. See [Main Board connections](../hardware/pcbs/main/connections.md#esp32-s3-display-header-6-pin).

### Reflash Sequence

1. Teensy asserts GPIO0 LOW (pin 10)
2. Teensy pulses EN LOW for ~100 ms, then releases HIGH (pin 9)
3. ESP32-S3 boots into UART download mode
4. Teensy negotiates baud rate up to 921600 via `esp-serial-flasher` SYNC protocol
5. Teensy streams `display.bin` in 1 KB blocks with per-block checksums
6. ESP32 writes to flash, ACKs each block
7. After last block: Teensy releases GPIO0 (HIGH-Z)
8. Teensy pulses EN to reboot ESP32 into normal app mode

**Flash time:** ~16 seconds for a 1.5 MB binary at 921600 baud.

### Progress Indication

During ESP32 reflash, the Teensy drives the NeoPixel LEDs as a progress bar (no display available since the ESP32 is in bootloader mode). All 16 LEDs fill left-to-right as flashing progresses.

------

## File System Layout

```
SD Card Root
├── /UPDATE/                  ← User places update files here
│   ├── manifest.json
│   ├── teensy.hex
│   ├── display.bin
│   └── ui.json
│
├── /UPDATE_DONE/             ← Renamed after successful update
│   └── (previous update files)
│
├── /SYSTEM/
│   └── ui.json               ← Active UI layout (copied from update)
│
└── /RECORDINGS/              ← Multitrack WAV recordings
    └── MIXTEE_2026-03-09_14-30-00.wav
```

------

## Error Handling

| Condition | Behavior |
|-----------|----------|
| manifest.json parse error | Log error to `/SYSTEM/update.log`, skip update, normal boot |
| Device ID mismatch | Log error, skip update, normal boot |
| Checksum mismatch | Log error for specific file, skip that component |
| FlasherX write failure | Previous firmware remains intact (upper-first write order). HalfKay USB recovery available. |
| ESP32 flash failure | Retry up to 3 times. On failure: log error, continue boot without display. NeoPixels show error pattern (all red). |
| Power loss during Teensy flash | Previous firmware runs on next boot. HalfKay ROM bootloader always available for USB recovery. |
| Power loss during ESP32 flash | ESP32 remains in bootloader-accessible state. Next boot retries the update (manifest still in /UPDATE/). |
| ui.json missing from /SYSTEM/ | Teensy sends hardcoded minimal UI (single page with error message) |

------

## User Experience

### First-Time Setup

1. Download update package from project website
2. Extract to SD card root (creates `/UPDATE/` folder)
3. Insert SD card into MIXTEE
4. Power on
5. NeoPixels show update progress (~20 seconds total)
6. MIXTEE boots normally with updated firmware and UI

### Subsequent Updates

Same process — only components with version changes are reflashed.

### No-Update Boot

If `/UPDATE/manifest.json` is not found, MIXTEE boots normally in <3 seconds. No delay from update checking.

------

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| ESP32 EN/GPIO0 inaccessible | Custom display PCB guarantees direct access to EN and GPIO0 — not dependent on third-party module pinout |
| Power loss during FlasherX | Upper-flash-first write order + HalfKay ROM = always recoverable via USB |
| ESP32 reflash takes too long | 921600 baud after SYNC (~16s for 1.5 MB); NeoPixel progress indicator |
| Wrong update package for device | `device` field in manifest.json must match EEPROM; prevents cross-device flashing |
| Corrupted download | SHA-256 checksums verified before any write begins |
| SD card removed during update | Same as power loss — safe due to write ordering and retry-on-next-boot |
