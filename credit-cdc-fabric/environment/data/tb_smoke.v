`timescale 1ns/1ps

// 1:1, 40 packets. Not the grader.
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

    reg        p_valid = 1'b0;
    reg        p_sop   = 1'b0;
    reg        p_eop   = 1'b0;
    reg [31:0] p_data  = 32'b0;
    wire       p_credit;

    wire        c_valid;
    wire        c_sop;
    wire        c_eop;
    wire [31:0] c_data;
    reg         c_ready = 1'b1;
    reg         cr_ret  = 1'b0;

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
        .p_valid(p_valid), .p_sop(p_sop), .p_eop(p_eop), .p_data(p_data),
        .p_credit(p_credit),
        .c_valid(c_valid), .c_sop(c_sop), .c_eop(c_eop), .c_data(c_data),
        .c_ready(c_ready), .cr_ret(cr_ret)
    );

    initial begin
        fail = 0;
        credits = 0;
        beat_id = 0;
        pkt_left = 40;
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
        credits = 8;
        started = 1;
    end

    always @(posedge clk_a) begin
        if (started && rst_a_n) begin
            if (p_credit)
                credits = credits + 1;
            if (!done_send && (pkt_left > 0 || beat_ix != 0) && credits > 0) begin
                if (beat_ix == 0)
                    pkt_len = (beat_id % 7) + 1;
                p_valid <= 1'b1;
                p_sop   <= (beat_ix == 0);
                p_eop   <= (beat_ix == pkt_len - 1);
                p_data  <= {beat_id[15:0], beat_ix[7:0], pkt_len[7:0]};
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
                p_valid <= 1'b0;
                p_sop   <= 1'b0;
                p_eop   <= 1'b0;
            end
        end
    end

    always @(posedge clk_b) begin
        cr_ret <= 1'b0;
        c_ready <= 1'b1;
        if (started && rst_b_n && c_valid && c_ready) begin
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
            cr_ret     <= 1'b1;
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
