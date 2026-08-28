`timescale 1ns/1ps

module tb_scoreboard;
    integer PA, PB, PHASE, NPKT, TRAFFIC, SEED, RST_ORD, CRDLY;
    integer CREDITS;

    reg cfg_ready;
    reg clk_a;
    reg clk_b;
    reg rst_a_n;
    reg rst_b_n;

    reg        p_valid;
    reg        p_sop;
    reg        p_eop;
    reg [31:0] p_data;
    wire       p_credit;

    wire        c_valid;
    wire        c_sop;
    wire        c_eop;
    wire [31:0] c_data;
    reg         c_ready;
    reg         cr_ret;

    integer fail;
    integer credits;
    integer beat_id;
    integer pkt_left;
    integer beat_ix;
    integer pkt_len;
    integer idle_gap;
    integer sent_beats;
    integer recv_beats;
    integer pcred_cnt;
    integer crret_cnt;
    integer done_send;
    integer pk_state;
    integer exp_len;
    integer exp_ix;
    integer next_id;
    integer owed_cr;
    integer cr_wait;
    integer pause;
    reg [31:0] rnd_a;
    reg [31:0] rnd_b;
    reg started;
    integer want;
    integer stall_a;
    integer last_recv;

    cdc_fabric dut (
        .clk_a(clk_a), .rst_a_n(rst_a_n),
        .clk_b(clk_b), .rst_b_n(rst_b_n),
        .p_valid(p_valid), .p_sop(p_sop), .p_eop(p_eop), .p_data(p_data),
        .p_credit(p_credit),
        .c_valid(c_valid), .c_sop(c_sop), .c_eop(c_eop), .c_data(c_data),
        .c_ready(c_ready), .cr_ret(cr_ret)
    );

    function [31:0] step32;
        input [31:0] s;
        begin
            step32 = {s[30:0], s[31] ^ s[21] ^ s[1] ^ s[0]};
        end
    endfunction

    initial begin
        cfg_ready = 1'b0;
        PA = 10; PB = 10; PHASE = 0; NPKT = 40; TRAFFIC = 0; SEED = 1;
        RST_ORD = 0; CRDLY = 0; CREDITS = 8;
        void'($value$plusargs("PA=%d", PA));
        void'($value$plusargs("PB=%d", PB));
        void'($value$plusargs("PHASE=%d", PHASE));
        void'($value$plusargs("NPKT=%d", NPKT));
        void'($value$plusargs("TRAFFIC=%d", TRAFFIC));
        void'($value$plusargs("SEED=%d", SEED));
        void'($value$plusargs("RST=%d", RST_ORD));
        void'($value$plusargs("CRDLY=%d", CRDLY));
        cfg_ready = 1'b1;
    end

    initial begin
        clk_a = 1'b0;
        wait (cfg_ready);
        forever begin
            #(PA / 2.0);
            clk_a = ~clk_a;
        end
    end

    initial begin
        clk_b = 1'b0;
        wait (cfg_ready);
        #(PHASE);
        forever begin
            #(PB / 2.0);
            clk_b = ~clk_b;
        end
    end

    task finish_fail;
        input [8*24-1:0] why;
        begin
            fail = 1;
            $display("RESULT FAIL %0s sent=%0d recv=%0d pcred=%0d crret=%0d",
                     why, sent_beats, recv_beats, pcred_cnt, crret_cnt);
            $fatal;
        end
    endtask

    initial begin
        fail = 0;
        p_valid = 1'b0;
        p_sop = 1'b0;
        p_eop = 1'b0;
        p_data = 32'b0;
        c_ready = 1'b0;
        cr_ret = 1'b0;
        rst_a_n = 1'b0;
        rst_b_n = 1'b0;
        credits = 0;
        beat_id = 0;
        pkt_left = 0;
        beat_ix = 0;
        pkt_len = 1;
        idle_gap = 0;
        sent_beats = 0;
        recv_beats = 0;
        pcred_cnt = 0;
        crret_cnt = 0;
        done_send = 0;
        pk_state = 0;
        exp_len = 0;
        exp_ix = 0;
        next_id = 0;
        owed_cr = 0;
        cr_wait = 0;
        pause = 0;
        started = 1'b0;
        stall_a = 0;
        last_recv = 0;
        rnd_a = 32'd1;
        rnd_b = 32'd1;

        wait (cfg_ready);
        pkt_left = NPKT;
        rnd_a = SEED ^ 32'hA5A5_1234;
        rnd_b = SEED ^ 32'h5A5A_9BDF;

        if (RST_ORD == 0) begin
            repeat (10) @(posedge clk_a);
            repeat (10) @(posedge clk_b);
            rst_a_n = 1'b1;
            rst_b_n = 1'b1;
        end else if (RST_ORD == 1) begin
            repeat (10) @(posedge clk_a);
            rst_a_n = 1'b1;
            repeat (14) @(posedge clk_b);
            rst_b_n = 1'b1;
        end else begin
            repeat (10) @(posedge clk_b);
            rst_b_n = 1'b1;
            repeat (14) @(posedge clk_a);
            rst_a_n = 1'b1;
        end

        if (PA >= PB) repeat (16) @(posedge clk_a);
        else         repeat (16) @(posedge clk_b);

        credits = CREDITS;
        stall_a = 0;
        last_recv = 0;
        started = 1'b1;
    end

    always @(posedge clk_a) begin
        if (!rst_a_n) begin
            p_valid <= 1'b0;
            p_sop   <= 1'b0;
            p_eop   <= 1'b0;
            p_data  <= 32'b0;
        end else if (started) begin
            if (p_credit === 1'bx)
                finish_fail("p_credit_x");
            if (p_credit) begin
                pcred_cnt = pcred_cnt + 1;
                credits   = credits + 1;
            end

            want = 0;
            if (!done_send && (pkt_left > 0 || beat_ix != 0)) begin
                if (idle_gap > 0)
                    idle_gap = idle_gap - 1;
                else
                    want = 1;
            end

            if (want && credits > 0) begin
                if (beat_ix == 0) begin
                    rnd_a   = step32(rnd_a);
                    pkt_len = (rnd_a[3:0]) + 1;
                end
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
                if (TRAFFIC != 0) begin
                    rnd_a    = step32(rnd_a);
                    idle_gap = rnd_a[4:0] % 21;
                end
            end else begin
                p_valid <= 1'b0;
                p_sop   <= 1'b0;
                p_eop   <= 1'b0;
            end

            if (credits > 8 || credits < 0)
                finish_fail("credit_range");

            if (done_send && recv_beats == sent_beats) begin
                stall_a = 0;
            end else if (recv_beats != last_recv) begin
                last_recv = recv_beats;
                stall_a = 0;
            end else begin
                stall_a = stall_a + 1;
                if (stall_a > 250000)
                    finish_fail("stall");
            end
        end
    end

    always @(posedge clk_b) begin
        if (!rst_b_n) begin
            c_ready <= 1'b0;
            cr_ret  <= 1'b0;
            owed_cr = 0;
            cr_wait = 0;
            pause   = 0;
        end else if (started) begin
            if (c_valid === 1'bx)
                finish_fail("c_valid_x");
            if (c_valid) begin
                if (c_sop === 1'bx || c_eop === 1'bx)
                    finish_fail("flag_x");
                if (^c_data === 1'bx)
                    finish_fail("data_x");
            end

            rnd_b = step32(rnd_b);
            if (pause > 0) begin
                pause = pause - 1;
                c_ready <= 1'b0;
            end else if (rnd_b[9:0] == 10'd0) begin
                pause = 96;
                c_ready <= 1'b0;
            end else if (TRAFFIC == 0) begin
                c_ready <= 1'b1;
            end else begin
                c_ready <= (rnd_b[2:0] != 3'd0);
            end

            cr_ret <= 1'b0;

            if (c_valid && c_ready) begin
                if (c_data[31:16] !== next_id[15:0])
                    finish_fail("id_mismatch");
                if (pk_state == 0) begin
                    if (c_sop !== 1'b1)
                        finish_fail("missing_sop");
                    exp_len = c_data[7:0];
                    exp_ix  = 0;
                    if (exp_len < 1 || exp_len > 16)
                        finish_fail("bad_len");
                end else begin
                    if (c_sop !== 1'b0)
                        finish_fail("mid_sop");
                end
                if (c_data[15:8] !== exp_ix[7:0])
                    finish_fail("idx_mismatch");
                if (c_data[7:0] !== exp_len[7:0])
                    finish_fail("len_mismatch");
                if (exp_ix == exp_len - 1) begin
                    if (c_eop !== 1'b1)
                        finish_fail("missing_eop");
                    pk_state = 0;
                end else begin
                    if (c_eop !== 1'b0)
                        finish_fail("early_eop");
                    pk_state = 1;
                end
                next_id    = next_id + 1;
                recv_beats = recv_beats + 1;
                exp_ix     = exp_ix + 1;

                if (CRDLY == 0) begin
                    cr_ret    <= 1'b1;
                    crret_cnt = crret_cnt + 1;
                end else begin
                    owed_cr = owed_cr + 1;
                    if (cr_wait == 0) begin
                        rnd_b   = step32(rnd_b);
                        cr_wait = (rnd_b[3:0] % 12) + 1;
                    end
                end
            end

            if (CRDLY != 0) begin
                if (cr_wait > 0)
                    cr_wait = cr_wait - 1;
                if (cr_wait == 0 && owed_cr > 0 && !(c_valid && c_ready)) begin
                    cr_ret    <= 1'b1;
                    crret_cnt = crret_cnt + 1;
                    owed_cr   = owed_cr - 1;
                    if (owed_cr > 0) begin
                        rnd_b   = step32(rnd_b);
                        cr_wait = (rnd_b[3:0] % 12) + 1;
                    end
                end
            end
        end
    end

    initial begin
        wait (started);
        wait (done_send == 1);
        begin : drain
            integer spins;
            spins = 0;
            while (!(recv_beats == sent_beats && owed_cr == 0 && pk_state == 0)) begin
                @(posedge clk_a);
                spins = spins + 1;
                if (spins > 2000000)
                    finish_fail("drain_timeout");
            end
        end
        repeat (80) @(posedge clk_a);
        repeat (80) @(posedge clk_b);
        if (recv_beats !== sent_beats)
            finish_fail("count");
        if (pcred_cnt !== crret_cnt)
            finish_fail("credit_count");
        if (sent_beats == 0)
            finish_fail("nothing_sent");
        if (pk_state != 0)
            finish_fail("truncated");
        $display("RESULT PASS sent=%0d recv=%0d pcred=%0d crret=%0d",
                 sent_beats, recv_beats, pcred_cnt, crret_cnt);
        $finish;
    end

    initial begin
        wait (cfg_ready);
        #(2000000000);
        finish_fail("wall_timeout");
    end
endmodule
