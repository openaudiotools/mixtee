"""
MIXTEE Daughter/Output Board - SKiDL Netlist Generator

Board: Universal Daughter/Output (80 x 20 mm, 2-layer)
Instances: 5 (2x input daughter, 2x output top, 1x output bottom)

Components:
  - 4x 1/4" TS jacks (Switchcraft 112BPC)
  - 4x BAT54 ESD clamp diodes (SOD-323)
  - 1x 100nF decoupling cap (0603)
  - 1x 6-pin JST-PH connector (B6B-PH-K-S) to mother board

Nets:
  - AIN1..AIN4: Analog signals (jack tip -> connector)
  - +5VA: Analog power from mother board
  - GND: Ground

ESD protection: BAT54 anode on signal, cathode on +5VA rail.
Decoupling cap: 100nF across +5VA and GND.
"""

import os

# Set KiCad symbol library path before importing skidl
os.environ["KICAD_SYMBOL_DIR"] = r"D:\programs\KiCad\9.0\share\kicad\symbols"

from skidl import *

# Manually add KiCad library path (SKiDL doesn't always pick up env vars)
lib_search_paths[KICAD].append(r"D:\programs\KiCad\9.0\share\kicad\symbols")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Footprint references
CUSTOM_FP_LIB = "mixtee-footprints"
FP_112BPC = f"{CUSTOM_FP_LIB}:Switchcraft_112BPC"
FP_SOD323 = "Diode_SMD:D_SOD-323"
FP_C0603 = "Capacitor_SMD:C_0603_1608Metric"
FP_JST_PH_6 = "Connector_JST:JST_PH_B6B-PH-K_1x06_P2.00mm_Vertical"

NUM_CHANNELS = 4

# ---------------------------------------------------------------------------
# Named nets
# ---------------------------------------------------------------------------

gnd = Net("GND")
gnd.drive = POWER

vcc = Net("+5VA")
vcc.drive = POWER

ain = [Net(f"AIN{i+1}") for i in range(NUM_CHANNELS)]

# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------

# 4x 1/4" TS jacks (Switchcraft 112BPC)
# Connector_Audio:AudioJack2 pins: T (Tip=signal), S (Sleeve=ground)
jacks = []
for i in range(NUM_CHANNELS):
    j = Part(
        "Connector_Audio",
        "AudioJack2",
        footprint=FP_112BPC,
        ref=f"J{i+1}",
        value="112BPC",
    )
    j["T"] += ain[i]    # Tip carries the analog signal
    j["S"] += gnd        # Sleeve is ground
    jacks.append(j)

# 4x ESD protection diodes (Schottky, SOD-323)
# Device:D_Schottky pins: 1=K (Cathode), 2=A (Anode)
# ESD clamp: anode on signal, cathode on +5VA rail
diodes = []
for i in range(NUM_CHANNELS):
    d = Part(
        "Device",
        "D_Schottky",
        footprint=FP_SOD323,
        ref=f"D{i+1}",
        value="BAT54",
    )
    d["A"] += ain[i]    # Anode on signal
    d["K"] += vcc       # Cathode on +5VA supply
    diodes.append(d)

# 1x 100nF decoupling capacitor (0603)
# Device:C pins: 1, 2 (both passive)
cap = Part(
    "Device",
    "C",
    footprint=FP_C0603,
    ref="C1",
    value="100nF",
)
cap[1] += vcc
cap[2] += gnd

# 1x 6-pin JST-PH connector to mother board (B6B-PH-K-S)
# Connector_Generic:Conn_01x06 pins: 1..6
# Pin assignment per docs/pcb-architecture.md (Mother <-> Daughter):
#   Pin 1: AIN1
#   Pin 2: AIN2
#   Pin 3: AIN3
#   Pin 4: AIN4
#   Pin 5: +5VA
#   Pin 6: GND
conn = Part(
    "Connector_Generic",
    "Conn_01x06",
    footprint=FP_JST_PH_6,
    ref="J5",
    value="B6B-PH-K-S",
)
for i in range(NUM_CHANNELS):
    conn[i + 1] += ain[i]
conn[5] += vcc
conn[6] += gnd

# ---------------------------------------------------------------------------
# ERC and netlist generation
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    ERC()
    generate_netlist()
    print(f"\nDaughter/Output board netlist generated successfully.")
    print(f"Components: {NUM_CHANNELS} jacks + {NUM_CHANNELS} diodes + 1 cap + 1 connector = {2*NUM_CHANNELS + 2} total")
