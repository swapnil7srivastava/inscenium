#!/bin/bash
set -euo pipefail

echo "Setting up Node.js environment for Inscenium CMS..."

# Check Node.js version
if ! command -v node &> /dev/null; then
    echo "Node.js not found. Please install Node.js 20+"
    exit 1
fi

NODE_VERSION=$(node --version | sed 's/v//' | cut -d. -f1)
if [ "$NODE_VERSION" -lt 20 ]; then
    echo "Node.js version $NODE_VERSION is too old. Please install Node.js 20+"
    exit 1
fi

# Install pnpm if not present
if ! command -v pnpm &> /dev/null; then
    echo "Installing pnpm..."
    npm install -g pnpm
fi

# Navigate to CMS directory
cd control/cms/webapp

# Install dependencies
echo "Installing Node.js dependencies..."
pnpm install

# Return to root
cd ../../../

echo "✓ Node.js environment setup complete!"
echo ""
echo "To start the CMS:"
echo "  make cms"
echo "  # or manually:"
echo "  cd control/cms/webapp && pnpm dev"