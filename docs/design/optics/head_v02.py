"""Inside-moon illumination for the v0.2 head (18 mm LED board) and the v0.1 head, with the opening as the aperture.

Same physics as the round-1 as-built model: Lambertian LEDs facing up, a corrected integrating-sphere term for the
inter-reflections (wall reflectance rho 0.70), the visible wall = polar angle > 50 deg from the bottom pole. A ray
from an LED reaches a wall point only if it crosses the opening plane inside the opening (r <= open_r) and, below
the plane, stays inside the bore (here the bore is never narrower than the opening, moon_shell B14). Each white
2835 is spread into 5 points along its radial long axis (lens +/- 1.3 mm); the RGB sits 1.2 mm higher (taller body).

Correction of 2026-11-03: an earlier version of the sweep let rays pass a flared bore that was WIDER than the
opening at the cut plane, i.e. through the PLA wall, and reported max/min 1.01 at 2.9 mm depth. With the opening as
the aperture the same layout gives 1.21; the LED depth below the opening is what matters (B13).

Round 3 (2026-11-04, R3-O1/O2): the RGB package at the centre (2.8 x 3.5 mm, 1.9 mm tall, i.e. 1.2 mm above the
white emitters) now shades the white LEDs' low rays across the centre, and the wall's area element includes the
slant of the 40-50 deg band where the wall radius changes (it overstated the band's area, so the escape fraction).

Usage: python docs/design/optics/head_v02.py     (prints the table; ~5 min)
"""
import math

import numpy as np

R_OUT, T_MAX = 25.0, 2.6
R_IN0, R_IN_MEAN = R_OUT - T_MAX, R_OUT - 1.75
RHO, RHO_PORT = 0.70, 0.70
XY = {"WW": (0.4599, 0.4106), "CW": (0.3451, 0.3516)}


def geom(board_d, open_r=None):
    open_r = board_d / 2 - 0.7 if open_r is None else open_r
    return open_r, -math.sqrt(R_IN0 ** 2 - open_r ** 2)


RGB_HALF = (1.4, 1.75)     # Wurth PLCC-4 3528 at the centre (rot 90): half-sizes in x, y
RGB_H = 1.9                 # package height above the board top (moonlib RGB_TOP_H); board top = emitters - 0.7


def grid(open_r, n_t=200, n_p=144):
    t0 = math.asin(open_r / R_IN0)
    th = np.linspace(t0 + 1e-3, math.pi - 1e-3, n_t)
    ph = np.linspace(0, 2 * math.pi, n_p, endpoint=False)
    T, P = np.meshgrid(th, ph, indexing="ij")
    w = np.clip((np.degrees(T) - 40.0) / 10.0, 0, 1)
    R = (1 - w) * R_IN0 + w * R_IN_MEAN                     # 2.6 mm collar band, 1.75 mm mean wall above
    X = np.stack([R * np.sin(T) * np.cos(P), R * np.sin(T) * np.sin(P), -R * np.cos(T)], -1)
    # surface normal and area of r = R(theta): tangent (R' sin + R cos, ., R sin - R' cos) in the meridian plane
    in_band = (np.degrees(T) > 40.0) & (np.degrees(T) < 50.0)
    dR = np.where(in_band, (R_IN_MEAN - R_IN0) / math.radians(10.0), 0.0)   # analytic: R is linear in the band
    slant = np.sqrt(1.0 + (dR / R) ** 2)
    nr, nz = R * np.sin(T) - dR * np.cos(T), -(R * np.cos(T) + dR * np.sin(T))   # outward normal (unnormalised)
    nn = np.hypot(nr, nz)
    nrm = -np.stack([nr / nn * np.cos(P), nr / nn * np.sin(P), nz / nn], -1)     # facing the inside
    dA = (R ** 2 * np.sin(T)) * slant * (th[1] - th[0]) * (2 * math.pi / n_p)
    return th, X, nrm, dA


def _box_blocks(l, v, box):
    """True where the segment l -> l + v passes through the axis-aligned box ((x0, x1), (y0, y1), (z0, z1))."""
    t0 = np.zeros(v.shape[:-1])
    t1 = np.ones(v.shape[:-1])
    for k in range(3):
        lo, hi = box[k]
        vk = np.where(np.abs(v[..., k]) > 1e-12, v[..., k], 1e-12)
        a, b = (lo - l[k]) / vk, (hi - l[k]) / vk
        t0 = np.maximum(t0, np.minimum(a, b))
        t1 = np.minimum(t1, np.maximum(a, b))
    return t1 > t0


def direct(L, X, nrm, z_cut, open_r, box=None):
    E = np.zeros(X.shape[:-1])
    for l in L:
        v = X - l
        d2 = (v ** 2).sum(-1)
        d = np.sqrt(d2)
        ca, cb = v[..., 2] / d, (-v * nrm).sum(-1) / d
        e = np.where((ca > 0) & (cb > 0), ca * cb / d2, 0.0)
        t = (z_cut - l[2]) / np.where(np.abs(v[..., 2]) > 1e-9, v[..., 2], 1e-9)
        r_at_cut = np.hypot(l[0] + t * v[..., 0], l[1] + t * v[..., 1])
        blocked = (t > 0) & (t < 1) & (r_at_cut > open_r)  # the opening is the aperture
        if box is not None:
            blocked |= _box_blocks(l, v, box)
        E += np.where(blocked, 0.0, e)
    return E


