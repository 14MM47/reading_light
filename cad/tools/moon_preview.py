"""Preview of the lit lithophane moon (front view, near side) from the wall-thickness field.

Transmitted brightness ~ exp(-t / LAMBDA) with LAMBDA = 0.8 mm (typical white PLA lithophane contrast; VERIFY with a
step-wedge print). Writes docs/design/moon_preview.png (lit at 3000 K and 2700 K-red night, plus unlit).
Usage: python cad/tools/moon_preview.py
"""
import math
import sys
import types
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "cad" / "parts"))
import moon_shell as M  # noqa: E402
from _lib import moonlib as L  # noqa: E402

LAMBDA = 0.8


def view(t_grid, th, ph, size=520, tint=(255, 214, 170), lit=True):
    R = 1.0
    u = np.linspace(-1, 1, size)
    U, V = np.meshgrid(u, -u)
    inside = U ** 2 + V ** 2 < 1
    Y = -np.sqrt(np.clip(1 - U ** 2 - V ** 2, 0, 1))
    d0x, d0y, d0z = -U, -Y, V                       # undo the 180 deg rotation (B10)
    T = np.arccos(np.clip(-d0z, -1, 1))
    P = np.mod(np.arctan2(d0y, d0x), 2 * math.pi)
    ti = np.interp(T, th, np.arange(len(th)))
    pj = P / (2 * math.pi) * len(ph)
    t = ndimage.map_coordinates(t_grid, [ti, pj], order=1, mode="wrap")
    below = T < math.radians(L.opening_half_angle_deg() + 2)
    img = np.zeros((size, size, 3))
    if lit:
        b = np.exp(-(t - L.T_MIN) / LAMBDA)
        b = b / b[inside & ~below].max()
        img[...] = np.array(tint)[None, None, :] * (0.08 + 0.92 * b)[..., None]
    else:
        n_dot_l = np.clip(-Y * 0.6 + V * 0.5 + U * -0.3, 0, 1)
        img[...] = 235 * (0.35 + 0.65 * n_dot_l)[..., None]
    img[~inside] = 18
    img[inside & below] = (90, 90, 96)
    return Image.fromarray(img.astype(np.uint8))


def main():
    p = types.SimpleNamespace(n_lon=600, n_lat=300, albedo_w=0.75, smooth_px=3.5, gamma=1.0, seam_lon_deg=180.0)
    th, ph, t = M.thickness_field(p)
    tiles = [("lit, soft white 3000 K", view(t, th, ph, tint=(255, 221, 183))),
             ("lit, red night light", view(t, th, ph, tint=(255, 40, 20))),
             ("unlit (smooth outside)", view(t, th, ph, lit=False))]
    W = sum(im.width for _, im in tiles) + 40
    out = Image.new("RGB", (W, tiles[0][1].height + 40), (18, 18, 18))
    x = 10
    d = ImageDraw.Draw(out)
    for name, im in tiles:
        out.paste(im, (x, 30))
        d.text((x + 6, 8), name, fill=(220, 220, 220))
        x += im.width + 10
    path = ROOT / "docs" / "design" / "moon_preview.png"
    out.save(path)
    print("wrote", path, f"thickness range {t.min():.2f}-{t.max():.2f} mm")


if __name__ == "__main__":
    main()
