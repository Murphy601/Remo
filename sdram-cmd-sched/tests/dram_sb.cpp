#include "Vsdr4_mc.h"
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

static const int kScoreFd = 12;
static const int kNonceFd = 11;

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
struct Digest256 {
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
    if (fcntl(kNonceFd, F_GETFD) < 0)
        return;
    int n = 0;
    while (n < 32) {
        ssize_t r = read(kNonceFd, g_secret + n, 32 - n);
        if (r <= 0)
            break;
        n += (int)r;
    }
    g_have_secret = (n == 32);
    close(kNonceFd);
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



#include <algorithm>
#include <deque>
#include <map>
#include <vector>

static uint32_t step32(uint32_t s) {
    return (s << 1) | (((s >> 31) ^ (s >> 21) ^ (s >> 1) ^ (s >> 0)) & 1u);
}

static const int CL = 3;
static const int T_RCD = 3;
static const int T_RP = 3;
static const int T_RAS = 7;
static const int T_RC = 10;
static const int T_RRD = 2;
static const int T_FAW = 10;
static const int T_WTR = 2;
static const int T_RTP = 2;
static const int T_WR = 3;
static const int T_RFC = 10;
static const int T_REFI = 96;

enum Cmd { C_NOP, C_ACT, C_RD, C_WR, C_PRE, C_PREA, C_REF, C_MRS, C_ILL };

struct Cfg {
    int mode = 0;
    int n0 = 32;
    int n1 = 0;
    uint32_t seed = 1;
    int deadline = 2000;
    int rstextra = 0;
    int rready_mode = 0;
    int minref = 0;
};

struct Op {
    int we;
    int ba;
    int row;
    int col;
    uint64_t wdata;
};

struct Inf {
    Op op;
    int port;
    int seq;
    int st; // 0 accepted, 1 ACTed, 2 CASed
};

static uint64_t addr_key(int ba, int row, int col) {
    return ((uint64_t)(ba & 3) << 32) | ((uint64_t)(row & 0x1fff) << 16) | (uint64_t)(col & 0xff);
}

static uint64_t cell_key(int ba, int row, int col) {
    return ((uint64_t)(ba & 3) << 32) | ((uint64_t)(row & 0x1fff) << 8) | (uint64_t)(col & 0xff);
}

static Cmd decode(int cs_n, int ras_n, int cas_n, int we_n, int a10) {
    if (cs_n)
        return C_NOP;
    int k = (ras_n << 2) | (cas_n << 1) | we_n;
    if (k == 7)
        return C_NOP;
    if (k == 3)
        return C_ACT;
    if (k == 5)
        return C_RD;
    if (k == 4)
        return C_WR;
    if (k == 2)
        return a10 ? C_PREA : C_PRE;
    if (k == 1)
        return C_REF;
    if (k == 0)
        return C_MRS;
    return C_ILL;
}

static void fail_why(char* why, const char* s) {
    if (why[0] == 0)
        std::snprintf(why, 80, "%s", s);
}

static uint64_t rnd64(uint32_t* s) {
    uint64_t x = step32(*s);
    *s = step32(*s);
    x = (x << 32) | step32(*s);
    *s = step32(*s);
    return x;
}

static void build_ops(const Cfg& cfg, std::vector<Op> ops[2]) {
    uint32_t s = cfg.seed;
    auto push = [&](int p, int we, int ba, int row, int col, uint64_t w) {
        Op o;
        o.we = we;
        o.ba = ba & 3;
        o.row = row & 0x1fff;
        o.col = col & 0xfc;
        o.wdata = w;
        ops[p].push_back(o);
    };
    int n0 = cfg.n0;
    int n1 = cfg.n1;
    switch (cfg.mode) {
    case 2: // same-port RAW
        for (int i = 0; i < n0; i++) {
            uint64_t w = rnd64(&s) | 1ull;
            int ba = i & 3;
            int row = 20 + i;
            int col = 4;
            push(0, 1, ba, row, col, w);
            push(0, 0, ba, row, col, 0);
        }
        break;
    case 3: // R/W mix
        for (int i = 0; i < n0; i++) {
            int we = (i & 1);
            push(0, we, i & 3, 40 + i, (i & 3) * 4, rnd64(&s));
        }
        for (int i = 0; i < n1; i++) {
            int we = ((i + 1) & 1);
            push(1, we, (i + 1) & 3, 400 + i, (i & 3) * 4, rnd64(&s));
        }
        break;
    case 5: // tFAW storm
        for (int i = 0; i < n0; i++)
            push(0, 0, i & 3, 80 + i, 0, 0);
        for (int i = 0; i < n1; i++)
            push(1, 0, (i + 2) & 3, 600 + i, 8, 0);
        break;
    default: // reads, dual, refresh, backpressure, late reset
        for (int i = 0; i < n0; i++)
            push(0, 0, i & 3, i, (i & 7) * 4, 0);
        for (int i = 0; i < n1; i++)
            push(1, 0, i & 3, 300 + i, (i & 7) * 4, 0);
        break;
    }
}

static void parse_cfg(int argc, char** argv, Cfg* c) {
    for (int i = 1; i < argc; i++) {
        auto take = [&](int* dst) {
            if (i + 1 < argc)
                *dst = std::atoi(argv[++i]);
        };
        if (!std::strcmp(argv[i], "--mode"))
            take(&c->mode);
        else if (!std::strcmp(argv[i], "--n0"))
            take(&c->n0);
        else if (!std::strcmp(argv[i], "--n1"))
            take(&c->n1);
        else if (!std::strcmp(argv[i], "--deadline"))
            take(&c->deadline);
        else if (!std::strcmp(argv[i], "--rstextra"))
            take(&c->rstextra);
        else if (!std::strcmp(argv[i], "--rready"))
            take(&c->rready_mode);
        else if (!std::strcmp(argv[i], "--minref"))
            take(&c->minref);
        else if (!std::strcmp(argv[i], "--seed")) {
            if (i + 1 < argc)
                c->seed = (uint32_t)std::strtoul(argv[++i], nullptr, 10);
        }
    }
}

static void grade_write(int ok, long sent, long done, long nref, long cyc, const char* why) {
    char payload[128];
    int pn = std::snprintf(payload, sizeof(payload), "%d %ld %ld %ld %ld",
                           ok, sent, done, nref, cyc);
    char mac[65];
    mac[0] = '0';
    mac[1] = '\0';
    if (g_have_secret && pn > 0) {
        Digest256 h;
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
    int n = std::snprintf(buf, sizeof(buf), "SCORE %s %s %s\n",
                          payload, mac, why ? why : "");
    if (n > 0 && fcntl(kScoreFd, F_GETFD) >= 0) {
        ssize_t off = 0;
        while (off < n) {
            ssize_t w = write(kScoreFd, buf + off, static_cast<size_t>(n - off));
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

    Vsdr4_mc dut;

    std::vector<Op> ops[2];
    build_ops(cfg, ops);
    int n_ops = (int)ops[0].size() + (int)ops[1].size();
    int send_i[2] = {0, 0};
    int outst[2] = {0, 0};
    std::deque<uint64_t> exp_rd[2];
    std::deque<Inf> inf[2];
    std::map<uint64_t, uint64_t> logical;
    std::map<uint64_t, uint16_t> dram;
    std::map<int, uint16_t> rd_data;
    std::map<int, int> bus_wr;
    std::map<int, int> bus_rd;

    int bank_open[4] = {0, 0, 0, 0};
    int bank_row[4] = {0, 0, 0, 0};
    int last_act[4] = {-1000, -1000, -1000, -1000};
    int last_pre[4] = {-1000, -1000, -1000, -1000};
    int last_rd[4] = {-1000, -1000, -1000, -1000};
    int last_wr[4] = {-1000, -1000, -1000, -1000};
    int last_cas_we[4] = {0, 0, 0, 0};
    int saw_cas[4] = {0, 0, 0, 0};
    std::vector<int> act_times;
    int last_act_any = -1000;
    int last_ref = -10000;
    int last_mrs = -10000;
    int n_ref = 0, n_act = 0, n_rd = 0, n_wr = 0;
    int seen_prea = 0, seen_mrs = 0, refs_before_mrs = 0;
    int wr_left = 0;
    int wr_ba = 0, wr_row = 0, wr_col = 0, wr_beat = 0;
    uint64_t wr_word = 0;
    int sent = 0, done = 0;
    int seq = 0;
    int user_cmd = 0;
    uint32_t rrnd = cfg.seed ^ 0xA5A5u;
    char why[80];
    why[0] = 0;
    int ok = 1;

    auto die = [&](const char* s) {
        fail_why(why, s);
        ok = 0;
    };

    dut.clk = 0;
    dut.rst_n = 0;
    dut.m0_valid = 0;
    dut.m1_valid = 0;
    dut.m0_wr = 0;
    dut.m1_wr = 0;
    dut.m0_ba = 0;
    dut.m1_ba = 0;
    dut.m0_row = 0;
    dut.m1_row = 0;
    dut.m0_col = 0;
    dut.m1_col = 0;
    dut.m0_wdata = 0;
    dut.m1_wdata = 0;
    dut.m0_rready = 0;
    dut.m1_rready = 0;
    dut.dq_i = 0;
    dut.eval();

    int rst_hold = 12 + cfg.rstextra;
    int cyc = 0;
    int max_cyc = cfg.deadline;

    auto tick = [&]() {
        dut.clk = 0;
        dut.eval();
        dut.clk = 1;
        dut.eval();
    };

    for (int i = 0; i < rst_hold; i++) {
        dut.rst_n = 0;
        dut.dq_i = 0;
        tick();
        cyc++;
    }
    dut.rst_n = 1;

    int last_wr_beat = -1000;
    int last_rd_beat = -1000;

    while (cyc < max_cyc && ok) {
        auto it = rd_data.find(cyc);
        dut.dq_i = (it == rd_data.end()) ? 0 : it->second;

        rrnd = step32(rrnd);
        if (cfg.rready_mode == 0) {
            dut.m0_rready = 1;
            dut.m1_rready = 1;
        } else {
            dut.m0_rready = ((rrnd >> 3) & 3) == 0;
            dut.m1_rready = ((rrnd >> 7) & 3) == 0;
        }

        for (int p = 0; p < 2; p++) {
            int can = (p == 0) ? dut.m0_ready : dut.m1_ready;
            int more = send_i[p] < (int)ops[p].size();
            int drive = more && outst[p] < 4 && can;
            Op z;
            z.we = 0;
            z.ba = 0;
            z.row = 0;
            z.col = 0;
            z.wdata = 0;
            const Op& o = drive ? ops[p][send_i[p]] : z;
            if (p == 0) {
                dut.m0_valid = drive;
                dut.m0_wr = o.we;
                dut.m0_ba = o.ba;
                dut.m0_row = o.row;
                dut.m0_col = o.col;
                dut.m0_wdata = o.wdata;
            } else {
                dut.m1_valid = drive;
                dut.m1_wr = o.we;
                dut.m1_ba = o.ba;
                dut.m1_row = o.row;
                dut.m1_col = o.col;
                dut.m1_wdata = o.wdata;
            }
        }

        dut.clk = 0;
        dut.eval();
        int acc0 = dut.m0_valid && dut.m0_ready;
        int acc1 = dut.m1_valid && dut.m1_ready;
        int take0 = dut.m0_rvalid && dut.m0_rready;
        int take1 = dut.m1_rvalid && dut.m1_rready;
        uint64_t got0 = dut.m0_rdata;
        uint64_t got1 = dut.m1_rdata;
        dut.clk = 1;
        dut.eval();

        if (!dut.cke)
            die("cke");

        Cmd cmd = decode(dut.cs_n, dut.ras_n, dut.cas_n, dut.we_n, (dut.a >> 10) & 1);
        int ba = dut.ba & 3;
        int aa = dut.a & 0x1fff;

        if (last_ref >= 0 && (cyc - last_ref) > T_REFI)
            die("tREFI");

        if (cmd == C_ILL)
            die("bad_cmd");

        int rfc_busy = (n_ref > 0) && (cyc - last_ref < T_RFC);
        if (rfc_busy && cmd != C_NOP)
            die("tRFC");

        if (cmd == C_MRS) {
            if (seen_mrs && user_cmd)
                die("late_mrs");
            if (aa != 0x032)
                die("mrs_val");
            if (refs_before_mrs < 2)
                die("mrs_early");
            seen_mrs = 1;
            last_mrs = cyc;
        } else if (cmd == C_REF) {
            int all_closed = 1;
            for (int b = 0; b < 4; b++) {
                if (bank_open[b])
                    all_closed = 0;
                if (cyc - last_pre[b] < T_RP)
                    all_closed = 0;
            }
            if (!all_closed)
                die("ref_banks");
            if (!seen_prea)
                die("ref_no_prea");
            last_ref = cyc;
            n_ref++;
            if (!seen_mrs)
                refs_before_mrs++;
        } else if (cmd == C_PREA || cmd == C_PRE) {
            auto pre_one = [&](int b) {
                if (bank_open[b]) {
                    if (cyc - last_act[b] < T_RAS)
                        die("tRAS");
                    if (saw_cas[b]) {
                        if (last_cas_we[b]) {
                            if (cyc - (last_wr[b] + 3) < T_WR)
                                die("tWR");
                        } else {
                            if (cyc - last_rd[b] < T_RTP)
                                die("tRTP");
                        }
                    }
                    bank_open[b] = 0;
                }
                last_pre[b] = cyc;
            };
            if (cmd == C_PREA) {
                seen_prea = 1;
                for (int b = 0; b < 4; b++)
                    pre_one(b);
            } else {
                seen_prea = 1;
                pre_one(ba);
            }
        } else if (cmd == C_ACT) {
            if (!seen_mrs)
                die("act_before_mrs");
            if (last_mrs >= 0 && cyc - last_mrs < 2)
                die("tMRD");
            user_cmd = 1;
            if (bank_open[ba])
                die("act_open");
            if (cyc - last_pre[ba] < T_RP)
                die("tRP");
            if (cyc - last_act[ba] < T_RC)
                die("tRC");
            if (cyc - last_act_any < T_RRD)
                die("tRRD");
            int nwin = 0;
            for (int t : act_times)
                if (cyc - t < T_FAW)
                    nwin++;
            if (nwin >= 4)
                die("tFAW");
            bank_open[ba] = 1;
            bank_row[ba] = aa;
            last_act[ba] = cyc;
            last_act_any = cyc;
            saw_cas[ba] = 0;
            act_times.push_back(cyc);
            n_act++;

            Inf* hit = nullptr;
            int best = 1 << 30;
            for (int p = 0; p < 2; p++) {
                for (auto& e : inf[p]) {
                    if (e.st == 0 && e.op.ba == ba && e.op.row == aa && e.seq < best) {
                        best = e.seq;
                        hit = &e;
                    }
                }
            }
            if (!hit)
                die("act_orphan");
            else
                hit->st = 1;
        } else if (cmd == C_RD || cmd == C_WR) {
            if (!seen_mrs)
                die("cas_before_mrs");
            user_cmd = 1;
            if (!bank_open[ba])
                die("cas_closed");
            if (cyc - last_act[ba] < T_RCD)
                die("tRCD");
            if ((aa >> 10) & 1)
                die("ap");
            int col = aa & 0xff;
            if (col & 3)
                die("col_align");
            Inf* hit = nullptr;
            for (int p = 0; p < 2; p++) {
                for (auto& e : inf[p]) {
                    if (e.st == 1 && e.op.ba == ba && e.op.row == bank_row[ba])
                        hit = &e;
                }
            }
            if (!hit)
                die("cas_orphan");
            else {
                if ((cmd == C_WR) != hit->op.we)
                    die("cas_we");
                if (hit->op.col != col)
                    die("cas_col");
            }
            if (cmd == C_RD) {
                if (cyc - last_wr_beat < T_WTR)
                    die("tWTR");
                for (int k = 0; k < 4; k++) {
                    int t = cyc + CL + k;
                    if (bus_rd[t] || bus_wr[t])
                        die("dq_clash_r");
                    bus_rd[t] = 1;
                    uint16_t d = 0;
                    auto mit = dram.find(cell_key(ba, bank_row[ba], col + k));
                    if (mit != dram.end())
                        d = mit->second;
                    rd_data[t] = d;
                }
                last_rd[ba] = cyc;
                last_rd_beat = cyc + CL + 3;
                n_rd++;
            } else {
                if (cyc <= last_rd_beat)
                    die("tRTW");
                for (int k = 0; k < 4; k++) {
                    if (bus_rd[cyc + k] || bus_wr[cyc + k])
                        die("dq_clash_w");
                    bus_wr[cyc + k] = 1;
                }
                last_wr[ba] = cyc;
                last_wr_beat = cyc + 3;
                wr_left = 4;
                wr_ba = ba;
                wr_row = bank_row[ba];
                wr_col = col;
                wr_beat = 0;
                wr_word = hit ? hit->op.wdata : 0;
                n_wr++;
            }
            saw_cas[ba] = 1;
            last_cas_we[ba] = (cmd == C_WR);
            if (hit)
                hit->st = 2;
            if (hit && hit->op.we) {
                done++;
                outst[hit->port]--;
            }
        }

        if (wr_left > 0) {
            if (!dut.dq_oe)
                die("dq_oe");
            uint16_t beat = (uint16_t)((wr_word >> (16 * wr_beat)) & 0xffff);
            if ((uint16_t)dut.dq_o != beat)
                die("wr_data");
            dram[cell_key(wr_ba, wr_row, wr_col + wr_beat)] = (uint16_t)dut.dq_o;
            wr_beat++;
            wr_left--;
        } else if (dut.dq_oe && cmd != C_WR) {
            die("dq_oe_idle");
        }

        auto take_acc = [&](int p, int acc, uint64_t got, int take) {
            if (acc) {
                Op o = ops[p][send_i[p]++];
                Inf e;
                e.op = o;
                e.port = p;
                e.seq = seq++;
                e.st = 0;
                inf[p].push_back(e);
                outst[p]++;
                sent++;
                uint64_t ak = addr_key(o.ba, o.row, o.col);
                if (o.we)
                    logical[ak] = o.wdata;
                else {
                    uint64_t w = 0;
                    auto lit = logical.find(ak);
                    if (lit != logical.end())
                        w = lit->second;
                    exp_rd[p].push_back(w);
                }
            }
            if (take) {
                if (exp_rd[p].empty())
                    die("rd_extra");
                else if (got != exp_rd[p].front())
                    die("rd_data");
                else {
                    exp_rd[p].pop_front();
                    done++;
                    outst[p]--;
                }
            }
        };
        take_acc(0, acc0, got0, take0);
        take_acc(1, acc1, got1, take1);

        int all_sent = send_i[0] == (int)ops[0].size() && send_i[1] == (int)ops[1].size();
        int all_done = (done == n_ops);
        if (all_sent && all_done)
            break;
        cyc++;
    }

    if (ok) {
        if (done != n_ops)
            die("timeout");
        else if (n_ref < cfg.minref)
            die("minref");
        else if (!seen_mrs)
            die("no_mrs");
        else if (exp_rd[0].size() || exp_rd[1].size())
            die("rd_left");
    }

    grade_write(ok && done == n_ops, sent, done, n_ref, cyc, why);
    return (ok && done == n_ops) ? 0 : 1;
}
