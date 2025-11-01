#!/bin/bash
# Generate Go code from Protocol Buffers
# =====================================

set -euo pipefail

echo "Generating Go code from Protocol Buffers..."

# Check if protoc is available
if ! command -v protoc &> /dev/null; then
    echo "protoc could not be found. Please install Protocol Buffer compiler."
    echo "On macOS: brew install protobuf"
    echo "On Ubuntu: apt-get install protobuf-compiler"
    exit 1
fi

# Check if protoc-gen-go is available
if ! command -v protoc-gen-go &> /dev/null; then
    echo "protoc-gen-go not found. Installing..."
    go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
fi

# Check if protoc-gen-go-grpc is available
if ! command -v protoc-gen-go-grpc &> /dev/null; then
    echo "protoc-gen-go-grpc not found. Installing..."
    go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
fi

# Create output directory
mkdir -p pb

# Generate Go code
echo "Generating Go code from graph.proto..."
protoc \
    --go_out=pb \
    --go_opt=paths=source_relative \
    --go-grpc_out=pb \
    --go-grpc_opt=paths=source_relative \
    graph.proto

echo "✓ Protocol Buffer generation complete!"
echo "Generated files:"
ls -la pb/

# Verify generated files exist
if [ -f "pb/graph.pb.go" ]; then
    echo "✓ graph.pb.go generated successfully"
else
    echo "⚠️  graph.pb.go not found"
fi

if [ -f "pb/graph_grpc.pb.go" ]; then
    echo "✓ graph_grpc.pb.go generated successfully"
else
    echo "⚠️  graph_grpc.pb.go not found"
fi