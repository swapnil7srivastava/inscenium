#!/bin/bash
set -euo pipefail

echo "Setting up and seeding Inscenium database..."

# Database configuration
DB_NAME="inscenium"
DB_USER="inscenium"  
DB_PASSWORD="inscenium"
DB_HOST="localhost"
DB_PORT="5432"

# Check if PostgreSQL is available
if ! command -v psql &> /dev/null; then
    echo "PostgreSQL not found. Attempting to start with Docker..."
    
    if command -v docker &> /dev/null; then
        echo "Starting PostgreSQL container..."
        docker run -d \
            --name inscenium-postgres \
            -e POSTGRES_DB="$DB_NAME" \
            -e POSTGRES_USER="$DB_USER" \
            -e POSTGRES_PASSWORD="$DB_PASSWORD" \
            -p "$DB_PORT:5432" \
            postgres:15-alpine 2>/dev/null || {
                echo "PostgreSQL container may already be running..."
            }
        
        # Wait for PostgreSQL to be ready
        echo "Waiting for PostgreSQL to be ready..."
        sleep 5
        
        # Test connection using docker exec
        if docker exec inscenium-postgres psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
            echo "✓ PostgreSQL container is ready"
        else
            echo "✗ Failed to connect to PostgreSQL container"
            exit 1
        fi
    else
        echo "Neither PostgreSQL nor Docker found. Please install one of:"
        echo "  - PostgreSQL 14+ directly"
        echo "  - Docker to run PostgreSQL in container"
        exit 1
    fi
fi

# Connection string
export PGPASSWORD="$DB_PASSWORD"
PSQL_CMD="psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME"

# Function to run SQL with docker if needed
run_sql() {
    if command -v psql &> /dev/null; then
        echo "$1" | $PSQL_CMD
    else
        echo "$1" | docker exec -i inscenium-postgres psql -U "$DB_USER" -d "$DB_NAME"
    fi
}

# Test connection
echo "Testing database connection..."
if run_sql "SELECT 1;" > /dev/null 2>&1; then
    echo "✓ Database connection successful"
else
    echo "✗ Failed to connect to database"
    echo "Please ensure PostgreSQL is running and accessible at:"
    echo "  Host: $DB_HOST:$DB_PORT"
    echo "  Database: $DB_NAME"
    echo "  User: $DB_USER"
    exit 1
fi

# Apply database schema
echo "Applying database schema..."
if [ -f "sgi/sgi_schema.sql" ]; then
    if command -v psql &> /dev/null; then
        $PSQL_CMD < sgi/sgi_schema.sql
    else
        docker exec -i inscenium-postgres psql -U "$DB_USER" -d "$DB_NAME" < sgi/sgi_schema.sql
    fi
    echo "✓ Database schema applied"
else
    echo "⚠️  Schema file not found: sgi/sgi_schema.sql"
    echo "Creating basic tables..."
    
    run_sql "
    CREATE TABLE IF NOT EXISTS titles (
        id SERIAL PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        duration_seconds INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS shots (
        id SERIAL PRIMARY KEY,
        title_id INTEGER REFERENCES titles(id),
        start_time REAL NOT NULL,
        end_time REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_shots_title_id ON shots(title_id);
    "
    echo "✓ Basic schema created"
fi

# Insert sample data
echo "Inserting sample data..."
run_sql "
INSERT INTO titles (title, duration_seconds) VALUES 
    ('Sample Movie Trailer', 120),
    ('Product Demo Video', 300),
    ('Sports Highlight Reel', 180)
ON CONFLICT DO NOTHING;

INSERT INTO shots (title_id, start_time, end_time) VALUES
    (1, 0.0, 5.2),
    (1, 5.2, 12.8),
    (1, 12.8, 25.1),
    (2, 0.0, 10.5),
    (2, 10.5, 30.2),
    (3, 0.0, 8.7),
    (3, 8.7, 15.3)
ON CONFLICT DO NOTHING;
"

# Verify data
echo "Verifying database setup..."
TITLE_COUNT=$(run_sql "SELECT COUNT(*) FROM titles;" | grep -E "^\s*[0-9]+\s*$" | xargs)
SHOT_COUNT=$(run_sql "SELECT COUNT(*) FROM shots;" | grep -E "^\s*[0-9]+\s*$" | xargs)

echo "✓ Database seeded successfully!"
echo "  Titles: $TITLE_COUNT"
echo "  Shots: $SHOT_COUNT"
echo ""
echo "Database connection details:"
echo "  Host: $DB_HOST:$DB_PORT"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo ""
echo "To connect manually:"
if command -v psql &> /dev/null; then
    echo "  psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME"
else
    echo "  docker exec -it inscenium-postgres psql -U $DB_USER -d $DB_NAME"
fi