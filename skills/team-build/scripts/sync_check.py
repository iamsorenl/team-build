#!/usr/bin/env python3
"""Per-branch sync report for a team-build repo.

Usage: sync_check.py [--base main] [--no-fetch]
       sync_check.py --check-team   (exit 1 if owned paths overlap)
"""
import os, sys, time

sys.dont_write_bytecode = True  # the skill is vendored into projects; don't leave .pyc files to get committed
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "hooks"))
from team_hook import git, owns, overlaps, parse_team  # noqa: E402


def load_people(root):
    try:
        with open(os.path.join(root, "TEAM.md")) as fh:
            return parse_team(fh.read())
    except OSError:
        return []


def branch_report(root, base, branch, people, now):
    times = git("log", "--format=%ct", f"{base}..{branch}", cwd=root).split()
    if not times:
        return None  # nothing unmerged
    behind = int(git("rev-list", "--count", f"{branch}..{base}", cwd=root) or 0)
    authors = git("log", "--format=%an", f"{base}..{branch}", cwd=root).splitlines()
    author = max(set(authors), key=authors.count)
    person = next((p for p in people if p["git"].lower() == author.lower()), None)
    files = git("diff", "--name-only", f"{base}...{branch}", cwd=root).splitlines()
    foreign = [f for f in files if person and not owns(person, f)
               and any(owns(p, f) for p in people if p is not person)]
    return {"author": author, "behind": behind, "age_min": (now - int(times[-1])) // 60, "foreign": foreign}


def main(argv):
    root = git("rev-parse", "--show-toplevel")
    if not root:
        print("Not inside a git repo.")
        return 1
    people = load_people(root)
    if "--check-team" in argv:
        bad = overlaps(people)
        for a, pa, b, pb in bad:
            print(f"Overlap: {a} `{pa}` and {b} `{pb}`")
        if not bad:
            print("TEAM.md ok")
        return 1 if bad else 0
    base = argv[argv.index("--base") + 1] if "--base" in argv else "main"
    remote = (git("remote", cwd=root).splitlines() or [""])[0]
    if remote and "--no-fetch" not in argv:
        git("fetch", "--prune", "--quiet", cwd=root)
    ns, base_ref = (f"refs/remotes/{remote}", f"{remote}/{base}") if remote else ("refs/heads", base)
    if not git("rev-parse", "--verify", "--quiet", base_ref, cwd=root):
        print(f"Base branch {base_ref} not found. Pass --base <name> (e.g. --base master).")
        return 1
    branches = [b for b in git("for-each-ref", "--format=%(refname:short)", ns, cwd=root).splitlines()
                if b not in (base_ref, f"{remote}/HEAD", remote)]
    now = int(time.time())
    for b in branches:
        r = branch_report(root, base_ref, b, people, now)
        if r is None:
            continue
        flags = []
        if r["behind"]:
            flags.append(f"{r['behind']} commits behind {base_ref}, pull main into it")
        if r["age_min"] > 60:
            flags.append(f"oldest unmerged commit is {r['age_min']} min old, merge soon")
        if r["foreign"]:
            flags.append("touches other slices: " + ", ".join(r["foreign"]))
        print(f"{b} ({r['author']}): " + ("; ".join(flags) if flags else "ok"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
