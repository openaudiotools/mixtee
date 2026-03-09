# MIXTEE: Display Architecture Rationale

*← Back to [README](../../README.md) | See also: [Display Protocol](protocol.md) · [SD Update](../sd-update.md) · [Firmware](../firmware.md)*

------

## Overview

MIXTEE offloads all display rendering to a dedicated ESP32-S3 rather than driving the LCD directly from the Teensy 4.1. This is not about CPU horsepower — the Teensy has cycles to spare. It is about protecting real-time audio from the one subsystem that routinely breaks real-time guarantees: graphics.

------

## Recommended Hardware

**Custom display PCB** with:

- **MCU:** ESP32-S3-WROOM-1-N16R8 (16 MB flash, 8 MB PSRAM)
- **LCD panel:** 4.3" 800×480 capacitive touch, 40-pin RGB interface (e.g., a bare panel from Waveshare, BuyDisplay, or equivalent — no integrated controller board)
- **Touch controller:** GT911 or CST340 (typically integrated in the LCD FPC)

This replaces the earlier approach of using an off-the-shelf integrated display module (Waveshare/Elecrow dev board). A custom PCB gives us direct control over boot control pins (EN, GPIO0), power sequencing, FPC routing, backlight drive, and board outline — none of which are guaranteed on third-party dev boards.

### Why custom PCB over integrated module

| Concern | Integrated module | Custom PCB |
|---------|------------------|------------|
| EN / GPIO0 access | May or may not be broken out; varies by revision | Guaranteed — routed to 6-pin header |
| Board outline / mounting | Fixed by vendor; may not fit enclosure | Designed to MIXTEE enclosure dimensions |
| Backlight control | Usually always-on or vendor-controlled | PWM-dimmable via ESP32 GPIO |
| BOM cost (volume) | ~$20–25 per module | ~$8–12 (WROOM-1 + bare panel + passives) |
| Supply risk | Single vendor, may EOL | Standard WROOM module + generic LCD panel |

### Connection to Teensy

6-pin JST-PH header (same pinout as previous design):

| Pin | Signal | Purpose |
|-----|--------|---------|
| 1 | 5V | Power (from 5V_DIG rail) |
| 2 | GND | Ground |
| 3 | UART TX | Teensy Serial1 TX → ESP32 RX |
| 4 | UART RX | Teensy Serial1 RX ← ESP32 TX |
| 5 | ESP32_EN | Reset control (Teensy pin 9) |
| 6 | GPIO0 | Boot mode select (Teensy pin 10) |

------

## System Architecture

### Rendering Split

The Teensy is the brain; the ESP32 is a dumb renderer.

| Responsibility | Owner |
|---------------|-------|
| UI layout definitions | `ui.json` on SD card, parsed by Teensy at boot |
| Widget creation commands | Teensy (translates JSON → binary protocol) |
| LVGL widget rendering | ESP32-S3 display engine (generic, no device knowledge) |
| Meter data streaming | Teensy → ESP32 (METER_BATCH at 30 Hz, ~4.6 KB/s) |
| Parameter updates | Teensy → ESP32 (SET_VALUE/SET_TEXT on change) |
| Touch input | ESP32 → Teensy (coordinate-based events) |
| Touch interpretation | Teensy (maps coordinates to UI elements) |

### The core problem: display rendering is hostile to real-time audio

The Teensy 4.1 runs block-based DSP at 48 kHz with 128-sample blocks — a hard deadline every 2.67 ms. Any task that blocks the CPU for longer than that causes audible glitches. Display rendering is one of the few subsystems that can routinely exceed this budget:

- **SPI bus contention.** A 480×272 16-bit framebuffer is ~261 KB. Even at 60 MHz SPI, a full refresh takes ~35 ms — 13× the audio block time. Partial updates help but still produce unpredictable multi-millisecond bursts. Meanwhile the SD card (multitrack recording) also needs SPI or SDIO bandwidth.
- **LVGL tick processing.** LVGL's `lv_timer_handler()` performs layout recalculation, animation stepping, and dirty-region rendering in a single call. Duration varies from microseconds (idle) to several milliseconds (page transition, multiple widget updates). This variability is the enemy of real-time — you cannot bound it tightly enough to guarantee zero audio glitches.
- **Memory pressure.** LVGL needs 50–80 KB of heap for the full MIXTEE UI (128 widgets across multiple pages). The Teensy has 1 MB RAM, but the audio library, PSRAM ring buffers, and recording interleave buffers already compete for it. Adding a graphics heap introduces fragmentation risk in a system that must never fail an allocation during audio processing.
- **Interrupt priority conflicts.** The Teensy's audio runs in a timer interrupt at high priority. SPI DMA completion interrupts, touch controller I2C reads, and LVGL tick callbacks all compete for interrupt slots. On a single-core MCU with no hardware task isolation, every interrupt source is a potential jitter source for the audio path.

