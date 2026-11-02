"""Pack geometry shared by pack_front, pack_back, pack_clip and button caps. Board data come from
hardware/main-board/design.py so the enclosure follows the PCB layout automatically.

Frame: X right, Y up (toward the neck), Z out of the front face (the back plate's outer face is Z = 0).
Board (x right, y down, origin top-left) -> X = x - W/2, Y = H/2 - y.
"""
import importlib.util
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
_spec = importlib.util.spec_from_file_location("main_design", ROOT / "hardware" / "main-board" / "design.py")
MB = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(MB)

PCB_W, PCB_H, PCB_T = MB.W, MB.H, 1.6
WALL = 1.8
CLEAR = 0.35                  # PCB edge to inner wall
NECK_REGION = 11.0            # inner space above the PCB's top edge: J3 plug + cable bend + gooseneck nut
BAT = (36.0, 64.5, 5.6)       # battery bay (W, L, T) for 35.5 x 64 x 5.3 pouches (VERIFY: Pimoroni BAT0004 / PiHut)
BAT_SWELL = 0.6               # free space over the pouch (LiPo swelling allowance)
BACK_T = 1.8                  # back plate thickness
FRONT_T = 1.8                 # front face thickness
TOP_CLEAR = 5.6               # PCB top surface to the inside of the front face (tallest part: PH header ~5 mm VERIFY)
BTN_HOLE_D = 7.4
BTN_CAP_D = 7.0
NECK_HOLE_D = 10.5            # gooseneck M10x1 end
NUT_AF, NUT_T = 14.0, 3.0     # M10x1 nut (VERIFY)
SCREW_PILOT = 1.7             # M2 self-tapping into PETG
SCREW_CLEAR = 2.4
BOSS_D = 5.0

Z_BACK = BACK_T
Z_BAT_TOP = Z_BACK + BAT[2] + BAT_SWELL
Z_PCB_BOT = Z_BAT_TOP + 0.4
Z_PCB_TOP = Z_PCB_BOT + PCB_T
Z_FACE_IN = Z_PCB_TOP + TOP_CLEAR
Z_TOP = Z_FACE_IN + FRONT_T                      # overall thickness without the clip

IN_X = PCB_W / 2 + CLEAR
IN_Y_BOT = -PCB_H / 2 - CLEAR
IN_Y_TOP = PCB_H / 2 + NECK_REGION
OUT_X = IN_X + WALL
OUT_Y_BOT = IN_Y_BOT - WALL
OUT_Y_TOP = IN_Y_TOP + WALL
CORNER_R = 4.0


def board_xy(x, y):
    return x - PCB_W / 2, PCB_H / 2 - y


def placed(ref):
    x, y, rot, side = MB.PLACE[ref]
    X, Y = board_xy(x, y)
    return X, Y, rot


def mount_holes():
    return [board_xy(x, y) for (x, y) in getattr(MB, "MOUNT_HOLES", [])]
