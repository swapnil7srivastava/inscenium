#!/bin/bash
set -euo pipefail

echo "Starting local Airflow for Inscenium pipeline..."

# Activate Python environment
source .venv/bin/activate

# Check if Airflow is installed
if ! command -v airflow &> /dev/null; then
    echo "Installing Apache Airflow..."
    pip install "apache-airflow==2.9.*" --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.9.0/constraints-3.11.txt"
fi

# Set Airflow environment variables
export AIRFLOW_HOME="$(pwd)/airflow"
export AIRFLOW__CORE__DAGS_FOLDER="$(pwd)/ops/pipelines"
export AIRFLOW__CORE__LOAD_EXAMPLES=False
export AIRFLOW__CORE__EXECUTOR=LocalExecutor
export AIRFLOW__DATABASE__SQL_ALCHEMY_CONN="sqlite:///$(pwd)/airflow/airflow.db"
export AIRFLOW__WEBSERVER__WEB_SERVER_PORT=8081
export AIRFLOW__CORE__ENABLE_XCOM_PICKLING=True

# Create Airflow directory
mkdir -p "$AIRFLOW_HOME"

# Initialize database if it doesn't exist
if [ ! -f "$AIRFLOW_HOME/airflow.db" ]; then
    echo "Initializing Airflow database..."
    airflow db init
    
    # Create admin user
    echo "Creating admin user..."
    airflow users create \
        --username admin \
        --firstname Admin \
        --lastname User \
        --role Admin \
        --email admin@inscenium.dev \
        --password admin
fi

# Check if Airflow is already running
if pgrep -f "airflow webserver" > /dev/null; then
    echo "Airflow webserver is already running"
else
    echo "Starting Airflow webserver..."
    airflow webserver --port 8081 --daemon
fi

if pgrep -f "airflow scheduler" > /dev/null; then
    echo "Airflow scheduler is already running"
else
    echo "Starting Airflow scheduler..."
    airflow scheduler --daemon
fi

# Wait a moment for services to start
sleep 3

# Check if services started successfully
if pgrep -f "airflow webserver" > /dev/null && pgrep -f "airflow scheduler" > /dev/null; then
    echo "✓ Airflow started successfully!"
    echo ""
    echo "Airflow Web UI: http://localhost:8081"
    echo "Username: admin"
    echo "Password: admin"
    echo ""
    echo "DAGs location: ops/pipelines/"
    echo ""
    echo "To stop Airflow:"
    echo "  pkill -f 'airflow webserver'"
    echo "  pkill -f 'airflow scheduler'"
else
    echo "✗ Failed to start Airflow services"
    echo "Check logs in: $AIRFLOW_HOME/logs/"
    exit 1
fi

# Show recent logs
echo "Recent scheduler logs:"
if [ -f "$AIRFLOW_HOME/logs/scheduler/latest" ]; then
    tail -n 5 "$AIRFLOW_HOME/logs/scheduler/latest" 2>/dev/null || echo "No logs available yet"
fi