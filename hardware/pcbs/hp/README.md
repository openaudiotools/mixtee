# HP Board (Headphone Amplifier)

**Dimensions:** ~30 × 20 mm (or sized to fit breakout module) | **Layers:** 2 | **Orientation:** Horizontal, under top panel (left zone) | **Instances:** 1

Standalone headphone amplifier board in the **galvanically isolated analog domain**. Receives Master L/R audio and isolated power from Board 1-top (Input Mother TDM1) via a 4-pin JST-PH cable. Entire board runs on GND_ISO — no connection to system GND.

## Key Components

- Off-the-shelf TPA6132 or MAX97220 breakout module (soldered or socketed)
- 10k log potentiometer (volume control)
- 1/4" TRS headphone jack (panel-mount, with detect switch)
- 4-pin JST-PH connector (signal + power input from Board 1-top)

## Why Standalone

Moving the headphone amp to its own board keeps it fully in the isolated analog domain without complicating the IO Board with split ground planes. It also allows physical placement flexibility within the enclosure.

## See Also

- [`connections.md`](connections.md) — connector pinouts (4-pin input cable, headphone jack)
- [`architecture.md`](architecture.md) — amp circuit, power, headphone detect routing
- [`../input-mother/connections.md`](../input-mother/connections.md) — Board 1-top HP cable pinout (source)

## Status

Not started. New board added as part of galvanic isolation architecture.
