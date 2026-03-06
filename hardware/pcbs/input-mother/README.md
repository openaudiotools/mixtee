# Input Mother Board

**Dimensions:** ~80 x 40 mm | **Layers:** 4 | **Orientation:** Vertical, mounted to back panel | **Instances:** 2

Board 1-top handles channels 1–8 (TDM1), Board 2-top handles channels 9–16 (TDM2). Same PCB design for both — I2C address selection via solder jumpers. Board 1-top also carries 4× output reconstruction filters + line drivers, 4× TS5A3159 mute switches, MCP23008 GPIO expander, and HP amp cable connector; Board 2-top leaves output/mute/control section unpopulated. Entire board runs in the **galvanically isolated analog domain** (GND_ISO).

## Key ICs

- 2× AK4619VN codec (4-in/4-out each, 8 ADC channels per board)
- 8× OPA1678 input buffer op-amps + 8× Sallen-Key anti-alias filters
- 8× ESD clamp diodes
- ADP7118 LDO (5V_ISO → 3.3V_A, per-board analog supply)
- MCP23008 I2C GPIO expander (Board 1-top only — mute control, codec PDN, headphone detect; address 0x21)
- 4× TS5A3159 analog mute switches (Board 1-top only — pop suppression, I2C-controlled via MCP23008)

## See Also

- [`connections.md`](connections.md) — FFC, JST, jack pinouts (interface contract)
- [`architecture.md`](architecture.md) — analog stage design, LDO, I2C addressing, BOM variant
- [`ak4619-wiring.md`](ak4619-wiring.md) — AK4619VN codec reference (pin table, registers, TDM)

## Status

Previously routed; wiped for fresh start after galvanic isolation architecture change (FFC 16→20 pin, MCP23008/TS5A3159 addition, isolated power). Needs regeneration.
