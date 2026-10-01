#!/usr/bin/env bash
# Builds a throwaway local repo (no remote) and checks sync_check.py output.
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"
script="$here/skills/team-build/scripts/sync_check.py"
d="$(mktemp -d)"; trap 'rm -rf "$d"' EXIT
rm -rf "$here/skills/team-build/hooks/__pycache__"
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

# missing base branch must be an error, not a silent "all clear"
if out2="$(python3 "$script" --no-fetch --base master)"; then echo "FAIL: missing base exited 0"; exit 1; fi
echo "$out2" | grep -q "master not found" || { echo "FAIL: missing base message: $out2"; exit 1; }
# remote not named origin
git init -q --bare "$d/remote.git"; git remote add upstream "$d/remote.git"; git push -q upstream main bo-api 2>/dev/null
out3="$(python3 "$script" --no-fetch)"
echo "$out3" | grep -q "upstream/bo-api (bo)" || { echo "FAIL: upstream remote: $out3"; exit 1; }
python3 "$script" --check-team | grep -q "TEAM.md ok" || { echo "FAIL: clean team"; exit 1; }
echo "| Cy | cy | web/x.ts |" >> TEAM.md
if python3 "$script" --check-team; then echo "FAIL: overlap not caught"; exit 1; fi
[ -d "$here/skills/team-build/hooks/__pycache__" ] && { echo "FAIL: sync_check left __pycache__ in the skill (gets committed into projects)"; exit 1; }
echo "sync_check_test ok"
