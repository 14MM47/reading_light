"""Moon shell: 50 mm lithophane moon, lit from LEDs in its base.

Requirements (newest last; never renumber):
  B1  GIVEN    (Matt) a hollow model of the moon, ~5 cm diameter, lit fully from inside by LEDs
  B2  GIVEN    (Matt, answer 2) generated from NASA public-domain LRO data, not a scaled Thingiverse model
  B3  GIVEN    (Matt, answer 1) the LEDs sit in the base of the moon at the top of the neck
  B4  RULE     (optics model docs/design/optics, v0.1 head) bottom opening half-angle 30-35 deg, LED plane 1-2 mm below
               the opening plane gives max/min wall illuminance <= 1.05 (superseded by B13 for the v0.2 head)
  B5  RULE     (3dprint PLAN 11) lithophane wall >= 0.84 mm everywhere (2 perimeters), <= 2.6 mm
  B6  ASSUMED  dark maria and low ground thicker (darker), highlands and rims thinner: 75 % albedo, 25 % elevation
  B7  ASSUMED  (v0.1 head) a skirt below the opening carries 3 bayonet lugs into the LED base; its bottom face presses
               the PETG clamp ring onto the LED board edge band (superseded by B15/B16)
  B8  RULE     outer surface below 45 deg from the bottom pole is a 45 deg collar (designs that overhang out)
  B9  ASSUMED  printed upright on the skirt in white PLA; the inner dome closes without supports (moon-lamp practice)
  B10 ASSUMED  the near side (longitude 0) faces -Y, the lunar north pole is up
  B11 ASSUMED  the outer surface is a smooth 50.0 mm sphere; the lithophane relief is on the inside (crisp silhouette,
               exact diameter, clean outer perimeter)
  B12 RULE     (thermal review) the PLA moon never touches the LED board: a 0.6 mm PETG ring sits between them
  B13 RULE     (corrected optics model 2026-11-03, 18 mm LED board v0.2) opening r 9.0 on the inner sphere (half-angle
               ~23.7 deg); white emitters 1-2 mm below the opening plane (1.2 chosen): model max/min 1.011 one white,
               1.002 both whites, 1.037 RGB on the visible wall (docs/design/optics/head_v02.txt; the opening is the
               aperture, so deeper LEDs shade the low wall: 2.0 mm gives 1.055)
  B14 RULE     (no shadow) below the opening the bore is never narrower than the cone from the outermost emitter edge to
               the opening rim, so no LED ray that can pass the opening is clipped
  B15 ASSUMED  (v0.2 head) the base cup sits inside the moon's skirt (a slim stem instead of a wide cup): skirt 25.3 mm
               OD; bayonet turned inside out, grooves inside the skirt (roof = the 45 deg clamp cone, floor 45 deg with
               a cam), entry slots open at the skirt bottom; the 45 deg collar runs down onto the skirt (B8)
  B16 RULE     (B12, v0.2) the moon presses the PETG ring through a 45 deg cone on the ring's chamfer, 0.25 mm clear of
               the cup's matching 45 deg rim
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

SHIFT = -L.Z_SKIRT_BOT          # bake print orientation: skirt bottom on the bed (z=0)

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
    "skirt_fit": "skirt ID 21.1 mm over the 20.8 mm cup (0.15 radial): confirm with the bayonet coupon",
    "lug_engagement": "cup lugs 0.8 mm radial in the skirt grooves; 0.25 mm cam: confirm the moon locks firmly "
                      "without cracking the skirt and the board does not rattle",
}


def defaults_note():
    return "see _lib/moonlib.py"


def _skirt_profile():
    """(r, z) outline of the exact lower part (moon frame): skirt, clamp cone up to where it meets the inner sphere
    (the opening rim, a 67 deg ridge), the inner sphere (0.02 inside the lithophane's) up to Z_TRIM, where the
    lithophane (trimmed there) sits on its top face, then a band 0.2 mm inside the lithophane wall up to
    Z_CUT + 0.6 (overlap, no exposed seam: every face left at Z_TRIM faces up)."""
    zt = L.Z_CUT + 0.6
    if L.Z_BORE_BOT < L.Z_BORE_TOP - 0.1:                 # vertical bore from the clamp cone up to the sphere
        start, z0 = [(L.BORE_R, L.Z_BORE_BOT)], L.Z_BORE_TOP
    else:                                                 # the cone meets the sphere directly
        start, z0 = [], L.Z_RIDGE
    inner = start + [(math.sqrt(L.R_IN_EXACT ** 2 - z * z), z) for z in np.linspace(z0, L.Z_TRIM, 6)]
    r_in_t = math.sqrt(L.R_IN ** 2 - zt * zt) + 0.2
    band = [(math.sqrt(L.R_IN ** 2 - L.Z_TRIM ** 2) + 0.2, L.Z_TRIM), (r_in_t, zt), (L.COLLAR_K + zt - 0.2, zt),
            (L.COLLAR_K + L.Z_TRIM - 0.2, L.Z_TRIM), (L.COLLAR_K + L.Z_TRIM + 0.01, L.Z_TRIM)]
    return (inner + band +
            [(L.COLLAR_K + L.Z_CUT + 0.01, L.Z_CUT), (L.SKIRT_R_OUT, L.Z_COLLAR_SKIRT - 0.01),
             (L.SKIRT_R_OUT, L.Z_SKIRT_BOT), (L.SKIRT_R_IN, L.Z_SKIRT_BOT), (L.SKIRT_R_IN, L.CONE_C - L.SKIRT_R_IN)])


def lock_angle(k):
    """Moon-frame angle of lug k when locked (= its cup-frame angle: the moon is turned +BAYONET_TURN to lock)."""
    return L.LUG_ANGLES[k]


def part(*, n_lon=600, n_lat=300, albedo_w=0.75, smooth_px=3.5, gamma=1.0, seam_lon_deg=180.0):
    """Exact features in moon coordinates: skirt + clamp cone + bore, minus the bayonet grooves and entry slots."""
    m = _revolved(_skirt_profile(), 0.0, 360.0)
    span = math.degrees(L.LUG_W / L.LUG_R_OUT)           # lug width as an angle
    slot = math.degrees((L.LUG_W + 0.8) / L.SKIRT_R_IN)   # entry slot (0.4 clear each side)
    for k in range(L.LUG_N):
        a = lock_angle(k)
        # groove: flat at FLOOR_K_LOCK under the locked lug, ramping down (the cam) toward the entry slot at
        # a + turn; one lofted solid (no stacked steps, so no coincident faces)
        a0, a1 = a - span / 2 - 1.0, a + L.BAYONET_TURN_DEG + slot / 2 - 0.4   # ends inside the slot (no coplanar end)
        ramp0, ramp1 = a + span / 2, a + L.BAYONET_TURN_DEG - span / 2
        angles = list(np.linspace(a0, a1, 41))
        profiles = []
        for b in angles:
            t = min(1.0, max(0.0, (b - ramp0) / (ramp1 - ramp0)))
            profiles.append(L.groove_profile(L.FLOOR_K_LOCK + (L.FLOOR_K_OPEN - L.FLOOR_K_LOCK) * t))
        m = m - _loft_revolve(profiles, angles)
        # entry slot: straight up from below the bed to the roof (the clamp cone extended, 45 deg)
        r0 = L.SKIRT_R_IN - 0.05
        c = L.CONE_C + 0.03
        prof = [(r0, L.Z_SKIRT_BOT - 0.2), (L.GROOVE_R, L.Z_SKIRT_BOT - 0.2), (L.GROOVE_R, c - L.GROOVE_R), (r0, c - r0)]
        m = m - _revolved(prof, a + L.BAYONET_TURN_DEG - slot / 2, slot)
    return as_manifold(m).translate((0, 0, SHIFT))


def _loft_revolve(profiles, angles_deg):
    """Watertight solid through (r, z) profiles (same point count, counter-clockwise or not) placed at the given
    angles about Z: rings joined by quads, the two ends capped."""
    n = len(profiles[0])
    V, F = [], []
    for prof, a in zip(profiles, angles_deg):
        pts = list(prof)
        area2 = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))
        if area2 < 0:
            pts = pts[::-1]
        c, s_ = math.cos(math.radians(a)), math.sin(math.radians(a))
        V += [(r * c, r * s_, z) for r, z in pts]
    rings = len(angles_deg)
    for i in range(rings - 1):
        for j in range(n):
            a0, a1 = i * n + j, i * n + (j + 1) % n
            b0, b1 = a0 + n, a1 + n
            F += [(a0, b1, a1), (a0, b0, b1)]
    for j in range(1, n - 1):                             # end caps (convex profiles)
        F.append((0, j + 1, j))
        last = (rings - 1) * n
        F.append((last, last + j, last + j + 1))
    t = trimesh.Trimesh(np.array(V), np.array(F), process=True)
    trimesh.repair.fix_winding(t)                         # one consistent winding (caps and sides)
    if t.volume < 0:
        t.invert()
    return as_manifold(t)


def _revolved(profile, a0_deg, span_deg, n=None):
    """Manifold of an (r, z) profile revolved from a0 over span (degrees), built directly in manifold3d."""
    segs = n or max(8, int(abs(span_deg) / 1.5))
    pts = [(float(r), float(z)) for r, z in profile]
    area2 = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))
    cs = mf.CrossSection([pts if area2 > 0 else pts[::-1]])     # counter-clockwise for the positive fill rule
    solid = mf.Manifold.revolve(cs, segs, float(span_deg))
    return solid.rotate((0.0, 0.0, float(a0_deg)))


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
    big = mf.Manifold.cube((200, 200, 200)).translate((-100, -100, L.Z_ORG_TRIM))
    return {"add": [(as_manifold(shell) ^ big).translate((0, 0, SHIFT))], "cut": []}


def context(p):
    """LED board (grey) and PETG ring in their clamped positions, for clear_of checks."""
    board = mf.Manifold.cylinder(L.BOARD_T, L.BOARD_R, L.BOARD_R, 96).translate((0, 0, L.Z_BOARD_BOT + SHIFT))
    ring = (mf.Manifold.cylinder(L.RING_T - 0.05, L.RING_R_OUT - L.RING_CHAMFER, L.RING_R_OUT - L.RING_CHAMFER, 96)
            - mf.Manifold.cylinder(L.RING_T, L.RING_R_IN, L.RING_R_IN, 96).translate((0, 0, -0.1))
            ).translate((0, 0, L.Z_BOARD_TOP + SHIFT))
    return {"led_board": board, "ring_core": ring}


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
    # B13: opening and LED depth (v0.2); B14: nothing solid inside the emitter-to-opening cone
    ang = L.opening_half_angle_deg()
    out.append(claim("B13", "opening r 9.0 on the inner sphere (half-angle 22-25 deg)", 22.0 <= ang <= 25.0, round(ang, 2)))
    out.append(claim("B14", "bore under the opening >= 0.5 mm tall (blunt lip, no knife edge)",
                     L.Z_BORE_TOP - L.Z_BORE_BOT >= 0.5, round(L.Z_BORE_TOP - L.Z_BORE_BOT, 3)))
    out.append(claim("B13", "white emitters 1-2 mm below the opening plane", 1.0 <= L.LED_DEPTH <= 2.0, L.LED_DEPTH))
    probes = [[(L.emitter_cone_r(z) - 0.02) * math.cos(a), (L.emitter_cone_r(z) - 0.02) * math.sin(a), z + SHIFT]
              for z in np.linspace(L.Z_EMIT + 0.05, L.Z_CUT - 0.02, 9) for a in np.linspace(0, 2 * math.pi, 24, endpoint=False)]
    hit = int(np.asarray(m.contains(probes)).sum())
    out.append(claim("B14", "no material inside the emitter-to-opening cone (9 heights x 24 angles)", hit == 0, hit))
    out.append(claim("B14", "bore radius >= the opening radius", L.BORE_R >= L.OPEN_R - 1e-9, L.BORE_R))
    # B16: the cone bears on the ring's chamfer, and its clearance to the cup's 45 deg rim
    out.append(claim("B16", "clamp cone passes through the ring chamfer",
                     abs(L.CONE_C - (L.RING_R_OUT - L.RING_CHAMFER + L.Z_RING_TOP)) < 1e-9, round(L.CONE_C, 3)))
    out.append(claim("B16", "cone 0.25 mm clear of the cup rim (perpendicular)",
                     abs((L.CONE_C - L.TOP_C) / math.sqrt(2) - L.GAP_45) < 1e-9, round((L.CONE_C - L.TOP_C) / math.sqrt(2), 3)))
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
    out.append(claim("B15", "skirt bottom on the bed (z=0)", abs(lo[2]) < 1e-3, round(float(lo[2]), 3)))
    out.append(claim("B15", "skirt OD 25.3 mm (cup inside it)", abs(2 * L.SKIRT_R_OUT - 25.3) < 0.05, 2 * L.SKIRT_R_OUT))
    r_g = (L.SKIRT_R_IN + L.GROOVE_R) / 2
    a = math.radians(lock_angle(0))
    zg = (L.FLOOR_K_LOCK + L.CONE_C) / 2 + 0.0 + SHIFT     # mid-height of the groove at r_g
    zg = ((L.FLOOR_K_LOCK + r_g) + (L.CONE_C - r_g)) / 2 + SHIFT
    open_at_lock = not bool(m.contains([[r_g * math.cos(a), r_g * math.sin(a), zg]])[0])
    out.append(claim("B15", "groove open where the locked lug sits", open_at_lock))
    return out
