# Local Airflow Setup for Inscenium

This guide helps you set up and run Apache Airflow locally for the Inscenium video processing pipeline.

## Quick Start

```bash
# Start Airflow (this will install and configure everything)
make airflow

# Access the web UI
open http://localhost:8081
```

Default credentials:
- Username: `admin`
- Password: `admin`

## Manual Setup

If you prefer to set up Airflow manually:

```bash
# Activate Python environment
source .venv/bin/activate

# Install Airflow
pip install "apache-airflow==2.9.*" --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.9.0/constraints-3.11.txt"

# Set environment variables
export AIRFLOW_HOME="$(pwd)/airflow"
export AIRFLOW__CORE__DAGS_FOLDER="$(pwd)/ops/pipelines"

# Initialize database
airflow db init

# Create admin user
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@inscenium.dev \
    --password admin

# Start services
airflow webserver --port 8081 --daemon
airflow scheduler --daemon
```

## Pipeline Configuration

The main DAG is defined in `ops/pipelines/airflow_dag.py` with the following tasks:

1. **ingest_video** - Load and validate video input
2. **detect_shots** - PySceneDetect shot boundary detection
3. **sam2_segmentation** - SAM2 object segmentation
4. **depth_flow_estimation** - MiDaS depth + RAFT flow estimation
5. **surface_proposals** - Generate placement surface candidates
6. **uaor_fusion** - Uncertainty-aware occlusion reasoning
7. **update_sgi** - Persist results to Scene Graph Intelligence DB
8. **render_assets** - Generate HLS sidecar assets
9. **quality_control** - PRS scoring and validation

## Running the Pipeline

### Via Web UI

1. Navigate to http://localhost:8081
2. Find the `inscenium_video_pipeline` DAG
3. Click the play button to trigger a run
4. Configure run parameters in JSON:

```json
{
  "video_path": "/path/to/your/video.mp4",
  "title_id": 1
}
```

### Via CLI

```bash
# Trigger with default parameters
airflow dags trigger inscenium_video_pipeline

# Trigger with custom configuration
airflow dags trigger inscenium_video_pipeline \
    --conf '{"video_path": "tests/golden_scenes/assets/sample.mp4", "title_id": 1}'

# Monitor task status
airflow tasks list inscenium_video_pipeline
airflow dags state inscenium_video_pipeline
```

### Via Python API

```python
from airflow.api.client.local_client import Client

client = Client(None, None)
client.trigger_dag(
    dag_id='inscenium_video_pipeline',
    conf={'video_path': '/path/to/video.mp4', 'title_id': 1}
)
```

## Environment Variables

The pipeline uses these environment variables:

```bash
# Required
PYTHONPATH=.                    # Python module path
INSCENIUM_DATA=./data          # Data directory
POSTGRES_DSN=postgresql://...   # Database connection

# Optional
MOCK_ML_MODELS=true            # Use stub implementations
CUDA_VISIBLE_DEVICES=0         # GPU selection
OTEL_EXPORTER_OTLP_ENDPOINT=   # OpenTelemetry endpoint
```

## Development Mode

For development, enable stub implementations:

```bash
export MOCK_ML_MODELS=true
export INSCENIUM_TEST_MODE=true
```

This will use deterministic stubs for:
- SAM2 segmentation
- MiDaS depth estimation  
- RAFT optical flow
- Heavy ML computations

## Monitoring

### Task Logs

Logs are available in the Airflow UI under each task instance, or locally:

```bash
# View scheduler logs
tail -f airflow/logs/scheduler/latest

# View webserver logs
tail -f airflow/logs/dag_processor_manager/dag_processor_manager.log
```

### Metrics

The pipeline emits OpenTelemetry metrics for:
- Task execution times
- Processing throughput
- Quality scores
- Error rates

Configure `OTEL_EXPORTER_OTLP_ENDPOINT` to collect metrics.

## Troubleshooting

### Common Issues

**DAG not appearing:**
- Check DAGS_FOLDER path: `echo $AIRFLOW__CORE__DAGS_FOLDER`
- Verify Python path: `export PYTHONPATH=.`
- Check DAG syntax: `python ops/pipelines/airflow_dag.py`

**Task failures:**
- Check task logs in web UI
- Verify environment variables are set
- Ensure database is accessible
- Check file permissions

**Database connection errors:**
- Verify PostgreSQL is running: `make db`
- Check connection string in `.env`
- Test connection: `psql $POSTGRES_DSN`

**Missing dependencies:**
- Install Python packages: `poetry install`
- Install system dependencies per README

### Reset Airflow

To completely reset Airflow:

```bash
# Stop services
pkill -f "airflow webserver"
pkill -f "airflow scheduler"

# Remove Airflow data
rm -rf airflow/

# Reinitialize
make airflow
```

## Production Deployment

For production deployment:

1. Use external PostgreSQL (not SQLite)
2. Configure Redis for Celery executor
3. Set up proper authentication/authorization
4. Configure SSL/TLS
5. Use environment-specific configuration
6. Set up monitoring and alerting
7. Configure backup strategies

See `ops/infra/terraform/` for infrastructure templates.

## Performance Tuning

For better performance:

```bash
# Increase parallelism
export AIRFLOW__CORE__PARALLELISM=16
export AIRFLOW__CORE__DAG_CONCURRENCY=8

# Use LocalExecutor
export AIRFLOW__CORE__EXECUTOR=LocalExecutor

# Optimize database
export AIRFLOW__DATABASE__SQL_ALCHEMY_POOL_SIZE=10
```

For GPU workloads:
- Ensure CUDA is available
- Set `CUDA_VISIBLE_DEVICES`
- Monitor GPU memory usage
- Consider task queueing for GPU tasks