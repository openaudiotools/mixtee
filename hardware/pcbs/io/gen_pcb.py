"""
MIXTEE IO Board - KiCad PCB Generator

Board: 50 x 80 mm, 2-layer
Instances: 1
Orientation: Horizontal, under top panel (left side)

Components (32 total):
  ICs (4):
    U1  FE1.1s USB 2.0 hub (SSOP-28) + Y1 12MHz crystal (3225)
    U2  TPS2051 USB power switch port 1 (SOT-23-5)
    U3  TPS2051 USB power switch port 2 (SOT-23-5)
    U4  6N138 optocoupler MIDI IN (DIP-8)
  Caps (12):
    C1,C2   15pF crystal load (0603)
    C3      100nF FE1.1s VDD5 decoupling (0603)
    C4      100nF FE1.1s VDD33 decoupling (0603)
    C5      10uF  FE1.1s VDD33 bulk (0805)
    C6,C7   100nF TPS2051 input decoupling (0603)
    C8-C11  100nF Ethernet coupling (0603)
    C12     100nF 6N138 VCC decoupling (0603)
  Resistors (5):
    R1  220ohm MIDI IN series (0603)
    R2  470ohm MIDI RX pull-up (0603)
    R3  33ohm  MIDI OUT series (0603)
    R4  10ohm  MIDI OUT source (0603)
    R5  12kohm FE1.1s REXT (0603)
  Diode (1):
    D1  1N4148 MIDI IN protection (SOD-123)
  Connectors (10):
    J1  USB-A dual stacked (67298-4090, through-hole)
    J2  RJ45 MagJack w/ magnetics (through-hole)
    J3  3.5mm TRS MIDI IN (SJ-3523-SMT)
    J4  3.5mm TRS MIDI OUT (SJ-3523-SMT)
    J5  FFC 12-pin ZIF 1.0mm
    J6  6-pin header Ethernet ribbon (2.54mm)
    J7  4-pin header HP breakout input (2.54mm)
    J8  Headphone TRS jack (through-hole)
    J9  3-pin header HP amp output (2.54mm)
    VR1 Dual-gang 10kohm log pot (through-hole)

Layout (top view, y=0 = panel edge, y=80 = interior/FFC edge):

  x=0                                                     x=50
  ┌──────────────────────────────────────────────────────────┐
  │  J1 USB-A (12,8)          J2 RJ45 (38,10)               │ y=0
  │                                                          │
  │  U1 FE1.1s (14,24)    U2(30,22) U3(38,22)              │
  │  Y1(5,24) C1 C2       C6  C7    R5                     │
  │  C3 C4 C5                                               │
  │                        U4 6N138 (38,32)                 │
  │  J3 MIDI_IN (10,42)   R1 R2 D1  C12                    │
  │  J4 MIDI_OUT (30,42)  R3 R4                             │
  │                                                          │
  │  J8 HP jack (10,58)   VR1 pot (30,58)                   │
  │                        J7(42,58) J9(42,52)              │
  │                                                          │
  │  J5 FFC (12,76)        J6 ETH hdr (38,76)              │ y=80
  └──────────────────────────────────────────────────────────┘

FE1.1s pinout (SSOP-28) — NEEDS VERIFICATION against actual datasheet:
  Pins 1-14 left side (top to bottom), pins 15-28 right side (bottom to top)
  Pin 1:  VDD5_2    Pin 28: VDD5
  Pin 2:  DM0       Pin 27: GND_2
  Pin 3:  DP0       Pin 26: GND
  Pin 4:  VDD33     Pin 25: TEST_N
  Pin 5:  XO        Pin 24: BUS_PWR_N
  Pin 6:  XI        Pin 23: SUSP_N
  Pin 7:  REXT      Pin 22: CFG_SEL0
  Pin 8:  VDD33O    Pin 21: CFG_SEL1
  Pin 9:  DM4       Pin 20: PSELF
  Pin 10: DP4       Pin 19: PGANG_N
  Pin 11: DM3       Pin 18: PWREN_N
  Pin 12: DP3       Pin 17: OVCR_N
  Pin 13: DM2       Pin 16: DP1
  Pin 14: DP2       Pin 15: DM1
"""

import uuid
import math
import os


# ---------------------------------------------------------------------------
# Board parameters
# ---------------------------------------------------------------------------

BOARD_W = 50.0   # mm
BOARD_H = 80.0   # mm
CORNER_R = 1.0   # mm

# Layers
F_CU = "F.Cu"
B_CU = "B.Cu"
F_SILK = "F.SilkS"
B_SILK = "B.SilkS"
F_MASK = "F.Mask"
B_MASK = "B.Mask"
F_FAB = "F.Fab"
F_CRTYD = "F.CrtYd"
EDGE_CUTS = "Edge.Cuts"


# ---------------------------------------------------------------------------
# Net definitions
# ---------------------------------------------------------------------------

NETS = {
    0: "",
    1: "GND",
    2: "5V_DIG",
    3: "V33",
    4: "USB_UP_DP",
    5: "USB_UP_DM",
    6: "USB_DN1_DP",
    7: "USB_DN1_DM",
    8: "USB_DN2_DP",
    9: "USB_DN2_DM",
    10: "VBUS1",
    11: "VBUS2",
    12: "XTAL_IN",
    13: "XTAL_OUT",
    14: "REXT_N",
    15: "ETH_TXP",
    16: "ETH_TXN",
    17: "ETH_RXP",
    18: "ETH_RXN",
    19: "ETH_TXP_MJ",
    20: "ETH_TXN_MJ",
    21: "ETH_RXP_MJ",
    22: "ETH_RXN_MJ",
    23: "ETH_LED",
    24: "MIDI_RX",
    25: "MIDI_TX",
    26: "MIDI_IN_R",
    27: "MIDI_IN_OA",
    28: "MIDI_IN_OK",
    29: "MIDI_OUT_SRC",
    30: "MIDI_OUT_SINK",
    31: "HP_L",
    32: "HP_R",
    33: "5V_A",
    34: "HP_AMP_L",
    35: "HP_AMP_R",
    36: "HP_OUT_L",
    37: "HP_OUT_R",
}


