import fcntl
import hashlib
import os
import signal
import subprocess
import shutil

import pytest

DUT = os.environ.get("CDC_DUT", "/app/cdc_fabric.v")
TB_CC = os.environ.get("CDC_TB_CC", "/tests/tb_main.cpp")
BUILD = os.environ.get("CDC_BUILD", "/tmp/cdc_build")
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
    dict(id="equal_burst", pa=10, pb=10, phase=0, npkt=50000, traffic=0, seed=1, rst=0, crdly=0),
    dict(id="ratio_3_2_burst", pa=20, pb=30, phase=3, npkt=50000, traffic=0, seed=11, rst=0, crdly=0),
    dict(id="a_fast_burst", pa=10, pb=50, phase=0, npkt=50000, traffic=0, seed=21, rst=0, crdly=0),
    dict(id="b_fast_burst", pa=70, pb=10, phase=7, npkt=50000, traffic=0, seed=31, rst=0, crdly=0),
    dict(id="b_fast_trickle", pa=70, pb=10, phase=3, npkt=8000, traffic=1, seed=41, rst=0, crdly=0),
    dict(id="a_fast_trickle", pa=10, pb=50, phase=7, npkt=8000, traffic=1, seed=51, rst=0, crdly=0),
    dict(id="ratio_3_2_late_credit", pa=20, pb=30, phase=0, npkt=8000, traffic=1, seed=61, rst=0, crdly=1),
    dict(id="equal_rst_b_first", pa=10, pb=10, phase=7, npkt=20000, traffic=0, seed=71, rst=2, crdly=0),
]


def _drop():
    return os.geteuid() == 0 and shutil.which("setpriv") is not None


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
        "cdc_fabric",
        "-Wno-fatal",
        "-Wno-WIDTH",
        "-CFLAGS",
        "-O2 -std=c++17",
        "-LDFLAGS",
        WRAP_LDFLAGS,
        "-Mdir",
        BUILD,
        "-o",
        "cdc_vsim",
        TB_CC,
        DUT,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        pytest.fail("verilator failed\n%s\n%s" % (r.stdout[-2000:], r.stderr[-4000:]))
    path = os.path.join(BUILD, "cdc_vsim")
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
    """Pipes on fd>=32 so dup2 onto 7/8 cannot clobber the other end."""
    r, w = os.pipe()
    r2 = fcntl.fcntl(r, fcntl.F_DUPFD_CLOEXEC, 32)
    w2 = fcntl.fcntl(w, fcntl.F_DUPFD_CLOEXEC, 32)
    os.close(r)
    os.close(w)
    return r2, w2


def _run_one(sim, cfg):
    argv = [
        sim,
        "--pa",
        str(cfg["pa"]),
        "--pb",
        str(cfg["pb"]),
        "--phase",
        str(cfg["phase"]),
        "--npkt",
        str(cfg["npkt"]),
        "--traffic",
        str(cfg["traffic"]),
        "--seed",
        str(cfg["seed"]),
        "--rst",
        str(cfg["rst"]),
        "--crdly",
        str(cfg["crdly"]),
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
            rc = p.wait(timeout=180)
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
def test_clock_ratio(sim, cfg):
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
    recv = int(parts[3])
    pcred = int(parts[4])
    crret = int(parts[5])
    mac = parts[6]
    why = " ".join(parts[7:]) if len(parts) > 7 else ""
    payload = "%d %d %d %d %d" % (ok, sent, recv, pcred, crret)
    expect = hashlib.sha256(secret + payload.encode("ascii")).hexdigest()
    assert mac == expect, "grade mac mismatch (forged or truncated record)"
    assert ok == 1, "ok=0 why=%s sent=%d recv=%d pcred=%d crret=%d" % (why, sent, recv, pcred, crret)
    assert rc == 0
    assert sent == recv
    assert sent == pcred
    assert pcred == crret
    assert sent >= cfg["npkt"]
    assert sent <= cfg["npkt"] * 16
