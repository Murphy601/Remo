// Dual-clock beat FIFO + token FIFO for cr_ret -> p_credit.
// Depth 16; protocol only allows 8 in flight. Headroom covers pointer sync.

module cdc_afifo #(
    parameter DW = 34,
    parameter AW = 4
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
    input  wire        p_valid,
    input  wire        p_sop,
    input  wire        p_eop,
    input  wire [31:0] p_data,
    output wire        p_credit,
    output wire        c_valid,
    output wire        c_sop,
    output wire        c_eop,
    output wire [31:0] c_data,
    input  wire        c_ready,
    input  wire        cr_ret
);
    wire        data_full, data_empty;
    wire [33:0] data_rdata;

    cdc_afifo #(.DW(34), .AW(4)) u_data (
        .wclk   (clk_a),
        .wrst_n (rst_a_n),
        .wen    (p_valid),
        .wdata  ({p_sop, p_eop, p_data}),
        .wfull  (data_full),
        .rclk   (clk_b),
        .rrst_n (rst_b_n),
        .ren    (c_valid & c_ready),
        .rdata  (data_rdata),
        .rempty (data_empty)
    );

    assign c_valid = ~data_empty;
    assign c_sop   = data_empty ? 1'b0 : data_rdata[33];
    assign c_eop   = data_empty ? 1'b0 : data_rdata[32];
    assign c_data  = data_empty ? 32'b0 : data_rdata[31:0];

    wire cred_full, cred_empty;
    wire cred_bit;

    cdc_afifo #(.DW(1), .AW(4)) u_cred (
        .wclk   (clk_b),
        .wrst_n (rst_b_n),
        .wen    (cr_ret),
        .wdata  (1'b1),
        .wfull  (cred_full),
        .rclk   (clk_a),
        .rrst_n (rst_a_n),
        .ren    (~cred_empty),
        .rdata  (cred_bit),
        .rempty (cred_empty)
    );

    assign p_credit = ~cred_empty;
endmodule
