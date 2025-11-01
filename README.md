# Inscenium™

**Make scenes addressable.**

Inscenium is an advanced computer vision and rendering system for creating contextual ad placement opportunities in video content. The platform combines scene understanding, surface geometry, rights management, and edge delivery to enable precise, unobtrusive advertising integration.

## Architecture Overview

Inscenium consists of four core modules:

- **Inscenium SGI** - Scene Graph Intelligence: Computer vision pipeline that analyzes video content to identify and track placement surfaces
- **Inscenium PRS** - Placement Readiness Score: Quality metrics for evaluating placement opportunities 
- **Inscenium Edge** - Edge delivery system with WebAssembly/WebGPU compositing workers
- **Inscenium UAOR** - Uncertainty-Aware Occlusion Reasoning: Advanced occlusion and uncertainty modeling

## Quick start

```bash
./fix_inscenium_env.sh && make smoke
```

- PyCharm/VSCode interpreter: `.venv-runtime/bin/python`

## Quick Start

### Prerequisites

- Python 3.11+
- CUDA 12.x (for GPU acceleration) 
- Rust stable with `wasm32-unknown-unknown` target
- Node.js 20+ with pnpm
- PostgreSQL 14+
- Docker (optional, for services)

### Setup

```bash
# Install Rust WASM target
rustup target add wasm32-unknown-unknown

# Set up the entire stack
make setup

# Start core services
make airflow    # Data pipeline
make cms        # Content management system

# Run tests
make test

# Run quality checks on golden scenes
make golden
```

### Development Workflow

```bash
make help       # Show all available targets
make build      # Full build (setup + test)
make lint       # Code formatting and linting
make all        # Complete local stack
```

## System Components

### Perception Pipeline (`perception/`)
- Shot detection and segmentation
- SAM2-based object segmentation  
- MiDaS depth estimation
- RAFT optical flow
- Surface proposal generation
- UAOR uncertainty fusion
- Saliency scoring

### Scene Graph Intelligence (`sgi/`)
- Surface tracking across shots
- Rights and restrictions ledger
- Placement opportunity matching
- Surface identity persistence

### Rendering Engine (`render/`)
- CUDA-accelerated compositor
- Spherical harmonics relighting
- HLS sidecar packaging
- Quality control metrics

### Edge Workers (`edge/`)
- Rust/WebAssembly compositing
- WebGPU shader pipeline
- Decision engine for creative selection
- HLS manifest patching

### Control Systems (`control/`)
- gRPC/HTTP API gateway (Go)
- Next.js content management system
- Placement booking interface
- Quality control dashboard

### Measurement (`measure/`)
- Placement Readiness Score (PRS)
- Exposure geometry calculation
- OpenTelemetry event emission
- Performance analytics

## Documentation

- [System Architecture](docs/architecture/system_overview.md)
- [UAOR Specification](docs/specs/uaor_v1.md)
- [Edge Sidecar Protocol](docs/specs/edge_sidecar_v1.md)
- [PRS Metrics](docs/specs/prs_metric_v1.md)
- [SGI Schema](docs/specs/sgi_schema_v1.md)
- [Legal & Compliance](docs/legal/compliance_playbook.md)

## Use in PyCharm/VSCode

For IDE integration, use the `.venv-runtime` environment created by `./fix_inscenium_env.sh`:
- **PyCharm**: Set Python Interpreter to `.venv-runtime/bin/python`
- **VSCode**: Select `.venv-runtime/bin/python` as your Python interpreter

## Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
PYTHONPATH=.
INSCENIUM_DATA=./data
CUDA_ARCH=all
POSTGRES_DSN=postgresql://inscenium:inscenium@localhost:5432/inscenium
```

| Variable | Description | Default |
|----------|-------------|---------|
| `PY_VERSION` | Python version to install | `3.11` |
| `POETRY_HYGIENE` | Clean install without cache | `1` |
| `FORCE_RECREATE` | Force recreate virtual environment | `1` |

## Running the CLI

Once installed with Poetry, the Inscenium CLI provides several utilities:

```bash
# Print a greeting
poetry run inscenium hello --name Inscenium

# Show library versions
poetry run inscenium versions
```

## Testing

The project includes comprehensive testing:

- **Acceptance Tests**: End-to-end pipeline validation
- **Golden Scenes**: Curated test cases with expected outputs
- **Unit Tests**: Component-level testing
- **Performance Tests**: PRS metric validation

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for community standards.

## Security

Report security issues per [SECURITY.md](SECURITY.md). All ML models use deterministic stubs by default for CI/development.

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

---

**Inscenium** - Advanced contextual advertising through computer vision and edge computing.