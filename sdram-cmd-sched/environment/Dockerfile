FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        iverilog \
        make \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY data/sdram_sched.v /app/sdram_sched.v
COPY data/tb_smoke.v /app/tb_smoke.v
