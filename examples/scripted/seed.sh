#!/usr/bin/env bash
# Builds the starting state for the scripted scenario: a bare remote plus two clones,
# ana/ (git user.name Ana, owns web/) and bo/ (git user.name Bo, owns api/).
# Usage: seed.sh <new-dir>
set -euo pipefail
[ $# -eq 1 ] || { echo "usage: seed.sh <new-dir>"; exit 1; }
dir="$1"
[ -e "$dir" ] && { echo "$dir already exists; pick a new directory so the run starts clean"; exit 1; }
installer="$(cd "$(dirname "$0")/../.." && pwd)/skills/team-build/scripts/install_project.py"

mkdir -p "$dir"; dir="$(cd "$dir" && pwd)"
git init -q --bare -b main "$dir/remote.git"
git clone -q "$dir/remote.git" "$dir/ana" 2>/dev/null
cd "$dir/ana"
git checkout -q -b main 2>/dev/null || true
git config user.name Ana; git config user.email ana@example.com
python3 "$installer" "$dir/ana" >/dev/null

cat > TEAM.md <<'EOF'
# Team

- Goal: weather dashboard (web page + forecast API)
- Ends at: end of the scripted run
- Integrator: Ana

| Name | git user.name | GitHub | Strengths | Role | Slice | Owned paths |
|---|---|---|---|---|---|---|
| Ana | Ana | | frontend | integrator | dashboard page | web/ |
| Bo | Bo | | backend | builder | forecast API | api/ |
EOF

cat >> CONTRACTS.md <<'EOF'

## GET /forecast
- Owner: Bo
- Used by: Ana
- Request: `GET /forecast?city=santa-cruz`
- Success (200):
```json
{ "city": "santa-cruz", "hours": [{ "time": "2026-10-29T09:00", "temp_c": 14 }] }
```
- Empty (200): `{ "city": "santa-cruz", "hours": [] }`
- Error (400): `{ "error": { "code": "UNKNOWN_CITY", "message": "..." } }`
EOF

mkdir -p web api
echo "# dashboard page goes here" > web/README.md
echo "# forecast API goes here" > api/README.md
git add -A; git commit -qm "seed: team-build scripted scenario"
git push -q -u origin main 2>/dev/null

git clone -q "$dir/remote.git" "$dir/bo" 2>/dev/null
git -C "$dir/bo" config user.name Bo; git -C "$dir/bo" config user.email bo@example.com
echo "seeded $dir: remote.git, ana/ (Ana), bo/ (Bo)"
