FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        iverilog \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY data/sdr4_mc.v /app/sdr4_mc.v
COPY data/tb_sdr.v /app/tb_sdr.v
