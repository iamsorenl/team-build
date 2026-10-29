# Scripted scenario: two teammates, two agents

One person can run this alone by playing both teammates. Ana is the integrator and owns `web/`. Bo owns `api/` and the `GET /forecast` contract. Use whatever agent you like for each side. Mixing agents is the point.

Each step has **team-build evidence**: what must be true for the step to pass, checkable without trusting the model. Grade the step on that. Then note separately what the agent did with it ("agent behavior"), because a weak model ignoring a warning is a model problem, not a team-build one.

Use the prompts exactly as written so runs are comparable. Do the git commands yourself between steps.

## Setup

```
bash examples/scripted/seed.sh /tmp/tb-run
```

On MCode, also run `python3 .agents/skills/team-build/scripts/install_project.py --mcode` once (see the main README).

## Steps

### 1. Both agents start from the same state
- In `ana/` and in `bo/`, prompt: `Read TEAM.md and tell me in one sentence which paths I own.`
- Evidence:
  - `git config user.name` is `Ana` in `ana/` and `Bo` in `bo/`, matching TEAM.md
  - `.git/team-build-seen` exists in both clones afterwards (the prompt hook ran)
- Agent behavior: did each name its own paths?

### 2. Ana records a discovery
- In `ana/`, prompt: `We found out the weather API has no hourly data, only daily. Log that in DECISIONS.md as a discovery that affects Bo and the GET /forecast contract. Don't change CONTRACTS.md, and don't commit or push; I'll do the git part.`
- Then: `git -C ana commit -am "decision: daily only" && git -C ana push`
- Evidence: `ana/DECISIONS.md` has a new entry mentioning daily data.
- Agent behavior: did it leave CONTRACTS.md alone? Did it draft a heads-up to Bo?

### 3. Bo picks it up
- `git -C bo pull`
- In `bo/`, prompt: `Plan the forecast endpoint in three bullets.`
- Evidence: the transcript contains `team-build: DECISIONS.md or CONTRACTS.md changed since you last saw them`.
- Agent behavior: does the plan use daily data instead of hourly?

### 4. Bo changes the contract
- In `bo/`, prompt: `Update the GET /forecast contract in CONTRACTS.md to return daily data (a "days" list with date, high_c, low_c) and log the change in DECISIONS.md. Don't commit or push; I'll do the git part.`
- Then: `git -C bo commit -am "contract: forecast is daily" && git -C bo push && git -C ana pull`
- In `ana/`, prompt: `What should the dashboard page show for the forecast?`
- Evidence: the transcript in `ana/` contains the same "changed since you last saw them" line.
- Agent behavior: does Ana's answer use the daily shape?

### 5. Someone else's file
- In `ana/`, prompt: `Create api/health.py with a function health() that returns {"ok": True}.`
- Evidence: the transcript contains `team-build: api/health.py belongs to Bo`.
- Agent behavior: did it stop and ask, or create the file anyway? (The warning never blocks; either is allowed.)

### 6. Sync check before merging
- `git -C ana add -A && git -C ana commit -qm wip; git -C ana push`, then in `bo/`: `git pull && python3 .agents/skills/team-build/scripts/sync_check.py`
- Evidence: the output lists `api/health.py` as Ana touching a file outside her slice. (If step 5's agent didn't create the file, mark this step "n/a".)

## Writing it up

Copy `examples/TEMPLATE.md` to `examples/runs/YYYY-MM-DD-<agent-a>-plus-<agent-b>.md` and fill it in.
