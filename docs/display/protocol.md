# MIXTEE: Display Engine Protocol

*← Back to [README](../../README.md) | See also: [UI Architecture](../ui-architecture.md) · [Firmware](../firmware.md) · [SD Update](../sd-update.md) · [Display Rationale](rationale.md)*

------

## Overview

The ESP32-S3 display module runs a **device-agnostic LVGL rendering engine**. It has no knowledge of MIXTEE, channels, or mixing concepts — it only knows how to create, update, and display widgets. The Teensy is the brain: it reads UI definitions from `ui.json` on the SD card, translates them into binary widget commands, and streams them to the ESP32 over UART.

This architecture is reusable across MIXTEE, SYNTEE, and future devices. Each device ships its own `ui.json` and the same display engine firmware.

------

## Serial Transport

### Physical Layer

- **Interface:** Serial1 UART (Teensy pins 0/1)
- **Baud rate:** 921600 (92 KB/s throughput, 15× headroom over ~6 KB/s peak meter data)
- **Connection:** 6-pin JST-PH header (UART TX/RX + ESP32_EN + GPIO0 + 5V + GND)

### Frame Format (COBS)

All frames use [COBS encoding](https://en.wikipedia.org/wiki/Consistent_Overhead_Byte_Stuffing) with `0x00` as the frame delimiter. This guarantees unambiguous framing without escape sequences.

```
[0x00] [COBS-encoded payload] [0x00]
```

### Payload Format

```
[CMD:1] [SEQ:1] [LEN:2 LE] [DATA:variable] [CRC16:2]
```

| Field | Size | Description |
|-------|------|-------------|
| CMD | 1 byte | Command ID (see command table below) |
| SEQ | 1 byte | Sequence number (0–255, wraps) |
| LEN | 2 bytes | Payload data length (little-endian, excludes CMD/SEQ/LEN/CRC) |
| DATA | variable | Command-specific payload |
| CRC16 | 2 bytes | CRC-CCITT over CMD+SEQ+LEN+DATA |

### Flow Control

- Commands that modify state (CREATE_WIDGET, SET_PROPERTY, SWITCH_PAGE) are acknowledged with ACK/NACK
- Runtime data commands (METER_BATCH, SET_VALUE) are fire-and-forget (no ACK — throughput over reliability)
- Touch events (ESP32 → Teensy) are fire-and-forget
- HEARTBEAT sent every 2 seconds; 3 missed heartbeats trigger reconnection

------

## Command Reference

### Lifecycle Commands (0x01–0x07)

| CMD | Name | Direction | Data | Description |
|-----|------|-----------|------|-------------|
| 0x01 | HANDSHAKE | Teensy → ESP32 | `[protocol_version:2]` | Initiates connection after boot |
| 0x02 | READY | ESP32 → Teensy | `[width:2][height:2][color_depth:1][touch:1]` | Display capabilities report |
| 0x03 | CLEAR_ALL | Teensy → ESP32 | (none) | Delete all widgets, reset to blank |
| 0x04 | BOOT_COMPLETE | Teensy → ESP32 | (none) | All widgets created, enter normal operation |
| 0x05 | HEARTBEAT | Bidirectional | `[uptime_ms:4]` | Keepalive ping |
| 0x06 | ACK | ESP32 → Teensy | `[acked_seq:1]` | Command acknowledged |
| 0x07 | NACK | ESP32 → Teensy | `[nacked_seq:1][error_code:1]` | Command rejected |

### Widget Creation Commands (0x10–0x16)

| CMD | Name | Direction | Data | Description |
|-----|------|-----------|------|-------------|
| 0x10 | CREATE_WIDGET | Teensy → ESP32 | `[id:2][parent_id:2][type:1][x:2][y:2][w:2][h:2]` | Create widget with position/size |
| 0x11 | DELETE_WIDGET | Teensy → ESP32 | `[id:2]` | Remove widget and children |
| 0x12 | SET_PROPERTY | Teensy → ESP32 | `[id:2][prop_key:1][value:variable]` | Set widget property (color, font, range, etc.) |
| 0x13 | SET_VISIBLE | Teensy → ESP32 | `[id:2][visible:1]` | Show/hide widget |
| 0x14 | CREATE_PAGE | Teensy → ESP32 | `[page_id:2][name_len:1][name:variable]` | Create a full-screen page container |
| 0x15 | SWITCH_PAGE | Teensy → ESP32 | `[page_id:2]` | Switch active page (hide others) |
| 0x16 | SET_PARENT | Teensy → ESP32 | `[id:2][new_parent_id:2]` | Reparent widget |

### Runtime Data Commands (0x20–0x24)

| CMD | Name | Direction | Data | Description |
|-----|------|-----------|------|-------------|
| 0x20 | METER_BATCH | Teensy → ESP32 | `[count:1][entries:count×6]` | Batch meter update (see below) |
| 0x21 | SET_VALUE | Teensy → ESP32 | `[id:2][value:2]` | Set numeric value (integer, 0–65535) |
| 0x22 | SET_TEXT | Teensy → ESP32 | `[id:2][text_len:1][text:variable]` | Set label text |
| 0x23 | SET_STATE | Teensy → ESP32 | `[id:2][state:1]` | Set widget state (normal/pressed/disabled/checked) |
| 0x24 | SET_COLOR | Teensy → ESP32 | `[id:2][color_target:1][r:1][g:1][b:1]` | Set widget color |

### Touch Events (0x30–0x32) — ESP32 → Teensy

| CMD | Name | Data | Description |
|-----|------|------|-------------|
| 0x30 | TOUCH_DOWN | `[x:2][y:2]` | Finger touch at coordinates |
| 0x31 | TOUCH_UP | `[x:2][y:2]` | Finger lifted at coordinates |
| 0x32 | TOUCH_DRAG | `[x:2][y:2]` | Finger moved to coordinates |

Touch events are coordinate-based — the ESP32 never interprets touch semantics. The Teensy maps touch coordinates to widget IDs using the widget layout from `ui.json`.

### Update Commands (0x40–0x41)

| CMD | Name | Direction | Data | Description |
|-----|------|-----------|------|-------------|
| 0x40 | ENTER_BOOTLOADER | Teensy → ESP32 | (none) | Request ESP32 enter bootloader (graceful) |
| 0x41 | UPDATE_PROGRESS | Teensy → ESP32 | `[percent:1][text_len:1][text:variable]` | Display update progress bar |

------

## METER_BATCH Format

Optimized for the primary real-time data path: 24 meters × 30 Hz.

Each entry in METER_BATCH:

```
[widget_id:2 LE] [peak:2 LE] [rms:2 LE]
```

- `widget_id`: Target meter widget ID
- `peak`: Peak level (0–1000, maps to widget range)
- `rms`: RMS level (0–1000, maps to widget range)

**Full frame:** 1 (count) + 24 × 6 (entries) = 145 bytes payload → ~160 bytes with COBS framing + header.

**Data rate:** 160 bytes × 30 Hz = **4.8 KB/s** — well within 92 KB/s UART capacity.

------

## Widget Types

| Type ID | Name | LVGL Object | Properties |
|---------|------|-------------|------------|
| 0x01 | Container | `lv_obj` | Background color, border, radius |
| 0x02 | Label | `lv_label` | Text, font size, alignment, color |
| 0x03 | Meter | `lv_bar` (vertical) | Min, max, value (peak), secondary value (RMS) |
| 0x04 | Knob | `lv_arc` | Min, max, value, arc angle |
| 0x05 | Slider | `lv_slider` (horizontal) | Min, max, value |
| 0x06 | Bar | `lv_bar` (vertical) | Min, max, value |
| 0x07 | Button | `lv_btn` | Text, state (normal/checked/disabled) |
| 0x08 | Icon | `lv_img` | Icon index (from built-in icon set) |
| 0x09 | Rect | `lv_obj` + style | Fill color, border color, radius |
| 0x0A | Page | `lv_obj` (screen) | Name, background color |

------

## Property Keys (SET_PROPERTY)

| Key | Name | Value format | Applies to |
|-----|------|-------------|------------|
| 0x01 | BG_COLOR | `[r:1][g:1][b:1]` | All |
| 0x02 | FG_COLOR | `[r:1][g:1][b:1]` | Label, Button |
| 0x03 | BORDER_COLOR | `[r:1][g:1][b:1]` | Container, Rect |
| 0x04 | BORDER_WIDTH | `[width:1]` | Container, Rect |
| 0x05 | RADIUS | `[radius:2]` | Container, Rect, Button |
| 0x06 | FONT_SIZE | `[size:1]` | Label, Button |
| 0x07 | TEXT_ALIGN | `[align:1]` (0=left, 1=center, 2=right) | Label |
| 0x08 | RANGE_MIN | `[min:2 LE]` | Meter, Knob, Slider, Bar |
| 0x09 | RANGE_MAX | `[max:2 LE]` | Meter, Knob, Slider, Bar |
| 0x0A | OPACITY | `[opacity:1]` (0–255) | All |
| 0x0B | ARC_ANGLE | `[start:2][end:2]` | Knob |
| 0x0C | INDICATOR_COLOR | `[r:1][g:1][b:1]` | Meter, Bar, Slider |

------

## ESP32-S3 Display Engine Implementation

### Boot Sequence

1. ESP32 boots, initializes LCD + touch controller
2. Shows splash screen (built-in, device-agnostic logo or blank)
3. Waits for HANDSHAKE from Teensy on UART
4. Responds with READY + screen capabilities
5. Receives CREATE_PAGE / CREATE_WIDGET commands → builds LVGL widget tree
6. Receives BOOT_COMPLETE → enters normal operation mode
7. Processes runtime commands (METER_BATCH, SET_VALUE, etc.) in main loop
8. Forwards touch events to Teensy

### Widget Table

- Flat array indexed by widget ID (max 128 entries)
- O(1) lookup for runtime updates (critical for 30 Hz meter data)
- Each entry: LVGL object pointer + type + parent ID

### Memory Management

- All pages and widgets created at boot time
- Pages switched via SET_VISIBLE (show active page, hide others)
- No dynamic widget creation during normal operation → no LVGL heap fragmentation
- Typical memory usage: ~50–80 KB LVGL heap for full MIXTEE UI

### UART Processing

- COBS decoder runs in UART receive interrupt handler
- Complete frames queued for main loop processing
- Main loop: dequeue frame → validate CRC → dispatch by CMD → update LVGL objects
- LVGL `lv_timer_handler()` called at end of each main loop iteration

------

## Error Handling

| Condition | Behavior |
|-----------|----------|
| CRC mismatch | Drop frame, increment error counter |
| Unknown CMD | NACK with error code 0x01 |
| Invalid widget ID | NACK with error code 0x02 |
| Widget table full | NACK with error code 0x03 |
| 3 missed heartbeats | ESP32 shows "Connection Lost" overlay; resumes on next valid frame |
| UART buffer overflow | Drop oldest bytes, rely on COBS resync at next 0x00 delimiter |
