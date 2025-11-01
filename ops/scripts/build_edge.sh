#!/bin/bash
set -euo pipefail

echo "Building edge worker components for Inscenium..."

# Parse command line arguments
RELEASE_MODE=false
if [ "${1:-}" = "--release" ]; then
    RELEASE_MODE=true
fi

# Check Rust installation
if ! command -v rustc &> /dev/null; then
    echo "Rust not found. Please install Rust:"
    echo "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
    exit 1
fi

# Check WASM target
if ! rustup target list --installed | grep -q "wasm32-unknown-unknown"; then
    echo "Adding WASM target..."
    rustup target add wasm32-unknown-unknown
fi

# Check Go installation  
if ! command -v go &> /dev/null; then
    echo "Go not found. Please install Go 1.22+"
    exit 1
fi

GO_VERSION=$(go version | grep -o 'go[0-9]\+\.[0-9]\+' | sed 's/go//')
if [ "$(echo "$GO_VERSION < 1.22" | bc -l)" = "1" ] 2>/dev/null; then
    echo "⚠️  Go version $GO_VERSION may be too old. Recommended: Go 1.22+"
fi

# Build Rust/WASM worker
echo "Building Rust WASM worker..."
cd edge/edge_worker_wasm

if [ "$RELEASE_MODE" = true ]; then
    echo "Building in release mode..."
    cargo build --target wasm32-unknown-unknown --release
    WASM_FILE="target/wasm32-unknown-unknown/release/edge_worker_wasm.wasm"
else
    echo "Building in debug mode..."
    cargo build --target wasm32-unknown-unknown
    WASM_FILE="target/wasm32-unknown-unknown/debug/edge_worker_wasm.wasm"
fi

# Check if wasm-pack is available for optimized builds
if command -v wasm-pack &> /dev/null; then
    echo "Using wasm-pack for optimized build..."
    if [ "$RELEASE_MODE" = true ]; then
        wasm-pack build --target web --release
    else
        wasm-pack build --target web --dev
    fi
    echo "✓ WASM package generated in pkg/"
else
    echo "⚠️  wasm-pack not found. Using basic cargo build."
    echo "Install wasm-pack for optimized builds: cargo install wasm-pack"
fi

cd ../../

if [ -f "edge/edge_worker_wasm/$WASM_FILE" ]; then
    echo "✓ WASM worker built: $WASM_FILE"
    
    # Show WASM file size
    WASM_SIZE=$(wc -c < "edge/edge_worker_wasm/$WASM_FILE")
    echo "WASM file size: $((WASM_SIZE / 1024))KB"
else
    echo "✗ WASM build failed"
    exit 1
fi

# Build native Rust components
echo "Building native Rust edge components..."
cd edge

if [ "$RELEASE_MODE" = true ]; then
    cargo build --release --bin edge_worker_wgpu --bin decision_engine
    RUST_BIN_DIR="target/release"
else
    cargo build --bin edge_worker_wgpu --bin decision_engine  
    RUST_BIN_DIR="target/debug"
fi

cd ..

if [ -f "edge/$RUST_BIN_DIR/edge_worker_wgpu" ]; then
    echo "✓ Native edge worker built: edge/$RUST_BIN_DIR/edge_worker_wgpu"
fi

if [ -f "edge/$RUST_BIN_DIR/decision_engine" ]; then
    echo "✓ Decision engine built: edge/$RUST_BIN_DIR/decision_engine"
fi

# Build Go components
echo "Building Go HLS manifest patcher..."
cd edge

if [ "$RELEASE_MODE" = true ]; then
    go build -ldflags "-s -w" -o hls_manifest_patcher hls_manifest_patcher.go
else
    go build -o hls_manifest_patcher hls_manifest_patcher.go
fi

cd ..

if [ -f "edge/hls_manifest_patcher" ]; then
    echo "✓ HLS manifest patcher built: edge/hls_manifest_patcher"
    
    # Show binary size
    PATCHER_SIZE=$(wc -c < "edge/hls_manifest_patcher")
    echo "Binary size: $((PATCHER_SIZE / 1024))KB"
else
    echo "✗ Go build failed"
    exit 1
fi

# Build API gateway
echo "Building Go API gateway..."
cd control/api

if [ "$RELEASE_MODE" = true ]; then
    go build -ldflags "-s -w" -o http_gateway *.go
else
    go build -o http_gateway *.go  
fi

cd ../../

if [ -f "control/api/http_gateway" ]; then
    echo "✓ API gateway built: control/api/http_gateway"
else
    echo "✗ API gateway build failed"
    exit 1
fi

echo ""
echo "✓ Edge worker build complete!"
echo "Components built:"
echo "  - WASM worker: edge/edge_worker_wasm/$WASM_FILE"
echo "  - Native worker: edge/$RUST_BIN_DIR/edge_worker_wgpu"  
echo "  - Decision engine: edge/$RUST_BIN_DIR/decision_engine"
echo "  - HLS patcher: edge/hls_manifest_patcher"
echo "  - API gateway: control/api/http_gateway"