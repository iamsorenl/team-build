#!/usr/bin/env bash
# Builds a throwaway local repo (no remote) and checks sync_check.py output.
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"
script="$here/skills/team-build/scripts/sync_check.py"
d="$(mktemp -d)"; trap 'rm -rf "$d"' EXIT
cd "$d"
git init -q -b main
git config user.name ana; git config user.email a@x
cat > TEAM.md <<'EOF'
| Name | git user.name | Owned paths |
|---|---|---|
| Ana | ana | web/ |
| Bo | bo | api/ |
EOF
git add -A; git commit -qm init
git checkout -qb bo-api
git config user.name bo
mkdir -p api web; echo x > api/a.py; echo y > web/hack.ts
git add -A
GIT_COMMITTER_DATE="$(date -v-2H +%s 2>/dev/null || date -d '-2 hours' +%s) +0000" git commit -qm "bo work"
git checkout -q main; git config user.name ana
mkdir -p web; echo z > web/b.ts; git add -A; git commit -qm "main moves"
git checkout -qb merged-already; git checkout -q main

out="$(python3 "$script" --no-fetch)"
echo "$out"
echo "$out" | grep -q "bo-api (bo)"            || { echo "FAIL: branch line"; exit 1; }
echo "$out" | grep -q "1 commits behind main"  || { echo "FAIL: behind"; exit 1; }
echo "$out" | grep -q "min old"                || { echo "FAIL: age"; exit 1; }
echo "$out" | grep -q "web/hack.ts"            || { echo "FAIL: foreign file"; exit 1; }
echo "$out" | grep -q "merged-already"         && { echo "FAIL: merged branch listed"; exit 1; }

python3 "$script" --check-team | grep -q "TEAM.md ok" || { echo "FAIL: clean team"; exit 1; }
echo "| Cy | cy | web/x.ts |" >> TEAM.md
if python3 "$script" --check-team; then echo "FAIL: overlap not caught"; exit 1; fi
echo "sync_check_test ok"