### What the ESP32-S3 buys us

Moving rendering to a separate chip eliminates all of these concerns:

| Problem | Solution with separate controller |
|---------|----------------------------------|
| SPI bus contention | Display SPI/RGB bus is entirely on the ESP32 PCB — zero shared bandwidth with Teensy |
| Unpredictable render time | LVGL runs on the ESP32's own cores — render duration is invisible to Teensy |
| Memory fragmentation | LVGL heap lives in ESP32 PSRAM — Teensy RAM is 100% audio/recording |
| Interrupt conflicts | Touch controller interrupts handled by ESP32 — Teensy never sees them |
| CPU jitter | Teensy communicates via UART (DMA, <1 µs per byte) — no multi-ms blocking calls |

The Teensy-to-ESP32 link is a thin UART stream: ~4.8 KB/s for 30 Hz meter data, plus occasional parameter updates. This is orders of magnitude lighter than driving a display directly, and it is fully non-blocking (hardware UART with DMA).

### Why not just use DMA and careful scheduling?

You can drive a display from a real-time audio MCU — commercial mixers do it. But it requires:

- Dedicated DMA channels for display SPI, carefully interleaved with audio DMA
- Custom display drivers that break rendering into sub-millisecond chunks
- Extensive profiling and worst-case timing analysis
- Giving up features (animations, smooth scrolling, anti-aliased fonts) that exceed the time budget

This is significant engineering effort for a result that is still fragile — any future UI change could accidentally exceed the timing budget. The separate controller approach eliminates the entire class of problems and lets the UI evolve freely.

------

## PCB and Firmware Notes

### Display PCB design considerations

- **FPC connector:** 40-pin 0.5mm FPC for RGB interface to LCD panel. Route RGB data lines as a group with matched lengths (±2mm tolerance is fine at RGB pixel clock speeds).
- **Backlight driver:** ESP32 GPIO → MOSFET → LED anode string. PWM dimming at ~25 kHz avoids audible whine. Backlight current set by series resistor (panel datasheet specifies typical 40–60 mA).
- **Boot control:** EN and GPIO0 directly routed to 6-pin header. 10kΩ pull-up on EN, 10kΩ pull-up on GPIO0 (both with 1µF decoupling for clean reset). Teensy can override both to enter UART bootloader for reflash.
- **Power:** 3.3V regulator on-board (AMS1117-3.3 or equivalent) fed from 5V via the 6-pin header. Keep digital and backlight power separate with ferrite bead filtering.
- **Decoupling:** Standard ESP32-S3 decoupling per Espressif hardware design guidelines (22µF + 0.1µF on each VDD pin group).

### Reusability across devices

Because the ESP32 display engine is device-agnostic (it only knows widgets, not mixer concepts), the same firmware runs on MIXTEE, SYNTEE, and any future Open Audio Tools device. Each device ships its own `ui.json` layout file — the display engine is identical. This means:

- One display firmware to maintain, test, and optimize
- New devices get a working display by writing a JSON file, not by porting graphics code
- Community contributors can redesign the UI without touching firmware on either side

------

## Why Not a Secondary Teensy?

A common question: why use an ESP32-S3 instead of a second Teensy 4.1 as the display controller?

### The showstopper: no UART reflash path

The Teensy 4.1 uses the **HalfKay USB bootloader** burned into ROM. It can only be programmed via USB — there is no UART bootloader. This means:

- The main Teensy cannot reflash a secondary Teensy over UART
- SD card update would require the secondary Teensy to self-update via its own FlasherX instance, which means it needs its own SD card access or USB connection
- The single-cable update flow (main Teensy controls everything) is impossible

The ESP32-S3 has a **UART bootloader in ROM** (the same one `esptool.py` uses). The main Teensy can enter it by toggling EN/GPIO0 and stream firmware over the existing Serial1 link. This is what makes the unified SD card update work.

### Comparison

