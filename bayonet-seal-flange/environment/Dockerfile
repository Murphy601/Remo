FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 \
        python3-numpy \
        openscad \
        xvfb \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# CLI export needs a display on the distro build. Call the real binary
# so a wrapper on PATH cannot recurse.
RUN printf '%s\n' \
        '#!/bin/sh' \
        'exec xvfb-run -a /usr/bin/openscad "$@"' \
        > /usr/local/bin/openscad \
    && chmod +x /usr/local/bin/openscad

WORKDIR /app
