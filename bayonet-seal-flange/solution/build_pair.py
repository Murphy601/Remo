#!/usr/bin/env python3
"""Helios-M34 male/female pair — voxelised binary STL."""

from __future__ import annotations

import argparse
import math
import struct
from pathlib import Path

import numpy as np

DX = 0.25


WINDOWS = ((0.0, 46.0), (107.0, 32.0), (236.0, 39.0))
LUGS = ((0.0, 38.0), (107.0, 24.0), (236.0, 31.0))
LOCK_DEG = 47.0
RAMP_MM = 1.10
M3_DEG = (22.0, 112.0, 202.0, 292.0)


def _in_span(ang_deg: np.ndarray, center: float, span: float) -> np.ndarray:
    d = (ang_deg - center + 180.0) % 360.0 - 180.0
    return np.abs(d) <= (span / 2.0)


def _in_windows(ang: np.ndarray) -> np.ndarray:
    m = np.zeros_like(ang, dtype=bool)
    for c, s in WINDOWS:
        m |= _in_span(ang, c, s)
    return m


def _ramp_extra(ang: np.ndarray) -> np.ndarray:
    extra = np.zeros_like(ang, dtype=np.float64)
    for c, s in WINDOWS:
        edge = c + s / 2.0
        dccw = (ang - edge + 360.0) % 360.0
        extra = np.maximum(
            extra, np.where(dccw <= LOCK_DEG, RAMP_MM * (dccw / LOCK_DEG), 0.0)
        )
    return extra


def female_solid(x: np.ndarray, y: np.ndarray, z: np.ndarray) -> np.ndarray:
    r = np.hypot(x, y)
    ang = np.degrees(np.arctan2(y, x))
    solid = (z >= 0.0) & (z <= 12.0)

    hole = np.zeros_like(solid)
    for deg in M3_DEG:
        a = math.radians(deg)
        cx, cy = 29.0 * math.cos(a), 29.0 * math.sin(a)
        d2 = (x - cx) ** 2 + (y - cy) ** 2
        hole |= d2 <= (1.70**2)
        hole |= (z >= 9.20) & (z <= 10.0) & (d2 <= (3.00**2))
    solid &= ~hole

    # 1.78 cord, 22% crush, width 1.40*cord, centreline r=26.05
    groove = (z >= 0.0) & (z <= 1.388) & (r >= 24.804) & (r <= 27.296)
    radial = (z >= 1.90) & (z <= 3.30) & (r >= 24.15) & (r <= 25.45)
    slot = (
        (z >= 0.0)
        & (z <= 3.20)
        & (np.abs(r - 33.20) <= 1.10)
        & (((ang - 14.0 + 360.0) % 360.0) <= 47.0)
    )
    wf = (
        33.50 * math.cos(math.radians(318.0)),
        33.50 * math.sin(math.radians(318.0)),
    )
    weep_f = ((x - wf[0]) ** 2 + (y - wf[1]) ** 2) <= (1.25**2)
    vice = (x <= -34.5) & (np.abs(y) <= 4.0) & (z >= 0.0) & (z <= 4.0)
    solid &= ~groove
    solid &= ~radial
    solid &= ~slot
    solid &= ~weep_f
    solid &= ~vice

    back = z >= 10.0
    solid &= ~back | ((r <= 25.0) & (r >= 17.0))
    solid &= ~(~back) | (r <= 36.0)
    solid &= ~((z < 10.0) & (r < 24.15))

    in_band = (r >= 24.15) & (r < 28.20) & (z < 10.0)
    z_lip_hi = 5.40 + _ramp_extra(ang)
    win = _in_windows(ang)
    # Windows are through the seal face — a z=3 pocket is a bowl the lugs cannot enter.
    solid &= ~((r >= 24.15) & (r < 28.20) & win & (z >= 0.0) & (z <= 5.40))

    stop = (
        (z >= 6.80)
        & (z <= 9.20)
        & (r >= 24.20)
        & (r <= 28.20)
        & _in_span(ang, 73.5, 9.0)
    )
    race = in_band & (z > z_lip_hi) & ~stop
    solid &= ~race
    return solid


