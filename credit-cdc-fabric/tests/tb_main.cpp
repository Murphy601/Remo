#include "Vcdc_fabric.h"
#include "verilated.h"

#include <cerrno>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fcntl.h>
#include <linux/audit.h>
#include <linux/filter.h>
#include <linux/seccomp.h>
#include <signal.h>
#include <stddef.h>
#include <string>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <unistd.h>

static const int kCredits = 8;
static const int kGradeFd = 8;
static const int kSecretFd = 7;

extern "C" {
int __wrap_system(const char*) { errno = EPERM; return -1; }
FILE* __wrap_popen(const char*, const char*) { errno = EPERM; return nullptr; }
pid_t __wrap_fork(void) { errno = EPERM; return -1; }
pid_t __wrap_vfork(void) { errno = EPERM; return -1; }
int __wrap_execve(const char*, char* const[], char* const[]) { errno = EPERM; return -1; }
int __wrap_execv(const char*, char* const[]) { errno = EPERM; return -1; }
int __wrap_execvp(const char*, char* const[]) { errno = EPERM; return -1; }
int __wrap_execl(const char*, const char*, ...) { errno = EPERM; return -1; }
int __wrap_execle(const char*, const char*, ...) { errno = EPERM; return -1; }
int __wrap_execlp(const char*, const char*, ...) { errno = EPERM; return -1; }
}

/* Public-domain SHA-256 (compact). */
struct Sha256 {
    uint32_t s[8];
    uint64_t nbits;
    uint8_t buf[64];
    size_t nbuf;

    static uint32_t rotr(uint32_t x, int n) { return (x >> n) | (x << (32 - n)); }

    void init() {
        s[0] = 0x6a09e667u;
        s[1] = 0xbb67ae85u;
        s[2] = 0x3c6ef372u;
        s[3] = 0xa54ff53au;
        s[4] = 0x510e527fu;
        s[5] = 0x9b05688cu;
        s[6] = 0x1f83d9abu;
        s[7] = 0x5be0cd19u;
        nbits = 0;
        nbuf = 0;
    }