# ---------------------------------------------------------------------------
# Component-to-net mapping
# ---------------------------------------------------------------------------

def build_comp_nets():
    cn = {}

    # ── FE1.1s USB hub (U1, SSOP-28) ──
    # NEEDS VERIFICATION — pin-to-function mapping from datasheet
    cn["U1"] = {
        "1": 2,    # VDD5_2 → 5V_DIG
        "2": 5,    # DM0 → USB_UP_DM
        "3": 4,    # DP0 → USB_UP_DP
        "4": 3,    # VDD33 → V33
        "5": 13,   # XO → XTAL_OUT
        "6": 12,   # XI → XTAL_IN
        "7": 14,   # REXT → REXT_N
        "8": 3,    # VDD33O → V33
        "9": 1,    # DM4 → GND (unused port)
        "10": 1,   # DP4 → GND (unused port)
        "11": 1,   # DM3 → GND (unused port)
        "12": 1,   # DP3 → GND (unused port)
        "13": 9,   # DM2 → USB_DN2_DM
        "14": 8,   # DP2 → USB_DN2_DP
        "15": 7,   # DM1 → USB_DN1_DM
        "16": 6,   # DP1 → USB_DN1_DP
        "17": 3,   # OVCR_N → V33 (tie high, no OC detect via hub)
        "18": 0,   # PWREN_N → NC (TPS2051 always enabled)
        "19": 1,   # PGANG_N → GND (gang mode)
        "20": 2,   # PSELF → 5V_DIG (self-powered)
        "21": 1,   # CFG_SEL1 → GND
        "22": 1,   # CFG_SEL0 → GND
        "23": 0,   # SUSP_N → NC
        "24": 1,   # BUS_PWR_N → GND
        "25": 3,   # TEST_N → V33 (tie high)
        "26": 1,   # GND
        "27": 1,   # GND_2
        "28": 2,   # VDD5 → 5V_DIG
    }

    # ── TPS2051 #1 (U2, SOT-23-5) — USB port 1 power ──
    cn["U2"] = {
        "1": 2,    # IN → 5V_DIG
        "2": 0,    # ~OC → NC (overcurrent fault, could go to GPIO)
        "3": 1,    # GND
        "4": 2,    # EN → 5V_DIG (always enabled)
        "5": 10,   # OUT → VBUS1
    }

    # ── TPS2051 #2 (U3, SOT-23-5) — USB port 2 power ──
    cn["U3"] = {
        "1": 2,    # IN → 5V_DIG
        "2": 0,    # ~OC → NC
        "3": 1,    # GND
        "4": 2,    # EN → 5V_DIG (always enabled)
        "5": 11,   # OUT → VBUS2
    }

    # ── 6N138 optocoupler (U4, DIP-8) — MIDI IN ──
    cn["U4"] = {
        "1": 0,    # NC
        "2": 27,   # Anode → MIDI_IN_OA
        "3": 28,   # Cathode → MIDI_IN_OK
        "4": 0,    # NC
        "5": 1,    # GND
        "6": 24,   # VO (collector) → MIDI_RX
        "7": 3,    # VB (base) → V33
        "8": 3,    # VCC → V33
    }

    # ── 12 MHz crystal (Y1) ──
    cn["Y1"] = {
        "1": 12,   # → XTAL_IN
        "2": 13,   # → XTAL_OUT
    }

    # ── Crystal load caps ──
    cn["C1"] = {"1": 12, "2": 1}   # XTAL_IN → GND
    cn["C2"] = {"1": 13, "2": 1}   # XTAL_OUT → GND

    # ── FE1.1s decoupling ──
    cn["C3"] = {"1": 2, "2": 1}    # 5V_DIG → GND (VDD5)
    cn["C4"] = {"1": 3, "2": 1}    # V33 → GND (VDD33)
    cn["C5"] = {"1": 3, "2": 1}    # V33 → GND (VDD33 bulk 10uF)

    # ── TPS2051 decoupling ──
    cn["C6"] = {"1": 2, "2": 1}    # 5V_DIG → GND (U2 input)
    cn["C7"] = {"1": 2, "2": 1}    # 5V_DIG → GND (U3 input)

    # ── Ethernet coupling caps ──
    cn["C8"]  = {"1": 15, "2": 19}  # ETH_TXP → ETH_TXP_MJ
    cn["C9"]  = {"1": 16, "2": 20}  # ETH_TXN → ETH_TXN_MJ
    cn["C10"] = {"1": 17, "2": 21}  # ETH_RXP → ETH_RXP_MJ
    cn["C11"] = {"1": 18, "2": 22}  # ETH_RXN → ETH_RXN_MJ

    # ── 6N138 decoupling ──
    cn["C12"] = {"1": 3, "2": 1}   # V33 → GND

    # ── MIDI IN resistor (220Ω series) ──
    cn["R1"] = {"1": 26, "2": 27}  # MIDI_IN_R → MIDI_IN_OA

    # ── MIDI RX pull-up (470Ω to V33) ──
    cn["R2"] = {"1": 3, "2": 24}   # V33 → MIDI_RX

    # ── MIDI OUT series (33Ω) ──
    cn["R3"] = {"1": 30, "2": 25}  # MIDI_OUT_SINK → MIDI_TX

    # ── MIDI OUT source (10Ω) ──
    cn["R4"] = {"1": 3, "2": 29}   # V33 → MIDI_OUT_SRC

    # ── FE1.1s REXT (12kΩ to GND) ──
    cn["R5"] = {"1": 14, "2": 1}   # REXT_N → GND

    # ── MIDI IN protection diode (1N4148) ──
    # Cathode at opto anode (reverse protection)
    cn["D1"] = {"1": 27, "2": 28}  # K=MIDI_IN_OA, A=MIDI_IN_OK

    # ── USB-A dual stacked (J1) ──
    # Port 1 (bottom): pins 1-4, Port 2 (top): pins 5-8
    cn["J1"] = {
        "1": 10,   # Port 1 VBUS → VBUS1
        "2": 7,    # Port 1 D- → USB_DN1_DM
        "3": 6,    # Port 1 D+ → USB_DN1_DP
        "4": 1,    # Port 1 GND
        "5": 11,   # Port 2 VBUS → VBUS2
        "6": 9,    # Port 2 D- → USB_DN2_DM
        "7": 8,    # Port 2 D+ → USB_DN2_DP
        "8": 1,    # Port 2 GND
        "S1": 1,   # Shield → GND
        "S2": 1,   # Shield → GND
    }

    # ── RJ45 MagJack (J2) ──
    # Simplified pin mapping for MagJack with integrated magnetics
    # PHY-side pins (from coupling caps)
    cn["J2"] = {
        "1": 19,   # TX+ → ETH_TXP_MJ (post-cap)
        "2": 20,   # TX- → ETH_TXN_MJ
        "3": 21,   # RX+ → ETH_RXP_MJ
        "4": 1,    # GND (center tap)
        "5": 1,    # GND (center tap)
        "6": 22,   # RX- → ETH_RXN_MJ
        "7": 23,   # LED+ → ETH_LED
        "8": 1,    # LED- → GND
        "S1": 1,   # Shield → GND
        "S2": 1,   # Shield → GND
    }

    # ── MIDI IN jack (J3, 3.5mm TRS Type A) ──
    cn["J3"] = {
        "T": 28,   # Tip (sink) → MIDI_IN_OK
        "R": 26,   # Ring (source) → MIDI_IN_R
        "S": 1,    # Sleeve → GND
    }

    # ── MIDI OUT jack (J4, 3.5mm TRS Type A) ──
    cn["J4"] = {
        "T": 30,   # Tip (sink) → MIDI_OUT_SINK
        "R": 29,   # Ring (source) → MIDI_OUT_SRC
        "S": 1,    # Sleeve → GND
    }

    # ── FFC 12-pin ZIF (J5) — Main Board interconnect ──
    cn["J5"] = {
        "1": 15,   # ETH_TXP
        "2": 16,   # ETH_TXN
        "3": 1,    # GND (guard)
        "4": 17,   # ETH_RXP
        "5": 18,   # ETH_RXN
        "6": 1,    # GND (guard)
        "7": 4,    # USB_UP_DP
        "8": 5,    # USB_UP_DM
        "9": 24,   # MIDI_RX
        "10": 25,  # MIDI_TX
        "11": 2,   # 5V_DIG
        "12": 1,   # GND
    }

    # ── 6-pin Ethernet header (J6) ──
    cn["J6"] = {
        "1": 15,   # ETH_TXP
        "2": 16,   # ETH_TXN
        "3": 17,   # ETH_RXP
        "4": 18,   # ETH_RXN
        "5": 23,   # ETH_LED
        "6": 1,    # GND
    }

    # ── HP breakout input header (J7, 4-pin) ──
    cn["J7"] = {
        "1": 31,   # HP_L
        "2": 32,   # HP_R
        "3": 33,   # 5V_A
        "4": 1,    # GND
    }

    # ── Headphone TRS jack (J8) ──
    cn["J8"] = {
        "T": 36,   # Tip → HP_OUT_L
        "R": 37,   # Ring → HP_OUT_R
        "S": 1,    # Sleeve → GND
    }

    # ── HP amp output header (J9, 3-pin) ──
    cn["J9"] = {
        "1": 34,   # HP_AMP_L
        "2": 35,   # HP_AMP_R
        "3": 1,    # GND
    }

    # ── Volume pot (VR1, dual-gang) ──
    # Gang A: L channel, Gang B: R channel
    # Pin layout: A1(input), A2(wiper), A3(gnd), B1(input), B2(wiper), B3(gnd)
    cn["VR1"] = {
        "A1": 34,  # HP_AMP_L input
        "A2": 36,  # HP_OUT_L wiper → headphone jack
        "A3": 1,   # GND
        "B1": 35,  # HP_AMP_R input
        "B2": 37,  # HP_OUT_R wiper → headphone jack
        "B3": 1,   # GND
    }

    return cn


