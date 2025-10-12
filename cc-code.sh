#!/usr/bin/env bash
set -e

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker ps &> /dev/null; then
    echo -e "${RED}❌ Error: Docker is not running.${NC}"
    echo ""
    echo "Please start Docker (OrbStack or Docker Desktop) and try again."
    exit 1
fi

# Get current directory name
CURRENT_DIR=$(basename "$(pwd)")
PWD=$(pwd)

# Run Docker container
docker run -it --rm --platform linux/amd64 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v "$HOME/.ssh:/root/.ssh:ro" \
  -v "$HOME/.claude:/root/.claude" \
  -v "$HOME/.gitconfig:/root/.gitconfig" \
  -v "$PWD:$PWD" \
  --workdir "$PWD" \
  glmctl-env-amd64 /bin/bash
