# MIXTEE: Features

*← Back to [README](../README.md) | See also: [Hardware](hardware.md) · [Firmware](firmware.md) · [UI Architecture](ui-architecture.md)*

------

## Control Interface

### On-Device Controls

**3× Rotary Encoders with Push:**

- **NavX Encoder (left, below display):** Horizontal navigation — scroll laterally within current depth; push = drill down one level
- **NavY Encoder (center, below display):** Vertical navigation — scroll between pages/rows; push = context action
- **Edit Encoder (right, below display):** Adjust value of focused parameter; push = confirm / drill into focused element

**16× Mechanical Key Switches (custom PCB, CHOC hotswap, 4×4 grid):**

- Layout: 4×4 grid below display (all 16 keys in one block)
- Button mapping:
  - Row 1 (channel controls): Mute, Solo, Rec, (assignable)
  - Row 2: (assignable), (assignable), (assignable), (assignable)
  - Row 3: (assignable), (assignable), (assignable), (assignable)
  - Row 4 (navigation): Home, Back, Page, Shift
- **Mute/Solo/Rec:** Depth-independent — always act on the currently selected channel regardless of navigation depth
- **Home:** Hard reset to Overview (clears navigation stack, returns to top-level overview)
- **Back:** Navigate up one level in the hierarchy
- **Page:** Hold Page + turn Nav encoder to scroll vertically between pages within a view
- **Shift:** Modifier key (hold + other key for alternate functions)
- Custom PCB per key group with Kailh CHOC hotswap sockets, WS2812B-2020 NeoPixels (daisy-chained, single data pin), 100nF decoupling cap per LED
- 16 switches scanned via MCP23017 I2C GPIO expander (4×4 matrix with anti-ghosting diodes, on Key PCB)

### Display

**Custom display PCB** with ESP32-S3-WROOM-1-N16R8 + bare 4.3" 800×480 capacitive touch LCD panel. See [Display Rationale](display/rationale.md) for why custom PCB over integrated module.

- Custom PCB: ESP32-S3-WROOM-1-N16R8 (16 MB flash, 8 MB PSRAM) + 40-pin RGB LCD panel + GT911/CST340 touch controller
- Resolution: 800×480 — wider aspect ratio suits horizontal channel strip layout
- ESP32-S3 runs a **device-agnostic LVGL display engine** — no device-specific knowledge; reusable across MIXTEE, SYNTEE, and future devices
- Teensy streams binary widget commands over UART at 921600 baud (COBS-encoded frames with CRC16); see [Display Protocol](display/protocol.md)
- UI layout defined in `ui.json` on SD card — Teensy parses JSON, translates to binary protocol commands, streams to ESP32
- 6-pin connection: UART TX/RX + ESP32_EN + GPIO0 (bootloader control) + 5V + GND
- Per-channel strip width: 120 px × display height (mono pair occupies 2 strips)
- Stereo-linked pairs occupy 2 slots but grouped visually
- 30 Hz meter update rate via METER_BATCH command (~4.6 KB/s); parameter state sent on change
- Touch events forwarded from ESP32 to Teensy as coordinate-based events (ESP32 never interprets touch semantics)
- Frees SPI0 bus on Teensy (no display SPI bus contention)

### SD Card Update

Single update mechanism for all firmware — no separate flashing tools required. See [SD Update](sd-update.md).

- **User experience:** Copy update files to SD card → insert → power on → done
- **Update package:** `/UPDATE/` folder on SD card containing `manifest.json`, `teensy.hex`, `display.bin`, `ui.json`
- **Teensy self-update** via FlasherX library (reads .hex from SD, writes to flash, reboots)
- **ESP32 reflash** via `esp-serial-flasher` library (Teensy drives ESP32_EN/GPIO0 pins to enter bootloader, streams binary over UART, ~16s)
- **UI layout update:** `ui.json` copied to `/SYSTEM/ui.json` — no reflash needed for UI-only changes
- Version tracking via Teensy EEPROM — only components with version mismatches are updated
- Power-loss safe: FlasherX writes upper flash first, vector table last; HalfKay USB bootloader ROM is never overwritten (USB recovery always possible)

### Color Scheme

- **Main:** Default black — primary text, borders, UI chrome
- **Fill:** Main at 75% — backgrounds, inactive areas, meter ticks
- **Accent:** Default red — active states, record indicators, warnings, selected highlights
- **Inverse:** Inverse of Main — selected button states, focused elements (white on black)

*Colors are configurable in firmware; defaults chosen for maximum contrast on TFT.*

