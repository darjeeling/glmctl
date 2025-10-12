#!/usr/bin/env bash
# Claude Code Monitor & Retry Runner with Model Selection
# - Allows choosing a model: opus, sonnet, haiku (default: sonnet)
# - Runs Claude until it exits with code 0 (success), otherwise waits and retries.
# - If the process exits with a non-zero code, the script will wait for 1.5 hours and then restart the process.
# - If the process exits with a zero code, the script will exit.

set -u

# ===== Find Claude Command =====
find_claude_cmd() {
  # Try common paths for claude command
  local claude_paths=(
    "claude"  # Try PATH first
    "$HOME/.claude/local/claude"
    "$HOME/.local/bin/claude"
    "/usr/local/bin/claude"
    "/opt/homebrew/bin/claude"
    "$(which claude 2>/dev/null)"
  )

  for path in "${claude_paths[@]}"; do
    if [[ -n "$path" ]] && command -v "$path" &>/dev/null; then
      echo "$path"
      return 0
    fi
  done

  echo "claude"  # fallback to PATH
}

# ===== Defaults =====
SLEEP_SECS="${SLEEP_SECS:-5400}"   # default: 1.5 hours
#CLAUDE_CMD="${CLAUDE_CMD:-$(find_claude_cmd) --dangerously-skip-permissions}"  # auto-detect claude command
CLAUDE_CMD="${CLAUDE_CMD:-$(find_claude_cmd) }"  # auto-detect claude command
MODEL="sonnet"  # default model: sonnet
CONTINUE_MODE=false  # --continue flag disabled by default

print_usage() {
  cat <<'USAGE'
Usage:
  _claude_cont.sh [-q "QUERY"] [-f prompt.txt] [-m opus|sonnet|haiku] [-c] [-- ...extra args...]

Options:
  -q "QUERY"     : Prompt string passed to Claude
  -f FILE        : Read prompt from file
  -m MODEL       : Model to use (opus, sonnet, haiku). Default is sonnet
  -c             : Add --continue flag to CLAUDE_CMD
  --             : All remaining args are passed directly to CLAUDE_CMD

Environment:
  SLEEP_SECS     : Wait time before retry (seconds). Default 5400 (1.5h)
  CLAUDE_CMD     : Execution command. Default "claude code"

Examples:
  ./_claude_cont.sh -q "please continue"
  ./_claude_cont.sh -f prompt.txt -m opus -c
  ./_claude_cont.sh -q "build project" -m haiku -- --dangerously-skip-permissions
USAGE
}

log() { printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }

# ===== Argument parsing =====
QUERY=""
FILE=""
EXTRA_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    -q|--query) QUERY="${2:-}"; shift 2 ;;
    -f|--file)  FILE="${2:-}";  shift 2 ;;
    -m|--model) MODEL="${2:-}"; shift 2 ;;
    -c|--continue) CONTINUE_MODE=true; shift ;;
    --) shift; EXTRA_ARGS=("$@"); break ;;
    -h|--help) print_usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; print_usage; exit 2 ;;
  esac
done

# Validate model
case "$MODEL" in
  opus|sonnet|haiku) ;; # valid
  *) echo "ERROR: Invalid model '$MODEL'. Allowed: opus, sonnet, haiku" >&2; exit 2 ;;
esac

# Load query from file if provided
if [[ -n "$FILE" ]]; then
  if [[ ! -f "$FILE" ]]; then
    echo "ERROR: File not found: $FILE" >&2
    exit 2
  fi
  QUERY="$(cat "$FILE")"
fi

# Prompt for query if still empty
if [[ -z "${QUERY}" ]]; then
  echo -n "Enter query for Claude: "
  IFS= read -r QUERY
fi

# Safe shutdown on signals
trap 'log "Received termination signal. Stopping monitor."; exit 130' INT TERM

# Prepare final command with continue flag if needed
FINAL_CLAUDE_CMD="$CLAUDE_CMD"
if [[ "$CONTINUE_MODE" == true ]]; then
  FINAL_CLAUDE_CMD="$CLAUDE_CMD --continue"
fi

log "Claude Process Monitor started"
log "Retry interval: ${SLEEP_SECS}s | Command: ${FINAL_CLAUDE_CMD} | Model: ${MODEL}"

# ===== Loop =====
FIRST_RUN=true
while true; do
  if [[ "$FIRST_RUN" == true ]]; then
    FIRST_RUN=false
    log "Launching Claude (model=$MODEL)"
    ${FINAL_CLAUDE_CMD} --model "$MODEL" -p "$QUERY" ${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"}
  else
    log "Continuing Claude (model=$MODEL)"
    ${FINAL_CLAUDE_CMD} --model "$MODEL" -p "continue all previous works" ${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"}
  fi

  EXIT_STATUS=$?

  if [[ $EXIT_STATUS -eq 0 ]]; then
    log "Claude exited successfully (exit code=0). Stopping loop."
    break
  else
    log "Claude exited with error (exit code=${EXIT_STATUS}). Retrying after ${SLEEP_SECS}s..."
    sleep "${SLEEP_SECS}"
  fi
done
