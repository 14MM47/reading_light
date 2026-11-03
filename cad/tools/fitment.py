"""Fitment renders: how every part sits in the pack and in the moon head (exploded and cut-away views, labelled).

  python cad/tools/fitment.py          (CAD venv; calls KiCad's system python3 for the board geometry)

Writes docs/design/fitment/*.png. Geometry sources, all live:
- printed parts: cad/parts/*.py, in their assembled frames (the same placement as cad/tools/assembly.py);
- boards: the generated .kicad_pcb (hardware/export_geometry.py). Outline, slot and holes are exact; components are
  their Fab-layer body outline extruded to a datasheet body height (HEIGHTS below);
- bought parts drawn from design constants: LiPo pouch (pack_back context), M10 nut (moon_base context), M2 screws,
  gooseneck (10 mm OD, 6.8 mm bore), the four cable wires (Qwiic colours).
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
import types
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import MultiPoint, Point, Polygon

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "cad" / "parts"))
from _lib import moonlib as L  # noqa: E402
from _lib import packlib as K  # noqa: E402
from _lib.meshkit import as_manifold, to_trimesh  # noqa: E402
import button_caps, moon_base, moon_ring, moon_shell, pack_back, pack_clip, pack_front  # noqa: E402,E401

OUT = ROOT / "docs" / "design" / "fitment"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# body heights (mm) by footprint name fragment, from the datasheets / KiCad models
HEIGHTS = [("PTS645", 3.5), ("PCM12", 1.5), ("USB4125", 3.26), ("S2B-PH-SM4", 5.5), ("SM04B-SRSS", 2.95),
           ("SOIC-20W", 2.65), ("TSSOP-28", 1.2), ("TSSOP-8", 1.1), ("SOT-23-5", 1.1), ("SOT-23", 1.1),
           ("D_SMA", 2.3), ("SOD-123F", 1.0), ("Fuse_1812", 1.3), ("C_0805", 1.25), ("R_0805", 0.6),
           ("C_0603", 0.8), ("R_0603", 0.5), ("LED_0603", 0.8), ("LED_PLCC_2835", 0.8), ("PLCC4_3.2x2.8", 1.9)]
SKIP = ("TestPoint", "PinHeader", "LED_WirePads")    # flat pads, the DNP header, the cable pads

COL = {"front": (122, 150, 182), "back": (92, 112, 140), "clip": (70, 76, 88), "caps": (226, 140, 60),
       "pcb_main": (36, 112, 66), "pcb_led": (238, 238, 232), "battery": (196, 198, 206), "screw": (150, 150, 158),
       "neck": (62, 62, 68), "cup": (122, 150, 182), "ring": (90, 170, 210), "moon": (246, 242, 230),
       "nut": (196, 160, 70), "ic": (48, 48, 52), "passive": (180, 150, 110), "conn": (232, 232, 226),
       "switch": (60, 60, 64), "led_w": (250, 236, 150), "led_rgb": (235, 235, 235), "diode": (70, 70, 74),
       "usb": (200, 200, 205)}


# ------------------------------------------------------------------------------------------------ geometry
def tm(x):
    return to_trimesh(as_manifold(x))


def board_geometry():
    dst = ROOT / "out" / "fitment" / "board_geometry.json"
    subprocess.run(["/usr/bin/python3", str(ROOT / "hardware" / "export_geometry.py"), str(dst)], check=True,
                   capture_output=True)
    return json.loads(dst.read_text())


def comp_color(fpname):
    f = fpname
    if any(s in f for s in ("SOIC", "TSSOP", "SOT-23")):
        return COL["ic"]
    if "PTS645" in f or "PCM12" in f:
        return COL["switch"]
    if "USB" in f:
        return COL["usb"]
    if "JST" in f:
        return COL["conn"]
    if "2835" in f:
        return COL["led_w"]
    if "PLCC4" in f:
        return COL["led_rgb"]
    if "D_SMA" in f or "SOD-123" in f:
        return COL["diode"]
    if "LED_0603" in f:
        return (220, 60, 50)
    return COL["passive"]


def board_meshes(g, xform, z_bot, thickness, pcb_color):
    """Board slab (exact outline, slot, mounting holes) + component bodies. xform(x, y) -> (X, Y)."""
    out = []
    holes_xy = [f["pads"][0] for f in g["footprints"] if f["ref"].startswith("H") and f["pads"]]
    for poly in g["outline"]:
        outer = [xform(*p) for p in poly["outer"]]
        inner = [[xform(*p) for p in h] for h in poly["holes"]]
        shp = Polygon(outer, inner).buffer(0)
        for (hx, hy) in holes_xy:
            shp = shp.difference(Point(*xform(hx, hy)).buffer(1.1, 24))
        slab = trimesh.creation.extrude_polygon(shp, thickness)
        slab.apply_translation((0, 0, z_bot))
        out.append(("board", slab, pcb_color))
    for f in g["footprints"]:
        name = f["fp"]
        if f["ref"].startswith("H") or any(s in name for s in SKIP) or len(f["body"]) < 3:
            continue
        h = next((v for k, v in HEIGHTS if k in name), 0.6)
        hull = MultiPoint([xform(*p) for p in f["body"]]).convex_hull
        if hull.area < 0.05:
            continue
        body = trimesh.creation.extrude_polygon(hull, h)
        top = f["side"] == "top"
        z0 = z_bot + thickness if top else z_bot - h
        body.apply_translation((0, 0, z0))
        out.append((f["ref"], body, comp_color(name)))
        if "PTS645" in name:                   # round actuator to 4.3 mm
            X, Y = xform(*f["pos"])
            act = trimesh.creation.cylinder(radius=1.75, height=0.8, sections=32)
            act.apply_translation((X, Y, z0 + h + 0.4))
            out.append((f["ref"] + "-act", act, (30, 30, 32)))
    return out


def tube(p0, p1, r, sections=20):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    c = trimesh.creation.cylinder(radius=r, segment=[p0, p1], sections=sections)
    return c


def wire(points, r=0.35):
    pts = np.asarray(points, float)
    return trimesh.creation.sweep_polygon(Point(0, 0).buffer(r, 8), pts)


def pack_parts(g):
    """All pack parts in the pack frame (X right, Y toward the neck, Z out of the front face)."""
    P = []
    fs = tm(pack_front.part())
    fs.apply_translation((0, 0, -K.Z_TOP))
    fs.apply_transform(trimesh.transformations.rotation_matrix(math.pi, (0, 1, 0)))
    P.append(("front shell (PETG)", fs, COL["front"], "front"))
    bp = tm(pack_back.part())
    P.append(("back plate (PETG)", bp, COL["back"], "back"))
    cl = tm(pack_clip.part())
    cl.apply_transform(trimesh.transformations.rotation_matrix(math.pi, (0, 1, 0)))
    P.append(("book clip (PETG)", cl, COL["clip"], "clip"))
    bat = tm(pack_back.context(None)["battery"])
    P.append(("LiPo 1200 mAh pouch", bat, COL["battery"], "battery"))
    xf = lambda x, y: (x - K.PCB_W / 2, K.PCB_H / 2 - y)   # noqa: E731
    for name, m, c in board_meshes(g["main-board"], xf, K.Z_PCB_BOT, K.PCB_T, COL["pcb_main"]):
        P.append((name, m, c, "pcb"))
    for ref, sym in (("SW2", "+"), ("SW3", "o"), ("SW4", "-")):
        cap = tm(button_caps._cap(sym))
        X, Y, _ = K.placed(ref)
        cap.apply_translation((X, Y, K.Z_PCB_TOP + 4.3))
        P.append((f"button cap {ref}", cap, COL["caps"], "caps"))
    for (X, Y) in K.mount_holes():               # M2x6 pan heads under the PCB (1.3 mm high, in the 1.6 mm gap)
        head = tube((X, Y, K.Z_PCB_BOT - 1.3), (X, Y, K.Z_PCB_BOT), 1.9)
        shank = tube((X, Y, K.Z_PCB_BOT), (X, Y, K.Z_PCB_BOT + 6.0), 1.0)
        P.append(("M2x6 screw", trimesh.util.concatenate([head, shank]), COL["screw"], "pcb"))
    zc = float(cl.bounds[0][2])
    for (X, Y) in pack_back.SCREWS:              # M2x12 through clip root + back plate into the shell bosses
        head = tube((X, Y, zc - 1.3), (X, Y, zc), 1.9)
        shank = tube((X, Y, zc), (X, Y, zc + 12.0), 1.0)
        P.append(("M2x12 screw", trimesh.util.concatenate([head, shank]), COL["screw"], "clip"))
    neck_z = (K.Z_BACK + K.Z_FACE_IN) / 2
    g_out = tube((0, K.PCB_H / 2 + 4.0, neck_z), (0, K.OUT_Y_TOP + 18.0, neck_z), 5.0, 40)
    g_in = tube((0, K.PCB_H / 2 + 3.9, neck_z), (0, K.OUT_Y_TOP + 18.1, neck_z), 3.4, 40)
    P.append(("gooseneck (M10x1 end)", g_out.difference(g_in), COL["neck"], "neck"))
    return P


def head_parts(g):
    """Moon head in the base frame (Z up, cup floor at Z = 0)."""
    d = moon_base.dims()
    P = []
    P.append(("base cup (PETG)", tm(moon_base.part()), COL["cup"], "cup"))
    P.append(("M10x1 nut", tm(moon_base.context(None)["nut"]), COL["nut"], "nut"))
    xf = lambda x, y: (x - 50.0, 50.0 - y)       # noqa: E731
    for name, m, c in board_meshes(g["led-board"], xf, d["ledge_z"], L.BOARD_T, COL["pcb_led"]):
        P.append((name, m, c, "board"))
    ring = tm(moon_ring.part())
    ring.apply_translation((0, 0, d["board_top"]))
    P.append(("clamp ring (PETG)", ring, COL["ring"], "ring"))
    p = types.SimpleNamespace(n_lon=300, n_lat=150, albedo_w=0.75, smooth_px=3.5, gamma=1.0, seam_lon_deg=180.0)
    moon = tm(moon_shell.part(**vars(p)) + moon_shell.organic(p)["add"][0])
    moon.apply_translation((0, 0, d["moon_z0"]))       # skirt bottom over the cup, clamp cone on the ring
    P.append(("lithophane moon (PLA)", moon, COL["moon"], "moon"))
    t_out = tube((0, 0, -22.0), (0, 0, d["nut_top"]), 5.0, 40)
    t_in = tube((0, 0, -22.1), (0, 0, d["nut_top"] + 0.1), 3.4, 40)
    P.append(("gooseneck (thread flush with nut)", t_out.difference(t_in), COL["neck"], "neck"))
    # the four cable wires: up the bore, out above the nut, to the G V D C pads on the board's underside
    j1 = next(f for f in g["led-board"]["footprints"] if f["ref"] == "J1")
    cols = {"GND": (25, 25, 25), "VLED": (200, 40, 40), "SDA": (40, 90, 200), "SCL": (230, 200, 40)}   # Qwiic
    zt = d["ledge_z"]
    for k, ((px, py), net) in enumerate(zip(j1["pads"], j1["pad_nets"])):
        X, Y = xf(px, py)
        ox, oy = (k - 1.5) * 0.9, 0.0
        w = wire([(ox, oy, -20.0), (ox, oy, d["nut_top"] + 0.8), (ox * 0.6 + X * 0.4, Y * 0.5, zt - 1.6),
                  (X, Y, zt - 0.35)])
        P.append((f"wire {net}", w, cols.get(net, (120, 120, 120)), "wires"))
    return P


# ------------------------------------------------------------------------------------------------ render
class View:
    def __init__(self, eye, up, px_per_mm):
        e = np.asarray(eye, float)
        self.eye = e / np.linalg.norm(e)
        self.fwd = -self.eye
        up = np.asarray(up, float)
        r = np.cross(self.fwd, up)
        self.right = r / np.linalg.norm(r)
        self.up = np.cross(self.right, self.fwd)
        self.s = px_per_mm

    def uv(self, pts):
        pts = np.atleast_2d(pts)
        return np.stack([pts @ self.right, pts @ self.up], 1)


def section(mesh, normal, origin):
    try:
        m = trimesh.intersections.slice_mesh_plane(mesh, normal, origin, cap=True)
    except Exception:  # noqa: BLE001  (non-watertight piece: drop the cap, keep the half)
        m = trimesh.intersections.slice_mesh_plane(mesh, normal, origin, cap=False)
    return m


def render(parts, view: View, path: Path, title, labels, cut=None, notes=()):
    """parts: [(name, mesh, color, group)]; labels: [(text, key, hint_xyz)]: the dot lands on the visible pixel of
    the part whose name or group is `key` nearest to the hint (key None: exactly at the hint).
    cut: (normal, origin) - keep the normal side and hatch the section faces."""
    meshes, cols, capflag, keys = [], [], [], []
    for name, m, c, grp in parts:
        if cut is not None:
            m = section(m, *cut)
            if m is None or len(m.faces) == 0:
                continue
            n = np.asarray(cut[0], float)
            on = (np.abs(m.face_normals @ n) > 0.999) & (np.abs((m.triangles_center - cut[1]) @ n) < 1e-3)
        else:
            on = np.zeros(len(m.faces), bool)
        meshes.append(m)
        cols.append(np.tile(np.asarray(c, float), (len(m.faces), 1)))
        capflag.append(on)
        keys.append((name, grp))
    scene = trimesh.util.concatenate(meshes)
    fcol = np.concatenate(cols)
    fcap = np.concatenate(capflag)
    owner = np.concatenate([np.full(len(m.faces), i) for i, m in enumerate(meshes)])
    uv = view.uv(scene.vertices)
    lo, hi = uv.min(0), uv.max(0)
    W = int((hi[0] - lo[0]) * view.s) + 40
    H = int((hi[1] - lo[1]) * view.s) + 40
    us = lo[0] - 20 / view.s + (np.arange(W) + 0.5) / view.s
    vs = hi[1] + 20 / view.s - (np.arange(H) + 0.5) / view.s
    U, V = np.meshgrid(us, vs)
    depth0 = float((scene.vertices @ view.fwd).min()) - 10
    o = U.reshape(-1, 1) * view.right + V.reshape(-1, 1) * view.up + depth0 * view.fwd
    d = np.tile(view.fwd, (len(o), 1))
    try:
        from trimesh.ray.ray_pyembree import RayMeshIntersector
        inter = RayMeshIntersector(scene)
    except Exception:  # noqa: BLE001
        inter = scene.ray
    tri, ray, loc = inter.intersects_id(o, d, multiple_hits=False, return_locations=True)
    img = np.full((W * H, 3), 255.0)
    light = 0.55 * view.eye + 0.45 * view.up + 0.25 * view.right
    light /= np.linalg.norm(light)
    nrm = scene.face_normals[tri]
    nrm = np.where((nrm @ view.fwd)[:, None] > 0, -nrm, nrm)
    shade = 0.42 + 0.58 * np.clip(nrm @ light, 0, 1)
    col = fcol[tri] * shade[:, None]
    cap = fcap[tri]
    # section faces: flat, slightly darker, 45 deg hatch
    px = ray % W
    py = ray // W
    hatch = ((px + py) % 9) < 2
    col[cap] = fcol[tri][cap] * 0.80
    col[cap & hatch] = fcol[tri][cap & hatch] * 0.45
    img[ray] = col
    # outlines: depth jumps and part boundaries
    dimg = np.full(W * H, np.nan)
    dimg[ray] = (loc - o[ray]) @ view.fwd
    oimg = np.full(W * H, -1)
    oimg[ray] = owner[tri]
    dimg, oimg = dimg.reshape(H, W), oimg.reshape(H, W)
    edge = np.zeros((H, W), bool)
    for ax in (0, 1):
        dd = np.abs(np.diff(np.nan_to_num(dimg, nan=1e6), axis=ax, prepend=np.take(np.nan_to_num(dimg, nan=1e6), [0], ax)))
        oo = np.diff(oimg, axis=ax, prepend=np.take(oimg, [0], ax)) != 0
        edge |= (dd > 0.6) | oo
    img = img.reshape(H, W, 3)
    img[edge] = img[edge] * 0.30
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    # label anchors: snap each hint to the nearest visible pixel of its part
    f_t = ImageFont.truetype(FONT_B, 26)
    f_l = ImageFont.truetype(FONT, 19)
    f_n = ImageFont.truetype(FONT, 17)
    vis_y, vis_x = np.divmod(np.arange(W * H), W)
    oflat = oimg.reshape(-1)

    def hint_px(p):
        q = view.uv(np.asarray(p, float))[0]
        return np.array([(q[0] - us[0]) * view.s, (vs[0] - q[1]) * view.s])

    anchors = []
    for text, key, hint in labels:
        if key is None:
            anchors.append((text, hint_px(hint)))
            continue
        ids = [i for i, (n, g) in enumerate(keys) if n == key or g == key or n.startswith(key + " ")]
        sel = np.isin(oflat, ids)
        if not sel.any():
            print(f"  label '{text}': part '{key}' not visible, skipped")
            continue
        px_ = np.stack([vis_x[sel], vis_y[sel]], 1).astype(float)
        target = hint_px(hint) if hint is not None else np.median(px_, 0)
        anchors.append((text, px_[np.argmin(((px_ - target) ** 2).sum(1))]))
    tmp = ImageDraw.Draw(im)
    left = [(t, a) for t, a in anchors if a[0] < W / 2]
    right = [(t, a) for t, a in anchors if a[0] >= W / 2]
    ml = int(max([tmp.textlength(t, font=f_l) for t, _ in left] + [60]) + 60)
    mr = int(max([tmp.textlength(t, font=f_l) for t, _ in right] + [60]) + 60)
    top = 70
    bottom = 40 + 24 * len(notes)
    canvas = Image.new("RGB", (W + ml + mr, H + top + bottom), "white")
    canvas.paste(im, (ml, top))
    dr = ImageDraw.Draw(canvas)
    dr.text((20, 18), title, fill=(25, 25, 25), font=f_t)
    for side, group in (("L", left), ("R", right)):
        group = sorted(group, key=lambda z: z[1][1])
        ys, last = [], -1e9
        for _, a in group:
            y = max(a[1] + top, last + 30)
            ys.append(y)
            last = y
        over = (ys[-1] - (H + top - 10)) if ys else 0
        if over > 0:
            ys = [y - over for y in ys]
        for (t, a), y in zip(group, ys):
            ax, ay = a[0] + ml, a[1] + top
            tw = dr.textlength(t, font=f_l)
            if side == "L":
                x_text, x_end = ml - 24 - tw, ml - 16
            else:
                x_text, x_end = ml + W + 24, ml + W + 16
            dr.line([(ax, ay), (x_end, y)], fill=(90, 90, 90), width=2)
            dr.ellipse([ax - 4, ay - 4, ax + 4, ay + 4], fill=(200, 40, 40))
            dr.text((x_text, y - 11), t, fill=(20, 20, 20), font=f_l)
    for i, n in enumerate(notes):
        dr.text((20, H + top + 12 + 24 * i), n, fill=(70, 70, 70), font=f_n)
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path)
    print("wrote", path.relative_to(ROOT), canvas.size)


# ------------------------------------------------------------------------------------------------ views
def exploded(parts, offsets):
    out = []
    for name, m, c, grp in parts:
        mm = m.copy()
        mm.apply_translation(offsets.get(grp, (0, 0, 0)))
        out.append((name, mm, c, grp))
    return out


def main():
    g = board_geometry()
    pk = pack_parts(g)
    hd = head_parts(g)
    d = moon_base.dims()
    zf = K.Z_FACE_IN
    nz = (K.Z_BACK + zf) / 2
    notes_pack = ["Board and components from the generated KiCad board (body outlines extruded to datasheet heights); "
                  "printed parts from cad/parts.",
                  "Pouch drawn at its 35.5 x 64 x 5.3 mm listing size (VERIFY M7). Section faces are hatched."]

    # ---- 1. pack, exploded (lying face up, layers lifted along Z)
    off = {"clip": (0, 0, -26), "back": (0, 0, -12), "battery": (0, 0, 2), "pcb": (0, 0, 18), "caps": (0, 0, 46),
           "front": (0, 0, 82), "neck": (0, 10, 82)}
    v = View(eye=(0.75, -1.0, 0.85), up=(0, 0, 1), px_per_mm=11)
    labels = [("front shell (PETG): face, PCB bosses, J2 pocket", "front", (K.OUT_X, 0, K.Z_TOP + 82)),
              ("gooseneck M10x1 end: self-taps into the neck socket", "neck", None),
              ("button caps UP / MAIN / DOWN", "caps", None),
              ("moon cable connector J3", "J3", None),
              ("ATtiny3216 microcontroller", "U2", None),
              ("tact switches", "SW3", None),
              ("slide switch SW1 (on/off)", "SW1", None),
              ("charger, power path, LED-board switch", "Q2", None),
              ("battery header J2 + 6.4 x 5.0 mm lead slot", "J2", None),
              ("USB-C J1", "J1", None),
              ("main board 35 x 62 mm", "board", (K.PCB_W / 2, -10, K.Z_PCB_TOP + 18)),
              ("LiPo pouch 1200 mAh", "battery", None),
              ("back plate (PETG): 2 tabs + 2 screws", "back", (-K.IN_X, 10, K.BACK_T - 12)),
              ("M2x12 screws (clip + plate to shell)", "M2x12 screw", None),
              ("book clip (PETG)", "clip", None)]
    render(exploded(pk, off), v, OUT / "pack_exploded.png", "Pack: exploded (lying face up)", labels,
           notes=notes_pack)

    # ---- 2. pack, assembled, section through the button column (X = 0), seen from +X
    v = View(eye=(1.0, -0.12, 0.10), up=(0, 0, 1), px_per_mm=16)
    S = K.placed("SW3")
    labels = [("front face 1.8 mm", "front", (0, 12, K.Z_TOP)),
              ("button cap on its tact switch", "caps", (0, S[1], K.Z_TOP + 0.8)),
              ("tact switch (4.3 mm)", "SW3", None),
              ("PCB boss + M2 screw (head below the PCB)", "M2x6 screw", (0, K.mount_holes()[1][1], K.Z_PCB_BOT - 1)),
              ("main board", "board", (0, 5, K.Z_PCB_BOT)),
              ("1.6 mm gap: screw heads + Kapton", None, (0, -24, (K.Z_PCB_BOT + K.Z_BAT_TOP) / 2)),
              ("0.6 mm swelling space", None, (0, -20, K.Z_BAT_TOP - 0.3)),
              ("LiPo pouch", "battery", (0, 0, K.Z_BACK + 2.6)),
              ("back plate", "back", (0, 5, K.BACK_T / 2)),
              ("book clip", "clip", None),
              ("USB-C J1 behind its window", "J1", None),
              ("JST-SH J3: cable to the moon", "J3", None),
              ("gooseneck in the neck socket", "neck", None)]
    render(pk, v, OUT / "pack_section_buttons.png", "Pack: section through the buttons (X = 0)", labels,
           cut=((-1, 0, 0), (0, 0, 0)), notes=notes_pack)

    # ---- 3. pack section through J2 (battery header under its face pocket)
    J2 = K.placed("J2")
    X2 = J2[0]
    labels = [("0.8 mm pocket in the face over J2", None, (X2, J2[1], zf + 0.4)),
              ("J2 battery header, 5.5 mm tall", "J2", None),
              ("main board", "board", (X2, J2[1] + 10, K.Z_PCB_BOT)),
              ("LiPo pouch", "battery", None),
              ("back plate", "back", None),
              ("front shell", "front", (X2, -20, K.Z_TOP)),
              ("book clip", "clip", None)]
    render(pk, v, OUT / "pack_section_J2.png", f"Pack: section through the battery header J2 (X = {X2:.1f} mm)",
           labels, cut=((-1, 0, 0), (X2, 0, 0)), notes=notes_pack)

    # ---- 4. head, exploded
    offh = {"neck": (0, 0, -18), "nut": (0, 0, -9), "wires": (0, 0, -9), "cup": (0, 0, 0), "board": (0, 0, 14),
            "ring": (0, 0, 24), "moon": (0, 0, 36)}
    v = View(eye=(0.7, -1.0, 0.45), up=(0, 0, 1), px_per_mm=9)
    labels = [("lithophane moon 50 mm (PLA): skirt with 3 bayonet grooves", "moon", None),
              ("PETG clamp ring 0.8 mm: the PLA never touches the board", "ring", None),
              ("LED board 18 mm: 8 white + 1 RGB LEDs on top", "board", None),
              ("(LP5012 driver + MCP9800 sensor underneath)", "D9", None),
              ("base cup (PETG) inside the skirt: pocket, ledge, 3 lugs", "cup", None),
              ("M10x1 nut in the hex socket", "nut", None),
              ("4 wires GND / VLED / SDA / SCL", "wires", None),
              ("gooseneck tube, thread filed flush with the nut", "neck", None)]
    render(exploded(hd, offh), v, OUT / "head_exploded.png", "Moon head: exploded", labels,
           notes=["LED board and its components from the generated KiCad board; moon at preview resolution."])

    # ---- 5. head, section through the axis (X = 0), seen from +X
    v = View(eye=(1.0, -0.15, 0.12), up=(0, 0, 1), px_per_mm=14)
    labels = [("lithophane wall 0.9-2.6 mm (relief inside)", "moon", (0, -L.R_OUT, d["cut_z"] + 20)),
              ("white LEDs 1.2 mm below the opening", "D4", (0, -6, d["board_top"] + 0.6)),
              ("45 deg clamp cone presses the PETG ring", "moon", (0, -9.3, d["ring_top"])),
              ("PETG clamp ring", "ring", (0, -8.6, d["board_top"] + 0.4)),
              ("LED board, 0.1 mm proud of the cup rim", "board", (0, -8.8, d["ledge_z"] + 0.5)),
              ("LP5012 under the board centre", "U1", None),
              ("4.5 mm for the wires above the nut", "wires", (0, 0, d["nut_top"] + 2.5)),
              ("M10x1 nut", "nut", None),
              ("gooseneck tube end", "neck", (0, -4.6, -12)),
              ("cup lug in the skirt's bayonet groove", "cup", (0, L.LUG_R_OUT, L.cup_z(L.Z_LUG_FACE_TOP))),
              ("base cup (PETG) inside the moon's skirt", "cup", (0, L.CUP_R, d["floor_top"] + 3))]
    render(hd, v, OUT / "head_section.png", "Moon head: section through the axis", labels,
           cut=((-1, 0, 0), (0, 0, 0)),
           notes=["Section faces hatched. Nut and gooseneck from moonlib dimensions (nut 14 AF x 3: VERIFY M1).",
                  "Moon turned to its locked position: the lugs sit at the end of their grooves."])

    # ---- contact sheet
    files = ["pack_exploded.png", "pack_section_buttons.png", "pack_section_J2.png", "head_exploded.png",
             "head_section.png"]
    ims = [Image.open(OUT / f) for f in files]
    wmax = max(i.width for i in ims)
    sheet = Image.new("RGB", (wmax, sum(i.height for i in ims) + 20 * len(ims)), "white")
    y = 0
    for i in ims:
        sheet.paste(i, ((wmax - i.width) // 2, y))
        y += i.height + 20
    sheet.thumbnail((1800, 100000))
    sheet.save(OUT / "fitment_sheet.png")
    print("wrote", (OUT / "fitment_sheet.png").relative_to(ROOT), sheet.size)


if __name__ == "__main__":
    main()
