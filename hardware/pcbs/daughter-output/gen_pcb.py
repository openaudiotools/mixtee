"""
MIXTEE Daughter/Output Board - KiCad PCB Generator

Reads the SKiDL-generated netlist and produces a .kicad_pcb file with:
  - Board outline (80 x 20 mm, 1 mm corner radius)
  - Component placement
  - Net definitions
  - Design rules per docs/pcb-design-rules.md

Board layout (looking at front copper, top view):
  - Jack barrels point DOWN (toward board edge at y=20)
  - JST-PH connector between J2/J3, near top edge
  - Diodes between jacks and connector
  - Cap near connector

  ┌──────────────────────────────────────────────────────────────────────┐
  │                              J5(JST) C1                            │ y=0
  │        D1    D2    D3    D4                                        │
  │        J1    J2    J3    J4  (jack pads, tip @ y~2.2)             │
  │  ════════════════════════════════════════  jack barrels → panel     │ y=20
  └──────────────────────────────────────────────────────────────────────┘
  x=0                                                              x=80
"""

import uuid
import math
import re


# ---------------------------------------------------------------------------
# Board parameters
# ---------------------------------------------------------------------------

BOARD_W = 80.0  # mm
BOARD_H = 20.0  # mm
CORNER_R = 1.0  # mm, corner radius
EDGE_CLEARANCE = 0.3  # mm, copper to edge

# Jack spacing: 4 jacks evenly across 80mm
# Center-to-center: 20mm, first jack at x=10
JACK_PITCH = 20.0
JACK_X_START = 10.0  # center of first jack from left edge

# Jack Y position: bushing center near board bottom edge
# The bushing extends off the edge; pad positions are 17.78mm and 11.43mm
# behind bushing in the footprint.
# With bushing at y=20 (bottom edge), the Tip pad is at y=20-17.78=2.22
# and Sleeve pad at y=20-11.43=8.57, offset 7.62 in x.
# But wait - with the footprint origin at bushing center, placing the
# footprint at y=20 puts the bushing at the board edge.
# The pads end up INSIDE the board, which is correct.
JACK_Y = 20.0  # bushing center at bottom edge

# JST-PH connector: between J2 and J3, near top edge
# B6B-PH-K-S: 6 pins at 2mm pitch = 10mm span, origin at pin 1
# Place between J2 sleeve (x~37.6) and J3 tip (x=50), above jack pads
CONN_X = 35.0
CONN_Y = 1.5  # near top edge, clear of jack tip pads at y~2.2

# Diode placement: above their respective jack tip pads
DIODE_Y = 5.5  # between connector and jack sleeve pads
DIODE_X_OFFSET = 2.0  # offset from jack center toward sleeve side

# Cap placement: between J1 and J2 in the mid-band, clear of all pads
CAP_X = 25.0
CAP_Y = 4.0

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
# Net definitions (matching the SKiDL netlist)
# ---------------------------------------------------------------------------

NETS = {
    0: "",       # unconnected net
    1: "+5VA",
    2: "AIN1",
    3: "AIN2",
    4: "AIN3",
    5: "AIN4",
    6: "GND",
}

# Component-to-net mapping (derived from netlist)
# Format: {ref: {pad_num: net_code}}
COMP_NETS = {
    "J1": {"T": 2, "S": 6},   # AIN1, GND
    "J2": {"T": 3, "S": 6},   # AIN2, GND
    "J3": {"T": 4, "S": 6},   # AIN3, GND
    "J4": {"T": 5, "S": 6},   # AIN4, GND
    "D1": {"1": 1, "2": 2},   # K=+5VA, A=AIN1
    "D2": {"1": 1, "2": 3},   # K=+5VA, A=AIN2
    "D3": {"1": 1, "2": 4},   # K=+5VA, A=AIN3
    "D4": {"1": 1, "2": 5},   # K=+5VA, A=AIN4
    "C1": {"1": 1, "2": 6},   # +5VA, GND
    "J5": {"1": 2, "2": 3, "3": 4, "4": 5, "5": 1, "6": 6},
}


def gen_uuid():
    return str(uuid.uuid4())


def arc_points(cx, cy, r, start_deg, end_deg, steps=8):
    """Generate arc points for rounded corners."""
    points = []
    for i in range(steps + 1):
        angle = math.radians(start_deg + (end_deg - start_deg) * i / steps)
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    return points


