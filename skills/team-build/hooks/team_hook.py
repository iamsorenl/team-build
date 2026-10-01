#!/usr/bin/env python3
"""team-build hook for Claude Code and Codex.

Usage: team_hook.py prompt|edit   (hook JSON on stdin)
       team_hook.py --selftest
Always exits 0 as a hook and prints JSON only when it has something to say.
"""
import fnmatch, hashlib, json, os, re, subprocess, sys, tempfile

WATCHED = ("DECISIONS.md", "CONTRACTS.md")


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
        if path in WATCHED or any(owns(m, path) for m in mine):
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
    shared_owner = people + [{"name": "Sam", "git": "sam", "paths": ["DECISIONS.md", "CONTRACTS.md"]}]
    assert edit_warning(shared_owner, "ana", ["DECISIONS.md", "CONTRACTS.md"]) is None  # shared logs: anyone may append

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
    if sys.argv[1:] == ["--selftest"]:
        sys.exit(selftest())
    try:
        sys.exit(main(sys.argv))
    except Exception:
        sys.exit(0)
