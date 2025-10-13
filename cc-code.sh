#!/usr/bin/env bash
set -e

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Show help message
show_help() {
    cat << EOF
Usage: cc-code.sh [OPTIONS]

Run Claude Code in an isolated Docker environment.

Options:
  --with <path>    Mount an additional project directory as readonly
                   Can be specified multiple times
                   Example: --with ../backend --with ../frontend
  --help           Show this help message

Examples:
  cc-code.sh
  cc-code.sh --with ../backend
  cc-code.sh --with ../backend --with ../frontend

Inside the container:
  Current project: Read-write access
  Additional projects (--with): Readonly access at /workspace/<dirname>
EOF
    exit 0
}

# Parse command line arguments
ADDITIONAL_PROJECTS=()
while [[ $# -gt 0 ]]; do
    case $1 in
        --with)
            if [[ -z "$2" || "$2" == --* ]]; then
                echo -e "${RED}❌ Error: --with requires a path argument${NC}"
                exit 1
            fi
            ADDITIONAL_PROJECTS+=("$2")
            shift 2
            ;;
        --help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}❌ Error: Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

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

# Validate and process additional projects
MOUNT_OPTIONS=""
MOUNTED_DIRS=("$CURRENT_DIR")

for project_path in "${ADDITIONAL_PROJECTS[@]}"; do
    # Check if directory exists
    if [[ ! -d "$project_path" ]]; then
        echo -e "${RED}❌ Error: Directory does not exist: $project_path${NC}"
        exit 1
    fi

    # Convert to absolute path
    abs_path=$(cd "$project_path" && pwd)
    dir_name=$(basename "$abs_path")

    # Check for name conflicts
    for mounted in "${MOUNTED_DIRS[@]}"; do
        if [[ "$mounted" == "$dir_name" ]]; then
            echo -e "${RED}❌ Error: Directory name conflict: '$dir_name'${NC}"
            echo "Multiple directories with the same name cannot be mounted."
            echo "Please rename one of the directories or use a different path."
            exit 1
        fi
    done

    MOUNTED_DIRS+=("$dir_name")
    MOUNT_OPTIONS="$MOUNT_OPTIONS -v \"$abs_path:/workspace/$dir_name:ro\""
    echo -e "${GREEN}✓ Will mount (readonly): $dir_name${NC}"
done

# Run Docker container
eval docker run -it --rm --platform linux/amd64 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v \"$HOME/.ssh:/root/.ssh:ro\" \
  -v \"$HOME/.claude:/root/.claude\" \
  -v \"$HOME/.gitconfig:/root/.gitconfig\" \
  -v \"$PWD:$PWD\" \
  -e IS_SANDBOX=1 \
  --workdir \"$PWD\" \
  $MOUNT_OPTIONS \
  glmctl-env-amd64 /bin/bash
