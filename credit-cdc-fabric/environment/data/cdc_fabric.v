// Stub. Replace the body. Pin list is frozen.
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
    assign p0_credit = 1'b0;
    assign p1_credit = 1'b0;
    assign c_valid   = 1'b0;
    assign c_sop     = 1'b0;
    assign c_eop     = 1'b0;
    assign c_vc      = 1'b0;
    assign c_data    = 32'b0;
endmodule
