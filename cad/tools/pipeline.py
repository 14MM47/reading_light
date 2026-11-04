"""Local CAD build pipeline for reading_light parts.

It follows the 14MM47/3dprint part-module contract (PLAN §4): a part module has a docstring with
`B<n> GIVEN|ASSUMED|RULE` requirement lines, `PRINT`, `VERIFY`, `part(**kw)` (exact build123d solid or
None), optional `organic(p)` (mesh pieces), `context(p)` and `spec(m, p)` (claims). When the 3dprint
pipeline lands (its task A1), these modules can move there unchanged; until then this script
implements the same stages:

  load -> part -> organic -> mesh -> spec -> check -> verdict -> views

Usage:
  python -m cad.tools.pipeline cad/parts/<part>.py [--out print/<part>] [--no-views]
Exit 0 = PASS, 1 = FAIL, 2 = error. Never relaxes a check; per-part overrides need a `why`.
"""
from __future__ import annotations

import argparse
import importlib.util
import inspect
import json
import math
import sys
import time
import types
from dataclasses import dataclass, field
from pathlib import Path

import manifold3d as mf
import numpy as np
import trimesh

# thresholds (3dprint PLAN §4.4 / X2D rules); per-part overrides come from PRINT["overrides"]
CHECKS = {
    "bed_xy": 246.0, "bed_z": 260.0,
    "wall_fail": 0.84, "wall_warn": 1.2,
    "overhang_max": 45.0,
    "bridge_max": 20.0,
    "first_layer_warn": 400.0,
    "tall_thin": 8.0,
}
# ------------------------------------------------------------------ helpers
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "parts"))
from _lib.meshkit import Claim, as_manifold, claim, solid_to_trimesh, to_manifold, to_trimesh  # noqa: E402,F401


def stage(name):
    print(f"LIVE-STAGE {name}", flush=True)


@dataclass
class Measured:
    mesh: trimesh.Trimesh
    extra: dict = field(default_factory=dict)

    @property
    def bounds(self):
        return self.mesh.bounds

    def contains(self, pts):
        return self.mesh.contains(np.atleast_2d(pts))

    def thickness_along(self, origin, direction, max_len=50.0):
        """Length of material along a ray starting outside the part (first entry to first exit)."""
        o = np.asarray(origin, float)[None]
        d = np.asarray(direction, float)[None]
        d = d / np.linalg.norm(d)
        loc, idx_ray, _ = self.mesh.ray.intersects_location(o, d, multiple_hits=True)
        if len(loc) < 2:
            return 0.0
        t = np.sort(((loc - o) @ d.T).ravel())
        return float(t[1] - t[0])


