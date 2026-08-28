import fcntl
import hashlib
import os
import signal
import subprocess
import shutil

import pytest

DUT = os.environ.get("SDRAM_DUT", "/app/sdram_sched.v")
TB_CC = os.environ.get("SDRAM_TB_CC", "/tests/tb_main.cpp")
BUILD = os.environ.get("SDRAM_BUILD", "/tmp/sdram_build")
SIM_UID = 65534
SIM_GID = 65534
GRADE_FD = 8
SECRET_FD = 7
WRAP_LDFLAGS = (
    "-Wl,--wrap=system "
    "-Wl,--wrap=popen "
    "-Wl,--wrap=fork "
    "-Wl,--wrap=vfork "
    "-Wl,--wrap=execve "
    "-Wl,--wrap=execv "
    "-Wl,--wrap=execvp "
    "-Wl,--wrap=execl "
    "-Wl,--wrap=execle "
    "-Wl,--wrap=execlp"
)

CONFIGS = [
    dict(id="p0_reads", mode=0, n0=32, n1=0, seed=1, deadline=260, rstextra=0, rready=0, minref=0),
    dict(id="dual_read", mode=1, n0=48, n1=48, seed=11, deadline=630, rstextra=0, rready=0, minref=0),
    dict(id="same_port_raw", mode=2, n0=8, n1=0, seed=21, deadline=240, rstextra=0, rready=0, minref=0),
    dict(id="rw_mix", mode=3, n0=24, n1=24, seed=31, deadline=420, rstextra=0, rready=0, minref=0),
    dict(id="refresh_load", mode=4, n0=64, n1=32, seed=41, deadline=630, rstextra=0, rready=0, minref=4),
    dict(id="tfaw_storm", mode=5, n0=40, n1=8, seed=51, deadline=350, rstextra=0, rready=0, minref=0),
    dict(id="rready_backpressure", mode=6, n0=32, n1=32, seed=61, deadline=460, rstextra=0, rready=1, minref=0),
    dict(id="late_reset", mode=7, n0=24, n1=24, seed=71, deadline=380, rstextra=16, rready=0, minref=0),
]


def _drop():
    return os.geteuid() == 0 and shutil.which("setpriv") is not None


def _expect_ops(cfg):
    if cfg["mode"] == 2:
        return cfg["n0"] * 2 + cfg["n1"]
    return cfg["n0"] + cfg["n1"]


