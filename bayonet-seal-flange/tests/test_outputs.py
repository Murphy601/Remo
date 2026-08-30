"""Sealed geometry checks for the Helios-M34 bayonet pair."""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from stlutil import bbox, load_binary_stl, point_inside, rotate_z, signed_volume, translate

FEMALE = Path("/app/female.stl")
MALE = Path("/app/male.stl")


def polar(r: float, deg: float, z: float):
    a = math.radians(deg)
    return (r * math.cos(a), r * math.sin(a), z)


@pytest.fixture(scope="module")
def female_tris():
    assert FEMALE.is_file(), "missing /app/female.stl"
    return load_binary_stl(FEMALE)


@pytest.fixture(scope="module")
def male_tris():
    assert MALE.is_file(), "missing /app/male.stl"
    return load_binary_stl(MALE)


def test_files_exist():
    """Both declared artifacts have to be sitting in /app."""
    assert FEMALE.is_file(), "missing /app/female.stl"
    assert MALE.is_file(), "missing /app/male.stl"
    assert FEMALE.stat().st_size > 2000
    assert MALE.stat().st_size > 2000
    assert FEMALE.read_bytes() != MALE.read_bytes()


def test_binary_stl_sane(female_tris, male_tris):
    """Binary STL, enough triangles that this is not a 12-face box."""
    assert female_tris.shape[0] >= 400
    assert male_tris.shape[0] >= 400


def test_female_bbox(female_tris):
    """Female envelope: Ø72 flange, 12 mm long, nothing below z = 0."""
    lo, hi = bbox(female_tris)
    assert lo[0] < -34.5 and hi[0] > 34.5
    assert lo[1] < -34.5 and hi[1] > 34.5
    assert hi[0] < 38.5 and hi[1] < 38.5
    assert lo[2] > -1.2
    assert hi[2] > 11.4
    assert hi[2] < 13.2


def test_male_bbox(male_tris):
    """Male envelope: Ø64 cap, barrel to z = 9.5, cap down to z = -8."""
    lo, hi = bbox(male_tris)
    assert lo[0] < -30.5 and hi[0] > 30.5
    assert hi[0] < 34.5 and hi[1] < 34.5
    assert lo[2] < -7.3
    assert lo[2] > -9.2
    assert hi[2] > 8.8
    assert hi[2] < 10.6


def test_volumes(female_tris, male_tris):
    """Closed solids in the right mass range — a shell or a brick misses."""
    fv = signed_volume(female_tris)
    mv = signed_volume(male_tris)
    assert 15000.0 < fv < 28000.0, f"female volume {fv:.1f}"
    assert 19000.0 < mv < 34000.0, f"male volume {mv:.1f}"


def test_optical_bore_clear(female_tris, male_tris):
    """Ø34 path is open on both parts, including the female back wall."""
    for p in [(0.0, 0.0, 6.0), (0.0, 0.0, 11.0), (0.0, 0.0, 1.0)]:
        assert not point_inside(female_tris, p), f"female blocked at {p}"
    for p in [(0.0, 0.0, 2.0), (0.0, 0.0, 7.0), (0.0, 0.0, -6.9)]:
        assert not point_inside(male_tris, p), f"male blocked at {p}"


def test_female_gland(female_tris):
    """HX-7 rectangular groove on the female z = 0 face, metal beside it."""
    trough = (26.05, 0.0, 0.70)
    land_out = (28.50, 0.0, 0.70)
    land_in = (24.70, 0.0, 0.70)
    assert not point_inside(female_tris, trough), "groove trough filled in"
    assert point_inside(female_tris, land_out), "no metal outside the gland"
    assert point_inside(female_tris, land_in), "no metal inside the gland"


def test_m3_and_spotface(female_tris):
    """4 × Ø3.4 on a 58 BCD, with Ø6 × 0.8 spotfaces on the seal face."""
    for deg in (45.0, 135.0, 225.0, 315.0):
        hole = polar(29.0, deg, 5.0)
        spot = polar(29.0, deg, 9.60)
        metal = polar(29.0, deg + 12.0, 5.0)
        assert not point_inside(female_tris, hole), f"M3 not open at {deg}"
        assert not point_inside(female_tris, spot), f"spotface missing at {deg}"
        assert point_inside(female_tris, metal), f"flange vanished near {deg}"


def test_back_wall_step(female_tris):
    """Ø72 stops at z = 10. Tube seat is Ø50 with a real back wall."""
    assert point_inside(female_tris, (20.0, 0.0, 11.0)), "back wall missing"
    assert not point_inside(female_tris, (30.0, 0.0, 11.0)), "Ø72 ran through z>10"
    assert point_inside(female_tris, (30.0, 0.0, 2.0)), "flange OD missing"


