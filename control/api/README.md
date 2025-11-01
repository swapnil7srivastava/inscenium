# Inscenium API Gateway

REST API gateway that exposes Inscenium services over HTTP.

## Quick Start

```bash
# Generate Protocol Buffers
./scripts/gen_proto.sh

# Run the gateway
go run http_gateway.go

# Or with Docker
docker build -f ../../ops/docker/api.Dockerfile -t inscenium-api .
docker run -p 8080:8080 inscenium-api
```

## API Documentation

Interactive OpenAPI documentation is available:
- Swagger UI: `http://localhost:8080/docs` (when running)
- OpenAPI Spec: [openapi.yaml](./openapi.yaml)

## Key Endpoints

- `GET /health` - Health check
- `GET /readiness` - Readiness probe
- `GET /api/v1/sgi/opportunities` - List placement opportunities
- `POST /api/v1/bookings` - Create placement booking
- `GET /api/v1/analytics/metrics/:id` - Get placement metrics

## Authentication

Uses JWT Bearer tokens:

```bash
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"demo"}'
```

## Development

```bash
# Install dependencies
go mod download

# Generate gRPC code
./scripts/gen_proto.sh

# Run tests
go test ./...

# Format code
go fmt ./...

# Lint
golangci-lint run
```

## Configuration

Environment variables:
- `API_PORT` - Server port (default: 8080)
- `POSTGRES_DSN` - Database connection string
- `REDIS_URL` - Redis connection string
- `JWT_SECRET` - JWT signing secret
- `LOG_LEVEL` - Logging level (INFO, DEBUG, etc.)

## Database

Uses PostgreSQL for data persistence. Schema is applied automatically on startup from `sgi/sgi_schema.sql`.

## Monitoring

Exposes Prometheus metrics at `/metrics` when enabled.