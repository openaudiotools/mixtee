# MIXTEE: UI Architecture

*← Back to [README](../README.md) | See also: [Features](features.md) · [Hardware](hardware.md) · [Firmware](firmware.md)*

------

## Overview

> **The ESP32-S3 is a device-agnostic LVGL display engine.** It has no knowledge of MIXTEE, channels, or mixing — it only knows how to render widgets. The Teensy is the brain: it reads UI definitions from `ui.json` on the SD card, translates them into binary widget commands, and streams them to the ESP32 over UART. This architecture is reusable across MIXTEE, SYNTEE, and future devices.

> For the binary serial protocol specification, see [Display Protocol](display/protocol.md). For the SD card update mechanism, see [SD Update](sd-update.md).

The MIXTEE display UI is built on a modular, hierarchical framework designed for two goals: fast access to the most-used mixing parameters (gain, level, mute) with minimal button presses, and extensibility so that community contributors can add new processing modules without reworking the navigation engine.

The signal path is hardcoded in the DSP audio graph (fixed at compile time). UI modules provide windows into different points of that fixed graph — rearranging or adding modules on screen does not affect DSP processing order.

No internal FX for now. The mixer does not include built-in effects (reverb, delay, compression). Aux sends route to external FX gear. Internal FX may be added in a future revision as additional modules.

------

## Display Engine Architecture

### Rendering Split

| Responsibility | Owner | Notes |
|---------------|-------|-------|
| UI layout definitions | `ui.json` on SD card | Parsed by Teensy at boot |
| Widget creation commands | Teensy | Translates JSON → binary CREATE_WIDGET protocol |
| LVGL widget rendering | ESP32-S3 display engine | Generic renderer, no device knowledge |
| Meter data streaming | Teensy | METER_BATCH at 30 Hz (~4.6 KB/s) |
| Parameter updates | Teensy | SET_VALUE/SET_TEXT/SET_STATE on change |
| Touch input | ESP32-S3 → Teensy | Coordinate-based events (TOUCH_DOWN/UP/DRAG) |
| Touch interpretation | Teensy | Maps coordinates to UI elements via widget bindings |

### ui.json Format

The UI layout is defined in a JSON file on the SD card (`/SYSTEM/ui.json`), loaded by the Teensy at boot. This is what makes the same display engine work for different devices — MIXTEE, SYNTEE, etc. each ship their own `ui.json`.

```json
{
  "device": "MIXTEE",
  "version": "1.0.0",
  "display": { "width": 800, "height": 480 },
  "colors": { "bg": "#000000", "fg": "#FFFFFF", "accent": "#FF0000" },
  "pages": [
    {
      "id": 0, "name": "overview",
      "widgets": [
        { "id": 100, "type": "label", "x": 10, "y": 5, "w": 40, "h": 20, "text": "CH1" },
        { "id": 101, "type": "bar", "x": 10, "y": 30, "w": 20, "h": 200, "min": 0, "max": 1000 },
        { "id": 102, "type": "meter", "x": 35, "y": 30, "w": 15, "h": 200, "min": 0, "max": 1000 }
      ]
    }
  ],
  "bindings": {
    "meters": [{ "channel": 0, "widget": 102 }],
    "params": [{ "param": "ch1_gain", "widget": 110, "type": "value" }]
  }
}
```

**Key fields:**
- `pages[]` — each page contains widget definitions with absolute positioning
- `bindings.meters[]` — maps audio channel indices to meter widget IDs (for METER_BATCH routing)
- `bindings.params[]` — maps Teensy-side parameter names to widget IDs (for SET_VALUE/SET_TEXT routing)

**Size:** ~15–25 KB for full MIXTEE UI. ArduinoJson streaming parser handles this in ~5 ms.

### Widget Types

| Type | LVGL mapping | Use case |
|------|-------------|----------|
| Container | lv_obj | Grouping, backgrounds |
| Label | lv_label | Channel names, values, headers |
| Meter | lv_bar (vertical) | Level meters (peak + RMS) |
| Knob | lv_arc | Gain, pan controls |
| Slider | lv_slider (horizontal) | Pan sliders |
| Bar | lv_bar (vertical) | EQ bands, send levels |
| Button | lv_btn | Mute, solo, rec indicators |
| Icon | lv_img | Status icons |
| Rect | lv_obj + style | Colored rectangles, separators |
| Page | lv_obj (screen) | Full-screen page containers |