def board_outline_with_corners():
    """Generate board outline as line segments with rounded corners."""
    r = CORNER_R
    w, h = BOARD_W, BOARD_H
    lines = []

    # Top edge (left corner to right corner)
    lines.append(f'  (gr_line (start {r} 0) (end {w-r} 0) (layer "{EDGE_CUTS}") (stroke (width 0.05) (type solid)) (uuid "{gen_uuid()}"))')

    # Right edge
    lines.append(f'  (gr_line (start {w} {r}) (end {w} {h-r}) (layer "{EDGE_CUTS}") (stroke (width 0.05) (type solid)) (uuid "{gen_uuid()}"))')

    # Bottom edge
    lines.append(f'  (gr_line (start {w-r} {h}) (end {r} {h}) (layer "{EDGE_CUTS}") (stroke (width 0.05) (type solid)) (uuid "{gen_uuid()}"))')

    # Left edge
    lines.append(f'  (gr_line (start 0 {h-r}) (end 0 {r}) (layer "{EDGE_CUTS}") (stroke (width 0.05) (type solid)) (uuid "{gen_uuid()}"))')

    # Corner arcs (KiCad arc format: start, mid, end)
    # In KiCad Y-down coordinates with standard cos/sin:
    #   angle 0° = +X (right), 90° = +Y (down), 180° = -X (left), 270° = -Y (up)
    corners = [
        # Top-left: center (r, r), arc from (0, r) to (r, 0)
        # (0,r) is at 180° from center, (r,0) is at 270° from center
        (r, r, 180, 270),
        # Top-right: center (w-r, r), arc from (w-r, 0) to (w, r)
        # (w-r,0) is at 270° from center, (w,r) is at 360° from center
        (w - r, r, 270, 360),
        # Bottom-right: center (w-r, h-r), arc from (w, h-r) to (w-r, h)
        # (w,h-r) is at 0° from center, (w-r,h) is at 90° from center
        (w - r, h - r, 0, 90),
        # Bottom-left: center (r, h-r), arc from (r, h) to (0, h-r)
        # (r,h) is at 90° from center, (0,h-r) is at 180° from center
        (r, h - r, 90, 180),
    ]

    for cx, cy, start, end in corners:
        # Arc start, mid, end points
        # KiCad uses Y-down coordinates; standard trig with Y-down means
        # positive angles go clockwise. Use (cx + r*cos, cy + r*sin) directly
        # since sin/cos naturally handle the Y-down mapping.
        s_angle = math.radians(start)
        m_angle = math.radians((start + end) / 2)
        e_angle = math.radians(end)
        sx, sy = cx + r * math.cos(s_angle), cy + r * math.sin(s_angle)
        mx, my = cx + r * math.cos(m_angle), cy + r * math.sin(m_angle)
        ex, ey = cx + r * math.cos(e_angle), cy + r * math.sin(e_angle)
        lines.append(
            f'  (gr_arc (start {sx:.4f} {sy:.4f}) (mid {mx:.4f} {my:.4f}) '
            f'(end {ex:.4f} {ey:.4f}) (layer "{EDGE_CUTS}") '
            f'(stroke (width 0.05) (type solid)) (uuid "{gen_uuid()}"))'
        )

    return "\n".join(lines)


def footprint_112bpc(ref, x, y, rotation, nets):
    """Generate a Switchcraft 112BPC jack footprint placement.

    Origin at bushing center. Pads:
      T (Tip) at local (17.78, 0)
      S (Sleeve) at local (11.43, 7.62)

    rotation: degrees, clockwise (KiCad PCB convention)
    nets: dict {pad_name: net_code}
    """
    rot_rad = math.radians(rotation)
    cos_r = math.cos(rot_rad)
    sin_r = math.sin(rot_rad)

    def transform(lx, ly):
        # KiCad PCB: clockwise rotation, Y-down
        ax = x + lx * cos_r + ly * sin_r
        ay = y - lx * sin_r + ly * cos_r
        return ax, ay

    # Pad positions in local coords
    pads = {
        "T": (17.78, 0.0),
        "S": (11.43, 7.62),
    }

    pad_lines = []
    for name, (lx, ly) in pads.items():
        net_code = nets.get(name, 0)
        net_name = NETS.get(net_code, "")
        pad_lines.append(
            f'    (pad "{name}" thru_hole circle (at {lx} {ly}) (size 2.4 2.4) '
            f'(drill 1.3) (layers "*.Cu" "*.Mask") '
            f'(net {net_code} "{net_name}") (uuid "{gen_uuid()}"))'
        )

    return f"""  (footprint "mixtee-footprints:Switchcraft_112BPC"
    (layer "{F_CU}")
    (uuid "{gen_uuid()}")
    (at {x} {y} {rotation})
    (property "Reference" "{ref}" (at 0 -8.5 {rotation}) (layer "{F_SILK}") (uuid "{gen_uuid()}") (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "112BPC" (at 0 12.5 {rotation}) (layer "{F_FAB}") (uuid "{gen_uuid()}") (effects (font (size 1 1) (thickness 0.15))))
    (property "Footprint" "mixtee-footprints:Switchcraft_112BPC" (at 0 0 {rotation}) (layer "{F_FAB}") (uuid "{gen_uuid()}") (effects (font (size 1 1) (thickness 0.15)) hide))
{chr(10).join(pad_lines)}
    (fp_line (start -4.0 -6.35) (end 22.0 -6.35) (stroke (width 0.12) (type solid)) (layer "{F_SILK}") (uuid "{gen_uuid()}"))
    (fp_line (start 22.0 -6.35) (end 22.0 10.0) (stroke (width 0.12) (type solid)) (layer "{F_SILK}") (uuid "{gen_uuid()}"))
    (fp_line (start 22.0 10.0) (end -4.0 10.0) (stroke (width 0.12) (type solid)) (layer "{F_SILK}") (uuid "{gen_uuid()}"))
    (fp_line (start -4.0 10.0) (end -4.0 -6.35) (stroke (width 0.12) (type solid)) (layer "{F_SILK}") (uuid "{gen_uuid()}"))
  )"""


