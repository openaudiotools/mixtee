# MIXTEE: Connector Part Numbers

*← Back to [README](../README.md) | See also: [System Topology](system-topology.md) · [Hardware](hardware.md)*

------

## MPN Index

Quick reference for connector part numbers across all boards. For detailed pinouts and usage, see each board's `connections.md`.

| Part | MPN | Manufacturer | Board(s) | Notes |
|------|-----|-------------|----------|-------|
| USB-C (PC) | USB4105-GF-A | GCT | Main | Data only, mid-mount SMD |
| USB-A dual stacked | 67298-4090 | Amphenol | IO | 2× MIDI host ports |
| FFC 20-pin ZIF | TBD (Molex 502586 series, 20-pin) | Molex | Main (×2), Input Mother (×2) | 1.0mm pitch, bottom-contact; galvanic isolation boundary |
| FFC 12-pin ZIF | TBD (Molex 502586 series) | Molex | Main, IO | 1.0mm pitch, bottom-contact |
| JST-PH 6-pin | B6B-PH-K-S | JST | Main, Key, Mother/Daughter | 2.0mm pitch, through-hole |
| JST-PH 10-pin | B10B-PH-K-S | JST | Input Mother (1-top), Daughter-Output (O-top) | Output analog cable |
| 1/4" TS jack | 112BPC | Switchcraft | Input Mother, Daughter-Output | 24× total (16 in + 8 out) |
| 1/4" TRS jack (HP) | 35RASMT2BHNTRX | Switchcraft | HP | Stereo headphone, detect switch |
| 3.5mm TRS (MIDI) | SJ-3523-SMT | CUI Devices | IO | MIDI IN + MIDI OUT Type A |
| RJ45 MagJack | TBD | TBD | IO | 10/100 Ethernet, integrated magnetics |
| 6-pin header (ETH) | TBD | TBD | Main, IO | 2.54mm, Ethernet ribbon |
| JST-PH 4-pin (HP cable) | B4B-PH-K-S | JST | Input Mother (1-top), HP | HP amp signal + power cable |
| SD card socket | 472192001 | Molex | Main | Full-size, panel-mount |
| Rotary encoder | PEC11R-4215F-S0024 | Bourns | Main (×3) | 24 detents, push switch |
| Power button | TBD | TBD | Back panel | Screw-collar momentary |
| CHOC hotswap | CPG135001S30 | Kailh | Key (×16) | CHOC v1/v2 compatible |

## Cable Assemblies

| Cable | Type | Pins | Length |
|-------|------|------|--------|
| Main ↔ Input Mother (×2) | FFC 1.0mm | 20 | 40–50mm |
| Main ↔ IO Board | FFC 1.0mm | 12 | 100–120mm |
| Ethernet ribbon | 6-pin 2.54mm | 6 | ~100mm |
| Mother ↔ Daughter (×3) | JST-PH harness | 6 | 15–20mm |
| 1-top → O-top | JST-PH harness | 10 | ~80mm |
| Main ↔ Key PCB | JST-PH harness | 6 | 30–40mm |
| 1-top → HP Board | JST-PH harness | 4 | 40–60mm |
