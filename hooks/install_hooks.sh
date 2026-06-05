#!/usr/bin/env bash
# Optimus Prime CarosIA — install runtime protection hook.
#
# Registers optimus_preflight.py as a PreToolUse hook in Claude Code.
# Idempotent (running twice is safe). Reversible via uninstall_hooks.sh.
#
# Scope:
#   --user     (default) Install globally at ~/.claude/settings.json
#   --project  Install only for the current project at .claude/settings.json
#
# Requires: python3, jq

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_PATH="$SCRIPT_DIR/optimus_preflight.py"
SCOPE="user"

for arg in "$@"; do
  case "$arg" in
    --user) SCOPE="user" ;;
    --project) SCOPE="project" ;;
    -h|--help)
      echo "Usage: $0 [--user|--project]"
      exit 0
      ;;
    *)
      echo "Unknown flag: $arg" >&2; exit 2 ;;
  esac
done

if ! command -v jq >/dev/null 2>&1; then
  echo "❌ jq is required. Install with: brew install jq  (macOS) or apt install jq (Linux)" >&2
  exit 1
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ python3 is required but not found on PATH." >&2
  exit 1
fi
if [[ ! -f "$HOOK_PATH" ]]; then
  echo "❌ Could not find $HOOK_PATH" >&2
  exit 1
fi

chmod +x "$HOOK_PATH"

if [[ "$SCOPE" == "user" ]]; then
  SETTINGS_FILE="$HOME/.claude/settings.json"
else
  SETTINGS_FILE="$(pwd)/.claude/settings.json"
fi
mkdir -p "$(dirname "$SETTINGS_FILE")"

# Initialize file if missing or empty
if [[ ! -s "$SETTINGS_FILE" ]]; then
  echo '{}' > "$SETTINGS_FILE"
fi

# Validate existing JSON
if ! jq empty "$SETTINGS_FILE" 2>/dev/null; then
  echo "❌ $SETTINGS_FILE is not valid JSON. Please fix it or remove it, then retry." >&2
  exit 1
fi

BACKUP="$SETTINGS_FILE.optimus.bak.$(date +%s)"
cp "$SETTINGS_FILE" "$BACKUP"
echo "📦 Backup saved to $BACKUP"

HOOK_COMMAND="python3 \"$HOOK_PATH\""

# Add or replace the PreToolUse hook. Any existing non-Optimus hooks are preserved.
TMP="$(mktemp)"
jq --arg cmd "$HOOK_COMMAND" '
  .hooks //= {}
  | .hooks.PreToolUse //= []
  | .hooks.PreToolUse |= (
      map(select(.hooks[]?.command != $cmd))   # remove any stale Optimus entry
      + [{
          matcher: "",
          hooks: [{type: "command", command: $cmd}]
        }]
    )
' "$SETTINGS_FILE" > "$TMP"

mv "$TMP" "$SETTINGS_FILE"
echo "✅ Optimus Prime CarosIA runtime protection installed in $SETTINGS_FILE"
echo ""
echo "Next time Claude Code runs a tool call, Optimus will check it first."
echo "To verify: ask Claude to run a harmless command. You should see no friction."
echo "To uninstall: run uninstall_hooks.sh"
