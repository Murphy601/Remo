# sdr4_mc

Write `/app/sdr4_mc.v`, module `sdr4_mc`. It is a memory controller: two host ports on one side, a 16-bit SDR SDRAM on the other. Four banks. Closed page. Burst length 4. One clock (10 ns, 50% duty). The pin list below is the whole interface.

`/app/tb_sdr.v` is a local iverilog check — host m0 only, four stores then four loads. Hidden tests drive both hosts and score the DRAM command pins. The local check is not the grade.

## Interface

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

`rst_n` async, active low, held at least 8 cycles. After release, `cke` is 1 for the rest of the run. Host ready bits stay 0 until mode-register programming has finished. After reset, do not leave X or Z on outputs.

Host handshake is `m*_valid && m*_ready` on the rising edge. `m*_wr=1` writes; `m*_wr=0` reads. Depth 4 per host: a request counts until its WR goes out (writes) or until `m*_rvalid && m*_rready` (reads). Reads on one host come back in accept order. The two hosts are not ordered with each other. Both valids may be high together. Leave one host idle on a dual-host run and that run fails.

`m*_rvalid` holds `m*_rdata` until `m*_rready`. The tests drop `m*_rready` for long stretches.

Addresses from the two hosts do not collide, except one RAW sequence that writes then reads the same line on the same host. A location that was never written reads as 0.

## SDRAM pins

Sample commands on the rising edge. Encoding is `CS# RAS# CAS# WE#`:

| command | encoding | notes |
|---|---|---|
| DESL | `cs_n=1` | NOP if `cs_n=0` and RAS/CAS/WE are 111 |
| ACT | 0011 | `a` = row |
| RD | 0101 | `a[7:0]` = column, `a[10]=0` |
| WR | 0100 | same column rules |
| PRE | 0010 | `a[10]=0` one bank, `a[10]=1` all banks |
| REF | 0001 | all banks idle, tRP already met |
| MRS | 0000 | `ba=0`, `a=13'h032` |

Closed page: no auto-precharge on RD/WR. Issue PRE yourself. Columns are BL-aligned (`col[1:0]=0`).

CL=3, sequential BL=4. A 64-bit host word is four 16-bit beats, low halfword first: `[15:0]`, `[31:16]`, `[47:32]`, `[63:48]`.

On WR you drive `dq_oe` and `dq_o` for four cycles starting that command. On RD the first `dq_i` beat is CL rising edges later. DQ is half-duplex. A write window `WR..WR+3` and a read window `RD+CL..RD+CL+3` must not overlap. After a write, wait tWTR from the last write beat before RD. After a read, the earliest WR is the cycle after the last read beat.

## Timing (clocks)

CL=3, BL=4, tRCD=3, tRP=3, tRAS=7, tRC=10, tRRD=2, tFAW=10, tWTR=2, tRTP=2, tWR=3, tRFC=10, tREFI=96, tMRD=2.

tRCD ACT→CAS same bank. tRP PRE→ACT or PRE→REF. tRAS ACT→PRE same bank. tRC ACT→ACT same bank. tRRD ACT→ACT any bank. tFAW: no more than four ACT in any 10 consecutive clocks. tRTP RD→PRE. tWR last write beat→PRE. tRFC after REF, NOP/DESL only. tREFI is a hard max between REF commands; issuing early is allowed.

Bring-up, before the first ACT/RD/WR: ≥8 idle clocks, PREA, tRP, REF, tRFC, REF, tRFC, MRS (`13'h032`), tMRD. Extra NOPs in the gaps are fine.

## Grade

The hidden scoreboard runs at least:

1. 32 reads on m0, m1 quiet
2. 48 reads on each host, all four banks
3. write-then-read the same address on m0
4. mixed reads and writes on both hosts
5. a long stream that needs refresh after bring-up
6. ACT traffic rotating banks 0-1-2-3 (tFAW)
7. the dual-read pattern with `m*_rready` mostly low
8. longer reset, then traffic

Seeds are baked into the scoreboard. Each run must:

- return every read with the right 64-bit word, in that host's accept order
- emit a WR with the right beats for every accepted write
- issue only legal commands, no DQ clash
- keep REF spacing ≤ tREFI
- finish MRS before the first ACT
- complete both hosts
- finish inside the cycle budget for that run

A controller that walks one bank at a time, or that skips refresh, misses the budget or the timing check. Verilog-2001, one file.

Local compile:

```
cd /app
iverilog -g2005 -o sdr tb_sdr.v sdr4_mc.v && vvp sdr
```

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