### Navigation Model

The UI uses a 4-level hierarchical navigation model. See [UI Architecture](ui-architecture.md) for full details on the View/Page/Module/Component framework.

**Hierarchy:** Global → Page → Module → Component

**Navigation Rules:**

- **Nav encoder:** Move laterally within the current depth (views at Global, modules at Page, components at Module, params at Component)
- **PAGE + Nav:** Move vertically between pages within a view
- **Push Nav:** Drill down one level
- **Edit encoder:** Adjust the default parameter of the focused element
- **Push Edit:** Drill into the focused element
- **Back:** Go up one level
- **Home:** Hard reset to Overview (clears navigation stack)
- **Mute/Solo/Rec:** Always act on the selected channel, depth-independent

**View Boundary Crossing:**

When navigating laterally past the last channel in a view, the Nav encoder crosses into the neighboring view at the same page level:

- Inputs 1–8, past channel 8 → Inputs 9–16, focus channel 9 (same page)
- Inputs 9–16, past channel 16 → Outputs, focus first output bus
- Reverse direction: same logic, focus the last element of the previous view
- Page level is preserved across transitions (e.g., EQ page stays on EQ page)
- If the destination view has fewer pages, clamp to the last available page

**Context Behavior Table:**

| Context   | Nav ↻         | PAGE + Nav ↻  | Push Nav   | Edit ↻              | Push Edit     |
| --------- | ------------- | ------------- | ---------- | -------------------- | ------------- |
| Global    | Navigate views | Navigate pages | Enter page | ×                    | ×             |
| Page      | Select modules | Navigate pages | Enter module | Edit default module param | Enter module  |
| Module    | Select components | Navigate pages | Enter component | Edit default component param | Enter component |
| Component | Select params | Navigate pages | ×          | Edit selected param   | ×             |

### Scope Constraints

- **No internal FX for now.** The mixer does not include built-in effects processing (reverb, delay, compression, etc.). Aux sends route to external FX gear. Internal FX may be added in a future revision as additional modules.
- **Signal path is hardcoded.** The DSP audio graph is fixed at compile time. UI modules provide windows into different points of the fixed graph; rearranging modules on screen does not rearrange DSP processing order.

------

## State Management

### Save Behavior

- **Manual save:** User-triggered via key combo or menu action
- **Shutdown save:** Soft power button press triggers firmware to save current state to SD before load switch releases power
- State includes: all channel levels, pan, EQ, mute/solo, send levels, record arm states, and UI navigation position
- Future: named scenes and projects (larger save files, multiple snapshots)

### Power

- Soft power button (momentary) on back panel (next to PWR USB-C) controls TPS22965 load switch via wire to Main Board
- Power-on: press → load switch latches → Teensy boots → last saved state restored from SD
- Power-off: press → firmware flushes state to SD → confirms write complete → load switch releases

------

## DAW Audio (AES67 over Ethernet)

MIXTEE provides **16-in / 8-out network audio** to any DAW via AES67 over the Ethernet port (RJ45 MagJack on IO Board, 100 Mbps). No USB audio bridge — MIXTEE speaks standard AES67, and users install an existing virtual soundcard on their DAW host.

- **To DAW (16 in):** 16 pre-mix ADC inputs as 2× 8-channel AES67 streams
- **From DAW (8 out):** DAW playback returns routed into mixer as 1× 8-channel AES67 stream
- **Format:** 24-bit, 48 kHz, 1 ms packet time (L24 RTP)
- **Discovery:** SAP/SDP for AES67 interop; mDNS/DNS-SD for JFA ecosystem
- **OS support:** PipeWire (Linux, built-in); AES67 macOS Driver (beta); DIGISYN VSC (Windows, early-stage); commercial options available

See [network-connectivity.md](network-connectivity.md) §9 for stream layout, AES67 compliance details, and recommended virtual soundcards.

------

## MIDI Control

### MIDI Host Configuration

- **2× USB-A host ports** (dual stacked, top panel)
- Self-powered hub architecture (500 mA per port)
- Accepts standard MIDI controllers (Akai MIDImix, Korg nanoKONTROL Studio, Launch Control XL, etc.)
- Users map their controllers to the mixer's CC spec

### MIDI IN / OUT

- **MIDI IN:** 3.5mm TRS Type A input with 6N138 optocoupler isolation (Serial3 RX, pin 15)
- **MIDI OUT:** 3.5mm TRS Type A output (Serial4 TX, pin 17) — standard MIDI current-loop at 31.25 kbaud
- Software MIDI THRU: incoming MIDI IN messages can be forwarded to MIDI OUT (configurable)
- Teensy-generated MIDI: firmware can send CC/note messages out MIDI OUT (e.g., parameter feedback, sync)

