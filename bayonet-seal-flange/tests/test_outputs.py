"""Sealed geometry checks for the Helios-M34 bayonet pair."""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from stlutil import bbox, load_binary_stl, point_inside, rotate_z, signed_volume, translate

FEMALE = Path("/app/female.stl")
MALE = Path("/app/male.stl")
LOCK = 47.0
PROUD = -1.10


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
    """STL (binary or ASCII), enough triangles that this is not a 12-face box."""
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
    """Male envelope: Ø68 cap, barrel to z = 9.35, cap down to z = -8."""
    lo, hi = bbox(male_tris)
    assert lo[0] < -32.5 and hi[0] > 32.5
    assert hi[0] < 36.5 and hi[1] < 36.5
    assert lo[2] < -7.3
    assert lo[2] > -9.2
    assert hi[2] > 8.6
    assert hi[2] < 10.4


def test_volumes(female_tris, male_tris):
    """Closed solids in the right mass range — a shell or a brick misses."""
    fv = signed_volume(female_tris)
    mv = signed_volume(male_tris)
    # Oracle voxel volumes ~19600 / ~30000. Slack is 0.2 mm breaks + mesh flavour.
    assert 17500.0 < fv < 22500.0, f"female volume {fv:.1f}"
    assert 27000.0 < mv < 34000.0, f"male volume {mv:.1f}"


def test_optical_bore_clear(female_tris, male_tris):
    """Ø34 path is open on both parts, including the female back wall."""
    for p in [(0.0, 0.0, 6.0), (0.0, 0.0, 11.0), (0.0, 0.0, 1.0)]:
        assert not point_inside(female_tris, p), f"female blocked at {p}"
    for p in [(0.0, 0.0, 2.0), (0.0, 0.0, 7.0), (0.0, 0.0, -6.9)]:
        assert not point_inside(male_tris, p), f"male blocked at {p}"


def test_female_face_gland(female_tris):
    """HX-7 face groove from 22% crush / 1.40×cord about r=26.05."""
    trough = (26.05, 0.0, 0.70)
    land_out = (28.60, 0.0, 0.70)
    land_in = (24.50, 0.0, 0.70)
    assert not point_inside(female_tris, trough), "groove trough filled in"
    assert point_inside(female_tris, land_out), "no metal outside the gland"
    assert point_inside(female_tris, land_in), "no metal inside the gland"


def test_radial_gland(female_tris, male_tris):
    """Radial groove in the female bore; male barrel stays plain Ø48."""
    assert not point_inside(female_tris, (24.80, 0.0, 2.60)), "radial groove missing"
    assert point_inside(female_tris, (26.80, 0.0, 2.60)), "wall gone outside radial groove"
    assert point_inside(male_tris, (23.40, 0.0, 2.60)), "male barrel missing"
    assert not point_inside(male_tris, (24.80, 0.0, 2.60)), "male has a radial groove"


def test_m3_and_spotface(female_tris):
    """4 × Ø3.4 on a 58 BCD at 22/112/202/292, spotfaces on the z=10 shoulder."""
    for deg in (22.0, 112.0, 202.0, 292.0):
        hole = polar(29.0, deg, 5.0)
        spot = polar(29.0, deg, 9.60)
        metal = polar(29.0, deg + 14.0, 5.0)
        assert not point_inside(female_tris, hole), f"M3 not open at {deg}"
        assert not point_inside(female_tris, spot), f"spotface missing at {deg}"
        assert point_inside(female_tris, metal), f"flange vanished near {deg}"
    # default 45° pattern is wrong
    assert point_inside(female_tris, polar(29.0, 45.0, 5.0)), "M3 landed on 45s"


def test_back_wall_step(female_tris):
    """Ø72 stops at z = 10. Tube seat is Ø50 with a real back wall."""
    assert point_inside(female_tris, (20.0, 0.0, 11.0)), "back wall missing"
    assert not point_inside(female_tris, (30.0, 0.0, 11.0)), "Ø72 ran through z>10"
    assert point_inside(female_tris, (30.0, 0.0, 2.0)), "flange OD missing"


def test_unequal_windows(female_tris):
    """Windows at 0/107/236, not 120. Lip metal where a 120 pattern would cut."""
    assert not point_inside(female_tris, polar(26.2, 0.0, 4.20)), "fat window closed"
    assert not point_inside(female_tris, polar(26.2, 107.0, 4.20)), "107 window closed"
    assert not point_inside(female_tris, polar(26.2, 236.0, 4.20)), "236 window closed"
    assert point_inside(female_tris, polar(26.2, 85.0, 4.20)), "lip gone at 85"
    assert point_inside(female_tris, polar(26.2, 180.0, 4.20)), "lip gone at 180"
    assert point_inside(female_tris, polar(26.2, 70.0, 4.20)), "lip gone at 70"
    assert not point_inside(female_tris, polar(26.2, 0.0, 7.40)), "race filled at 0"


def test_ramp_on_lip(female_tris):
    """Lip +Z face climbs after a window's CCW edge. Flat lip fails this."""
    # key window CCW edge is 23°. at 35° (~12° into the ramp) rise ~0.28
    assert point_inside(female_tris, polar(26.2, 35.0, 5.55)), "no ramp after fat window"
    assert not point_inside(female_tris, polar(26.2, 0.0, 5.55)), "ramp filled the window"
    # further along the key ramp, near lock, lip is higher
    assert point_inside(female_tris, polar(26.2, 60.0, 6.10)), "ramp died before lock"


