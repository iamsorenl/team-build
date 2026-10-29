# team-build on MiniMax Code + public examples: design

Date: 2026-10-28. Status: draft for Soren's review.

## Why

On X, Ronny He (Head of R&D at MiniMax Code) wrote that a design or progress doc should hold a task's plan, decisions, rejected options and review conclusions, so a new session or a new person can pick up from it. Soren replied that team-build does that for a whole team. Ronny answered: "Shared state in the repo is the multiplayer version of the progress doc. If you try it with MiniMax Code, would love to see it on GitHub."

What Soren wants from the reply link: show team-build working in MiniMax Code (MCode), in a way other people can rerun and add to. He can't test every agent and scenario himself, so the examples are open source and grow through other people's runs.

## Goals

1. team-build works in MCode, installed by following the README and checked with a real run.
2. A repeatable scripted scenario that one person can run alone, playing two teammates on different agents: Claude Code in one clone, MCode in the other. Codex is optional.
3. An `examples/` folder of run reports in one template. Two kinds: scripted runs of that scenario, and free-form reports of real sessions.
4. A short contributing note so other people can add a run with their own agent or scenario.
5. After that: rewrite the README opening around "the multiplayer version of the progress doc", then reply on the X thread with the link.

## Non-goals

- No new coordination features. This is about support and evidence.
- No automated CI harness that drives agents. Runs are done and written up by people.
- Not covering MiniMax's "Agent Team" feature (one person, many subagents). That isn't what team-build is for.

## Anti-goals (would make this a failure even if it works)

- Claims that go further than what was run. Every "works in MCode" line needs a run report behind it.
- Making a contributor pay. The scripted scenario must be runnable without paid MiniMax credits (see local models below).
- Breaking or doubling up the existing Claude Code and Codex behavior.

## What we already know (spike, 2026-10-28, MCode 0.7.1)

Spike setup: a scratch repo with team-build installed by `install_project.py`. TEAM.md listed Ana (owns `web/`) and Bo (owns `api/`), and git user.name was Ana. MCode ran through `mcode exec`, using the local Ollama model `gpt-oss:20b` as a custom provider.

- **The skill loads.** MCode reads `.agents/skills`, `.claude/skills` and `.minimax/skills`, and team-build's installer already writes `.agents/skills/team-build`.
- **Project-level hooks are ignored.** With only `.claude/settings.json` and `.codex/hooks.json` in the repo, neither hook ran: no `.git/team-build-seen` marker, and no warning when Ana created `api/health.py`.
- **Hooks shipped inside a plugin work.** We copied the plugin folder (`.claude-plugin/plugin.json`, `skills/`, plus `hooks/hooks.json` with the same content as `skills/team-build/hooks/claude-settings.json`) into `~/.minimax/plugins/team-build/`. MCode then listed it as `team-build@local`, enabled, with 1 skill. On the next run:
  - The edit hook fired on a new file, and the model quoted the warning verbatim: "team-build: api/health.py belongs to Bo. …". MCode maps its own `edit`/`write` tools to Claude's names, so the `Edit|Write|MultiEdit` matcher worked unchanged.
  - The prompt hook ran (the marker was written). After DECISIONS.md changed, the model saw "team-build: DECISIONS.md or CONTRACTS.md changed since you last saw them…" in its context.
  - The warning is advisory, same as in Claude Code: the file was still created.
- **Install is manual.** MCode has no command to install a plugin from a GitHub URL or a local path. Users copy a plugin folder into `<MCode data dir>/plugins/<name>/` (`~/.minimax/plugins/` by default). The npm build said "Plugin marketplaces are not available in this build".
- **Gotchas for the README:**
  - `mcode login` defaults to the China site (it asks for a Chinese phone number or WeChat). Use `mcode login --region global`.
  - MiniMax models need paid credits; the error is `insufficient balance (1008)`.
  - For free runs, use a local model: `mcode provider add --name ollama-gptoss --base-url http://localhost:11434/v1 --api-format openai-completions --model gpt-oss:20b --api-key-env <VAR> --context-limit 32768 --output-limit 4096`, then `mcode exec --model custom_provider:ollama-gptoss/gpt-oss:20b`. `qwen3-coder:30b` failed with "does not support thinking".
  - Warm the model first, or the 10-second provider test times out.

## Decided

