`timescale 1ns/1ps

// Host m0 only: four writes, four reads. Not the hidden scoreboard.
module tb_sdr;
    reg clk = 1'b0;
    always #5 clk = ~clk;

    reg rst_n = 1'b0;

    reg         m0_valid = 1'b0;
    wire        m0_ready;
    reg         m0_wr    = 1'b0;
    reg  [1:0]  m0_ba    = 2'b0;
    reg  [12:0] m0_row   = 13'b0;
    reg  [7:0]  m0_col   = 8'b0;
    reg  [63:0] m0_wdata = 64'b0;
    wire        m0_rvalid;
    reg         m0_rready = 1'b1;
    wire [63:0] m0_rdata;

    wire        m1_ready;
    wire        m1_rvalid;
    wire [63:0] m1_rdata;

    wire        cke, cs_n, ras_n, cas_n, we_n, dq_oe;
    wire [1:0]  ba;
    wire [12:0] a;
    wire [15:0] dq_o;
    wire [15:0] dq_i;

    integer fail;
    integer sent_w, sent_r, recv_r;
    integer i;
    integer waitc;
    integer cmd_act, cmd_rd, cmd_wr, cmd_pre;

    // Tiny DRAM: 16-bit cells. Index {ba, row[2:0], col}.
    reg [15:0] ram [0:8191];
    integer ri;
    integer wr_left;
    integer wr_addr;
    integer wr_beat;
    reg [15:0] dqs [0:7];
    integer burst_col;
    integer mem_idx;
    reg [12:0] open_row [0:3];

    function [12:0] midx;
        input [1:0] b;
        input [12:0] r;
        input [7:0] c;
        begin
            midx = {b, r[2:0], c};
        end
    endfunction

    sdr4_mc dut (
        .clk(clk), .rst_n(rst_n),
        .m0_valid(m0_valid), .m0_ready(m0_ready), .m0_wr(m0_wr),
        .m0_ba(m0_ba), .m0_row(m0_row), .m0_col(m0_col), .m0_wdata(m0_wdata),
        .m0_rvalid(m0_rvalid), .m0_rready(m0_rready), .m0_rdata(m0_rdata),
        .m1_valid(1'b0), .m1_ready(m1_ready), .m1_wr(1'b0),
        .m1_ba(2'b0), .m1_row(13'b0), .m1_col(8'b0), .m1_wdata(64'b0),
        .m1_rvalid(m1_rvalid), .m1_rready(1'b1), .m1_rdata(m1_rdata),
        .cke(cke), .cs_n(cs_n), .ras_n(ras_n), .cas_n(cas_n), .we_n(we_n),
        .ba(ba), .a(a), .dq_o(dq_o), .dq_oe(dq_oe), .dq_i(dq_i)
    );

    assign dq_i = dqs[0];

    always @(*) begin
        cmd_act = (!cs_n && !ras_n &&  cas_n &&  we_n);
        cmd_rd  = (!cs_n &&  ras_n && !cas_n &&  we_n);
        cmd_wr  = (!cs_n &&  ras_n && !cas_n && !we_n);
        cmd_pre = (!cs_n && !ras_n &&  cas_n && !we_n);
    end

    always @(negedge clk) begin
        dqs[0] <= dqs[1];
        dqs[1] <= dqs[2];
        dqs[2] <= dqs[3];
        dqs[3] <= dqs[4];
        dqs[4] <= dqs[5];
        dqs[5] <= 16'h0;
        if (rst_n && cmd_rd) begin
            burst_col = {a[7:2], 2'b00};
            dqs[2] <= ram[midx(ba, open_row[ba], burst_col + 0)];
            dqs[3] <= ram[midx(ba, open_row[ba], burst_col + 1)];
            dqs[4] <= ram[midx(ba, open_row[ba], burst_col + 2)];
            dqs[5] <= ram[midx(ba, open_row[ba], burst_col + 3)];
        end
    end

    always @(posedge clk) begin
        if (!rst_n) begin
            wr_left <= 0;
            wr_beat <= 0;
        end else if (cmd_act)
            open_row[ba] <= a;
    end

    always @(negedge clk) begin
        if (rst_n && cmd_wr) begin
            wr_addr <= midx(ba, open_row[ba], {a[7:2], 2'b00});
            ram[midx(ba, open_row[ba], {a[7:2], 2'b00})] <= dq_o;
            wr_left <= 3;
            wr_beat <= 1;
        end else if (rst_n && wr_left != 0) begin
            ram[wr_addr + wr_beat] <= dq_o;
            wr_left <= wr_left - 1;
            wr_beat <= wr_beat + 1;
        end
    end

    always @(posedge clk) begin
        if (rst_n && m0_rvalid && m0_rready) begin
            if (m0_rdata !== {16'hA000 + recv_r[15:0], 16'hB000 + recv_r[15:0],
                              16'hC000 + recv_r[15:0], 16'hD000 + recv_r[15:0]}) begin
                $display("SMOKE FAIL data got=%h i=%0d", m0_rdata, recv_r);
                fail = 1;
            end
            recv_r = recv_r + 1;
        end
    end

    initial begin
        fail = 0;
        sent_w = 0;
        sent_r = 0;
        recv_r = 0;
        wr_left = 0;
        for (ri = 0; ri < 8; ri = ri + 1)
            dqs[ri] = 16'h0;
        for (ri = 0; ri < 8192; ri = ri + 1)
            ram[ri] = 16'h0;

        repeat (12) @(posedge clk);
        rst_n = 1'b1;

        waitc = 0;
        while (!m0_ready && waitc < 200) begin
            @(posedge clk);
            waitc = waitc + 1;
        end
        if (!m0_ready) begin
            $display("SMOKE FAIL ready never rose");
            $finish;
        end

        for (i = 0; i < 4; i = i + 1) begin
            m0_wr = 1'b1;
            m0_ba = i[1:0];
            m0_row = i[12:0];
            m0_col = 8'h00;
            m0_wdata = {16'hA000 + i[15:0], 16'hB000 + i[15:0],
                        16'hC000 + i[15:0], 16'hD000 + i[15:0]};
            m0_valid = 1'b1;
            waitc = 0;
            begin : wait_w
                forever begin
                    @(posedge clk);
                    waitc = waitc + 1;
                    if (m0_ready) begin
                        sent_w = sent_w + 1;
                        m0_valid = 1'b0;
                        m0_wr = 1'b0;
                        disable wait_w;
                    end
                    if (waitc > 400) begin
                        $display("SMOKE FAIL write accept");
                        $finish;
                    end
                end
            end
            repeat (24) @(posedge clk);
        end

        repeat (16) @(posedge clk);

        // 4 reads, same addresses
        for (i = 0; i < 4; i = i + 1) begin
            m0_wr = 1'b0;
            m0_ba = i[1:0];
            m0_row = i[12:0];
            m0_col = 8'h00;
            m0_wdata = 64'b0;
            m0_valid = 1'b1;
            waitc = 0;
            begin : wait_r
                forever begin
                    @(posedge clk);
                    waitc = waitc + 1;
                    if (m0_ready) begin
                        sent_r = sent_r + 1;
                        m0_valid = 1'b0;
                        disable wait_r;
                    end
                    if (waitc > 400) begin
                        $display("SMOKE FAIL read accept");
                        $finish;
                    end
                end
            end
            repeat (24) @(posedge clk);
        end

        waitc = 0;
        while (recv_r < 4 && waitc < 2000) begin
            @(posedge clk);
            waitc = waitc + 1;
        end

        if (fail || recv_r != 4 || sent_w != 4) begin
            $display("SMOKE FAIL sent_w=%0d recv=%0d", sent_w, recv_r);
        end else begin
            $display("SMOKE PASS");
        end
        $finish;
    end
endmodule
