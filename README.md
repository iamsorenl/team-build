# team-build

A skill for Claude Code and Codex that keeps a team in sync when everyone is driving their own coding agent on the same repo. It's built for hackathons and anything else that moves that fast.

## Why this exists

I built this after a hackathon where every person on the team had their own coding agent, and we kept having to redo work because of each other's discoveries.

We were figuring it out as we went. We split up the tasks, and then someone would learn something an hour in: the API couldn't do what we'd assumed, or a data shape had to change. Nobody else's agent knew. Their plans were built on the old assumption, so people had to start over. Planning in parallel didn't work either, because every plan depended on the others, so one person ended up planning while everyone else waited.

The agents made each of us fast. What slowed us down was the team. Coding agents help a lot when one person holds all the context, and they fall apart once several people each hold a different slice of it under a deadline.

It's a known problem, not just a bad weekend:

- [CooperBench](https://arxiv.org/abs/2601.13295) gave two coding agents separate features in the same repo. Together they succeeded about 30% less often than one agent doing both. The failures came from vague or late messages, agents breaking agreed integration points, and wrong guesses about what the other agent was doing.
- [When Agents Coordinate](https://arxiv.org/abs/2608.16801) found that a shared file works better than agents messaging each other, and that naming one agent "coordinator" didn't reliably help.
- Brooks's law still applies (["The Mythical Agent-Month"](https://codemanship.wordpress.com/2026/04/06/the-mythical-agent-month/)). Merges land one at a time, and parallel branches drift further apart the longer they go without syncing. Agents make that worse, because they write code faster than people sync.

team-build puts the team's shared knowledge in a few repo files that every agent reads, whether it's Claude Code or Codex, and gives the team a simple routine around them.

## The routine

1. **Pick an integrator.** One person owns `main`, the plan and the merges.
2. **Run spikes before splitting.** While the integrator builds the skeleton, everyone else answers one open question ("can this API do X?"). Discoveries should happen before the work is divided.
3. **Build a walking skeleton.** One end-to-end path with mock data, plus the folder layout.
4. **Write contracts.** API shapes and types go in `CONTRACTS.md`, with examples for success, empty and error. Each contract has one owner.
5. **Give each person a vertical slice** with owned paths that don't overlap.
6. **Every agent reads `DECISIONS.md`** before planning. Discoveries go there first.
7. **Contract changes are a team event.** The owner edits the contract, logs it and tells the people who use it.
8. **Merge every 30 to 60 minutes.** Always branch from the latest `main`.
9. **Plan only the current task.** Big plans written at hour 0 are stale by hour 3.

## Install (just the person running kickoff)

**Claude Code**
```
/plugin marketplace add iamsorenl/team-build
/plugin install team-build@team-build
```

**Codex**
```
codex plugin marketplace add iamsorenl/team-build
codex plugin add team-build@team-build
```

**Manual:** copy `skills/team-build` into `~/.claude/skills/` (Claude Code) or `~/.agents/skills/` (Codex).

**MiniMax Code (MCode)**

MCode loads the skill from the project like Codex does, but it ignores project hook files and only runs hooks that come from a plugin. So after kickoff, each teammate on MCode runs this once from the project:

```
python3 .agents/skills/team-build/scripts/install_project.py --mcode
```

That writes a small plugin to `~/.minimax/plugins/team-build` (or `$MINIMAX_DATA_DIR/plugins`) with the two hooks and its own copy of the hook script. It never overwrites an existing one. The hooks only read the project's TEAM.md, DECISIONS.md and CONTRACTS.md, and never run code from the repo, so they do nothing in repos without team-build. To update after a team-build upgrade, delete that folder and run the command again.

Things that tripped me up setting MCode up:

- `mcode login` goes to MiniMax's China site by default. Use `mcode login --region global`.
- MiniMax's own models need paid credits (`insufficient balance (1008)` means none). You can run it free on a local Ollama model instead:
  ```
  read -s KEY; export KEY   # any value, Ollama ignores it
  mcode provider add --name ollama-gptoss --base-url http://localhost:11434/v1 \
    --api-format openai-completions --model gpt-oss:20b --api-key-env KEY \
    --context-limit 32768 --output-limit 4096
  mcode exec --model custom_provider:ollama-gptoss/gpt-oss:20b "..."
  ```
  `qwen3-coder:30b` failed with "does not support thinking". `gpt-oss:20b` worked.
- Load the model in Ollama before the first run, or MCode's 10-second connection check times out.

Then say something like "we're doing a hackathon with three people, set us up."

## Your teammates don't install anything

Kickoff copies the skill into the project, so cloning the repo is enough for both Claude Code and Codex users. MCode users also run the one `--mcode` command above to get the hooks.

| File | What it's for |
|---|---|
| `AGENTS.md` | The team rules. Codex reads it automatically. Existing content is kept and the rules are appended. |
| `CLAUDE.md` | Contains `@AGENTS.md`, so Claude reads the same rules. |
| `DECISIONS.md` | Append-only log of what the team learned or decided. |
| `CONTRACTS.md` | Interfaces between slices, with owners and examples. |
| `TEAM.md` | People, strengths, slices and owned paths. |
| `.agents/skills/team-build/` | The skill, where Codex looks for it. |
| `.claude/skills/team-build` | Symlink to the same skill, where Claude Code looks for it. |
| `.claude/settings.json`, `.codex/hooks.json` | The two hooks below, merged with any you already have. |

## What it does during the event

- **Kickoff:** asks what you're building and who's on the team. Everything about each person is optional; give a GitHub handle and it reads their public repos to guess strengths. Then it assigns spikes, helps build the skeleton, writes the files and prints a message to paste into your group chat.
- **During:** "turns out X" logs a discovery and drafts a heads-up to the people affected. "Change the contract" checks you own it first. "Sync check" reports, per branch, how far behind `main` it is, how old its oldest unmerged commit is, and whether it touched someone else's files.
- **Wrap:** checks the real app against the contracts, calls a code freeze and drafts a demo script that credits everyone's work.

## Hooks

Two small hooks run for every teammate whose tool has them enabled:

1. **Decisions changed.** If `DECISIONS.md` or `CONTRACTS.md` changed since the agent last saw them (usually after a `git pull`), the agent is told to re-read them before continuing.
2. **Someone else's file.** If an agent is about to edit a file owned by another person in `TEAM.md`, it gets a warning naming the owner. The edit is never blocked.

Codex asks each person to review and trust project hooks. Run `/hooks` once after cloning. Codex also only loads project config for projects you've trusted. If someone skips this, they still get the rules through `AGENTS.md`.

MCode doesn't read `.claude/settings.json` or `.codex/hooks.json`. It gets the same two hooks from the plugin that `--mcode` installs.

The ownership warning matches your `git config user.name` against `TEAM.md`, so make sure yours matches.

## Known limits

- The overlap check compares path patterns with each other, not with every possible file, so unusual globs can slip past.
- Codex users who don't trust the hooks only get the written rules. (In testing, Codex followed the AGENTS.md ownership rule on its own and refused to edit someone else's file.)
- If the integrator has the plugin installed and the project also has the vendored copy, the skill shows up twice in the skill list. Either one works.

## Try it and add your run

[examples/](examples/) has a scripted two-teammate scenario you can run alone with any two agents, plus reports from runs so far. If you try team-build with an agent or setup that isn't there, add a report. Failed runs count too.

## Tests

```
python3 skills/team-build/hooks/team_hook.py --selftest
python3 skills/team-build/scripts/install_project.py --selftest
bash tests/sync_check_test.sh
bash tests/seed_test.sh
```

## License

MIT
