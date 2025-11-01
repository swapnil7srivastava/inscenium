# Inscenium Edge Worker Dockerfile
# ================================

# Multi-stage build for Rust components
FROM rust:1.75-slim AS rust-builder

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Add WASM target
RUN rustup target add wasm32-unknown-unknown

# Install wasm-pack
RUN curl https://rustwasm.github.io/wasm-pack/installer/init.sh -sSf | sh

WORKDIR /app

# Copy Rust source
COPY edge/ ./edge/

# Build native Rust binaries
RUN cd edge && cargo build --release --bin edge_worker_wgpu --bin decision_engine

# Build WASM module
RUN cd edge/edge_worker_wasm && \
    if command -v wasm-pack; then \
        wasm-pack build --target web --release; \
    else \
        cargo build --target wasm32-unknown-unknown --release; \
    fi

# Go builder stage
FROM golang:1.22-alpine AS go-builder

RUN apk add --no-cache git ca-certificates

WORKDIR /app

# Copy Go modules
COPY edge/go.mod edge/go.sum ./edge/
RUN cd edge && go mod download

# Copy Go source
COPY edge/ ./edge/

# Build Go binaries
RUN cd edge && go build -ldflags="-w -s" -o hls_manifest_patcher hls_manifest_patcher.go

# Final runtime image
FROM debian:bookworm-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash --uid 1000 inscenium

WORKDIR /app

# Copy built binaries
COPY --from=rust-builder /app/edge/target/release/edge_worker_wgpu ./bin/
COPY --from=rust-builder /app/edge/target/release/decision_engine ./bin/
COPY --from=go-builder /app/edge/hls_manifest_patcher ./bin/

# Copy WASM artifacts
COPY --from=rust-builder /app/edge/edge_worker_wasm/pkg/ ./wasm/
COPY --from=rust-builder /app/edge/edge_worker_wasm/target/wasm32-unknown-unknown/release/*.wasm ./wasm/ 2>/dev/null || true

# Copy edge worker source for runtime reference
COPY edge/ ./edge/

# Create directories
RUN mkdir -p /app/data /app/sidecar_assets /app/logs

# Set permissions
RUN chown -R inscenium:inscenium /app
RUN chmod +x /app/bin/*

USER inscenium

# Environment variables
ENV RUST_LOG=info
ENV EDGE_WORKER_PORT=8083

# Create health check script
RUN echo '#!/bin/bash\nwget --no-verbose --tries=1 --spider http://localhost:8083/health 2>/dev/null || curl -f http://localhost:8083/health || exit 1' > /app/health-check.sh
RUN chmod +x /app/health-check.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD ["/app/health-check.sh"]

EXPOSE 8083

# Simple HTTP server for edge requests (placeholder)
CMD ["sh", "-c", "echo 'Edge Worker starting on port 8083...'; while true; do echo -e 'HTTP/1.1 200 OK\\r\\n\\r\\n{\"status\":\"healthy\",\"service\":\"edge-worker\"}' | nc -l -p 8083; done"]