`timescale 1ns/1ps
// No cache: every CPU op is one word on the mem port. Legal data, too slow.
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
    localparam I = 2'd0, W = 2'd1, R = 2'd2, P = 2'd3;
    reg [1:0] st0, st1;
    reg       we0, we1;
    reg [15:0] a0, a1;
    reg [31:0] d0, d1, rd0, rd1;
    reg        rv0, rv1;
    reg        mv, mw, mrr;
    reg [15:0] ma;
    reg [31:0] md;
    reg        src;

    assign c0_ready  = rst_n && (st0 == I);
    assign c1_ready  = rst_n && (st1 == I);
    assign c0_rvalid = rv0;
    assign c1_rvalid = rv1;
    assign c0_rdata  = rd0;
    assign c1_rdata  = rd1;
    assign m_valid   = mv;
    assign m_we      = mw;
    assign m_addr    = ma;
    assign m_wdata   = md;
    assign m_rready  = mrr;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            st0 <= I; st1 <= I;
            we0 <= 1'b0; we1 <= 1'b0;
            a0 <= 16'h0; a1 <= 16'h0;
            d0 <= 32'h0; d1 <= 32'h0;
            rd0 <= 32'h0; rd1 <= 32'h0;
            rv0 <= 1'b0; rv1 <= 1'b0;
            mv <= 1'b0; mw <= 1'b0; mrr <= 1'b0;
            ma <= 16'h0; md <= 32'h0; src <= 1'b0;
        end else begin
            if (c0_valid && c0_ready) begin
                st0 <= W; we0 <= c0_we; a0 <= c0_addr; d0 <= c0_wdata;
            end
            if (c1_valid && c1_ready) begin
                st1 <= W; we1 <= c1_we; a1 <= c1_addr; d1 <= c1_wdata;
            end
            if (rv0 && c0_rready) begin rv0 <= 1'b0; st0 <= I; end
            if (rv1 && c1_rready) begin rv1 <= 1'b0; st1 <= I; end

            if (!mv && (st0 == W || st1 == W)) begin
                if (st0 == W && (st1 != W || src == 1'b0)) begin
                    mv <= 1'b1; mw <= we0; ma <= a0; md <= d0; src <= 1'b0; st0 <= R;
                end else begin
                    mv <= 1'b1; mw <= we1; ma <= a1; md <= d1; src <= 1'b1; st1 <= R;
                end
                mrr <= 1'b0;
            end else if (mv && m_ready) begin
                mv <= 1'b0;
                mrr <= 1'b1;
            end else if (m_rvalid && mrr) begin
                mrr <= 1'b0;
                if (src == 1'b0) begin
                    rd0 <= we0 ? d0 : m_rdata;
                    rv0 <= 1'b1;
                    st0 <= P;
                end else begin
                    rd1 <= we1 ? d1 : m_rdata;
                    rv1 <= 1'b1;
                    st1 <= P;
                end
            end
        end
    end
endmodule