    void block(const uint8_t* p) {
        static const uint32_t K[64] = {
            0x428a2f98u, 0x71374491u, 0xb5c0fbcfu, 0xe9b5dba5u, 0x3956c25bu, 0x59f111f1u,
            0x923f82a4u, 0xab1c5ed5u, 0xd807aa98u, 0x12835b01u, 0x243185beu, 0x550c7dc3u,
            0x72be5d74u, 0x80deb1feu, 0x9bdc06a7u, 0xc19bf174u, 0xe49b69c1u, 0xefbe4786u,
            0x0fc19dc6u, 0x240ca1ccu, 0x2de92c6fu, 0x4a7484aau, 0x5cb0a9dcu, 0x76f988dau,
            0x983e5152u, 0xa831c66du, 0xb00327c8u, 0xbf597fc7u, 0xc6e00bf3u, 0xd5a79147u,
            0x06ca6351u, 0x14292967u, 0x27b70a85u, 0x2e1b2138u, 0x4d2c6dfcu, 0x53380d13u,
            0x650a7354u, 0x766a0abbu, 0x81c2c92eu, 0x92722c85u, 0xa2bfe8a1u, 0xa81a664bu,
            0xc24b8b70u, 0xc76c51a3u, 0xd192e819u, 0xd6990624u, 0xf40e3585u, 0x106aa070u,
            0x19a4c116u, 0x1e376c08u, 0x2748774cu, 0x34b0bcb5u, 0x391c0cb3u, 0x4ed8aa4au,
            0x5b9cca4fu, 0x682e6ff3u, 0x748f82eeu, 0x78a5636fu, 0x84c87814u, 0x8cc70208u,
            0x90befffau, 0xa4506cebu, 0xbef9a3f7u, 0xc67178f2u};
        uint32_t w[64];
        for (int i = 0; i < 16; i++) {
            w[i] = (uint32_t)p[4 * i] << 24 | (uint32_t)p[4 * i + 1] << 16 |
                   (uint32_t)p[4 * i + 2] << 8 | (uint32_t)p[4 * i + 3];
        }
        for (int i = 16; i < 64; i++) {
            uint32_t t0 = rotr(w[i - 15], 7) ^ rotr(w[i - 15], 18) ^ (w[i - 15] >> 3);
            uint32_t t1 = rotr(w[i - 2], 17) ^ rotr(w[i - 2], 19) ^ (w[i - 2] >> 10);
            w[i] = w[i - 16] + t0 + w[i - 7] + t1;
        }
        uint32_t a = s[0], b = s[1], c = s[2], d = s[3], e = s[4], f = s[5], g = s[6], h = s[7];
        for (int i = 0; i < 64; i++) {
            uint32_t S1 = rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25);
            uint32_t ch = (e & f) ^ ((~e) & g);
            uint32_t t1 = h + S1 + ch + K[i] + w[i];
            uint32_t S0 = rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22);
            uint32_t maj = (a & b) ^ (a & c) ^ (b & c);
            uint32_t t2 = S0 + maj;
            h = g;
            g = f;
            f = e;
            e = d + t1;
            d = c;
            c = b;
            b = a;
            a = t1 + t2;
        }
        s[0] += a;
        s[1] += b;
        s[2] += c;
        s[3] += d;
        s[4] += e;
        s[5] += f;
        s[6] += g;
        s[7] += h;
    }

    void update(const uint8_t* p, size_t n) {
        nbits += (uint64_t)n * 8;
        while (n) {
            size_t take = 64 - nbuf;
            if (take > n)
                take = n;
            std::memcpy(buf + nbuf, p, take);
            nbuf += take;
            p += take;
            n -= take;
            if (nbuf == 64) {
                block(buf);
                nbuf = 0;
            }
        }
    }

    void final(uint8_t out[32]) {
        uint8_t pad[64 + 8];
        size_t np = 0;
        pad[np++] = 0x80;
        size_t zeros = (nbuf + 1 <= 56) ? (56 - (nbuf + 1)) : (56 + 64 - (nbuf + 1));
        std::memset(pad + np, 0, zeros);
        np += zeros;
        for (int i = 7; i >= 0; i--)
            pad[np++] = (uint8_t)((nbits >> (8 * i)) & 0xff);
        update(pad, np);
        for (int i = 0; i < 8; i++) {
            out[4 * i] = (uint8_t)(s[i] >> 24);
            out[4 * i + 1] = (uint8_t)(s[i] >> 16);
            out[4 * i + 2] = (uint8_t)(s[i] >> 8);
            out[4 * i + 3] = (uint8_t)s[i];
        }
    }
};

static uint8_t g_secret[32];
static int g_have_secret = 0;

static void load_secret() {
    g_have_secret = 0;
    if (fcntl(kSecretFd, F_GETFD) < 0)
        return;
    int n = 0;
    while (n < 32) {
        ssize_t r = read(kSecretFd, g_secret + n, 32 - n);
        if (r <= 0)
            break;
        n += (int)r;
    }
    g_have_secret = (n == 32);
    close(kSecretFd);
}

static void deny_spawn() {
    prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);
    struct sock_filter filt[] = {
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, nr)),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_execve, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | (EPERM & 0xffff)),
#ifdef __NR_execveat
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_execveat, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | (EPERM & 0xffff)),
#endif
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_fork, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | (EPERM & 0xffff)),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_vfork, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | (EPERM & 0xffff)),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_ptrace, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | (EPERM & 0xffff)),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
    };
    struct sock_fprog prog;
    prog.len = (unsigned short)(sizeof(filt) / sizeof(filt[0]));
    prog.filter = filt;
    prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &prog);
}

static uint32_t step32(uint32_t s) {
    return (s << 1) | (((s >> 31) ^ (s >> 21) ^ (s >> 1) ^ (s >> 0)) & 1u);
}

struct Cfg {
    int pa = 10;
    int pb = 10;
    int phase = 0;
    int npkt = 40;
    int traffic = 0;
    uint32_t seed = 1;
    int rst = 0;
    int crdly = 0;
};

static void parse_cfg(int argc, char** argv, Cfg* c) {
    for (int i = 1; i < argc; i++) {
        auto eat = [&](const char* k, int* dst) {
            if (std::strcmp(argv[i], k) == 0 && i + 1 < argc) {
                *dst = std::atoi(argv[++i]);
                return true;
            }
            return false;
        };
        if (eat("--pa", &c->pa)) continue;
        if (eat("--pb", &c->pb)) continue;
        if (eat("--phase", &c->phase)) continue;
        if (eat("--npkt", &c->npkt)) continue;
        if (eat("--traffic", &c->traffic)) continue;
        if (eat("--rst", &c->rst)) continue;
        if (eat("--crdly", &c->crdly)) continue;
        if (std::strcmp(argv[i], "--seed") == 0 && i + 1 < argc) {
            c->seed = static_cast<uint32_t>(std::strtoul(argv[++i], nullptr, 10));
            continue;
        }
    }
}