### Boot-Time Widget Creation

All pages and widgets are created at startup via CREATE_WIDGET commands. Pages are switched at runtime via SET_VISIBLE — no dynamic widget creation during operation. This avoids LVGL memory fragmentation.

The widget table on the ESP32 is a flat array indexed by widget ID (max ~128 entries), providing O(1) lookup for 30 Hz meter updates.

------

## Hierarchy

```
View
  └→ Page
       └→ Module
            └→ Component
                 └→ Param
```

**View:** A top-level screen context representing a major section of the mixer. Views are navigated at the Global level using the Nav encoder.

**Page:** A vertical layer within a view. Each page fills the full 480×272 display. Pages within a view are scrolled using PAGE + Nav. All pages in a view share a persistent channel name strip header.

**Module:** A self-contained UI block within a page, representing one stage of signal processing for one channel. Modules are laid out horizontally (one per channel) within a page. At the Page level, Nav encoder selects between modules.

**Component:** A single processing element within a module (e.g., the Low band of an EQ module). At the Module level, Nav encoder selects between components.

**Param:** An individual adjustable value within a component (e.g., level, frequency, Q). At the Component level, Nav encoder selects params, Edit encoder adjusts the selected param.

------

## Views

| View            | Contents                                            | Pages                    |
| --------------- | --------------------------------------------------- | ------------------------ |
| Overview        | Read-only metering of all 16 inputs + 4 output buses | 1 (no sub-pages)         |
| Inputs 1–8      | Channel strips for inputs 1–8                       | Page 1: Main strip, Page 2: EQ + Sends |
| Inputs 9–16     | Channel strips for inputs 9–16                      | Page 1: Main strip, Page 2: EQ + Sends |
| Outputs         | Output bus strips (Aux1, Aux2, Aux3, Main)          | Page 1: Main strip       |
| Recorder Setup  | Recording configuration and status                  | Page 1: Settings         |

------

## Overview (Read-Only)

The Overview is a non-interactive display of all channels and buses. It shows vertical level meters (peak + RMS) for all 16 inputs plus Aux1, Aux2, Aux3, and Master. Mute/solo status and record arm indicators are visible per channel. No parameter editing from this view — it is purely visual for monitoring the full mix at a glance.

The Overview is the Home destination. Pressing the Home button from any depth returns here immediately (hard reset, navigation stack cleared).

When recording is active, the Overview shows elapsed time, file size, and buffer health.

For output buses, all except Master are FX sends. The Overview distinguishes these visually.

------

## Input Views (Inputs 1–8 / Inputs 9–16)

Each input view displays 8 channels. The two input views are structurally identical, just controlling different channel groups.

### Page 1: Main Strip

Each channel shows (top to bottom):

- **Channel name/number** (persistent header row, always visible across all pages)
- **Gain knob** (radial indicator; default param for this module — Edit encoder adjusts immediately at Page level)
- **Pan slider** (horizontal bar, center-detented)
- **Peak indicator** (P)
- **Level meter** (vertical bar, peak + RMS with horizontal tick marks)
- **Mute button** (M): hollow = disengaged, filled = muted
- **Solo button** (S): only visible on stereo-linked channels in place of second Mute
- **Record arm** (O): hollow circle = not armed, filled red circle = armed

**Mono vs. Stereo layout:**

- Mono pair: two independent channel strips side by side, each 60 px wide within a 120 px pair slot
- Stereo pair: single combined strip at 120 px, shared gain knob (displayed as split circle indicating L/R balance), single pan (becomes balance), shared mute, solo visible, single record arm

### Page 2: EQ + Sends

Accessed by PAGE + Nav down from Page 1. The channel name/number header persists.

**EQ Module (upper section):**

- 3 vertical bars per channel labeled L, M, H (Low, Mid, High)
- Bar height represents gain (center = flat/0 dB, up = boost, down = cut)
- Range: ±12 dB

**Send Module (lower section):**

- 3 vertical bars per channel labeled A1, A2, A3 (Aux 1, Aux 2, Aux 3)
- Bar height represents send level (bottom = off, top = full)

Maybe up to 2 modules per page — the exact vertical split between EQ and Sends depends on available pixel height after the header.

------

## Output View

Each output bus (Aux1, Aux2, Aux3, Main) has a simplified channel strip:

- Bus name header
- Peak indicators (L/R)
- Stereo level meter (L + R vertical bars)
- Mute indicator
- Record arm (for stem recording, future)