@pytest.fixture(scope="session")
def sim():
    if not os.path.isfile(DUT):
        pytest.fail("missing DUT file %s" % DUT)
    if not os.path.isfile(TB_CC):
        pytest.fail("missing TB file %s" % TB_CC)
    shutil.rmtree(BUILD, ignore_errors=True)
    os.makedirs(BUILD, exist_ok=True)
    cmd = [
        "verilator",
        "--cc",
        "--exe",
        "--build",
        "--top-module",
        "sdram_sched",
        "-Wno-fatal",
        "-Wno-WIDTH",
        "-Wno-UNOPTFLAT",
        "-Wno-CASEINCOMPLETE",
        "-CFLAGS",
        "-O2 -std=c++17",
        "-LDFLAGS",
        WRAP_LDFLAGS,
        "-Mdir",
        BUILD,
        "-o",
        "sdram_vsim",
        TB_CC,
        DUT,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        pytest.fail("verilator failed\n%s\n%s" % (r.stdout[-2000:], r.stderr[-4000:]))
    path = os.path.join(BUILD, "sdram_vsim")
    if not os.path.isfile(path):
        pytest.fail("verilator did not emit %s" % path)
    os.chmod(path, 0o751)
    os.chmod(BUILD, 0o711)
    return path


def _try_dup(fd):
    try:
        return os.dup(fd)
    except OSError:
        return None


def _close_quiet(fd):
    if fd is None or fd < 0:
        return
    try:
        os.close(fd)
    except OSError:
        pass


def _pipe_high():
    r, w = os.pipe()
    r2 = fcntl.fcntl(r, fcntl.F_DUPFD_CLOEXEC, 32)
    w2 = fcntl.fcntl(w, fcntl.F_DUPFD_CLOEXEC, 32)
    os.close(r)
    os.close(w)
    return r2, w2


def _run_one(sim, cfg):
    argv = [
        sim,
        "--mode",
        str(cfg["mode"]),
        "--n0",
        str(cfg["n0"]),
        "--n1",
        str(cfg["n1"]),
        "--seed",
        str(cfg["seed"]),
        "--deadline",
        str(cfg["deadline"]),
        "--rstextra",
        str(cfg["rstextra"]),
        "--rready",
        str(cfg["rready"]),
        "--minref",
        str(cfg["minref"]),
    ]
    if _drop():
        argv = [
            "setpriv",
            "--reuid=%d" % SIM_UID,
            "--regid=%d" % SIM_GID,
            "--clear-groups",
            "--nnp",
            "--inh-caps=-all",
            "--bounding-set=-all",
        ] + argv

    secret = os.urandom(32)
    nonce_r, nonce_w = _pipe_high()
    grade_r, grade_w = _pipe_high()
    os.set_inheritable(nonce_r, True)
    os.set_inheritable(grade_w, True)
    saved7 = saved8 = None
    p = None
    parent_closed_7 = parent_closed_8 = False
    try:
        saved7 = _try_dup(SECRET_FD)
        saved8 = _try_dup(GRADE_FD)
        os.dup2(nonce_r, SECRET_FD)
        os.dup2(grade_w, GRADE_FD)
        os.set_inheritable(SECRET_FD, True)
        os.set_inheritable(GRADE_FD, True)
        if nonce_r != SECRET_FD:
            _close_quiet(nonce_r)
        nonce_r = -1
        if grade_w != GRADE_FD:
            _close_quiet(grade_w)
        grade_w = -1
        os.write(nonce_w, secret)
        _close_quiet(nonce_w)
        nonce_w = -1
        p = subprocess.Popen(
            argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            pass_fds=(SECRET_FD, GRADE_FD),
            start_new_session=True,
        )
        os.close(SECRET_FD)
        parent_closed_7 = True
        os.close(GRADE_FD)
        parent_closed_8 = True
        if saved7 is not None:
            os.dup2(saved7, SECRET_FD)
            _close_quiet(saved7)
            saved7 = None
            parent_closed_7 = False
        if saved8 is not None:
            os.dup2(saved8, GRADE_FD)
            _close_quiet(saved8)
            saved8 = None
            parent_closed_8 = False
        chunks = []
        while True:
            buf = os.read(grade_r, 4096)
            if not buf:
                break
            chunks.append(buf)
        try:
            rc = p.wait(timeout=120)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except OSError:
                p.kill()
            p.wait()
            pytest.fail("sim timeout")
        return rc, b"".join(chunks), secret
    finally:
        _close_quiet(grade_r)
        _close_quiet(nonce_r)
        _close_quiet(nonce_w)
        _close_quiet(grade_w)
        if saved7 is not None:
            if parent_closed_7:
                os.dup2(saved7, SECRET_FD)
            _close_quiet(saved7)
        if saved8 is not None:
            if parent_closed_8:
                os.dup2(saved8, GRADE_FD)
            _close_quiet(saved8)
        if p is not None and p.poll() is None:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except OSError:
                try:
                    p.kill()
                except OSError:
                    pass


@pytest.mark.parametrize("cfg", CONFIGS, ids=lambda c: c["id"])
def test_sched_cfg(sim, cfg):
    rc, raw, secret = _run_one(sim, cfg)
    lines = raw.decode("ascii", "replace").strip().splitlines()
    grade = None
    for ln in lines:
        if ln.startswith("GRADE "):
            grade = ln
    assert grade is not None, "no grade record on result fd"
    parts = grade.split()
    assert len(parts) >= 7, grade
    ok = int(parts[1])
    sent = int(parts[2])
    done = int(parts[3])
    nref = int(parts[4])
    cyc = int(parts[5])
    mac = parts[6]
    why = " ".join(parts[7:]) if len(parts) > 7 else ""
    payload = "%d %d %d %d %d" % (ok, sent, done, nref, cyc)
    expect = hashlib.sha256(secret + payload.encode("ascii")).hexdigest()
    assert mac == expect, "grade mac mismatch (forged or truncated record)"
    want = _expect_ops(cfg)
    assert ok == 1, "ok=0 why=%s sent=%d done=%d nref=%d cyc=%d" % (why, sent, done, nref, cyc)
    assert rc == 0
    assert sent == done
    assert sent == want
    assert cyc < cfg["deadline"]
    if cfg["minref"]:
        assert nref >= cfg["minref"]