def footprint_sod323(ref, x, y, rotation, nets):
    """SOD-323 diode footprint. Pad 1=Cathode, Pad 2=Anode.
    Standard KiCad SOD-323: pads at (-1.1, 0) and (1.1, 0), size 1.0x0.6."""
    net1 = nets.get("1", 0)
    net2 = nets.get("2", 0)
    return f"""  (footprint "Diode_SMD:D_SOD-323"
    (layer "{F_CU}")
    (uuid "{gen_uuid()}")
    (at {x} {y} {rotation})
    (property "Reference" "{ref}" (at 0 -1.5 {rotation}) (layer "{F_SILK}") (uuid "{gen_uuid()}") (effects (font (size 0.8 0.8) (thickness 0.12))))
    (property "Value" "BAT54" (at 0 1.5 {rotation}) (layer "{F_FAB}") (uuid "{gen_uuid()}") (effects (font (size 0.8 0.8) (thickness 0.12))))
    (property "Footprint" "Diode_SMD:D_SOD-323" (at 0 0 {rotation}) (layer "{F_FAB}") (uuid "{gen_uuid()}") (effects (font (size 1 1) (thickness 0.15)) hide))
    (pad "1" smd roundrect (at -1.1 0 {rotation}) (size 1.0 0.6) (layers "{F_CU}" "{F_MASK}") (roundrect_rratio 0.25) (net {net1} "{NETS.get(net1, '')}") (uuid "{gen_uuid()}"))
    (pad "2" smd roundrect (at 1.1 0 {rotation}) (size 1.0 0.6) (layers "{F_CU}" "{F_MASK}") (roundrect_rratio 0.25) (net {net2} "{NETS.get(net2, '')}") (uuid "{gen_uuid()}"))
    (fp_line (start -1.8 -0.6) (end 1.8 -0.6) (stroke (width 0.12) (type solid)) (layer "{F_SILK}") (uuid "{gen_uuid()}"))
    (fp_line (start -1.8 0.6) (end 1.8 0.6) (stroke (width 0.12) (type solid)) (layer "{F_SILK}") (uuid "{gen_uuid()}"))
    (fp_line (start -1.8 -0.6) (end -1.8 0.6) (stroke (width 0.12) (type solid)) (layer "{F_SILK}") (uuid "{gen_uuid()}"))
  )"""


def footprint_c0603(ref, x, y, rotation, nets):
    """0603 capacitor. Pads at (-0.8, 0) and (0.8, 0), size 0.9x1.0."""
    net1 = nets.get("1", 0)
    net2 = nets.get("2", 0)
    return f"""  (footprint "Capacitor_SMD:C_0603_1608Metric"
    (layer "{F_CU}")
    (uuid "{gen_uuid()}")
    (at {x} {y} {rotation})
    (property "Reference" "{ref}" (at 0 -1.5 {rotation}) (layer "{F_SILK}") (uuid "{gen_uuid()}") (effects (font (size 0.8 0.8) (thickness 0.12))))
    (property "Value" "100nF" (at 0 1.5 {rotation}) (layer "{F_FAB}") (uuid "{gen_uuid()}") (effects (font (size 0.8 0.8) (thickness 0.12))))
    (property "Footprint" "Capacitor_SMD:C_0603_1608Metric" (at 0 0 {rotation}) (layer "{F_FAB}") (uuid "{gen_uuid()}") (effects (font (size 1 1) (thickness 0.15)) hide))
    (pad "1" smd roundrect (at -0.8 0 {rotation}) (size 0.9 1.0) (layers "{F_CU}" "{F_MASK}") (roundrect_rratio 0.25) (net {net1} "{NETS.get(net1, '')}") (uuid "{gen_uuid()}"))
    (pad "2" smd roundrect (at 0.8 0 {rotation}) (size 0.9 1.0) (layers "{F_CU}" "{F_MASK}") (roundrect_rratio 0.25) (net {net2} "{NETS.get(net2, '')}") (uuid "{gen_uuid()}"))
  )"""


