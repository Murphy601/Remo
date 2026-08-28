// Two VC data FIFOs + wormhole output arbiter.
// Credit returns (0/1/2 per cycle) go through a token FIFO and serialize to pulses.

module cdc_afifo #(
    parameter DW = 34,
    parameter AW = 3
) (
    input  wire            wclk,
    input  wire            wrst_n,
    input  wire            wen,
    input  wire [DW-1:0]   wdata,
    output reg             wfull,
    input  wire            rclk,
    input  wire            rrst_n,
    input  wire            ren,
    output wire [DW-1:0]   rdata,
    output reg             rempty
);
    localparam DP = (1 << AW);

    reg [DW-1:0] mem [0:DP-1];
    reg [AW:0] wbin, wgray;
    reg [AW:0] rbin, rgray;
    reg [AW:0] wq1_rgray, wq2_rgray;
    reg [AW:0] rq1_wgray, rq2_wgray;

    wire wpush = wen & ~wfull;
    wire rpop  = ren & ~rempty;

    wire [AW:0] wbin_n  = wbin + {{AW{1'b0}}, wpush};
    wire [AW:0] wgray_n = (wbin_n >> 1) ^ wbin_n;
    wire [AW:0] rbin_n  = rbin + {{AW{1'b0}}, rpop};
    wire [AW:0] rgray_n = (rbin_n >> 1) ^ rbin_n;

    wire wfull_n  = (wgray_n == {~wq2_rgray[AW:AW-1], wq2_rgray[AW-2:0]});
    wire rempty_n = (rgray_n == rq2_wgray);

    assign rdata = mem[rbin[AW-1:0]];

    always @(posedge wclk or negedge wrst_n) begin
        if (!wrst_n) begin
            wbin  <= {AW+1{1'b0}};
            wgray <= {AW+1{1'b0}};
            wfull <= 1'b0;
        end else begin
            wbin  <= wbin_n;
            wgray <= wgray_n;
            wfull <= wfull_n;
            if (wpush)
                mem[wbin[AW-1:0]] <= wdata;
        end
    end

    always @(posedge rclk or negedge rrst_n) begin
        if (!rrst_n) begin
            rbin   <= {AW+1{1'b0}};
            rgray  <= {AW+1{1'b0}};
            rempty <= 1'b1;
        end else begin
            rbin   <= rbin_n;
            rgray  <= rgray_n;
            rempty <= rempty_n;
        end
    end

    always @(posedge wclk or negedge wrst_n) begin
        if (!wrst_n) begin
            wq1_rgray <= {AW+1{1'b0}};
            wq2_rgray <= {AW+1{1'b0}};
        end else begin
            wq1_rgray <= rgray;
            wq2_rgray <= wq1_rgray;
        end
    end

    always @(posedge rclk or negedge rrst_n) begin
        if (!rrst_n) begin
            rq1_wgray <= {AW+1{1'b0}};
            rq2_wgray <= {AW+1{1'b0}};
        end else begin
            rq1_wgray <= wgray;
            rq2_wgray <= rq1_wgray;
        end
    end
endmodule

module cdc_fabric (
    input  wire        clk_a,
    input  wire        rst_a_n,
    input  wire        clk_b,
    input  wire        rst_b_n,
    input  wire        p0_valid,
    input  wire        p0_sop,
    input  wire        p0_eop,
    input  wire [31:0] p0_data,
    output wire        p0_credit,
    input  wire        p1_valid,
    input  wire        p1_sop,
    input  wire        p1_eop,
    input  wire [31:0] p1_data,
    output wire        p1_credit,
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
    wire        e0, e1;
    wire [33:0] d0, d1;
    wire        f0, f1;

    reg valid_q, vc_q, sop_q, eop_q;
    reg [31:0] data_q;
    reg locked, lvc, rr;

    wire acc = valid_q & c_ready & c_allow[vc_q];
    wire hold_vc = (valid_q & ~eop_q) | (~valid_q & locked);
    wire hv = valid_q ? vc_q : lvc;
    wire start0 = ~e0 & c_allow[0];
    wire start1 = ~e1 & c_allow[1];
    wire cand1 = hold_vc ? (hv & ~e1) : (start1 & (~start0 | rr));
    wire cand0 = hold_vc ? (~hv & ~e0) : (start0 & ~cand1);
    wire has = cand0 | cand1;
    wire load = (~valid_q | acc) & has;
    wire nvc = cand1;

    assign c_valid = valid_q;
    assign c_vc    = vc_q;
    assign c_sop   = valid_q ? sop_q : 1'b0;
    assign c_eop   = valid_q ? eop_q : 1'b0;
    assign c_data  = valid_q ? data_q : 32'b0;

    cdc_afifo #(.DW(34), .AW(3)) u_d0 (
        .wclk(clk_a), .wrst_n(rst_a_n), .wen(p0_valid), .wdata({p0_sop, p0_eop, p0_data}), .wfull(f0),
        .rclk(clk_b), .rrst_n(rst_b_n), .ren(load & ~nvc), .rdata(d0), .rempty(e0)
    );
    cdc_afifo #(.DW(34), .AW(3)) u_d1 (
        .wclk(clk_a), .wrst_n(rst_a_n), .wen(p1_valid), .wdata({p1_sop, p1_eop, p1_data}), .wfull(f1),
        .rclk(clk_b), .rrst_n(rst_b_n), .ren(load & nvc), .rdata(d1), .rempty(e1)
    );

    always @(posedge clk_b or negedge rst_b_n) begin
        if (!rst_b_n) begin
            valid_q <= 1'b0;
            vc_q    <= 1'b0;
            sop_q   <= 1'b0;
            eop_q   <= 1'b0;
            data_q  <= 32'b0;
            locked  <= 1'b0;
            lvc     <= 1'b0;
            rr      <= 1'b0;
        end else begin
            if (load) begin
                valid_q <= 1'b1;
                vc_q    <= nvc;
                sop_q   <= nvc ? d1[33] : d0[33];
                eop_q   <= nvc ? d1[32] : d0[32];
                data_q  <= nvc ? d1[31:0] : d0[31:0];
            end else if (acc) begin
                valid_q <= 1'b0;
            end
            if (acc) begin
                if (eop_q) begin
                    locked <= 1'b0;
                    rr     <= ~vc_q;
                end else begin
                    locked <= 1'b1;
                    lvc    <= vc_q;
                end
            end
        end
    end

    wire        ce0, ce1;
    wire [1:0]  cv0, cv1;
    wire        cf0, cf1;
    cdc_afifo #(.DW(2), .AW(3)) u_c0 (
        .wclk(clk_b), .wrst_n(rst_b_n), .wen(|cr0_n), .wdata(cr0_n), .wfull(cf0),
        .rclk(clk_a), .rrst_n(rst_a_n), .ren(~ce0), .rdata(cv0), .rempty(ce0)
    );
    cdc_afifo #(.DW(2), .AW(3)) u_c1 (
        .wclk(clk_b), .wrst_n(rst_b_n), .wen(|cr1_n), .wdata(cr1_n), .wfull(cf1),
        .rclk(clk_a), .rrst_n(rst_a_n), .ren(~ce1), .rdata(cv1), .rempty(ce1)
    );

    reg [4:0] pend0, pend1;
    wire [4:0] add0 = ce0 ? 5'd0 : {3'b0, cv0};
    wire [4:0] add1 = ce1 ? 5'd0 : {3'b0, cv1};
    wire iss0 = (pend0 != 5'd0);
    wire iss1 = (pend1 != 5'd0);

    always @(posedge clk_a or negedge rst_a_n) begin
        if (!rst_a_n) begin
            pend0 <= 5'd0;
            pend1 <= 5'd0;
        end else begin
            pend0 <= pend0 + add0 - {4'b0, iss0};
            pend1 <= pend1 + add1 - {4'b0, iss1};
        end
    end

    assign p0_credit = rst_a_n & iss0;
    assign p1_credit = rst_a_n & iss1;
endmodule
