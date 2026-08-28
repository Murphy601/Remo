# clkA/clkB credit fabric

Two blocks on this chip are already taped out at the pin level. One produces variable-length packets on `clk_a`. The other consumes them on `clk_b`. Your job is the fabric in the middle: `/app/cdc_fabric.v`, module name `cdc_fabric`.

There is no ready/valid backpressure on the producer pin. Credits are the only throttle. Do not rename pins. Do not add ports. Do not require the two clocks to be related.

A smoke TB is in `/app/tb_smoke.v`. It is a 1:1, 40-packet sanity check, nothing more. The grader uses a sealed scoreboard with other ratios, phase offsets, reset orders, and traffic. If you only pass smoke you will fail.

## Pins

```
module cdc_fabric (
    input  wire        clk_a,
    input  wire        rst_a_n,
    input  wire        clk_b,
    input  wire        rst_b_n,

    // producer, clk_a domain
    input  wire        p_valid,
    input  wire        p_sop,
    input  wire        p_eop,
    input  wire [31:0] p_data,
    output wire        p_credit,

    // consumer, clk_b domain
    output wire        c_valid,
    output wire        c_sop,
    output wire        c_eop,
    output wire [31:0] c_data,
    input  wire        c_ready,
    input  wire        cr_ret
);
```

`rst_a_n` / `rst_b_n` are async assert, active low. Each stays low for at least 8 of its own clocks. They do not deassert on the same cycle; some runs release A first, some B first. After the later release, traffic starts 16 cycles of the slower clock later. While a domain is in reset its outputs from you must be 0 (`p_credit` on A, `c_valid/c_sop/c_eop/c_data` on B). No X/Z on those after that domain leaves reset.

## Credits

`CREDITS = 8`.

The producer model (not you) starts at 8 after both resets are high. You do not mint those 8.

- Producer may assert `p_valid` only when its local count is > 0. One beat consumes one credit the same `clk_a` cycle.
- A 1-cycle `p_credit` pulse on `clk_a` gives one credit back. Pulse it high for exactly one `clk_a` cycle per returned credit. Do not pulse while `rst_a_n` is low.
- `p_valid` is a fire-and-forget beat. There is no `p_ready`. If `p_valid` is 1, you take that beat this cycle. The producer will never have more than 8 beats that have been sent and not yet matched by a `p_credit`.
- `cr_ret` is a 1-cycle pulse on `clk_b`. The consumer pulses it once per beat it has already accepted (`c_valid && c_ready`), either on that accept cycle or later. It never pulses more `cr_ret` than accepted beats. It is allowed to pulse `cr_ret` on back-to-back `clk_b` cycles.
- Every `cr_ret` must become exactly one `p_credit`. If `clk_b` is faster than `clk_a`, several `cr_ret` pulses can land inside one `clk_a` period — you still owe that many `p_credit` pulses, serialized on `clk_a`. Dropping them deadlocks the producer.

In-flight (producer's view) = beats sent minus `p_credit` seen. That number stays in 0..8.

## Packets

Beats, not whole packets, are what credits count.

- Length 1..16 beats.
- First beat: `p_sop=1`. Last beat: `p_eop=1`. A 1-beat packet has both set.
- Middle beats: sop=0, eop=0.
- No empty packets. No sop in the middle. No back-to-back sop without an eop in between.
- `p_data` is opaque 32-bit. Same bits, same order, same sop/eop, out the other side.
- A packet may stall mid-packet waiting for credits. Do not merge packets or insert beats.

Consumer side is ordinary valid/ready:

- `c_valid` means the current `c_data/c_sop/c_eop` are stable and can be taken.
- Transfer when `c_valid && c_ready`.
- If `c_valid && !c_ready`, hold the same beat.

`c_valid` stays 0 until you actually have a beat.

The consumer drops `c_ready`, including pauses long enough that several beats sit in the fabric and then drain on back-to-back `clk_b` cycles. Same-cycle `cr_ret` on a gulp is allowed.

## Clocks, as the grader models them

This is discrete-event RTL sim. No analogue metastability, no random sampling inside a synchronizer. Two independent clocks, both 50% duty.

Ratio `Fa:Fb` means:

- `clk_a` period = `Fb * 10 ns`
- `clk_b` period = `Fa * 10 ns`

So `5:1` is `clk_a` at 10 ns and `clk_b` at 50 ns. `1:7` is `clk_a` at 70 ns and `clk_b` at 10 ns.

Phase offset: first rising edge of `clk_b` is delayed `PHASE` ns from the first rising edge of `clk_a`. PHASE is one of 0, 3, 7.

You will be run on at least:

| name | ratio | PHASE ns | traffic | packets |
|---|---|---|---|---|
| equal burst | 1:1 | 0 | burst | 50000 |
| 3/2 burst | 3:2 | 3 | burst | 50000 |
| A-fast burst | 5:1 | 0 | burst | 50000 |
| B-fast burst | 1:7 | 7 | burst | 50000 |
| B-fast trickle | 1:7 | 3 | trickle | 8000 |
| A-fast trickle | 5:1 | 7 | trickle | 8000 |
| 3/2 trickle, late credits | 3:2 | 0 | trickle + delayed `cr_ret` | 8000 |
| equal, rst_b first | 1:1 | 7 | burst | 20000 |

Burst: producer sends on any cycle it has a credit. Trickle: producer also inserts 0..20 idle `clk_a` cycles between beats, and the consumer drops `c_ready` in stretches. Delayed `cr_ret`: accept and credit-return are not the same cycle; return is 1..12 `clk_b` cycles later, still one per accepted beat.

Seeds are fixed inside the grader. Functional pass/fail only.

## What pass means

On every config above, after the last packet is sent and the pipeline drains:

- beat count in == beat count out
- every beat matches (sop, eop, data) in order
- packet boundaries intact (no truncated packet at the end)
- number of `p_credit` pulses == number of `cr_ret` pulses
- no overflow, no underflow, no leftover occupancy that never returns a credit
- no watchdog timeout (the TB trips if nothing is sent and nothing is received for 20000 cycles of the faster clock while work remains)

A design that only works at 1:1 will not pass. A pulse-toggle on `cr_ret` will not pass `1:7`. Tying the two clocks together is not available to you; the TB drives them.

Synthesizable Verilog is enough. Verilog-2001 is fine. One file, `/app/cdc_fabric.v`.

Smoke, if you want it:

```
cd /app
iverilog -g2005 -o smoke tb_smoke.v cdc_fabric.v && vvp smoke
```

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
