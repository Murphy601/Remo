import os
import subprocess
import shutil

import pytest

TB = os.environ.get("CDC_TB", "/tests/tb_scoreboard.v")
DUT = os.environ.get("CDC_DUT", "/app/cdc_fabric.v")
BUILD = os.environ.get("CDC_BUILD", "/tmp/cdc_build")

CONFIGS = [
    dict(id="equal_burst", pa=10, pb=10, phase=0, npkt=50000, traffic=0, seed=1, rst=0, crdly=0),
    dict(id="ratio_3_2_burst", pa=20, pb=30, phase=3, npkt=50000, traffic=0, seed=11, rst=0, crdly=0),
    dict(id="a_fast_burst", pa=10, pb=50, phase=0, npkt=50000, traffic=0, seed=21, rst=0, crdly=0),
    dict(id="b_fast_burst", pa=70, pb=10, phase=7, npkt=50000, traffic=0, seed=31, rst=0, crdly=0),
    dict(id="b_fast_trickle", pa=70, pb=10, phase=3, npkt=8000, traffic=1, seed=41, rst=0, crdly=0),
    dict(id="a_fast_trickle", pa=10, pb=50, phase=7, npkt=8000, traffic=1, seed=51, rst=0, crdly=0),
    dict(id="ratio_3_2_late_credit", pa=20, pb=30, phase=0, npkt=8000, traffic=1, seed=61, rst=0, crdly=1),
    dict(id="equal_rst_b_first", pa=10, pb=10, phase=7, npkt=20000, traffic=0, seed=71, rst=2, crdly=0),
]


@pytest.fixture(scope="session")
def sim():
    if not os.path.isfile(DUT):
        pytest.fail("missing DUT file %s" % DUT)
    if not os.path.isfile(TB):
        pytest.fail("missing TB file %s" % TB)
    shutil.rmtree(BUILD, ignore_errors=True)
    os.makedirs(BUILD, exist_ok=True)
    cmd = [
        "verilator",
        "--binary",
        "--timing",
        "--top-module",
        "tb_scoreboard",
        "-Wno-fatal",
        "-Wno-WIDTH",
        "-Mdir",
        BUILD,
        "-o",
        "cdc_vsim",
        TB,
        DUT,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        pytest.fail("verilator failed\n%s\n%s" % (r.stdout[-2000:], r.stderr[-4000:]))
    path = os.path.join(BUILD, "cdc_vsim")
    if not os.path.isfile(path):
        pytest.fail("verilator did not emit %s" % path)
    return path


@pytest.mark.parametrize("cfg", CONFIGS, ids=lambda c: c["id"])
def test_clock_ratio(sim, cfg):
    args = [
        sim,
        "+PA=%d" % cfg["pa"],
        "+PB=%d" % cfg["pb"],
        "+PHASE=%d" % cfg["phase"],
        "+NPKT=%d" % cfg["npkt"],
        "+TRAFFIC=%d" % cfg["traffic"],
        "+SEED=%d" % cfg["seed"],
        "+RST=%d" % cfg["rst"],
        "+CRDLY=%d" % cfg["crdly"],
    ]
    r = subprocess.run(args, capture_output=True, text=True, timeout=180)
    out = (r.stdout or "") + "\n" + (r.stderr or "")
    assert "RESULT PASS" in out, out[-3000:]
    assert "RESULT FAIL" not in out, out[-3000:]
    assert r.returncode == 0
