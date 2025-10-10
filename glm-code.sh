#!/usr/bin/env bash
set -e

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

GLMENV_DIR="$HOME/.glmenv"
ENV_FILE="$GLMENV_DIR/env"

# Check if env file exists
if [[ ! -f "$ENV_FILE" ]]; then
    echo -e "${RED}❌ Error: Configuration file not found${NC}"
    echo ""
    echo "Expected location: $ENV_FILE"
    echo ""
    echo "Please run 'install.sh' first to set up glmctl."
    exit 1
fi

# Check if Docker is running
if ! docker ps &> /dev/null; then
    echo -e "${RED}❌ Error: Docker is not running.${NC}"
    echo ""
    echo "Please start Docker (OrbStack or Docker Desktop) and try again."
    exit 1
fi

# Get current directory name
CURRENT_DIR=$(basename "$(pwd)")

# Run Docker container
docker run -it --rm --platform linux/amd64 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v "$GLMENV_DIR/claude:/root/.claude" \
  -v "$HOME/.gitconfig:/root/.gitconfig" \
  -v "$(pwd):/workspace/$CURRENT_DIR" \
  --env-file "$ENV_FILE" \
  --workdir "/workspace/$CURRENT_DIR" \
  glmctl-env-amd64 /bin/bash