def test_male_lugs_and_pin(male_tris):
    """Unequal lugs at 0/107/236 and the clock pin at r=33.20 / 14°."""
    assert point_inside(male_tris, polar(25.8, 0.0, 7.90)), "fat lug missing"
    assert point_inside(male_tris, polar(25.8, 14.0, 7.90)), "fat lug too narrow"
    assert point_inside(male_tris, polar(25.8, 107.0, 7.90)), "107 lug missing"
    assert point_inside(male_tris, polar(25.8, 236.0, 7.90)), "236 lug missing"
    assert not point_inside(male_tris, polar(25.8, 120.0, 7.90)), "extra lug at 120"
    assert not point_inside(male_tris, polar(25.8, 20.4, 7.90)), "fat lug too wide"
    assert point_inside(male_tris, polar(33.20, 14.0, 1.30)), "clock pin missing"
    assert point_inside(male_tris, (20.5, 0.0, 3.0)), "barrel missing"
    assert point_inside(male_tris, (22.0, 0.0, -4.0)), "cap missing"
    assert not point_inside(male_tris, (20.0, 0.0, 11.0)), "barrel hits the back wall"


def test_clock_slot(female_tris):
    """Arc slot 14°–61°, not a round hole."""
    assert not point_inside(female_tris, polar(33.20, 14.0, 1.50)), "slot closed at 14"
    assert not point_inside(female_tris, polar(33.20, 40.0, 1.50)), "slot does not travel"
    assert point_inside(female_tris, polar(33.20, 8.0, 1.50)), "slot opened the wrong way"
    assert point_inside(female_tris, polar(33.20, 70.0, 1.50)), "slot ran past lock"


def test_insert_no_clash(female_tris, male_tris):
    """At the proud insert pose (dz=-1.10) male metal is not inside female."""
    samples = [
        (22.0, 0.0, -4.0),
        (20.5, 0.0, 3.0),
        polar(25.8, 0.0, 7.90),
        polar(25.8, 107.0, 7.90),
        polar(25.8, 236.0, 7.90),
        polar(33.20, 14.0, 1.30),
    ]
    for p in samples:
        assert point_inside(male_tris, p), f"sample not in male {p}"
        proud = translate(p, PROUD)
        assert not point_inside(female_tris, proud), f"insert clash at {proud}"
        mid = translate(p, -3.20)
        assert not point_inside(female_tris, mid), f"stroke clash at {mid}"


def test_lock_retention(female_tris, male_tris):
    """+47° CCW, faces seated: lugs in the race, lip blocks a -Z pull."""
    key = polar(25.8, 0.0, 7.90)
    locked = rotate_z(key, LOCK)
    assert point_inside(male_tris, key)
    assert not point_inside(female_tris, locked), "lug buried in female at lock"
    behind = polar(25.8, LOCK, 4.20)
    assert point_inside(female_tris, behind), "no lip behind the locked fat lug"
    assert not point_inside(female_tris, polar(33.20, 54.0, 1.30)), "slot closed at lock travel"


def test_hard_stop(female_tris):
    """Race stop at 69–78° so the cap cannot walk past lock."""
    assert point_inside(female_tris, polar(26.2, 73.5, 8.00)), "hard stop missing"
    assert not point_inside(female_tris, polar(26.2, LOCK, 8.00)), "race closed at lock"


def test_wrong_clock_blocked(female_tris, male_tris):
    """Fat lug will not pass the 32° window at 107°."""
    edge = polar(25.8, 17.5, 7.90)
    assert point_inside(male_tris, edge), "fat lug does not reach 17.5°"
    jammed = translate(rotate_z(edge, 107.0), -3.20)
    assert point_inside(female_tris, jammed), "fat lug fits the 107 window"


def test_vice_flat(female_tris, male_tris):
    """2 mm fixture flat on the female OD at 180°, not on the cap."""
    assert not point_inside(female_tris, polar(35.4, 180.0, 2.0)), "vice flat missing"
    assert point_inside(female_tris, polar(33.2, 180.0, 2.0)), "flat cut too deep"
    assert point_inside(male_tris, polar(33.2, 180.0, -3.0)), "male got the vice flat"


def test_weep_aligns(female_tris, male_tris):
    """Ø2.5 weeps coincide only after +47°. Wrong male angle misses."""
    assert not point_inside(female_tris, polar(33.50, 318.0, 5.0)), "female weep missing"
    assert not point_inside(male_tris, polar(33.50, 271.0, -4.0)), "male weep missing"
    assert point_inside(male_tris, polar(33.50, 318.0, -4.0)), "male weep already at 318"
    locked = rotate_z(polar(33.50, 271.0, -4.0), LOCK)
    assert abs(locked[0] - polar(33.50, 318.0, -4.0)[0]) < 0.35
    assert not point_inside(female_tris, (locked[0], locked[1], 5.0))


def test_cw_blocked(female_tris, male_tris):
    """CW is the wrong sense — fat lug hits the lip mid-stroke."""
    p = translate(rotate_z(polar(25.8, 0.0, 7.90), -30.0), -3.20)
    assert point_inside(male_tris, polar(25.8, 0.0, 7.90))
    assert point_inside(female_tris, p), "CW insert is clear"


def test_parts_are_not_copies(female_tris, male_tris):
    """Receiver and cap are different bodies, not one file written twice."""
    flo, fhi = bbox(female_tris)
    mlo, mhi = bbox(male_tris)
    assert abs((fhi[2] - flo[2]) - (mhi[2] - mlo[2])) > 1.0
    assert point_inside(female_tris, (30.0, 0.0, 2.0))
    assert not point_inside(male_tris, (30.0, 0.0, 2.0))
