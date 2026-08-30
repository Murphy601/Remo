FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        openscad \
        xvfb \
        python3 \
        python3-numpy \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
