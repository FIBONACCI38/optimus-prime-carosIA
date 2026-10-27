#!/usr/bin/env bash
# Regression tests for hooks/install_hooks.sh and hooks/uninstall_hooks.sh.
#
# Runs both scripts with --project inside a throwaway directory and checks
# that unrelated PreToolUse hooks are preserved exactly (no duplication,
# no loss) and that repeated installs are idempotent.
#
# Exit code 0 = all tests pass; 1 = at least one failure. Requires jq.

set -uo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

PASSED=0
FAILED=0

check() {
  local name="$1" expected="$2" actual="$3"
  if [[ "$expected" == "$actual" ]]; then
    echo "✅ $name"
    PASSED=$((PASSED + 1))
  else
    echo "❌ $name"
    echo "   expected: $expected"
    echo "   actual:   $actual"
    FAILED=$((FAILED + 1))
  fi
}

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# Run against a copy of hooks/ so the installer's chmod doesn't touch the repo.
cp -R "$REPO_DIR/hooks" "$WORK/hooks"
INSTALL="$WORK/hooks/install_hooks.sh"
UNINSTALL="$WORK/hooks/uninstall_hooks.sh"

mkdir -p "$WORK/project/.claude"
cd "$WORK/project"

# A user config with an entry holding two hooks, plus a single-hook entry.
ORIGINAL='{"hooks":{"PreToolUse":[{"matcher":"Bash","hooks":[{"type":"command","command":"a"},{"type":"command","command":"b"}]},{"matcher":"Write","hooks":[{"type":"command","command":"c"}]}]}}'
echo "$ORIGINAL" > .claude/settings.json
USER_ENTRIES="$(echo "$ORIGINAL" | jq -c '.hooks.PreToolUse')"

bash "$INSTALL" --project >/dev/null
check "install keeps existing hooks unchanged" \
  "$USER_ENTRIES" \
  "$(jq -c '[.hooks.PreToolUse[] | select(any(.hooks[]; .command | test("optimus_preflight")) | not)]' .claude/settings.json)"
check "install adds exactly one Optimus hook" \
  "1" \
  "$(jq '[.hooks.PreToolUse[].hooks[] | select(.command | test("optimus_preflight"))] | length' .claude/settings.json)"

bash "$INSTALL" --project >/dev/null
bash "$INSTALL" --project >/dev/null
check "repeated installs are idempotent (3 entries total)" \
  "3" \
  "$(jq '.hooks.PreToolUse | length' .claude/settings.json)"
check "repeated installs keep a single Optimus hook" \
  "1" \
  "$(jq '[.hooks.PreToolUse[].hooks[] | select(.command | test("optimus_preflight"))] | length' .claude/settings.json)"

bash "$UNINSTALL" --project >/dev/null
check "uninstall restores the original PreToolUse entries" \
  "$USER_ENTRIES" \
  "$(jq -c '.hooks.PreToolUse' .claude/settings.json)"

echo ""
echo "Results: $PASSED/$((PASSED + FAILED)) passed, $FAILED failed"
[[ "$FAILED" -eq 0 ]]