| Factor | ESP32-S3 (WROOM-1-N16R8) | Teensy 4.1 |
|--------|--------------------------|------------|
| UART reflash from host MCU | Yes (ROM bootloader) | No (HalfKay is USB-only) |
| LVGL + RGB LCD support | Native (ESP-IDF, Arduino) | Possible but no RGB peripheral |
| PSRAM for framebuffer | 8 MB on-module (WROOM-1-N16R8) | Requires external PSRAM soldering |
| Cost | ~$3–4 (WROOM module) | ~$30 (dev board) |
| Display ecosystem | Mature (ESP-IDF display drivers, LVGL ESP port) | Minimal (no official display stack) |
| Wi-Fi/BLE (future) | Built-in | Not available |

The ESP32-S3 is purpose-built for this role. A secondary Teensy would be more expensive, harder to update, and less capable for display tasks.

------

## Why a Single Update Flow

MIXTEE has three independently versioned firmware components:

1. **Teensy firmware** (`teensy.hex`) — DSP, routing, control logic
2. **ESP32 display firmware** (`display.bin`) — LVGL rendering engine
3. **UI layout** (`ui.json`) — widget definitions, page structure, bindings

Without a unified update mechanism, users would need to know which components changed, use different tools for each (Teensy Loader for Teensy, esptool.py for ESP32, manual file copy for ui.json), and get the order right. This is fine for developers; it is unacceptable for a consumer-facing device.

### The problem with separate update paths

- **Multiple tools.** Teensy uses HalfKay USB bootloader (requires Teensy Loader app). ESP32 uses UART bootloader (requires esptool.py or Arduino IDE). UI layout is a file copy. Three different procedures, three different failure modes.
- **Version coupling.** A Teensy firmware update may depend on a matching display engine version (new widget type, changed protocol). If the user updates one but not the other, the device breaks silently — meters don't render, touch doesn't work, pages are missing.
- **Ordering matters.** The Teensy must be updated before the ESP32 (since the Teensy drives the ESP32 reflash process). If a user updates the ESP32 first via some external tool, the old Teensy firmware may not speak the new protocol.
- **No computer required.** MIXTEE is a standalone hardware device. Many users will operate it without a connected computer. USB-based update flows require a PC, a specific app, and platform-specific drivers. SD card update requires only a card reader.

### How the single flow works

The user copies one folder (`/UPDATE/`) to the SD card. On next power-on, the Teensy:

1. Validates `manifest.json` — checks device ID (prevents cross-device flashing) and SHA-256 checksums (prevents corrupted files)
2. Self-updates via FlasherX if the Teensy version differs — safe because it writes upper flash first, vector table last; power loss at any point leaves old firmware intact
3. Reflashes the ESP32 via esp-serial-flasher if the display version differs — the Teensy controls EN/GPIO0 pins on the custom display PCB to enter the ESP32's UART bootloader, then streams the binary
4. Copies `ui.json` to `/SYSTEM/` if the UI version differs
5. Records new versions in EEPROM and renames `/UPDATE/` → `/UPDATE_DONE/`

Any component can be omitted from the package — a UI-only update skips both firmware reflashes. Version comparison prevents redundant reflash cycles.

### Why this is safe

- **Teensy self-update (FlasherX):** Writes to upper flash first, copies to lower flash, writes vector table last. If power is lost at any point, the previous firmware boots normally. The HalfKay ROM bootloader is never overwritten — USB recovery via Teensy Loader is always possible, even after a catastrophic failure.
- **ESP32 reflash (esp-serial-flasher):** If flashing fails or power is lost, the ESP32 stays in a bootloader-accessible state. On next boot, the Teensy retries (manifest is still in `/UPDATE/`). Worst case: the device boots without a display and shows a NeoPixel error pattern.
- **No bricking path.** Both the Teensy (HalfKay ROM) and ESP32 (UART bootloader in ROM) have hardware-level recovery that cannot be overwritten by software. The custom display PCB guarantees EN/GPIO0 pin access — no risk of a module revision removing these pins.

### Why SD card, not USB or OTA

| Method | Pros | Cons for MIXTEE |
|--------|------|----------------|
| USB (Teensy Loader / esptool) | Fast, developer-friendly | Requires PC + apps + drivers; two separate tools; not standalone |
| OTA (Wi-Fi) | Convenient for connected devices | MIXTEE has no Wi-Fi on the Teensy; ESP32 Wi-Fi is dedicated to display; adds attack surface |
| SD card | No PC required; single flow; works offline; simple UX | Requires SD card reader for initial copy; slightly slower |

SD card is the right trade-off for a standalone audio device. The SD card slot already exists for multitrack recording — no additional hardware cost. The update check adds zero latency to normal boot (just a file-exists check).
