FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        iverilog \
        make \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY data/cdc_fabric.v /app/cdc_fabric.v
COPY data/tb_smoke.v /app/tb_smoke.v
