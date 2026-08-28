# clkA/clkB credit fabric

Two producer blocks and one consumer are already taped out. Your job is the fabric in the middle: `/app/cdc_fabric.v`, module name `cdc_fabric`.

There are two virtual channels. Each producer has its own pin, its own credit pool, and may fire on the same `clk_a` cycle as the other. The consumer is one valid/ready stream with a VC tag. Do not rename pins. Do not add ports. Do not require the two clocks to be related.

A smoke TB is in `/app/tb_smoke.v`. It is 1:1, VC0 only, 24 packets. It never dual-issues, never starves a VC, never returns two credits in one cycle. If you only pass smoke you will fail.

## Pins

```
module cdc_fabric (
    input  wire        clk_a,
    input  wire        rst_a_n,
    input  wire        clk_b,
    input  wire        rst_b_n,

    // VC0 producer, clk_a
    input  wire        p0_valid,
    input  wire        p0_sop,
    input  wire        p0_eop,
    input  wire [31:0] p0_data,
    output wire        p0_credit,

    // VC1 producer, clk_a
    input  wire        p1_valid,
    input  wire        p1_sop,
    input  wire        p1_eop,
    input  wire [31:0] p1_data,
    output wire        p1_credit,

    // consumer, clk_b
    output wire        c_valid,
    output wire        c_sop,
    output wire        c_eop,
    output wire        c_vc,
    output wire [31:0] c_data,
    input  wire        c_ready,
    input  wire [1:0]  c_allow,
    input  wire [1:0]  cr0_n,
    input  wire [1:0]  cr1_n
);
```

`rst_a_n` / `rst_b_n` are async assert, active low. Each stays low for at least 8 of its own clocks. They do not deassert on the same cycle. After the later release, traffic starts 16 cycles of the slower clock later. While a domain is in reset its outputs from you must be 0. No X/Z on those after that domain leaves reset.

## Two producers, same clock

`p0_*` and `p1_*` are independent. Both `p*_valid` may be 1 on the same `clk_a` cycle. There is no `p_ready`. If a valid is 1, you take that beat that cycle. Dropping one because you only have a single write port is a fail.

Each producer may stall mid-packet waiting for its own credits. Do not merge packets, do not move a beat to the other VC, do not insert beats.

## Credits

`CREDITS = 4` per VC. The two pools do not share.

Each producer model starts at 4 after both resets are high. You do not mint those 4.

- A producer asserts `p*_valid` only when its local count is > 0. One beat consumes one credit the same `clk_a` cycle.
- `p0_credit` / `p1_credit` are 1-cycle pulses on `clk_a`. One pulse returns one credit to that VC. Never pulse while that domain is in reset. Never pulse the other VC's pin for a credit that belongs here.
- In-flight per VC (producer's view) stays in 0..4.
- `cr0_n` / `cr1_n` are counts on `clk_b`, 0, 1, or 2. They are the number of credits returned for that VC this cycle, for beats the consumer has already accepted. They can both be nonzero the same cycle. They never over-return.
- Every credit in `cr0_n` must become exactly one `p0_credit` pulse (same for VC1). If `clk_b` is faster, several counts can land inside one `clk_a` period — serialize the pulses on `clk_a`. A return of 2 is two pulses, not one. Mixing VC0 returns into `p1_credit` deadlocks VC0.

## Packets

Credits count beats, not whole packets. Length 1..16. SOP on the first beat, EOP on the last, both on a 1-beat packet. `p*_data` is opaque 32-bit. Same bits, same order, same sop/eop, same VC, out the other side.

Per-VC order is preserved. Global order between VCs is not.

## Consumer: wormhole + allow mask

Ordinary valid/ready, plus:

- `c_vc` is 0 or 1 for the beat on `c_data`.
- Transfer when `c_valid && c_ready && c_allow[c_vc]`.
- If `c_valid && !c_ready`, hold the same beat.
- If `c_valid && c_ready && !c_allow[c_vc]`, that is also a hold. Do not pop.

Wormhole: once the consumer has accepted a SOP of a packet that is not also EOP, the next beat you present must be the rest of that packet. You may not switch VCs until that EOP is accepted. Mid-packet, `c_allow` for the locked VC may drop; hold.

Between packets (idle, or after EOP accepted): you may only *start* a VC if `c_allow` for that VC is 1. If only VC1 is allowed and only VC0 has data, sit with `c_valid` 0 until the mask or the occupancy changes. A locked mid-packet VC is the exception; that one you keep presenting.

`c_allow` is one-hot, both, or neither. It changes every cycle. Long stretches of `2'b01` then `2'b10` happen. If you always present VC0 when idle, VC1 never drains.

`c_valid` stays 0 until you actually have a beat you are presenting.

## Clocks

Discrete-event RTL sim. No analogue metastability. Two independent clocks, 50% duty.

Ratio `Fa:Fb` means `clk_a` period = `Fb * 10 ns`, `clk_b` period = `Fa * 10 ns`. PHASE is 0, 3, or 7 ns from the first rising `clk_a` to the first rising `clk_b`.

You will be run on at least:

| name | ratio | PHASE ns | traffic | packets per VC |
|---|---|---|---|---|
| equal burst | 1:1 | 0 | both burst, allow=11 | 20000 |
| 3/2 burst | 3:2 | 3 | both burst, allow=11 | 20000 |
| A-fast burst | 5:1 | 0 | both burst, allow=11 | 20000 |
| B-fast burst | 1:7 | 7 | both burst, allow=11 | 20000 |
| B-fast trickle | 1:7 | 3 | trickle + random allow | 6000 |
| allow starve | 1:1 | 0 | burst, long 01/10 allow stretches | 6000 |
| 3/2 packed late credits | 3:2 | 0 | trickle, delayed `cr*_n` of 1 or 2 | 6000 |
| equal, rst_b first | 1:1 | 7 | both burst, allow=11 | 10000 |

Burst: each producer sends on any cycle it has a credit. Both will dual-issue often. Trickle: 0..20 idle `clk_a` cycles between beats on each producer, and the consumer drops `c_ready` in stretches. Packed late credits: accept and credit-return are not the same cycle; a VC may later return 2 in one `clk_b` cycle.

Seeds are fixed. Functional pass/fail only.

## What pass means

On every config, after both producers finish and the fabric drains:

- per-VC beat count in == beat count out
- every beat matches (vc, sop, eop, data) in per-VC order
- no VC interleave mid-packet
- packet boundaries intact
- `p0_credit` pulses == sum of `cr0_n` (same for VC1)
- no overflow, no underflow, no leftover occupancy
- no watchdog timeout

A single async FIFO that muxes the two valids will drop a dual-issue beat. A pulse-toggle on `cr0_n[0]` will drop a return of 2 and will die on `1:7`. Tying the clocks together is not available; the TB drives them.

Synthesizable Verilog is enough. Verilog-2001 is fine. One file, `/app/cdc_fabric.v`.

Smoke, if you want it (VC0 only):

```
cd /app
iverilog -g2005 -o smoke tb_smoke.v cdc_fabric.v && vvp smoke
```

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
