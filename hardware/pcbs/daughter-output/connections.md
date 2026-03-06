# Daughter / Output Board — Connections

## JST-PH to Mother/Output Board (6-pin)

| Pin | Signal | Notes |
|-----|--------|-------|
| 1 | AIN1 / OUT1 | Analog signal (input or output depending on instance) |
| 2 | AIN2 / OUT2 | Analog signal |
| 3 | AIN3 / OUT3 | Analog signal |
| 4 | AIN4 / OUT4 | Analog signal |
| 5 | 5V_ISO | Isolated analog power from mother board |
| 6 | GND_ISO | Isolated ground |

Connector: 6-pin JST-PH (B6B-PH-K-S), 2.0mm pitch, ~15–20mm wire harness. Flexible cable accommodates both boards hanging off the same back panel jacks.

Note: Same PCB used for all 5 instances (2× input daughter, 2× output, 1× output bottom). Signal names vary by instance but physical pinout is identical.

## 1/4" TS Jacks (panel-mount)

4× Switchcraft 112BPC per board instance:
- Input Daughter 1-bot: R input channels 2, 4, 6, 8
- Input Daughter 2-bot: R input channels 10, 12, 14, 16
- Output O-top: L outputs Master, AUX1, AUX2, AUX3
- Output O-bot: R outputs
- Output O-top also receives line-level signals via 10-pin cable from Board 1-top

Jack nets: AIN1–4 (jack tip → JST connector). 4× BAT54 ESD clamp diodes (SOD-323).

---
Back to [README](README.md)
