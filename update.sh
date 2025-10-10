#!/usr/bin/env bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔄 glmctl Docker image Update Script"
echo "================================"
echo ""
echo "This will rebuild the Docker image to update Claude Code CLI"
echo "and other dependencies to their latest versions."
echo ""

# Build Docker image
echo "🐳 Rebuilding Docker image..."
if ! ./build.sh; then
    echo -e "${RED}❌ Docker build failed!${NC}"
    exit 1
fi

echo ""
echo "================================"
echo -e "${GREEN}✅ Update complete!${NC}"
echo ""
echo "You can now use 'glm-code' with the latest version."
echo ""
