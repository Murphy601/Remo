// Closed-page SDRAM scheduler, 2 ports, 4 banks, BL=4, CL=3.
module sdram_sched (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        p0_valid,
    output wire        p0_ready,
    input  wire        p0_we,
    input  wire [1:0]  p0_ba,
    input  wire [12:0] p0_row,
    input  wire [7:0]  p0_col,
    input  wire [63:0] p0_wdata,
    output wire        p0_rvalid,
    input  wire        p0_rready,
    output wire [63:0] p0_rdata,
    input  wire        p1_valid,
    output wire        p1_ready,
    input  wire        p1_we,
    input  wire [1:0]  p1_ba,
    input  wire [12:0] p1_row,
    input  wire [7:0]  p1_col,
    input  wire [63:0] p1_wdata,
    output wire        p1_rvalid,
    input  wire        p1_rready,
    output wire [63:0] p1_rdata,
    output reg         cke,
    output reg         cs_n,
    output reg         ras_n,
    output reg         cas_n,
    output reg         we_n,
    output reg  [1:0]  ba,
    output reg  [12:0] a,
    output reg  [15:0] dq_o,
    output reg         dq_oe,
    input  wire [15:0] dq_i
);
    localparam CL      = 3;
    localparam T_RCD   = 3;
    localparam T_RP    = 3;
    localparam T_RAS   = 7;
    localparam T_RC    = 10;
    localparam T_RRD   = 2;
    localparam T_FAW   = 10;
    localparam T_WTR   = 2;
    localparam T_RTP   = 2;
    localparam T_WR    = 3;
    localparam T_RFC   = 10;
    localparam T_REFI  = 96;
    localparam T_FLUSH = 36;
    localparam ST_IDLE = 2'd0;
    localparam ST_ACT  = 2'd1;
    localparam ST_PRE  = 2'd2;

    reg        init_done;
    reg  [2:0] init_st;
    reg  [4:0] init_wait;
    reg [31:0] cyc;
    reg [31:0] last_ref;
    reg [31:0] t_rrd_ok;
    reg [31:0] rd_cmd_ok;
    reg [31:0] wr_cmd_ok;
    reg [31:0] act_hist [0:3];
    reg  [2:0] n_hist;
    reg        rr;

    reg  [1:0] st       [0:3];
    reg [31:0] t_act_ok [0:3];
    reg [31:0] t_cas_ok [0:3];
    reg [31:0] t_pre_ok [0:3];
    reg [31:0] last_act [0:3];
    reg [31:0] last_pre [0:3];
    reg        b_we     [0:3];
    reg  [1:0] b_port   [0:3];
    reg  [7:0] b_col    [0:3];
    reg [63:0] b_wdata  [0:3];

    reg  [2:0] qn  [0:1];
    reg  [1:0] qwp [0:1];
    reg  [1:0] qrp [0:1];
    reg        q_we   [0:1][0:3];
    reg  [1:0] q_ba   [0:1][0:3];
    reg [12:0] q_row  [0:1][0:3];
    reg  [7:0] q_col  [0:1][0:3];
    reg [63:0] q_wd   [0:1][0:3];
    reg  [2:0] outst  [0:1];

    reg [63:0] rfifo [0:1][0:3];
    reg  [1:0] rwp   [0:1];
    reg  [1:0] rrp   [0:1];
    reg  [2:0] rfn   [0:1];
    reg [63:0] racc  [0:1];
    reg [11:0] rp_v;
    reg  [1:0] rp_port [0:11];
    reg  [1:0] rp_beat [0:11];

    reg  [1:0] wr_left;
    reg [47:0] wr_rest;

    integer i, b, p, k;
    integer cas_b, pre_b, act_p, act_b;
    integer acc0, acc1, pop0, pop1;
    integer popr0, popr1, push0, push1, decw0, decw1;
    integer nwin, all_idle, rp_met, any_acted, all_needpre_ok;
    integer faw_ok, rfc_busy, need_flush;
    integer do_ref, do_prea, do_pre, do_cas, do_act;
    integer cap_p, cap_bt;
    integer npre_ok;

    assign p0_ready  = rst_n && init_done && (outst[0] < 3'd4);
    assign p1_ready  = rst_n && init_done && (outst[1] < 3'd4);
    assign p0_rvalid = (rfn[0] != 3'd0);
    assign p1_rvalid = (rfn[1] != 3'd0);
    assign p0_rdata  = rfifo[0][rrp[0]];
    assign p1_rdata  = rfifo[1][rrp[1]];

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cke <= 1'b1;
            cs_n <= 1'b1;
            ras_n <= 1'b1;
            cas_n <= 1'b1;
            we_n <= 1'b1;
            ba <= 2'b0;
            a <= 13'b0;
            dq_o <= 16'b0;
            dq_oe <= 1'b0;
            init_done <= 1'b0;
            init_st <= 3'd0;
            init_wait <= 5'd8;
            cyc <= 32'd0;
            last_ref <= 32'd0;
            t_rrd_ok <= 32'd0;
            rd_cmd_ok <= 32'd0;
            wr_cmd_ok <= 32'd0;
            n_hist <= 3'd0;
            rr <= 1'b0;
            wr_left <= 2'd0;
            wr_rest <= 48'd0;
            rp_v <= 12'd0;
            qn[0] <= 3'd0;
            qn[1] <= 3'd0;
            qwp[0] <= 2'd0;
            qwp[1] <= 2'd0;
            qrp[0] <= 2'd0;
            qrp[1] <= 2'd0;
            outst[0] <= 3'd0;
            outst[1] <= 3'd0;
            rwp[0] <= 2'd0;
            rwp[1] <= 2'd0;
            rrp[0] <= 2'd0;
            rrp[1] <= 2'd0;
            rfn[0] <= 3'd0;
            rfn[1] <= 3'd0;
            racc[0] <= 64'd0;
            racc[1] <= 64'd0;
            for (i = 0; i < 4; i = i + 1) begin
                st[i] <= ST_IDLE;
                t_act_ok[i] <= 32'd0;
                t_cas_ok[i] <= 32'd0;
                t_pre_ok[i] <= 32'd0;
                last_act[i] <= 32'd0;
                last_pre[i] <= 32'd0;
                b_we[i] <= 1'b0;
                b_port[i] <= 2'd0;
                b_col[i] <= 8'd0;
                b_wdata[i] <= 64'd0;
                act_hist[i] <= 32'd0;
            end
            for (i = 0; i < 12; i = i + 1) begin
                rp_port[i] <= 2'd0;
                rp_beat[i] <= 2'd0;
            end
        end else begin
            cyc <= cyc + 32'd1;
            cke <= 1'b1;
            cs_n <= 1'b1;
            ras_n <= 1'b1;
            cas_n <= 1'b1;
            we_n <= 1'b1;
            ba <= 2'b0;
            a <= 13'b0;

            if (wr_left != 2'd0) begin
                dq_oe <= 1'b1;
                dq_o <= wr_rest[15:0];
                wr_rest <= {16'h0, wr_rest[47:16]};
                wr_left <= wr_left - 2'd1;
            end else begin
                dq_oe <= 1'b0;
                dq_o <= 16'b0;
            end

            for (i = 0; i < 11; i = i + 1) begin
                rp_v[i] <= rp_v[i + 1];
                rp_port[i] <= rp_port[i + 1];
                rp_beat[i] <= rp_beat[i + 1];
            end
            rp_v[11] <= 1'b0;

            push0 = 0;
            push1 = 0;
            if (rp_v[0]) begin
                cap_p = rp_port[0];
                cap_bt = rp_beat[0];
                if (cap_bt == 0)
                    racc[cap_p][15:0] <= dq_i;
                else if (cap_bt == 1)
                    racc[cap_p][31:16] <= dq_i;
                else if (cap_bt == 2)
                    racc[cap_p][47:32] <= dq_i;
                else if (cap_p == 0) begin
                    rfifo[0][rwp[0]] <= {dq_i, racc[0][47:0]};
                    rwp[0] <= rwp[0] + 2'd1;
                    push0 = 1;
                end else begin
                    rfifo[1][rwp[1]] <= {dq_i, racc[1][47:0]};
                    rwp[1] <= rwp[1] + 2'd1;
                    push1 = 1;
                end
            end

            acc0 = (p0_valid && p0_ready) ? 1 : 0;
            acc1 = (p1_valid && p1_ready) ? 1 : 0;
            popr0 = (p0_rvalid && p0_rready) ? 1 : 0;
            popr1 = (p1_rvalid && p1_rready) ? 1 : 0;
            pop0 = 0;
            pop1 = 0;
            decw0 = 0;
            decw1 = 0;

            if (acc0) begin
                q_we[0][qwp[0]] <= p0_we;
                q_ba[0][qwp[0]] <= p0_ba;
                q_row[0][qwp[0]] <= p0_row;
                q_col[0][qwp[0]] <= p0_col;
                q_wd[0][qwp[0]] <= p0_wdata;
                qwp[0] <= qwp[0] + 2'd1;
            end
            if (acc1) begin
                q_we[1][qwp[1]] <= p1_we;
                q_ba[1][qwp[1]] <= p1_ba;
                q_row[1][qwp[1]] <= p1_row;
                q_col[1][qwp[1]] <= p1_col;
                q_wd[1][qwp[1]] <= p1_wdata;
                qwp[1] <= qwp[1] + 2'd1;
            end
            if (popr0)
                rrp[0] <= rrp[0] + 2'd1;
            if (popr1)
                rrp[1] <= rrp[1] + 2'd1;

            do_ref = 0;
            do_prea = 0;
            do_pre = 0;
            do_cas = 0;
            do_act = 0;
            cas_b = 4;
            pre_b = 4;
            act_p = 2;
            act_b = 0;

            if (!init_done) begin
                if (init_wait != 5'd0)
                    init_wait <= init_wait - 5'd1;
                else begin
                    case (init_st)
                    3'd0: begin
                        cs_n <= 1'b0; ras_n <= 1'b0; cas_n <= 1'b1; we_n <= 1'b0;
                        a <= 13'h400;
                        for (i = 0; i < 4; i = i + 1) begin
                            st[i] <= ST_IDLE;
                            last_pre[i] <= cyc;
                            t_act_ok[i] <= cyc + T_RP;
                        end
                        init_st <= 3'd1;
                        init_wait <= T_RP - 1;
                    end
                    3'd1: begin
                        cs_n <= 1'b0; ras_n <= 1'b0; cas_n <= 1'b0; we_n <= 1'b1;
                        last_ref <= cyc;
                        init_st <= 3'd2;
                        init_wait <= T_RFC - 1;
                    end
                    3'd2: begin
                        cs_n <= 1'b0; ras_n <= 1'b0; cas_n <= 1'b0; we_n <= 1'b1;
                        last_ref <= cyc;
                        init_st <= 3'd3;
                        init_wait <= T_RFC - 1;
                    end
                    3'd3: begin
                        cs_n <= 1'b0; ras_n <= 1'b0; cas_n <= 1'b0; we_n <= 1'b0;
                        a <= 13'h032;
                        init_st <= 3'd4;
                        init_wait <= 5'd1;
                    end
                    default: init_done <= 1'b1;
                    endcase
                end
            end else begin
                nwin = 0;
                for (i = 0; i < 4; i = i + 1)
                    if (i < n_hist && (cyc - act_hist[i]) < T_FAW)
                        nwin = nwin + 1;
                faw_ok = (nwin < 4);
                rfc_busy = (cyc < (last_ref + T_RFC));
                need_flush = ((cyc - last_ref) >= (T_REFI - T_FLUSH));

                all_idle = 1;
                rp_met = 1;
                any_acted = 0;
                all_needpre_ok = 1;
                npre_ok = 0;
                for (b = 0; b < 4; b = b + 1) begin
                    if (st[b] != ST_IDLE)
                        all_idle = 0;
                    if (st[b] != ST_IDLE || (cyc < (last_pre[b] + T_RP)))
                        rp_met = 0;
                    if (st[b] == ST_ACT)
                        any_acted = 1;
                    if (st[b] == ST_PRE) begin
                        if (cyc >= t_pre_ok[b])
                            npre_ok = npre_ok + 1;
                        else
                            all_needpre_ok = 0;
                    end
                    if (st[b] == ST_ACT && cyc >= t_cas_ok[b]) begin
                        if ((b_we[b] && cyc >= wr_cmd_ok) ||
                            (!b_we[b] && cyc >= rd_cmd_ok)) begin
                            if (cas_b == 4 || last_act[b] < last_act[cas_b])
                                cas_b = b;
                        end
                    end
                    if (st[b] == ST_PRE && cyc >= t_pre_ok[b] && pre_b == 4)
                        pre_b = b;
                end

                if (!rfc_busy) begin
                    if (need_flush && all_idle && rp_met)
                        do_ref = 1;
                    else if (need_flush && !any_acted && npre_ok > 0 && all_needpre_ok)
                        do_prea = 1;
                    else if (need_flush && pre_b != 4)
                        do_pre = 1;
                    else if (cas_b != 4)
                        do_cas = 1;
                    else if (!need_flush) begin
                        for (k = 0; k < 2; k = k + 1) begin
                            p = rr ^ k[0];
                            if (act_p == 2 && qn[p] != 3'd0) begin
                                b = q_ba[p][qrp[p]];
                                if (st[b] == ST_IDLE && cyc >= t_act_ok[b] &&
                                    cyc >= t_rrd_ok && faw_ok &&
                                    all_idle && (rp_v == 12'd0) && (wr_left == 2'd0)) begin
                                    act_p = p;
                                    act_b = b;
                                end
                            end
                        end
                        if (act_p != 2)
                            do_act = 1;
                        else if (pre_b != 4)
                            do_pre = 1;
                    end
                end

                if (do_ref) begin
                    cs_n <= 1'b0; ras_n <= 1'b0; cas_n <= 1'b0; we_n <= 1'b1;
                    last_ref <= cyc;
                end else if (do_prea) begin
                    cs_n <= 1'b0; ras_n <= 1'b0; cas_n <= 1'b1; we_n <= 1'b0;
                    a <= 13'h400;
                    for (b = 0; b < 4; b = b + 1) begin
                        st[b] <= ST_IDLE;
                        last_pre[b] <= cyc;
                        t_act_ok[b] <= ((last_act[b] + T_RC) > (cyc + T_RP)) ?
                                       (last_act[b] + T_RC) : (cyc + T_RP);
                    end
                end else if (do_cas) begin
                    b = cas_b;
                    cs_n <= 1'b0;
                    ras_n <= 1'b1;
                    cas_n <= 1'b0;
                    we_n <= b_we[b] ? 1'b0 : 1'b1;
                    ba <= b[1:0];
                    a <= {5'b0, b_col[b]};
                    st[b] <= ST_PRE;
                    if (b_we[b]) begin
                        if ((cyc + 3 + T_WR) > (last_act[b] + T_RAS))
                            t_pre_ok[b] <= cyc + 3 + T_WR;
                        else
                            t_pre_ok[b] <= last_act[b] + T_RAS;
                        wr_cmd_ok <= cyc + 4;
                        if ((cyc + 3 + T_WTR) > rd_cmd_ok)
                            rd_cmd_ok <= cyc + 3 + T_WTR;
                        dq_oe <= 1'b1;
                        dq_o <= b_wdata[b][15:0];
                        wr_rest <= b_wdata[b][63:16];
                        wr_left <= 2'd3;
                        if (b_port[b] == 2'd0)
                            decw0 = 1;
                        else
                            decw1 = 1;
                    end else begin
                        if ((cyc + T_RTP) > (last_act[b] + T_RAS))
                            t_pre_ok[b] <= cyc + T_RTP;
                        else
                            t_pre_ok[b] <= last_act[b] + T_RAS;
                        rd_cmd_ok <= cyc + 4;
                        if ((cyc + CL + 4) > wr_cmd_ok)
                            wr_cmd_ok <= cyc + CL + 4;
                        rp_v[2] <= 1'b1;
                        rp_v[3] <= 1'b1;
                        rp_v[4] <= 1'b1;
                        rp_v[5] <= 1'b1;
                        rp_port[2] <= b_port[b];
                        rp_port[3] <= b_port[b];
                        rp_port[4] <= b_port[b];
                        rp_port[5] <= b_port[b];
                        rp_beat[2] <= 2'd0;
                        rp_beat[3] <= 2'd1;
                        rp_beat[4] <= 2'd2;
                        rp_beat[5] <= 2'd3;
                    end
                end else if (do_act) begin
                    p = act_p;
                    b = act_b;
                    cs_n <= 1'b0; ras_n <= 1'b0; cas_n <= 1'b1; we_n <= 1'b1;
                    ba <= b[1:0];
                    a <= q_row[p][qrp[p]];
                    st[b] <= ST_ACT;
                    last_act[b] <= cyc;
                    t_cas_ok[b] <= cyc + T_RCD;
                    t_rrd_ok <= cyc + T_RRD;
                    b_we[b] <= q_we[p][qrp[p]];
                    b_port[b] <= p[1:0];
                    b_col[b] <= q_col[p][qrp[p]];
                    b_wdata[b] <= q_wd[p][qrp[p]];
                    qrp[p] <= qrp[p] + 2'd1;
                    if (p == 0)
                        pop0 = 1;
                    else
                        pop1 = 1;
                    rr <= ~p[0];
                    if (n_hist < 3'd4) begin
                        act_hist[n_hist] <= cyc;
                        n_hist <= n_hist + 3'd1;
                    end else begin
                        act_hist[0] <= act_hist[1];
                        act_hist[1] <= act_hist[2];
                        act_hist[2] <= act_hist[3];
                        act_hist[3] <= cyc;
                    end
                end else if (do_pre) begin
                    b = pre_b;
                    cs_n <= 1'b0; ras_n <= 1'b0; cas_n <= 1'b1; we_n <= 1'b0;
                    ba <= b[1:0];
                    a <= 13'h000;
                    st[b] <= ST_IDLE;
                    last_pre[b] <= cyc;
                    t_act_ok[b] <= ((last_act[b] + T_RC) > (cyc + T_RP)) ?
                                   (last_act[b] + T_RC) : (cyc + T_RP);
                end
            end

            qn[0] <= qn[0] + acc0[0] - pop0[0];
            qn[1] <= qn[1] + acc1[0] - pop1[0];
            rfn[0] <= rfn[0] + push0[0] - popr0[0];
            rfn[1] <= rfn[1] + push1[0] - popr1[0];
            outst[0] <= outst[0] + acc0[0] - popr0[0] - decw0[0];
            outst[1] <= outst[1] + acc1[0] - popr1[0] - decw1[0];
        end
    end
endmodule
