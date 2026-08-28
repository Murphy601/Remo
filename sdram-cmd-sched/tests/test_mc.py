import fcntl
import hashlib
import os
import shutil
import signal
import subprocess

import pytest

RTL = os.environ.get("MC_RTL", "/app/sdr4_mc.v")
SB = os.environ.get("MC_SB", "/tests/dram_sb.cpp")
OBJDIR = os.environ.get("MC_OBJ", "/tmp/mc_build")
UID = 65534
GID = 65534
FD_NONCE = 11
FD_SCORE = 12
LDWRAP = (
    "-Wl,--wrap=execve -Wl,--wrap=execv -Wl,--wrap=execvp "
    "-Wl,--wrap=execl -Wl,--wrap=execle -Wl,--wrap=execlp "
    "-Wl,--wrap=fork -Wl,--wrap=vfork -Wl,--wrap=system -Wl,--wrap=popen"
)

# mode, n0, n1, seed, deadline, rst_pad, rready, min_ref
CASES = [
    ("m0_only", 0, 32, 0, 1, 260, 0, 0, 0),
    ("both_hosts", 1, 48, 48, 11, 630, 0, 0, 0),
    ("raw_hazard", 2, 8, 0, 21, 240, 0, 0, 0),
    ("mixed_rw", 3, 24, 24, 31, 420, 0, 0, 0),
    ("need_refresh", 4, 64, 32, 41, 630, 0, 0, 4),
    ("act_rotate", 5, 40, 8, 51, 350, 0, 0, 0),
    ("hold_rready", 6, 32, 32, 61, 460, 0, 1, 0),
    ("long_reset", 7, 24, 24, 71, 380, 16, 0, 0),
]


def _nops(row):
    _, mode, n0, n1, *_ = row
    return n0 * 2 + n1 if mode == 2 else n0 + n1


def _as_root():
    return os.geteuid() == 0 and shutil.which("setpriv")


@pytest.fixture(scope="session")
def binary():
    if not os.path.isfile(RTL):
        pytest.fail("no RTL at %s" % RTL)
    if not os.path.isfile(SB):
        pytest.fail("no scoreboard at %s" % SB)
    shutil.rmtree(OBJDIR, ignore_errors=True)
    os.makedirs(OBJDIR, exist_ok=True)
    cmd = [
        "verilator", "--cc", "--exe", "--build",
        "--top-module", "sdr4_mc",
        "-Wno-fatal", "-Wno-WIDTH", "-Wno-UNOPTFLAT", "-Wno-CASEINCOMPLETE",
        "-CFLAGS", "-O2 -std=c++17",
        "-LDFLAGS", LDWRAP,
        "-Mdir", OBJDIR,
        "-o", "mc_sim",
        SB, RTL,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        pytest.fail("verilator failed\n%s\n%s" % (r.stdout[-2000:], r.stderr[-4000:]))
    exe = os.path.join(OBJDIR, "mc_sim")
    if not os.path.isfile(exe):
        pytest.fail("missing %s" % exe)
    os.chmod(exe, 0o751)
    os.chmod(OBJDIR, 0o711)
    return exe


def _dup(fd):
    try:
        return os.dup(fd)
    except OSError:
        return None


def _quiet(fd):
    if fd is None or fd < 0:
        return
    try:
        os.close(fd)
    except OSError:
        pass


def _hi_pipe():
    r, w = os.pipe()
    r2 = fcntl.fcntl(r, fcntl.F_DUPFD_CLOEXEC, 32)
    w2 = fcntl.fcntl(w, fcntl.F_DUPFD_CLOEXEC, 32)
    os.close(r)
    os.close(w)
    return r2, w2


def _launch(exe, row):
    name, mode, n0, n1, seed, deadline, rst_pad, rready, min_ref = row
    argv = [
        exe,
        "--mode", str(mode), "--n0", str(n0), "--n1", str(n1),
        "--seed", str(seed), "--deadline", str(deadline),
        "--rstextra", str(rst_pad), "--rready", str(rready),
        "--minref", str(min_ref),
    ]
    if _as_root():
        argv = [
            "setpriv",
            "--reuid=%d" % UID,
            "--regid=%d" % GID,
            "--clear-groups",
            "--nnp",
            "--inh-caps=-all",
            "--bounding-set=-all",
        ] + argv

    nonce = os.urandom(32)
    nr, nw = _hi_pipe()
    sr, sw = _hi_pipe()
    os.set_inheritable(nr, True)
    os.set_inheritable(sw, True)
    keep11 = keep12 = None
    child = None
    closed11 = closed12 = False
    try:
        keep11 = _dup(FD_NONCE)
        keep12 = _dup(FD_SCORE)
        os.dup2(nr, FD_NONCE)
        os.dup2(sw, FD_SCORE)
        os.set_inheritable(FD_NONCE, True)
        os.set_inheritable(FD_SCORE, True)
        if nr != FD_NONCE:
            _quiet(nr)
        nr = -1
        if sw != FD_SCORE:
            _quiet(sw)
        sw = -1
        os.write(nw, nonce)
        _quiet(nw)
        nw = -1
        child = subprocess.Popen(
            argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            pass_fds=(FD_NONCE, FD_SCORE),
            start_new_session=True,
        )
        os.close(FD_NONCE)
        closed11 = True
        os.close(FD_SCORE)
        closed12 = True
        if keep11 is not None:
            os.dup2(keep11, FD_NONCE)
            _quiet(keep11)
            keep11 = None
            closed11 = False
        if keep12 is not None:
            os.dup2(keep12, FD_SCORE)
            _quiet(keep12)
            keep12 = None
            closed12 = False
        bits = []
        while True:
            chunk = os.read(sr, 4096)
            if not chunk:
                break
            bits.append(chunk)
        try:
            rc = child.wait(timeout=120)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except OSError:
                child.kill()
            child.wait()
            pytest.fail("sim hung")
        return rc, b"".join(bits), nonce
    finally:
        _quiet(sr)
        _quiet(nr)
        _quiet(nw)
        _quiet(sw)
        if keep11 is not None:
            if closed11:
                os.dup2(keep11, FD_NONCE)
            _quiet(keep11)
        if keep12 is not None:
            if closed12:
                os.dup2(keep12, FD_SCORE)
            _quiet(keep12)
        if child is not None and child.poll() is None:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except OSError:
                try:
                    child.kill()
                except OSError:
                    pass


@pytest.mark.parametrize("row", CASES, ids=lambda r: r[0])
def test_mc_case(binary, row):
    rc, blob, nonce = _launch(binary, row)
    rec = None
    for line in blob.decode("ascii", "replace").splitlines():
        if line.startswith("SCORE "):
            rec = line
    assert rec is not None, "no SCORE on result fd"
    tok = rec.split()
    assert len(tok) >= 7, rec
    ok = int(tok[1])
    sent = int(tok[2])
    done = int(tok[3])
    nref = int(tok[4])
    cyc = int(tok[5])
    mac = tok[6]
    why = " ".join(tok[7:]) if len(tok) > 7 else ""
    body = "%d %d %d %d %d" % (ok, sent, done, nref, cyc)
    want_mac = hashlib.sha256(nonce + body.encode("ascii")).hexdigest()
    assert mac == want_mac, "SCORE mac mismatch"
    want = _nops(row)
    deadline = row[5]
    min_ref = row[8]
    assert ok == 1, "fail %s sent=%d done=%d nref=%d cyc=%d" % (why, sent, done, nref, cyc)
    assert rc == 0
    assert sent == done == want
    assert cyc < deadline
    if min_ref:
        assert nref >= min_ref