# ------------------------------------------------------------------- checks
def check_mesh(m: trimesh.Trimesh, P: dict, contexts: dict, sample_walls=6000, seed=1):
    ov = {k: v["value"] for k, v in P.get("overrides", {}).items()}
    th = dict(CHECKS, **ov)
    res = []

    def add(name, severity, value, limit, hint=""):
        res.append({"source": "check", "name": name, "severity": severity, "value": value, "limit": limit, "hint": hint})

    wt = bool(m.is_watertight and m.is_volume)
    add("watertight", "ok" if wt else "fail", wt, True)
    lo, hi = m.bounds
    ext = hi - lo
    sev = "ok"
    if max(ext[0], ext[1]) > th["bed_xy"] or ext[2] > th["bed_z"]:
        sev = "fail"
    elif max(ext[0], ext[1]) > th["bed_xy"] - 10 or ext[2] > th["bed_z"] - 10:
        sev = "warn"
    add("bed_fit", sev, [round(float(e), 2) for e in ext], [th["bed_xy"], th["bed_xy"], th["bed_z"]])
    add("on_bed", "ok" if abs(lo[2]) < 1e-3 else "fail", round(float(lo[2]), 4), 0.0,
        "model must be baked in print orientation, lowest point at z=0")

    # wall thickness: rays inward from sampled facet centroids (area-weighted)
    rng = np.random.default_rng(seed)
    areas = m.area_faces
    # sample only facets with area: a revolve or boolean can leave a few zero-area slivers, and sampling without
    # replacement needs at least n non-zero weights (else numpy raises instead of checking the part)
    nz = areas > 0
    n = min(sample_walls, int(nz.sum()))
    idx = rng.choice(len(m.faces), n, replace=False, p=areas / areas.sum())
    # ... plus facets drawn uniformly per facet (round 3): a thin feature with little area (a 0.03 mm lip at the
    # moon's groove roofs) is made of many small facets, so area weighting alone almost never samples it
    n_f = min(10 * sample_walls, int(nz.sum()))
    idx_f = rng.choice(np.flatnonzero(nz), n_f, replace=False)
    idx = np.union1d(idx, idx_f)
    n = len(idx)
    c = m.triangles_center[idx]
    d = -m.face_normals[idx]
    origins = c + d * 1e-3
    loc, ri, ti = m.ray.intersects_location(origins, d, multiple_hits=False)
    thick = np.full(n, np.inf)
    if len(ri):
        dist = np.linalg.norm(loc - origins[ri], axis=1)
        # skip rays that exit through a face sharing a vertex with the entry facet (corners)
        entry = m.faces[idx[ri]]
        hitf = m.faces[ti]
        share = (entry[:, :, None] == hitf[:, None, :]).any(axis=(1, 2))
        dist = np.where(share, np.inf, dist)
        thick[ri] = dist
    keep = areas[idx] > 1e-3
    thick = thick[keep]
    where = c[keep]
    wmin = float(np.min(thick)) if len(thick) else float("inf")
    at = where[int(np.argmin(thick))].round(2).tolist() if len(thick) else None
    p01 = float(np.percentile(thick[np.isfinite(thick)], 1)) if np.isfinite(thick).any() else float("inf")
    sev = "fail" if wmin < th["wall_fail"] else ("warn" if wmin < th["wall_warn"] else "ok")
    add(f"wall_min:{th['wall_fail']}", sev, round(wmin, 3), th["wall_fail"],
        f"at {at}; 1st percentile {p01:.3f} mm over {n} samples")
    res[-1]["at"] = at

    # overhangs: downward-facing facets steeper than the limit, ignoring the bed contact layer
    nz = m.face_normals[:, 2]
    zc = m.triangles_center[:, 2]
    ang = np.degrees(np.arcsin(np.clip(-nz, -1, 1)))     # 0 = vertical wall, 90 = flat ceiling
    over = (ang > th["overhang_max"] + 0.5) & (zc > 0.25) & (areas > 1e-4)
    # bridges: connected flat ceilings (> 80 deg) whose narrowest span is <= bridge_max are bridges, not overhangs
    flat = over & (ang > 80.0)
    bridge_spans = []
    if flat.any():
        import networkx as nx
        from shapely.geometry import MultiPoint
        idx_flat = set(np.nonzero(flat)[0].tolist())
        g = nx.Graph()
        g.add_nodes_from(idx_flat)
        for a, b in m.face_adjacency:
            if a in idx_flat and b in idx_flat:
                g.add_edge(a, b)
        for comp in nx.connected_components(g):
            comp = np.fromiter(comp, int)
            pts = m.vertices[m.faces[comp]].reshape(-1, 3)[:, :2]
            rect = MultiPoint([tuple(q) for q in pts]).minimum_rotated_rectangle
            xs, ys = rect.exterior.coords.xy
            sides = [math.dist((xs[k], ys[k]), (xs[k + 1], ys[k + 1])) for k in range(2)]
            span = min(sides) if min(sides) > 0 else max(sides)
            if span <= th["bridge_max"]:
                over[comp] = False
                bridge_spans.append(round(span, 2))
    zones = P.get("supported", [])
    in_zone = np.zeros(len(m.faces), bool)
    for zn in zones:
        zlo, zhi = zn["z"]
        r_lo, r_hi = zn.get("r", (0, 1e9))
        rr = np.hypot(m.triangles_center[:, 0], m.triangles_center[:, 1])
        in_zone |= (zc >= zlo - 0.2) & (zc <= zhi + 0.2) & (rr >= r_lo - 0.2) & (rr <= r_hi + 0.2)
    out_area = float(areas[over & ~in_zone].sum())
    in_area = float(areas[over & in_zone].sum())
    bad = over & ~in_zone
    worst = float(ang[bad].max()) if bad.any() else None
    at = m.triangles_center[bad][np.argmax(areas[bad])].round(2).tolist() if bad.any() else None
    add(f"overhang_max:{th['overhang_max']}", "fail" if out_area > 0.5 else "ok", worst, th["overhang_max"],
        f"{out_area:.1f} mm^2 outside supported zones; largest facet at {at}")
    res[-1]["at"] = at
    if in_area > 0:
        add("supported_zones", "warn", round(in_area, 1), None, "; ".join(z["why"] for z in zones))
    add(f"bridge_max:{th['bridge_max']}", "ok", max(bridge_spans) if bridge_spans else None, th["bridge_max"],
        f"{len(bridge_spans)} flat ceilings treated as bridges")

    # first-layer contact
    bed = (nz < -0.999) & (zc < 0.05)
    fl = float(areas[bed].sum())
    add("first_layer_contact", "warn" if fl < th["first_layer_warn"] else "ok", round(fl, 1), th["first_layer_warn"],
        "consider a brim" if fl < th["first_layer_warn"] else "")
    hw = ext[2] / max(1e-6, min(ext[0], ext[1]))
    add("tall_thin", "warn" if hw > th["tall_thin"] else "ok", round(float(hw), 2), th["tall_thin"])

    for name, cm in contexts.items():
        try:
            inter = as_manifold(m) ^ as_manifold(cm)
            vol = float(inter.volume())
        except Exception as e:     # noqa: BLE001
            vol = float("nan")
            add(f"clear_of:{name}", "fail", str(e), 0.0)
            continue
        add(f"clear_of:{name}", "fail" if vol > 1e-3 else "ok", round(vol, 4), 0.0, "intersection volume mm^3")
    return res