Output strips are wider than input strips since there are only 4 buses to fill the display width.

------

## Recorder Setup View

Full-screen settings page showing a parameter/value list:

- Record mode (Immediate / Armed)
- Arm threshold level
- File format info (channels, sample rate, bit depth)
- SD card status (capacity, free space)
- Current session info when recording

------

## Navigation Details

### View Boundary Crossing

When the Nav encoder moves past the last channel in an input view, it seamlessly crosses into the neighboring view:

- **Inputs 1–8, right past ch 8** → Inputs 9–16, focus channel 9
- **Inputs 9–16, right past ch 16** → Outputs, focus first bus
- **Inputs 9–16, left past ch 9** → Inputs 1–8, focus channel 8
- **Outputs, left past first bus** → Inputs 9–16, focus channel 16

The current **page level is preserved** across boundary crossings. If you are on the EQ+Sends page for Inputs 1–8 and cross into Inputs 9–16, you land on the EQ+Sends page. If the destination view has fewer pages than the current page index, clamp to the last available page.

Navigation stops at the outer boundaries (left edge of Inputs 1–8, right edge of Outputs/Recorder Setup).

### Channel Name Strip

Every page within an input or output view displays a persistent channel name strip as the top row. For now, names are simply channel numbers (1, 2, 3/4, 5, 6, 7/8 for inputs; AUX1, AUX2, AUX3, MST for outputs). This header is the spatial anchor — it remains constant as you scroll through pages, so you always know which channels you are editing.

### Depth-Independent Buttons

**Mute, Solo, and Record** buttons always act on the currently selected channel, regardless of navigation depth. The "selected channel" is a global state variable set whenever a channel strip is focused at the Page level, and it persists as you drill into modules and components.

### Context Behavior Summary

| Context   | Nav ↻              | PAGE + Nav ↻   | Push Nav        | Edit ↻                     | Push Edit       |
| --------- | ------------------ | -------------- | --------------- | --------------------------- | --------------- |
| Global    | Navigate views     | Navigate pages | Enter page      | ×                           | ×               |
| Page      | Select modules     | Navigate pages | Enter module    | Edit default module param   | Enter module    |
| Module    | Select components  | Navigate pages | Enter component | Edit default component param | Enter component |
| Component | Select params      | Navigate pages | ×               | Edit selected param          | ×               |

------

## Module Architecture (Firmware)

Modules are self-contained UI+parameter units. Each module knows:

- Its component count (e.g., EQ module has 3: Low, Mid, High)
- Its default parameter (the param adjusted by Edit encoder at Page level without drilling in)
- How to draw its channel strip segment
- How to handle Edit encoder input at each depth

This architecture supports community extensibility. A contributor adds a new Module subclass, registers it on a page, and it integrates with the existing navigation engine automatically.

### Current Modules

**Input channels:**

| Module          | Components              | Default Param | Signal Stage         |
| --------------- | ----------------------- | ------------- | -------------------- |
| Main (Gain/Pan) | Gain, Pan               | Gain          | Input gain + panning |
| Level/Mute      | Level, Mute, Solo       | Level         | Output level + muting |
| EQ              | Low, Mid, High          | —             | 3-band fixed EQ      |
| Sends           | Send 1, Send 2, Send 3  | Send 1        | Aux bus send levels  |

*Note: The Main module is an exception — it holds both input-side (Gain, Pan) and output-side (Level, Mute) params for fast access. The signal path order (Gain → Pan → EQ → Sends → Level → Mute → Bus) is hardcoded in the DSP graph regardless of module display order.*

**Output buses:**

| Module     | Components         | Default Param | Signal Stage        |
| ---------- | ------------------ | ------------- | ------------------- |
| Bus Master | Level, Mute        | Level         | Bus output level    |

------

## Design Principles

### Modularity

The UI framework is designed so that open-source contributors can add new pages and modules for further signal processing without modifying the navigation engine. The module interface is the extension point.

### Signal Path Encoding

The signal path should be hardcoded. The order of both modules and components on screen does not have to match the DSP processing order — just the separation of signal stages matters for the user's mental model. The actual processing order is fixed in the audio graph.

### Minimal Chrome

The display prioritizes channel data over navigation UI. The channel name strip and module content fill the screen. Navigation state is communicated through which elements are highlighted/focused, not through dedicated nav bars or breadcrumbs.
