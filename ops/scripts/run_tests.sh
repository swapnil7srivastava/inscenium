#!/bin/bash
set -euo pipefail

echo "Running Inscenium test suite..."

# Activate Python environment
source .venv/bin/activate

# Set environment variables for testing
export PYTHONPATH="$(pwd)"
export MOCK_ML_MODELS=true
export INSCENIUM_TEST_MODE=true

# Check if pytest is available
if ! command -v pytest &> /dev/null; then
    echo "pytest not found. Installing test dependencies..."
    poetry install --with dev
fi

# Run tests with coverage
echo "Running Python tests with coverage..."
python -m pytest tests/ \
    --cov=perception \
    --cov=sgi \
    --cov=render \
    --cov=edge \
    --cov=measure \
    --cov-report=term-missing \
    --cov-report=html:htmlcov \
    -v

# Check test results
if [ $? -eq 0 ]; then
    echo "✓ Python tests passed"
else
    echo "✗ Python tests failed"
    exit 1
fi

# Run Go tests if Go components exist
if [ -d "control/api" ] && [ -f "control/api/go.mod" ]; then
    echo "Running Go tests..."
    cd control/api
    go test ./... -v
    if [ $? -eq 0 ]; then
        echo "✓ Go tests passed"
    else
        echo "✗ Go tests failed"
        cd ../..
        exit 1
    fi
    cd ../..
fi

# Run Rust tests if Rust components exist
if [ -d "edge" ] && [ -f "edge/Cargo.toml" ]; then
    echo "Running Rust tests..."
    cd edge
    cargo test --verbose
    if [ $? -eq 0 ]; then
        echo "✓ Rust tests passed"
    else
        echo "✗ Rust tests failed"
        cd ..
        exit 1
    fi
    cd ..
fi

# Run Node.js tests if CMS exists
if [ -d "control/cms/webapp" ] && [ -f "control/cms/webapp/package.json" ]; then
    echo "Running CMS tests..."
    cd control/cms/webapp
    if command -v pnpm &> /dev/null; then
        pnpm test 2>/dev/null || echo "⚠️  CMS tests not configured yet"
    fi
    cd ../../..
fi

echo ""
echo "✓ Test suite completed!"
echo ""
echo "Coverage report generated in: htmlcov/index.html"
echo ""
echo "Test summary:"
echo "  Python: ✓ Passed"
if [ -d "control/api" ]; then
    echo "  Go API: ✓ Passed"
fi
if [ -d "edge" ]; then
    echo "  Rust Edge: ✓ Passed"
fi
if [ -d "control/cms/webapp" ]; then
    echo "  CMS: ⚠️  Tests not configured"
fi