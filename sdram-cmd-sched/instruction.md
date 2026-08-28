# SDRAM command scheduler

Two masters on this chip are already taped out. They talk valid/ready. Your job is the scheduler in the middle: `/app/sdram_sched.v`, module name `sdram_sched`. It owns a 4-bank SDR SDRAM, closed-page, burst length 4. One clock. Do not rename pins. Do not add ports.

A smoke TB is in `/app/tb_smoke.v`. It is p0-only, a few write/read pairs, nothing more. The grader uses a sealed cycle-accurate scoreboard with both ports, refresh, tFAW, backpressure, and a cycle bound. If you only pass smoke you will fail.

## Pins

```
module sdram_sched (
    input  wire        clk,
    input  wire        rst_n,

    input  wire        p0_valid,
    output wire        p0_ready,
    input  wire        p0_we,
    input  wire [1:0]  p0_ba,
    input  wire [12:0] p0_row,
    input  wire [7:0]  p0_col,
    input  wire [63:0] p0_wdata,
    output wire        p0_rvalid,
    input  wire        p0_rready,
    output wire [63:0] p0_rdata,

    input  wire        p1_valid,
    output wire        p1_ready,
    input  wire        p1_we,
    input  wire [1:0]  p1_ba,
    input  wire [12:0] p1_row,
    input  wire [7:0]  p1_col,
    input  wire [63:0] p1_wdata,
    output wire        p1_rvalid,
    input  wire        p1_rready,
    output wire [63:0] p1_rdata,

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

`rst_n` is async assert, active low. It stays low at least 8 clocks. After it goes high, `cke` is 1 and stays 1. No X/Z on your outputs once `rst_n` is high. `p0_ready` / `p1_ready` stay 0 until init is done.

## DRAM

10 ns clock, 50% duty. Commands are sampled on the rising edge. `CS# RAS# CAS# WE#`:

- DESL / NOP: `cs_n=1` (or `cs_n=0` and `3'b111` on RAS/CAS/WE)
- ACT: `0011`
- RD:  `0101`
- WR:  `0100`
- PRE: `0010` (`a[10]=0` one bank, `a[10]=1` all banks)
- REF: `0001`
- MRS: `0000`

Closed-page. `a[10]=0` on RD and WR. Close with a separate PRE. `col[1:0]` are 0. On ACT, `a` is the row. On RD/WR, `a[7:0]` is the column.

Burst length 4, sequential, CL=3. Four 16-bit beats. Little-endian in the 64-bit word: beat 0 is `[15:0]`, then `[31:16]`, `[47:32]`, `[63:48]`.

Write DQ: you drive `dq_oe=1` and `dq_o` for 4 clocks starting the WR cycle. Read DQ: first beat on `dq_i` is CL clocks after the RD command, same rising-edge count. DQ is exclusive: a write burst (`WR` .. `WR+3`) must not overlap a read burst (`RD+CL` .. `RD+CL+3`).

Timing, in clocks:

`CL=3`, `BL=4`, `tRCD=3`, `tRP=3`, `tRAS=7`, `tRC=10`, `tRRD=2`, `tFAW=10`, `tWTR=2`, `tRTP=2`, `tWR=3`, `tRFC=10`, `tREFI=96`, `tMRD=2`.

- tRCD: ACT to RD/WR on that bank
- tRP: PRE to ACT or REF
- tRAS: ACT to PRE on that bank
- tRC: ACT to ACT on that bank
- tRRD: ACT to ACT, any bank
- tFAW: at most 4 ACT in any 10 consecutive clocks
- tWTR: last write beat to RD command
- tRTP: RD to PRE on that bank
- tWR: last write beat to PRE
- tRFC: REF to the next non-NOP
- tREFI: REF to the next REF, maximum. Early is fine. Never go past 96.
- After a read burst, the first WR command is the clock after the last read beat.

MRS value: `a = 13'h032` (BL=4, sequential, CL=3), `ba=0`.

Init, before any ACT/RD/WR: wait at least 8 clocks, PREA, tRP, REF, tRFC, REF, tRFC, MRS, tMRD. Extra NOPs in between are fine.

Refresh needs every bank precharged and tRP met. While tRFC is running, only NOP/DESL.

## Ports

A transfer is `p*_valid && p*_ready`. `we=1` is a write. `we=0` is a read.

At most 4 outstanding requests per port: accepted and not finished. A write finishes when you have issued its WR. A read finishes when `p*_rvalid && p*_rready` takes the 64-bit word.

Per-port order. Reads on a port come back in the order that port accepted them. The two ports are not ordered with each other. Both ports can have `valid` high on the same clock. Starving one port fails the dual-port runs.

`p*_rvalid` means `p*_rdata` is stable. If `rvalid && !rready`, hold the same word. `rready` drops, including long stretches.

The grader's addresses on the two ports do not alias, except the RAW run which reuses an address on the same port (write then read). Unwritten locations read as 0.

## What pass means

You will be run on at least:

| name | traffic |
|---|---|
| p0 reads | 32 reads on p0, p1 idle |
| dual read | 48 reads on each port, all 4 banks |
| same-port RAW | write then read the same address |
| R/W mix | both ports, reads and writes |
| refresh under load | long enough that extra REF is required |
| tFAW storm | rotating banks 0,1,2,3 |
| rready backpressure | dual reads, `rready` mostly low |
| late reset | `rst_n` held longer, then traffic |

Seeds are fixed inside the grader. Functional pass/fail only.

On every config:

- every accepted read returns the right 64-bit word, in per-port order
- every accepted write is issued as a WR with the right beats
- no DRAM timing violation, no illegal command, no DQ clash
- refresh interval never exceeds tREFI
- init happens before the first ACT
- both ports finish their work
- the run ends before the cycle bound the testbench applies

A scheduler that only ever uses one bank, or that never refreshes, will not pass. A design that only wires p0 will not pass.

Synthesizable Verilog is enough. Verilog-2001 is fine. One file, `/app/sdram_sched.v`.

Smoke, if you want it:

```
cd /app
iverilog -g2005 -o smoke tb_smoke.v sdram_sched.v && vvp smoke
```

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
