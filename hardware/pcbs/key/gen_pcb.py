"""
MIXTEE Key PCB - KiCad PCB Generator

Board: 72 x 72 mm, 2-layer
Instances: 1 (one unique Key PCB in system)

Components (68 total):
  - 16x Kailh CHOC hotswap sockets (CPG135001S30) — SW1..SW16
  - 16x WS2812B-2020 NeoPixels — LED1..LED16
  - 16x 100nF decoupling caps (0603) for NeoPixels — C1..C16
  - 16x 1N4148 diodes (SOD-123) anti-ghosting — D1..D16
  -  1x MCP23017 I2C GPIO expander (SOIC-28) — U1
  -  1x 100nF decoupling cap for MCP23017 — C17
  -  1x 6-pin JST-PH connector (B6B-PH-K-S) — J1

Key matrix: 4x4 via MCP23017
  - Port A (GPA0-3) = columns, inputs with internal pull-ups
  - Port B (GPB0-3) = rows, active-low scan outputs
  - 1N4148 diodes: cathode toward row (prevents ghosting)

NeoPixel chain: serpentine order for shortest routing
  LED1->LED2->LED3->LED4->LED8->LED7->LED6->LED5->
  LED9->LED10->LED11->LED12->LED16->LED15->LED14->LED13

JST-PH 6-pin connector to main board:
  Pin 1: NeoPixel DIN   (Teensy pin 6)
  Pin 2: I2C SDA         (Teensy pin 18)
  Pin 3: I2C SCL         (Teensy pin 19)
  Pin 4: MCP23017 INT    (Teensy pin 22, optional)
  Pin 5: 5V
  Pin 6: GND

Board layout (top view, F.Cu side):

  ┌──────────────────────────────────────────────────────────────────┐
  │  SW1(9,9)    SW2(27,9)    SW3(45,9)    SW4(63,9)              │ y=0
  │                                                                │
  │  SW5(9,27)   SW6(27,27)   SW7(45,27)   SW8(63,27)            │
  │                                                                │
  │  SW9(9,45)   SW10(27,45)  SW11(45,45)  SW12(63,45)           │
  │                                                                │
  │  SW13(9,63)  SW14(27,63)  SW15(45,63)  SW16(63,63)           │
  │                         [U1 on B.Cu center]  [J1]             │ y=72
  └──────────────────────────────────────────────────────────────────┘
  x=0                                                          x=72
"""

import uuid
import math
import os


# ---------------------------------------------------------------------------
# Board parameters
# ---------------------------------------------------------------------------

BOARD_W = 72.0   # mm
BOARD_H = 80.0   # mm (extra 8mm for MCP23017 + connector strip)
CORNER_R = 1.0   # mm, corner radius

# Switch grid: 4x4, 18mm pitch, centered on board
GRID_COLS = 4
GRID_ROWS = 4
PITCH = 18.0
GRID_ORIGIN_X = 9.0   # (72 - 3*18) / 2
GRID_ORIGIN_Y = 9.0

# NeoPixel chain order (serpentine): switch indices 1-16
# Row 0 L->R, Row 1 R->L, Row 2 L->R, Row 3 R->L
CHAIN_ORDER = [1, 2, 3, 4, 8, 7, 6, 5, 9, 10, 11, 12, 16, 15, 14, 13]

# Component offsets from switch center (x, y)
LED_OFFSET = (0.0, 3.5)       # NeoPixel below switch center, within cell
CAP_OFFSET = (-3.0, 3.5)      # Cap left of NeoPixel
DIODE_OFFSET = (7.0, -1.0)    # Diode right of switch

# MCP23017 placement (bottom strip, rotated 90° so pins along X)
MCP_X = 36.0
MCP_Y = 73.0
MCP_ROTATION = 90   # pins along X axis

# MCP23017 decoupling cap
MCP_CAP_X = 28.0
MCP_CAP_Y = 73.0   # left of MCP

# JST-PH connector (bottom strip, left of MCP)
CONN_X = 5.0
CONN_Y = 75.0
CONN_ROTATION = 0

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