struct Sim {
    Cfg cfg;
    Vcdc_fabric* dut;
    int clk_a = 0;
    int clk_b = 0;
    int64_t t = 0;
    int64_t next_a = 0;
    int64_t next_b = 0;
    int pos_a = 0;
    int pos_b = 0;

    int credits = 0;
    int beat_id = 0;
    int pkt_left = 0;
    int beat_ix = 0;
    int pkt_len = 1;
    int idle_gap = 0;
    long sent_beats = 0;
    long recv_beats = 0;
    long pcred_cnt = 0;
    long crret_cnt = 0;
    int done_send = 0;
    int pk_state = 0;
    int exp_len = 0;
    int exp_ix = 0;
    int next_id = 0;
    int owed_cr = 0;
    int cr_wait = 0;
    int pause = 0;
    uint32_t rnd_a = 1;
    uint32_t rnd_b = 1;
    int started = 0;
    int stall_a = 0;
    int last_recv = 0;
    int fail = 0;
    const char* why = "";

    uint8_t p_valid = 0, p_sop = 0, p_eop = 0;
    uint32_t p_data = 0;
    uint8_t c_ready = 0, cr_ret = 0;
    uint8_t rst_a_n = 0, rst_b_n = 0;

    int p_credit_s = 0;
    int c_valid_s = 0;
    int c_sop_s = 0;
    int c_eop_s = 0;
    uint32_t c_data_s = 0;

    void sample() {
        p_credit_s = dut->p_credit;
        c_valid_s = dut->c_valid;
        c_sop_s = dut->c_sop;
        c_eop_s = dut->c_eop;
        c_data_s = dut->c_data;
    }

    void fail_at(const char* w) {
        if (!fail) {
            fail = 1;
            why = w;
        }
    }

    void drive() {
        dut->clk_a = clk_a;
        dut->clk_b = clk_b;
        dut->rst_a_n = rst_a_n;
        dut->rst_b_n = rst_b_n;
        dut->p_valid = p_valid;
        dut->p_sop = p_sop;
        dut->p_eop = p_eop;
        dut->p_data = p_data;
        dut->c_ready = c_ready;
        dut->cr_ret = cr_ret;
        dut->eval();
    }

    void posedge_a() {
        pos_a++;
        if (!rst_a_n) {
            p_valid = 0;
            p_sop = 0;
            p_eop = 0;
            p_data = 0;
            return;
        }
        if (!started)
            return;

        if (p_credit_s) {
            pcred_cnt++;
            credits++;
        }

        int want = 0;
        if (!done_send && (pkt_left > 0 || beat_ix != 0)) {
            if (idle_gap > 0)
                idle_gap--;
            else
                want = 1;
        }

        if (want && credits > 0) {
            if (beat_ix == 0) {
                rnd_a = step32(rnd_a);
                pkt_len = (rnd_a & 15u) + 1;
            }
            p_valid = 1;
            p_sop = (beat_ix == 0);
            p_eop = (beat_ix == pkt_len - 1);
            p_data = ((beat_id & 0xffff) << 16) | ((beat_ix & 0xff) << 8) | (pkt_len & 0xff);
            credits--;
            sent_beats++;
            beat_id++;
            beat_ix++;
            if (beat_ix == pkt_len) {
                beat_ix = 0;
                pkt_left--;
                if (pkt_left == 0)
                    done_send = 1;
            }
            if (cfg.traffic) {
                rnd_a = step32(rnd_a);
                idle_gap = (rnd_a & 31u) % 21;
            }
        } else {
            p_valid = 0;
            p_sop = 0;
            p_eop = 0;
        }

        if (credits > kCredits || credits < 0)
            fail_at("credit_range");

        if (done_send && recv_beats == sent_beats) {
            stall_a = 0;
        } else if (recv_beats != last_recv) {
            last_recv = static_cast<int>(recv_beats);
            stall_a = 0;
        } else {
            stall_a++;
            if (stall_a > 250000)
                fail_at("stall");
        }
    }

