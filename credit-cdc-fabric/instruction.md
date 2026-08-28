# clkA/clkB credit fabric

Two producer blocks on this chip are already taped out at the pin level, plus one consumer. The producers run on `clk_a`. The consumer runs on `clk_b`. Your job is the fabric in the middle: `/app/cdc_fabric.v`, module name `cdc_fabric`.

VC0 and VC1 are separate. Each producer has its own pins and its own credits. Both producers can have `valid` high on the same `clk_a` cycle. The consumer is one valid/ready bus with a `c_vc` bit saying which VC the beat belongs to. There is no `p_ready`. Credits are the only throttle. Do not rename pins. Do not add ports. Do not require the two clocks to be related.

A smoke TB is in `/app/tb_smoke.v`. It is a 1:1, VC0-only, 24-packet sanity check, nothing more. The grader uses a sealed scoreboard with other ratios, phase offsets, reset orders, allow masks, and traffic. If you only pass smoke you will fail.

## Pins

```
module cdc_fabric (
    input  wire        clk_a,
    input  wire        rst_a_n,
    input  wire        clk_b,
    input  wire        rst_b_n,

    // VC0 producer, clk_a domain
    input  wire        p0_valid,
    input  wire        p0_sop,
    input  wire        p0_eop,
    input  wire [31:0] p0_data,
    output wire        p0_credit,

    // VC1 producer, clk_a domain
    input  wire        p1_valid,
    input  wire        p1_sop,
    input  wire        p1_eop,
    input  wire [31:0] p1_data,
    output wire        p1_credit,

    // consumer, clk_b domain
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

`rst_a_n` / `rst_b_n` are async assert, active low. Each stays low for at least 8 of its own clocks. They do not deassert on the same cycle; some runs release A first, some B first. After the later release, traffic starts 16 cycles of the slower clock later. While a domain is in reset its outputs from you must be 0 (`p0_credit`/`p1_credit` on A, `c_valid`/`c_sop`/`c_eop`/`c_vc`/`c_data` on B). No X/Z on those after that domain leaves reset.

## Credits

`CREDITS = 4` per VC. The two pools are separate. The producer models (not you) each start at 4 after both resets are high. You do not mint those 4.

- A producer may assert `p0_valid` or `p1_valid` only when that VC's local count is > 0. One beat consumes one credit the same `clk_a` cycle.
- `p0_valid` and `p1_valid` are fire-and-forget. If either is 1, you take that beat this cycle. Both can be 1 the same cycle. The producer will never have more than 4 beats of a VC sent and not yet matched by that VC's `p*_credit`.
- `p0_credit` / `p1_credit` are 1-cycle pulses on `clk_a`. Pulse a pin high for exactly one `clk_a` cycle per returned credit on that VC. Do not pulse while `rst_a_n` is low. Do not put VC0's returns on `p1_credit` or the other way around.
- `cr0_n` / `cr1_n` are 2-bit counts on `clk_b`: 0, 1, or 2. That is how many credits come back for that VC this cycle, for beats the consumer already accepted (`c_valid && c_ready && c_allow[c_vc]`). Both counts can be nonzero the same cycle. The consumer never returns more credits than accepted beats.
- Every unit in `cr0_n` must become exactly one `p0_credit` pulse. Same mapping for VC1. A count of 2 is two pulses, not one. If `clk_b` is faster than `clk_a`, several counts can land inside one `clk_a` period — you still owe that many pulses, serialized on `clk_a`. Dropping them deadlocks that producer.

In-flight for a VC (producer's view) = beats sent minus `p*_credit` seen. That number stays in 0..4.

## Packets

Beats, not whole packets, are what credits count.

- Length 1..16 beats.
- First beat: sop=1. Last beat: eop=1. A 1-beat packet has both set.
- Middle beats: sop=0, eop=0.
- No empty packets. No sop in the middle. No back-to-back sop without an eop in between.
- `p0_data` / `p1_data` are opaque 32-bit. Same bits, same order, same sop/eop, same VC, out the other side.
- A packet may stall mid-packet waiting for credits. Do not merge packets or insert beats. Do not move a beat to the other VC.

Per-VC order is preserved. Order between VCs is not.

Consumer side is valid/ready plus an allow mask:

- `c_vc` is 0 or 1 for the beat on `c_data`.
- `c_valid` means the current `c_data`/`c_sop`/`c_eop`/`c_vc` are stable and can be taken.
- Transfer when `c_valid && c_ready && c_allow[c_vc]`.
- If `c_valid && !c_ready`, hold the same beat.
- If `c_valid && c_ready && !c_allow[c_vc]`, hold the same beat. Do not pop it.

Once a SOP has been accepted and that packet is not a 1-beat packet, the next beat you present has to be the rest of that packet. You do not switch VCs until that EOP is accepted. While you are in the middle of a packet, `c_allow` for that VC can go to 0; you still hold that beat.

When you are not in the middle of a packet, only start a VC if `c_allow` for it is 1. If VC1 is the only one allowed and you only have VC0 data, keep `c_valid` at 0 until that changes. If you always come out of idle on VC0, VC1 never gets out when the mask sits on `2'b10`.

