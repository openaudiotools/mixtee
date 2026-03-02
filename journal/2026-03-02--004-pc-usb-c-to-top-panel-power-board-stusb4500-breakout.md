## 2026-03-02 — PC USB-C to Top Panel, Power Board, STUSB4500 Breakout

### What was done
Two commits (`acfc9be`, `76ba381`) restructured the power and PC USB-C layout:

1. **PC USB-C moved to top panel** — Data-only USB-C receptacle moved from back panel to top panel left zone (on Main Board, near SD card slot). Eliminates 480 Mbps USB HS routing to back panel.
2. **Dedicated Power Board added** — Originally power input was on the Main Board. Moved to a separate vertical back-panel PCB for mechanical isolation.
3. **Power Board → off-the-shelf STUSB4500 breakout** — Replaced custom Power Board PCB with a purchased STUSB4500 USB PD breakout module (SparkFun or equivalent). Simplifies build — no custom power PCB needed.
4. **SD card repositioned** — Full-size SD card slot moved to left of display, vertically aligned with bottom edge of screen.

### Key decisions

| Decision | Rationale |
|----------|-----------|
| PC USB-C on top panel (not back) | Shorter USB HS traces; back panel now audio-only + power |
| STUSB4500 breakout (purchased) | USB PD negotiation is well-solved; no reason to design custom |
| SD left of display | Near Teensy SDIO bottom pads; intuitive user access |

### Files updated
12 files across docs, hardware, and layout images. Created `hardware/pcbs/power/README.md`.

---