def build_nets():
    """Build the complete net dictionary {code: name}."""
    nets = {0: ""}  # unconnected
    nets[1] = "GND"
    nets[2] = "5V"
    nets[3] = "SDA"
    nets[4] = "SCL"
    nets[5] = "INT"
    nets[6] = "NEO_DIN"
    # Inter-LED chain nets: NEO_D0..NEO_D14
    for i in range(15):
        nets[7 + i] = f"NEO_D{i}"
    # Column nets: COL0..COL3
    for i in range(4):
        nets[22 + i] = f"COL{i}"
    # Row nets: ROW0..ROW3
    for i in range(4):
        nets[26 + i] = f"ROW{i}"
    # Switch-to-diode junction nets: SW1_D..SW16_D
    for i in range(16):
        nets[30 + i] = f"SW{i+1}_D"
    return nets

NETS = build_nets()


# ---------------------------------------------------------------------------
# Component-to-net mapping
# ---------------------------------------------------------------------------

def build_comp_nets():
    """Build {ref: {pad: net_code}} for all components."""
    cn = {}

    for n in range(1, 17):
        row = (n - 1) // GRID_COLS
        col = (n - 1) % GRID_COLS

        # Switch SWn: pad 1 = column, pad 2 = switch-diode junction
        cn[f"SW{n}"] = {
            "1": 22 + col,      # COL{col}
            "2": 30 + (n - 1),  # SW{n}_D
        }

        # Diode Dn: pad 1 (K) = row, pad 2 (A) = switch-diode junction
        cn[f"D{n}"] = {
            "1": 26 + row,      # ROW{row}
            "2": 30 + (n - 1),  # SW{n}_D
        }

        # Decoupling cap Cn: pad 1 = 5V, pad 2 = GND
        cn[f"C{n}"] = {"1": 2, "2": 1}

    # NeoPixels: chain order determines DIN/DOUT nets
    for p, sw_idx in enumerate(CHAIN_ORDER):
        din_net = 6 + p           # p=0 -> NEO_DIN(6), p=1 -> NEO_D0(7), etc.
        dout_net = 7 + p if p < 15 else 0  # last LED DOUT unconnected
        cn[f"LED{sw_idx}"] = {
            "1": dout_net,  # Pin 1 = DOUT
            "2": 1,         # Pin 2 = GND
            "3": 2,         # Pin 3 = VDD
            "4": din_net,   # Pin 4 = DIN
        }

    # MCP23017 U1 (SOIC-28)
    cn["U1"] = {
        "1": 26,   # GPB0 -> ROW0
        "2": 27,   # GPB1 -> ROW1
        "3": 28,   # GPB2 -> ROW2
        "4": 29,   # GPB3 -> ROW3
        "5": 0,    # GPB4 NC
        "6": 0,    # GPB5 NC
        "7": 0,    # GPB6 NC
        "8": 0,    # GPB7 NC
        "9": 2,    # VDD -> 5V
        "10": 1,   # VSS -> GND
        "11": 0,   # NC (CS for SPI mode)
        "12": 4,   # SCL
        "13": 3,   # SDA
        "14": 0,   # NC
        "15": 1,   # A0 -> GND (addr 0x20)
        "16": 1,   # A1 -> GND
        "17": 1,   # A2 -> GND
        "18": 2,   # ~RESET -> 5V (not reset)
        "19": 0,   # INTB NC
        "20": 5,   # INTA -> INT
        "21": 22,  # GPA0 -> COL0
        "22": 23,  # GPA1 -> COL1
        "23": 24,  # GPA2 -> COL2
        "24": 25,  # GPA3 -> COL3
        "25": 0,   # GPA4 NC
        "26": 0,   # GPA5 NC
        "27": 0,   # GPA6 NC
        "28": 0,   # GPA7 NC
    }

    # MCP23017 decoupling cap C17
    cn["C17"] = {"1": 2, "2": 1}

    # JST-PH 6-pin connector J1
    cn["J1"] = {
        "1": 6,   # NEO_DIN
        "2": 3,   # SDA
        "3": 4,   # SCL
        "4": 5,   # INT
        "5": 2,   # 5V
        "6": 1,   # GND
    }

    return cn

COMP_NETS = build_comp_nets()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def gen_uuid():
    return str(uuid.uuid4())


def switch_xy(n):
    """Board (x, y) for switch n (1-indexed) center."""
    row = (n - 1) // GRID_COLS
    col = (n - 1) % GRID_COLS
    return GRID_ORIGIN_X + col * PITCH, GRID_ORIGIN_Y + row * PITCH


