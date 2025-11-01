# Inscenium™

[![CI](https://github.com/inscenium/inscenium/actions/workflows/inscenium-smoke.yml/badge.svg)](https://github.com/inscenium/inscenium/actions/workflows/inscenium-smoke.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://python.org)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

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

## Video Pipeline Quick Start

> On CI/macOS we default to CPU and will fall back to the **stub detector** if torchvision ops aren't available; the pipeline still produces overlays, events, metrics, and the HTML report.

```bash
# Setup environment
./fix_inscenium_env.sh && make smoke

# Install main dependencies only
poetry install -n --only main

# Generate demo video and run pipeline
poetry run inscenium video --in samples/demo.mp4 --out runs/demo --profile cpu --render-overlay yes --max-frames 60

# Expected output structure:
# runs/demo/<timestamp>/
# ├── overlay.mp4          # Video with tracking overlays
# ├── events.sgi.jsonl     # Scene Graph Intelligence events
# ├── tracks.jsonl         # Individual track data  
# ├── metrics.json         # Pipeline performance metrics
# ├── thumbs/             # Frame thumbnails
# └── logs/               # Processing logs

# Example SGI JSONL line:
# {"ts": 0.033, "frame": 1, "objects": [{"id": 1, "label": "person", "bbox": [100, 50, 80, 120], "conf": 0.85}], "events": [], "uaor": {"occlusion": 0.1, "uncertainty": 0.2}}
```

## Reports & Gallery

Generate beautiful HTML reports and galleries from your pipeline runs:

```bash
# Generate report for the latest run
make report

# Generate gallery index of all runs  
make gallery

# View reports at runs/<run_id>/report.html
# View gallery at runs/index.html
```

Reports include performance metrics, stage latencies with mini sparklines, thumbnail galleries, and links to overlay videos. The gallery provides a consolidated view of all pipeline runs with quick access to reports and videos.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for community standards.

## Security

Report security issues per [SECURITY.md](SECURITY.md). All ML models use deterministic stubs by default for CI/development.

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

---

**Inscenium** - Advanced contextual advertising through computer vision and edge computing.