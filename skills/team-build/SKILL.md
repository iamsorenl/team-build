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
7. **Slices.** Split the remaining work into vertical slices with owned paths that don't overlap. Assign by strengths where known, otherwise by need. The integrator owns shared files (layout, config). Don't list DECISIONS.md or CONTRACTS.md as anyone's paths: everyone appends to DECISIONS.md, and each contract's owner is named inside CONTRACTS.md.
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
2. Get only that entry onto main straight away, never the rest of a feature branch:
   - On main: `git pull --rebase`, commit only DECISIONS.md, `git push`.
   - On a feature branch: commit only DECISIONS.md there, then `git checkout main && git pull --rebase && git cherry-pick <that commit> && git push && git checkout -`. Never push the feature branch to main.
   - If they can't push to main, give them the entry to send to the integrator.
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
