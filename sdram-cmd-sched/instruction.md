# sdr4_mc

The file you edit is `/app/sdr4_mc.v`. Module name `sdr4_mc`.

Two requestors, m0 and m1, valid/ready. Other side is a 16-bit SDR SDRAM: 4 banks, closed page, burst length 4. One clock, 10 ns.

`/app/tb_sdr.v` only drives m0. Four writes, four reads, iverilog. The grader is a cycle-accurate model on the DRAM pins and it uses both hosts, refresh, tFAW, backpressure, and a cycle cap. Getting smoke green is not the same as passing.

## Pins

```
module sdr4_mc (
    input  wire        clk,
    input  wire        rst_n,

    input  wire        m0_valid,
    output wire        m0_ready,
    input  wire        m0_wr,
    input  wire [1:0]  m0_ba,
    input  wire [12:0] m0_row,
    input  wire [7:0]  m0_col,
    input  wire [63:0] m0_wdata,
    output wire        m0_rvalid,
    input  wire        m0_rready,
    output wire [63:0] m0_rdata,

    input  wire        m1_valid,
    output wire        m1_ready,
    input  wire        m1_wr,
    input  wire [1:0]  m1_ba,
    input  wire [12:0] m1_row,
    input  wire [7:0]  m1_col,
    input  wire [63:0] m1_wdata,
    output wire        m1_rvalid,
    input  wire        m1_rready,
    output wire [63:0] m1_rdata,

    output wire        cke,
    output wire        cs_n,
    output wire        ras_n,
    output wire        cas_n,
    output wire        we_n,
    output wire [1:0]  ba,
    output wire [12:0] a,
    output wire [15:0] dq_o,
    output wire        dq_oe,
    input  wire [15:0] dq_i
);
```

`rst_n` is async, active low. It stays low for at least 8 clocks. After that `cke` is 1 and stays 1. Keep `m0_ready` / `m1_ready` at 0 until MRS is done. Once reset is released, no X or Z on the outputs.

## Hosts

A request is taken when valid and ready are both 1 that rising edge. `m*_wr` 1 is a write, 0 is a read.

At most 4 outstanding per port. A write finishes when you issue WR. A read finishes when `m*_rvalid && m*_rready` takes the word. Reads have to come back in the order that port accepted them. The two ports are unordered vs each other. Both valids can be high the same clock. If m1 never gets service on a two-port run, that run fails.

If rvalid is 1 and rready is 0, hold the same rdata. rready goes away for long stretches in some tests.

The two ports don't alias, except the RAW case which is write-then-read of the same address on the same port. Never-written memory reads as 0.

## DRAM

Commands sampled on posedge. `CS# RAS# CAS# WE#`:

- DESL: `cs_n=1`. Or `cs_n=0` and 111 on RAS/CAS/WE (NOP).
- ACT: 0011. `a` is the row.
- RD: 0101. `a[7:0]` is the column. `a[10]` stays 0.
- WR: 0100. Same column rule.
- PRE: 0010. `a[10]=0` one bank, `a[10]=1` all banks.
- REF: 0001.
- MRS: 0000. `ba=0`, `a=13'h032` (BL=4, sequential, CL=3).

Closed page. Don't set A10 on RD/WR; close with PRE. `col[1:0]` is 0.

CL=3, BL=4 sequential. Four 16-bit beats. Low halfword first: `[15:0]`, then `[31:16]`, `[47:32]`, `[63:48]`.

On a write you drive `dq_oe`/`dq_o` for 4 clocks starting at WR. On a read the first `dq_i` beat is 3 clocks after RD. Those two windows can't overlap. After the last write beat, wait tWTR before RD. After the last read beat, the next WR is the clock after that.

Clocks: CL=3, tRCD=3, tRP=3, tRAS=7, tRC=10, tRRD=2, tFAW=10, tWTR=2, tRTP=2, tWR=3, tRFC=10, tREFI=96, tMRD=2.

tRCD is ACT to RD/WR on that bank. tRP is PRE to ACT or REF. tRAS is ACT to PRE. tRC is ACT to ACT same bank. tRRD is ACT to ACT any bank. tFAW: at most 4 ACT in any 10 clocks. tRTP is RD to PRE. tWR is last write beat to PRE. tRFC after REF, only NOP. tREFI is the max from REF to REF. Early REF is fine. Going past 96 is not.

Init, before any ACT/RD/WR: wait 8, PREA, tRP, REF, tRFC, REF, tRFC, MRS, tMRD. Extra NOPs between those are ok. REF needs all banks precharged and tRP done.

## What the TB actually checks

Runs include:

| run | what |
|---|---|
| m0 reads | 32 reads on m0, m1 idle |
| both ports | 48 reads each, all 4 banks |
| RAW | write then read the same line on m0 |
| mix | reads and writes, both ports |
| refresh | long enough that you have to REF again after init |
| tFAW | banks 0,1,2,3 rotating |
| backpressure | dual reads, rready mostly 0 |
| late reset | rst_n held extra, then go |

Right data, in the order that port accepted the reads. Writes have to actually go out as WR with those beats. Command timing has to hold, DQ included, and REF spacing stays under tREFI. MRS before the first ACT. Both ports finish. And it has to be inside the cycle bound; walking one bank at a time is too slow. Skip refresh and you fail tREFI. Only implementing m0 fails the two-port runs.

One Verilog file is all you turn in. 2001 is fine.

```
cd /app
iverilog -g2005 -o sdr tb_sdr.v sdr4_mc.v && vvp sdr
```

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