def test_key_window_and_retainers(female_tris):
    """Fat window on +X, thin windows at 120/240, lip metal at 90°."""
    assert not point_inside(female_tris, polar(26.2, 0.0, 4.20)), "key window closed"
    assert not point_inside(female_tris, polar(26.2, 120.0, 4.20)), "120 window closed"
    assert not point_inside(female_tris, polar(26.2, 240.0, 4.20)), "240 window closed"
    assert point_inside(female_tris, polar(26.2, 90.0, 4.20)), "retainer gone at 90"
    assert point_inside(female_tris, polar(26.2, 180.0, 4.20)), "retainer gone at 180"
    # race empty on the key line after the lip
    assert not point_inside(female_tris, polar(26.2, 0.0, 6.80)), "race filled at 0"


def test_male_lugs(male_tris):
    """One 38° key lug on +X and two 26° regulars. No lug at 60°."""
    assert point_inside(male_tris, polar(25.8, 0.0, 6.80)), "key lug missing"
    assert point_inside(male_tris, polar(25.8, 12.0, 6.80)), "key lug too narrow"
    assert point_inside(male_tris, polar(25.8, 120.0, 6.80)), "120 lug missing"
    assert point_inside(male_tris, polar(25.8, 240.0, 6.80)), "240 lug missing"
    assert not point_inside(male_tris, polar(25.8, 60.0, 6.80)), "extra lug at 60"
    assert not point_inside(male_tris, polar(25.8, 20.4, 6.80)), "key lug too wide"
    assert point_inside(male_tris, (20.5, 0.0, 3.0)), "barrel missing"
    assert point_inside(male_tris, (20.0, 0.0, -4.0)), "cap missing"
    assert not point_inside(male_tris, (20.0, 0.0, 11.0)), "barrel hits the back wall"


def test_insert_no_clash(female_tris, male_tris):
    """Seated at 0° and mid-stroke at 0°, male metal is not inside female."""
    samples = [
        (20.0, 0.0, -4.0),
        (20.5, 0.0, 3.0),
        polar(25.8, 0.0, 6.80),
        polar(25.8, 120.0, 6.80),
        polar(25.8, 240.0, 6.80),
        (0.0, 20.5, 4.0),
    ]
    for p in samples:
        assert point_inside(male_tris, p), f"sample not in male {p}"
        assert not point_inside(female_tris, p), f"seated clash at {p}"
        mid = translate(p, -2.50)
        assert not point_inside(female_tris, mid), f"insert clash at {mid}"


def test_lock_retention(female_tris, male_tris):
    """+50° CCW: lugs sit in the race, lip blocks a -Z pull."""
    key = polar(25.8, 0.0, 6.80)
    locked = rotate_z(key, 50.0)
    assert point_inside(male_tris, key)
    assert not point_inside(female_tris, locked), "lug buried in female at lock"
    behind = polar(25.8, 50.0, 4.20)
    assert point_inside(female_tris, behind), "no lip behind the locked key lug"
    # locked regular
    reg = rotate_z(polar(25.8, 120.0, 6.80), 50.0)
    assert not point_inside(female_tris, reg)


def test_hard_stop(female_tris):
    """Race stop at 72–80° so the cap cannot walk past lock."""
    assert point_inside(female_tris, polar(26.2, 76.0, 6.80)), "hard stop missing"
    assert not point_inside(female_tris, polar(26.2, 50.0, 6.80)), "race closed at lock"


def test_wrong_clock_blocked(female_tris, male_tris):
    """Fat lug will not pass a 34° window — +120° clock is jammed."""
    edge = polar(25.8, 18.5, 6.80)
    assert point_inside(male_tris, edge), "key lug does not reach 18.5°"
    jammed = translate(rotate_z(edge, 120.0), -2.50)
    assert point_inside(female_tris, jammed), "key lug fits a thin window (wrong clock works)"


def test_parts_are_not_copies(female_tris, male_tris):
    """Receiver and cap are different bodies, not one file written twice."""
    flo, fhi = bbox(female_tris)
    mlo, mhi = bbox(male_tris)
    assert abs((fhi[2] - flo[2]) - (mhi[2] - mlo[2])) > 1.0
    assert point_inside(female_tris, (30.0, 0.0, 2.0))
    assert not point_inside(male_tris, (30.0, 0.0, 2.0))