def arc_points(cx, cy, r, start_deg, end_deg, steps=8):
    points = []
    for i in range(steps + 1):
        angle = math.radians(start_deg + (end_deg - start_deg) * i / steps)
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    return points


# ---------------------------------------------------------------------------
# Board outline
# ---------------------------------------------------------------------------

def board_outline():
    """Generate board outline with rounded corners."""
    r = CORNER_R
    w, h = BOARD_W, BOARD_H
    lines = []

    # Straight edges
    edges = [
        (r, 0, w - r, 0),       # top
        (w, r, w, h - r),       # right
        (w - r, h, r, h),       # bottom
        (0, h - r, 0, r),       # left
    ]
    for x1, y1, x2, y2 in edges:
        lines.append(
            f'  (gr_line (start {x1} {y1}) (end {x2} {y2}) '
            f'(layer "{EDGE_CUTS}") (stroke (width 0.05) (type solid)) '
            f'(uuid "{gen_uuid()}"))'
        )

    # Corner arcs
    corners = [
        (r, r, 180, 270),           # top-left
        (w - r, r, 270, 360),       # top-right
        (w - r, h - r, 0, 90),      # bottom-right
        (r, h - r, 90, 180),        # bottom-left
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
# Footprint generators
# ---------------------------------------------------------------------------

def fp_choc_hotswap(ref, x, y, rotation, nets):
    """Kailh CHOC V1 hotswap socket (CPG135001S30).

    Pads (from switch center, default orientation):
      Pad 1: (0, -5.9mm)  — SMD 2.55x2.5mm
      Pad 2: (5.0, -3.8mm) — SMD 2.55x2.5mm
    Mounting holes (NPTH):
      Center: (0, 0) 3.2mm
      Sides: (-5.22, 0), (5.22, 0) 1.7mm
    """
    pad_lines = []
    pads = {"1": (0.0, -5.9), "2": (5.0, -3.8)}
    for name, (px, py) in pads.items():
        net_code = nets.get(name, 0)
        net_name = NETS.get(net_code, "")
        pad_lines.append(
            f'    (pad "{name}" smd roundrect (at {px} {py}) (size 2.55 2.5) '
            f'(layers "{F_CU}" "{F_MASK}") (roundrect_rratio 0.15) '
            f'(net {net_code} "{net_name}") (uuid "{gen_uuid()}"))'
        )

    # NPTH mounting holes omitted for routing — add back for manufacturing

    return f"""  (footprint "mixtee-footprints:Kailh_Choc_V1_Hotswap"
    (layer "{F_CU}")
    (uuid "{gen_uuid()}")
    (at {x} {y} {rotation})
    (property "Reference" "{ref}" (at 0 -8.5 {rotation}) (layer "{F_SILK}") (uuid "{gen_uuid()}") (effects (font (size 0.8 0.8) (thickness 0.12))))
    (property "Value" "CPG135001S30" (at 0 3 {rotation}) (layer "{F_FAB}") (uuid "{gen_uuid()}") (effects (font (size 0.8 0.8) (thickness 0.12))))
    (property "Footprint" "mixtee-footprints:Kailh_Choc_V1_Hotswap" (at 0 0 {rotation}) (layer "{F_FAB}") (uuid "{gen_uuid()}") (effects (font (size 1 1) (thickness 0.15)) hide))
{chr(10).join(pad_lines)}
  )"""


def fp_ws2812b_2020(ref, x, y, rotation, nets):
    """WS2812B-2020 NeoPixel LED (2x2mm).

    Pin layout (top view):
      Pin 1 (DOUT) — top-left    (-0.65, -0.475)
      Pin 2 (GND)  — bottom-left (-0.65,  0.475)
      Pin 3 (VDD)  — bottom-right (0.65,  0.475)
      Pin 4 (DIN)  — top-right    (0.65, -0.475)
    """
    pads = {
        "1": (-0.65, -0.475),   # DOUT
        "2": (-0.65,  0.475),   # GND
        "3": ( 0.65,  0.475),   # VDD
        "4": ( 0.65, -0.475),   # DIN
    }
    pad_lines = []
    for name, (px, py) in pads.items():
        net_code = nets.get(name, 0)
        net_name = NETS.get(net_code, "")
        pad_lines.append(
            f'    (pad "{name}" smd rect (at {px} {py}) (size 0.5 0.55) '
            f'(layers "{F_CU}" "{F_MASK}") '
            f'(net {net_code} "{net_name}") (uuid "{gen_uuid()}"))'
        )

    return f"""  (footprint "LED_SMD:WS2812B-2020"
    (layer "{F_CU}")
    (uuid "{gen_uuid()}")
    (at {x} {y} {rotation})
    (property "Reference" "{ref}" (at 0 -1.5 {rotation}) (layer "{F_SILK}") (uuid "{gen_uuid()}") (effects (font (size 0.6 0.6) (thickness 0.1))))
    (property "Value" "WS2812B-2020" (at 0 1.5 {rotation}) (layer "{F_FAB}") (uuid "{gen_uuid()}") (effects (font (size 0.6 0.6) (thickness 0.1))))
    (property "Footprint" "LED_SMD:WS2812B-2020" (at 0 0 {rotation}) (layer "{F_FAB}") (uuid "{gen_uuid()}") (effects (font (size 1 1) (thickness 0.15)) hide))
{chr(10).join(pad_lines)}
    (fp_line (start -1.1 -1.1) (end 1.1 -1.1) (stroke (width 0.12) (type solid)) (layer "{F_SILK}") (uuid "{gen_uuid()}"))
    (fp_line (start 1.1 -1.1) (end 1.1 1.1) (stroke (width 0.12) (type solid)) (layer "{F_SILK}") (uuid "{gen_uuid()}"))
    (fp_line (start 1.1 1.1) (end -1.1 1.1) (stroke (width 0.12) (type solid)) (layer "{F_SILK}") (uuid "{gen_uuid()}"))
    (fp_line (start -1.1 1.1) (end -1.1 -1.1) (stroke (width 0.12) (type solid)) (layer "{F_SILK}") (uuid "{gen_uuid()}"))
  )"""


def fp_sod123(ref, x, y, rotation, nets):
    """1N4148 diode in SOD-123 package.
    Pad 1 = Cathode (-1.1, 0), Pad 2 = Anode (1.1, 0)."""
    net1 = nets.get("1", 0)
    net2 = nets.get("2", 0)
    return f"""  (footprint "Diode_SMD:D_SOD-123"
    (layer "{F_CU}")
    (uuid "{gen_uuid()}")
    (at {x} {y} {rotation})
    (property "Reference" "{ref}" (at 0 -1.5 {rotation}) (layer "{F_SILK}") (uuid "{gen_uuid()}") (effects (font (size 0.6 0.6) (thickness 0.1))))
    (property "Value" "1N4148" (at 0 1.5 {rotation}) (layer "{F_FAB}") (uuid "{gen_uuid()}") (effects (font (size 0.6 0.6) (thickness 0.1))))
    (property "Footprint" "Diode_SMD:D_SOD-123" (at 0 0 {rotation}) (layer "{F_FAB}") (uuid "{gen_uuid()}") (effects (font (size 1 1) (thickness 0.15)) hide))
    (pad "1" smd roundrect (at -1.1 0 {rotation}) (size 1.0 0.7) (layers "{F_CU}" "{F_MASK}") (roundrect_rratio 0.25) (net {net1} "{NETS.get(net1, '')}") (uuid "{gen_uuid()}"))
    (pad "2" smd roundrect (at 1.1 0 {rotation}) (size 1.0 0.7) (layers "{F_CU}" "{F_MASK}") (roundrect_rratio 0.25) (net {net2} "{NETS.get(net2, '')}") (uuid "{gen_uuid()}"))
    (fp_line (start -1.8 -0.6) (end 1.8 -0.6) (stroke (width 0.12) (type solid)) (layer "{F_SILK}") (uuid "{gen_uuid()}"))
    (fp_line (start -1.8 0.6) (end 1.8 0.6) (stroke (width 0.12) (type solid)) (layer "{F_SILK}") (uuid "{gen_uuid()}"))
    (fp_line (start -1.8 -0.6) (end -1.8 0.6) (stroke (width 0.12) (type solid)) (layer "{F_SILK}") (uuid "{gen_uuid()}"))
  )"""


def fp_c0603(ref, x, y, rotation, nets, layer=None):
    """0603 capacitor. Pads at (-0.8, 0) and (0.8, 0), size 0.9x1.0."""
    if layer is None:
        layer = F_CU
    mask = F_MASK if layer == F_CU else B_MASK
    silk = F_SILK if layer == F_CU else B_SILK
    net1 = nets.get("1", 0)
    net2 = nets.get("2", 0)
    return f"""  (footprint "Capacitor_SMD:C_0603_1608Metric"
    (layer "{layer}")
    (uuid "{gen_uuid()}")
    (at {x} {y} {rotation})
    (property "Reference" "{ref}" (at 0 -1.3 {rotation}) (layer "{silk}") (uuid "{gen_uuid()}") (effects (font (size 0.6 0.6) (thickness 0.1))))
    (property "Value" "100nF" (at 0 1.3 {rotation}) (layer "{F_FAB}") (uuid "{gen_uuid()}") (effects (font (size 0.6 0.6) (thickness 0.1))))
    (property "Footprint" "Capacitor_SMD:C_0603_1608Metric" (at 0 0 {rotation}) (layer "{F_FAB}") (uuid "{gen_uuid()}") (effects (font (size 1 1) (thickness 0.15)) hide))
    (pad "1" smd roundrect (at -0.8 0 {rotation}) (size 0.9 1.0) (layers "{layer}" "{mask}") (roundrect_rratio 0.25) (net {net1} "{NETS.get(net1, '')}") (uuid "{gen_uuid()}"))
    (pad "2" smd roundrect (at 0.8 0 {rotation}) (size 0.9 1.0) (layers "{layer}" "{mask}") (roundrect_rratio 0.25) (net {net2} "{NETS.get(net2, '')}") (uuid "{gen_uuid()}"))
  )"""


def fp_mcp23017(ref, x, y, rotation, nets):
    """MCP23017 SOIC-28 (MCP23017-E/SO).

    28 pins, 14 per side, 1.27mm pitch.
    Pad center-to-center across: 8.89mm (±4.445 from center).
    Pad size: 1.55mm (length, perpendicular to row) x 0.6mm (width, along row).
    Pins 1-14 on left, 15-28 on right (counter-clockwise).

    NOTE: KiCad .kicad_pcb (size sx sy) is in BOARD coordinates — it does NOT
    rotate with the footprint.  When the footprint is placed at 90°, we must
    swap the pad dimensions so that the 0.6mm (along-row) dimension aligns
    with the board axis carrying the 1.27mm pin pitch.
    """
    pad_lines = []
    half_span = 13 * 1.27 / 2  # 8.255mm from first to last pin

    # Pad size in footprint's unrotated frame: (1.55, 0.6)
    # Swap for 90°/270° rotation so the narrow dimension stays along pin pitch
    pad_length = 1.55  # perpendicular to pin row
    pad_width = 0.6    # along pin row (must be < 1.27mm pitch)
    if rotation in (90, 270):
        pad_sx, pad_sy = pad_width, pad_length   # (0.6, 1.55) on board
    else:
        pad_sx, pad_sy = pad_length, pad_width    # (1.55, 0.6) on board

    for pin in range(1, 29):
        if pin <= 14:
            # Left column, top to bottom
            px = -4.445
            py = -half_span + (pin - 1) * 1.27
        else:
            # Right column, bottom to top
            px = 4.445
            py = half_span - (pin - 15) * 1.27
        net_code = nets.get(str(pin), 0)
        net_name = NETS.get(net_code, "")
        pad_lines.append(
            f'    (pad "{pin}" smd roundrect (at {px:.3f} {py:.3f}) (size {pad_sx} {pad_sy}) '
            f'(layers "{F_CU}" "{F_MASK}") (roundrect_rratio 0.25) '
            f'(net {net_code} "{net_name}") (uuid "{gen_uuid()}"))'
        )

    body_half_w = 3.75
    body_half_h = half_span + 0.5

    return f"""  (footprint "Package_SO:SOIC-28W_7.5x17.9mm_P1.27mm"
    (layer "{F_CU}")
    (uuid "{gen_uuid()}")
    (at {x} {y} {rotation})
    (property "Reference" "{ref}" (at 0 {-body_half_h - 1.5} {rotation}) (layer "{F_SILK}") (uuid "{gen_uuid()}") (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "MCP23017" (at 0 {body_half_h + 1.5} {rotation}) (layer "{F_FAB}") (uuid "{gen_uuid()}") (effects (font (size 1 1) (thickness 0.15))))
    (property "Footprint" "Package_SO:SOIC-28W_7.5x17.9mm_P1.27mm" (at 0 0 {rotation}) (layer "{F_FAB}") (uuid "{gen_uuid()}") (effects (font (size 1 1) (thickness 0.15)) hide))
{chr(10).join(pad_lines)}
    (fp_line (start {-body_half_w} {-body_half_h}) (end {body_half_w} {-body_half_h}) (stroke (width 0.15) (type solid)) (layer "{F_SILK}") (uuid "{gen_uuid()}"))
    (fp_line (start {body_half_w} {-body_half_h}) (end {body_half_w} {body_half_h}) (stroke (width 0.15) (type solid)) (layer "{F_SILK}") (uuid "{gen_uuid()}"))
    (fp_line (start {body_half_w} {body_half_h}) (end {-body_half_w} {body_half_h}) (stroke (width 0.15) (type solid)) (layer "{F_SILK}") (uuid "{gen_uuid()}"))
    (fp_line (start {-body_half_w} {body_half_h}) (end {-body_half_w} {-body_half_h}) (stroke (width 0.15) (type solid)) (layer "{F_SILK}") (uuid "{gen_uuid()}"))
  )"""


def fp_jst_ph_6(ref, x, y, rotation, nets):
    """JST-PH B6B-PH-K 6-pin vertical through-hole connector.
    Pins at 2mm pitch, pin 1 at origin, pins going in +X."""
    pad_lines = []
    for i in range(6):
        pin = str(i + 1)
        net_code = nets.get(pin, 0)
        net_name = NETS.get(net_code, "")
        pad_lines.append(
            f'    (pad "{pin}" thru_hole circle (at {i * 2.0} 0) (size 1.75 1.75) '
            f'(drill 0.8) (layers "*.Cu" "*.Mask") '
            f'(net {net_code} "{net_name}") (uuid "{gen_uuid()}"))'
        )
    return f"""  (footprint "Connector_JST:JST_PH_B6B-PH-K_1x06_P2.00mm_Vertical"
    (layer "{F_CU}")
    (uuid "{gen_uuid()}")
    (at {x} {y} {rotation})
    (property "Reference" "{ref}" (at 5 -2.5 {rotation}) (layer "{F_SILK}") (uuid "{gen_uuid()}") (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "B6B-PH-K-S" (at 5 3 {rotation}) (layer "{F_FAB}") (uuid "{gen_uuid()}") (effects (font (size 1 1) (thickness 0.15))))
    (property "Footprint" "Connector_JST:JST_PH_B6B-PH-K_1x06_P2.00mm_Vertical" (at 0 0 {rotation}) (layer "{F_FAB}") (uuid "{gen_uuid()}") (effects (font (size 1 1) (thickness 0.15)) hide))
{chr(10).join(pad_lines)}
    (fp_line (start -1.25 -1.6) (end 11.25 -1.6) (stroke (width 0.12) (type solid)) (layer "{F_SILK}") (uuid "{gen_uuid()}"))
    (fp_line (start 11.25 -1.6) (end 11.25 4.4) (stroke (width 0.12) (type solid)) (layer "{F_SILK}") (uuid "{gen_uuid()}"))
    (fp_line (start 11.25 4.4) (end -1.25 4.4) (stroke (width 0.12) (type solid)) (layer "{F_SILK}") (uuid "{gen_uuid()}"))
    (fp_line (start -1.25 4.4) (end -1.25 -1.6) (stroke (width 0.12) (type solid)) (layer "{F_SILK}") (uuid "{gen_uuid()}"))
  )"""


# ---------------------------------------------------------------------------
# PCB assembly
# ---------------------------------------------------------------------------

def generate_pcb():
    """Generate the complete .kicad_pcb file."""

    # Net declarations
    net_decls = "\n".join(
        f'  (net {code} "{name}")' for code, name in sorted(NETS.items())
    )

    # Board outline
    outline = board_outline()

    # Component placements
    footprints = []

    # --- 16x CHOC hotswap sockets ---
    for n in range(1, 17):
        sx, sy = switch_xy(n)
        footprints.append(
            fp_choc_hotswap(f"SW{n}", sx, sy, 0, COMP_NETS[f"SW{n}"])
        )

    # --- 16x WS2812B-2020 NeoPixels ---
    for n in range(1, 17):
        sx, sy = switch_xy(n)
        lx = sx + LED_OFFSET[0]
        ly = sy + LED_OFFSET[1]
        footprints.append(
            fp_ws2812b_2020(f"LED{n}", lx, ly, 0, COMP_NETS[f"LED{n}"])
        )

    # --- 16x NeoPixel decoupling caps ---
    for n in range(1, 17):
        sx, sy = switch_xy(n)
        cx = sx + CAP_OFFSET[0]
        cy = sy + CAP_OFFSET[1]
        footprints.append(
            fp_c0603(f"C{n}", cx, cy, 0, COMP_NETS[f"C{n}"])
        )

    # --- 16x anti-ghosting diodes ---
    for n in range(1, 17):
        sx, sy = switch_xy(n)
        dx = sx + DIODE_OFFSET[0]
        dy = sy + DIODE_OFFSET[1]
        # Rotate 90° for col 3 (rightmost) to avoid board edge
        col = (n - 1) % GRID_COLS
        rot = 90 if col == 3 else 0
        # Adjust position for rotated diodes
        if col == 3:
            dx = sx + 5.0
            dy = sy + 2.0
        footprints.append(
            fp_sod123(f"D{n}", dx, dy, rot, COMP_NETS[f"D{n}"])
        )

    # --- MCP23017 (on B.Cu) ---
    footprints.append(
        fp_mcp23017("U1", MCP_X, MCP_Y, MCP_ROTATION, COMP_NETS["U1"])
    )

    # --- MCP23017 decoupling cap (near U1 on F.Cu) ---
    footprints.append(
        fp_c0603("C17", MCP_CAP_X, MCP_CAP_Y, 0, COMP_NETS["C17"])
    )

    # --- JST-PH 6-pin connector ---
    footprints.append(
        fp_jst_ph_6("J1", CONN_X, CONN_Y, CONN_ROTATION, COMP_NETS["J1"])
    )

    all_footprints = "\n\n".join(footprints)

    # GND zone on back copper
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

    # Silkscreen text
    board_text = f"""  (gr_text "MIXTEE Key PCB" (at {BOARD_W/2} {BOARD_H - 2.5}) (layer "{F_SILK}") (uuid "{gen_uuid()}")
    (effects (font (size 1.2 1.2) (thickness 0.15)))
  )"""

    pcb = f"""(kicad_pcb
  (version 20240108)
  (generator "mixtee_gen_key_pcb")
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
    """Generate a minimal .kicad_pro project file."""
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
    "filename": "mixtee-key-pcb.kicad_pro",
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

    # Write PCB file
    pcb_path = os.path.join(out_dir, "mixtee-key-pcb.kicad_pcb")
    with open(pcb_path, "w") as f:
        f.write(generate_pcb())
    print(f"PCB written to: {pcb_path}")

    # Write project file
    pro_path = os.path.join(out_dir, "mixtee-key-pcb.kicad_pro")
    with open(pro_path, "w") as f:
        f.write(generate_project())
    print(f"Project written to: {pro_path}")

    # Write footprint library table
    fp_lib_path = os.path.join(out_dir, "fp-lib-table")
    with open(fp_lib_path, "w") as f:
        f.write("""(fp_lib_table
  (version 7)
  (lib (name "mixtee-footprints") (type "KiCad") (uri "${KIPRJMOD}/../../lib/mixtee-footprints.pretty") (options "") (descr ""))
)
""")
    print(f"Footprint lib table written to: {fp_lib_path}")

    # Summary
    n_sw = 16
    n_led = 16
    n_cap = 17
    n_diode = 16
    n_ic = 1
    n_conn = 1
    total = n_sw + n_led + n_cap + n_diode + n_ic + n_conn
    print(f"\nDone! Open mixtee-key-pcb.kicad_pcb in KiCad to view.")
    print(f"Board dimensions: {BOARD_W} x {BOARD_H} mm")
    print(f"Components: {n_sw} switches + {n_led} LEDs + {n_cap} caps + "
          f"{n_diode} diodes + {n_ic} IC + {n_conn} connector = {total} total")
    print(f"Nets: {len(NETS) - 1} named ({len(NETS)} including unconnected)")
    print(f"NeoPixel chain order (serpentine): {CHAIN_ORDER}")
