"""Moon shell: 50 mm lithophane moon, lit from LEDs in its base.

Requirements (newest last; never renumber):
  B1  GIVEN    (Matt) a hollow model of the moon, ~5 cm diameter, lit fully from inside by LEDs
  B2  GIVEN    (Matt, answer 2) generated from NASA public-domain LRO data, not a scaled Thingiverse model
  B3  GIVEN    (Matt, answer 1) the LEDs sit in the base of the moon at the top of the neck
  B4  RULE     (optics model docs/design/optics) bottom opening half-angle 30-35 deg, LED plane 1-3 mm below the
               opening plane gives max/min wall illuminance <= 1.05 (integrating-sphere geometry)
  B5  RULE     (3dprint PLAN 11) lithophane wall >= 0.84 mm everywhere (2 perimeters), <= 2.6 mm
  B6  ASSUMED  dark maria and low ground thicker (darker), highlands and rims thinner: 75 % albedo, 25 % elevation
  B7  ASSUMED  a 1.5 mm skirt below the opening (full width of the cut circle) carries 3 bayonet lugs into the LED
               base; its bottom face presses the PETG clamp ring onto the LED board edge band (B12)
  B8  RULE     outer surface below 45 deg from the bottom pole is a 45 deg collar (designs that overhang out)
  B9  ASSUMED  printed upright on the skirt in white PLA; the inner dome closes without supports (moon-lamp practice)
  B10 ASSUMED  the near side (longitude 0) faces -Y, the lunar north pole is up
  B11 ASSUMED  the outer surface is a smooth 50.0 mm sphere; the lithophane relief is on the inside (crisp silhouette,
               exact diameter, clean outer perimeter)
  B12 RULE     (thermal review) the PLA moon never touches the LED board: a 0.6 mm PETG ring sits between them
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import manifold3d as mf
import numpy as np
import trimesh
from PIL import Image
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).parent))
from _lib import moonlib as L  # noqa: E402
from _lib.meshkit import as_manifold, claim  # noqa: E402

SHIFT = L.SKIRT_H - L.Z_CUT    # bake print orientation: skirt bottom on the bed (z=0)

ASSETS = Path(__file__).resolve().parents[1] / "assets" / "moon"

PRINT = {
    "material": "pla-basic-white",
    "process": "0.12-fine",          # finer layers resolve the lithophane; see print/README
    "supports": "none",
    "supported": [{"why": "inner dome closure at the north pole: a <= 8 mm bridge, no support material (none could "
                          "be removed from inside a closed sphere)", "z": (40.0, 48.0), "r": (0.0, 4.0),
                   "support_material": False}],
    "orientation": "as-modelled",
    "slicer_overrides": {"wall_loops": 6, "sparse_infill_density": "100%", "top_shell_layers": 0,
                         "bottom_shell_layers": 3, "seam_position": "back", "brim_type": "outer_only",
                         "brim_width": 3},
    "overrides": {
        "overhang_max": {"value": 82.0,
                         "why": "inside of a closed hollow sphere: supports could never be removed; the dome "
                                "closes 0.2 mm per layer over a >=0.9 mm wall (each layer overlaps the one below "
                                "for theta_top >= 13 deg) and the last ~7 mm opening is a short bridge; this is how "
                                "every printed moon lamp is made. The outer surface is held to 45 deg by claim B8, so this "
                                "override only admits the interior. VERIFY with the slicer preview and the first print."},
    },
}

VERIFY = {
    "lithophane_range": "0.9-2.6 mm in white PLA at 0.12 mm layers: confirm contrast on the first print",
    "skirt_fit": "skirt OD 33.4 mm into a 33.7 mm base bore (0.15 radial): confirm with the fit coupon",
    "lug_engagement": "bayonet lugs 0.8 mm radial; confirm they lock without cracking the skirt",
}


def defaults_note():
    return "see _lib/moonlib.py"


def part(*, n_lon=600, n_lat=300, albedo_w=0.75, smooth_px=3.5, gamma=1.0, seam_lon_deg=180.0):
    """Exact features: skirt + bayonet lugs (manifold primitives), in moon coordinates (centre at 0)."""
    z0 = L.Z_CUT - L.SKIRT_H
    ring = (mf.Manifold.cylinder(L.SKIRT_H + 0.6, L.SKIRT_R_OUT, L.SKIRT_R_OUT, 233)
            - mf.Manifold.cylinder(L.SKIRT_H + 1.0, L.SKIRT_R_IN, L.SKIRT_R_IN, 211).translate((0, 0, -0.2))
            ).translate((0, 0, z0))
    lugs = []
    span = math.degrees(L.LUG_W / L.SKIRT_R_OUT)
    for k in range(L.LUG_N):
        lugs.append(_revolved(L.lug_profile(z0), 90.37 + k * 360 / L.LUG_N - span / 2, span))
    m = ring
    for g in lugs:
        m = m + g
    return m.translate((0, 0, SHIFT))


def _revolved(profile, a0_deg, span_deg):
    """Manifold of an (r, z) profile revolved from a0 over span (degrees)."""
    from build123d import Axis, BuildPart, BuildSketch, Plane, Polygon, revolve
    with BuildPart() as bp:
        with BuildSketch(Plane.XZ):
            Polygon(*profile, align=None)
        revolve(axis=Axis.Z, revolution_arc=span_deg)
    solid = bp.part.rotate(Axis.Z, a0_deg)
    return as_manifold(solid)


def _maps(smooth_px, albedo_w, gamma):
    col = np.asarray(Image.open(ASSETS / "lroc_color_2k.jpg").convert("L"), float) / 255.0
    dem = np.asarray(Image.open(ASSETS / "ldem_4.tif"), float)
    dem = np.asarray(Image.fromarray(dem.astype(np.float32)).resize(col.shape[::-1], Image.BILINEAR), float)
    col = ndimage.gaussian_filter(col, smooth_px, mode="wrap")
    dem = ndimage.gaussian_filter(dem, smooth_px, mode="wrap")
    a = np.clip((col - np.percentile(col, 1)) / (np.percentile(col, 99.5) - np.percentile(col, 1)), 0, 1)
    e = np.clip((dem - np.percentile(dem, 1)) / (np.percentile(dem, 99) - np.percentile(dem, 1)), 0, 1)
    dark = albedo_w * (1 - a) + (1 - albedo_w) * (1 - e)      # 1 = thickest
    return np.clip(dark, 0, 1) ** gamma


def _sample(img, lon, lat):
    h, w = img.shape
    u = ((lon + math.pi) / (2 * math.pi)) * w - 0.5
    v = ((math.pi / 2 - lat) / math.pi) * h - 0.5
    return ndimage.map_coordinates(img, [np.clip(v, 0, h - 1), np.mod(u, w)], order=1, mode="grid-wrap")


def thickness_field(p):
    """(theta, phi, t): polar angle from the bottom pole, azimuth (before the B10 rotation), wall thickness (mm)."""
    return _field(p)[:3]


def _field(p):
    dark = _maps(p.smooth_px, p.albedo_w, p.gamma)
    th0 = math.radians(L.opening_half_angle_deg() - 6)       # start a little below the cut; trimmed later
    th = np.linspace(th0, math.pi, p.n_lat)                    # polar angle from the bottom pole
    ph = np.linspace(0, 2 * math.pi, p.n_lon, endpoint=False)
    T, P = np.meshgrid(th, ph, indexing="ij")
    lat = T - math.pi / 2                                      # bottom pole = south (-90)
    lon = np.mod(P - math.pi / 2 + math.pi, 2 * math.pi) - math.pi   # lon 0 at phi=90deg... rotated below
    d = _sample(dark, lon.ravel(), lat.ravel()).reshape(T.shape)
    # blend to full thickness near the opening (collar band) and keep the pole cap smooth
    deg = np.degrees(T)
    w = np.clip((deg - 40.0) / 10.0, 0, 1)
    # upper interior: the dome already overhangs (theta-90 deg); soften the relief there so relief + dome stays
    # under ~80 deg (micro-overhangs of the inner surface, B9). Amplitude 1.0 below 120 deg -> 0.4 at 165 deg.
    amp = 1.0 - 0.6 * np.clip((deg - 120.0) / 45.0, 0, 1)
    d = 0.5 + (d - 0.5) * amp
    t = L.T_MIN + (L.T_MAX - L.T_MIN) * (w * d + (1 - w) * 1.0)
    # north-pole cap: the equirectangular map degenerates there; blend to the ring-average thickness at 168 deg
    k = int(np.searchsorted(th, math.radians(168.0)))
    t_cap = float(t[k].mean())
    wp = np.clip((deg - 168.0) / 6.0, 0, 1)
    t = (1 - wp) * t + wp * t_cap
    # slope limiter (B9): going up the dome, the wall may thicken no faster than keeps the inner facet's
    # overhang (dome angle theta-90 plus relief slope) <= 80 deg. One forward pass in theta.
    ds = (L.R_OUT - L.T_MAX) * (th[1] - th[0])
    beta = np.radians(np.clip(80.0 - np.maximum(deg[:, 0] - 90.0, 0.0), 0.5, 80.0))
    lim = np.tan(beta) * ds
    for i in range(1, len(th)):
        t[i] = np.minimum(t[i], t[i - 1] + lim[i - 1])
    return th, ph, t, T, P, deg


def organic(p):
    """Textured lithophane shell, trimmed at the opening plane, plus the 45 deg outer collar."""
    th, ph, t, T, P, deg = _field(p)
    r_in = L.R_OUT - t                                         # relief on the inside (B11)
    r_out = np.full_like(t, L.R_OUT)
    # outer collar: r_out at least the 45deg cone tangent to R_OUT at theta=45deg (B8)
    cone = L.R_OUT / np.maximum(np.cos(T - math.radians(45.0)), 1e-6)   # line tangent at 45deg in (r,z) plane
    r_out = np.where(deg < 45.0, np.maximum(r_out, np.minimum(cone, L.R_OUT * 1.2)), r_out)

    def grid(R):
        x = R * np.sin(T) * np.cos(P)
        y = R * np.sin(T) * np.sin(P)
        z = -R * np.cos(T)
        return np.stack([x, y, z], -1)

    Vo = grid(r_out)
    Vi = grid(r_in)
    nl, nm = T.shape
    # vertices: outer rings (excluding last ring = top pole), outer pole, inner rings, inner pole
    vo = Vo[:-1].reshape(-1, 3)
    vi = Vi[:-1].reshape(-1, 3)
    pole_o = np.array([[0, 0, r_out[-1].mean()]])
    pole_i = np.array([[0, 0, r_in[-1].mean()]])
    V = np.vstack([vo, pole_o, vi, pole_i])
    no = len(vo)
    io = no + 1
    ii0 = io
    ipole = io + len(vi)

    def idx(off, i, j):
        return off + i * nm + (j % nm)

    F = []
    rings = nl - 1
    for i in range(rings - 1):
        for j in range(nm):
            a, b, c, d2 = idx(0, i, j), idx(0, i, j + 1), idx(0, i + 1, j + 1), idx(0, i + 1, j)
            F += [(a, c, b), (a, d2, c)]                     # outer faces point outward
            a, b, c, d2 = idx(ii0, i, j), idx(ii0, i, j + 1), idx(ii0, i + 1, j + 1), idx(ii0, i + 1, j)
            F += [(a, b, c), (a, c, d2)]                     # inner faces point inward
    last = rings - 1
    for j in range(nm):
        F.append((idx(0, last, j), no, idx(0, last, j + 1)))
        F.append((idx(ii0, last, j), idx(ii0, last, j + 1), ipole))
    for j in range(nm):                                       # bottom band joins outer and inner rings
        F += [(idx(0, 0, j), idx(0, 0, j + 1), idx(ii0, 0, j + 1)), (idx(0, 0, j), idx(ii0, 0, j + 1), idx(ii0, 0, j))]
    shell = trimesh.Trimesh(V, np.array(F), process=True)
    if shell.volume < 0:
        shell.invert()
    # rotate so the near side (lon 0) faces -Y (B10)
    shell.apply_transform(trimesh.transformations.rotation_matrix(math.radians(p.seam_lon_deg), (0, 0, 1)))
    # trim at the opening plane
    big = mf.Manifold.cube((200, 200, 200)).translate((-100, -100, L.Z_CUT))
    return {"add": [(as_manifold(shell) ^ big).translate((0, 0, SHIFT))], "cut": []}


def context(p):
    """LED board (grey), sitting at the skirt's bottom edge, for clear_of checks."""
    z_top = L.Z_CUT - L.SKIRT_H - L.RING_T - 0.05
    return {"led_board": mf.Manifold.cylinder(L.BOARD_T, L.BOARD_R, L.BOARD_R, 96).translate(
        (0, 0, z_top - L.BOARD_T + SHIFT))}