`c_allow` can be `2'b00`, `2'b01`, `2'b10`, or `2'b11`, and it changes every cycle. Some runs leave it on one VC for a long stretch, then the other.

`c_valid` stays 0 until you actually have a beat you are presenting.

The consumer also drops `c_ready`, including pauses long enough that several beats sit in the fabric and then drain on back-to-back `clk_b` cycles.

## Clocks, as the grader models them

This is discrete-event RTL sim. No analogue metastability, no random sampling inside a synchronizer. Two independent clocks, both 50% duty.

Ratio `Fa:Fb` means:

- `clk_a` period = `Fb * 10 ns`
- `clk_b` period = `Fa * 10 ns`

So `5:1` is `clk_a` at 10 ns and `clk_b` at 50 ns. `1:7` is `clk_a` at 70 ns and `clk_b` at 10 ns.

Phase offset: first rising edge of `clk_b` is delayed `PHASE` ns from the first rising edge of `clk_a`. PHASE is one of 0, 3, 7.

You will be run on at least:

| name | ratio | PHASE ns | traffic | packets per VC |
|---|---|---|---|---|
| equal burst | 1:1 | 0 | burst, allow=11 | 20000 |
| 3/2 burst | 3:2 | 3 | burst, allow=11 | 20000 |
| A-fast burst | 5:1 | 0 | burst, allow=11 | 20000 |
| B-fast burst | 1:7 | 7 | burst, allow=11 | 20000 |
| B-fast trickle | 1:7 | 3 | trickle + changing allow | 6000 |
| allow starve | 1:1 | 0 | burst, long 01/10 allow stretches | 6000 |
| 3/2 trickle, late credits | 3:2 | 0 | trickle, delayed `cr*_n` of 1 or 2 | 6000 |
| equal, rst_b first | 1:1 | 7 | burst, allow=11 | 10000 |

Burst: each producer sends on any cycle it has a credit. Both of them doing that means a lot of cycles with both valids high. Trickle: each producer also inserts 0..20 idle `clk_a` cycles between beats, and the consumer drops `c_ready` in stretches. Delayed credits: accept and credit-return are not the same cycle; later the consumer can return 2 on one `clk_b` cycle for a VC.

Seeds are fixed inside the grader. Functional pass/fail only.

## What pass means

On every config above, after both producers are done and the pipeline drains:

- per-VC beat count in == beat count out
- every beat matches (vc, sop, eop, data) in per-VC order
- no VC switch in the middle of a packet
- packet boundaries intact (no truncated packet at the end)
- number of `p0_credit` pulses == sum of `cr0_n` (and the same for VC1)
- no overflow, no underflow, no leftover occupancy that never returns a credit
- no watchdog timeout (the TB trips if nothing is sent and nothing is received for 20000 cycles of the faster clock while work remains)

A design that only works at 1:1 will not pass. A design that only wires VC0 will not pass. A pulse-toggle on `cr0_n[0]` will not pass a return of 2, and it will not pass `1:7`. Tying the two clocks together is not available to you; the TB drives them.

Synthesizable Verilog is enough. Verilog-2001 is fine. One file, `/app/cdc_fabric.v`.

Smoke, if you want it:

```
cd /app
iverilog -g2005 -o smoke tb_smoke.v cdc_fabric.v && vvp smoke
```

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
