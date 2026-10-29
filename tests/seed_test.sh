#!/usr/bin/env bash
# Runs the scripted-scenario seed into a temp dir and checks both clones start from the same state.
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"
d="$(mktemp -d)"; trap 'rm -rf "$d"' EXIT
bash "$here/examples/scripted/seed.sh" "$d/run" >/dev/null
[ "$(git -C "$d/run/bo" log -1 --format=%H)" = "$(git -C "$d/run/ana" log -1 --format=%H)" ] || { echo "FAIL: clones differ"; exit 1; }
[ "$(git -C "$d/run/ana" config user.name)" = Ana ] || { echo "FAIL: ana user.name"; exit 1; }
[ "$(git -C "$d/run/bo" config user.name)" = Bo ] || { echo "FAIL: bo user.name"; exit 1; }
grep -q "| Bo | Bo |" "$d/run/bo/TEAM.md" || { echo "FAIL: TEAM.md not seeded"; exit 1; }
[ -f "$d/run/bo/.agents/skills/team-build/hooks/team_hook.py" ] || { echo "FAIL: skill not vendored"; exit 1; }
if bash "$here/examples/scripted/seed.sh" "$d/run" >/dev/null 2>&1; then echo "FAIL: reused existing dir"; exit 1; fi
echo "seed_test ok"
