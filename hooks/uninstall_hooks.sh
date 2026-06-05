#!/usr/bin/env bash
# Optimus Prime CarosIA — uninstall runtime protection hook.
#
# Removes optimus_preflight.py from Claude Code's PreToolUse hooks.
# Leaves other hooks untouched.

set -euo pipefail

SCOPE="user"
for arg in "$@"; do
  case "$arg" in
    --user) SCOPE="user" ;;
    --project) SCOPE="project" ;;
    *) echo "Unknown flag: $arg" >&2; exit 2 ;;
  esac
done

if ! command -v jq >/dev/null 2>&1; then
  echo "❌ jq is required." >&2; exit 1
fi

if [[ "$SCOPE" == "user" ]]; then
  SETTINGS_FILE="$HOME/.claude/settings.json"
else
  SETTINGS_FILE="$(pwd)/.claude/settings.json"
fi

if [[ ! -f "$SETTINGS_FILE" ]]; then
  echo "ℹ️  No settings file at $SETTINGS_FILE — nothing to uninstall."
  exit 0
fi

TMP="$(mktemp)"
jq '
  if .hooks.PreToolUse then
    .hooks.PreToolUse |= map(
      .hooks |= map(select((.command // "") | test("optimus_preflight") | not))
    )
    | .hooks.PreToolUse |= map(select((.hooks // []) | length > 0))
  else
    .
  end
' "$SETTINGS_FILE" > "$TMP"

mv "$TMP" "$SETTINGS_FILE"
echo "✅ Optimus Prime CarosIA runtime protection removed from $SETTINGS_FILE"