### MIDI CC Map (Per-Channel-Group)

MIDI channels are assigned to groups of 8 channels. This allows a single 8-fader/knob controller to map 1:1 to a channel group — the user switches MIDI transmit channel on their controller to flip between input banks.

**MIDI Ch 1 — Inputs 1–8 (8 channels, all params):**

- CC1–CC8: Gain ch1-8 (0=min, 127=max)
- CC9–CC16: Pan ch1-8 (0=left, 64=center, 127=right)
- CC17–CC24: Mute ch1-8 (0-63=off, 64-127=on)
- CC25–CC32: Solo ch1-8 (0-63=off, 64-127=on)
- CC33–CC40: Send 1 level ch1-8 (0=min, 127=max; target: Aux1)
- CC41–CC48: Send 2 level ch1-8 (0=min, 127=max; target: Aux2)
- CC49–CC56: Send 3 level ch1-8 (0=min, 127=max; target: Aux3)
- CC57–CC64: EQ Low level ch1-8 (0=−12 dB, 64=flat, 127=+12 dB)
- CC65–CC72: EQ Mid level ch1-8 (0=−12 dB, 64=flat, 127=+12 dB)
- CC73–CC80: EQ High level ch1-8 (0=−12 dB, 64=flat, 127=+12 dB)

**MIDI Ch 2 — Inputs 9–16 (identical CC layout, offset by channel group):**

- Same CC numbers as Ch 1, controlling channels 9–16

**MIDI Ch 3 — Outputs (4 stereo buses):**

- CC1–CC4: Output bus master level (Aux1, Aux2, Aux3, Main)
- CC5–CC8: Output bus mute (0-63=off, 64-127=on)
- Remaining CCs reserved for future output bus EQ, global controls, record start/stop

*Rationale: Grouping by 8 channels mirrors the physical layout (Inputs 1–8, Inputs 9–16) and the TDM bus assignment (TDM1, TDM2). A single 8-fader controller maps directly to one group. Switching the controller's MIDI transmit channel flips between banks with zero relearning.*

**14-bit MIDI CC Pairs (Future / Configurable):**

- Standard MIDI spec pairs CC0–31 (MSB) with CC32–63 (LSB) for 14-bit resolution
- When enabled, provides 16,384 steps instead of 128 — eliminates audible stepping on gain and EQ sweeps
- Firmware setting: 7-bit (default, all controllers) or 14-bit (per channel group or per parameter type)
- Backward-compatible: if no LSB received, MSB treated as standard 7-bit
- Note: enabling 14-bit on all params exceeds the 0–31 MSB range (10 params × 8 ch = 80 CCs); prioritize gain, pan, and EQ bands for 14-bit support

**Behavior:**

- All CCs absolute 7-bit by default (0-127)
- Controller-agnostic design (users configure their hardware)
- Optional soft-takeover/pickup mode to prevent jumps

------

## Mixing & Routing

### Channel Processing

**Per Input Channel (signal order):**

- Gain (0 to 0 dB, adjustable curve)
- Pan/Balance (equal-power or linear law, implemented as L/R gains in software)
- 3-Band Fixed EQ:
  - Low shelf @ 200 Hz
  - Mid bell @ 1 kHz (Q ≈ 0.7–1.0)
  - High shelf @ 5 kHz
  - Gain range: ±12 dB per band
  - Implementation: 3× biquad filters per channel (48 total), pre-computed coefficients at fixed frequencies, recalculated on gain change only
  - MIDI mapping: 64 = flat (0 dB), 0 = −12 dB, 127 = +12 dB (~0.19 dB/step in 7-bit)
  - CPU impact: ~4–6% total for all 48 biquads (see [Firmware](firmware.md))
- Mute (instant)
- Solo (solo bus, mutes non-soloed channels)
- Send levels (Send 1/2/3 to Aux 1/2/3)
- Level (post-EQ, post-send tap, to Main bus)

**Stereo Pair Linking:**

- Dual-mono mode: two independent channels (separate gain/mute/pan/EQ)
- Stereo mode: shared gain/mute/EQ, pan becomes balance

### Bus Architecture

- **Main (Out 4):** Default master mix, always stereo
- **Aux 1-3 (Out 1-3):** Stereo aux/FX sends
- Each input has 4 send levels (Main + Aux1 + Aux2 + Aux3)
- All sends accessible via Sends module on Page 2 of input views (see [UI Architecture](ui-architecture.md))