def spec(m, p):
    lo, hi = m.bounds
    dia = hi[0] - lo[0], hi[1] - lo[1]
    mesh = m.mesh
    cen = mesh.triangles_center - np.array([0, 0, SHIFT])
    rad = np.linalg.norm(cen, axis=1)
    outer = (rad > L.R_OUT - 0.05) & (cen[:, 2] > -L.R_OUT * math.cos(math.radians(46.0)))
    out = [claim("B1", "outer sphere diameter 50.0 +/- 0.1 mm", abs(2 * rad[outer].max() - 50.0) <= 0.1,
                 round(float(2 * rad[outer].max()), 3))]
    nz = mesh.face_normals[:, 2]
    ang = np.degrees(np.arcsin(np.clip(-nz, -1, 1)))
    shell_outer = (rad > L.R_OUT - 0.3) & (cen[:, 2] > L.Z_CUT + 0.05)
    worst = float(ang[shell_outer].max())
    out.append(claim("B8", "outer surface overhang <= 45 deg", worst <= 45.5, round(worst, 2)))
    # B4: opening half-angle and LED plane depth
    ang = L.opening_half_angle_deg()
    out.append(claim("B4", "opening half-angle 28-35 deg", 28 <= ang <= 35, round(ang, 2)))
    led_dz = -(L.SKIRT_H + L.RING_T - 0.7)
    out.append(claim("B4", "LED plane 1-3 mm below the opening plane", -3.0 <= led_dz <= -1.0, round(led_dz, 2)))
    # B5: thickness along radial rays at sampled directions (above the collar band)
    rng = np.random.default_rng(3)
    ok, n, tmin, tmax = 0, 200, 9.0, 0.0
    for _ in range(n):
        th = math.radians(rng.uniform(55, 175))
        ph = rng.uniform(0, 2 * math.pi)
        d = np.array([math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), -math.cos(th)])
        centre = np.array([0, 0, SHIFT])
        tt = m.thickness_along(centre + d * 30.0, -d)
        tmin, tmax = min(tmin, tt), max(tmax, tt)
        ok += (0.84 <= tt <= L.T_MAX + 0.1)
    out.append(claim("B5", f"radial wall 0.84-2.7 mm at sampled points ({ok}/{n})", ok == n, [round(tmin, 3), round(tmax, 3)]))
    out.append(claim("B7", "skirt + 3 lugs present (bottom ring at z=0)", abs(lo[2]) < 1e-3, round(float(lo[2]), 3)))
    return out