def total(L, X, nrm, dA, z_cut, open_r, box=None):
    Ed = direct(L, X, nrm, z_cut, open_r, box)
    phi_wall, phi_led = (Ed * dA).sum(), math.pi * len(L)
    A_wall, A_port = dA.sum(), math.pi * open_r ** 2
    A_tot = A_wall + A_port
    rho_avg = (RHO * A_wall + RHO_PORT * A_port) / A_tot
    return Ed + (RHO * phi_led) / (A_tot * (1 - rho_avg)), phi_wall / phi_led, A_port / A_tot


def layout(n_per_cct, n_rgb, ring_r, z_led, les=1.3):
    k = 2 * n_per_cct
    ang = [2 * math.pi * (i + 0.5) / k for i in range(k)]

    def leds(angles):
        out = []
        for a in angles:
            for s in np.linspace(-les, les, 5):
                out.append(((ring_r + s) * math.cos(a), (ring_r + s) * math.sin(a), z_led))
        return np.array(out)
    rgb = [(0.0, 0.0, z_led + 1.2)] if n_rgb == 1 else [(-3.0, 0.0, z_led + 1.2), (3.0, 0.0, z_led + 1.2)]
    return leds(ang[0::2]), leds(ang[1::2]), np.array(rgb)


def uv(x, y):
    d = -2 * x + 12 * y + 3
    return 4 * x / d, 9 * y / d


def colour_spread(Eww, Ecw, vis, share_ww=0.37):
    """Local 4000 K mix over the visible wall: max distance in u'v' from the wall-average colour."""
    a = Eww[vis] / Eww[vis].mean() * share_ww
    b = Ecw[vis] / Ecw[vis].mean() * (1 - share_ww)

    def xy_of(lw, lc):
        X = XY["WW"][0] / XY["WW"][1] * lw + XY["CW"][0] / XY["CW"][1] * lc
        Z = (1 - sum(XY["WW"])) / XY["WW"][1] * lw + (1 - sum(XY["CW"])) / XY["CW"][1] * lc
        Y = lw + lc
        return X / (X + Y + Z), Y / (X + Y + Z)
    u, v = uv(*xy_of(a, b))
    u0, v0 = uv(*xy_of(share_ww, 1 - share_ww))
    return np.hypot(u - u0, v - v0).max()


def run(board_d, ring_r, depth, n_cct=4, n_rgb=1, open_r=None, rgb_box=True):
    open_r, z_cut = geom(board_d, open_r)
    th, X, nrm, dA = grid(open_r)
    z_led = z_cut - depth
    ww, cw, rgb = layout(n_cct, n_rgb, ring_r, z_led)
    box = None
    if rgb_box and n_rgb == 1:      # the centred RGB package shades the whites' low rays across the centre
        box = ((-RGB_HALF[0], RGB_HALF[0]), (-RGB_HALF[1], RGB_HALF[1]), (z_led - 0.7, z_led - 0.7 + RGB_H))
    vis = np.broadcast_to((th > math.radians(50))[:, None], X.shape[:-1])
    Eww, eta, fp = total(ww, X, nrm, dA, z_cut, open_r, box)
    Ecw, _, _ = total(cw, X, nrm, dA, z_cut, open_r, box)
    Eall, _, _ = total(np.vstack([ww, cw]), X, nrm, dA, z_cut, open_r, box)
    Ergb, _, _ = total(rgb, X, nrm, dA, z_cut, open_r)
    U = lambda E: E[vis].max() / E[vis].min()   # noqa: E731
    escape = 0.20 * eta / (1 - RHO * ((1 - fp) + RHO_PORT * fp))
    return U(Eww), U(Eall), U(Ergb), colour_spread(Eww, Ecw, vis), escape


if __name__ == "__main__":
    print(f"{'head':<36}{'depth':>6}{'1 CCT':>8}{'all W':>8}{'RGB':>7}{'4000K du_v_':>12}{'escape':>8}")
    for name, b, rr, nrgb, op, depths in (
            ("v0.2 as built: Ø18, opening r 9.0", 18, 5.8, 1, 9.0, (1.0, 1.2, 1.5, 2.0)),
            ("v0.2, opening r 8.3 (board - 0.7)", 18, 5.8, 1, 8.3, (1.2, 2.0, 2.9)),
            ("v0.1: Ø26, opening r 12.3, 2 RGB", 26, 8.0, 2, 12.3, (1.8, 2.9))):
        for dep in depths:
            u1, ua, ur, t, esc = run(b, rr, dep, n_rgb=nrgb, open_r=op)
            print(f"{name:<36}{dep:6.1f}{u1:8.3f}{ua:8.3f}{ur:7.3f}{t:12.4f}{esc:8.3f}", flush=True)
