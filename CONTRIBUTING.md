# Contributing to Inscenium

Thank you for your interest in contributing to Inscenium! This document provides guidelines and information for contributors.

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- Python 3.11+
- CUDA 12.x (for GPU features)
- Rust stable with `wasm32-unknown-unknown` target
- Node.js 20+ with pnpm
- PostgreSQL 14+
- Git with LFS support

### Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/inscenium.git
   cd inscenium
   ```

3. Install dependencies:
   ```bash
   make setup
   ```

4. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Development Workflow

### Code Style

We maintain strict code quality standards:

- **Python**: PEP-8 compliance, type hints required
- **TypeScript**: ESLint + Prettier configuration
- **Rust**: Standard rustfmt + clippy
- **Go**: gofmt + golint + go vet

All code is automatically formatted via pre-commit hooks.

### Testing

Before submitting changes:

1. Run the test suite:
   ```bash
   make test
   ```

2. Run golden scene acceptance tests:
   ```bash
   make golden
   ```

3. Verify linting passes:
   ```bash
   make lint
   ```

### Making Changes

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following the project conventions
3. Add tests for new functionality
4. Update documentation if needed
5. Commit with descriptive messages

### Commit Messages

Use conventional commit format:

```
type(scope): description

feat(sgi): add surface identity persistence
fix(render): resolve depth buffer allocation issue
docs(uaor): update fusion algorithm specification
test(golden): add new placement scenarios
```

## Code Organization

### Module Structure

- **perception/**: Computer vision pipeline components
- **sgi/**: Scene graph intelligence and rights management
- **render/**: CUDA compositing and quality metrics
- **edge/**: WebAssembly workers and decision engines
- **control/**: API gateway and content management
- **measure/**: PRS scoring and analytics
- **docs/**: Specifications and architecture documentation

### Adding New Features

When adding features:

1. Check existing patterns in similar modules
2. Add comprehensive docstrings and type hints
3. Include unit tests with >80% coverage
4. Update relevant documentation
5. Consider performance implications
6. Add logging with structured format

### ML Model Integration

ML models should:

- Provide deterministic stub implementations for CI
- Include proper error handling for missing models
- Support both CPU and CUDA execution paths
- Include performance benchmarks
- Document model versions and requirements

## Pull Request Process

1. Ensure CI passes (tests, linting, type checking)
2. Update documentation for user-facing changes
3. Add changelog entry if appropriate
4. Request review from relevant module maintainers
5. Address review feedback promptly

### Review Criteria

Pull requests are evaluated on:

- Code quality and style consistency
- Test coverage and quality
- Performance impact
- Security considerations
- Documentation completeness
- Backward compatibility

## Security

### Reporting Issues

Report security vulnerabilities via email to security@inscenium.dev. Do not create public GitHub issues for security problems.

### Best Practices

- Never commit secrets, API keys, or credentials
- Validate all user inputs
- Use parameterized SQL queries
- Follow OWASP guidelines for web components
- Implement proper authentication and authorization

## Documentation

### Types of Documentation

- **Code Documentation**: Comprehensive docstrings and inline comments
- **API Documentation**: OpenAPI specs for REST endpoints
- **Architecture Documentation**: System design and decision records
- **User Documentation**: Setup guides and usage examples

### Writing Guidelines

- Use clear, concise language
- Include code examples
- Keep documentation up-to-date with code changes
- Follow the project's documentation templates

## Legal and Compliance

### Rights and Clearances

When contributing content recognition or rights management features:

- Understand advertising disclosure requirements
- Consider international compliance (FTC, ASCI, Ofcom)
- Document any legal assumptions or limitations
- Consult legal team for significant changes

### Data Privacy

- Follow GDPR/CCPA requirements for personal data
- Implement data minimization principles
- Document data flows and retention policies
- Include privacy impact assessments

## Getting Help

### Resources

- [Architecture Overview](docs/architecture/system_overview.md)
- [API Documentation](control/api/README.md)
- [Development Setup](README.md#quick-start)
- [Troubleshooting Guide](docs/troubleshooting.md)

### Community

- GitHub Issues: Bug reports and feature requests
- GitHub Discussions: General questions and ideas
- Email: dev@inscenium.dev for development questions

## Recognition

Contributors are recognized in:

- README.md contributor section
- Release notes for significant contributions
- Annual contributor acknowledgments

Thank you for helping make Inscenium better!