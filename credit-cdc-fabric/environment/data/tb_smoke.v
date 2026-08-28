`timescale 1ns/1ps

// 1:1, VC0 only, 24 packets. Not the grader.
module tb_smoke;
    reg clk_a = 1'b0;
    reg clk_b = 1'b0;
    always #5 clk_a = ~clk_a;
    initial begin
        #1;
        forever #5 clk_b = ~clk_b;
    end

    reg rst_a_n = 1'b0;
    reg rst_b_n = 1'b0;

    reg        p0_valid = 1'b0;
    reg        p0_sop   = 1'b0;
    reg        p0_eop   = 1'b0;
    reg [31:0] p0_data  = 32'b0;
    wire       p0_credit;
    wire       p1_credit;

    wire        c_valid;
    wire        c_sop;
    wire        c_eop;
    wire        c_vc;
    wire [31:0] c_data;
    reg         c_ready = 1'b1;
    reg [1:0]   c_allow = 2'b11;
    reg [1:0]   cr0_n   = 2'b00;
    reg [1:0]   cr1_n   = 2'b00;

    integer credits;
    integer beat_id;
    integer pkt_left;
    integer beat_ix;
    integer pkt_len;
    integer sent_beats;
    integer recv_beats;
    integer next_id;
    integer pk_state;
    integer exp_len;
    integer exp_ix;
    integer started;
    integer done_send;
    integer fail;

    cdc_fabric dut (
        .clk_a(clk_a), .rst_a_n(rst_a_n),
        .clk_b(clk_b), .rst_b_n(rst_b_n),
        .p0_valid(p0_valid), .p0_sop(p0_sop), .p0_eop(p0_eop), .p0_data(p0_data),
        .p0_credit(p0_credit),
        .p1_valid(1'b0), .p1_sop(1'b0), .p1_eop(1'b0), .p1_data(32'b0),
        .p1_credit(p1_credit),
        .c_valid(c_valid), .c_sop(c_sop), .c_eop(c_eop), .c_vc(c_vc), .c_data(c_data),
        .c_ready(c_ready), .c_allow(c_allow), .cr0_n(cr0_n), .cr1_n(cr1_n)
    );

    initial begin
        fail = 0;
        credits = 0;
        beat_id = 0;
        pkt_left = 24;
        beat_ix = 0;
        pkt_len = 1;
        sent_beats = 0;
        recv_beats = 0;
        next_id = 0;
        pk_state = 0;
        exp_len = 0;
        exp_ix = 0;
        started = 0;
        done_send = 0;
        repeat (12) @(posedge clk_a);
        rst_a_n = 1'b1;
        rst_b_n = 1'b1;
        repeat (16) @(posedge clk_a);
        credits = 4;
        started = 1;
    end

    always @(posedge clk_a) begin
        if (started && rst_a_n) begin
            if (p0_credit)
                credits = credits + 1;
            if (!done_send && (pkt_left > 0 || beat_ix != 0) && credits > 0) begin
                if (beat_ix == 0)
                    pkt_len = (beat_id % 7) + 1;
                p0_valid <= 1'b1;
                p0_sop   <= (beat_ix == 0);
                p0_eop   <= (beat_ix == pkt_len - 1);
                p0_data  <= {beat_id[15:0], beat_ix[7:0], pkt_len[7:0]};
                credits    = credits - 1;
                sent_beats = sent_beats + 1;
                beat_id    = beat_id + 1;
                beat_ix    = beat_ix + 1;
                if (beat_ix == pkt_len) begin
                    beat_ix = 0;
                    pkt_left = pkt_left - 1;
                    if (pkt_left == 0)
                        done_send = 1;
                end
            end else begin
                p0_valid <= 1'b0;
                p0_sop   <= 1'b0;
                p0_eop   <= 1'b0;
            end
        end
    end

    always @(posedge clk_b) begin
        cr0_n <= 2'b00;
        cr1_n <= 2'b00;
        c_ready <= 1'b1;
        c_allow <= 2'b11;
        if (started && rst_b_n && c_valid && c_ready && c_allow[c_vc]) begin
            if (c_vc !== 1'b0)
                fail = 1;
            if (c_data[31:16] !== next_id[15:0])
                fail = 1;
            if (pk_state == 0) begin
                if (!c_sop) fail = 1;
                exp_len = c_data[7:0];
                exp_ix = 0;
            end else if (c_sop) begin
                fail = 1;
            end
            if (exp_ix == exp_len - 1) begin
                if (!c_eop) fail = 1;
                pk_state = 0;
            end else begin
                if (c_eop) fail = 1;
                pk_state = 1;
            end
            next_id    = next_id + 1;
            recv_beats = recv_beats + 1;
            exp_ix     = exp_ix + 1;
            cr0_n      <= 2'b01;
        end
    end

    initial begin
        wait (started);
        wait (done_send);
        begin : drain
            integer n;
            n = 0;
            while (recv_beats != sent_beats) begin
                @(posedge clk_a);
                n = n + 1;
                if (n > 20000) fail = 1;
                if (fail) disable drain;
            end
        end
        repeat (20) @(posedge clk_a);
        if (fail || sent_beats != recv_beats || sent_beats == 0) begin
            $display("SMOKE FAIL sent=%0d recv=%0d", sent_beats, recv_beats);
            $fatal;
        end
        $display("SMOKE PASS sent=%0d", sent_beats);
        $finish;
    end

    initial begin
        #2000000;
        $display("SMOKE FAIL timeout");
        $fatal;
    end
endmodule
