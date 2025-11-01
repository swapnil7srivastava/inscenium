# Inscenium Airflow Dockerfile
# ============================

FROM apache/airflow:2.9.0-python3.11

USER root

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Copy requirements and install Python dependencies
COPY perception/requirements.txt /tmp/perception-requirements.txt
COPY pyproject.toml poetry.lock /tmp/

# Install Python packages
RUN pip install --no-cache-dir \
    poetry \
    psycopg2-binary \
    apache-airflow[postgres,celery] \
    && pip install --no-cache-dir -r /tmp/perception-requirements.txt

# Install project dependencies using poetry
COPY --chown=airflow:root pyproject.toml poetry.lock /app/
WORKDIR /app
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-root

# Copy application code
COPY --chown=airflow:root perception/ ./perception/
COPY --chown=airflow:root sgi/ ./sgi/
COPY --chown=airflow:root render/ ./render/
COPY --chown=airflow:root measure/ ./measure/
COPY --chown=airflow:root ops/pipelines/ ./ops/pipelines/

# Set environment variables
ENV PYTHONPATH=/app
ENV AIRFLOW_HOME=/home/airflow/airflow

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/sidecar_assets

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:8081/health || exit 1

WORKDIR /app
EXPOSE 8081