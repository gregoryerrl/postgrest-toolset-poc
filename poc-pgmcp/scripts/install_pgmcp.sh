#!/bin/bash

# Install PGMCP from source

set -e

echo "Installing PGMCP..."

# Check for Go
if ! command -v go &> /dev/null; then
    echo "Go is required. Please install Go 1.21+ first."
    echo "  macOS: brew install go"
    echo "  Ubuntu: sudo apt install golang-go"
    exit 1
fi

# Clone repository
if [ ! -d "pgmcp" ]; then
    git clone https://github.com/subnetmarco/pgmcp.git
fi

cd pgmcp

# Build server and client
echo "Building PGMCP server..."
go build -o ../bin/pgmcp-server ./server

echo "Building PGMCP client..."
go build -o ../bin/pgmcp-client ./client

cd ..

echo ""
echo "PGMCP installed successfully!"
echo "  Server: ./bin/pgmcp-server"
echo "  Client: ./bin/pgmcp-client"
