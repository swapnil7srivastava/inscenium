.PHONY: help setup python node cuda edge airflow cms db test lint qa golden build all smoke fix clean

help: ## Show this help message
	@echo "Inscenium Build System"
	@echo "====================="
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'
	@echo ""
	@echo "Environment variables:"
	@echo "  PYTHONPATH=. (automatically set)"
	@echo "  CUDA_ARCH=all (for GPU compilation)"

setup: python node cuda edge db ## Set up the entire development stack

python: ## Set up Python virtual environment and dependencies
	@echo "Setting up Python environment..."
	@bash ops/scripts/setup_python.sh

node: ## Install Node.js dependencies for CMS
	@echo "Setting up Node.js environment..."
	@bash ops/scripts/setup_node.sh

cuda: ## Compile CUDA kernels and create Python bindings
	@echo "Building CUDA components..."
	@bash ops/scripts/build_cuda.sh

edge: ## Build Rust/WASM edge workers and Go components
	@echo "Building edge workers..."
	@bash ops/scripts/build_edge.sh

airflow: ## Start local Airflow pipeline
	@echo "Starting Airflow..."
	@bash ops/scripts/run_airflow.sh

cms: ## Start Next.js content management system
	@echo "Starting CMS..."
	@bash ops/scripts/run_cms.sh

db: ## Set up and seed local database
	@echo "Setting up database..."
	@bash ops/scripts/seed_db.sh

test: ## Run test suite
	@echo "Running tests..."
	@poetry run pytest -q

lint: ## Run code linting and formatting
	@echo "Running linters..."
	@bash ops/scripts/lint_all.sh

golden: ## Run golden scene acceptance tests
	@echo "Running golden scene tests..."
	@. .venv/bin/activate && PYTHONPATH=. pytest -q tests/test_acceptance_quality.py

qa: test lint ## Run quality assurance (tests + linting)

build: setup test ## Full build (setup + test)

all: setup airflow cms ## Start complete local stack

smoke: ## Run smoke test to verify environment setup
	@echo "Running smoke test..."
	@[ -f "./.venv-runtime/bin/python" ] || ./fix_inscenium_env.sh
	@.venv-runtime/bin/python -c "import torch, torchvision, PIL, pydantic, numpy; print(f'Python: {__import__(\"sys\").version.split()[0]}'); print(f'torch: {torch.__version__}'); print(f'torchvision: {torchvision.__version__}'); print(f'Pillow: {PIL.__version__}'); print(f'pydantic: {pydantic.__version__}'); print(f'numpy: {numpy.__version__}')"

fix: ## Run environment fix script
	@echo "Running environment fix..."
	@./fix_inscenium_env.sh

clean: ## Clean build artifacts and runtime environment
	@echo "Cleaning build artifacts..."
	@rm -rf build/ dist/ target/ *.egg-info/
	@rm -rf render/*.so edge/*.wasm control/api/*.exe
	@rm -rf .venv-runtime inscenium_env_fix_*.log
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true

status: ## Show system status
	@echo "Inscenium System Status"
	@echo "======================"
	@echo ""
	@echo "Python environment:"
	@if [ -d ".venv" ]; then echo "  ✓ Virtual environment exists"; else echo "  ✗ Virtual environment missing"; fi
	@if [ -f "poetry.lock" ]; then echo "  ✓ Poetry dependencies locked"; else echo "  ✗ Poetry lock file missing"; fi
	@echo ""
	@echo "Build artifacts:"
	@if [ -f "render/compositor_cuda.so" ]; then echo "  ✓ CUDA compositor compiled"; else echo "  ✗ CUDA compositor missing"; fi
	@if [ -f "edge/edge_worker_wasm/pkg/edge_worker_wasm.wasm" ]; then echo "  ✓ WASM worker built"; else echo "  ✗ WASM worker missing"; fi
	@if [ -f "control/api/http_gateway" ]; then echo "  ✓ Go API gateway built"; else echo "  ✗ Go API gateway missing"; fi
	@echo ""
	@echo "Services:"
	@if pgrep -f "airflow" > /dev/null; then echo "  ✓ Airflow running"; else echo "  ✗ Airflow stopped"; fi
	@if pgrep -f "next" > /dev/null; then echo "  ✓ CMS running"; else echo "  ✗ CMS stopped"; fi
	@if pgrep -f "postgres" > /dev/null; then echo "  ✓ PostgreSQL running"; else echo "  ✗ PostgreSQL stopped"; fi

install-tools: ## Install required system tools
	@echo "Installing development tools..."
	@command -v rustc >/dev/null 2>&1 || (echo "Installing Rust..." && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh)
	@rustup target add wasm32-unknown-unknown 2>/dev/null || echo "WASM target already installed"
	@command -v go >/dev/null 2>&1 || echo "Please install Go 1.22+ manually"
	@command -v node >/dev/null 2>&1 || echo "Please install Node.js 20+ manually"
	@command -v pnpm >/dev/null 2>&1 || npm install -g pnpm
	@command -v nvcc >/dev/null 2>&1 || echo "CUDA toolkit not found - GPU features will be disabled"
	@command -v docker >/dev/null 2>&1 || echo "Docker not found - some services may not work"

dev: setup ## Start development mode (alias for setup)

prod-build: ## Production build (optimized)
	@echo "Building for production..."
	@PYTHONPATH=. . .venv/bin/activate && python -m pytest tests/ -x
	@bash ops/scripts/build_cuda.sh --release
	@bash ops/scripts/build_edge.sh --release
	@cd control/cms/webapp && pnpm build

docker-build: ## Build Docker images
	@echo "Building Docker images..."
	@docker build -t inscenium/api:latest -f ops/docker/Dockerfile.api .
	@docker build -t inscenium/worker:latest -f ops/docker/Dockerfile.worker .
	@docker build -t inscenium/cms:latest -f ops/docker/Dockerfile.cms control/cms/webapp/

logs: ## Show application logs
	@echo "Recent application logs:"
	@echo "======================"
	@if [ -f "logs/inscenium.log" ]; then tail -n 50 logs/inscenium.log; else echo "No log file found"; fi

benchmark: ## Run performance benchmarks
	@echo "Running performance benchmarks..."
	@. .venv/bin/activate && PYTHONPATH=. python -m pytest tests/benchmarks/ -v --benchmark-only

profile: ## Run profiling on key components
	@echo "Profiling key components..."
	@. .venv/bin/activate && PYTHONPATH=. python -m cProfile -o profile.stats -m inscenium.cli benchmark
	@. .venv/bin/activate && python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(20)"

api:
	@echo "[api] Starting API gateway"
	@docker compose up -d api

run-video: ## Run video processing demo
	@poetry run inscenium video --in samples/demo.mp4 --out runs/demo --profile cpu --render-overlay yes --every-nth 1

ci-quick: ## Quick CI test without rendering
	@poetry run inscenium video --in samples/demo.mp4 --out runs/ci --profile cpu --render-overlay no

report: ## Build HTML report for latest run
	@python -m inscenium.render.report --runs-dir runs

gallery: ## Build runs index gallery
	@python -m inscenium.render.report --runs-dir runs --index

fmt: ## Format code via ruff and pre-commit
	@command -v pre-commit >/dev/null 2>&1 && (pre-commit run -a || (pre-commit install && pre-commit run -a)) || echo "pre-commit not available"

lint-ruff: ## Run ruff linting
	@poetry run ruff check .