COMP_NETS = build_comp_nets()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def gen_uuid():
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Board outline
# ---------------------------------------------------------------------------

def board_outline():
    r = CORNER_R
    w, h = BOARD_W, BOARD_H
    lines = []

    edges = [
        (r, 0, w - r, 0),
        (w, r, w, h - r),
        (w - r, h, r, h),
        (0, h - r, 0, r),
    ]
    for x1, y1, x2, y2 in edges:
        lines.append(
            f'  (gr_line (start {x1} {y1}) (end {x2} {y2}) '
            f'(layer "{EDGE_CUTS}") (stroke (width 0.05) (type solid)) '
            f'(uuid "{gen_uuid()}"))'
        )

    corners = [
        (r, r, 180, 270),
        (w - r, r, 270, 360),
        (w - r, h - r, 0, 90),
        (r, h - r, 90, 180),
    ]
    for cx, cy, start, end in corners:
        s_a = math.radians(start)
        m_a = math.radians((start + end) / 2)
        e_a = math.radians(end)
        sx, sy = cx + r * math.cos(s_a), cy + r * math.sin(s_a)
        mx, my = cx + r * math.cos(m_a), cy + r * math.sin(m_a)
        ex, ey = cx + r * math.cos(e_a), cy + r * math.sin(e_a)
        lines.append(
            f'  (gr_arc (start {sx:.4f} {sy:.4f}) (mid {mx:.4f} {my:.4f}) '
            f'(end {ex:.4f} {ey:.4f}) (layer "{EDGE_CUTS}") '
            f'(stroke (width 0.05) (type solid)) (uuid "{gen_uuid()}"))'
        )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generic footprint helpers