def footprint_jst_ph_6(ref, x, y, rotation, nets):
    """JST-PH B6B-PH-K 6-pin vertical through-hole connector.
    Pins at 2mm pitch, pin 1 at origin, pins going in +X."""
    pad_lines = []
    for i in range(6):
        pin_num = str(i + 1)
        net_code = nets.get(pin_num, 0)
        net_name = NETS.get(net_code, "")
        pad_lines.append(
            f'    (pad "{pin_num}" thru_hole circle (at {i*2.0} 0) (size 1.75 1.75) '
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


def generate_pcb():
    """Generate the complete .kicad_pcb file."""

    # Net declarations
    net_decls = "\n".join(
        f'  (net {code} "{name}")' for code, name in sorted(NETS.items())
    )

    # Board outline
    outline = board_outline_with_corners()

    # Component placements
    footprints = []

    # 4x TS Jacks - spaced along bottom edge
    # Jack footprint: origin at bushing center, barrel goes toward -X in local coords
    # We want barrels pointing DOWN (toward y=20), so rotate 90° (barrel goes +Y)
    # Actually: in the footprint, barrel extends in -X from origin.
    # rotation=90 means -X local maps to +Y global, so barrel goes DOWN. Correct!
    for i in range(4):
        jx = JACK_X_START + i * JACK_PITCH
        jy = JACK_Y
        footprints.append(
            footprint_112bpc(f"J{i+1}", jx, jy, 90, COMP_NETS[f"J{i+1}"])
        )

    # 4x ESD diodes - above their respective jacks
    for i in range(4):
        dx = JACK_X_START + i * JACK_PITCH + DIODE_X_OFFSET
        dy = DIODE_Y
        footprints.append(
            footprint_sod323(f"D{i+1}", dx, dy, 0, COMP_NETS[f"D{i+1}"])
        )

    # 1x 100nF cap - near connector
    footprints.append(
        footprint_c0603("C1", CAP_X, CAP_Y, 0, COMP_NETS["C1"])
    )

    # 1x JST-PH 6-pin connector - at top edge
    footprints.append(
        footprint_jst_ph_6("J5", CONN_X, CONN_Y, 0, COMP_NETS["J5"])
    )

    all_footprints = "\n\n".join(footprints)

    # Ground zone on back copper
    zone_uuid = gen_uuid()
    zone = f"""  (zone
    (net 6)
    (net_name "GND")
    (layer "{B_CU}")
    (uuid "{zone_uuid}")
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
    board_text = f"""  (gr_text "MIXTEE Daughter/Output" (at {BOARD_W/2} {BOARD_H + 2}) (layer "{F_SILK}") (uuid "{gen_uuid()}")
    (effects (font (size 1.5 1.5) (thickness 0.15)))
  )"""

    pcb = f"""(kicad_pcb
  (version 20240108)
  (generator "mixtee_gen_pcb")
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
    "filename": "mixtee-daughter-output.kicad_pro",
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
        "name": "Audio_Analog",
        "clearance": 0.25,
        "track_width": 0.3,
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


if __name__ == "__main__":
    import os

    out_dir = os.path.dirname(os.path.abspath(__file__))

    # Write PCB file
    pcb_path = os.path.join(out_dir, "mixtee-daughter-output.kicad_pcb")
    with open(pcb_path, "w") as f:
        f.write(generate_pcb())
    print(f"PCB written to: {pcb_path}")

    # Write project file
    pro_path = os.path.join(out_dir, "mixtee-daughter-output.kicad_pro")
    with open(pro_path, "w") as f:
        f.write(generate_project())
    print(f"Project written to: {pro_path}")

    # Write footprint library table
    fp_lib_path = os.path.join(out_dir, "fp-lib-table")
    with open(fp_lib_path, "w") as f:
        f.write(f"""(fp_lib_table
  (version 7)
  (lib (name "mixtee-footprints") (type "KiCad") (uri "${{KIPRJMOD}}/../../lib/mixtee-footprints.pretty") (options "") (descr ""))
)
""")
    print(f"Footprint lib table written to: {fp_lib_path}")

    print("\nDone! Open mixtee-daughter-output.kicad_pcb in KiCad to view.")
    print(f"Board dimensions: {BOARD_W} x {BOARD_H} mm")
    print(f"Components placed: 4 jacks, 4 diodes, 1 cap, 1 connector")