### Send Configuration

- **Sends 1–3:** All visible on the Sends module page (accessible by scrolling down from the main strip page on any input view)
- Send levels displayed as vertical bars labeled A1, A2, A3 per channel
- All sends are stereo (maintain L/R into stereo buses)
- Pre/post fader: configurable later (start with post-fader for simplicity)

------

## Multitrack Recording

### Hardware

- **Storage:** Teensy 4.1 built-in micro SD card slot (4-bit SDIO interface, ~20-25 MB/s write)
- **Buffer memory:** 8 MB PSRAM chip (e.g., IPS6404LSQ or AP Memory APS6404L) soldered to Teensy 4.1 QSPI pads
  - Provides ~3.5 seconds of buffer at full 16-channel data rate
  - Absorbs SD card write latency spikes (100-250 ms typical on consumer cards)
  - PJRC sells PSRAM as a pre-tested add-on; also available from standard distributors
- **SD card requirement:** UHS-I U3 / V30 rated minimum (30 MB/s sustained write)
  - Recommend 32-64 GB for practical session lengths
  - Pre-format with large cluster size (64 KB) for contiguous writes

### Data Rate & Capacity

- **16 channels × 48 kHz × 24-bit = 2.3 MB/s** sustained write
- **Per-hour storage:** ~8.3 GB
- **32 GB card:** ~3.5 hours continuous recording
- **64 GB card:** ~7 hours continuous recording

### Recording Architecture

**Signal tap point:** Post-ADC, pre-mixer (records dry input signals for full remix flexibility in a DAW)

**Buffer strategy:**

- 16× `AudioRecordQueue` objects tap TDM input channels
- Audio callback interleaves samples into PSRAM ring buffer (producer)
- Main loop drains PSRAM ring buffer to SD card via SDIO DMA (consumer)
- Ring buffer size: ~4-6 MB of PSRAM dedicated to recording (remainder available for other uses)
- Buffer health monitored: if fill level exceeds 80%, display shows warning indicator

**File format:**

- Single 16-channel interleaved WAV file (BWF/RF64 for files >4 GB)
  - One file handle, one sequential write stream — minimizes filesystem contention
  - RF64 extension handles files beyond the 4 GB WAV limit transparently
  - Most DAWs (Reaper, Ableton, Logic, Pro Tools) import multichannel WAV natively
- Filename: auto-generated timestamp (e.g., `MIXTEE_2026-02-25_14-30-00.wav`)
- File pre-allocated as contiguous block before recording starts (`createContiguous()` via SdFat)
  - Eliminates filesystem fragmentation stalls during recording

**Post-recording utility:**

- Firmware menu option to split multichannel WAV into individual mono WAV files on the SD card
- Alternatively, a Python script in the repository for splitting on a computer
- Channel naming metadata embedded in WAV file (BWF iXML or cue chunk) for DAW import

### User Interface

- **Record button (Row 1, position 3):** Global record start/stop
  - NeoPixel: solid red = recording, blinking red = armed/standby, off = idle
- **Per-channel record arming:**
  - Each input channel has an arm/disarm toggle visible on the channel strip (circle indicator)
  - Armed: filled red circle; disarmed: hollow circle
  - Arming is set via the on-device UI (navigate to channel, toggle arm)
  - Only armed channels are recorded — reduces data rate for longer sessions when fewer than 16 channels are needed
  - All channels armed by default on boot
- **Display overlay:** When recording active, show elapsed time, file size, and buffer health bar
- **Record modes:**
  - Immediate: press Record to start, press again to stop
  - Armed: press Record to arm (button blinks), recording starts on first audio above threshold on any armed channel (configurable)
- **Safe stop:** Firmware finalizes WAV header and flushes buffer on stop; also on power-loss detection via voltage monitoring (if supply drops below 4.5V, auto-stop and flush)

### Future Recording Enhancements

- Record post-fader / post-mixer for stems (Main L/R, Aux1 L/R, etc.)
- MIDI CC trigger for remote record start/stop
- Per-channel arm/disarm via MIDI CC

### CPU & Resource Impact

- **CPU:** ~1-2% additional (interleaving and buffer management are memory copies)
- **SDIO DMA:** Runs in background, does not block audio or UI
- **PSRAM bandwidth:** QSPI at 133 MHz provides ~30 MB/s, shared with any other PSRAM users — recording needs ~4.6 MB/s (read + write), well within budget
- **No impact** on mixer DSP, metering, display refresh, or MIDI responsiveness
