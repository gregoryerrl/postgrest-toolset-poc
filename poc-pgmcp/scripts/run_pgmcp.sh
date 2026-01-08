#!/bin/bash

# Run PGMCP server

set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check required env vars
if [ -z "$DATABASE_URL" ]; then
    echo "Error: DATABASE_URL environment variable is required"
    exit 1
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY environment variable is required"
    exit 1
fi

# Check if binary exists
if [ ! -f ./bin/pgmcp-server ]; then
    echo "PGMCP not found. Running install script..."
    ./scripts/install_pgmcp.sh
fi

echo "Starting PGMCP server..."
echo "Database: $DATABASE_URL"
echo "API: http://localhost:${PGMCP_PORT:-8080}"
echo ""

# Run server
./bin/pgmcp-server
