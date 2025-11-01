# Inscenium API Gateway Dockerfile
# ================================

FROM golang:1.22-alpine AS builder

# Install dependencies
RUN apk add --no-cache git ca-certificates tzdata protobuf protobuf-dev

WORKDIR /app

# Copy Go modules first for better caching
COPY control/api/go.mod control/api/go.sum ./control/api/
RUN cd control/api && go mod download

# Copy source code
COPY control/api ./control/api
COPY sgi/sgi_schema.sql ./sgi/

# Generate protobuf code if needed
RUN cd control/api && \
    if [ -f "scripts/gen_proto.sh" ]; then \
        chmod +x scripts/gen_proto.sh && \
        ./scripts/gen_proto.sh; \
    fi

# Build the application
RUN cd control/api && \
    CGO_ENABLED=0 GOOS=linux go build \
    -ldflags="-w -s -X main.Version=$(git describe --tags --always --dirty) -X main.BuildTime=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    -o inscenium-api .

# Final stage
FROM alpine:3.18

# Install runtime dependencies
RUN apk add --no-cache ca-certificates tzdata wget curl

# Create non-root user
RUN adduser -D -s /bin/sh -u 1000 inscenium

# Copy binary and migrations
COPY --from=builder /app/control/api/inscenium-api /usr/local/bin/
COPY --from=builder /app/sgi/sgi_schema.sql /app/

# Set ownership
RUN chown -R inscenium:inscenium /app

USER inscenium

WORKDIR /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

EXPOSE 8080

CMD ["inscenium-api"]