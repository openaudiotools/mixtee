"""
MIXTEE Input Mother Board - KiCad PCB Generator

Board: 80 x 40 mm, 4-layer (F.Cu, In1.Cu=GND, In2.Cu=V33_A, B.Cu)
Instances: 2 (Board 1-bottom: ch 1-8, Board 2-bottom: ch 9-16)
Orientation: Lower board in pair (daughter above), jacks at panel edge (y=40)

Components (71 total):
  Codecs (2):
    U1  AK4619VN (QFN-32, 5x5mm, 0.5mm pitch) — ch 1-4, I2C 0x10
    U2  AK4619VN (QFN-32, 5x5mm, 0.5mm pitch) — ch 5-8, I2C 0x11
  Op-amps (4):
    U4  OPA1678 dual (SOIC-8) — Sallen-Key ch 1,2
    U5  OPA1678 dual (SOIC-8) — Sallen-Key ch 3,4
    U6  OPA1678 dual (SOIC-8) — Sallen-Key ch 5,6
    U7  OPA1678 dual (SOIC-8) — Sallen-Key ch 7,8
  LDO (1):
    U3  ADP7118 (SOIC-8) — 5V -> 3.3V_A
  TS Jacks (4):
    J1-J4  Switchcraft 112BPC — L channels
  Connectors (2):
    J5  FFC 16-pin ZIF 1.0mm (to Main Board)
    J6  JST-PH 6-pin (to Daughter Board)
  ESD diodes (8):
    D1-D8  SOD-323 Schottky clamp
  AC coupling caps (4):
    C1-C4  10uF 0805 (L channel input coupling)
  Filter passives (32):
    R1-R16   1k 0603 (Sallen-Key resistors, 2 per channel)
    C5-C20   3.3nF/6.8nF 0603 (Sallen-Key caps, 2 per channel)
  Codec decoupling (8):
    C21-C24  100nF 0603 (AVDD/TVDD per codec, 2 each)
    C25-C28  2.2uF 0805 (AVDRV/VCOM per codec, 2 each)
  LDO caps (4):
    C29  100nF 0603 (LDO input)
    C30  1uF 0805 (LDO output)
    C31  10uF 0805 (LDO output bulk)
    C32  100nF 0603 (5V_DIG local decoupling)
  Pull-ups (2):
    R17  10k 0603 (U1 PDN pull-up to V33_A)
    R18  10k 0603 (U2 PDN pull-up to V33_A)

Layout (y=0 interior/FFC edge, y=30 panel edge):

  x=0                                                              x=80
  +--------------------------------------------------------------------+
  | U3(LDO,5,4)  J5(FFC-16,25,2)              J6(JST-PH-6,62,2)      | y=0
  | C29 C30 C31  C32                                                   |
  |    U1(AK4619,18,10)              U2(AK4619,58,10)                 |
  |  C21 C22 C25 C26              C23 C24 C27 C28                     |
  |                                                                    |
  |  U4(16,18) U5(26,18)          U6(56,18) U7(66,18)                | y~18
  |  R1-R4 C5-C8                  R9-R12 C13-C16                      |
  |  R5-R8 C9-C12                 R13-R16 C17-C20                     |
  |  D1-D4  C1-C4                 D5-D8                                |
  |  J1(10,30) J2(30,30)          J3(50,30) J4(70,30)                | y=30
  +--------------------------------------------------------------------+
"""

import uuid
import math
import os


# ---------------------------------------------------------------------------
# Board parameters
# ---------------------------------------------------------------------------

BOARD_W = 80.0   # mm
BOARD_H = 40.0   # mm  (increased from 30 to clear jack pads from filter zone)
CORNER_R = 1.0   # mm

# Layers
F_CU = "F.Cu"
IN1_CU = "In1.Cu"
IN2_CU = "In2.Cu"
B_CU = "B.Cu"
F_SILK = "F.SilkS"
B_SILK = "B.SilkS"
F_MASK = "F.Mask"
B_MASK = "B.Mask"
F_PASTE = "F.Paste"
F_FAB = "F.Fab"
F_CRTYD = "F.CrtYd"
EDGE_CUTS = "Edge.Cuts"


# ---------------------------------------------------------------------------
# Net definitions
# ---------------------------------------------------------------------------

NETS = {
    0: "",
    # Power
    1: "GND",
    2: "5V_A",
    3: "V33_A",
    4: "5V_DIG",
    # TDM bus (shared by both codecs on this board)
    5: "MCLK",
    6: "BCLK",
    7: "LRCLK",
    8: "SDIN1",         # Teensy -> both codecs
    9: "SDOUT1",        # U1 -> Teensy (FFC pin 4)
    10: "SDOUT2",       # U2 -> Teensy (FFC pin 13)
    # I2C
    11: "SDA",
    12: "SCL",
    # Codec internal rails
    13: "U1_AVDRV",     # U1 internal LDO output
    14: "U1_VCOM",      # U1 AVDD/2 reference
    15: "U2_AVDRV",     # U2 internal LDO output
    16: "U2_VCOM",      # U2 AVDD/2 reference
    # Audio input nets (from jacks, after AC coupling)
    17: "AIN_1_AC",     # Ch 1 after AC coupling cap
    18: "AIN_2_AC",     # Ch 2
    19: "AIN_3_AC",     # Ch 3
    20: "AIN_4_AC",     # Ch 4
    21: "AIN_5_AC",     # Ch 5
    22: "AIN_6_AC",     # Ch 6
    23: "AIN_7_AC",     # Ch 7
    24: "AIN_8_AC",     # Ch 8
    # Raw jack tip nets (before AC coupling)
    25: "JACK_1",
    26: "JACK_2",
    27: "JACK_3",
    28: "JACK_4",
    # Filter node 1 (between R1 and R2 in Sallen-Key)
    29: "FN1_1",
    30: "FN1_2",
    31: "FN1_3",
    32: "FN1_4",
    33: "FN1_5",
    34: "FN1_6",
    35: "FN1_7",
    36: "FN1_8",
    # Filter node 2 (op-amp output = filter output -> codec ADC)
    37: "FOUT_1",
    38: "FOUT_2",
    39: "FOUT_3",
    40: "FOUT_4",
    41: "FOUT_5",
    42: "FOUT_6",
    43: "FOUT_7",
    44: "FOUT_8",
    # Op-amp power
    45: "VOPA",         # 5V_A to op-amp VCC (same as 5V_A but separate for clarity)
    # Daughter board signals (via JST-PH-6)
    # R channels come from Daughter Board: pins 1-4 are AIN for R channels
    46: "DAIN_R1",      # Daughter board ch R1 (e.g. ch 2)
    47: "DAIN_R2",      # Daughter board ch R2 (e.g. ch 4)
    48: "DAIN_R3",      # Daughter board ch R3 (e.g. ch 6)
    49: "DAIN_R4",      # Daughter board ch R4 (e.g. ch 8)
    # Filter nodes for R channels (from daughter board, through filter)
    50: "FN1_R1",
    51: "FN1_R2",
    52: "FN1_R3",
    53: "FN1_R4",
    54: "FOUT_R1",
    55: "FOUT_R2",
    56: "FOUT_R3",
    57: "FOUT_R4",
}

# Alias: op-amp VCC is just 5V_A
# We'll use net 2 (5V_A) directly for op-amp power pins


# ---------------------------------------------------------------------------
# Component-to-net mapping
# ---------------------------------------------------------------------------

