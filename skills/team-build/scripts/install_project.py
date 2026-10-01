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
