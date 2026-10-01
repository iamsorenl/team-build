#!/usr/bin/env bash
# Public GitHub summary for writing a one-line "good at" note. Always exits 0.
set -uo pipefail
h="${1#@}"
[ -n "$h" ] || { echo "usage: github_profile.sh <handle>"; exit 0; }
command -v gh >/dev/null || { echo "skip: gh not installed"; exit 0; }
profile="$(gh api "users/$h" --jq '"\(.login) | \(.name // "") | \(.bio // "no bio") | \(.public_repos) public repos"' 2>/dev/null)" \
  || { echo "skip: GitHub user $h not found or gh not logged in"; exit 0; }
echo "$profile"
echo "Languages (recent non-fork repos):"
gh api "users/$h/repos?sort=pushed&per_page=30" \
  --jq '[.[] | select(.fork | not) | .language // empty] | group_by(.) | sort_by(-length) | map("\(.[0]) \(length)") | join(", ")'
echo "Recent repos:"
gh api "users/$h/repos?sort=pushed&per_page=30" \
  --jq '[.[] | select(.fork | not)][:10][] | "- \(.name): \(.description // "") [\(.language // "?")] \(.topics | join(","))"'