    void posedge_b() {
        pos_b++;
        if (!rst_b_n) {
            c_ready = 0;
            cr_ret = 0;
            owed_cr = 0;
            cr_wait = 0;
            pause = 0;
            return;
        }
        if (!started)
            return;

        rnd_b = step32(rnd_b);

        /* DUT already sampled this cycle's c_ready. Score against that value,
           then NBA the next-cycle pin state — same as the Verilog TB. */
        int accept = c_valid_s && c_ready;
        int next_ready;
        int next_pause = pause;
        if (pause > 0) {
            next_pause = pause - 1;
            next_ready = 0;
        } else if ((rnd_b & 1023) == 0) {
            next_pause = 96;
            next_ready = 0;
        } else if (cfg.traffic == 0) {
            next_ready = 1;
        } else {
            next_ready = ((rnd_b & 7u) != 0);
        }

        int next_cr = 0;
        int next_owed = owed_cr;
        int next_wait = cr_wait;

        if (accept) {
            int id = (c_data_s >> 16) & 0xffff;
            int idx = (c_data_s >> 8) & 0xff;
            int len = c_data_s & 0xff;
            if (id != (next_id & 0xffff))
                fail_at("id_mismatch");
            if (pk_state == 0) {
                if (!c_sop_s)
                    fail_at("missing_sop");
                exp_len = len;
                exp_ix = 0;
                if (exp_len < 1 || exp_len > 16)
                    fail_at("bad_len");
            } else {
                if (c_sop_s)
                    fail_at("mid_sop");
            }
            if (idx != (exp_ix & 0xff))
                fail_at("idx_mismatch");
            if (len != (exp_len & 0xff))
                fail_at("len_mismatch");
            if (exp_ix == exp_len - 1) {
                if (!c_eop_s)
                    fail_at("missing_eop");
                pk_state = 0;
            } else {
                if (c_eop_s)
                    fail_at("early_eop");
                pk_state = 1;
            }
            next_id++;
            recv_beats++;
            exp_ix++;

            if (cfg.crdly == 0) {
                next_cr = 1;
                crret_cnt++;
            } else {
                next_owed = owed_cr + 1;
                if (cr_wait == 0) {
                    rnd_b = step32(rnd_b);
                    next_wait = (int)((rnd_b & 15u) % 12) + 1;
                }
            }
        }

        if (cfg.crdly != 0) {
            if (next_wait > 0)
                next_wait = next_wait - 1;
            if (next_wait == 0 && next_owed > 0 && !accept) {
                next_cr = 1;
                crret_cnt++;
                next_owed = next_owed - 1;
                if (next_owed > 0) {
                    rnd_b = step32(rnd_b);
                    next_wait = (int)((rnd_b & 15u) % 12) + 1;
                }
            }
        }

        c_ready = next_ready;
        cr_ret = next_cr;
        pause = next_pause;
        owed_cr = next_owed;
        cr_wait = next_wait;
    }
};

static void grade_write(int ok, long sent, long recv, long pcred, long crret, const char* why) {
    char payload[128];
    int pn = std::snprintf(payload, sizeof(payload), "%d %ld %ld %ld %ld",
                           ok, sent, recv, pcred, crret);
    char mac[65];
    mac[0] = '0';
    mac[1] = '\0';
    if (g_have_secret && pn > 0) {
        Sha256 h;
        h.init();
        h.update(g_secret, 32);
        h.update(reinterpret_cast<const uint8_t*>(payload), static_cast<size_t>(pn));
        uint8_t dig[32];
        h.final(dig);
        for (int i = 0; i < 32; i++)
            std::snprintf(mac + 2 * i, 3, "%02x", dig[i]);
        mac[64] = '\0';
    }
    char buf[320];
    int n = std::snprintf(buf, sizeof(buf), "GRADE %s %s %s\n",
                          payload, mac, why ? why : "");
    if (n > 0 && fcntl(kGradeFd, F_GETFD) >= 0) {
        ssize_t off = 0;
        while (off < n) {
            ssize_t w = write(kGradeFd, buf + off, static_cast<size_t>(n - off));
            if (w <= 0)
                break;
            off += w;
        }
    }
}

