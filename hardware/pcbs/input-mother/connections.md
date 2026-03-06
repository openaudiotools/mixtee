# Input Mother Board — Connections

*← Back to [README](README.md)*

This document defines all connector interfaces on the Input Mother Board, including pinouts, directions, and mating connectors.

------

## FFC to Main Board (20-pin 1.0mm ZIF, galvanically isolated)

All signals on the FFC are in the **isolated analog domain** (GND_ISO). The Main Board provides galvanic isolation via Si8662BB (TDM), ISO1541 (I2C), and MEJ2S0505SC (power) — see [Main Board architecture](../main/architecture.md#galvanic-isolation).

| FFC Pin | Signal | Direction |
|---------|--------|-----------|
| 1 | MCLK_ISO | In (from Si8662BB Side 2) |
| 2 | BCLK_ISO | In |
| 3 | LRCLK_ISO | In |
| 4 | TDM_TX_ISO (Teensy → codec SDIN1) | In |
| 5 | TDM_RX0_ISO (codec 1 SDOUT → Teensy) | Out |
| 6 | GND_ISO | Ground |
| 7 | TDM_RX1_ISO (codec 2 SDOUT → Teensy) | Out |
| 8 | GND_ISO | Ground |
| 9 | I2C_SDA_ISO | Bidirectional (via ISO1541) |
| 10 | I2C_SCL_ISO | In (via ISO1541) |
| 11 | GND_ISO | Ground |
| 12–13 | 5V_ISO (×2) | Power in (paralleled, from MEJ2S0505SC) |
| 14–15 | GND_ISO (×2) | Ground |
| 16 | Spare | — |
| 17 | GND_ISO | Ground |
| 18–19 | Spare | — |
| 20 | GND_ISO | Ground |

Same pinout for both TDM1 and TDM2 instances, substituting bus signals. 7× GND_ISO pins provide low-impedance isolated return paths.

**Connector:** 20-pin 1.0mm pitch FFC, ZIF socket. Cable length ~40–50mm.

------

## Mother ↔ Daughter Board (6-pin JST-PH)

| Pin | Signal | Notes |
|-----|--------|-------|
| 1–4 | AIN1–4 (analog R channels) | From daughter board jacks |
| 5 | 5V_ISO | Isolated analog power to daughter |
| 6 | GND_ISO | Isolated ground |

**Connector:** 6-pin JST-PH wire harness (B6B-PH-K-S), 2.0mm pitch, ~15–20mm cable.

------

## Output Analog Cable (10-pin JST-PH, Board 1-top only)

| Pin | Signal |
|-----|--------|
| 1 | Master L (line level, post-TS5A3159 mute) |
| 2 | AUX1 L |
| 3 | AUX2 L |
| 4 | AUX3 L |
| 5 | Master R (post-TS5A3159 mute) |
| 6 | AUX1 R |
| 7 | AUX2 R |
| 8 | AUX3 R |
| 9–10 | GND_ISO |

**Connector:** 10-pin JST-PH (B10B-PH-K-S), 2.0mm pitch, ~80mm cable. Board 1-top only — carries post-mute, post-driver line-level signals to Output Board O-top.

------

## Headphone Amp Cable (4-pin JST-PH, Board 1-top only)

| Pin | Signal | Notes |
|-----|--------|-------|
| 1 | Master L | Post-TS5A3159 mute, post-line driver |
| 2 | Master R | Post-TS5A3159 mute, post-line driver |
| 3 | 5V_ISO | Isolated power for HP amp |
| 4 | GND_ISO | Isolated ground |

**Connector:** 4-pin JST-PH (B4B-PH-K-S), 2.0mm pitch, ~40–60mm cable. Board 1-top only — carries Master L/R audio and isolated power to the standalone HP Board.

------

## 1/4" TS Jacks (panel-mount)

4x Switchcraft 112BPC on each instance. Carry L channels (odd: 1,3,5,7 on Board 1-top; 9,11,13,15 on Board 2-top).