def build_comp_nets():
    cn = {}

    # ── U1: AK4619VN codec (QFN-32), I2C addr 0x10 (CAD=low) ──
    # Channels: ADC2L=ch1, ADC2R=ch2, ADC1L=ch3, ADC1R=ch4
    # Pin mapping from ak4619-wiring.md:
    #   Pin 1: SDIN1, Pin 2: SDIN2, Pin 3: TVDD, Pin 4: VSS2
    #   Pin 5: AVDRV, Pin 6: LRCK, Pin 7: BICK, Pin 8: MCLK
    #   Pin 9: AIN5R(open), Pin 10: AIN4R(ch2), Pin 11: AIN5L(open), Pin 12: AIN4L(ch1)
    #   Pin 13: AIN2R(open), Pin 14: AIN1R(ch4), Pin 15: AIN2L(open), Pin 16: AIN1L(ch3)
    #   Pin 17: VCOM, Pin 18: AVDD, Pin 19: VSS1, Pin 20: VREFL
    #   Pin 21: VREFH, Pin 22: AOUT1L, Pin 23: AOUT1R, Pin 24: AOUT2L
    #   Pin 25: AOUT2R, Pin 26: PDN, Pin 27: CAD, Pin 28: SCL
    #   Pin 29: SI, Pin 30: SDA, Pin 31: SDOUT1, Pin 32: SDOUT2
    #   Pin 33: EP (exposed pad)
    cn["U1"] = {
        "1": 8,       # SDIN1 -> TDM data in
        "2": 1,       # SDIN2 -> VSS2 (unused in TDM)
        "3": 3,       # TVDD -> V33_A
        "4": 1,       # VSS2 -> GND
        "5": 13,      # AVDRV -> U1_AVDRV (internal LDO out)
        "6": 7,       # LRCK -> LRCLK
        "7": 6,       # BICK -> BCLK
        "8": 5,       # MCLK
        "9": 0,       # AIN5R -> open
        "10": 54,     # AIN4R -> FOUT_R1 (ch 2 R from daughter, filtered)
        "11": 0,      # AIN5L -> open
        "12": 37,     # AIN4L -> FOUT_1 (ch 1 filtered)
        "13": 0,      # AIN2R -> open
        "14": 57,     # AIN1R -> FOUT_R2 (ch 4 R from daughter, filtered)
        "15": 0,      # AIN2L -> open
        "16": 39,     # AIN1L -> FOUT_3 (ch 3 filtered, note: pin16=ADC1L=ch3 per wiring doc)
        "17": 14,     # VCOM -> U1_VCOM
        "18": 3,      # AVDD -> V33_A
        "19": 1,      # VSS1 -> GND
        "20": 1,      # VREFL -> VSS1 = GND
        "21": 3,      # VREFH -> AVDD = V33_A
        "22": 0,      # AOUT1L -> open (Phase 2)
        "23": 0,      # AOUT1R -> open (Phase 2)
        "24": 0,      # AOUT2L -> open (Phase 2)
        "25": 0,      # AOUT2R -> open (Phase 2)
        "26": 3,      # PDN -> V33_A via R17 (pull-up)
        "27": 1,      # CAD -> VSS2 = GND (addr 0x10)
        "28": 12,     # SCL
        "29": 1,      # SI -> VSS2 = GND (unused, I2C mode)
        "30": 11,     # SDA
        "31": 9,      # SDOUT1 -> SDOUT1 (FFC pin 4)
        "32": 0,      # SDOUT2 -> open (goes low in TDM)
        "33": 1,      # EP -> GND
    }

    # ── U2: AK4619VN codec (QFN-32), I2C addr 0x11 (CAD=high) ──
    # Channels: ADC2L=ch5, ADC2R=ch6, ADC1L=ch7, ADC1R=ch8
    cn["U2"] = {
        "1": 8,       # SDIN1 -> TDM data in (shared)
        "2": 1,       # SDIN2 -> VSS2
        "3": 3,       # TVDD -> V33_A
        "4": 1,       # VSS2 -> GND
        "5": 15,      # AVDRV -> U2_AVDRV
        "6": 7,       # LRCK -> LRCLK
        "7": 6,       # BICK -> BCLK
        "8": 5,       # MCLK
        "9": 0,       # AIN5R -> open
        "10": 55,     # AIN4R -> FOUT_R3 (ch 6 R from daughter, filtered)
        "11": 0,      # AIN5L -> open
        "12": 41,     # AIN4L -> FOUT_5 (ch 5 filtered)
        "13": 0,      # AIN2R -> open
        "14": 56,     # AIN1R -> FOUT_R4 (ch 8 R from daughter, filtered)
        "15": 0,      # AIN2L -> open
        "16": 43,     # AIN1L -> FOUT_7 (ch 7 filtered, note: pin16=ADC1L=ch7)
        "17": 16,     # VCOM -> U2_VCOM
        "18": 3,      # AVDD -> V33_A
        "19": 1,      # VSS1 -> GND
        "20": 1,      # VREFL -> VSS1 = GND
        "21": 3,      # VREFH -> AVDD = V33_A
        "22": 0,      # AOUT1L -> open (Phase 2)
        "23": 0,      # AOUT1R -> open (Phase 2)
        "24": 0,      # AOUT2L -> open (Phase 2)
        "25": 0,      # AOUT2R -> open (Phase 2)
        "26": 3,      # PDN -> V33_A via R18 (pull-up)
        "27": 3,      # CAD -> TVDD = V33_A (addr 0x11)
        "28": 12,     # SCL
        "29": 1,      # SI -> VSS2 = GND
        "30": 11,     # SDA
        "31": 10,     # SDOUT1 -> SDOUT2 (FFC pin 13)
        "32": 0,      # SDOUT2 -> open
        "33": 1,      # EP -> GND
    }

    # ── U3: ADP7118 LDO (SOIC-8) — 5V -> 3.3V_A ──
    # Pin 1: OUT, Pin 2: SENSE, Pin 3: GND, Pin 4: NC
    # Pin 5: NC, Pin 6: NC, Pin 7: EN, Pin 8: IN
    cn["U3"] = {
        "1": 3,       # OUT -> V33_A
        "2": 3,       # SENSE -> V33_A (tied to OUT)
        "3": 1,       # GND
        "4": 0,       # NC
        "5": 0,       # NC
        "6": 0,       # NC
        "7": 2,       # EN -> 5V_A (always enabled)
        "8": 2,       # IN -> 5V_A
    }

    # ── U4: OPA1678 dual op-amp (SOIC-8) — Sallen-Key ch 1 (A) & ch 2 R (B) ──
    # Pin 1: OUT_A, Pin 2: IN-_A, Pin 3: IN+_A, Pin 4: V-
    # Pin 5: IN+_B, Pin 6: IN-_B, Pin 7: OUT_B, Pin 8: V+
    # Ch 1: Sallen-Key LPF. IN+ = FN1_1 (between R1 and R2), OUT = FOUT_1
    # IN- tied to OUT (unity gain follower config for Sallen-Key)
    # Ch R1: IN+ = FN1_R1, OUT = FOUT_R1
    cn["U4"] = {
        "1": 37,      # OUT_A -> FOUT_1 (ch 1 filter output)
        "2": 37,      # IN-_A -> FOUT_1 (tied to output, unity gain)
        "3": 29,      # IN+_A -> FN1_1 (filter node)
        "4": 1,       # V- -> GND
        "5": 50,      # IN+_B -> FN1_R1 (R channel filter node)
        "6": 54,      # IN-_B -> FOUT_R1 (tied to output)
        "7": 54,      # OUT_B -> FOUT_R1
        "8": 2,       # V+ -> 5V_A
    }

    # ── U5: OPA1678 dual op-amp (SOIC-8) — Sallen-Key ch 3 (A) & ch 4 R (B) ──
    cn["U5"] = {
        "1": 39,      # OUT_A -> FOUT_3
        "2": 39,      # IN-_A -> FOUT_3
        "3": 31,      # IN+_A -> FN1_3
        "4": 1,       # V- -> GND
        "5": 51,      # IN+_B -> FN1_R2
        "6": 57,      # IN-_B -> FOUT_R2
        "7": 57,      # OUT_B -> FOUT_R2
        "8": 2,       # V+ -> 5V_A
    }

    # ── U6: OPA1678 dual op-amp (SOIC-8) — Sallen-Key ch 5 (A) & ch 6 R (B) ──
    cn["U6"] = {
        "1": 41,      # OUT_A -> FOUT_5
        "2": 41,      # IN-_A -> FOUT_5
        "3": 33,      # IN+_A -> FN1_5
        "4": 1,       # V- -> GND
        "5": 52,      # IN+_B -> FN1_R3
        "6": 55,      # IN-_B -> FOUT_R3
        "7": 55,      # OUT_B -> FOUT_R3
        "8": 2,       # V+ -> 5V_A
    }

    # ── U7: OPA1678 dual op-amp (SOIC-8) — Sallen-Key ch 7 (A) & ch 8 R (B) ──
    cn["U7"] = {
        "1": 43,      # OUT_A -> FOUT_7
        "2": 43,      # IN-_A -> FOUT_7
        "3": 35,      # IN+_A -> FN1_7
        "4": 1,       # V- -> GND
        "5": 53,      # IN+_B -> FN1_R4
        "6": 56,      # IN-_B -> FOUT_R4
        "7": 56,      # OUT_B -> FOUT_R4
        "8": 2,       # V+ -> 5V_A
    }

    # ── J1-J4: Switchcraft 112BPC TS jacks (L channels) ──
    # Pad T = tip (signal), Pad S = sleeve (ground)
    cn["J1"] = {"T": 25, "S": 1}   # JACK_1, GND
    cn["J2"] = {"T": 26, "S": 1}   # JACK_2, GND
    cn["J3"] = {"T": 27, "S": 1}   # JACK_3, GND
    cn["J4"] = {"T": 28, "S": 1}   # JACK_4, GND

    # ── J5: FFC 16-pin ZIF (Main Board interconnect) ──
    # Pinout from pcb-architecture.md:
    cn["J5"] = {
        "1": 5,       # MCLK
        "2": 6,       # BCLK
        "3": 7,       # LRCLK
        "4": 9,       # SDOUT1 (U1 codec -> Teensy)
        "5": 8,       # SDIN1 (Teensy -> codecs)
        "6": 11,      # SDA
        "7": 12,      # SCL
        "8": 4,       # 5V_DIG
        "9": 2,       # 5V_A (raw, LDO input)
        "10": 1,      # GND
        "11": 1,      # GND
        "12": 1,      # GND
        "13": 10,     # SDOUT2 (U2 codec -> Teensy)
        "14": 0,      # spare
        "15": 0,      # spare
        "16": 0,      # spare
    }

    # ── J6: JST-PH 6-pin (to Daughter Board) ──
    # Carries 4 R-channel audio signals + power
    cn["J6"] = {
        "1": 46,      # DAIN_R1 (ch 2 R)
        "2": 47,      # DAIN_R2 (ch 4 R)
        "3": 48,      # DAIN_R3 (ch 6 R)
        "4": 49,      # DAIN_R4 (ch 8 R)
        "5": 2,       # 5V_A
        "6": 1,       # GND
    }

    # ── D1-D4: ESD diodes for L channel jacks ──
    # Schottky clamp to 5V_A rail. Cathode to 5V_A, Anode to signal
    cn["D1"] = {"1": 2, "2": 25}   # K=5V_A, A=JACK_1
    cn["D2"] = {"1": 2, "2": 26}   # K=5V_A, A=JACK_2
    cn["D3"] = {"1": 2, "2": 27}   # K=5V_A, A=JACK_3
    cn["D4"] = {"1": 2, "2": 28}   # K=5V_A, A=JACK_4

    # ── D5-D8: ESD diodes for R channels (from daughter board) ──
    cn["D5"] = {"1": 2, "2": 46}   # K=5V_A, A=DAIN_R1
    cn["D6"] = {"1": 2, "2": 47}   # K=5V_A, A=DAIN_R2
    cn["D7"] = {"1": 2, "2": 48}   # K=5V_A, A=DAIN_R3
    cn["D8"] = {"1": 2, "2": 49}   # K=5V_A, A=DAIN_R4

    # ── C1-C4: AC coupling caps (10uF 0805) for L channels ──
    # Series between jack tip and filter input
    cn["C1"] = {"1": 25, "2": 17}   # JACK_1 -> AIN_1_AC
    cn["C2"] = {"1": 26, "2": 19}   # JACK_2 -> AIN_3_AC
    cn["C3"] = {"1": 27, "2": 21}   # JACK_3 -> AIN_5_AC
    cn["C4"] = {"1": 28, "2": 23}   # JACK_4 -> AIN_7_AC

    # ── Sallen-Key filter passives ──
    # Each channel: AIN_x_AC -> R_a -> FN1_x -> R_b -> op-amp IN+
    # With C_a from FN1 to GND, and C_b from op-amp IN+ to OUT (feedback)
    # Actually for Sallen-Key unity-gain:
    #   IN -> R1 -> node1 -> R2 -> IN+(opamp)
    #   C1 from node1 to GND
    #   C2 from IN+(opamp) to OUT(opamp)
    # R1,R2 = 1k; C1 = 6.8nF, C2 = 3.3nF for ~22kHz Butterworth

    # Ch 1 (L): AIN_1_AC -> R1 -> FN1_1 -> R2 -> FN1_1 side of opamp
    # Wait, let me reconsider. Standard Sallen-Key unity gain:
    #   Vin -> R1 -> A -> R2 -> B -> (op-amp non-inv input)
    #   C1: A to GND
    #   C2: B to op-amp output
    # So: FN1 = node A (between R1 and R2), and B = op-amp IN+ directly
    # Actually we need a separate net for node B. But the plan says 2R+2C per ch.
    # Let me use FN1 for node A and the op-amp IN+ net is effectively node B.
    # Since C2 goes from B to OUT, and IN- is tied to OUT (unity gain),
    # C2 connects from op-amp IN+ to op-amp OUT.

    # For the L channels (ch 1,3,5,7 on this board):
    # Ch 1: AIN_1_AC -[R1]-> FN1_1 -[R2]-> U4 pin3 (IN+_A)
    #        C_a: FN1_1 to GND; C_b: U4 pin3 to U4 pin1 (OUT_A = FOUT_1)
    # Ch 3: AIN_3_AC -[R3]-> FN1_3 -[R4]-> U5 pin3
    # Ch 5: AIN_5_AC -[R5]-> FN1_5 -[R6]-> U6 pin3
    # Ch 7: AIN_7_AC -[R7]-> FN1_7 -[R8]-> U7 pin3

    # For C_b: it connects op-amp IN+ to OUT. Since both are already defined
    # as separate nets (FN1 for IN+, FOUT for OUT), C_b bridges them.
    # But wait: the op-amp IN+ IS the node after R2, which is a new node.
    # Let me redefine: FN1 = between R1 and R2, and op-amp IN+ has its
    # own net. But we already mapped op-amp IN+ to FN1_x... That's wrong.
    # FN1 should be between R1 and R2, and the op-amp IN+ is a DIFFERENT
    # node that R2 connects to.

    # Actually looking at the plan: "FN1_*, FN2_*" are listed as audio nets.
    # The plan uses FN1 for the node between the two resistors, and FOUT
    # for the filter output. The op-amp IN+ connects to a node after R2
    # which is the same node where C2 connects. Let's call this the op-amp
    # input node = same as what we feed to op-amp IN+.

    # I already mapped op-amp IN+ (e.g. U4 pin3) to FN1_1. So FN1_1 IS
    # the op-amp IN+ node. Then R1 goes from AIN_AC to some intermediate
    # node, and R2 goes from that node to FN1_1 (op-amp IN+).
    # That intermediate node needs its own net. Let's reuse: the "between
    # R1 and R2" node can be called FN2_x, and FN1_x is the op-amp input.

    # Actually let me simplify. The standard Sallen-Key has:
    #   Vin --R1-- A --R2-- B -- (op-amp +)
    #                |            |
    #               C1           C2 -- (op-amp out)
    #                |
    #               GND
    # Node A = between R1 and R2 (with C1 to GND)
    # Node B = op-amp non-inv input (with C2 to output)
    # In our mapping: A needs its own net, B = FN1_x (op-amp IN+)
    # But we only have 2 filter nodes budgeted per channel.

    # Let me reassign: use intermediate nets for node A.
    # We have enough net numbers. Let me add FN2 nets for node A.
    # Actually, I realize I was overcomplicating this. Looking at the plan
    # more carefully, FN1 = node A, FOUT = filter output. The connection
    # from R2 to op-amp IN+ is direct - the op-amp IN+ net IS the same
    # net going into the op-amp. Let me use a simpler model:
    #   AIN_AC -[R_a]-> FN1 (node A, C_a here to GND)
    #   FN1 -[R_b]-> op-amp IN+ = let's give this net FN2
    #   C_b: FN2 to FOUT
    # This means I need FN2 nets. But FN2 isn't in my net list...
    # The op-amp IN+ was mapped to FN1, which is wrong for Sallen-Key.

    # OK let me fix the nets and op-amp mappings. I'll remap:
    # - FN1_x = node between R1 and R2 (node A)
    # - Op-amp IN+ = a new net (we can just use the pin connection directly)
    # Since I have 57 nets already and need 8 more for the B nodes,
    # that's fine but getting complex. A simpler approach:
    # Just wire it correctly. The op-amp IN+ for ch1 is NOT FN1_1.
    # FN1_1 is between the two resistors. Let me fix.

    # I'll keep the current net numbering but fix the meanings.
    # FN1_x = node A (between R1 and R2 + C_a to GND)
    # FOUT_x = op-amp output (also C_b connects here)
    # We need a node B between R2, C_b, and op-amp IN+.
    # But since C_b goes to FOUT and R2 comes from FN1,
    # node B is ONLY connected to: R2 output, C_b, op-amp IN+
    # This is effectively the op-amp non-inv input net.

    # For simplicity, since Sallen-Key unity-gain has IN- = OUT,
    # C_b from node_B to FOUT creates the feedback. The op-amp
    # just buffers node_B filtered by C_b.
    # In practice for PCB routing, having a separate "node B" net
    # is correct but adds complexity. Many implementations just
    # treat R2->opamp_IN+ as a short trace with C_b nearby.

    # Let me just make the op-amp IN+ be its own net per channel.
    # I don't need to name them all - I can reuse the FN1 concept.

    # FINAL DECISION: Keep it simple.
    # FN1_x connects: R_a pad2, R_b pad1, C_a pad1 (C_a pad2 = GND)
    # Op-amp IN+ gets its own implicit net = FOUT is op-amp output.
    # The C_b cap bridges op-amp IN+ to FOUT.
    # The op-amp IN+ net only touches: R_b pad2, C_b pad1, op-amp IN+ pin.
    # Since this net is very local, I'll just assign the op-amp IN+ pin
    # the FN1 net and have R_b be from AIN_AC directly to FN1, making
    # R_a + C_a + R_b one combined filter section.

    # Actually, I think the cleanest approach for the PCB is:
    # Single-R + single-C per op-amp section (1st order), giving 2nd order
    # total across two op-amp sections. But the plan says "2R + 2C per channel"
    # with dual op-amps (each OPA1678 handles 2 channels).

    # Let me just do: proper 2nd order Sallen-Key.
    # Net assignments per L channel (using ch1 as example):
    #   AIN_1_AC --[R1]--> FN1_1 --[R2]--> (op-amp IN+)
    #   C5: FN1_1 to GND
    #   C6: (op-amp IN+) to FOUT_1 (= op-amp OUT)
    # The op-amp IN+ node needs a net. I'll encode it in the FOUT net
    # directly since C_b ties it to the output anyway and in- = out.
    # Wait no, that shorts R2 output to op-amp output via C_b at DC!
    # C_b is a capacitor so no DC short. The op-amp IN+ is a distinct node.

    # I need 8 more nets for the L+R channel op-amp input nodes.
    # OR I can note that in Sallen-Key, the cap C2 goes from the
    # op-amp input to the op-amp output, so we DO need a separate net.
    # Let me just have R2 connect to FN1 as well (merge nodes A and B)
    # and skip C_b... No, that changes the filter topology.

    # PRAGMATIC SOLUTION: In the PCB, R_b pad2 and C_b pad1 and op-amp IN+
    # are all on the same tiny net. I'll just assign the op-amp IN+ pin
    # directly in the component nets, creating implicit local nets.
    # These are effectively "opamp input" nets per channel section.

    # Renumber: let FN1_x be between R1+R2 (node A with C_a to GND).
    # FOUT_x is op-amp output. And I'll NOT have a named net for the
    # op-amp IN+ / C_b / R2 output junction — instead I'll just connect
    # them by assigning the same net code to all three pads.

    # I need to pick net codes for these. Let me extend the net list.
    # ... actually this is already handled by the FN1 nets if I
    # restructure slightly. Let me just be explicit:

    # For ch1 L:
    #   R1: pad1=AIN_1_AC(17), pad2=FN1_1(29)    [R1 = series input]
    #   R2: pad1=FN1_1(29), pad2=29               [WAIT - R2 output needs different net]

    # OK I'm going in circles. Let me just add the needed nets.
    # I'll use nets 58-65 for "op-amp input" nodes.
    # But first, let me reconsider: do I even need all those filter
    # nodes as separate nets for PCB routing? FreeRouter needs unique
    # net names for each electrical node. So yes.

    # For now, let me merge nodes A and B into one net (FN1).
    # This means R1 and R2 are in series from AIN_AC to FN1,
    # and both C_a (to GND) and C_b (to FOUT) hang off FN1.
    # This IS actually a valid 2nd-order MFB (multiple feedback)
    # topology variant, not Sallen-Key. But for the PCB layout
    # it routes essentially the same. The exact component values
    # would differ but the physical layout is identical.

    # FINAL ANSWER: Use a single filter node FN1 per channel.
    # R_a: AIN_AC -> FN1, R_b: FN1 -> op-amp IN+ (= FN1, same net)
    # Wait that makes R_b a 0-ohm jumper since both ends are FN1.
    # That doesn't work either.

    # Let me step back and use the CORRECT Sallen-Key topology with
    # proper separate nets. I'll extend the net dictionary.

    # Ch 1 L Sallen-Key:
    #   AIN_1_AC -[R1]-> FN1_1 -[R2]-> FILT_IN_1 -> opamp IN+
    #   C_a: FN1_1 -> GND
    #   C_b: FILT_IN_1 -> FOUT_1 (opamp OUT)

    # I'll hardcode: reassign op-amp pin3 from FN1 to a new FILT_IN net.
    # The plan's net count is ~57. I need 8 more = 65 total. Fine.

    # -- end of deliberation, implementing clean version --

    # Fix: reassign op-amp IN+ pins to proper filter input nets
    # Re-patch U4-U7 after adding new nets (done below in net extension)

    # L channel filter resistors (R1-R8): 1k each
    # Ch 1: R1(AIN_1_AC->FN1_1), R2(FN1_1->filtIN_1)
    cn["R1"] = {"1": 17, "2": 29}    # AIN_1_AC -> FN1_1
    cn["R2"] = {"1": 29, "2": 58}    # FN1_1 -> FILT_IN_1 (net 58)

    cn["R3"] = {"1": 19, "2": 31}    # AIN_3_AC -> FN1_3
    cn["R4"] = {"1": 31, "2": 59}    # FN1_3 -> FILT_IN_3

    cn["R5"] = {"1": 21, "2": 33}    # AIN_5_AC -> FN1_5
    cn["R6"] = {"1": 33, "2": 60}    # FN1_5 -> FILT_IN_5

    cn["R7"] = {"1": 23, "2": 35}    # AIN_7_AC -> FN1_7
    cn["R8"] = {"1": 35, "2": 61}    # FN1_7 -> FILT_IN_7

    # R channel filter resistors (R9-R16): 1k each
    # R channels come from daughter board via JST
    cn["R9"]  = {"1": 46, "2": 50}   # DAIN_R1 -> FN1_R1
    cn["R10"] = {"1": 50, "2": 62}   # FN1_R1 -> FILT_IN_R1

    cn["R11"] = {"1": 47, "2": 51}   # DAIN_R2 -> FN1_R2
    cn["R12"] = {"1": 51, "2": 63}   # FN1_R2 -> FILT_IN_R2

    cn["R13"] = {"1": 48, "2": 52}   # DAIN_R3 -> FN1_R3
    cn["R14"] = {"1": 52, "2": 64}   # FN1_R3 -> FILT_IN_R3

    cn["R15"] = {"1": 49, "2": 53}   # DAIN_R4 -> FN1_R4
    cn["R16"] = {"1": 53, "2": 65}   # FN1_R4 -> FILT_IN_R4

    # L channel filter caps
    # C_a (6.8nF): FN1 -> GND
    cn["C5"]  = {"1": 29, "2": 1}    # FN1_1 -> GND
    cn["C6"]  = {"1": 31, "2": 1}    # FN1_3 -> GND
    cn["C7"]  = {"1": 33, "2": 1}    # FN1_5 -> GND
    cn["C8"]  = {"1": 35, "2": 1}    # FN1_7 -> GND

    # C_b (3.3nF): FILT_IN -> FOUT (op-amp IN+ to OUT, feedback)
    cn["C9"]  = {"1": 58, "2": 37}   # FILT_IN_1 -> FOUT_1
    cn["C10"] = {"1": 59, "2": 39}   # FILT_IN_3 -> FOUT_3
    cn["C11"] = {"1": 60, "2": 41}   # FILT_IN_5 -> FOUT_5
    cn["C12"] = {"1": 61, "2": 43}   # FILT_IN_7 -> FOUT_7

    # R channel filter caps
    # C_a (6.8nF): FN1_R -> GND
    cn["C13"] = {"1": 50, "2": 1}    # FN1_R1 -> GND
    cn["C14"] = {"1": 51, "2": 1}    # FN1_R2 -> GND
    cn["C15"] = {"1": 52, "2": 1}    # FN1_R3 -> GND
    cn["C16"] = {"1": 53, "2": 1}    # FN1_R4 -> GND

    # C_b (3.3nF): FILT_IN_R -> FOUT_R
    cn["C17"] = {"1": 62, "2": 54}   # FILT_IN_R1 -> FOUT_R1
    cn["C18"] = {"1": 63, "2": 57}   # FILT_IN_R2 -> FOUT_R2
    cn["C19"] = {"1": 64, "2": 55}   # FILT_IN_R3 -> FOUT_R3
    cn["C20"] = {"1": 65, "2": 56}   # FILT_IN_R4 -> FOUT_R4

    # Codec decoupling: 100nF ceramic close to AVDD and TVDD
    cn["C21"] = {"1": 3, "2": 1}     # U1 AVDD decoupling: V33_A -> GND
    cn["C22"] = {"1": 3, "2": 1}     # U1 TVDD decoupling: V33_A -> GND
    cn["C23"] = {"1": 3, "2": 1}     # U2 AVDD decoupling: V33_A -> GND
    cn["C24"] = {"1": 3, "2": 1}     # U2 TVDD decoupling: V33_A -> GND

    # Codec decoupling: 2.2uF for AVDRV and VCOM
    cn["C25"] = {"1": 13, "2": 1}    # U1 AVDRV: U1_AVDRV -> GND
    cn["C26"] = {"1": 14, "2": 1}    # U1 VCOM: U1_VCOM -> GND
    cn["C27"] = {"1": 15, "2": 1}    # U2 AVDRV: U2_AVDRV -> GND
    cn["C28"] = {"1": 16, "2": 1}    # U2 VCOM: U2_VCOM -> GND

    # LDO decoupling
    cn["C29"] = {"1": 2, "2": 1}     # LDO input: 5V_A -> GND (100nF)
    cn["C30"] = {"1": 3, "2": 1}     # LDO output: V33_A -> GND (1uF)
    cn["C31"] = {"1": 3, "2": 1}     # LDO output bulk: V33_A -> GND (10uF)
    cn["C32"] = {"1": 4, "2": 1}     # 5V_DIG local: 5V_DIG -> GND (100nF)

    # PDN pull-up resistors
    cn["R17"] = {"1": 3, "2": 3}     # V33_A to U1 PDN (both sides V33_A since PDN pin=V33_A)
    cn["R18"] = {"1": 3, "2": 3}     # V33_A to U2 PDN

    # Fix: update op-amp IN+ pins to use FILT_IN nets instead of FN1
    cn["U4"]["3"] = 58     # IN+_A -> FILT_IN_1
    cn["U4"]["5"] = 62     # IN+_B -> FILT_IN_R1
    cn["U5"]["3"] = 59     # IN+_A -> FILT_IN_3
    cn["U5"]["5"] = 63     # IN+_B -> FILT_IN_R2
    cn["U6"]["3"] = 60     # IN+_A -> FILT_IN_5
    cn["U6"]["5"] = 64     # IN+_B -> FILT_IN_R3
    cn["U7"]["3"] = 61     # IN+_A -> FILT_IN_7
    cn["U7"]["5"] = 65     # IN+_B -> FILT_IN_R4

    return cn


