#!/bin/bash
set -euo pipefail

echo "Starting Inscenium CMS (Next.js)..."

# Check if Node.js and pnpm are available
if ! command -v node &> /dev/null; then
    echo "Node.js not found. Please run 'make node' first."
    exit 1
fi

if ! command -v pnpm &> /dev/null; then
    echo "pnpm not found. Please run 'make node' first."
    exit 1
fi

# Navigate to CMS directory
cd control/cms/webapp

# Check if dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    pnpm install
fi

# Check if .env.local exists, if not copy from example
if [ ! -f ".env.local" ]; then
    if [ -f ".env.example" ]; then
        echo "Creating .env.local from example..."
        cp .env.example .env.local
        echo "⚠️  Please review .env.local and update configuration as needed"
    fi
fi

# Start the development server
echo "Starting Next.js development server..."
echo ""
echo "CMS will be available at: http://localhost:3000"
echo ""
echo "To stop the CMS, press Ctrl+C"
echo ""

# Start in development mode
pnpm dev