def male_solid(x: np.ndarray, y: np.ndarray, z: np.ndarray) -> np.ndarray:
    r = np.hypot(x, y)
    ang = np.degrees(np.arctan2(y, x))
    if_cap = (z >= -8.0) & (z <= 0.0) & (r <= 34.0)
    if_barrel = (z >= 0.0) & (z <= 9.35) & (r <= 24.0)
    lug_z = (z >= 6.70) & (z <= 9.10) & (r >= 24.00) & (r <= 27.60)
    if_lugs = np.zeros_like(lug_z)
    for c, s in LUGS:
        if_lugs |= lug_z & _in_span(ang, c, s)
    pin_c = (33.20 * math.cos(math.radians(14.0)), 33.20 * math.sin(math.radians(14.0)))
    if_pin = (
        (z >= 0.0)
        & (z <= 2.70)
        & (((x - pin_c[0]) ** 2 + (y - pin_c[1]) ** 2) <= (0.95**2))
    )
    wm = (
        33.50 * math.cos(math.radians(271.0)),
        33.50 * math.sin(math.radians(271.0)),
    )
    weep_m = ((x - wm[0]) ** 2 + (y - wm[1]) ** 2) <= (1.25**2)
    solid = if_cap | if_barrel | if_lugs | if_pin
    solid &= (r >= 17.0) | if_pin
    pocket = (z >= -8.0) & (z <= -5.80) & (r < 18.25)
    solid &= ~pocket
    solid &= ~weep_m
    return solid


def voxelize(fn, bounds, dx=DX):
    (x0, x1), (y0, y1), (z0, z1) = bounds
    xs = np.arange(x0 + dx * 0.5, x1, dx, dtype=np.float64)
    ys = np.arange(y0 + dx * 0.5, y1, dx, dtype=np.float64)
    zs = np.arange(z0 + dx * 0.5, z1, dx, dtype=np.float64)
    occ = np.zeros((xs.size, ys.size, zs.size), dtype=bool)
    xx, yy = np.meshgrid(xs, ys, indexing="ij")
    for k, zc in enumerate(zs):
        occ[:, :, k] = fn(xx, yy, np.full_like(xx, float(zc)))
    origin = (float(xs[0] - dx * 0.5), float(ys[0] - dx * 0.5), float(zs[0] - dx * 0.5))
    return occ, origin, dx


def _quads(c00, c10, c11, c01):
    t1 = np.stack([c00, c10, c11], axis=1)
    t2 = np.stack([c00, c11, c01], axis=1)
    return np.concatenate([t1, t2], axis=0)


