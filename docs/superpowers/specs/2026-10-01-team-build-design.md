# team-build: design spec

Date: 2026-10-01
Status: draft, awaiting review

## Problem

When several people each drive their own coding agent (Claude Code or Codex) on one project, as at a hackathon, the team loses work in a predictable way. Each agent plans from a snapshot of shared assumptions (data shapes, libraries, how auth works). Someone discovers something that changes an assumption, and nothing tells the other agents, so their plans go stale and people restart. Planning in parallel doesn't work well, so in practice one person plans and the others wait.

This is documented:
- CooperBench (arXiv 2601.13295): two coding agents splitting features succeed about 30% less often than one agent doing both. The causes are vague or late messages, agents breaking agreed integration points, and wrong beliefs about the partner's plan.
- "When Agents Coordinate" (arXiv 2608.16801): a shared file works better than 1-to-1 messages (about 42% fewer output tokens at 8 agents), and naming a coordinator agent doesn't reliably help.
- Brooks's law applies (Codemanship, "The Mythical Agent-Month"): merges land one at a time, and parallel branches drift apart the longer they go without syncing.

## Goal

Nobody on the team restarts work because of a change they didn't hear about.

## Non-goals

- A live shared service (MCP decisions board, web dashboard). Repo files reach every agent with no install and no auth. Revisit only if git sync proves too slow.
- Linear/Plane task sync.
- Pre-push contract enforcement.
- Coordinating multiple agents for one person. Claude Code agent teams already cover that.

## Users

- **Integrator** (usually Soren): runs the skill, owns `main`, the plan and the merges.
- **Teammates**: use Claude Code or Codex. They don't need to install anything; cloning the repo is enough.

## Distribution

One public repo, `iamsorenl/team-build`, holding the skill in the shared Agent Skills format (`SKILL.md` with `name` + `description`, which both Claude Code and Codex read).

The integrator installs it one of three ways:
- Claude Code plugin: `/plugin marketplace add iamsorenl/team-build`, then `/plugin install team-build@team-build`. The repo has `.claude-plugin/marketplace.json` and `plugin.json`.
- Codex: `$skill-installer` pointed at the repo, or a copy into `~/.agents/skills/team-build`.
- Manual: copy the folder into `~/.claude/skills/`.

**Teammates get it by cloning.** At kickoff the skill copies itself into the project at `.agents/skills/team-build/` (where Codex looks) and adds a `.claude/skills/team-build` symlink to it (where Claude Code looks). Every teammate's agent can then run the "during" and "wrap" phases with no install.

## Repo layout

```
team-build/
  README.md                      # what it is, install for Claude + Codex, the playbook
  LICENSE                        # MIT
  .claude-plugin/
    marketplace.json
    plugin.json
  skills/team-build/
    SKILL.md                     # phase detection + all three phases
    templates/
      AGENTS.md                  # team rules; the single source both tools read
      DECISIONS.md
      CONTRACTS.md
      TEAM.md
    hooks/
      team_hook.py               # one script, both tools, both hook events
      claude-settings.json       # snippet merged into project .claude/settings.json
      codex-hooks.json           # copied to project .codex/hooks.json
    scripts/
      github_profile.sh          # gh api -> languages/topics/recent repos for one handle
      sync_check.sh              # branch age/behind-main/ownership report
```

## Files the skill writes into a project

| File | Purpose |
|---|---|
| `AGENTS.md` | Team rules (below). Codex reads it natively. If an `AGENTS.md` already exists, the rules are appended under a `## Team rules` heading. |
| `CLAUDE.md` | Contains `@AGENTS.md` so Claude reads the same rules. If a `CLAUDE.md` already exists, the import line is added. |
| `DECISIONS.md` | Append-only log: time, who, decision, slices affected. |
| `CONTRACTS.md` | API shapes, types and schema, with example JSON for success, empty and error cases. Each contract names its owner and consumers. |
| `TEAM.md` | People: name, `git config user.name`, optional GitHub handle, one-line strengths, role, slice, **owned paths** (globs). |
| `.agents/skills/team-build/`, `.claude/skills/team-build` | The vendored skill (see Distribution). |
| `.claude/settings.json`, `.codex/hooks.json` | Hook registration (see Hooks). |

Rules in `AGENTS.md` (short, imperative):
1. Read `DECISIONS.md` and `CONTRACTS.md` before planning any task.
2. Edit only files in your slice's owned paths (`TEAM.md`). If you need to change someone else's file, stop and tell your human.
3. Never change a contract quietly. Its owner edits `CONTRACTS.md`, logs it in `DECISIONS.md`, and tells the consumers.
4. When you learn something that changes the plan, add it to `DECISIONS.md` before continuing.
5. Plan only the current task. Keep plans short.
6. Branch from the latest `main` and merge small and often (every 30–60 min).

## Phase detection

- No `DECISIONS.md` in the repo root → **kickoff**.
- The user mentions wrap, demo, freeze or "we're done" → **wrap**.
- Otherwise → **during**. The sub-action comes from the user's words; if unclear, ask which one.

## Phase 1: kickoff

