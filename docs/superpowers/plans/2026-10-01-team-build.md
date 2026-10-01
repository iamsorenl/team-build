# team-build Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a public skill + plugin (`iamsorenl/team-build`) that coordinates a multi-person team where each person drives Claude Code or Codex on one repo.

**Architecture:** One Agent Skills folder (`skills/team-build/`), read natively by both Claude Code and Codex, plus plugin manifests for both. Kickoff vendors the skill into the project (`.agents/skills/` + `.claude/skills` symlink) and installs two project hooks that call one Python script. All shared state lives in four repo files: `AGENTS.md`, `DECISIONS.md`, `CONTRACTS.md`, `TEAM.md`.

**Tech Stack:** Markdown skill, Python 3 stdlib (hooks + scripts), bash + `gh` (GitHub profiles), git.

**Spec:** `docs/superpowers/specs/2026-10-01-team-build-design.md`

**Deltas from the spec (found during planning):**
- Claude and Codex accept the same hook output (`systemMessage` + `hookSpecificOutput.additionalContext`), so `team_hook.py` has no `--tool` flag. It takes the mode as an argument instead: `prompt` or `edit`.
- Codex reports file edits as `tool_name: apply_patch` with the patch in `tool_input.command` (`*** Update File: <path>` lines). The matcher `Edit|Write` works in Codex too.
- `sync_check.sh` becomes `sync_check.py` so it can reuse the `TEAM.md` parser. It also has a `--check-team` mode for the overlap refusal.
- New `scripts/install_project.py` does the vendoring, templates and merge-not-overwrite work deterministically.
- The plugin manifests do **not** register hooks. Hooks are installed per project only, so they never fire in the integrator's unrelated repos.

## Global Constraints

- Python 3 standard library only; no pip installs. Target `python3` ≥ 3.9.
- Hooks fail open: any exception exits 0 with no output, and a hook never blocks a tool call (warn only).
- Never overwrite an existing `AGENTS.md`, `CLAUDE.md`, `.claude/settings.json` or `.codex/hooks.json`; merge into them. Invalid existing JSON → abort that file with a message.
- Skill frontmatter has only `name` and `description` (both tools require these; nothing Claude-only).
- Public repo, MIT license, owner `iamsorenl`.
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`.
- Messages to teammates are drafted, never sent.

## Review Focus

1. A teammate whose `git config user.name` doesn't match `TEAM.md` → hooks stay silent (no false warnings). Pinned in Task 2's selftest.
2. Existing project files (`AGENTS.md`, `.claude/settings.json` with the user's own hooks) → merged, with the user's content intact, and running twice adds nothing. Pinned in Task 4's selftest.
3. Codex `apply_patch` with relative paths, multiple files, or a path outside the repo → each in-repo path is checked and outside paths are ignored. Pinned in Task 2.
4. `DECISIONS.md` changes arriving via `git pull` (not edited in-session) → the next prompt gets the reminder once. Pinned in Task 2's e2e selftest.
5. A repo with no remote (local-only hackathon) → `sync_check.py` uses local branches and doesn't crash. Pinned in Task 3's test.

---

### Task 1: Repo scaffold and plugin manifests

**Files:**
- Create: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json`, `LICENSE`, `.gitignore`, `skills/team-build/SKILL.md` (stub, replaced in Task 6)

**Interfaces:**
- Produces: plugin name `team-build`, marketplace name `team-build`, skills root `./skills/`.

- [ ] **Step 1: Write the manifests**

`.claude-plugin/plugin.json`:
```json
{
  "name": "team-build",
  "version": "0.1.0",
  "description": "Keep a team in sync when everyone drives their own Claude Code or Codex agent on one repo (hackathons).",
  "author": { "name": "Soren Larsen", "url": "https://github.com/iamsorenl" },
  "homepage": "https://github.com/iamsorenl/team-build",
  "repository": "https://github.com/iamsorenl/team-build",
  "license": "MIT",
  "keywords": ["team", "hackathon", "coordination", "codex", "multiplayer"],
  "skills": "./skills/"
}
```

`.claude-plugin/marketplace.json`:
```json
{
  "name": "team-build",
  "description": "team-build: coordination for teams of people each using a coding agent.",
  "owner": { "name": "Soren Larsen", "url": "https://github.com/iamsorenl" },
  "plugins": [
    {
      "name": "team-build",
      "description": "Kickoff, sync and wrap-up for multi-person Claude Code / Codex projects.",
      "source": "./"
    }
  ]
}
```

`.codex-plugin/plugin.json`:
```json
{
  "name": "team-build",
  "version": "0.1.0",
  "description": "Keep a team in sync when everyone drives their own Claude Code or Codex agent on one repo (hackathons).",
  "author": { "name": "Soren Larsen", "url": "https://github.com/iamsorenl" },
  "homepage": "https://github.com/iamsorenl/team-build",
  "repository": "https://github.com/iamsorenl/team-build",
  "license": "MIT",
  "keywords": ["team", "hackathon", "coordination", "codex", "multiplayer"],
  "skills": "./skills/",
  "interface": {
    "displayName": "team-build",
    "shortDescription": "Team coordination for multi-agent hackathons",
    "developerName": "Soren Larsen",
    "category": "Productivity",
    "capabilities": ["Instructions"],
    "websiteURL": "https://github.com/iamsorenl/team-build",
    "defaultPrompt": ["We're starting a hackathon with a team, set us up."]
  }
}
```

