# Main Board — Connections

Interface contract for the Main Board — the central hub connecting all other boards. Every inter-board cable terminates here. This document defines connector types, pinouts, and cable specs for each interface.

---

## FFC to Input Mother Boards (20-pin 1.0mm ZIF, ×2, galvanically isolated)

See [`../input-mother/connections.md`](../input-mother/connections.md) for the full 20-pin FFC pinout. Summary:

- Pins 1–4: TDM clocks + TX data (isolated via Si8662BB forward channels)
- Pins 5, 7: TDM RX data (isolated via Si8662BB reverse channels)
- Pins 9–10: I2C SDA/SCL (isolated via ISO1541)
- Pins 12–13: 5V_ISO (×2, from MEJ2S0505SC isolated DC-DC)
- Pins 6, 8, 11, 14–15, 17, 20: GND_ISO (×7 — low-impedance isolated return)
- Pins 16, 18–19: Spare

All signals on the FFC are in the isolated analog domain. Galvanic isolation components (Si8662BB-B-IS1, ISO1541DR, MEJ2S0505SC) are on the Main Board — see [architecture](architecture.md#galvanic-isolation).

**Connector:** 20-pin 1.0mm ZIF socket.
**Cable:** ~40–50mm FFC.
**Instances:** Two — one per Input Mother Board (TDM1 vs TDM2).

---

## FFC to IO Board (12-pin 1.0mm ZIF)

See [`../io/connections.md`](../io/connections.md) for the full 12-pin FFC pinout. Summary:

- Pins 1–6: Ethernet TX/RX differential pairs + GND guards
- Pins 7–8: USB Host D+/D-
- Pins 9–10: MIDI RX/TX
- Pin 11: 5V_DIG, Pin 12: GND

**Connector:** Molex 502586 series (12-pin 1.0mm ZIF).
**Cable:** ~100–120mm FFC.

---

## JST-PH to Key PCB (6-pin)

| Pin | Signal | Teensy Pin | Notes |
|-----|--------|------------|-------|
| 1 | NeoPixel DIN | 6 | Data line, 300–500 ohm series resistor |
| 2 | I2C SDA | 18 | Shared Wire bus |
| 3 | I2C SCL | 19 | Shared Wire bus |
| 4 | MCP23017 INT | 22 | Optional interrupt |
| 5 | 5V | — | NeoPixel + MCP23017 power |
| 6 | GND | — | Common ground |

**Connector:** 6-pin JST-PH (B6B-PH-K-S), 2.0mm pitch.
**Cable:** ~30–40mm.

---

## JST-PH from Power Board (2-pin)

| Pin | Signal | Notes |
|-----|--------|-------|
| 1 | 5V (VBUS) | From STUSB4500 output, up to 5A |
| 2 | GND | Power return |

**Connector:** 2-pin JST-PH or screw terminal.
**Cable:** ~60–80mm, 22 AWG. Carries full system current.

---

## ESP32-S3 Display Header (4 pin)

| Pin | Signal |
|-----|--------|
| 1 | UART TX (Teensy → ESP32-S3) |
| 2 | UART RX (ESP32-S3 → Teensy) |
| 3 | 5V |
| 4 | GND |

**Connector:** 4-pin JST or pin header to ESP32-S3 integrated display module.
**Cable:** ~20mm. SPI0 bus no longer needed — display rendering handled entirely by ESP32-S3 module running LVGL.

---

## Ethernet Ribbon (6-pin header)

6-pin 2.54mm pitch header carries ETH TX+/TX-/RX+/RX-/LED/GND from Teensy bottom pads to IO Board. ~100mm ribbon cable (separate from FFC).

---

## PC USB-C (panel-mount)

USB4105-GF-A (GCT), mid-mount SMD. Data only — D+/D- routed to **XMOS XU216 USB audio bridge** (not Teensy native USB). USB Audio Class 2 (24-in/8-out, 24-bit 48 kHz) + USB MIDI composite device. Top panel, left zone. USBLC6-2 ESD protection on D+/D- between connector and XMOS.

Teensy's native USB device port is available via a debug header for firmware updates (not panel-accessible).

---

## XMOS XU216 ↔ Teensy (on-board connections)

All connections are internal to the Main Board — no external cables.

**TDM passive tap (9 signals):** XMOS taps existing TDM bus traces as high-Z inputs:
- SAI1: BCLK (pin 21), LRCLK (pin 20), RX_DATA0 (pin 8), RX_DATA1 (pin 32), TX_DATA0 (pin 7)
- SAI2: BCLK (pin 4), LRCLK (pin 3), RX_DATA0 (pin 5), RX_DATA1 (pin 34)

**SPI control bus (4 signals):** MIDI forwarding between Teensy and XMOS:
- CS (pin 10), MOSI (pin 11), MISO (pin 12), SCK (pin 13)

**Return audio (1 signal, TBD):** XMOS TX data line → Teensy (candidate: pin 9 as SAI1_RX_DATA2)

---

## SD Card Socket

Molex 472192001, full-size SD. SDIO from Teensy bottom pads 42–47. Top panel, left of display.

---

[Back to README](README.md)
