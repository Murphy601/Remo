`timescale 1ns/1ps

// Core 0 write then read. 8-cycle mem slave. Not the grader.
module tb_coh;
    reg clk = 0;
    always #5 clk = ~clk;
    reg rst_n = 0;

    reg         c0_valid = 0;
    wire        c0_ready;
    reg         c0_we = 0;
    reg  [15:0] c0_addr = 0;
    reg  [31:0] c0_wdata = 0;
    wire        c0_rvalid;
    reg         c0_rready = 1;
    wire [31:0] c0_rdata;
    wire        c1_ready, c1_rvalid;
    wire [31:0] c1_rdata;

    wire        m_valid, m_we, m_rready;
    reg         m_ready = 0;
    wire [15:0] m_addr;
    wire [31:0] m_wdata;
    reg         m_rvalid = 0;
    reg  [31:0] m_rdata = 0;

    reg [31:0] mem [0:4095];
    integer i, waitc, fail, got;
    integer m_busy, m_cnt;
    reg m_isw;
    reg [15:0] m_a;
    reg [31:0] m_wd;

    mesi_pair dut (
        .clk(clk), .rst_n(rst_n),
        .c0_valid(c0_valid), .c0_ready(c0_ready), .c0_we(c0_we),
        .c0_addr(c0_addr), .c0_wdata(c0_wdata),
        .c0_rvalid(c0_rvalid), .c0_rready(c0_rready), .c0_rdata(c0_rdata),
        .c1_valid(1'b0), .c1_ready(c1_ready), .c1_we(1'b0),
        .c1_addr(16'b0), .c1_wdata(32'b0),
        .c1_rvalid(c1_rvalid), .c1_rready(1'b1), .c1_rdata(c1_rdata),
        .m_valid(m_valid), .m_ready(m_ready), .m_we(m_we),
        .m_addr(m_addr), .m_wdata(m_wdata),
        .m_rvalid(m_rvalid), .m_rready(m_rready), .m_rdata(m_rdata)
    );

    always @(posedge clk) begin
        if (!rst_n) begin
            m_busy <= 0;
            m_cnt <= 0;
            m_ready <= 1;
            m_rvalid <= 0;
        end else begin
            if (m_rvalid && m_rready)
                m_rvalid <= 0;
            if (!m_busy) begin
                m_ready <= 1;
                if (m_valid && m_ready) begin
                    m_busy <= 1;
                    m_cnt <= 8;
                    m_isw <= m_we;
                    m_a <= m_addr;
                    m_wd <= m_wdata;
                    m_ready <= 0;
                end
            end else begin
                m_ready <= 0;
                if (m_cnt != 0)
                    m_cnt <= m_cnt - 1;
                else if (!m_rvalid) begin
                    if (m_isw)
                        mem[m_a[13:2]] <= m_wd;
                    m_rdata <= m_isw ? 32'b0 : mem[m_a[13:2]];
                    m_rvalid <= 1;
                    m_busy <= 0;
                end
            end
        end
    end

    initial begin
        fail = 0;
        got = 0;
        for (i = 0; i < 4096; i = i + 1)
            mem[i] = 0;
        repeat (12) @(posedge clk);
        rst_n = 1;
        waitc = 0;
        while (!c0_ready && waitc < 40) begin
            @(posedge clk);
            waitc = waitc + 1;
        end
        @(negedge clk);
        c0_valid = 1;
        c0_we = 1;
        c0_addr = 16'h0040;
        c0_wdata = 32'hA5A5_3210;
        waitc = 0;
        while (!(c0_valid && c0_ready) && waitc < 400) begin
            @(posedge clk);
            waitc = waitc + 1;
        end
        @(negedge clk);
        c0_valid = 0;
        c0_we = 0;
        waitc = 0;
        while (!c0_rvalid && waitc < 800) begin
            @(posedge clk);
            waitc = waitc + 1;
        end
        if (!c0_rvalid) begin
            $display("SMOKE FAIL write rsp");
            $finish;
        end
        @(negedge clk);

        while (!c0_ready && waitc < 40) begin
            @(posedge clk);
            waitc = waitc + 1;
        end
        @(negedge clk);
        c0_valid = 1;
        c0_we = 0;
        c0_addr = 16'h0040;
        waitc = 0;
        while (!(c0_valid && c0_ready) && waitc < 400) begin
            @(posedge clk);
            waitc = waitc + 1;
        end
        @(negedge clk);
        c0_valid = 0;
        waitc = 0;
        while (!c0_rvalid && waitc < 800) begin
            @(posedge clk);
            waitc = waitc + 1;
        end
        if (c0_rvalid) begin
            if (c0_rdata !== 32'hA5A5_3210) begin
                $display("SMOKE FAIL data %h", c0_rdata);
                fail = 1;
            end else
                got = 1;
        end
        if (!fail && got)
            $display("SMOKE PASS");
        else
            $display("SMOKE FAIL");
        $finish;
    end
endmodule
