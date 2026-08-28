// Stub. Replace the body. Pin list is frozen.
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

    assign p_credit = 1'b0;
    assign c_valid  = 1'b0;
    assign c_sop    = 1'b0;
    assign c_eop    = 1'b0;
    assign c_data   = 32'b0;

endmodule
