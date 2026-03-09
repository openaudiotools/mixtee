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

## ESP32-S3 Display Header (6 pin)

| Pin | Signal | Teensy Pin | Notes |
|-----|--------|------------|-------|
| 1 | UART TX (Teensy → ESP32-S3) | 1 | Serial1 TX — widget commands, meter data |
| 2 | UART RX (ESP32-S3 → Teensy) | 0 | Serial1 RX — touch events, READY/ACK |
| 3 | ESP32_EN | 9 | Active-high enable; pull-up on module. Assert LOW to reset. |
| 4 | ESP32_GPIO0 | 10 | Boot mode: LOW = UART bootloader, HIGH/float = normal app boot |
| 5 | 5V | — | Module power (5V_DIG) |
| 6 | GND | — | Common ground |

**Connector:** 6-pin JST-PH (B6B-PH-K-S) or pin header to custom ESP32-S3 display PCB.
**Cable:** ~20mm. Pins 3–4 enable Teensy-controlled ESP32 reflash from SD card — see [SD Update](../../docs/sd-update.md). SPI0 bus no longer needed — display rendering handled entirely by ESP32-S3 custom display PCB running LVGL.

---

## Ethernet Ribbon (6-pin header)

6-pin 2.54mm pitch header carries ETH TX+/TX-/RX+/RX-/LED/GND from Teensy bottom pads to IO Board. ~100mm ribbon cable (separate from FFC).

---

---

## SD Card Socket

Molex 472192001, full-size SD. SDIO from Teensy bottom pads 42–47. Top panel, left of display.

---

[Back to README](README.md)