1. Ask what's being built and the time box.
2. Ask who's on the team. For each person, everything is optional:
   - a name (default `Teammate N`)
   - a GitHub handle → `github_profile.sh` reads public repos (languages, topics, recent projects) and the agent writes a one-line strengths summary, which the person can correct
   - a self-description, typed by the person or relayed
   - their `git config user.name`, needed for ownership warnings; if missing, the agent asks them to run `git config user.name` and reply
3. Pick the integrator (default: whoever is running the skill).
4. List open technical questions as **spikes**. Assign one to each non-integrator, matched to strengths where known. Spikes run in throwaway worktrees or branches and report back to `DECISIONS.md`.
5. The integrator (with their agent) builds the **walking skeleton**: folder layout, one end-to-end path with mock data, sample JSON next to `CONTRACTS.md`.
6. Write `CONTRACTS.md` for the skeleton's interfaces.
7. Split the build into **vertical slices**, each with owned paths that don't overlap. Assign slices by strengths; with no info, assign by need. Write `TEAM.md`.
8. Write the rules, vendor the skill, install the hooks, and commit on `main`.
9. Print a message ready to paste into the group chat: each person's spike, then their slice and owned paths, the repo URL, and "your agent: read AGENTS.md first; Codex users run /hooks once to trust the hooks."

Spikes come before the slice split on purpose: discoveries should happen before the work is divided. If a spike changes the skeleton or contracts, the integrator updates them before teammates start their slices.

## Phase 2: during

- **Discovery** ("we found", "turns out", "X doesn't work"): append to `DECISIONS.md`. Use `TEAM.md` and `CONTRACTS.md` to find which slices and contracts it affects. Draft a heads-up naming those people. Commit and push the `DECISIONS.md` change straight away (small commit to `main`, or tell the integrator).
- **Contract change**: confirm the requester owns the contract (if not, draft a request to the owner instead). Edit `CONTRACTS.md` and the sample JSON, log it in `DECISIONS.md`, and draft a heads-up to the consumers.
- **Sync / merge check**: `sync_check.sh` runs `git fetch`, then for each remote branch reports commits behind `main`, age of the oldest unmerged commit (flag over 60 min), and changed files outside that branch owner's owned paths. The agent turns this into a short action list.
- **Reassign / add a person**: update `TEAM.md` with non-overlapping paths and log it.

## Phase 3: wrap

1. Integration check: run the project's start and test commands (asking for them if they can't be detected), and compare real responses with the `CONTRACTS.md` examples (field names and types).
2. Call a code freeze: log it in `DECISIONS.md` and draft the group message ("merge by HH:MM, then only the integrator commits").
3. Draft a demo script from the goal, the `DECISIONS.md` highlights and `TEAM.md`, crediting each person's slice.

## Hooks

One script, `team_hook.py` (Python 3 standard library only), called from both tools. It reads the event JSON on stdin and replies in the tool's format (a `--tool claude|codex` flag picks the format).

1. **Decisions-changed reminder** (`UserPromptSubmit`): hash `DECISIONS.md` + `CONTRACTS.md` and compare with the last-seen hash in `.git/team-build-seen` (per clone, never committed). If they differ, inject context: "DECISIONS.md/CONTRACTS.md changed since you last read them; re-read before continuing," then store the new hash. If the files are missing or the directory isn't a repo, do nothing.
2. **Ownership warning** (`PreToolUse` on file-edit tools: Claude `Edit|Write|MultiEdit`; Codex's edit tool, name to be confirmed during planning): map `git config user.name` to a person in `TEAM.md`. If the target path is outside their owned paths and inside someone else's, return a **warning, not a block**, naming the owner. Unknown user or unowned path → allow silently.

Codex requires each user to trust a project hook (`/hooks`) before it runs. The kickoff message tells Codex users to do this. Codex users who skip it still get the rules through `AGENTS.md`.

To verify during planning: Codex's exact hook output format for injecting context and for warnings, and Codex's edit tool name for the matcher.

## Error handling

- `gh` missing or not logged in, or a handle not found: skip the profile, use the typed description or nothing, and say so in one line.
- The project already has `AGENTS.md`, `CLAUDE.md` or `.claude/settings.json`: merge into it, never overwrite.
- `TEAM.md` owned paths overlap: kickoff refuses to write them and asks for a fix.
- Hooks fail open: any exception exits 0 with no output, so a broken hook never blocks anyone's agent.

## Testing

- `team_hook.py` gets a `__main__` self-check (`python3 team_hook.py --selftest`) that builds a temp git repo and asserts: a hash change produces a reminder, then none on the next call; an owned path is silent; another person's path warns; an unknown user is silent; both output formats parse.
- `sync_check.sh` gets a dry run against a temp repo with two branches, one touching foreign paths.
- Manual end-to-end: kickoff in a scratch repo with a made-up 3-person team (one real GitHub handle, one typed description, one with nothing). Then run a discovery, a contract change, a sync and a wrap. Then open the repo in Codex and confirm the skill is found and the hooks show up in `/hooks`.

## Open questions

None blocking. The repo name `team-build` can change before publishing.