def voxel_faces(occ: np.ndarray, origin, dx: float) -> np.ndarray:
    x0, y0, z0 = origin
    chunks = []

    def emit(mask, corners):
        if mask.any():
            chunks.append(_quads(*corners))

    # +X faces of solid cells that meet empty (or boundary)
    east = np.pad(occ, ((0, 1), (0, 0), (0, 0)), constant_values=False)
    m = east[:-1] & ~east[1:]
    i, j, k = np.nonzero(m)
    x = x0 + (i + 1) * dx
    y = y0 + j * dx
    z = z0 + k * dx
    emit(
        m,
        (
            np.column_stack([x, y, z]),
            np.column_stack([x, y + dx, z]),
            np.column_stack([x, y + dx, z + dx]),
            np.column_stack([x, y, z + dx]),
        ),
    )

    west = np.pad(occ, ((1, 0), (0, 0), (0, 0)), constant_values=False)
    m = west[1:] & ~west[:-1]
    i, j, k = np.nonzero(m)
    x = x0 + i * dx
    y = y0 + j * dx
    z = z0 + k * dx
    emit(
        m,
        (
            np.column_stack([x, y, z]),
            np.column_stack([x, y, z + dx]),
            np.column_stack([x, y + dx, z + dx]),
            np.column_stack([x, y + dx, z]),
        ),
    )

    north = np.pad(occ, ((0, 0), (0, 1), (0, 0)), constant_values=False)
    m = north[:, :-1] & ~north[:, 1:]
    i, j, k = np.nonzero(m)
    x = x0 + i * dx
    y = y0 + (j + 1) * dx
    z = z0 + k * dx
    emit(
        m,
        (
            np.column_stack([x, y, z]),
            np.column_stack([x, y, z + dx]),
            np.column_stack([x + dx, y, z + dx]),
            np.column_stack([x + dx, y, z]),
        ),
    )

    south = np.pad(occ, ((0, 0), (1, 0), (0, 0)), constant_values=False)
    m = south[:, 1:] & ~south[:, :-1]
    i, j, k = np.nonzero(m)
    x = x0 + i * dx
    y = y0 + j * dx
    z = z0 + k * dx
    emit(
        m,
        (
            np.column_stack([x, y, z]),
            np.column_stack([x + dx, y, z]),
            np.column_stack([x + dx, y, z + dx]),
            np.column_stack([x, y, z + dx]),
        ),
    )

    up = np.pad(occ, ((0, 0), (0, 0), (0, 1)), constant_values=False)
    m = up[:, :, :-1] & ~up[:, :, 1:]
    i, j, k = np.nonzero(m)
    x = x0 + i * dx
    y = y0 + j * dx
    z = z0 + (k + 1) * dx
    emit(
        m,
        (
            np.column_stack([x, y, z]),
            np.column_stack([x + dx, y, z]),
            np.column_stack([x + dx, y + dx, z]),
            np.column_stack([x, y + dx, z]),
        ),
    )

    down = np.pad(occ, ((0, 0), (0, 0), (1, 0)), constant_values=False)
    m = down[:, :, 1:] & ~down[:, :, :-1]
    i, j, k = np.nonzero(m)
    x = x0 + i * dx
    y = y0 + j * dx
    z = z0 + k * dx
    emit(
        m,
        (
            np.column_stack([x, y, z]),
            np.column_stack([x, y + dx, z]),
            np.column_stack([x + dx, y + dx, z]),
            np.column_stack([x + dx, y, z]),
        ),
    )

    if not chunks:
        return np.zeros((0, 3, 3), dtype=np.float32)
    return np.concatenate(chunks, axis=0).astype(np.float32)


def write_binary_stl(path: Path, tris: np.ndarray) -> None:
    n = int(tris.shape[0])
    v0, v1, v2 = tris[:, 0], tris[:, 1], tris[:, 2]
    nrm = np.cross(v1 - v0, v2 - v0)
    ln = np.linalg.norm(nrm, axis=1, keepdims=True)
    nrm = np.divide(nrm, np.maximum(ln, 1e-20))
    rec = np.zeros(n, dtype=[("n", "<f4", 3), ("v", "<f4", 9), ("a", "<u2")])
    rec["n"] = nrm
    rec["v"] = tris.reshape(n, 9)
    header = bytearray(80)
    header[:24] = b"Helios-M34 ICD-H34-09 C2"
    path.write_bytes(bytes(header) + struct.pack("<I", n) + rec.tobytes())


def build_one(fn, bounds, path: Path) -> tuple[int, float]:
    occ, origin, dx = voxelize(fn, bounds)
    vol = float(occ.sum()) * dx**3
    tris = voxel_faces(occ, origin, dx)
    write_binary_stl(path, tris)
    return int(tris.shape[0]), vol


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--outdir", default="/app")
    args = p.parse_args()
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)

    f_tris, f_vol = build_one(
        female_solid,
        ((-37.0, 37.0), (-37.0, 37.0), (-0.25, 12.25)),
        out / "female.stl",
    )
    m_tris, m_vol = build_one(
        male_solid,
        ((-35.0, 35.0), (-35.0, 35.0), (-8.25, 9.60)),
        out / "male.stl",
    )
    print(f"female triangles={f_tris} volume={f_vol:.1f} mm3")
    print(f"male triangles={m_tris} volume={m_vol:.1f} mm3")


if __name__ == "__main__":
    main()