# ---------------------------------------------------------------------------

def _pad_smd(name, px, py, sx, sy, net_code, layer=None, rotation=0):
    if layer is None:
        layer = F_CU
    mask = F_MASK if layer == F_CU else B_MASK
    net_name = NETS.get(net_code, "")
    rot_str = f" {rotation}" if rotation else ""
    return (
        f'    (pad "{name}" smd roundrect (at {px} {py}{rot_str}) (size {sx} {sy}) '
        f'(layers "{layer}" "{mask}") (roundrect_rratio 0.25) '
        f'(net {net_code} "{net_name}") (uuid "{gen_uuid()}"))'
    )


def _pad_thru(name, px, py, size, drill, net_code):
    net_name = NETS.get(net_code, "")
    return (
        f'    (pad "{name}" thru_hole circle (at {px} {py}) (size {size} {size}) '
        f'(drill {drill}) (layers "*.Cu" "*.Mask") '
        f'(net {net_code} "{net_name}") (uuid "{gen_uuid()}"))'
    )


def _pad_thru_rect(name, px, py, sx, sy, drill, net_code):
    net_name = NETS.get(net_code, "")
    return (
        f'    (pad "{name}" thru_hole roundrect (at {px} {py}) (size {sx} {sy}) '
        f'(drill {drill}) (layers "*.Cu" "*.Mask") (roundrect_rratio 0.25) '
        f'(net {net_code} "{net_name}") (uuid "{gen_uuid()}"))'
    )


def _silk_rect(x1, y1, x2, y2, layer=None):
    if layer is None:
        layer = F_SILK
    lines = []
    segs = [(x1, y1, x2, y1), (x2, y1, x2, y2), (x2, y2, x1, y2), (x1, y2, x1, y1)]
    for sx, sy, ex, ey in segs:
        lines.append(
            f'    (fp_line (start {sx} {sy}) (end {ex} {ey}) '
            f'(stroke (width 0.12) (type solid)) (layer "{layer}") '
            f'(uuid "{gen_uuid()}"))'
        )
    return "\n".join(lines)


def _fp_wrapper(lib_name, ref, value, x, y, rotation, pad_lines, silk="", layer=None):
    if layer is None:
        layer = F_CU
    silk_layer = F_SILK if layer == F_CU else B_SILK
    return f"""  (footprint "{lib_name}"
    (layer "{layer}")
    (uuid "{gen_uuid()}")
    (at {x} {y} {rotation})
    (property "Reference" "{ref}" (at 0 -2 {rotation}) (layer "{silk_layer}") (uuid "{gen_uuid()}") (effects (font (size 0.8 0.8) (thickness 0.12))))
    (property "Value" "{value}" (at 0 2 {rotation}) (layer "{F_FAB}") (uuid "{gen_uuid()}") (effects (font (size 0.8 0.8) (thickness 0.12))))
    (property "Footprint" "{lib_name}" (at 0 0 {rotation}) (layer "{F_FAB}") (uuid "{gen_uuid()}") (effects (font (size 1 1) (thickness 0.15)) hide))
{pad_lines}
{silk}
  )"""


# ---------------------------------------------------------------------------
# Footprint generators
# ---------------------------------------------------------------------------

def fp_ssop28(ref, x, y, rotation, nets):
    """SSOP-28 (FE1.1s). 28 pins, 0.65mm pitch, body 5.3x10.2mm.
    Pad-to-pad span ~8.0mm (±4.0 from center). Pad size 1.5x0.4mm."""
    pads = []
    half_span = 13 * 0.65 / 2  # 4.225mm

    pad_w, pad_h = 1.5, 0.4
    if rotation in (90, 270):
        pad_sx, pad_sy = pad_h, pad_w
    else:
        pad_sx, pad_sy = pad_w, pad_h

    for pin in range(1, 29):
        if pin <= 14:
            px = -4.0
            py = -half_span + (pin - 1) * 0.65
        else:
            px = 4.0
            py = half_span - (pin - 15) * 0.65
        net_code = nets.get(str(pin), 0)
        pads.append(_pad_smd(str(pin), px, py, pad_sx, pad_sy, net_code))

    body_hw = 2.65
    body_hh = half_span + 0.4
    silk = _silk_rect(-body_hw, -body_hh, body_hw, body_hh)
    return _fp_wrapper("Package_SO:SSOP-28_5.3x10.2mm_P0.65mm", ref, "FE1.1s",
                       x, y, rotation, "\n".join(pads), silk)


def fp_sot23_5(ref, x, y, rotation, nets, value="TPS2051"):
    """SOT-23-5. Pins: 1,2,3 on left; 4,5 on right.
    Pitch 0.95mm, pad-to-pad ~2.6mm."""
    positions = {
        "1": (-1.3, -0.95),
        "2": (-1.3, 0.0),
        "3": (-1.3, 0.95),
        "4": (1.3, 0.95),
        "5": (1.3, -0.95),
    }
    pads = []
    pad_w, pad_h = 1.0, 0.6
    if rotation in (90, 270):
        pad_sx, pad_sy = pad_h, pad_w
    else:
        pad_sx, pad_sy = pad_w, pad_h

    for pin, (px, py) in positions.items():
        net_code = nets.get(pin, 0)
        pads.append(_pad_smd(pin, px, py, pad_sx, pad_sy, net_code))

    silk = _silk_rect(-1.0, -1.6, 1.0, 1.6)
    return _fp_wrapper("Package_TO_SOT_SMD:SOT-23-5", ref, value,
                       x, y, rotation, "\n".join(pads), silk)


