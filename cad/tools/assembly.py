"""Assembly preview of the whole lamp: pack (front shell, back plate, clip), gooseneck, base cup, moon.
Writes docs/design/assembly.png. Geometry comes from the part modules (assembled frames), the gooseneck is a
10 mm tube bent on an arc. Usage: python cad/tools/assembly.py
"""
import math
import sys
import types
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "cad" / "parts"))
sys.path.insert(0, str(ROOT / "cad" / "tools"))
from _lib import moonlib as L  # noqa: E402
from _lib import packlib as K  # noqa: E402
from _lib.meshkit import as_manifold, to_trimesh  # noqa: E402
import moon_base, moon_shell, pack_back, pack_clip, pack_front  # noqa: E402,E401


def tm(x):
    return to_trimesh(as_manifold(x))


def gooseneck(length=120.0, bend_deg=150.0, r_tube=5.0):
    """Tube from the pack top going up then arcing over toward +Z (front): centreline in the YZ plane."""
    straight = 25.0
    arc_len = length - straight
    R = arc_len / math.radians(bend_deg)
    pts = [np.array([0, s, 0.0]) for s in np.linspace(0, straight, 6)]
    for a in np.linspace(0, math.radians(bend_deg), 40)[1:]:
        pts.append(np.array([0, straight + R * math.sin(a), R * (1 - math.cos(a))]))
    pts = np.array(pts)
    from shapely.geometry import Point
    tube = trimesh.creation.sweep_polygon(Point(0, 0).buffer(r_tube, 24), pts)
    end = pts[-1]
    tangent = pts[-1] - pts[-2]
    return tube, end, tangent / np.linalg.norm(tangent)


def main():
    meshes = []
    # pack in its assembled frame (front shell part() is in print orientation: undo the flip)
    fs = tm(pack_front.part())
    fs.apply_translation((0, 0, -K.Z_TOP))
    fs.apply_transform(trimesh.transformations.rotation_matrix(math.pi, (0, 1, 0)))
    bp = tm(pack_back.part())
    cl = tm(pack_clip.part())
    cl.apply_transform(trimesh.transformations.rotation_matrix(math.pi, (0, 1, 0)))   # outer face toward -Z
    for m in (fs, bp, cl):
        meshes.append(m)
    # gooseneck from the pack's top wall (neck axis at Z = middle of the pack)
    neck_z = (K.Z_BACK + K.Z_FACE_IN) / 2
    g, end, tan = gooseneck()
    g.apply_translation((0, K.OUT_Y_TOP, neck_z))
    meshes.append(g)
    # base + moon: base axis along the tube tangent at the end, rim facing outward
    p = types.SimpleNamespace(n_lon=300, n_lat=150, albedo_w=0.75, smooth_px=3.5, gamma=1.0, seam_lon_deg=180.0)
    base = tm(moon_base.part())
    moon = tm(moon_shell.part(**vars(p)) + moon_shell.organic(p)["add"][0])
    moon.apply_translation((0, 0, moon_base.dims()["ring_top"]))       # skirt bottom (z=0) seats on the clamp ring
    head = trimesh.util.concatenate([base, moon])
    # align head +Z with the tube tangent
    Rm = trimesh.geometry.align_vectors([0, 0, 1], tan)
    head.apply_transform(Rm)
    head.apply_translation(np.array([0, K.OUT_Y_TOP, neck_z]) + end)
    meshes.append(head)
    scene = trimesh.util.concatenate(meshes)
    # world: pack Y up -> render with Y as "up"
    scene.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, (1, 0, 0)))   # pack Y -> world up
    from pipeline import render
    out = ROOT / "docs" / "design"
    render(scene, out / "assembly_a.png", eye=(0.9, -1.3, 0.35), size=900, title="Moon reading light - front (buttons)")
    render(scene, out / "assembly_b.png", eye=(-0.9, 1.3, 0.35), size=900, title="rear (clip side)")
    a, b = Image.open(out / "assembly_a.png"), Image.open(out / "assembly_b.png")
    w = Image.new("RGB", (a.width + b.width, a.height), "white")
    w.paste(a, (0, 0)); w.paste(b, (a.width, 0))
    w.save(out / "assembly.png")
    (out / "assembly_a.png").unlink(); (out / "assembly_b.png").unlink()
    print("wrote", out / "assembly.png", "bounds", scene.bounds.round(1).tolist())


if __name__ == "__main__":
    main()