`.agents/plugins/marketplace.json`:
```json
{
  "name": "team-build",
  "interface": { "displayName": "team-build" },
  "plugins": [
    {
      "name": "team-build",
      "source": { "source": "url", "url": "https://github.com/iamsorenl/team-build.git", "ref": "main" },
      "policy": { "installation": "AVAILABLE", "authentication": "ON_INSTALL" },
      "category": "Productivity"
    }
  ]
}
```

`.gitignore`:
```
__pycache__/
*.pyc
.DS_Store
```

`LICENSE`: standard MIT text, `Copyright (c) 2026 Soren Larsen`.

`skills/team-build/SKILL.md` (stub):
```markdown
---
name: team-build
description: Placeholder, replaced in Task 6.
---
```

- [ ] **Step 2: Validate**

Run: `claude plugin validate "/Users/Soren/Desktop/Active Projects/team-build"`
Expected: no errors. Also run `python3 -m json.tool` on each JSON file; each must parse.

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "Scaffold plugin manifests for Claude Code and Codex"
```

---

### Task 2: `team_hook.py` (both hooks, both tools)

**Files:**
- Create: `skills/team-build/hooks/team_hook.py`

**Interfaces:**
- Produces (imported by Tasks 3 and 4):
  - `git(*args, cwd=None) -> str` (stdout stripped, `""` on failure)
  - `parse_team(text: str) -> list[dict]`, where each dict is `{"name": str, "git": str, "paths": list[str]}`
  - `owns(person: dict, path: str) -> bool`
  - `overlaps(people: list[dict]) -> list[tuple[str, str, str, str]]` (nameA, patA, nameB, patB)
- CLI: `team_hook.py prompt|edit` reads hook JSON on stdin; `team_hook.py --selftest` exits 0 and prints `selftest ok`, or exits non-zero with an AssertionError.

- [ ] **Step 1: Write the selftest first**

Create `team_hook.py` containing only the header, imports and `selftest()` below, plus a `__main__` that calls it:

```python
#!/usr/bin/env python3
"""team-build hook for Claude Code and Codex.

Usage: team_hook.py prompt|edit   (hook JSON on stdin)
       team_hook.py --selftest
Always exits 0 as a hook and prints JSON only when it has something to say.
"""
import fnmatch, hashlib, json, os, re, subprocess, sys, tempfile

WATCHED = ("DECISIONS.md", "CONTRACTS.md")


