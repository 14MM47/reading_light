"""Regression tests for cad/tools/pipeline.py checks. Run: <cad venv python> -m pytest cad/tests -q"""
import sys
from pathlib import Path

import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import pipeline  # noqa: E402

PRINT = {"material": "petg-basic", "process": "0.20-standard", "supports": "none", "supported": [],
         "orientation": "as-modelled"}


def test_wall_sampling_ignores_zero_area_faces():
    """A mesh with fewer non-zero-area facets than the sample count (here: a box plus degenerate slivers) used to
    crash rng.choice ("Fewer non-zero entries in p than size") instead of being checked (moon_base v0.2)."""
    box = trimesh.creation.box((10, 10, 5))
    box.apply_translation((0, 0, 2.5))
    v = box.vertices
    sliver = np.array([[0, 1, 1], [2, 3, 3], [4, 5, 5]])          # zero-area triangles on existing vertices
    m = trimesh.Trimesh(v, np.vstack([box.faces, sliver]), process=False)
    res = pipeline.check_mesh(m, PRINT, {}, sample_walls=100)
    wall = next(r for r in res if r["name"].startswith("wall_min"))
    assert wall["severity"] == "ok" and wall["value"] >= 4.9


def test_wall_check_finds_a_thin_feature_with_little_area():
    """A 0.05 mm fin (4 mm^2 of finely subdivided facets) beside a large block: 100 area-weighted samples land on
    the fin with ~2 % probability, so the check used to pass a part with a sub-0.84 mm wall (round 3: the moon's
    0.03 mm groove-roof lip, found only when the bayonet coupon put it on a small part)."""
    block = trimesh.creation.box((100, 100, 10))
    for _ in range(4):                       # 3072 facets: enough that sampling without replacement is not
        block = block.subdivide()            # forced onto the fin
    block.apply_translation((0, 0, 5))
    fin = trimesh.creation.box((1.0, 1.0, 0.05))
    for _ in range(4):
        fin = fin.subdivide()
    fin.apply_translation((80, 0, 0.025))
    m = trimesh.util.concatenate([block, fin])
    res = pipeline.check_mesh(m, PRINT, {}, sample_walls=100)
    wall = next(r for r in res if r["name"].startswith("wall_min"))
    assert wall["severity"] == "fail" and wall["value"] < 0.1
