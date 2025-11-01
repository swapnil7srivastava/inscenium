#!/bin/bash
set -euo pipefail

echo "Setting up Python environment for Inscenium..."

# Check Python version
if ! command -v python3.11 &> /dev/null; then
    echo "Python 3.11 not found. Please install Python 3.11+"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3.11 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Update pip
echo "Updating pip..."
pip install -U pip

# Install Poetry if not present
if ! command -v poetry &> /dev/null; then
    echo "Installing Poetry..."
    pip install poetry
fi

# Configure Poetry to use local venv
poetry config virtualenvs.in-project true
poetry config virtualenvs.create false

# Install dependencies
echo "Installing Python dependencies..."
poetry install --no-root

# Set up development tools
echo "Installing pre-commit hooks..."
pre-commit install

# Verify installation
echo "Verifying Python setup..."
python --version
poetry --version
pre-commit --version

echo "✓ Python environment setup complete!"
echo ""
echo "To activate the environment manually:"
echo "  source .venv/bin/activate"