def fp_dip8(ref, x, y, rotation, nets, value="6N138"):
    """DIP-8. 2.54mm pitch, 7.62mm row spacing. Through-hole."""
    pads = []
    for pin in range(1, 9):
        if pin <= 4:
            px = -3.81
            py = (pin - 1) * 2.54 - 3.81
        else:
            px = 3.81
            py = (8 - pin) * 2.54 - 3.81
        net_code = nets.get(str(pin), 0)
        pads.append(_pad_thru(str(pin), px, py, 1.6, 0.8, net_code))

    silk = _silk_rect(-4.5, -5.5, 4.5, 5.5)
    return _fp_wrapper("Package_DIP:DIP-8_W7.62mm", ref, value,
                       x, y, rotation, "\n".join(pads), silk)


def fp_crystal_3225(ref, x, y, rotation, nets):
    """3225 SMD crystal (3.2x2.5mm). 2 pads."""
    pads = []
    pad_w, pad_h = 1.2, 1.0
    if rotation in (90, 270):
        pad_sx, pad_sy = pad_h, pad_w
    else:
        pad_sx, pad_sy = pad_w, pad_h

    for pin, px in [("1", -1.1), ("2", 1.1)]:
        net_code = nets.get(pin, 0)
        pads.append(_pad_smd(pin, px, 0, pad_sx, pad_sy, net_code))

    silk = _silk_rect(-1.8, -1.5, 1.8, 1.5)
    return _fp_wrapper("Crystal:Crystal_SMD_3225-2Pin_3.2x2.5mm", ref, "12MHz",
                       x, y, rotation, "\n".join(pads), silk)


def fp_c0603(ref, x, y, rotation, nets, value="100nF"):
    """0603 capacitor. Pads at (-0.8, 0) and (0.8, 0)."""
    pads = []
    for pin, px in [("1", -0.8), ("2", 0.8)]:
        net_code = nets.get(pin, 0)
        pads.append(_pad_smd(pin, px, 0, 0.9, 1.0, net_code))
    return _fp_wrapper("Capacitor_SMD:C_0603_1608Metric", ref, value,
                       x, y, rotation, "\n".join(pads))


def fp_c0805(ref, x, y, rotation, nets, value="10uF"):
    """0805 capacitor. Pads at (-1.0, 0) and (1.0, 0)."""
    pads = []
    for pin, px in [("1", -1.0), ("2", 1.0)]:
        net_code = nets.get(pin, 0)
        pads.append(_pad_smd(pin, px, 0, 1.0, 1.3, net_code))
    return _fp_wrapper("Capacitor_SMD:C_0805_2012Metric", ref, value,
                       x, y, rotation, "\n".join(pads))


def fp_r0603(ref, x, y, rotation, nets, value=""):
    """0603 resistor. Same footprint as C_0603."""
    pads = []
    for pin, px in [("1", -0.8), ("2", 0.8)]:
        net_code = nets.get(pin, 0)
        pads.append(_pad_smd(pin, px, 0, 0.9, 1.0, net_code))
    return _fp_wrapper("Resistor_SMD:R_0603_1608Metric", ref, value,
                       x, y, rotation, "\n".join(pads))


def fp_sod123(ref, x, y, rotation, nets):
    """1N4148 SOD-123. Pad 1=K, Pad 2=A."""
    pads = []
    for pin, px in [("1", -1.1), ("2", 1.1)]:
        net_code = nets.get(pin, 0)
        pads.append(_pad_smd(pin, px, 0, 1.0, 0.7, net_code))
    silk = _silk_rect(-1.8, -0.6, 1.8, 0.6)
    return _fp_wrapper("Diode_SMD:D_SOD-123", ref, "1N4148",
                       x, y, rotation, "\n".join(pads), silk)


def fp_usb_a_dual(ref, x, y, rotation, nets):
    """USB-A dual stacked (Amphenol 67298-4090). Through-hole.
    8 signal pins (4 per port) + 2 shield tabs.
    Port 1 (bottom): pins 1-4, Port 2 (top): pins 5-8.
    Pin pitch 2.0mm. Rows separated by ~2.0mm vertically.
    Body ~14.2mm wide x 17mm deep."""
    pads = []
    # Port 1 pins (bottom row) — pin 1 at left
    for i, pin in enumerate(["1", "2", "3", "4"]):
        px = -3.0 + i * 2.0
        py = 0.0
        pads.append(_pad_thru(pin, px, py, 1.6, 0.8, nets.get(pin, 0)))

    # Port 2 pins (top row, offset in Y)
    for i, pin in enumerate(["5", "6", "7", "8"]):
        px = -3.0 + i * 2.0
        py = -2.5
        pads.append(_pad_thru(pin, px, py, 1.6, 0.8, nets.get(pin, 0)))

    # Shield tabs (large mounting holes)
    for i, (pin, sx) in enumerate([("S1", -6.5), ("S2", 6.5)]):
        pads.append(_pad_thru(pin, sx, -1.25, 2.5, 1.5, nets.get(pin, 0)))

    silk = _silk_rect(-7.1, -8.5, 7.1, 8.5)
    return _fp_wrapper("Connector_USB:USB_A_Amphenol_67298-4090_Dual", ref,
                       "67298-4090", x, y, rotation, "\n".join(pads), silk)


def fp_rj45_magjack(ref, x, y, rotation, nets):
    """RJ45 MagJack with integrated magnetics. Through-hole.
    ~16mm wide x 21mm deep. Simplified 8 signal pins + 2 shield.
    Pin row at back of connector body."""
    pads = []
    # Signal pins in two rows of 4
    for i, pin in enumerate(["1", "2", "3", "4"]):
        px = -3.81 + i * 2.54
        py = 0.0
        pads.append(_pad_thru(pin, px, py, 1.6, 0.9, nets.get(pin, 0)))

    for i, pin in enumerate(["5", "6", "7", "8"]):
        px = -3.81 + i * 2.54
        py = 2.54
        pads.append(_pad_thru(pin, px, py, 1.6, 0.9, nets.get(pin, 0)))

    # Shield/mounting tabs
    for pin, sx in [("S1", -7.9), ("S2", 7.9)]:
        pads.append(_pad_thru(pin, sx, 1.27, 3.0, 2.0, nets.get(pin, 0)))

    silk = _silk_rect(-8.0, -10.5, 8.0, 5.5)
    return _fp_wrapper("Connector_RJ:RJ45_MagJack", ref, "RJ45_MagJack",
                       x, y, rotation, "\n".join(pads), silk)


