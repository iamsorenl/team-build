# team-build on MCode + examples Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make team-build's hooks work in MiniMax Code (MCode), add a repeatable two-teammate scenario plus a run-report format, publish run #1 (Claude Code + MCode, agent-driven), and rewrite the README opening.

**Architecture:**
- MCode only takes hooks from plugins in `<data dir>/plugins/<name>/`. `install_project.py --mcode` writes a hooks-only Claude-format plugin there. Its hooks are generated from the existing `hooks/claude-settings.json`, so there's one source of truth, and nothing at the repo root changes for Claude Code.
- `examples/scripted/seed.sh` builds a bare remote and two clones (Ana, Bo) so every run starts from the same state.
- Run reports are Markdown files in `examples/runs/`.

**Tech Stack:** Python 3 stdlib, bash, git. MCode 0.7.1 for runs, on local Ollama `gpt-oss:20b`.

**Spec:** `docs/superpowers/specs/2026-10-28-mcode-and-examples-design.md`

## Global Constraints

- The installer never overwrites existing files (existing behavior; keep it).
- No change to the Claude Code or Codex hook commands, or to the root `.claude-plugin/` and `.codex-plugin/` manifests' behavior.
- MCode data dir is `$MINIMAX_DATA_DIR` if set, else `~/.minimax`.
- Runs must be possible without paid MiniMax credits (a local Ollama model).
- Claims in the README and reports go only as far as what was actually run. Report #1 says it was agent-driven.
- Plain English in docs, no buzzwords (Soren's style).

## Review Focus

1. `--mcode` run when `~/.minimax` doesn't exist (MCode not installed): should say so and exit non-zero, not create a stray `~/.minimax`. Tested in Task 1.
2. `--mcode` run twice, or over an existing `team-build` plugin dir: should leave it alone and say so. Tested in Task 1.
3. `seed.sh` pointed at a directory that already exists: should refuse instead of mixing old state in. Tested in Task 2.
4. A teammate whose `git user.name` doesn't match TEAM.md gets no ownership warning. That's existing behavior; the scenario doc says to check it. Covered in Task 2's SCENARIO.md.
5. The global MCode plugin fires in non-team-build repos: the hook must stay silent (`|| true`, no `.agents/skills/team-build`). Checked by hand in Task 1 step 6.

---

### Task 1: `install_project.py --mcode`

**Files:**
- Modify: `skills/team-build/scripts/install_project.py`
- Modify: `README.md` (install section and hooks section)

**Interfaces:**
- Produces: `install_mcode(data_dir: str, log=print) -> int`. It returns 0 on success or when the plugin already exists, and 1 when `data_dir` doesn't exist. CLI: `install_project.py --mcode`.

- [ ] **Step 1: Write the failing test.** Extend `selftest()`:
  - With `tmp/nomcode` missing: `install_mcode(...)` returns 1, and the dir is still missing.
  - With `tmp/mc` created: returns 0, and these files now exist:
    - `tmp/mc/plugins/team-build/.claude-plugin/plugin.json`, with `name == "team-build"` and no `skills` key
    - `tmp/mc/plugins/team-build/hooks/hooks.json`, equal to `json.load(claude-settings.json)`
  - Second call: returns 0, the log has a line containing `already`, and the file mtimes are unchanged.
- [ ] **Step 2:** Run `python3 skills/team-build/scripts/install_project.py --selftest`. Expected: fails with NameError `install_mcode`.
- [ ] **Step 3: Implement `install_mcode`.** Write `plugin.json` as `{"name","version","description","author","license"}`, copied from `.claude-plugin/plugin.json` fields but without `skills`. Copy `hooks/claude-settings.json` byte-for-byte to `hooks/hooks.json`. Add a `--mcode` CLI branch that resolves the data dir as in Global Constraints.
- [ ] **Step 4:** Run the selftest. Expected: `selftest ok`.
- [ ] **Step 5: Live check.**
  1. `rm -rf ~/.minimax/plugins/team-build`, then run `--mcode`.
  2. `mcode plugin list --available --marketplace local --json` should show `team-build@local` enabled.
  3. Rerun the spike scenario in a fresh scratch repo: as Ana, create `api/health.py`. The transcript should contain `belongs to Bo`, and `.git/team-build-seen` should exist.
  4. If MCode rejects a hooks-only plugin, add `"skills": "./skills/"` plus a copied skill. Record that in the spec.
- [ ] **Step 6:** In a scratch git repo without team-build, run one `mcode exec` prompt. Expected: no `team-build:` text and no error notice.
- [ ] **Step 7: README.** Under Install, add **MiniMax Code (MCode)**:
  1. The kickoff person installs as usual.
  2. Each MCode teammate runs `python3 .agents/skills/team-build/scripts/install_project.py --mcode` once.
  3. Gotchas: `mcode login --region global`; credits vs the local-model path, with the exact `mcode provider add …` line from the spec; warm the model first; `qwen3-coder:30b` fails on "thinking".

  Under Hooks, add one line: MCode ignores project hook files and loads them from the plugin. Add MCode to the README's table row for "your teammates don't install anything", with the exception.
- [ ] **Step 8:** Commit `feat: --mcode installs team-build hooks as an MCode plugin`.

### Task 2: Scripted scenario, seed script, report template

**Files:**
- Create: `examples/scripted/seed.sh`, `examples/scripted/SCENARIO.md`, `examples/TEMPLATE.md`, `examples/README.md`
- Create: `tests/seed_test.sh`
- Modify: `README.md` (Tests list, plus an "Add your run" section linking `examples/README.md`)

**Interfaces:**
- Produces: `seed.sh <dir>`, which creates:
  - `<dir>/remote.git` (bare)
  - `<dir>/ana` with `user.name Ana`, which ran `install_project.py` and holds TEAM.md (Ana: `web/`, Bo: `api/`), committed and pushed on `main`
  - `<dir>/bo` with `user.name Bo`, cloned after the push

  It exits 1 with a message if `<dir>` already exists.

- [ ] **Step 1:** Write `tests/seed_test.sh`. It runs seed into a `mktemp -d` subdir and asserts:
  - both clones exist, and `git -C bo log -1` equals `git -C ana log -1`
  - `bo/TEAM.md` contains `| Bo | Bo |`
  - `bo/.agents/skills/team-build/hooks/team_hook.py` exists
  - a second run on the same dir exits non-zero

  Then it prints `seed_test ok`.
- [ ] **Step 2:** Run `bash tests/seed_test.sh`. Expected: fails because there's no seed.sh yet.
- [ ] **Step 3:** Implement `seed.sh`. It finds the installer relative to itself (`../../skills/team-build/scripts/install_project.py`).
- [ ] **Step 4:** Run `bash tests/seed_test.sh`. Expected: `seed_test ok`.
- [ ] **Step 5: Write `SCENARIO.md`.**
  - Six steps from the spec. Each step names which clone it runs in, the exact prompt text, and its **team-build evidence**: what must be true for pass, checkable without trusting the model (marker file, `team-build:` text in the transcript, file contents after `git pull`). Agent behavior is recorded separately.
  - Step 1 also checks that each clone's `git config user.name` matches TEAM.md.
  - Prompts: Ana logs "the weather API has no hourly data, use daily" in DECISIONS.md and pushes. Bo pulls and asks "plan the forecast endpoint". Bo changes the `GET /forecast` contract and logs it. Ana pulls and asks anything. Ana asks to create `api/health.py`. Run `sync_check.py`.
- [ ] **Step 6:** Write `TEMPLATE.md`. Fields: date; who drove it (person or agent); agents and versions; models; scenario (scripted / free-form); a step table with columns `step | team-build evidence | pass/fail/partly | agent behavior`; what broke; links. Write `examples/README.md` covering the two kinds of run, how to add one (copy the template into `runs/YYYY-MM-DD-<agents>.md` and open a PR), and that free-form reports are welcome.
- [ ] **Step 7:** Add `bash tests/seed_test.sh` to the README Tests list. Commit `feat: scripted two-teammate scenario, seed script and run template`.

### Task 3: Run #1 (Claude Code as Ana, MCode as Bo, agent-driven)

**Files:**
- Create: `examples/runs/2026-10-29-claude-code-plus-mcode.md`

- [ ] **Step 1:** `bash examples/scripted/seed.sh <scratchpad>/run1`. Make sure the MCode plugin from Task 1 is installed and `gpt-oss:20b` is warm.
- [ ] **Step 2:** Run each SCENARIO.md step.
  - Ana: `claude -p "<prompt>"` in `run1/ana`.
  - Bo: `mcode exec --cwd run1/bo --model custom_provider:ollama-gptoss/gpt-oss:20b "<prompt>"`.
  - Do the git push and pull between steps by hand, as SCENARIO says.
  - Save each transcript under `<scratchpad>/run1/logs/`.
  - If `claude -p` doesn't load project hooks, record it, then check whether `--settings .claude/settings.json` fixes it.
- [ ] **Step 3:** Fill the report from the template, using the evidence from the logs. It states that Claude drove both sides, and includes short transcript excerpts for each `team-build:` line.
- [ ] **Step 4:** Commit `docs: run #1, Claude Code + MCode on gpt-oss:20b`.

### Task 4: README opening + X reply draft

**Files:**
- Modify: `README.md` (top paragraph only; keep "Why this exists")

- [ ] **Step 1:** Rewrite the first paragraph around the idea that one agent keeps a progress doc so a new session can resume, and team-build is that doc shared by every person's agent on the repo. Name Claude Code, Codex and MCode, and link `examples/`. Run it through soren-voice, then humanizer.
- [ ] **Step 2:** Run the test commands from the README. Expected: all print `ok`. Commit `docs: lead README with the multiplayer progress doc framing`.
- [ ] **Step 3:** Draft the X reply to Ronny in chat (soren-voice) with the repo link and run #1 link. Soren posts it. Do not push or post without Soren's say-so.
