# Run: Claude Code + MiniMax Code, scripted

- Date: 2026-10-29
- Driven by: an agent. Claude Code (Opus) ran both sides from one terminal: `claude -p` for Ana and `mcode exec` for Bo, with the git steps done in between. No human typed the prompts.
- Agents and versions: Claude Code 2.1.312 as Ana; MiniMax Code 0.7.1 as Bo
- Models: Ana on Claude Sonnet; Bo on `gpt-oss:20b`, local through Ollama (no MiniMax credits used)
- team-build version or commit: branch `mcode-and-examples` (MCode hooks installed with `install_project.py --mcode`)
- Scenario: [examples/scripted/SCENARIO.md](../scripted/SCENARIO.md), plus one extra step (5b)

## Results

| Step | team-build evidence | Result | Agent behavior |
|---|---|---|---|
| 1. Same starting state | user.name matched TEAM.md in both clones; prompt hook ran in both (`.git/team-build-seen` created) | pass | Ana (Claude): "You own `web/`", correct. Bo (gpt-oss): "You own `web/` and `api/`", wrong. |
| 2. Ana logs a discovery | New DECISIONS.md entry: API is daily only, affects Bo and `GET /forecast` | pass | Left CONTRACTS.md alone, said Bo has to pick the new shape as owner, drafted a heads-up to Bo. |
| 3. Bo picks it up (MCode) | After `git pull`, Bo's prompt hook sent the reminder: the marker hash changed `d55871a…` → `ea75605…`, and the hook only rewrites it when it sends the message. The reminder text is in MCode's session log. | pass | The plan switched to daily data and proposed changing the contract. |
| 4. Bo changes the contract, Ana picks it up | Ana's transcript has `team-build: DECISIONS.md or CONTRACTS.md changed since you last saw them.` | pass (see note) | Bo updated CONTRACTS.md to `days: [{date, high_c, low_c}]` and logged it. Ana's answer used the daily shape, and noticed that the log entry was signed "MiniMax Code" instead of Bo. |
| 5. Ana tries to edit Bo's file | No hook warning: the edit hook never ran, because Claude declined before trying the edit | n/a for the hook; the rules worked | Claude cited the AGENTS.md rule ("`api/` belongs to Bo") and offered two options: ask Bo, or reassign the path. |
| 5b (extra). Bo edits Ana's file (MCode) | MCode's session log has `team-build: web/status.html belongs to Ana. That is outside your slice in TEAM.md.` | pass | gpt-oss created the file anyway. That's allowed, since the warning never blocks, but a stronger model would likely have stopped. |
| 6. Sync check | `origin/bo-status (Bo): touches other slices: web/status.html` | pass | n/a |

## What broke

- **MCode ignores project hooks.** `.claude/settings.json` and `.codex/hooks.json` do nothing in MCode, so team-build now installs its hooks as an MCode plugin (`install_project.py --mcode`).
- **Setup friction:**
  - `mcode login` defaults to MiniMax's China site. Use `--region global`.
  - MiniMax models needed credits.
  - `qwen3-coder:30b` failed on "does not support thinking".
  - The first connection check timed out until the model was loaded.

  All of these are in the README.
- **Step 2, first try:** Claude stopped to ask before pushing to `main`, because the skill's discovery flow pushes, and it wrote nothing. The scenario prompts for steps 2 and 4 now say "don't commit or push; I'll do the git part".
- **Step 4 (Bo):** the local model's stream ended early ("Stream ended without finish_reason") after both files had been edited correctly. It's an Ollama or MCode hiccup, not a team-build one.
- **Signed by the tool, not the person:** gpt-oss on MCode wrote "MiniMax Code" as the author of its DECISIONS.md entry. Claude, on Ana's side, caught it.
- **Step 4 note:** Ana had also edited DECISIONS.md herself in step 2, so her reminder in step 4 would have fired even without Bo's change. The answer used Bo's new contract shape, so she did pick it up, but the hook alone doesn't prove it.
- **`mcode exec` only prints the final answer,** so hook text on the MCode side came from the marker file and MCode's session logs (`~/.minimax/v2/sessions/…/messages.jsonl`), not from stdout.

## Evidence

Ana, step 4 (Claude Code stream-json):
```
team-build: DECISIONS.md or CONTRACTS.md changed since you last saw them. Re-read both before planning or editing.
```

Ana, step 5 (final answer, excerpt):
```
I haven't created `api/health.py`. In TEAM.md, `api/` belongs to Bo (the forecast API slice). You're Ana, and you own `web/` only.
```

Bo, step 5b (MCode session log):
```
team-build: web/status.html belongs to Ana. That is outside your slice in TEAM.md.
```

Step 6:
```
origin/bo-status (Bo): touches other slices: web/status.html
```