def fp_sj3523_smt(ref, x, y, rotation, nets):
    """CUI SJ-3523-SMT 3.5mm TRS jack. SMD, 3 pins.
    Body ~12mm x 5mm. Pads: T(tip), R(ring), S(sleeve)."""
    pads = []
    # Approximate pad positions for SJ-3523-SMT
    pin_pos = {"T": (-4.5, 0.0), "R": (0.0, 2.0), "S": (4.5, 0.0)}
    for pin, (px, py) in pin_pos.items():
        net_code = nets.get(pin, 0)
        pads.append(_pad_smd(pin, px, py, 1.8, 1.2, net_code))

    silk = _silk_rect(-6.0, -2.5, 6.0, 3.5)
    return _fp_wrapper("Connector_Audio:CUI_SJ-3523-SMT", ref, "SJ-3523-SMT",
                       x, y, rotation, "\n".join(pads), silk)


def fp_ffc_12pin(ref, x, y, rotation, nets):
    """FFC/FPC ZIF connector, 12-pin, 1.0mm pitch. SMD.
    Pins span 11mm. Body ~14mm x 3mm."""
    pads = []
    for i in range(12):
        pin = str(i + 1)
        px = -5.5 + i * 1.0
        net_code = nets.get(pin, 0)
        pads.append(_pad_smd(pin, px, 0, 0.6, 1.5, net_code))

    # Mounting pads
    for sx in [-7.0, 7.0]:
        pads.append(
            f'    (pad "MP" smd rect (at {sx} 0) (size 1.2 2.0) '
            f'(layers "{F_CU}" "{F_MASK}") '
            f'(net 1 "GND") (uuid "{gen_uuid()}"))'
        )

    silk = _silk_rect(-7.5, -1.8, 7.5, 1.8)
    return _fp_wrapper("Connector_FFC-FPC:FFC_12pin_1mm", ref, "FFC-12",
                       x, y, rotation, "\n".join(pads), silk)


def fp_header(ref, x, y, rotation, nets, pin_count, pitch=2.54, value="Header"):
    """Generic pin header. Through-hole, vertical."""
    pads = []
    for i in range(pin_count):
        pin = str(i + 1)
        px = i * pitch
        net_code = nets.get(pin, 0)
        pads.append(_pad_thru(pin, px, 0, 1.75, 1.0, net_code))

    total_w = (pin_count - 1) * pitch
    silk = _silk_rect(-1.3, -1.3, total_w + 1.3, 1.3)
    lib = f"Connector_PinHeader_2.54mm:PinHeader_1x{pin_count:02d}_P2.54mm_Vertical"
    return _fp_wrapper(lib, ref, value, x, y, rotation, "\n".join(pads), silk)


def fp_hp_trs_jack(ref, x, y, rotation, nets):
    """Headphone TRS jack (Switchcraft 35RASMT2BHNTRX). Through-hole.
    3 main pins (T, R, S) for audio. ~12mm x 6mm body."""
    pads = []
    pin_pos = {"T": (0.0, 0.0), "R": (5.0, 0.0), "S": (10.0, 0.0)}
    for pin, (px, py) in pin_pos.items():
        net_code = nets.get(pin, 0)
        pads.append(_pad_thru(pin, px, py, 2.0, 1.0, net_code))

    silk = _silk_rect(-1.5, -3.0, 11.5, 3.0)
    return _fp_wrapper("Connector_Audio:Jack_3.5mm_Switchcraft_35RASMT2BHNTRX",
                       ref, "HP_TRS", x, y, rotation, "\n".join(pads), silk)


