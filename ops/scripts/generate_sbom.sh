#!/bin/bash
# CycloneDX SBOM Generation for Inscenium
# Generates Software Bill of Materials for Python/Node/Go/Rust components

set -euo pipefail

SBOM_DIR="./sbom"
mkdir -p "$SBOM_DIR"

echo "🔍 Generating SBOM artifacts..."

# Python dependencies (Poetry)
if command -v poetry &> /dev/null && [ -f "pyproject.toml" ]; then
    echo "📦 Python dependencies..."
    poetry export --format requirements.txt --output "$SBOM_DIR/requirements.txt"
    if command -v cyclonedx-py &> /dev/null; then
        cyclonedx-py --format json --output "$SBOM_DIR/python-bom.json" .
    else
        echo "  Warning: cyclonedx-py not installed, skipping Python BOM"
    fi
fi

# Node.js dependencies (pnpm)
if command -v pnpm &> /dev/null && [ -f "control/cms/webapp/package.json" ]; then
    echo "📦 Node.js dependencies..."
    cd control/cms/webapp
    if command -v cyclonedx-npm &> /dev/null; then
        cyclonedx-npm --output-file "../../../$SBOM_DIR/nodejs-bom.json"
    else
        echo "  Warning: cyclonedx-npm not installed, skipping Node.js BOM"
    fi
    cd ../../..
fi

# Go dependencies
if command -v go &> /dev/null && [ -f "control/api/go.mod" ]; then
    echo "📦 Go dependencies..."
    cd control/api
    go list -m -json all > "../../$SBOM_DIR/go-modules.json"
    if command -v cyclonedx-gomod &> /dev/null; then
        cyclonedx-gomod mod -json -output "../../$SBOM_DIR/go-bom.json"
    else
        echo "  Warning: cyclonedx-gomod not installed, skipping Go BOM"
    fi
    cd ../..
fi

# Rust dependencies
if command -v cargo &> /dev/null && [ -f "edge/Cargo.toml" ]; then
    echo "📦 Rust dependencies..."
    cd edge
    if command -v cargo-cyclonedx &> /dev/null; then
        cargo cyclonedx --format json --output "../$SBOM_DIR/rust-bom.json"
    else
        echo "  Warning: cargo-cyclonedx not installed, skipping Rust BOM"
    fi
    cd ..
fi

echo "✅ SBOM generation complete. Artifacts in $SBOM_DIR/"
ls -la "$SBOM_DIR/"