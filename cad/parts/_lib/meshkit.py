"""Mesh helpers shared by part modules and the pipeline (manifold3d <-> trimesh, claims)."""
from __future__ import annotations

from dataclasses import dataclass

import manifold3d as mf
import numpy as np
import trimesh

MESH_TOL_MM = 0.02


def to_manifold(m: trimesh.Trimesh) -> mf.Manifold:
    mesh = mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32))
    out = mf.Manifold(mesh)
    if out.status() != mf.Error.NoError:
        raise ValueError(f"mesh is not a manifold volume: {out.status()}")
    return out


def to_trimesh(m: mf.Manifold) -> trimesh.Trimesh:
    mm = m.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(mm.vert_properties)[:, :3], faces=np.asarray(mm.tri_verts), process=True)


def solid_to_trimesh(solid, tol=MESH_TOL_MM) -> trimesh.Trimesh:
    verts, tris = solid.tessellate(tol, 0.2)
    v = np.array([[p.X, p.Y, p.Z] for p in verts])
    return trimesh.Trimesh(v, np.array(tris), process=True)


def as_manifold(x) -> mf.Manifold:
    if isinstance(x, mf.Manifold):
        return x
    if isinstance(x, trimesh.Trimesh):
        return to_manifold(x)
    return to_manifold(solid_to_trimesh(x))


@dataclass
class Claim:
    req: str
    text: str
    ok: bool
    value: object = None


def claim(req, text, ok, value=None):
    return Claim(req, text, bool(ok), value)