# -------------------------------------------------------------------- views
def render(m: trimesh.Trimesh, path: Path, eye=(1.0, -1.4, 0.8), size=900, ctx=None, title=""):
    """Ray-cast render (orthographic, first hit, Lambert + ambient); context bodies in grey."""
    from PIL import Image, ImageDraw
    eye = np.asarray(eye, float)
    eye = eye / np.linalg.norm(eye)
    fwd = -eye
    up = np.array([0, 0, 1.0])
    right = np.cross(fwd, up)
    if np.linalg.norm(right) < 1e-6:
        right = np.array([1.0, 0, 0])
    right /= np.linalg.norm(right)
    up2 = np.cross(right, fwd)
    meshes = [m] + list(ctx or [])
    scene = trimesh.util.concatenate(meshes)
    owner = np.concatenate([np.full(len(mm.faces), i) for i, mm in enumerate(meshes)])
    ctr = (scene.bounds[0] + scene.bounds[1]) / 2
    ext = max(np.ptp(scene.vertices @ right), np.ptp(scene.vertices @ up2)) * 1.08
    px = ext / size
    u = (np.arange(size) - size / 2 + 0.5) * px
    U, Vv = np.meshgrid(u, -u)
    origins = ctr + U[..., None] * right + Vv[..., None] * up2 - fwd * (np.linalg.norm(np.ptp(scene.vertices, 0)) * 2)
    o = origins.reshape(-1, 3)
    d = np.tile(fwd, (len(o), 1))
    tri, ray, loc = scene.ray.intersects_id(o, d, multiple_hits=False, return_locations=True)
    img = np.full((size * size, 3), 252.0)
    light = np.array([0.35, -0.45, 0.85])
    light /= np.linalg.norm(light)
    n = scene.face_normals[tri]
    n = np.where((n @ fwd)[:, None] > 0, -n, n)
    sh = 0.30 + 0.70 * np.clip(n @ light, 0, 1) * 0.8 + 0.2 * np.clip(n @ eye, 0, 1)
    depth = (loc - o[ray]) @ fwd
    if len(depth):
        dn = (depth - depth.min()) / max(1e-6, np.ptp(depth))
        sh = sh * (1.0 - 0.45 * dn)          # depth cueing: deeper surfaces darker
    base = np.where((owner[tri] == 0)[:, None], np.array([236, 232, 220.0]), np.array([150, 152, 165.0]))
    img[ray] = base * sh[:, None]
    # silhouette / step edges: depth discontinuities
    dimg = np.full(size * size, np.nan)
    dimg[ray] = depth
    dimg = dimg.reshape(size, size)
    gy = np.abs(np.diff(dimg, axis=0, prepend=dimg[:1]))
    gx = np.abs(np.diff(dimg, axis=1, prepend=dimg[:, :1]))
    edge = (np.nan_to_num(gx, nan=9) > 0.4) | (np.nan_to_num(gy, nan=9) > 0.4)
    img = img.reshape(size, size, 3)
    img[edge & ~np.isnan(dimg)] *= 0.35
    img = img.reshape(-1, 3)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8).reshape(size, size, 3))
    if title:
        ImageDraw.Draw(im).text((10, 10), title, fill=(40, 40, 40))
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path)


