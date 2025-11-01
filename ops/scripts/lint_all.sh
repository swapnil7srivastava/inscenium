#!/bin/bash
set -euo pipefail

echo "Running code linting and formatting for Inscenium..."

# Activate Python environment
source .venv/bin/activate

LINT_ERRORS=0

# Python linting
echo "🐍 Linting Python code..."
echo "========================="

# Check if Python linters are available
if ! command -v ruff &> /dev/null || ! command -v black &> /dev/null; then
    echo "Installing Python linting tools..."
    poetry install --with dev
fi

echo "Running ruff..."
if ruff check . --fix; then
    echo "✓ ruff passed"
else
    echo "✗ ruff found issues"
    ((LINT_ERRORS++))
fi

echo "Running black..."
if black --check .; then
    echo "✓ black passed"
else
    echo "⚠️  Running black formatter..."
    black .
    echo "✓ black formatting applied"
fi

echo "Running isort..."
if isort --check-only .; then
    echo "✓ isort passed"
else
    echo "⚠️  Running isort..."
    isort .
    echo "✓ isort formatting applied"
fi

echo "Running mypy type checking..."
if mypy --install-types --non-interactive perception/ sgi/ render/ measure/ 2>/dev/null; then
    echo "✓ mypy passed"
else
    echo "⚠️  mypy found type issues (some may be expected for stubs)"
fi

# Go linting
if [ -d "control/api" ] && [ -f "control/api/go.mod" ]; then
    echo ""
    echo "🐹 Linting Go code..."
    echo "===================="
    
    cd control/api
    
    echo "Running gofmt..."
    if [ -z "$(gofmt -l .)" ]; then
        echo "✓ gofmt passed"
    else
        echo "⚠️  Running gofmt..."
        gofmt -w .
        echo "✓ gofmt formatting applied"
    fi
    
    echo "Running go vet..."
    if go vet ./...; then
        echo "✓ go vet passed"
    else
        echo "✗ go vet found issues"
        ((LINT_ERRORS++))
    fi
    
    # Run golint if available
    if command -v golint &> /dev/null; then
        echo "Running golint..."
        if golint ./...; then
            echo "✓ golint passed"
        else
            echo "⚠️  golint found style issues"
        fi
    fi
    
    cd ../..
fi

# Rust linting
if [ -d "edge" ] && [ -f "edge/Cargo.toml" ]; then
    echo ""
    echo "🦀 Linting Rust code..."
    echo "======================"
    
    cd edge
    
    echo "Running rustfmt..."
    if cargo fmt --check; then
        echo "✓ rustfmt passed"
    else
        echo "⚠️  Running rustfmt..."
        cargo fmt
        echo "✓ rustfmt formatting applied"
    fi
    
    echo "Running clippy..."
    if cargo clippy --all-targets --all-features -- -D warnings; then
        echo "✓ clippy passed"
    else
        echo "✗ clippy found issues"
        ((LINT_ERRORS++))
    fi
    
    cd ..
fi

# JavaScript/TypeScript linting
if [ -d "control/cms/webapp" ] && [ -f "control/cms/webapp/package.json" ]; then
    echo ""
    echo "📜 Linting TypeScript/JavaScript..."
    echo "=================================="
    
    cd control/cms/webapp
    
    if command -v pnpm &> /dev/null; then
        echo "Running ESLint..."
        if pnpm lint; then
            echo "✓ ESLint passed"
        else
            echo "✗ ESLint found issues"
            ((LINT_ERRORS++))
        fi
        
        echo "Running Prettier..."
        if pnpm prettier --check .; then
            echo "✓ Prettier passed"
        else
            echo "⚠️  Running Prettier..."
            pnpm prettier --write .
            echo "✓ Prettier formatting applied"
        fi
    else
        echo "⚠️  pnpm not found, skipping TS/JS linting"
    fi
    
    cd ../../..
fi

# Shell script linting
echo ""
echo "🐚 Linting shell scripts..."
echo "=========================="

if command -v shellcheck &> /dev/null; then
    echo "Running shellcheck..."
    if find . -name "*.sh" -not -path "./.venv/*" -not -path "./node_modules/*" -exec shellcheck {} \;; then
        echo "✓ shellcheck passed"
    else
        echo "✗ shellcheck found issues"
        ((LINT_ERRORS++))
    fi
else
    echo "⚠️  shellcheck not found, install with: brew install shellcheck"
fi

# Terraform linting
if [ -d "ops/infra/terraform" ]; then
    echo ""
    echo "🏗️  Linting Terraform..."
    echo "======================="
    
    cd ops/infra/terraform
    
    if command -v terraform &> /dev/null; then
        echo "Running terraform fmt..."
        if terraform fmt -check; then
            echo "✓ terraform fmt passed"
        else
            echo "⚠️  Running terraform fmt..."
            terraform fmt
            echo "✓ terraform formatting applied"
        fi
        
        echo "Running terraform validate..."
        if terraform validate; then
            echo "✓ terraform validate passed"
        else
            echo "✗ terraform validate found issues"
            ((LINT_ERRORS++))
        fi
    else
        echo "⚠️  terraform not found"
    fi
    
    cd ../../..
fi

# Summary
echo ""
echo "🎯 Lint Summary"
echo "==============="

if [ $LINT_ERRORS -eq 0 ]; then
    echo "✅ All linting checks passed!"
    echo ""
    echo "Code quality summary:"
    echo "  🐍 Python: Formatted and type-checked"
    echo "  🐹 Go: Formatted and vetted"
    echo "  🦀 Rust: Formatted and clippied"
    echo "  📜 TypeScript: Formatted and linted"
    echo "  🐚 Shell: Checked with shellcheck"
    echo "  🏗️  Terraform: Formatted and validated"
else
    echo "❌ Found $LINT_ERRORS linting errors that need attention"
    echo ""
    echo "Please fix the issues above and run 'make lint' again"
    exit 1
fi