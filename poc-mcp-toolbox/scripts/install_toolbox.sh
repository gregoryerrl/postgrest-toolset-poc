#!/bin/bash

# Install MCP Toolbox for Databases

set -e

echo "Installing MCP Toolbox for Databases..."

# Detect OS and architecture
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

if [ "$ARCH" = "x86_64" ]; then
    ARCH="amd64"
elif [ "$ARCH" = "arm64" ] || [ "$ARCH" = "aarch64" ]; then
    ARCH="arm64"
fi

# Get latest release
LATEST_VERSION=$(curl -s https://api.github.com/repos/googleapis/genai-toolbox/releases/latest | grep '"tag_name"' | sed -E 's/.*"([^"]+)".*/\1/')

if [ -z "$LATEST_VERSION" ]; then
    echo "Could not determine latest version. Using v0.6.0"
    LATEST_VERSION="v0.6.0"
fi

echo "Downloading Toolbox $LATEST_VERSION for $OS/$ARCH..."

# Download URL
DOWNLOAD_URL="https://github.com/googleapis/genai-toolbox/releases/download/${LATEST_VERSION}/toolbox_${OS}_${ARCH}"

# Download to local bin directory
mkdir -p ./bin
curl -L "$DOWNLOAD_URL" -o ./bin/toolbox
chmod +x ./bin/toolbox

echo "Toolbox installed to ./bin/toolbox"
./bin/toolbox --version