def selftest():
    team = """# Team
| Name | git user.name | GitHub | Strengths | Role | Slice | Owned paths |
|---|---|---|---|---|---|---|
| Ana | ana | @ana | frontend | builder | UI | `web/`, `.github/` |
| Bo | Bo Smith | | backend | builder | API | `api/*.py`, ./shared/types.ts |
| | | | | | | |
"""
    people = parse_team(team)
    assert [p["name"] for p in people] == ["Ana", "Bo"], people
    assert people[0]["paths"] == ["web/", ".github/"], people[0]
    assert people[1]["paths"] == ["api/*.py", "shared/types.ts"], people[1]
    assert owns(people[0], "web/app.tsx") and owns(people[0], "web/deep/x.ts")
    assert owns(people[1], "api/v1/routes.py")  # fnmatch * crosses folders
    assert not owns(people[0], "webby/x.ts")
    assert overlaps(people) == []
    assert overlaps(people + [{"name": "Cy", "git": "cy", "paths": ["web/app.tsx"]}])

    # edit warnings
    assert edit_warning(people, "ana", ["web/app.tsx"]) is None
    w = edit_warning(people, "ana", ["api/routes.py"])
    assert w and "Bo" in w and "api/routes.py" in w, w
    assert edit_warning(people, "BO SMITH", ["shared/types.ts"]) is None
    assert edit_warning(people, "stranger", ["api/routes.py"]) is None  # unknown user: silent
    assert edit_warning(people, "", ["api/routes.py"]) is None
    assert edit_warning(people, "ana", ["README.md"]) is None  # unowned: silent

    with tempfile.TemporaryDirectory() as d:
        root = os.path.realpath(d)
        patch = ("*** Begin Patch\n*** Update File: api/routes.py\n@@\n-a\n+b\n"
                 "*** Add File: web/new.tsx\n+x\n*** Delete File: ../outside.txt\n*** End Patch")
        assert edited_paths({"tool_input": {"command": patch}, "cwd": root}, root) == ["api/routes.py", "web/new.tsx"]
        assert edited_paths({"tool_input": {"file_path": os.path.join(root, "web/a.tsx")}}, root) == ["web/a.tsx"]
        assert edited_paths({"tool_input": {"file_path": "/etc/hosts"}}, root) == []
        assert edited_paths({}, root) == []

        state = os.path.join(root, "seen")
        assert prompt_reminder(root, state) is None  # no shared files yet
        with open(os.path.join(root, "DECISIONS.md"), "w") as f:
            f.write("v1")
        assert prompt_reminder(root, state)
        assert prompt_reminder(root, state) is None
        with open(os.path.join(root, "CONTRACTS.md"), "w") as f:
            f.write("c1")
        assert prompt_reminder(root, state)

        # end to end through main() in a real git repo
        subprocess.run(["git", "init", "-q", root], check=True)
        subprocess.run(["git", "-C", root, "config", "user.name", "ana"], check=True)
        with open(os.path.join(root, "TEAM.md"), "w") as f:
            f.write(team)
        me = os.path.abspath(__file__)

        def run(mode, payload):
            r = subprocess.run([sys.executable, me, mode], input=json.dumps(payload),
                               capture_output=True, text=True, cwd=root)
            assert r.returncode == 0, r.stderr
            return r.stdout.strip()

        out = run("edit", {"cwd": root, "tool_name": "Edit",
                           "tool_input": {"file_path": os.path.join(root, "api/x.py")}})
        msg = json.loads(out)
        assert msg["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
        assert "Bo" in msg["hookSpecificOutput"]["additionalContext"]
        assert "permissionDecision" not in msg["hookSpecificOutput"]  # warn, never block
        assert run("edit", {"cwd": root, "tool_input": {"file_path": os.path.join(root, "web/x.ts")}}) == ""
        first = run("prompt", {"cwd": root})
        assert json.loads(first)["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
        assert run("prompt", {"cwd": root}) == ""
        with open(os.path.join(root, "DECISIONS.md"), "a") as f:
            f.write("\npulled change")  # simulates a git pull
        assert run("prompt", {"cwd": root}) != ""
        assert run("edit", {"cwd": "/"}) == ""  # not a repo: silent
        run("prompt", "not json")  # non-object stdin must not crash (run asserts exit 0)
    print("selftest ok")
    return 0


if __name__ == "__main__":
    sys.exit(selftest())
```

- [ ] **Step 2: Run it and confirm it fails**

Run: `python3 skills/team-build/hooks/team_hook.py`
Expected: `NameError: name 'parse_team' is not defined`

- [ ] **Step 3: Implement**

Insert these functions above `selftest()` and replace the `__main__` block:

```python
def git(*args, cwd=None):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def _norm(p):
    p = p.strip().strip("`").strip()
    return p[2:] if p.startswith("./") else p


def parse_team(text):
    """Rows of the first markdown table in TEAM.md that has an 'Owned paths' column."""
    people, cols = [], None
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            cols = None
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cols is None:
            cols = [c.lower() for c in cells]
            continue
        if "owned paths" not in cols or all(set(c) <= set("-: ") for c in cells):
            continue
        row = dict(zip(cols, cells))
        paths = [_norm(p) for p in row.get("owned paths", "").split(",")]
        people.append({"name": row.get("name", ""), "git": _norm(row.get("git user.name", "")),
                       "paths": [p for p in paths if p]})
    return people


def owns(person, path):
    return any(fnmatch.fnmatch(path, pat) or path.startswith(pat.rstrip("/") + "/")
               for pat in person["paths"])


def overlaps(people):
    """Pairs of patterns from different people that can match the same file.
    Approximate: compares patterns to each other, not to every possible path."""
    found = []
    for i, a in enumerate(people):
        for b in people[i + 1:]:
            for pa in a["paths"]:
                for pb in b["paths"]:
                    if owns({"paths": [pa]}, pb.rstrip("/")) or owns({"paths": [pb]}, pa.rstrip("/")):
                        found.append((a["name"], pa, b["name"], pb))
    return found


PATCH_RE = re.compile(r"^\*\*\* (?:Update File|Add File|Delete File|Move to): (.+)$", re.M)


def edited_paths(payload, root):
    """Repo-relative paths a tool call will write. Claude: tool_input.file_path. Codex: apply_patch body."""
    ti = payload.get("tool_input") or {}
    if not isinstance(ti, dict):
        return []
    raw = [ti["file_path"]] if ti.get("file_path") else PATCH_RE.findall(ti.get("command") or "")
    base, root = payload.get("cwd") or root, os.path.realpath(root)
    out = []
    for p in raw:
        rel = os.path.relpath(os.path.realpath(os.path.join(base, p.strip())), root)
        if rel != ".." and not rel.startswith(".." + os.sep):
            out.append(rel)
    return out


def edit_warning(people, me, paths):
    mine = [p for p in people if me and p["git"].lower() == me.lower()]
    if not mine:
        return None
    notes = []
    for path in paths:
        if any(owns(m, path) for m in mine):
            continue
        owners = [p["name"] for p in people if p not in mine and owns(p, path)]
        if owners:
            notes.append(f"{path} belongs to {', '.join(owners)}")
    if not notes:
        return None
    return ("team-build: " + "; ".join(notes) + ". That is outside your slice in TEAM.md. "
            "Check with the owner before changing it, or tell your human.")


def decisions_hash(root):
    h, found = hashlib.sha256(), False
    for name in WATCHED:
        f = os.path.join(root, name)
        if os.path.isfile(f):
            found = True
            with open(f, "rb") as fh:
                h.update(name.encode() + b"\0" + fh.read())
    return h.hexdigest() if found else None


def prompt_reminder(root, state_file):
    cur = decisions_hash(root)
    if cur is None:
        return None
    try:
        with open(state_file) as fh:
            old = fh.read().strip()
    except OSError:
        old = ""
    if cur == old:
        return None
    with open(state_file, "w") as fh:
        fh.write(cur)
    return ("team-build: DECISIONS.md or CONTRACTS.md changed since you last saw them. "
            "Re-read both before planning or editing.")


def format_output(event, msg):
    return json.dumps({"systemMessage": msg,
                       "hookSpecificOutput": {"hookEventName": event, "additionalContext": msg}})


def main(argv):
    mode = argv[1] if len(argv) > 1 else ""
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    root = git("rev-parse", "--show-toplevel", cwd=payload.get("cwd") or None)
    if not root:
        return 0
    if mode == "prompt":
        state = os.path.join(git("rev-parse", "--absolute-git-dir", cwd=root), "team-build-seen")
        msg, event = prompt_reminder(root, state), "UserPromptSubmit"
    elif mode == "edit":
        try:
            with open(os.path.join(root, "TEAM.md")) as fh:
                people = parse_team(fh.read())
        except OSError:
            return 0
        msg = edit_warning(people, git("config", "user.name", cwd=root), edited_paths(payload, root))
        event = "PreToolUse"
    else:
        return 0
    if msg:
        print(format_output(event, msg))
    return 0
```

```python
if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        sys.exit(selftest())
    try:
        sys.exit(main(sys.argv))
    except Exception:
        sys.exit(0)
```

Note: `cwd` that isn't a directory makes `subprocess.run` raise, and the outer `except` turns that into a silent exit 0. That's the intended fail-open.

- [ ] **Step 4: Run the selftest**

Run: `python3 skills/team-build/hooks/team_hook.py --selftest`
Expected: `selftest ok`

- [ ] **Step 5: Commit**

```bash
git add skills/team-build/hooks/team_hook.py && git commit -m "Add team_hook.py: decisions reminder + ownership warning for Claude and Codex"
```

---

### Task 3: `sync_check.py`

**Files:**
- Create: `skills/team-build/scripts/sync_check.py`, `tests/sync_check_test.sh`

**Interfaces:**
- Consumes: `git`, `parse_team`, `owns`, `overlaps` from `skills/team-build/hooks/team_hook.py`.
- CLI: `sync_check.py [--base main] [--no-fetch]` prints one line per unmerged branch, `<branch> (<author>): ok` or a `; `-joined list of flags. `sync_check.py --check-team` prints overlaps and exits 1 if there are any, else prints `TEAM.md ok` and exits 0.

- [ ] **Step 1: Write the failing test**

`tests/sync_check_test.sh`:
```bash
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
echo z > web/b.ts; git add -A; git commit -qm "main moves"
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
```

- [ ] **Step 2: Run it and confirm it fails**

Run: `bash tests/sync_check_test.sh`
Expected: fails with python `can't open file ... sync_check.py`.

- [ ] **Step 3: Implement `sync_check.py`**

```python
#!/usr/bin/env python3
"""Per-branch sync report for a team-build repo.

Usage: sync_check.py [--base main] [--no-fetch]
       sync_check.py --check-team   (exit 1 if owned paths overlap)
"""
import os, sys, time

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
    remote = bool(git("remote", cwd=root))
    if remote and "--no-fetch" not in argv:
        git("fetch", "--prune", "--quiet", cwd=root)
    ns, base_ref = ("refs/remotes/origin", f"origin/{base}") if remote else ("refs/heads", base)
    branches = [b for b in git("for-each-ref", "--format=%(refname:short)", ns, cwd=root).splitlines()
                if b not in (base_ref, "origin/HEAD", "origin")]
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
```

- [ ] **Step 4: Run the test**

Run: `bash tests/sync_check_test.sh`
Expected: last line `sync_check_test ok`

- [ ] **Step 5: Commit**

```bash
git add skills/team-build/scripts/sync_check.py tests/sync_check_test.sh && git commit -m "Add sync_check.py: per-branch drift report and TEAM.md overlap check"
```

---

### Task 4: Templates, hook configs, `install_project.py`

**Files:**
- Create: `skills/team-build/templates/AGENTS.md`, `templates/DECISIONS.md`, `templates/CONTRACTS.md`, `templates/TEAM.md`, `skills/team-build/hooks/claude-settings.json`, `skills/team-build/hooks/codex-hooks.json`, `skills/team-build/scripts/install_project.py`

**Interfaces:**
- CLI: `install_project.py [project_root]` (default: `git rev-parse --show-toplevel` of the cwd) prints one line per action; `install_project.py --selftest` prints `selftest ok`.
- Produces in the project: `.agents/skills/team-build/` (copy), `.claude/skills/team-build` (symlink → `../../.agents/skills/team-build`), the four templates if absent, rules merged into `AGENTS.md`, `@AGENTS.md` in `CLAUDE.md`, and hooks merged into `.claude/settings.json` and `.codex/hooks.json`.
- Hook command (both tools): `python3 "$(git rev-parse --show-toplevel)/.agents/skills/team-build/hooks/team_hook.py" <mode> 2>/dev/null || true`

- [ ] **Step 1: Write the templates**

`templates/AGENTS.md`:
```markdown
<!-- team-build -->
## Team rules (team-build)

Several people are building this repo at the same time, each with their own coding agent. These rules keep anyone's work from getting thrown away.

1. Before planning any task, read DECISIONS.md and CONTRACTS.md. They change during the event.
2. Edit only files inside your person's owned paths in TEAM.md. If a task needs a file someone else owns, stop and tell your human who owns it.
3. Never change a contract quietly. Only its owner edits CONTRACTS.md, logs the change in DECISIONS.md, and tells the people who use it.
4. If you learn something that changes the plan (an API doesn't work, a library can't do X, a data shape has to change), add it to DECISIONS.md and tell your human before continuing.
5. Plan only the current task and keep the plan short. The bigger plan will change.
6. Branch from the latest main. Merge small and often, at least every 30 to 60 minutes.
7. If the team-build skill is available, use it for discoveries, contract changes, and sync checks.
```

`templates/DECISIONS.md`:
```markdown
# Decisions

Append-only, newest at the bottom. Every agent reads this before planning.

Entry format:

## HH:MM - one-line decision
- By: name
- What changed: what we now know or decided
- Affects: slices, people, contracts
```

`templates/CONTRACTS.md`:
````markdown
# Contracts

Interfaces between slices. Only a contract's owner changes it, and every change gets logged in DECISIONS.md.

## Example: GET /api/tasks
- Owner: name
- Used by: names
- Request: `GET /api/tasks`
- Success (200):
```json
{ "items": [{ "id": "task-1", "title": "Demo task", "assignee": null, "status": "todo" }] }
```
- Empty (200): `{ "items": [] }`
- Error (400): `{ "error": { "code": "INVALID_QUERY", "message": "..." } }`
````

`templates/TEAM.md`:
```markdown
# Team

- Goal:
- Ends at:
- Integrator:

| Name | git user.name | GitHub | Strengths | Role | Slice | Owned paths |
|---|---|---|---|---|---|---|
| | | | | | | |

Owned paths are comma-separated. A folder like `web/` covers everything under it, and `*` globs work (they match across folders). Paths must not overlap between people. Check with `sync_check.py --check-team`.
```

- [ ] **Step 2: Write the hook configs**

`hooks/claude-settings.json`:
```json
{
  "hooks": {
    "UserPromptSubmit": [
      { "hooks": [ { "type": "command", "timeout": 5,
        "command": "python3 \"$(git rev-parse --show-toplevel)/.agents/skills/team-build/hooks/team_hook.py\" prompt 2>/dev/null || true" } ] }
    ],
    "PreToolUse": [
      { "matcher": "Edit|Write|MultiEdit", "hooks": [ { "type": "command", "timeout": 5,
        "command": "python3 \"$(git rev-parse --show-toplevel)/.agents/skills/team-build/hooks/team_hook.py\" edit 2>/dev/null || true" } ] }
    ]
  }
}
```

`hooks/codex-hooks.json`: same JSON, except the `PreToolUse` matcher is `"apply_patch|Edit|Write"` and each handler has `"statusMessage": "team-build check"`.

- [ ] **Step 3: Write `install_project.py` with its selftest**

```python
#!/usr/bin/env python3
"""Install team-build into a project repo without overwriting anything.

Usage: install_project.py [project_root]
       install_project.py --selftest
"""
import json, os, shutil, subprocess, sys, tempfile

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARK = "<!-- team-build -->"


def read(path):
    try:
        with open(path) as fh:
            return fh.read()
    except OSError:
        return None


def write(path, text):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as fh:
        fh.write(text)


def merge_hooks(target, snippet_path, log):
    current = read(target)
    try:
        data = json.loads(current) if current else {}
    except ValueError:
        log(f"SKIPPED {target}: existing file is not valid JSON; add the hooks from {snippet_path} by hand")
        return
    with open(snippet_path) as fh:
        snippet = json.load(fh)
    added = 0
    for event, entries in snippet["hooks"].items():
        lst = data.setdefault("hooks", {}).setdefault(event, [])
        if not any("team_hook.py" in json.dumps(e) for e in lst):
            lst.extend(entries)
            added += 1
    if added:
        write(target, json.dumps(data, indent=2) + "\n")
    log(f"{'merged hooks into' if added else 'hooks already in'} {target}")


def install(root, log=print):
    vendored = os.path.join(root, ".agents", "skills", "team-build")
    if os.path.realpath(vendored) != os.path.realpath(SKILL_DIR):
        shutil.copytree(SKILL_DIR, vendored, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        log(f"copied skill to {vendored}")
    link = os.path.join(root, ".claude", "skills", "team-build")
    if not os.path.lexists(link):
        os.makedirs(os.path.dirname(link), exist_ok=True)
        os.symlink(os.path.join("..", "..", ".agents", "skills", "team-build"), link)
        log(f"linked {link}")
    tpl = os.path.join(SKILL_DIR, "templates")
    for name in ("DECISIONS.md", "CONTRACTS.md", "TEAM.md"):
        if read(os.path.join(root, name)) is None:
            shutil.copy(os.path.join(tpl, name), os.path.join(root, name))
            log(f"created {name}")
    rules = read(os.path.join(tpl, "AGENTS.md"))
    agents = read(os.path.join(root, "AGENTS.md"))
    if agents is None:
        write(os.path.join(root, "AGENTS.md"), rules)
        log("created AGENTS.md")
    elif MARK not in agents:
        write(os.path.join(root, "AGENTS.md"), agents.rstrip() + "\n\n" + rules)
        log("appended team rules to AGENTS.md")
    claude = read(os.path.join(root, "CLAUDE.md"))
    if claude is None:
        write(os.path.join(root, "CLAUDE.md"), "@AGENTS.md\n")
        log("created CLAUDE.md")
    elif "@AGENTS.md" not in claude:
        write(os.path.join(root, "CLAUDE.md"), claude.rstrip() + "\n\n@AGENTS.md\n")
        log("added @AGENTS.md to CLAUDE.md")
    hooks = os.path.join(SKILL_DIR, "hooks")
    merge_hooks(os.path.join(root, ".claude", "settings.json"), os.path.join(hooks, "claude-settings.json"), log)
    merge_hooks(os.path.join(root, ".codex", "hooks.json"), os.path.join(hooks, "codex-hooks.json"), log)


def selftest():
    with tempfile.TemporaryDirectory() as d:
        root = os.path.realpath(d)
        write(os.path.join(root, "AGENTS.md"), "# Existing rules\nKeep tests green.\n")
        own_hook = {"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "mine.sh"}]}]}}
        write(os.path.join(root, ".claude", "settings.json"), json.dumps(own_hook))
        write(os.path.join(root, ".codex", "hooks.json"), "{not json")
        lines = []
        install(root, lines.append)
        install(root, lines.append)  # idempotent
        agents = read(os.path.join(root, "AGENTS.md"))
        assert agents.startswith("# Existing rules") and agents.count(MARK) == 1, agents
        assert read(os.path.join(root, "CLAUDE.md")) == "@AGENTS.md\n"
        s = json.loads(read(os.path.join(root, ".claude", "settings.json")))
        assert "mine.sh" in json.dumps(s["hooks"]["PreToolUse"])
        assert json.dumps(s).count("team_hook.py") == 2, s  # one prompt + one edit, not doubled
        assert read(os.path.join(root, ".codex", "hooks.json")) == "{not json"  # untouched
        assert any(l.startswith("SKIPPED") for l in lines)
        assert os.path.isfile(os.path.join(root, ".claude", "skills", "team-build", "SKILL.md"))
        assert os.path.isfile(os.path.join(root, ".agents", "skills", "team-build", "hooks", "team_hook.py"))
        for name in ("DECISIONS.md", "CONTRACTS.md", "TEAM.md"):
            assert read(os.path.join(root, name))
    print("selftest ok")
    return 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        sys.exit(selftest())
    target = sys.argv[1] if len(sys.argv) > 1 else subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
    if not target:
        print("Run this inside the project's git repo, or pass its path.")
        sys.exit(1)
    install(os.path.realpath(target))
```

- [ ] **Step 4: Run the selftest and confirm it passes**

Run: `python3 skills/team-build/scripts/install_project.py --selftest`
Expected: `selftest ok`. If you wrote the selftest before `install()`, first confirm it fails with `NameError`.

- [ ] **Step 5: Commit**

```bash
git add skills/team-build && git commit -m "Add templates, hook configs and install_project.py (merge, never overwrite)"
```

---

### Task 5: `github_profile.sh`

**Files:**
- Create: `skills/team-build/scripts/github_profile.sh`

**Interfaces:**
- CLI: `github_profile.sh <handle>` (leading `@` allowed) prints a short profile. It always exits 0 and prints a `skip` line if `gh` is missing or the user isn't found.

- [ ] **Step 1: Write it**

```bash
#!/usr/bin/env bash
# Public GitHub summary for writing a one-line "good at" note. Always exits 0.
set -uo pipefail
h="${1#@}"
[ -n "$h" ] || { echo "usage: github_profile.sh <handle>"; exit 0; }
command -v gh >/dev/null || { echo "skip: gh not installed"; exit 0; }
gh api "users/$h" --jq '"\(.login) | \(.name // "") | \(.bio // "no bio") | \(.public_repos) public repos"' 2>/dev/null \
  || { echo "skip: GitHub user $h not found or gh not logged in"; exit 0; }
echo "Languages (recent non-fork repos):"
gh api "users/$h/repos?sort=pushed&per_page=30" \
  --jq '[.[] | select(.fork | not) | .language // empty] | group_by(.) | sort_by(-length) | map("\(.[0]) \(length)") | join(", ")'
echo "Recent repos:"
gh api "users/$h/repos?sort=pushed&per_page=30" \
  --jq '[.[] | select(.fork | not)][:10][] | "- \(.name): \(.description // "") [\(.language // "?")] \(.topics | join(","))"'
```

- [ ] **Step 2: Try it**

Run: `bash skills/team-build/scripts/github_profile.sh iamsorenl` → expect a profile line, languages, up to 10 repos.
Run: `bash skills/team-build/scripts/github_profile.sh this-user-does-not-exist-zz9` → expect a `skip:` line, exit 0.

- [ ] **Step 3: Commit**

```bash
git add skills/team-build/scripts/github_profile.sh && git commit -m "Add github_profile.sh for optional teammate strengths"
```

---

### Task 6: `SKILL.md` and `README.md`

**Files:**
- Modify: `skills/team-build/SKILL.md` (replace the stub)
- Create: `README.md`

- [ ] **Step 1: Write `SKILL.md`**

````markdown
---
name: team-build
description: Keep a team in sync when several people each drive their own coding agent (Claude Code or Codex) on one project, such as a hackathon. Use when the user says they're building something with a team or friends, starting a hackathon, "split this up between us", "we're all working on the same repo", "set up the team". Also use in a repo that has DECISIONS.md and TEAM.md when someone reports a discovery ("we found", "turns out", "X doesn't work"), wants to change an API or data contract, asks for a sync or merge check, adds or reassigns a teammate, or says wrap up, demo, or code freeze.
---

# team-build

Goal: nobody on the team restarts work because of a change they didn't hear about.

Shared state lives in repo files every agent reads: `AGENTS.md` (rules), `DECISIONS.md` (log), `CONTRACTS.md` (interfaces), `TEAM.md` (people, slices, owned paths). `SKILL_DIR` means the folder this file is in.

## Pick the phase

- No `DECISIONS.md` at the repo root → **Kickoff**.
- The user mentions wrap up, demo, freeze or "we're done" → **Wrap**.
- Otherwise → **During**. Pick the sub-action from what they said; if unclear, ask which one.

## Kickoff

This runs at the start of an event, so keep it quick. Ask one thing at a time.

1. Ask: "What are we building, and how long do we have?"
2. Ask: "Who's on the team? For each person, any of: name, GitHub handle, what they're good at, their `git config user.name`. All optional."
   - Handle given: run `bash SKILL_DIR/scripts/github_profile.sh <handle>`, write a one-line strengths summary from it, and show it so they can correct it.
   - Nothing given: call them `Teammate N` with blank strengths.
   - No git user.name: put `?` in TEAM.md. Ownership warnings skip that person until it's filled in; the paste message asks them for it.
3. The integrator defaults to the person running this. Confirm in one line.
4. **Spikes.** List the open technical questions (unknown APIs, model speed, library fit, deploy target). Give one to each non-integrator, matched to strengths. Each spike gets the question, a timebox (30 minutes or about 10% of the event, whichever is shorter), and a note that the answer goes in DECISIONS.md.
5. **Walking skeleton.** You and the integrator build it now: folder layout, one end-to-end path with mock data, nothing more. Discoveries from spikes land before the work is split. If a spike changes the skeleton, update it before teammates start their slices.
6. **Contracts.** Write `CONTRACTS.md` for each interface in the skeleton: owner, users, request, success/empty/error examples.
7. **Slices.** Split the remaining work into vertical slices with owned paths that don't overlap. Assign by strengths where known, otherwise by need. The integrator owns shared files (layout, config, CONTRACTS.md).
8. From the repo root, run `python3 SKILL_DIR/scripts/install_project.py`. Fill in `TEAM.md`, then run `python3 SKILL_DIR/scripts/sync_check.py --check-team` and fix any overlaps it reports. Add the first DECISIONS.md entry (goal, end time, integrator, spikes).
9. Commit on main (`team-build kickoff`) and push if there's a remote.
10. Print this for the user to paste into the group chat (fill every `<>`):

```
We're building: <goal> (until <end time>)
Repo: <url>
Integrator: <name> (owns main and merges)

Step 1, spikes (≤<N> min, put answers in DECISIONS.md):
- <name>: <question>

Step 2, slices (only edit your own paths):
- <name>: <slice> - <paths>

Setup: clone the repo and open your agent in it. It reads AGENTS.md automatically.
Set your git name to match TEAM.md: git config user.name "<git user.name>"
Codex users: run /hooks once and trust the two team-build hooks.
```

## During

### Discovery ("we found", "turns out", "X doesn't work")
1. Append to DECISIONS.md using its entry format. Fill in "Affects" from TEAM.md slices and CONTRACTS.md users.
2. `git pull --rebase`, commit only DECISIONS.md, and push to main straight away. If they can't push to main, tell them to send it to the integrator.
3. Draft a heads-up naming the affected people and what they should do differently.

### Contract change
1. Check the owner in CONTRACTS.md against the user's `git config user.name` and TEAM.md. If the user isn't the owner, draft a request to the owner and stop.
2. Edit the contract and its examples, log it in DECISIONS.md, commit, and push.
3. Draft a heads-up to everyone in "Used by", listing exact field changes.

### Sync or merge check
Run `python3 SKILL_DIR/scripts/sync_check.py` and turn the output into a short action list per person: who should pull main, who should merge now, who touched someone else's files.

### Add or reassign a teammate
Update TEAM.md, run `sync_check.py --check-team`, log it in DECISIONS.md, and commit.

## Wrap

1. **Integration check.** Find the start and test commands (package.json scripts, Makefile, pyproject); ask if unclear. Run the tests. Start the app and call each CONTRACTS.md interface, comparing field names and types to the examples. Report mismatches with the owner's name.
2. **Freeze.** Log it in DECISIONS.md and draft: "Merge everything by <time>. After that only <integrator> commits."
3. **Demo script** (3 to 5 minutes): the problem, the live demo path, who built what (from TEAM.md), the key decisions (from DECISIONS.md), what's next.

## Rules for you

- Draft messages; never send them.
- Never overwrite AGENTS.md, CLAUDE.md or hook settings by hand; install_project.py merges them.
- Keep DECISIONS.md entries to a few lines. People read them in a hurry.
````

- [ ] **Step 2: Write `README.md`**

The README covers:
1. One paragraph on the problem, citing CooperBench and "When Agents Coordinate" with links.
2. The playbook (the 9 points from the brainstorm, short).
3. Install:
   - Claude Code: `/plugin marketplace add iamsorenl/team-build` then `/plugin install team-build@team-build`
   - Codex: `codex plugin marketplace add iamsorenl/team-build` then `codex plugin add team-build@team-build`
   - Manual: copy `skills/team-build` into `~/.claude/skills/` or `~/.agents/skills/`
4. "Your teammates don't install anything": kickoff vendors the skill into the project.
5. What kickoff adds to a project (the file table from the spec).
6. Hooks: what the two hooks do, that they only warn, that Codex needs `/hooks` trust, and that Codex project config only loads for trusted projects.
7. Known limits: overlap check is pattern-vs-pattern (approximate); Codex users who skip hook trust only get the AGENTS.md rules; if the integrator has the plugin and the vendored copy, both show up in the skill list.
8. Tests: `python3 skills/team-build/hooks/team_hook.py --selftest`, `python3 skills/team-build/scripts/install_project.py --selftest`, `bash tests/sync_check_test.sh`.
9. License: MIT.

- [ ] **Step 3: Validate and run all tests**

Run: `claude plugin validate "/Users/Soren/Desktop/Active Projects/team-build"` and all three test commands above.
Expected: validate clean; `selftest ok`, `selftest ok`, `sync_check_test ok`.

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "Write SKILL.md phases and README"
```

---

### Task 7: End-to-end dry run

**Files:** none in this repo (scratch repo in the session scratchpad). Fix anything that breaks back in this repo, with a commit per fix.

- [ ] **Step 1: Claude Code kickoff dry run.** Create a scratch git repo. Run `claude -p` there with `--plugin-dir "/Users/Soren/Desktop/Active Projects/team-build"`, giving it: "We're doing a 6-hour hackathon building a shared task board. Team: me (iamsorenl), Ana (good at frontend, git name ana), and a third person, no info." Answer follow-ups in the prompt up front so it runs non-interactively. Check that DECISIONS.md, CONTRACTS.md, TEAM.md (3 rows, `Teammate 3`), the AGENTS.md rules, `@AGENTS.md` in CLAUDE.md, both hook files, the vendored skill and symlink, and the paste message all exist.
- [ ] **Step 2: Hooks live in Claude.** In the scratch repo, set `git config user.name ana`, then run `claude -p "add a line to <a file owned by someone else>"` and confirm the transcript shows the team-build warning and the edit still goes through. Append to DECISIONS.md, run another prompt, and confirm the reminder appears once.
- [ ] **Step 3: During and wrap phases.** Run `claude -p` with "turns out the API has to return due dates too" → DECISIONS.md entry + heads-up draft. Run with "sync check" → sync_check output summarized. Run with "wrap up" → freeze message + demo script.
- [ ] **Step 4: Codex.** Codex isn't installed on this machine. **Ask Soren** before installing it (`npm i -g @openai/codex`, needs his OpenAI login). If approved: open the scratch repo in Codex, confirm `team-build` appears in skills, run `/hooks`, trust both, and repeat Step 2's ownership check with an `apply_patch` edit. If not approved, record "Codex untested" in the README's Known limits.
- [ ] **Step 5: Commit any fixes**, one commit per fix.

---

### Task 8: Publish and wire up

- [ ] **Step 1: Create the public repo and push.** `gh repo create iamsorenl/team-build --public --source "/Users/Soren/Desktop/Active Projects/team-build" --push --description "Keep a team in sync when everyone drives their own Claude Code or Codex agent (hackathons)."`
- [ ] **Step 2: Install for Soren.** `claude plugin marketplace add iamsorenl/team-build` and `claude plugin install team-build@team-build`. Confirm with `claude plugin list`.
- [ ] **Step 3: Routing row.** Add to the Skill routing table in `~/.claude/CLAUDE.md`:
  `| "hackathon with", "team project", "we're all building", "split this up between us", "set up the team" | team-build |`
- [ ] **Step 4: Memory.** Update `~/.claude/projects/-Users-Soren/memory/project_team_build.md` with the repo URL, install commands, Codex tested/untested, and the date.
- [ ] **Step 5: Verify the GitHub install path** in a fresh scratch repo: run kickoff through the installed plugin (not `--plugin-dir`) and confirm `install_project.py` resolves `SKILL_DIR` inside the plugin cache and vendors correctly.
