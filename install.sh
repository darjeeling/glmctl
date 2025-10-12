#!/usr/bin/env bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🚀 glmctl Installation Script"
echo "================================"
echo ""

# 1. Check if macOS
if [[ "$(uname)" != "Darwin" ]]; then
    echo -e "${RED}❌ Error: This installer is for macOS only.${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} Platform check: macOS"

# 2. Check Docker is installed and running
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Error: Docker is not installed.${NC}"
    echo ""
    echo "Please install one of the following:"
    echo "  - OrbStack: https://orbstack.dev/"
    echo "  - Docker Desktop: https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! docker ps &> /dev/null; then
    echo -e "${RED}❌ Error: Docker is not running.${NC}"
    echo ""
    echo "Please start Docker (OrbStack or Docker Desktop) and try again."
    exit 1
fi
echo -e "${GREEN}✓${NC} Docker check: installed and running"

# 3. Create ~/.glmenv directory structure
GLMENV_DIR="$HOME/.glmenv"
echo ""
echo "📁 Setting up $GLMENV_DIR..."

mkdir -p "$GLMENV_DIR/claude"
echo -e "${GREEN}✓${NC} Created directory: $GLMENV_DIR/claude"

# 4. Copy ENV.example to ~/.glmenv/env if it doesn't exist
if [[ ! -f "$GLMENV_DIR/env" ]]; then
    cp ENV.example "$GLMENV_DIR/env"
    echo -e "${GREEN}✓${NC} Created: $GLMENV_DIR/env"
    echo -e "${YELLOW}⚠${NC}  Please edit $GLMENV_DIR/env to configure your API keys"
else
    echo -e "${YELLOW}⚠${NC}  $GLMENV_DIR/env already exists, skipping..."
fi

# 5. Build Docker image
echo ""
echo "🐳 Building Docker image..."
if ! ./build.sh; then
    echo -e "${RED}❌ Docker build failed!${NC}"
    exit 1
fi

# 6. Create ~/.local/bin if it doesn't exist
LOCAL_BIN="$HOME/.local/bin"
mkdir -p "$LOCAL_BIN"
echo ""
echo -e "${GREEN}✓${NC} Created directory: $LOCAL_BIN"

# 7. Create symlink to glm-code.sh and cc-code.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ln -sf "$SCRIPT_DIR/glm-code.sh" "$LOCAL_BIN/glm-code"
chmod +x "$SCRIPT_DIR/glm-code.sh"
echo -e "${GREEN}✓${NC} Created symlink: $LOCAL_BIN/glm-code"

ln -sf "$SCRIPT_DIR/cc-code.sh" "$LOCAL_BIN/cc-code"
chmod +x "$SCRIPT_DIR/cc-code.sh"
echo -e "${GREEN}✓${NC} Created symlink: $LOCAL_BIN/cc-code"

# 8. Check if ~/.local/bin is in PATH
echo ""
if [[ ":$PATH:" != *":$LOCAL_BIN:"* ]]; then
    echo -e "${YELLOW}⚠${NC}  $LOCAL_BIN is not in your PATH"
    echo ""
    echo "Add the following line to your shell config file:"
    echo ""
    echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
    echo "Shell config files:"
    echo "  - bash: ~/.bashrc or ~/.bash_profile"
    echo "  - zsh:  ~/.zshrc"
    echo ""
else
    echo -e "${GREEN}✓${NC} $LOCAL_BIN is already in PATH"
fi

# 9. Done
echo ""
echo "================================"
echo -e "${GREEN}✅ Installation complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Edit $GLMENV_DIR/env to configure your API settings"
echo "  2. Run 'glm-code' for GLM API or 'cc-code' for Claude Code"
echo ""
echo "Available commands:"
echo "  - glm-code: Use GLM API (requires $GLMENV_DIR/env configuration)"
echo "  - cc-code:  Use standard Claude Code (uses ~/.claude)"
echo ""
