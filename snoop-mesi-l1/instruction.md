# mesi_pair

Two cores, each with a tiny L1. They share one slow memory port. The caches have to stay coherent (MESI). File is `/app/mesi_pair.v`, module `mesi_pair`.

`/app/tb_coh.v` is iverilog smoke: core 0 writes a word, reads it back, memory is a dumb 8-cycle slave. The grader is a C++ model that runs both cores, conflicts, writebacks, and a cycle cap. Smoke is not the grade.

## Pins

```
module mesi_pair (
    input  wire        clk,
    input  wire        rst_n,

    input  wire        c0_valid,
    output wire        c0_ready,
    input  wire        c0_we,
    input  wire [15:0] c0_addr,
    input  wire [31:0] c0_wdata,
    output wire        c0_rvalid,
    input  wire        c0_rready,
    output wire [31:0] c0_rdata,

    input  wire        c1_valid,
    output wire        c1_ready,
    input  wire        c1_we,
    input  wire [15:0] c1_addr,
    input  wire [31:0] c1_wdata,
    output wire        c1_rvalid,
    input  wire        c1_rready,
    output wire [31:0] c1_rdata,

    output wire        m_valid,
    input  wire        m_ready,
    output wire        m_we,
    output wire [15:0] m_addr,
    output wire [31:0] m_wdata,
    input  wire        m_rvalid,
    output wire        m_rready,
    input  wire [31:0] m_rdata
);
```

`rst_n` async, active low, at least 8 clocks. After it goes high, no X/Z on your outputs. One outstanding request per core: `c*_ready` stays 0 until that core's `c*_rvalid && c*_rready` (reads AND writes both return a response; write rdata is don't-care). `c*_addr[1:0]` is 0.

Memory: word accesses. The TB slave takes a request when `m_valid && m_ready`, then 8 clocks later raises `m_rvalid` with `m_rdata` (writes still get that handshake, rdata unused). Hold `m_rvalid` until `m_rready`. Only one mem request in flight. Don't issue the next until the previous rsp is taken.

## Caches

Each core: 4 lines, direct mapped. Line is 16 bytes (4 words).

- index = `addr[5:4]`
- word = `addr[3:2]`
- tag = `addr[15:6]`

MESI on each line: I, S, E, M. Usual rules. At most one Modified copy. If someone is Modified or Exclusive, the other core's copy of that line is I. Shared can be on both. A read has to see the last completed write to that word, from either core. Same-core reads/writes stay in order.

Hits can answer without going to memory. Misses and upgrades use the mem port and/or a copy from the other L1 (snoop). If you replace a Modified line, write the whole line back (four word writes, addresses `line_base+0/+4/+8/+12`).

Fills are four word reads for the line. You can also copy a line from the other cache when it already has it; still need to get the states right (BusRd from M usually goes to S/S after the dirty data is written back or handed over).

## What fails

A design that just forwards every CPU access to the mem port will match data and still miss the cycle bound. A design that caches but ignores snoops will fail when core 0 writes and core 1 reads the same word. A design that never writebacks will lose dirty data on eviction.

## Tests

c0 writes a line then hammers it (that's the hit case). c0 stores, c1 loads that word. Two cores, same line, different words (false share). Ping-pong on one word. More than four dirty lines on one core so something has to write back. Both cores busy on disjoint lines. rready mostly low. A longer reset then traffic.

Right data. Per-core order. Don't drop responses. Stay under the cycle cap. Memory latency is 8, so you actually have to hit.

Verilog-2001, one file.

```
cd /app
iverilog -g2005 -o coh tb_coh.v mesi_pair.v && vvp coh
```

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
