# IO Board — Connections

Interface contract for the IO Board. Used by agents working on other boards to understand IO Board connectivity.

## FFC to Main Board (12-pin 1.0mm ZIF)

| FFC Pin | Signal | Direction | Notes |
|---------|--------|-----------|-------|
| 1 | ETH_TX+ | Analog | Post-PHY differential pair |
| 2 | ETH_TX- | Analog | Post-PHY differential pair |
| 3 | GND (guard) | Ground | Shield between Ethernet pairs |
| 4 | ETH_RX+ | Analog | Post-PHY differential pair |
| 5 | ETH_RX- | Analog | Post-PHY differential pair |
| 6 | GND (guard) | Ground | Shield between Ethernet/USB |
| 7 | USB_HOST_D+ | Bidirectional | FE1.1s upstream, USB FS 12 Mbps |
| 8 | USB_HOST_D- | Bidirectional | FE1.1s upstream |
| 9 | MIDI_RX | In (from 6N138) | Serial3 pin 15, 31.25 kbaud |
| 10 | MIDI_TX | Out (from Teensy) | Serial4 pin 17, 31.25 kbaud |
| 11 | 5V_DIG | Power | USB hub, MIDI, Ethernet circuits |
| 12 | GND | Ground | Main return |

Connector: 12-pin 1.0mm pitch FFC, ZIF socket (Molex 502586 series, 12-pin). Cable ~100-120mm.

Note: Ethernet signals are post-PHY analog -- cable-tolerant. Only USB Full-Speed over FFC.

## Ethernet Ribbon Cable (6-pin header, separate from FFC)

| Pin | Signal | Notes |
|-----|--------|-------|
| 1 | ETH_TX+ | Differential pair from Teensy bottom pads |
| 2 | ETH_TX- | Differential pair |
| 3 | ETH_RX+ | Differential pair |
| 4 | ETH_RX- | Differential pair |
| 5 | LED | Activity LED (optional) |
| 6 | GND | Shield/return |

6-pin 2.54mm pitch header, ~100mm ribbon cable. Signals route through 0.1uF coupling caps on IO Board to RJ45 MagJack transformer.

## Panel-Mount Connectors

| Connector | Type | Notes |
|-----------|------|-------|
| MIDI HOST | Dual stacked USB-A (Amphenol 67298-4090) | 2× USB host ports |
| ETH | RJ45 MagJack (integrated magnetics) | 10/100 Mbps Ethernet |
| MIDI IN | 3.5mm TRS Type A (CUI SJ-3523-SMT) | Optocoupler-isolated input |
| MIDI OUT | 3.5mm TRS Type A (CUI SJ-3523-SMT) | Current-loop output |

Headphone amp, jack, and volume pot have moved to the standalone **HP Board** — see [`../hp/connections.md`](../hp/connections.md).

All panel-mount components in left column of top panel.

---
Back to [README.md](README.md)