# Extend NETS with the op-amp input filter nodes
NETS.update({
    58: "FILT_IN_1",
    59: "FILT_IN_3",
    60: "FILT_IN_5",
    61: "FILT_IN_7",
    62: "FILT_IN_R1",
    63: "FILT_IN_R2",
    64: "FILT_IN_R3",
    65: "FILT_IN_R4",
})

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

def _pad_smd(name, px, py, sx, sy, net_code, layer=None, rotation=0,
             extra_layers=None):
    if layer is None:
        layer = F_CU
    mask = F_MASK if layer == F_CU else B_MASK
    net_name = NETS.get(net_code, "")
    rot_str = f" {rotation}" if rotation else ""
    layer_str = f'"{layer}" "{mask}"'
    if extra_layers:
        layer_str += " " + " ".join(f'"{l}"' for l in extra_layers)
    return (
        f'    (pad "{name}" smd roundrect (at {px} {py}{rot_str}) (size {sx} {sy}) '
        f'(layers {layer_str}) (roundrect_rratio 0.25) '
        f'(net {net_code} "{net_name}") (uuid "{gen_uuid()}"))'
    )


def _pad_thru(name, px, py, size, drill, net_code):
    net_name = NETS.get(net_code, "")
    return (
        f'    (pad "{name}" thru_hole circle (at {px} {py}) (size {size} {size}) '
        f'(drill {drill}) (layers "*.Cu" "*.Mask") '
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


def _fp_wrapper(lib_name, ref, value, x, y, rotation, pad_lines, silk="",
                layer=None):
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

def fp_qfn32(ref, x, y, rotation, nets):
    """QFN-32 (AK4619VN). 5x5mm body, 0.5mm pitch, 32 pins + exposed pad.
    Pad-to-pad span: 5.0mm body, pads extend 0.5mm beyond body edge.
    Pad size: 0.8mm x 0.25mm (length x width along pad row).
    Exposed pad: 3.45mm x 3.45mm with 3x3 thermal via array."""
    pads = []

    # QFN-32: 8 pins per side, 0.5mm pitch
    # Pin 1 at top-left corner (pin 1 indicator)
    # Pins go counter-clockwise: 1-8 left side, 9-16 bottom, 17-24 right, 25-32 top
    # Pad positions in local coordinates (origin at center of QFN)
    # Left side (pins 1-8): x = -2.75, y from -1.75 to +1.75
    # Bottom side (pins 9-16): y = +2.75, x from -1.75 to +1.75
    # Right side (pins 17-24): x = +2.75, y from +1.75 to -1.75
    # Top side (pins 25-32): y = -2.75, x from +1.75 to -1.75

    pad_len = 0.8   # along the direction perpendicular to the side
    pad_wid = 0.25  # along the side

    for pin in range(1, 33):
        if pin <= 8:
            # Left side: pins 1-8, going down
            px = -2.75
            py = -1.75 + (pin - 1) * 0.5
            if rotation in (90, 270):
                psx, psy = pad_wid, pad_len
            else:
                psx, psy = pad_len, pad_wid
        elif pin <= 16:
            # Bottom side: pins 9-16, going right
            px = -1.75 + (pin - 9) * 0.5
            py = 2.75
            if rotation in (90, 270):
                psx, psy = pad_len, pad_wid
            else:
                psx, psy = pad_wid, pad_len
        elif pin <= 24:
            # Right side: pins 17-24, going up
            px = 2.75
            py = 1.75 - (pin - 17) * 0.5
            if rotation in (90, 270):
                psx, psy = pad_wid, pad_len
            else:
                psx, psy = pad_len, pad_wid
        else:
            # Top side: pins 25-32, going left
            px = 1.75 - (pin - 25) * 0.5
            py = -2.75
            if rotation in (90, 270):
                psx, psy = pad_len, pad_wid
            else:
                psx, psy = pad_wid, pad_len

        net_code = nets.get(str(pin), 0)
        pads.append(_pad_smd(str(pin), px, py, psx, psy, net_code))

    # Exposed pad (thermal ground pad)
    ep_net = nets.get("33", 1)  # Usually GND
    ep_size = 3.45
    pads.append(
        f'    (pad "33" smd roundrect (at 0 0) (size {ep_size} {ep_size}) '
        f'(layers "{F_CU}" "{F_MASK}" "{F_PASTE}") (roundrect_rratio 0.1) '
        f'(net {ep_net} "{NETS.get(ep_net, "")}") (uuid "{gen_uuid()}"))'
    )

    # Thermal vias in exposed pad (3x3 array, 0.3mm drill, 0.6mm pad)
    via_pitch = 1.0
    for vr in range(-1, 2):
        for vc in range(-1, 2):
            vx = vc * via_pitch
            vy = vr * via_pitch
            pads.append(
                f'    (pad "33" thru_hole circle (at {vx} {vy}) '
                f'(size 0.6 0.6) (drill 0.3) (layers "*.Cu" "*.Mask") '
                f'(net {ep_net} "{NETS.get(ep_net, "")}") (uuid "{gen_uuid()}"))'
            )

    silk = _silk_rect(-2.7, -2.7, 2.7, 2.7)
    # Pin 1 marker
    silk += f'\n    (fp_circle (center -2.2 -2.2) (end -2.0 -2.2) (stroke (width 0.12) (type solid)) (layer "{F_SILK}") (uuid "{gen_uuid()}"))'

    return _fp_wrapper("Package_DFN_QFN:QFN-32-1EP_5x5mm_P0.5mm_EP3.45x3.45mm",
                        ref, "AK4619VN", x, y, rotation, "\n".join(pads), silk)


def fp_soic8(ref, x, y, rotation, nets, value="OPA1678"):
    """SOIC-8, narrow body. 1.27mm pitch, 4 pins per side.
    Pad-to-pad span ~5.4mm (center to center of pad rows).
    Pad size: 1.5mm x 0.6mm."""
    pads = []
    half_span = 1.5 * 1.27  # 1.905mm from center to top/bottom pin

    pad_w, pad_h = 1.5, 0.6
    if rotation in (90, 270):
        pad_sx, pad_sy = pad_h, pad_w
    else:
        pad_sx, pad_sy = pad_w, pad_h

    for pin in range(1, 9):
        if pin <= 4:
            # Left side: pins 1-4, going down
            px = -2.7
            py = -1.905 + (pin - 1) * 1.27
        else:
            # Right side: pins 5-8, going up
            px = 2.7
            py = 1.905 - (pin - 5) * 1.27
        net_code = nets.get(str(pin), 0)
        pads.append(_pad_smd(str(pin), px, py, pad_sx, pad_sy, net_code))

    silk = _silk_rect(-2.0, -2.5, 2.0, 2.5)
    return _fp_wrapper("Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", ref, value,
                        x, y, rotation, "\n".join(pads), silk)


def fp_sod323(ref, x, y, rotation, nets, value="ESD"):
    """SOD-323 diode. Pad 1=Cathode, Pad 2=Anode.
    Pads at (-1.1, 0) and (1.1, 0), size 1.0x0.6mm."""
    pads = []
    pad_w, pad_h = 1.0, 0.6
    if rotation in (90, 270):
        pad_sx, pad_sy = pad_h, pad_w
    else:
        pad_sx, pad_sy = pad_w, pad_h

    for pin, px in [("1", -1.1), ("2", 1.1)]:
        net_code = nets.get(pin, 0)
        pads.append(_pad_smd(pin, px, 0, pad_sx, pad_sy, net_code))

    silk = _silk_rect(-1.8, -0.6, 1.8, 0.6)
    return _fp_wrapper("Diode_SMD:D_SOD-323", ref, value,
                        x, y, rotation, "\n".join(pads), silk)


def fp_c0603(ref, x, y, rotation, nets, value="100nF"):
    """0603 capacitor. Pads at (-0.8, 0) and (0.8, 0)."""
    pads = []
    pad_w, pad_h = 0.9, 1.0
    if rotation in (90, 270):
        pad_sx, pad_sy = pad_h, pad_w
    else:
        pad_sx, pad_sy = pad_w, pad_h
    for pin, px in [("1", -0.8), ("2", 0.8)]:
        net_code = nets.get(pin, 0)
        pads.append(_pad_smd(pin, px, 0, pad_sx, pad_sy, net_code))
    return _fp_wrapper("Capacitor_SMD:C_0603_1608Metric", ref, value,
                        x, y, rotation, "\n".join(pads))


def fp_c0805(ref, x, y, rotation, nets, value="10uF"):
    """0805 capacitor. Pads at (-1.0, 0) and (1.0, 0)."""
    pads = []
    # Pad size must be in BOARD coords (doesn't rotate with footprint)
    pad_w, pad_h = 1.0, 1.3
    if rotation in (90, 270):
        pad_sx, pad_sy = pad_h, pad_w
    else:
        pad_sx, pad_sy = pad_w, pad_h
    for pin, px in [("1", -1.0), ("2", 1.0)]:
        net_code = nets.get(pin, 0)
        pads.append(_pad_smd(pin, px, 0, pad_sx, pad_sy, net_code))
    return _fp_wrapper("Capacitor_SMD:C_0805_2012Metric", ref, value,
                        x, y, rotation, "\n".join(pads))


def fp_r0603(ref, x, y, rotation, nets, value="1k"):
    """0603 resistor. Same footprint as C_0603."""
    pads = []
    pad_w, pad_h = 0.9, 1.0
    if rotation in (90, 270):
        pad_sx, pad_sy = pad_h, pad_w
    else:
        pad_sx, pad_sy = pad_w, pad_h
    for pin, px in [("1", -0.8), ("2", 0.8)]:
        net_code = nets.get(pin, 0)
        pads.append(_pad_smd(pin, px, 0, pad_sx, pad_sy, net_code))
    return _fp_wrapper("Resistor_SMD:R_0603_1608Metric", ref, value,
                        x, y, rotation, "\n".join(pads))


def fp_ffc_16pin(ref, x, y, rotation, nets):
    """FFC/FPC ZIF connector, 16-pin, 1.0mm pitch. SMD.
    Pins span 15mm. Body ~18mm x 3mm."""
    pads = []
    for i in range(16):
        pin = str(i + 1)
        px = -7.5 + i * 1.0
        net_code = nets.get(pin, 0)
        pads.append(_pad_smd(pin, px, 0, 0.6, 1.5, net_code))

    # Mounting pads
    for sx in [-9.0, 9.0]:
        pads.append(
            f'    (pad "MP" smd rect (at {sx} 0) (size 1.2 2.0) '
            f'(layers "{F_CU}" "{F_MASK}") '
            f'(net 1 "GND") (uuid "{gen_uuid()}"))'
        )

    silk = _silk_rect(-9.5, -1.8, 9.5, 1.8)
    return _fp_wrapper("Connector_FFC-FPC:FFC_16pin_1mm", ref, "FFC-16",
                        x, y, rotation, "\n".join(pads), silk)


def fp_jst_ph_6(ref, x, y, rotation, nets):
    """JST-PH B6B-PH-K 6-pin vertical through-hole connector.
    Pins at 2mm pitch, pin 1 at origin, pins going in +X."""
    pads = []
    for i in range(6):
        pin = str(i + 1)
        net_code = nets.get(pin, 0)
        pads.append(_pad_thru(pin, i * 2.0, 0, 1.75, 0.8, net_code))

    silk = (
        f'    (fp_line (start -1.25 -1.6) (end 11.25 -1.6) (stroke (width 0.12) (type solid)) (layer "{F_SILK}") (uuid "{gen_uuid()}"))\n'
        f'    (fp_line (start 11.25 -1.6) (end 11.25 4.4) (stroke (width 0.12) (type solid)) (layer "{F_SILK}") (uuid "{gen_uuid()}"))\n'
        f'    (fp_line (start 11.25 4.4) (end -1.25 4.4) (stroke (width 0.12) (type solid)) (layer "{F_SILK}") (uuid "{gen_uuid()}"))\n'
        f'    (fp_line (start -1.25 4.4) (end -1.25 -1.6) (stroke (width 0.12) (type solid)) (layer "{F_SILK}") (uuid "{gen_uuid()}"))'
    )
    return _fp_wrapper("Connector_JST:JST_PH_B6B-PH-K_1x06_P2.00mm_Vertical",
                        ref, "B6B-PH-K-S", x, y, rotation, "\n".join(pads), silk)


def fp_112bpc(ref, x, y, rotation, nets):
    """Switchcraft 112BPC 1/4" TS jack. Through-hole.
    Origin at bushing center. Pads:
      T (Tip) at local (17.78, 0)
      S (Sleeve) at local (11.43, 7.62)
    With rotation=90, barrel extends toward +Y (panel edge)."""
    pads = []
    for name, (lx, ly) in [("T", (17.78, 0.0)), ("S", (11.43, 7.62))]:
        net_code = nets.get(name, 0)
        net_name = NETS.get(net_code, "")
        pads.append(
            f'    (pad "{name}" thru_hole circle (at {lx} {ly}) (size 2.4 2.4) '
            f'(drill 1.3) (layers "*.Cu" "*.Mask") '
            f'(net {net_code} "{net_name}") (uuid "{gen_uuid()}"))'
        )

    silk = (
        f'    (fp_line (start -4.0 -6.35) (end 22.0 -6.35) (stroke (width 0.12) (type solid)) (layer "{F_SILK}") (uuid "{gen_uuid()}"))\n'
        f'    (fp_line (start 22.0 -6.35) (end 22.0 10.0) (stroke (width 0.12) (type solid)) (layer "{F_SILK}") (uuid "{gen_uuid()}"))\n'
        f'    (fp_line (start 22.0 10.0) (end -4.0 10.0) (stroke (width 0.12) (type solid)) (layer "{F_SILK}") (uuid "{gen_uuid()}"))\n'
        f'    (fp_line (start -4.0 10.0) (end -4.0 -6.35) (stroke (width 0.12) (type solid)) (layer "{F_SILK}") (uuid "{gen_uuid()}"))'
    )
    return f"""  (footprint "mixtee-footprints:Switchcraft_112BPC"
    (layer "{F_CU}")
    (uuid "{gen_uuid()}")
    (at {x} {y} {rotation})
    (property "Reference" "{ref}" (at 0 -8.5 {rotation}) (layer "{F_SILK}") (uuid "{gen_uuid()}") (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "112BPC" (at 0 12.5 {rotation}) (layer "{F_FAB}") (uuid "{gen_uuid()}") (effects (font (size 1 1) (thickness 0.15))))
    (property "Footprint" "mixtee-footprints:Switchcraft_112BPC" (at 0 0 {rotation}) (layer "{F_FAB}") (uuid "{gen_uuid()}") (effects (font (size 1 1) (thickness 0.15)) hide))
{chr(10).join(pads)}
{silk}
  )"""


# ---------------------------------------------------------------------------
# Component placement
# ---------------------------------------------------------------------------

# All coordinates are (x, y) on the 80x30mm board
# y=0 is interior edge (FFC/JST connectors), y=30 is panel edge (jacks)

PLACEMENTS = {
    # ═══════════════════════════════════════════════════════════════════
    # ZONE A (y=0-5): Connectors + LDO
    # Board is lower board in pair; daughter sits above (y=0 interior)
    # ═══════════════════════════════════════════════════════════════════
    "U3":  {"func": "soic8",     "x": 6,  "y": 3,   "rot": 0,  "val": "ADP7118"},
    "J5":  {"func": "ffc_16pin", "x": 30, "y": 2,   "rot": 0},
    "J6":  {"func": "jst_ph_6",  "x": 65, "y": 2,   "rot": 0},
    # LDO decoupling (C29 at y=6.5 clears U3 pin 4, C31 shifted to x=16)
    "C29": {"func": "c0603",     "x": 2,  "y": 6.5, "rot": 0,  "val": "100nF"},
    "C30": {"func": "c0805",     "x": 12, "y": 2,   "rot": 0,  "val": "1uF"},
    "C31": {"func": "c0805",     "x": 16, "y": 2,   "rot": 0,  "val": "10uF"},
    "C32": {"func": "c0603",     "x": 42, "y": 2,   "rot": 0,  "val": "100nF"},

    # ═══════════════════════════════════════════════════════════════════
    # ZONE B (y=4-12): Codecs + decoupling
    # U1 at (20,7): QFN pads x=16.85..23.15, y=3.85..10.15
    # U2 at (60,7): QFN pads x=56.85..63.15, y=3.85..10.15
    # ═══════════════════════════════════════════════════════════════════
    "U1":  {"func": "qfn32",     "x": 20, "y": 7,   "rot": 0},
    "U2":  {"func": "qfn32",     "x": 60, "y": 7,   "rot": 0},
    # PDN pull-ups (moved left to 0.875mm gap from QFN pin 32)
    "R17": {"func": "r0603",     "x": 16, "y": 4,   "rot": 0,  "val": "10k"},
    "R18": {"func": "r0603",     "x": 56, "y": 4,   "rot": 0,  "val": "10k"},
    # U1 decoupling (C22 moved to y=6 to clear R17)
    "C21": {"func": "c0603",     "x": 25, "y": 9,   "rot": 0,  "val": "100nF"},
    "C22": {"func": "c0603",     "x": 15, "y": 6,   "rot": 0,  "val": "100nF"},
    "C25": {"func": "c0805",     "x": 16, "y": 10,  "rot": 0,  "val": "2.2uF"},
    "C26": {"func": "c0805",     "x": 25, "y": 7,   "rot": 0,  "val": "2.2uF"},
    # U2 decoupling (mirrored)
    "C23": {"func": "c0603",     "x": 65, "y": 9,   "rot": 0,  "val": "100nF"},
    "C24": {"func": "c0603",     "x": 55, "y": 6,   "rot": 0,  "val": "100nF"},
    "C27": {"func": "c0805",     "x": 56, "y": 10,  "rot": 0,  "val": "2.2uF"},
    "C28": {"func": "c0805",     "x": 65, "y": 7,   "rot": 0,  "val": "2.2uF"},

    # ═══════════════════════════════════════════════════════════════════
    # ZONE C (y=11-16): ESD diodes + AC coupling
    # 40mm board: jack tips at y=22.22, sleeves at y=28.57
    # ═══════════════════════════════════════════════════════════════════
    # L-channel ESD (offset from jack x-positions)
    "D1":  {"func": "sod323",    "x": 7,  "y": 13,  "rot": 0},
    "D2":  {"func": "sod323",    "x": 27, "y": 13,  "rot": 0},
    "D3":  {"func": "sod323",    "x": 47, "y": 13,  "rot": 0},
    "D4":  {"func": "sod323",    "x": 67, "y": 13,  "rot": 0},
    # R-channel ESD (vertical column at x=77, clear of passive cols)
    "D5":  {"func": "sod323",    "x": 77, "y": 4,   "rot": 0},
    "D6":  {"func": "sod323",    "x": 77, "y": 6,   "rot": 0},
    "D7":  {"func": "sod323",    "x": 77, "y": 8,   "rot": 0},
    "D8":  {"func": "sod323",    "x": 77, "y": 10,  "rot": 0},
    # AC coupling caps (10uF 0805, rot=90, between ESD and filter zones)
    "C1":  {"func": "c0805_10u", "x": 13, "y": 12,  "rot": 90},
    "C2":  {"func": "c0805_10u", "x": 33, "y": 12,  "rot": 90},
    "C3":  {"func": "c0805_10u", "x": 53, "y": 12,  "rot": 90},
    "C4":  {"func": "c0805_10u", "x": 73, "y": 12,  "rot": 90},

    # ═══════════════════════════════════════════════════════════════════
    # ZONE D (y=14-22): Op-amps + filter passives
    # Jacks at y=40: tips at (10/30/50/70, 22.22), sleeves at y=28.57
    # Op-amps at y=17, passive cols at opamp_x ± 6
    # All passive-to-opamp clearances verified ≥ 1.3mm
    # R-channel cols shifted +2mm from jack-tip x (x=32/52/72)
    # ═══════════════════════════════════════════════════════════════════
    "J1":  {"func": "112bpc",    "x": 10, "y": 40,  "rot": 90},
    "J2":  {"func": "112bpc",    "x": 30, "y": 40,  "rot": 90},
    "J3":  {"func": "112bpc",    "x": 50, "y": 40,  "rot": 90},
    "J4":  {"func": "112bpc",    "x": 70, "y": 40,  "rot": 90},

    "U4":  {"func": "soic8",     "x": 8,  "y": 17,  "rot": 0,  "val": "OPA1678"},
    "U5":  {"func": "soic8",     "x": 24, "y": 17,  "rot": 0,  "val": "OPA1678"},
    "U6":  {"func": "soic8",     "x": 44, "y": 17,  "rot": 0,  "val": "OPA1678"},
    "U7":  {"func": "soic8",     "x": 64, "y": 17,  "rot": 0,  "val": "OPA1678"},

    # Filter passives: columns at opamp_x ± 6
    # Each column: R_a(y=14.5), C_a(y=16), R_b(y=19), C_b(y=20.5)

    # U4 group: ch1 L (col x=2) + ch2 R (col x=14)
    "R1":  {"func": "r0603",     "x": 2,  "y": 14.5, "rot": 0, "val": "1k"},
    "C5":  {"func": "c0603",     "x": 2,  "y": 16,   "rot": 0, "val": "6.8nF"},
    "R2":  {"func": "r0603",     "x": 2,  "y": 19,   "rot": 0, "val": "1k"},
    "C9":  {"func": "c0603",     "x": 2,  "y": 20.5, "rot": 0, "val": "3.3nF"},
    "R9":  {"func": "r0603",     "x": 14, "y": 14.5, "rot": 0, "val": "1k"},
    "C13": {"func": "c0603",     "x": 14, "y": 16,   "rot": 0, "val": "6.8nF"},
    "R10": {"func": "r0603",     "x": 14, "y": 19,   "rot": 0, "val": "1k"},
    "C17": {"func": "c0603",     "x": 14, "y": 20.5, "rot": 0, "val": "3.3nF"},

    # U5 group: ch3 L (col x=18) + ch4 R (col x=32, shifted from 30)
    "R3":  {"func": "r0603",     "x": 18, "y": 14.5, "rot": 0, "val": "1k"},
    "C6":  {"func": "c0603",     "x": 18, "y": 16,   "rot": 0, "val": "6.8nF"},
    "R4":  {"func": "r0603",     "x": 18, "y": 19,   "rot": 0, "val": "1k"},
    "C10": {"func": "c0603",     "x": 18, "y": 20.5, "rot": 0, "val": "3.3nF"},
    "R11": {"func": "r0603",     "x": 32, "y": 14.5, "rot": 0, "val": "1k"},
    "C14": {"func": "c0603",     "x": 32, "y": 16,   "rot": 0, "val": "6.8nF"},
    "R12": {"func": "r0603",     "x": 32, "y": 19,   "rot": 0, "val": "1k"},
    "C18": {"func": "c0603",     "x": 32, "y": 20.5, "rot": 0, "val": "3.3nF"},

    # U6 group: ch5 L (col x=38) + ch6 R (col x=52, shifted from 50)
    "R5":  {"func": "r0603",     "x": 38, "y": 14.5, "rot": 0, "val": "1k"},
    "C7":  {"func": "c0603",     "x": 38, "y": 16,   "rot": 0, "val": "6.8nF"},
    "R6":  {"func": "r0603",     "x": 38, "y": 19,   "rot": 0, "val": "1k"},
    "C11": {"func": "c0603",     "x": 38, "y": 20.5, "rot": 0, "val": "3.3nF"},
    "R13": {"func": "r0603",     "x": 52, "y": 14.5, "rot": 0, "val": "1k"},
    "C15": {"func": "c0603",     "x": 52, "y": 16,   "rot": 0, "val": "6.8nF"},
    "R14": {"func": "r0603",     "x": 52, "y": 19,   "rot": 0, "val": "1k"},
    "C19": {"func": "c0603",     "x": 52, "y": 20.5, "rot": 0, "val": "3.3nF"},

    # U7 group: ch7 L (col x=58) + ch8 R (col x=72, shifted from 70)
    "R7":  {"func": "r0603",     "x": 58, "y": 14.5, "rot": 0, "val": "1k"},
    "C8":  {"func": "c0603",     "x": 58, "y": 16,   "rot": 0, "val": "6.8nF"},
    "R8":  {"func": "r0603",     "x": 58, "y": 19,   "rot": 0, "val": "1k"},
    "C12": {"func": "c0603",     "x": 58, "y": 20.5, "rot": 0, "val": "3.3nF"},
    "R15": {"func": "r0603",     "x": 72, "y": 14.5, "rot": 0, "val": "1k"},
    "C16": {"func": "c0603",     "x": 72, "y": 16,   "rot": 0, "val": "6.8nF"},
    "R16": {"func": "r0603",     "x": 72, "y": 19,   "rot": 0, "val": "1k"},
    "C20": {"func": "c0603",     "x": 72, "y": 20.5, "rot": 0, "val": "3.3nF"},
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
        val = info.get("val", "")

        if func_name == "qfn32":
            footprints.append(fp_qfn32(ref, x, y, rot, nets))
        elif func_name == "soic8":
            footprints.append(fp_soic8(ref, x, y, rot, nets, val))
        elif func_name == "sod323":
            footprints.append(fp_sod323(ref, x, y, rot, nets))
        elif func_name == "c0603":
            footprints.append(fp_c0603(ref, x, y, rot, nets, val or "100nF"))
        elif func_name in ("c0805", "c0805_10u"):
            v = "10uF" if "10u" in func_name else (val or "10uF")
            footprints.append(fp_c0805(ref, x, y, rot, nets, v))
        elif func_name == "r0603":
            footprints.append(fp_r0603(ref, x, y, rot, nets, val or "1k"))
        elif func_name == "ffc_16pin":
            footprints.append(fp_ffc_16pin(ref, x, y, rot, nets))
        elif func_name == "jst_ph_6":
            footprints.append(fp_jst_ph_6(ref, x, y, rot, nets))
        elif func_name == "112bpc":
            footprints.append(fp_112bpc(ref, x, y, rot, nets))

    all_footprints = "\n\n".join(footprints)

    # Zone fills for 4-layer board
    # Zone 1: GND on In1.Cu (full board)
    # Zone 2: V33_A on In2.Cu (full board)
    # Zone 3: GND on B.Cu (full board)
    zones = []
    zone_defs = [
        (1, "GND", IN1_CU),
        (3, "V33_A", IN2_CU),
        (1, "GND", B_CU),
    ]
    for net_code, net_name, layer in zone_defs:
        zones.append(f"""  (zone
    (net {net_code})
    (net_name "{net_name}")
    (layer "{layer}")
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
  )""")

    all_zones = "\n\n".join(zones)

    board_text = f"""  (gr_text "MIXTEE Input Mother" (at {BOARD_W/2} {BOARD_H - 1}) (layer "{F_SILK}") (uuid "{gen_uuid()}")
    (effects (font (size 1.2 1.2) (thickness 0.15)))
  )"""

    pcb = f"""(kicad_pcb
  (version 20240108)
  (generator "mixtee_gen_input_mother")
  (generator_version "1.0")
  (general
    (thickness 1.6)
    (legacy_teardrops no)
  )
  (paper "A4")
  (layers
    (0 "{F_CU}" signal)
    (1 "{IN1_CU}" signal)
    (2 "{IN2_CU}" signal)
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

{all_zones}

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
    "filename": "mixtee-input-mother.kicad_pro",
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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    out_dir = os.path.dirname(os.path.abspath(__file__))

    pcb_path = os.path.join(out_dir, "mixtee-input-mother.kicad_pcb")
    with open(pcb_path, "w") as f:
        f.write(generate_pcb())
    print(f"PCB written to: {pcb_path}")

    pro_path = os.path.join(out_dir, "mixtee-input-mother.kicad_pro")
    with open(pro_path, "w") as f:
        f.write(generate_project())
    print(f"Project written to: {pro_path}")

    fp_lib_path = os.path.join(out_dir, "fp-lib-table")
    with open(fp_lib_path, "w") as f:
        f.write("""(fp_lib_table
  (version 7)
  (lib (name "mixtee-footprints") (type "KiCad") (uri "${KIPRJMOD}/../lib/mixtee-footprints.pretty") (options "") (descr ""))
)
""")
    print(f"Footprint lib table written to: {fp_lib_path}")

    # Summary
    comp_count = len(PLACEMENTS)
    net_count = len(NETS) - 1
    print(f"\nBoard: {BOARD_W} x {BOARD_H} mm, 4-layer")
    print(f"Components: {comp_count}")
    print(f"Nets: {net_count} named ({net_count + 1} including unconnected)")
    print(f"\nComponent breakdown:")
    cats = {}
    for ref in PLACEMENTS:
        prefix = ''.join(c for c in ref if c.isalpha())
        cats[prefix] = cats.get(prefix, 0) + 1
    for prefix, count in sorted(cats.items()):
        names = {"U": "ICs", "J": "Connectors", "D": "Diodes",
                 "C": "Capacitors", "R": "Resistors"}
        print(f"  {names.get(prefix, prefix)}: {count}")
    print(f"\nOpen mixtee-input-mother.kicad_pcb in KiCad to view.")