- Support MCode through its plugin path, using the Claude-format plugin team-build already ships, plus a `hooks/hooks.json`.
- The demo is one person playing two teammates: Claude Code in clone A, MCode in clone B, on one demo repo with a GitHub remote (or a local bare repo). Codex as a third clone is a bonus if time allows.
- One run-report template for both kinds of run.
- The scripted scenario, at minimum:
  1. Both clones start from the same TEAM.md (two people, non-overlapping owned paths).
  2. A records a discovery in DECISIONS.md and pushes.
  3. B pulls. B's next prompt shows the "DECISIONS.md changed" reminder, and B's agent acts on the new decision.
  4. B changes a contract in CONTRACTS.md and logs it. A pulls and gets the reminder.
  5. One agent tries to edit a path owned by the other person and gets the ownership warning.
  6. `sync_check.py` before merge.

  Each step's expected result is written down, so a report can mark pass, fail or "partly".
- The free-run path (local model through Ollama) is documented next to the MiniMax-credits path.

## Calls made after review (Claude's, not Soren's; check these)

- **Pass/fail is graded on team-build, not the model.**
  - Each step's pass check is evidence that team-build itself did its job: the hook ran (marker file, or the `team-build:` text in the transcript or in `systemMessage`), and the file state is right after pull.
  - Whether the model then acted on it is recorded in a separate "agent behavior" column, so a weak local model doesn't read as a team-build failure.
  - Prompts in the scripted scenario are fixed text, so runs are comparable.
- **The MCode plugin package is hooks-only and needs the project installer.**
  - The hook commands point at `.agents/skills/team-build/hooks/team_hook.py` inside the project. So the MCode package works only in repos where `install_project.py` already ran.
  - The README says: run the installer, then copy the MCode package.
  - The package doesn't include `skills/`, because MCode already loads the skill from `.agents/skills`. MCode accepts a plugin whose only capability is hooks.
  - This leaves the Claude Code and Codex hook commands untouched.
- **A seeding script builds the scenario's starting state.** A script in this repo (e.g. `examples/scripted/seed.sh`) creates the demo repo: a bare remote plus two clones with different `git user.name`, the baseline TEAM.md, and team-build installed. Every runner starts from the same state without a separate demo repo to maintain.
- **Claude may run MCode for verification on this machine,** using the local Ollama model and the plugin copy in `~/.minimax/plugins/`.

## Soren's answer (2026-10-29)

- Report #1 is agent-driven: Claude runs both teammates (`claude -p` for Claude Code, `mcode exec` for MCode). The report says so plainly.

## Left to the builder

- **Where the MCode `hooks/hooks.json` lives.** Constraint: Claude Code users who installed the plugin must not get every hook twice (once from the plugin, once from the project `.claude/settings.json` the installer writes). The prompt hook is safe to run twice because it uses the hash marker; the edit warning would show twice. Options:
  - a separate MCode package folder in the repo that the user copies
  - `install_project.py` printing or doing the copy into the MCode plugins dir
  - a root `hooks/hooks.json`, if Claude Code double-firing turns out to be harmless or avoidable

  Pick one, then test both Claude Code and MCode after the change.
- Whether `install_project.py` should detect MCode and handle the plugin copy. It must keep its "never overwrite" behavior.
- Run-report template fields. At least: date, agents and versions, models, scenario (scripted or free-form), step results, what broke, and links (commits or a transcript excerpt).
- File names and layout under `examples/`, and where the contributing note goes (README section or CONTRIBUTING.md).
- Whether the demo repo is a folder in this repo or its own small repo.
- Updating the tests (`tests/`, the `--selftest` modes) for whatever install change is made.

## Order of work

1. MCode support change, plus README install section for MCode (with the gotchas above).
2. Scripted scenario doc and run-report template.
3. Soren's first scripted run (Claude Code + MCode on a local model), written up as `examples/` report #1. If MiniMax credits are added later, a second run on MiniMax's own model.
4. Contributing note.
5. README opening rewrite around the progress-doc framing.
6. Draft the X reply with the link. Soren posts it.

## Cleanup from the spike

These are left on Soren's machine:
- `~/.minimax/plugins/team-build/` (copy of the plugin, with hooks)
- two custom providers in `~/.minimax/config.yaml` (`ollama-local`, `ollama-gptoss`)
- the scratch demo repo and the MCode install in the session scratchpad

The MCode install is not on PATH. MCode's config has `dataContribution: enabled: true` by default. Soren may want to turn that off.
