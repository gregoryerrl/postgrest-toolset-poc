#!/bin/bash

# Run the MCP Toolbox server

set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if toolbox binary exists
if [ ! -f ./bin/toolbox ]; then
    echo "Toolbox not found. Running install script..."
    ./scripts/install_toolbox.sh
fi

echo "Starting MCP Toolbox server..."
echo "Config: toolbox/tools.yaml"
echo "URL: http://127.0.0.1:5000"
echo ""

# Run toolbox with tools.yaml
./bin/toolbox --tools-file toolbox/tools.yaml
