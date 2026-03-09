# 018 — Display Docs Restructure: Custom PCB Approach

**Date:** 2026-03-10
**Scope:** Documentation restructure + hardware approach change

## What Changed

### Hardware approach: integrated module → custom PCB

Replaced the off-the-shelf ESP32-S3 integrated display module (Waveshare/Elecrow dev board) with a **custom display PCB** design:

- **MCU:** ESP32-S3-WROOM-1-N16R8 (16 MB flash, 8 MB PSRAM)
- **LCD:** Bare 4.3" 800×480 capacitive touch panel (40-pin RGB interface)
- **Touch:** GT911 or CST340 (integrated in LCD FPC)

**Why custom PCB:**
- Guaranteed EN/GPIO0 access (critical for SD card update reflash)
- Board outline designed to MIXTEE enclosure dimensions
- PWM-dimmable backlight
- Lower BOM cost at volume (~$8–12 vs ~$20–25 for dev board)
- No single-vendor supply risk

### Documentation restructure

Created `docs/display/` directory and reorganized:

| Old path | New path | Notes |
|----------|----------|-------|
| `docs/display-engine.md` | `docs/display/protocol.md` | Moved, nav links updated |
| `docs/display-rationale.md` | `docs/display/rationale.md` | Rewritten with custom PCB approach |

### New content in rationale.md

- Recommended hardware section (custom PCB specs, comparison table)
- PCB and firmware notes (FPC routing, backlight driver, boot control, decoupling)
- "Why not a secondary Teensy?" FAQ — HalfKay is USB-only (no UART reflash path), cost/capability comparison table
- Preserved detailed "Why a single update flow" section, updated for custom PCB

### Cross-reference updates

All files that referenced old paths or "integrated display module" updated:

- `docs/firmware.md` — links + terminology
- `docs/ui-architecture.md` — link
- `docs/sd-update.md` — link + risks table (EN/GPIO0 concern removed, custom PCB guarantees it)
- `docs/features.md` — display section rewritten
- `docs/hardware.md` — BOM table, power budget, panel layout
- `docs/architecture-diagram.md` — mermaid node label
- `hardware/pcbs/main/connections.md` — connector description
- `CLAUDE.md` — Architecture at a Glance, cross-ref table

## Verification

- Zero "Waveshare"/"Elecrow"/"integrated display module" in docs (except rationale.md historical context)
- Zero old paths (`display-engine.md`, `display-rationale.md`) in docs
- WROOM-1-N16R8 references confirmed in features, hardware, rationale, architecture-diagram