def fp_pot_dual(ref, x, y, rotation, nets):
    """Dual-gang potentiometer. Through-hole, 6 pins (A1,A2,A3,B1,B2,B3).
    3 pins per gang, 2.54mm pitch within gang, ~5mm between gangs.
    ~10mm diameter body."""
    pads = []
    pins = ["A1", "A2", "A3", "B1", "B2", "B3"]
    for i, pin in enumerate(pins):
        px = (i % 3) * 2.54
        py = (i // 3) * 5.0
        net_code = nets.get(pin, 0)
        pads.append(_pad_thru(pin, px, py, 1.75, 1.0, net_code))

    silk = _silk_rect(-1.5, -1.5, 6.6, 6.5)
    return _fp_wrapper("Potentiometer_THT:Potentiometer_Dual", ref, "10k_Dual",
                       x, y, rotation, "\n".join(pads), silk)


# ---------------------------------------------------------------------------
# Component placement
# ---------------------------------------------------------------------------

# All coordinates are (x, y) on the 50x80mm board
# y=0 is panel edge (large connectors), y=80 is interior edge (FFC)

PLACEMENTS = {
    # ── Panel-mount connectors ──
    "J1":  {"func": "usb_a_dual",   "x": 12, "y": 8,  "rot": 0},
    "J2":  {"func": "rj45_magjack", "x": 38, "y": 10, "rot": 0},
    "J3":  {"func": "sj3523_smt",   "x": 10, "y": 42, "rot": 0},
    "J4":  {"func": "sj3523_smt",   "x": 30, "y": 42, "rot": 0},
    "J8":  {"func": "hp_trs_jack",  "x": 6,  "y": 58, "rot": 0},
    "VR1": {"func": "pot_dual",     "x": 28, "y": 56, "rot": 0},

    # ── ICs ──
    "U1":  {"func": "ssop28",       "x": 14, "y": 24, "rot": 0},
    "U2":  {"func": "sot23_5",      "x": 30, "y": 22, "rot": 0},
    "U3":  {"func": "sot23_5",      "x": 38, "y": 22, "rot": 0},
    "U4":  {"func": "dip8",         "x": 38, "y": 34, "rot": 0},

    # ── Crystal ──
    "Y1":  {"func": "crystal_3225", "x": 5,  "y": 24, "rot": 0},

    # ── Crystal load caps ──
    "C1":  {"func": "c0603_15pF",   "x": 5,  "y": 28, "rot": 0},
    "C2":  {"func": "c0603_15pF",   "x": 5,  "y": 20, "rot": 0},

    # ── FE1.1s decoupling ──
    "C3":  {"func": "c0603",        "x": 8,  "y": 18, "rot": 0},
    "C4":  {"func": "c0603",        "x": 20, "y": 18, "rot": 0},
    "C5":  {"func": "c0805",        "x": 20, "y": 30, "rot": 0},

    # ── TPS2051 decoupling ──
    "C6":  {"func": "c0603",        "x": 30, "y": 18, "rot": 0},
    "C7":  {"func": "c0603",        "x": 38, "y": 18, "rot": 0},

    # ── Ethernet coupling caps ──
    "C8":  {"func": "c0603",        "x": 26, "y": 68, "rot": 90},
    "C9":  {"func": "c0603",        "x": 29, "y": 68, "rot": 90},
    "C10": {"func": "c0603",        "x": 32, "y": 68, "rot": 90},
    "C11": {"func": "c0603",        "x": 35, "y": 68, "rot": 90},

    # ── 6N138 decoupling ──
    "C12": {"func": "c0603",        "x": 44, "y": 30, "rot": 0},

    # ── MIDI resistors ──
    "R1":  {"func": "r0603_220",    "x": 20, "y": 38, "rot": 0},
    "R2":  {"func": "r0603_470",    "x": 44, "y": 38, "rot": 90},
    "R3":  {"func": "r0603_33",     "x": 20, "y": 46, "rot": 0},
    "R4":  {"func": "r0603_10",     "x": 34, "y": 46, "rot": 0},
    "R5":  {"func": "r0603_12k",    "x": 8,  "y": 30, "rot": 0},

    # ── MIDI protection diode ──
    "D1":  {"func": "sod123",       "x": 24, "y": 34, "rot": 0},

    # ── Interior connectors ──
    "J5":  {"func": "ffc_12pin",    "x": 14, "y": 76, "rot": 0},
    "J6":  {"func": "header_6pin",  "x": 32, "y": 76, "rot": 0},
    "J7":  {"func": "header_4pin",  "x": 42, "y": 62, "rot": 90},
    "J9":  {"func": "header_3pin",  "x": 42, "y": 48, "rot": 90},
}


# ---------------------------------------------------------------------------
# PCB assembly
# ---------------------------------------------------------------------------

def generate_pcb():
    net_decls = "\n".join(
        f'  (net {code} "{name}")' for code, name in sorted(NETS.items())
    )

    outline = board_outline()

    footprints = []
    for ref, info in PLACEMENTS.items():
        func_name = info["func"]
        x, y, rot = info["x"], info["y"], info["rot"]
        nets = COMP_NETS[ref]

        if func_name == "usb_a_dual":
            footprints.append(fp_usb_a_dual(ref, x, y, rot, nets))
        elif func_name == "rj45_magjack":
            footprints.append(fp_rj45_magjack(ref, x, y, rot, nets))
        elif func_name == "sj3523_smt":
            footprints.append(fp_sj3523_smt(ref, x, y, rot, nets))
        elif func_name == "hp_trs_jack":
            footprints.append(fp_hp_trs_jack(ref, x, y, rot, nets))
        elif func_name == "pot_dual":
            footprints.append(fp_pot_dual(ref, x, y, rot, nets))
        elif func_name == "ssop28":
            footprints.append(fp_ssop28(ref, x, y, rot, nets))
        elif func_name == "sot23_5":
            val = "TPS2051" if ref in ("U2", "U3") else "SOT-23-5"
            footprints.append(fp_sot23_5(ref, x, y, rot, nets, val))
        elif func_name == "dip8":
            footprints.append(fp_dip8(ref, x, y, rot, nets))
        elif func_name == "crystal_3225":
            footprints.append(fp_crystal_3225(ref, x, y, rot, nets))
        elif func_name in ("c0603", "c0603_15pF"):
            val = "15pF" if "15pF" in func_name else "100nF"
            footprints.append(fp_c0603(ref, x, y, rot, nets, val))
        elif func_name == "c0805":
            footprints.append(fp_c0805(ref, x, y, rot, nets))
        elif func_name.startswith("r0603"):
            val = func_name.split("_", 1)[1] if "_" in func_name else ""
            footprints.append(fp_r0603(ref, x, y, rot, nets, val))
        elif func_name == "sod123":
            footprints.append(fp_sod123(ref, x, y, rot, nets))
        elif func_name == "ffc_12pin":
            footprints.append(fp_ffc_12pin(ref, x, y, rot, nets))
        elif func_name == "header_6pin":
            footprints.append(fp_header(ref, x, y, rot, nets, 6, value="ETH_HDR"))
        elif func_name == "header_4pin":
            footprints.append(fp_header(ref, x, y, rot, nets, 4, value="HP_BRK"))
        elif func_name == "header_3pin":
            footprints.append(fp_header(ref, x, y, rot, nets, 3, value="HP_OUT"))

    all_footprints = "\n\n".join(footprints)

    # GND zone on B.Cu
    zone = f"""  (zone
    (net 1)
    (net_name "GND")
    (layer "{B_CU}")
    (uuid "{gen_uuid()}")
    (hatch edge 0.5)
    (connect_pads (clearance 0.2))
    (min_thickness 0.25)
    (fill yes (thermal_gap 0.5) (thermal_bridge_width 0.5))
    (polygon
      (pts
        (xy 0 0) (xy {BOARD_W} 0) (xy {BOARD_W} {BOARD_H}) (xy 0 {BOARD_H})
      )
    )
  )"""

    board_text = f"""  (gr_text "MIXTEE IO Board" (at {BOARD_W/2} {BOARD_H - 2}) (layer "{F_SILK}") (uuid "{gen_uuid()}")
    (effects (font (size 1.2 1.2) (thickness 0.15)))
  )"""

    pcb = f"""(kicad_pcb
  (version 20240108)
  (generator "mixtee_gen_io_board")
  (generator_version "1.0")
  (general
    (thickness 1.6)
    (legacy_teardrops no)
  )
  (paper "A4")
  (layers
    (0 "{F_CU}" signal)
    (31 "{B_CU}" signal)
    (32 "B.Adhes" user "B.Adhesive")
    (33 "F.Adhes" user "F.Adhesive")
    (34 "B.Paste" user)
    (35 "F.Paste" user)
    (36 "{B_SILK}" user "B.Silkscreen")
    (37 "{F_SILK}" user "F.Silkscreen")
    (38 "{B_MASK}" user "B.Mask")
    (39 "{F_MASK}" user "F.Mask")
    (40 "Dwgs.User" user "User.Drawings")
    (41 "Cmts.User" user "User.Comments")
    (42 "Eco1.User" user "User.Eco1")
    (43 "Eco2.User" user "User.Eco2")
    (44 "{EDGE_CUTS}" user)
    (45 "Margin" user)
    (46 "B.CrtYd" user "B.Courtyard")
    (47 "{F_CRTYD}" user "F.Courtyard")
    (48 "B.Fab" user "B.Fabrication")
    (49 "{F_FAB}" user "F.Fabrication")
    (50 "User.1" user)
    (51 "User.2" user)
    (52 "User.3" user)
    (53 "User.4" user)
    (54 "User.5" user)
    (55 "User.6" user)
    (56 "User.7" user)
    (57 "User.8" user)
    (58 "User.9" user)
  )
  (setup
    (pad_to_mask_clearance 0)
    (allow_soldermask_bridges_in_footprints no)
    (pcbplotparams
      (layerselection 0x00010fc_ffffffff)
      (plot_on_all_layers_selection 0x0000000_00000000)
      (disableapertmacros no)
      (usegerberextensions no)
      (usegerberattributes yes)
      (usegerberadvancedattributes yes)
      (creategerberjobfile yes)
      (dashed_line_dash_ratio 12.000000)
      (dashed_line_gap_ratio 3.000000)
      (svgprecision 4)
      (plotframeref no)
      (viasonmask no)
      (mode 1)
      (useauxorigin no)
      (hpglpennumber 1)
      (hpglpenspeed 20)
      (hpglpendiameter 15.000000)
      (pdf_front_fp_property_popups yes)
      (pdf_back_fp_property_popups yes)
      (pdf_metadata yes)
      (outputformat 1)
      (mirror no)
      (drillshape 1)
      (scaleselection 1)
      (outputdirectory "")
    )
  )
{net_decls}

{outline}

{all_footprints}

{zone}

{board_text}
)
"""
    return pcb


def generate_project():
    return """{
  "board": {
    "design_settings": {
      "defaults": {
        "board_outline_line_width": 0.05,
        "copper_line_width": 0.2,
        "copper_text_size_h": 1.5,
        "copper_text_size_v": 1.5,
        "copper_text_thickness": 0.3,
        "other_line_width": 0.1,
        "silk_line_width": 0.12,
        "silk_text_size_h": 1.0,
        "silk_text_size_v": 1.0,
        "silk_text_thickness": 0.15
      },
      "rules": {
        "min_clearance": 0.15,
        "min_track_width": 0.15,
        "min_via_annular_width": 0.15,
        "min_via_diameter": 0.6
      }
    },
    "layer_presets": [],
    "layer_pairs": []
  },
  "meta": {
    "filename": "mixtee-io-board.kicad_pro",
    "version": 1
  },
  "net_settings": {
    "classes": [
      {
        "name": "Default",
        "clearance": 0.2,
        "track_width": 0.25,
        "via_diameter": 0.6,
        "via_drill": 0.3
      },
      {
        "name": "Power",
        "clearance": 0.2,
        "track_width": 0.5,
        "via_diameter": 0.8,
        "via_drill": 0.4
      },
      {
        "name": "USB_Diff",
        "clearance": 0.15,
        "track_width": 0.2,
        "via_diameter": 0.6,
        "via_drill": 0.3,
        "nets": [
          "USB_UP_DP",
          "USB_UP_DM",
          "USB_DN1_DP",
          "USB_DN1_DM",
          "USB_DN2_DP",
          "USB_DN2_DM"
        ]
      }
    ],
    "net_colors": {}
  },
  "schematic": {
    "drawing": {},
    "meta": {
      "version": 1
    }
  },
  "sheets": []
}"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    out_dir = os.path.dirname(os.path.abspath(__file__))

    pcb_path = os.path.join(out_dir, "mixtee-io-board.kicad_pcb")
    with open(pcb_path, "w") as f:
        f.write(generate_pcb())
    print(f"PCB written to: {pcb_path}")

    pro_path = os.path.join(out_dir, "mixtee-io-board.kicad_pro")
    with open(pro_path, "w") as f:
        f.write(generate_project())
    print(f"Project written to: {pro_path}")

    fp_lib_path = os.path.join(out_dir, "fp-lib-table")
    with open(fp_lib_path, "w") as f:
        f.write("""(fp_lib_table
  (version 7)
  (lib (name "mixtee-footprints") (type "KiCad") (uri "${KIPRJMOD}/../../lib/mixtee-footprints.pretty") (options "") (descr ""))
)
""")
    print(f"Footprint lib table written to: {fp_lib_path}")

    # Summary
    comp_count = len(PLACEMENTS)
    net_count = len(NETS) - 1
    print(f"\nBoard: {BOARD_W} x {BOARD_H} mm, 2-layer")
    print(f"Components: {comp_count}")
    print(f"Nets: {net_count} named ({net_count + 1} including unconnected)")
    print(f"\nOpen mixtee-io-board.kicad_pcb in KiCad to view.")
