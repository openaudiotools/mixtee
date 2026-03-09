# MIXTEE: PCB Design Rules

*← Back to [README](../README.md) | See also: [System Topology](system-topology.md) · [Hardware](hardware.md)*

------

## Manufacturing Target

Primary: **JLCPCB** or **PCBWay** standard capabilities. All design rules chosen to be within standard process limits (no advanced/special process charges).

------

## Trace Widths

| Net Class | Trace Width | Use |
|-----------|------------|-----|
| Default (digital signal) | 0.25 mm (10 mil) | General digital signals, I2C, SPI, GPIO |
| Audio_Analog | 0.30 mm (12 mil) | Codec analog I/O, op-amp paths, reconstruction filter traces |
| Power | 0.5–1.0 mm (20–40 mil) | 5V, 3.3V, GND power distribution; width depends on current |
| USB_Diff | 0.2 mm (8 mil) | USB D+/D- differential pair; width set by 90Ω impedance target |

------

## Clearances

| Parameter | Value | Notes |
|-----------|-------|-------|
| Trace-to-trace (minimum) | 0.15 mm (6 mil) | JLCPCB standard minimum |
| Trace-to-pad | 0.15 mm | |
| Pad-to-pad | 0.15 mm | |
| USB differential pair gap | Per impedance calculator | Target 90Ω differential; use stackup-specific calculator |
| Analog-to-digital signal spacing | ≥0.5 mm preferred | Keep analog traces away from digital switching signals |
| Courtyard-to-courtyard | 0.25 mm | Component placement clearance |

------

## Via Sizes

| Via Type | Drill Diameter | Annular Ring | Use |
|----------|---------------|-------------|-----|
| Standard signal | 0.3 mm (12 mil) | 0.15 mm | General signal vias |
| Power | 0.4 mm (16 mil) | 0.2 mm | 5V, 3.3V, GND power vias |
| Thermal via array | 0.3 mm | 0.15 mm | Under QFN exposed pads (AK4619VN, STUSB4500); 4-9 vias per pad |

------

## Copper Weight

| Layer Position | Weight | Notes |
|---------------|--------|-------|
| Outer layers (Top, Bottom) | 1 oz (35 µm) | Standard, sufficient for power and signal |
| Inner layers (GND, PWR) | 0.5 oz (17.5 µm) | Standard 4-layer inner core |

**4-layer stackup (Main Board, Input Mother Board):**

| Layer | Function | Copper |
|-------|----------|--------|
| L1 (Top) | Signal + components | 1 oz |
| L2 | GND plane (continuous) | 0.5 oz |
| L3 | Power plane (5V / 3.3V) | 0.5 oz |
| L4 (Bottom) | Signal + components | 1 oz |

**2-layer stackup (IO Board, Daughter/Output, Key PCB):**

| Layer | Function | Copper |
|-------|----------|--------|
| L1 (Top) | Signal + components | 1 oz |
| L2 (Bottom) | GND plane + some signal routing | 1 oz |

------

## USB Differential Pair

| Parameter | Target |
|-----------|--------|
| Impedance | 90Ω differential |
| Trace width | Per stackup calculator (~0.2 mm typical on 4-layer) |
| Pair spacing (edge-to-edge) | Per stackup calculator |
| Length matching | ±0.1 mm between D+ and D- |
| Routing | Avoid vias; route on single layer if possible |
| Keep-out | No other traces within 3× trace width of pair edges |

------

## Grounding Strategy

### Digital Domain (Main Board, IO Board, Key PCB)

- **Single continuous GND plane** on L2 (4-layer) or L2 (2-layer)
- **Star topology** for high-current returns: USB host VBUS, NeoPixels, TFT backlight returns converge near power entry point
- **Component placement** enforces separation: power/USB at one end → Teensy/UI center → isolation boundary at opposite end

### Analog Domain (Input Mother Boards, Daughter/Output, HP Board)

- **Single continuous GND_ISO plane** — entirely isolated from digital GND
- **Short return paths** for audio signals — keep analog traces close to their ground reference
- All boards in the analog domain have no copper connection to system GND

### Isolation Boundary (Main Board only)

- GND_ISO exists on the Main Board as **small copper islands** around isolator Side 2 output pins and FFC pads
- **≥1 mm clearance** between GND and GND_ISO copper on all layers (creepage requirement)
- Place MEJ2S0505SC, Si8662BB, ISO1541 near each FFC connector
- Keep MEJ2S0505SC (switching DC-DC) physically separated from Si8662BB signal pins

### General

- **Thermal relief** on through-hole pads connected to ground plane (4 spokes, 0.3 mm spoke width)

------

## QFN Pad Design

For QFN packages (AK4619VN QFN-32, STUSB4500 QFN-24):

- **Exposed pad:** Solder paste coverage ~60-70% (windowed stencil pattern to prevent tombstoning)
- **Thermal vias:** 4-9 vias (0.3mm drill) in exposed pad, connected to ground plane
- **Via-in-pad:** Fill and cap if budget allows; otherwise use via tenting on bottom side
- **Pad extension:** Per manufacturer recommendation; no solder mask on exposed pad area

------

## Silkscreen

- **Minimum line width:** 0.15 mm (6 mil)
- **Minimum text height:** 1.0 mm
- **Reference designators:** On all components
- **Board markings:** Board name, revision, date, CERN-OHL-P v2 notice, openaudiotools.com
- **Polarity indicators:** On all polarized components (diodes, electrolytic caps, ICs)
- **Pin 1 markers:** On all ICs

------

## Board Outline

- **Edge clearance:** ≥0.3 mm from board edge to nearest copper
- **Mounting holes:** M3 (3.2 mm drill) or M2.5 (2.7 mm drill) with 6 mm pad, connected to GND
- **Corner radius:** 1.0 mm minimum on all boards (prevents stress cracks)
- **Panel tabs:** V-score or tab-route for production panels (discuss with fab house)

------

## Design Rule Check (DRC) Settings

Apply these as KiCad net class rules:

```
Net class: Default
  Track width: 0.25mm
  Clearance: 0.2mm
  Via size: 0.6mm (0.3mm drill)

Net class: Power
  Track width: 0.5mm
  Clearance: 0.2mm
  Via size: 0.8mm (0.4mm drill)

Net class: Audio_Analog
  Track width: 0.3mm
  Clearance: 0.25mm
  Via size: 0.6mm (0.3mm drill)

Net class: USB_Diff
  Track width: 0.2mm
  Clearance: 0.15mm
  Differential pair gap: (per impedance calc)
```
