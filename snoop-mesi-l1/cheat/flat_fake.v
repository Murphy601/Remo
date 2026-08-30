`timescale 1ns/1ps
// Adversary replica: one 16k RAM, per-core 2-way tags only to fake fill/WB.
// No MESI. CPU data always from the RAM. Refills ignore m_rdata.
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
    localparam I = 1'b0, V = 1'b1;
    localparam IDLE = 3'd0, FILL = 3'd1, FW = 3'd2, WB = 3'd3, WW = 3'd4, RSP = 3'd5;

    reg [31:0] ram [0:16383];
    reg        seen [0:16383];
    reg        val  [0:1][0:3][0:1];
    reg        drt  [0:1][0:3][0:1];
    reg [9:0]  tag  [0:1][0:3][0:1];
    reg        lru  [0:1][0:3];
    reg        busy [0:1], we [0:1], rv [0:1];
    reg [15:0] aa [0:1];
    reg [31:0] wd [0:1], rd [0:1];
    reg [2:0]  st;
    reg        us, mv, mw, mrr;
    reg [15:0] ma;
    reg [31:0] mwd;
    reg [1:0]  beat, ix, vic;
    reg [9:0]  vtg;
    integer    i;

    assign c0_ready  = rst_n && !busy[0];
    assign c1_ready  = rst_n && !busy[1];
    assign c0_rvalid = rv[0];
    assign c1_rvalid = rv[1];
    assign c0_rdata  = rd[0];
    assign c1_rdata  = rd[1];
    assign m_valid   = mv;
    assign m_we      = mw;
    assign m_addr    = ma;
    assign m_wdata   = mwd;
    assign m_rready  = mrr;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            busy[0] <= 0; busy[1] <= 0; rv[0] <= 0; rv[1] <= 0;
            rd[0] <= 0; rd[1] <= 0; st <= IDLE; us <= 0;
            mv <= 0; mw <= 0; mrr <= 0; ma <= 0; mwd <= 0;
            beat <= 0; ix <= 0; vic <= 0; vtg <= 0;
            for (i = 0; i < 4; i = i + 1) begin
                lru[0][i] <= 0; lru[1][i] <= 0;
                val[0][i][0] <= 0; val[0][i][1] <= 0;
                val[1][i][0] <= 0; val[1][i][1] <= 0;
                drt[0][i][0] <= 0; drt[0][i][1] <= 0;
                drt[1][i][0] <= 0; drt[1][i][1] <= 0;
            end
        end else begin
            if (c0_valid && c0_ready) begin
                busy[0] <= 1; we[0] <= c0_we; aa[0] <= c0_addr; wd[0] <= c0_wdata;
            end
            if (c1_valid && c1_ready) begin
                busy[1] <= 1; we[1] <= c1_we; aa[1] <= c1_addr; wd[1] <= c1_wdata;
            end
            if (rv[0] && c0_rready) begin rv[0] <= 0; busy[0] <= 0; end
            if (rv[1] && c1_rready) begin rv[1] <= 0; busy[1] <= 0; end

            case (st)
            IDLE: begin
                if (busy[0] && !rv[0]) begin
                    us <= 0; st <= FILL; beat <= 0; ix <= aa[0][5:4];
                end else if (busy[1] && !rv[1]) begin
                    us <= 1; st <= FILL; beat <= 0; ix <= aa[1][5:4];
                end
            end
            FILL: begin
                begin : dec
                    reg [15:0] a;
                    reg [9:0] t;
                    reg [1:0] x, wsel;
                    reg hit, hy, need_wb;
                    a = us ? aa[1] : aa[0];
                    t = a[15:6];
                    x = a[5:4];
                    hit = (val[us][x][0] && tag[us][x][0] == t) ||
                          (val[us][x][1] && tag[us][x][1] == t);
                    hy  = (val[us][x][1] && tag[us][x][1] == t);
                    if (hit) begin
                        wsel = hy;
                        if (us ? we[1] : we[0]) begin
                            ram[a[15:2]] <= us ? wd[1] : wd[0];
                            drt[us][x][wsel] <= 1;
                            if (us) rd[1] <= wd[1]; else rd[0] <= wd[0];
                        end else begin
                            if (us) rd[1] <= ram[a[15:2]]; else rd[0] <= ram[a[15:2]];
                        end
                        lru[us][x] <= ~wsel[0];
                        if (us) rv[1] <= 1; else rv[0] <= 1;
                        st <= IDLE;
                    end else begin
                        if (!val[us][x][0]) wsel = 0;
                        else if (!val[us][x][1]) wsel = 1;
                        else wsel = {1'b0, lru[us][x]};
                        vic <= wsel;
                        vtg <= tag[us][x][wsel];
                        need_wb = val[us][x][wsel] && drt[us][x][wsel];
                        if (need_wb) begin
                            mv <= 1; mw <= 1; mrr <= 0;
                            ma <= {tag[us][x][wsel], x, 2'b00, 2'b00};
                            mwd <= ram[{tag[us][x][wsel], x, 2'b00, 2'b00} >> 2];
                            beat <= 0;
                            st <= WW;
                        end else begin
                            mv <= 1; mw <= 0; mrr <= 0;
                            ma <= {t, x, 2'b00, 2'b00};
                            beat <= 0;
                            st <= FW;
                        end
                    end
                end
            end
            WW: begin
                if (mv && m_ready) begin mv <= 0; mrr <= 1; st <= WB; end
            end
            WB: begin
                if (m_rvalid && mrr) begin
                    mrr <= 0;
                    if (beat != 2'd3) begin
                        beat <= beat + 1;
                        mv <= 1; mw <= 1;
                        ma <= {vtg, ix, beat + 2'd1, 2'b00};
                        mwd <= ram[{vtg, ix, beat + 2'd1, 2'b00} >> 2];
                        st <= WW;
                    end else begin
                        val[us][ix][vic] <= 0;
                        drt[us][ix][vic] <= 0;
                        mv <= 1; mw <= 0; mrr <= 0;
                        ma <= {us ? aa[1][15:6] : aa[0][15:6], ix, 2'b00, 2'b00};
                        beat <= 0;
                        st <= FW;
                    end
                end
            end
            FW: begin
                if (mv && m_ready) begin mv <= 0; mrr <= 1; st <= FILL; end
            end
            default: begin
                if (m_rvalid && mrr) begin
                    // First touch of this word: keep m_rdata. Later dummy
                    // fills leave the 16k copy (the exploit).
                    if (!seen[{ma} >> 2]) begin
                        ram[{ma} >> 2] <= m_rdata;
                        seen[{ma} >> 2] <= 1;
                    end
                    mrr <= 0;
                    if (beat != 2'd3) begin
                        beat <= beat + 1;
                        mv <= 1; mw <= 0;
                        ma <= {us ? aa[1][15:6] : aa[0][15:6], ix, beat + 2'd1, 2'b00};
                        st <= FW;
                    end else begin
                        val[us][ix][vic] <= 1;
                        tag[us][ix][vic] <= us ? aa[1][15:6] : aa[0][15:6];
                        drt[us][ix][vic] <= us ? we[1] : we[0];
                        lru[us][ix] <= ~vic[0];
                        if (us ? we[1] : we[0]) begin
                            ram[(us ? aa[1] : aa[0]) >> 2] <= us ? wd[1] : wd[0];
                            if (us) rd[1] <= wd[1]; else rd[0] <= wd[0];
                        end else begin
                            if (us) rd[1] <= ram[aa[1] >> 2];
                            else    rd[0] <= ram[aa[0] >> 2];
                        end
                        if (us) rv[1] <= 1; else rv[0] <= 1;
                        st <= IDLE;
                    end
                end
            end
            endcase
        end
    end
endmodule