# --------------------------------------------------------------------- main
def load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    spec.loader.exec_module(mod)
    return mod


def defaults(fn):
    return {k: v.default for k, v in inspect.signature(fn).parameters.items() if v.default is not inspect._empty}


def build(path: Path, out: Path, views=True, kw=None):
    t0 = time.time()
    stage("load")
    mod = load_module(path)
    p = types.SimpleNamespace(**dict(defaults(mod.part), **(kw or {})))
    stage("part")
    solid = mod.part(**vars(p))
    pieces = []
    if solid is not None:
        pieces.append(as_manifold(solid))
    stage("organic")
    cuts = []
    if hasattr(mod, "organic"):
        org = mod.organic(p) or {}
        for piece in org.get("add", []):
            pieces.append(as_manifold(piece))
        cuts = [as_manifold(c) for c in org.get("cut", [])]
    stage("mesh")
    man = pieces[0]
    for pc in pieces[1:]:
        man = man + pc
    for c in cuts:
        man = man - c
    m = to_trimesh(man)
    out.mkdir(parents=True, exist_ok=True)
    stl = out / f"{path.stem}.stl"
    m.export(stl)
    stage("spec")
    meas = Measured(m)
    claims = mod.spec(meas, p) if hasattr(mod, "spec") else []
    stage("check")
    ctx = mod.context(p) if hasattr(mod, "context") else {}
    ctx_meshes = {k: (v if isinstance(v, trimesh.Trimesh) else to_trimesh(as_manifold(v))) for k, v in ctx.items()}
    checks = check_mesh(m, mod.PRINT, ctx_meshes)
    stage("verdict")
    fail = [c for c in claims if not c.ok] + [c for c in checks if c["severity"] == "fail"]
    verdict = "PASS" if not fail else "FAIL"
    diag = {"part": path.stem, "verdict": verdict, "seconds": round(time.time() - t0, 1),
            "volume_mm3": round(float(m.volume), 1), "bounds": m.bounds.round(3).tolist(),
            "faces": int(len(m.faces)), "print": mod.PRINT, "verify": mod.VERIFY,
            "claims": [vars(c) for c in claims], "checks": checks}
    (out / "diagnostics.json").write_text(json.dumps(diag, indent=1, default=str))
    for c in claims:
        print(f"  {'ok  ' if c.ok else 'FAIL'} {c.req} {c.text}  {c.value if c.value is not None else ''}")
    for c in checks:
        print(f"  {c['severity']:<4} {c['name']:<34} {c['value']}  {c['hint']}")
    if views:
        stage("views")
        render(m, out / "views" / "shaded_iso.png", title=f"{path.stem} {verdict}",
               ctx=list(ctx_meshes.values()))
        render(m, out / "views" / "shaded_under.png", eye=(0.6, -0.8, -0.9), title=f"{path.stem} underside")
    print(f"verdict {verdict}  ({diag['seconds']} s, {len(m.faces)} faces, {m.volume:.0f} mm^3)")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("part")
    ap.add_argument("--out", default=None)
    ap.add_argument("--no-views", action="store_true")
    a = ap.parse_args()
    pth = Path(a.part)
    sys.exit(build(pth, Path(a.out or f"out/{pth.stem}"), views=not a.no_views))
