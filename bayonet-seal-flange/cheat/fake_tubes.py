#!/usr/bin/env python3
"""Cheat: two tubes with a similar envelope. Should score 0."""

from __future__ import annotations

import math
import struct
from pathlib import Path


def tube(r_out, r_in, z0, z1, n=48):
    tris = []

    def ring(z, r):
        return [
            (r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n), z)
            for i in range(n)
        ]

    o0, o1 = ring(z0, r_out), ring(z1, r_out)
    i0, i1 = ring(z0, r_in), ring(z1, r_in)

    def quad(a, b, c, d):
        tris.append((a, b, c))
        tris.append((a, c, d))

    for i in range(n):
        j = (i + 1) % n
        quad(o0[i], o0[j], o1[j], o1[i])
        quad(i0[j], i0[i], i1[i], i1[j])
        quad(o0[j], o0[i], i0[i], i0[j])
        quad(o1[i], o1[j], i1[j], i1[i])
    return tris


def write_stl(path: Path, tris):
    n = len(tris)
    buf = bytearray(80 + 4 + n * 50)
    buf[0:8] = b"cheatbox"
    struct.pack_into("<I", buf, 80, n)
    off = 84
    for a, b, c in tris:
        struct.pack_into(
            "<12fH",
            buf,
            off,
            0,
            0,
            1,
            *a,
            *b,
            *c,
            0,
        )
        off += 50
    path.write_bytes(buf)


def main() -> None:
    out = Path("/app")
    out.mkdir(parents=True, exist_ok=True)
    write_stl(out / "female.stl", tube(36.0, 17.0, 0.0, 12.0))
    write_stl(out / "male.stl", tube(32.0, 17.0, -8.0, 9.5))


if __name__ == "__main__":
    main()
