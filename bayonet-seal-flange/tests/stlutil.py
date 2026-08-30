"""Binary STL load + point-in-mesh. Used only by the sealed verifier."""

from __future__ import annotations

import struct
from pathlib import Path

import numpy as np

EPS = 1e-8


def load_binary_stl(path: Path) -> np.ndarray:
    data = path.read_bytes()
    if len(data) < 84:
        raise ValueError(f"{path} too small to be a binary STL")
    # ASCII STL starts with "solid" and is newline text. A binary file can
    # coincidentally start with those bytes, so also require the size match.
    n = struct.unpack_from("<I", data, 80)[0]
    expect = 84 + n * 50
    if expect != len(data):
        raise ValueError(
            f"{path} is not a binary STL (size {len(data)} vs {expect} for {n} tris)"
        )
    if n < 20:
        raise ValueError(f"{path} has only {n} triangles")
    rec = np.frombuffer(data, dtype=np.dtype("<u1"), offset=84)
    rec = rec.reshape(n, 50)
    # 12 float32 after the normal: 9 vertex coords
    verts = rec[:, 12:48].view("<f4").reshape(n, 3, 3).astype(np.float64)
    return verts


def signed_volume(tris: np.ndarray) -> float:
    v0, v1, v2 = tris[:, 0], tris[:, 1], tris[:, 2]
    return float(np.abs(np.einsum("ij,ij->i", v0, np.cross(v1, v2)).sum()) / 6.0)


def bbox(tris: np.ndarray):
    pts = tris.reshape(-1, 3)
    return pts.min(axis=0), pts.max(axis=0)


def _ray_count(orig: np.ndarray, direction: np.ndarray, tris: np.ndarray) -> int:
    """Count Möller–Trumbore hits for one ray vs all triangles."""
    v0, v1, v2 = tris[:, 0], tris[:, 1], tris[:, 2]
    e1 = v1 - v0
    e2 = v2 - v0
    pvec = np.cross(direction, e2)
    det = np.einsum("ij,ij->i", e1, pvec)
    hit = np.abs(det) > 1e-10
    inv = np.zeros_like(det)
    inv[hit] = 1.0 / det[hit]
    tvec = orig - v0
    u = np.einsum("ij,ij->i", tvec, pvec) * inv
    hit &= (u >= -EPS) & (u <= 1.0 + EPS)
    qvec = np.cross(tvec, e1)
    v = np.einsum("ij,ij->i", np.broadcast_to(direction, qvec.shape), qvec) * inv
    hit &= (v >= -EPS) & (u + v <= 1.0 + EPS)
    t = np.einsum("ij,ij->i", e2, qvec) * inv
    hit &= t > 1e-6
    return int(np.count_nonzero(hit))


def point_inside(tris: np.ndarray, p, attempts: int = 3) -> bool:
    p = np.asarray(p, dtype=np.float64)
    dirs = np.array(
        [
            [1.0, 0.037, 0.019],
            [0.023, 1.0, 0.041],
            [0.031, 0.017, 1.0],
        ],
        dtype=np.float64,
    )
    votes = 0
    for i in range(attempts):
        d = dirs[i]
        d = d / np.linalg.norm(d)
        votes += _ray_count(p, d, tris) % 2
    return votes >= 2


def rotate_z(p, deg: float):
    a = math_rad(deg)
    c, s = np.cos(a), np.sin(a)
    x, y, z = p
    return (float(c * x - s * y), float(s * x + c * y), float(z))


def math_rad(deg: float) -> float:
    return deg * np.pi / 180.0


def translate(p, dz: float):
    return (p[0], p[1], p[2] + dz)
