# Examples

Reports from people running team-build with real agents. I can't test every agent and every team setup myself, so this folder is meant to grow from other people's runs.

There are two kinds:

- **Scripted runs** follow [scripted/SCENARIO.md](scripted/SCENARIO.md): two teammates, six steps, fixed prompts. One person can play both teammates. Because the prompts are the same each time, runs can be compared across agents and versions.
- **Free-form runs** are write-ups of a real session: a hackathon, a weekend project, anything with more than one person's agent on a repo. Messy is fine. Say what helped and what got in the way.

## Add yours

1. Copy [TEMPLATE.md](TEMPLATE.md) to `runs/YYYY-MM-DD-<agent-a>-plus-<agent-b>.md`.
2. Fill it in. Grade each step on what team-build did (did the hook fire, did the right text reach the agent), and note separately what the agent did with it.
3. Open a pull request.

Failed runs are as useful as passing ones. If an agent isn't supported yet, a report showing where it breaks is a good start.

## Runs so far

- [2026-10-29: Claude Code + MiniMax Code](runs/2026-10-29-claude-code-plus-mcode.md) (scripted, agent-driven)
