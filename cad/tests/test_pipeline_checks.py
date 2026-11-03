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
