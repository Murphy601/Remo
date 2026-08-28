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

static const int kCredits = 4;
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

struct VcProd {
    int credits = 0;
    int beat_id = 0;
    int pkt_left = 0;
    int beat_ix = 0;
    int pkt_len = 1;
    int idle_gap = 0;
    int done_send = 0;
    long sent = 0;
    uint8_t valid = 0, sop = 0, eop = 0;
    uint32_t data = 0;
    uint32_t rnd = 1;
};

struct VcCons {
    int pk_state = 0;
    int exp_len = 0;
    int exp_ix = 0;
    int next_id = 0;
    long recv = 0;
    long pcred = 0;
    long crsum = 0;
    int owed = 0;
    int cr_wait = 0;
};

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
    int started = 0;
    int stall_a = 0;
    int last_recv = 0;
    int fail = 0;
    const char* why = "";
    int pause = 0;
    int allow_hold = 0;
    int allow_sel = 1;
    uint32_t rnd_b = 1;
    uint8_t rst_a_n = 0, rst_b_n = 0;
    uint8_t c_ready = 0;
    uint8_t c_allow = 3;
    uint8_t cr0_n = 0, cr1_n = 0;
    int p0c_s = 0, p1c_s = 0;
    int c_valid_s = 0, c_sop_s = 0, c_eop_s = 0, c_vc_s = 0;
    uint32_t c_data_s = 0;
    int held = 0;
    int held_vc = 0, held_sop = 0, held_eop = 0;
    uint32_t held_data = 0;
    VcProd p[2];
    VcCons c[2];

    void sample() {
        p0c_s = dut->p0_credit;
        p1c_s = dut->p1_credit;
        c_valid_s = dut->c_valid;
        c_sop_s = dut->c_sop;
        c_eop_s = dut->c_eop;
        c_vc_s = dut->c_vc & 1;
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
        dut->p0_valid = p[0].valid;
        dut->p0_sop = p[0].sop;
        dut->p0_eop = p[0].eop;
        dut->p0_data = p[0].data;
        dut->p1_valid = p[1].valid;
        dut->p1_sop = p[1].sop;
        dut->p1_eop = p[1].eop;
        dut->p1_data = p[1].data;
        dut->c_ready = c_ready;
        dut->c_allow = c_allow;
        dut->cr0_n = cr0_n;
        dut->cr1_n = cr1_n;
        dut->eval();
    }

    void step_prod(int v, int credit_s) {
        VcProd& pr = p[v];
        if (credit_s) {
            c[v].pcred++;
            pr.credits++;
        }
        int want = 0;
        if (!pr.done_send && (pr.pkt_left > 0 || pr.beat_ix != 0)) {
            if (pr.idle_gap > 0)
                pr.idle_gap--;
            else
                want = 1;
        }
        if (want && pr.credits > 0) {
            if (pr.beat_ix == 0) {
                pr.rnd = step32(pr.rnd);
                pr.pkt_len = (int)(pr.rnd & 15u) + 1;
            }
            pr.valid = 1;
            pr.sop = (pr.beat_ix == 0);
            pr.eop = (pr.beat_ix == pr.pkt_len - 1);
            pr.data = ((pr.beat_id & 0xffff) << 16) | ((pr.beat_ix & 0xff) << 8) | (pr.pkt_len & 0xff);
            pr.credits--;
            pr.sent++;
            pr.beat_id++;
            pr.beat_ix++;
            if (pr.beat_ix == pr.pkt_len) {
                pr.beat_ix = 0;
                pr.pkt_left--;
                if (pr.pkt_left == 0)
                    pr.done_send = 1;
            }
            if (cfg.traffic == 1) {
                pr.rnd = step32(pr.rnd);
                pr.idle_gap = (int)(pr.rnd & 31u) % 21;
            }
        } else {
            pr.valid = 0;
            pr.sop = 0;
            pr.eop = 0;
        }
        if (pr.credits > kCredits || pr.credits < 0)
            fail_at(v ? "credit_range1" : "credit_range0");
    }

    void posedge_a() {
        pos_a++;
        if (!rst_a_n) {
            p[0].valid = p[0].sop = p[0].eop = 0;
            p[1].valid = p[1].sop = p[1].eop = 0;
            return;
        }
        if (!started)
            return;
        step_prod(0, p0c_s);
        step_prod(1, p1c_s);
        long recv = c[0].recv + c[1].recv;
        long sent = p[0].sent + p[1].sent;
        int both_done = p[0].done_send && p[1].done_send;
        if (both_done && recv == sent) {
            stall_a = 0;
        } else if (recv != last_recv) {
            last_recv = (int)recv;
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
            c_allow = 0;
            cr0_n = 0;
            cr1_n = 0;
            pause = 0;
            allow_hold = 0;
            allow_sel = 1;
            held = 0;
            return;
        }
        if (!started)
            return;

        rnd_b = step32(rnd_b);

        int allow_now = c_allow;
        int ready_now = c_ready;
        int acc = c_valid_s && ready_now && ((allow_now >> c_vc_s) & 1);
        int mid = (c_vc_s == 0 || c_vc_s == 1) ? (c[c_vc_s].pk_state != 0) : 0;
        int must_hold = c_valid_s && !acc && (!ready_now || mid);

        if (held) {
            if (!c_valid_s || c_vc_s != held_vc || c_sop_s != held_sop ||
                c_eop_s != held_eop || c_data_s != held_data)
                fail_at("hold");
        }
        if (must_hold) {
            held = 1;
            held_vc = c_vc_s;
            held_sop = c_sop_s;
            held_eop = c_eop_s;
            held_data = c_data_s;
        } else {
            held = 0;
        }

        int next_ready;
        int next_pause = pause;
        int next_allow;
        int next_hold = allow_hold;
        int next_sel = allow_sel;
        if (pause > 0) {
            next_pause = pause - 1;
            next_ready = 0;
        } else if ((rnd_b & 1023) == 0) {
            next_pause = 96;
            next_ready = 0;
        } else if (cfg.traffic == 0 || cfg.traffic == 2) {
            next_ready = 1;
        } else {
            next_ready = ((rnd_b & 7u) != 0);
        }

        if (cfg.traffic == 2) {
            if (allow_hold > 0) {
                next_hold = allow_hold - 1;
                next_allow = allow_sel;
            } else {
                next_sel = (allow_sel == 1) ? 2 : 1;
                next_hold = 80 + (int)(rnd_b & 31u);
                next_allow = next_sel;
            }
        } else if (cfg.traffic == 1) {
            int bits = (int)((rnd_b >> 10) & 3u);
            next_allow = bits == 0 ? 3 : bits;
        } else {
            next_allow = 3;
        }

        int next_cr0 = 0;
        int next_cr1 = 0;

        if (acc) {
            int v = c_vc_s;
            if (v != 0 && v != 1)
                fail_at("bad_vc");
            VcCons& co = c[v];
            int oth = v ^ 1;
            if (c[oth].pk_state != 0)
                fail_at("interleave");
            int id = (c_data_s >> 16) & 0xffff;
            int idx = (c_data_s >> 8) & 0xff;
            int len = c_data_s & 0xff;
            if (id != (co.next_id & 0xffff))
                fail_at(v ? "id_mismatch1" : "id_mismatch0");
            if (co.pk_state == 0) {
                if (!c_sop_s)
                    fail_at("missing_sop");
                co.exp_len = len;
                co.exp_ix = 0;
                if (co.exp_len < 1 || co.exp_len > 16)
                    fail_at("bad_len");
            } else {
                if (c_sop_s)
                    fail_at("mid_sop");
            }
            if (idx != (co.exp_ix & 0xff))
                fail_at("idx_mismatch");
            if (len != (co.exp_len & 0xff))
                fail_at("len_mismatch");
            if (co.exp_ix == co.exp_len - 1) {
                if (!c_eop_s)
                    fail_at("missing_eop");
                co.pk_state = 0;
            } else {
                if (c_eop_s)
                    fail_at("early_eop");
                co.pk_state = 1;
            }
            co.next_id++;
            co.recv++;
            co.exp_ix++;

            if (cfg.crdly == 0) {
                if (v)
                    next_cr1 = 1;
                else
                    next_cr0 = 1;
                co.crsum += 1;
            } else {
                co.owed += 1;
                if (co.cr_wait == 0) {
                    rnd_b = step32(rnd_b);
                    co.cr_wait = (int)((rnd_b & 15u) % 12) + 1;
                }
            }
        }

        auto retire = [&](int v, int* ncr) {
            VcCons& co = c[v];
            if (cfg.crdly == 0)
                return;
            if (co.cr_wait > 0)
                co.cr_wait--;
            if (co.cr_wait == 0 && co.owed > 0 && !acc) {
                int n = 1;
                if (cfg.crdly == 2 && co.owed >= 2)
                    n = 2;
                *ncr = n;
                co.crsum += n;
                co.owed -= n;
                if (co.owed > 0) {
                    rnd_b = step32(rnd_b);
                    co.cr_wait = (int)((rnd_b & 15u) % 12) + 1;
                }
            }
        };
        retire(0, &next_cr0);
        retire(1, &next_cr1);

        c_ready = next_ready;
        c_allow = (uint8_t)next_allow;
        pause = next_pause;
        allow_hold = next_hold;
        allow_sel = next_sel;
        cr0_n = (uint8_t)next_cr0;
        cr1_n = (uint8_t)next_cr1;
    }

    long sent() const { return p[0].sent + p[1].sent; }
    long recv() const { return c[0].recv + c[1].recv; }
    long pcred() const { return c[0].pcred + c[1].pcred; }
    long crsum() const { return c[0].crsum + c[1].crsum; }
    int done_all() const { return p[0].done_send && p[1].done_send; }
    int pk_clear() const { return c[0].pk_state == 0 && c[1].pk_state == 0; }
    int owed_clear() const { return c[0].owed == 0 && c[1].owed == 0; }
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
    s.p[0].pkt_left = cfg.npkt;
    s.p[1].pkt_left = cfg.npkt;
    s.p[0].rnd = cfg.seed ^ 0xA5A51234u;
    s.p[1].rnd = cfg.seed ^ 0x3C6EF372u;
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

    s.p[0].credits = kCredits;
    s.p[1].credits = kCredits;
    s.stall_a = 0;
    s.last_recv = 0;
    s.started = 1;

    const int64_t wall = 2000000000LL;
    while (!s.fail && !Verilated::gotFinish() && s.t < wall) {
        if (s.done_all() && s.recv() == s.sent() && s.owed_clear() && s.pk_clear())
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
        if (s.c[0].recv != s.p[0].sent)
            s.fail_at("count0");
        else if (s.c[1].recv != s.p[1].sent)
            s.fail_at("count1");
        else if (s.c[0].pcred != s.c[0].crsum)
            s.fail_at("credit_count0");
        else if (s.c[1].pcred != s.c[1].crsum)
            s.fail_at("credit_count1");
        else if (s.p[0].sent == 0)
            s.fail_at("nothing_sent0");
        else if (s.p[1].sent == 0)
            s.fail_at("nothing_sent1");
        else if (!s.pk_clear())
            s.fail_at("truncated");
    }
    if (Verilated::gotFinish() && !s.fail)
        s.fail_at("dut_finish");
    if (s.t >= wall && !s.done_all())
        s.fail_at("wall_timeout");

    int ok = (!s.fail && s.sent() == s.recv() && s.sent() > 0 && s.pcred() == s.crsum() &&
              s.pk_clear() && s.p[0].sent > 0 && s.p[1].sent > 0 &&
              s.c[0].pcred == s.c[0].crsum && s.c[1].pcred == s.c[1].crsum)
                 ? 1
                 : 0;
    grade_write(ok, s.sent(), s.recv(), s.pcred(), s.crsum(), s.why);
    dut.final();
    return ok ? 0 : 1;
}