int main(int argc, char** argv) {
    /* Consume the per-run secret before any DUT eval (Verilog initial / $c). */
    load_secret();
    prctl(PR_SET_PDEATHSIG, SIGKILL);
    prctl(PR_SET_DUMPABLE, 0);
    deny_spawn();

    Verilated::commandArgs(argc, argv);
    Cfg cfg;
    parse_cfg(argc, argv, &cfg);

    Vcdc_fabric dut;
    Sim s;
    s.cfg = cfg;
    s.dut = &dut;
    s.pkt_left = cfg.npkt;
    s.rnd_a = cfg.seed ^ 0xA5A51234u;
    s.rnd_b = cfg.seed ^ 0x5A5A9BDFu;
    s.next_a = cfg.pa / 2;
    s.next_b = cfg.phase + cfg.pb / 2;

    auto tick_to = [&](int64_t target) {
        while (s.t < target && !s.fail && !Verilated::gotFinish()) {
            int64_t nxt = s.next_a < s.next_b ? s.next_a : s.next_b;
            s.t = nxt;
            int edge_a = (s.t == s.next_a);
            int edge_b = (s.t == s.next_b);
            int rise_a = edge_a && (s.clk_a == 0);
            int rise_b = edge_b && (s.clk_b == 0);
            if (rise_a || rise_b)
                s.sample();
            if (edge_a) {
                s.clk_a ^= 1;
                s.next_a += cfg.pa / 2;
            }
            if (edge_b) {
                s.clk_b ^= 1;
                s.next_b += cfg.pb / 2;
            }
            s.drive();
            if (rise_a)
                s.posedge_a();
            if (rise_b)
                s.posedge_b();
            if ((edge_a && s.clk_a == 0) || (edge_b && s.clk_b == 0))
                s.drive();
        }
    };

    auto wait_pos_a = [&](int n) {
        int base = s.pos_a;
        while (s.pos_a < base + n && !s.fail && !Verilated::gotFinish())
            tick_to(s.t + 1);
    };
    auto wait_pos_b = [&](int n) {
        int base = s.pos_b;
        while (s.pos_b < base + n && !s.fail && !Verilated::gotFinish())
            tick_to(s.t + 1);
    };

    s.drive();
    if (cfg.rst == 0) {
        wait_pos_a(10);
        wait_pos_b(10);
        s.rst_a_n = 1;
        s.rst_b_n = 1;
    } else if (cfg.rst == 1) {
        wait_pos_a(10);
        s.rst_a_n = 1;
        wait_pos_b(14);
        s.rst_b_n = 1;
    } else {
        wait_pos_b(10);
        s.rst_b_n = 1;
        wait_pos_a(14);
        s.rst_a_n = 1;
    }
    if (cfg.pa >= cfg.pb)
        wait_pos_a(16);
    else
        wait_pos_b(16);

    s.credits = kCredits;
    s.stall_a = 0;
    s.last_recv = 0;
    s.started = 1;

    const int64_t wall = 2000000000LL;
    while (!s.fail && !Verilated::gotFinish() && s.t < wall) {
        if (s.done_send && s.recv_beats == s.sent_beats && s.owed_cr == 0 && s.pk_state == 0)
            break;
        tick_to(s.t + 1);
    }

    if (!s.fail) {
        int extra_a = 80;
        int extra_b = 80;
        int base_a = s.pos_a;
        int base_b = s.pos_b;
        while ((s.pos_a < base_a + extra_a || s.pos_b < base_b + extra_b) && !s.fail &&
               !Verilated::gotFinish() && s.t < wall)
            tick_to(s.t + 1);
        if (s.recv_beats != s.sent_beats)
            s.fail_at("count");
        else if (s.pcred_cnt != s.crret_cnt)
            s.fail_at("credit_count");
        else if (s.sent_beats == 0)
            s.fail_at("nothing_sent");
        else if (s.pk_state != 0)
            s.fail_at("truncated");
    }
    if (Verilated::gotFinish() && !s.fail)
        s.fail_at("dut_finish");
    if (s.t >= wall && !s.done_send)
        s.fail_at("wall_timeout");

    int ok = (!s.fail && s.sent_beats == s.recv_beats && s.sent_beats > 0 &&
              s.pcred_cnt == s.crret_cnt && s.pk_state == 0)
                 ? 1
                 : 0;
    grade_write(ok, s.sent_beats, s.recv_beats, s.pcred_cnt, s.crret_cnt, s.why);
    dut.final();
    return ok ? 0 : 1;
}
