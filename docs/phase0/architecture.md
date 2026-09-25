# HQ Office: architecture proposal

Grounded in `docs/context/plan.md`'s design principles and the reusable
pieces identified in `prior-art.md` and `agent-teams.md`. No code in this
phase; this is the shape phase 1/2 would build (see `mvp.md` for the cut).

## Components

### Floor UI
A read-only view (phase 1), then a task-input surface (phase 2), of every
team as an isometric platform, matching `img/ref-design-isometric-teams.jpg`:
one platform per team, agent count, a live/idle/waiting badge, an approval
count badge. A right panel lists tasks with status (pending, in progress,
waiting on approval, done), filterable, mirroring the "Restructure AI" demo's
sidebar badges (`references.md` section 4). Renders client-side; reads
state, never writes it directly (all writes go through the orchestrator or
the human approving in the queue).

### Orchestrator
The single persistent dispatcher. Per `plan.md`'s own gap analysis, this must
be a session or a script, never a subagent (a subagent cannot outlive the
call that spawned it, and HQ's rule is subagents cannot spawn subagents).
Concretely: a long-running `claude -p` loop (or a small Node/Python daemon
that calls `claude -p` per task) that reads the task queue, picks the next
task, resolves which team and which existing HQ agent should run it (from
the ~430-agent registry, not a new agent per task), and dispatches by
spawning that agent as its own `claude` process, matching munder-difflin's
"one agent, one real CLI process" model rather than the-office's in-process
SDK calls, specifically so CLAUDE.md, hooks, skills, and model routing apply
automatically.

### Workers
Each worker is an existing HQ agent (from the registry, `scripts/find.py`),
run as its own `claude` CLI process (a background session via `claude --bg`,
or a plain `claude -p` invocation for a one-shot task). Not a persistent Sims
character with its own memory; the "character" on the floor is a rendering of
that process's current state, sourced from Claude Code hooks (see event log
below).

### Task files and mailboxes
Borrowed directly from munder-difflin's `HIVE.md` pattern, adapted to drop
its two conflicts (auto-commit, second memory store). One JSON file per task
under a project-local (not brain) working directory, written via
temp-file-then-rename for atomicity:

```
office/
  tasks/<task-id>.json        # the task file (see contract below)
  events/log.jsonl            # append-only event log (see contract below)
  inboxes/<agent-name>.json   # optional, only if a task needs agent-to-agent
                               # handoff; most tasks need none
```

No `outbox/`, no per-agent `memory.md`. Handoff between agents happens by one
agent finishing a task and the orchestrator creating the next task in the
chain, reading the brain for anything that needs to persist. This is
deliberately thinner than munder-difflin's Hive: HQ does not need a
blackboard or a FIPA-style message schema for a single-orchestrator, mostly
one-agent-at-a-time system. Add mailboxes back only if phase 3 needs genuine
peer-to-peer coordination between two long-running agents.

### Approval queue
A subset of tasks, gated on `requires_approval: true` (see contract), shown
in the floor UI's right panel exactly like the "Restructure AI" reference's
per-item approval list: one Approve action per item, no "approve all" for
anything that leaves HQ or touches money, git `main`, or a mainnet action
(the explicit anti-pattern flagged in `references.md`). Internal, reversible
items (a brain note draft, a local file edit) can batch-approve; public or
irreversible ones cannot, enforced by a field on the task, not by UI
convention alone.

### Budget and kill switch
Per team, read from the existing `.claude/logs/usage.tsv` ledger (no new
cost-tracking system) plus a per-team cap file the orchestrator checks before
dispatching: if a team's spend this period exceeds its cap, the orchestrator
refuses new tasks for that team and surfaces it in the UI, rather than the
agent self-policing its own budget. The kill switch is a flag file per team
(`office/kill/<team>.flag`); its presence makes the orchestrator refuse to
dispatch to that team until removed. Both are enforced in the orchestrator's
dispatch loop, so a compromised or buggy agent cannot bypass its own budget
or revive itself past a kill switch.

### Event log
Append-only JSONL, one line per Claude Code hook firing
(`UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Notification`, `Stop`,
`SubagentStop`), the same event plane munder-difflin uses, with pixel-agents'
lesson applied from day one: hooks alone are not reliable enough to be the
only signal ("hook-based IPC failed... JSONL watching works" per
`~/HQ/PROJECTS/pixel-agents/CLAUDE.md:194`), so the floor UI's status also
polls each agent's own Claude Code JSONL transcript as a fallback, not as an
afterthought bolted on after hooks turn out to be flaky in practice.

### Brain as the only memory
No new memory store, no MemPalace-equivalent, no per-agent `memory.md`. Any
fact a task produces that should outlive the task goes to
`KNOWLEDGE_BASE/` through the existing note types (observation, decision,
hypothesis) via the existing `brain.sh` tooling, written by the agent that
did the work, exactly as it already does outside HQ Office. Task files
themselves are ephemeral (cleaned up once the task is done and anything worth
keeping is in the brain); they are working state, not memory.

## Data contracts

### Task file (`office/tasks/<task-id>.json`)

```json
{
  "id": "2026-09-26T10-15-00Z-a1b2",
  "team": "adtech",
  "agent": "tracking-audit",
  "model": "sonnet",
  "brief": "Audit the sGTM container on client X for consent propagation gaps",
  "requires_approval": true,
  "irreversible": false,
  "status": "pending",
  "dependencies": [],
  "budget_usd_cap": 2.0,
  "created_at": "2026-09-26T10:15:00Z",
  "result_ref": null
}
```

`status` moves through `pending`, `in_progress`, `waiting_approval`, `done`,
`failed`, `killed`. `irreversible` is what routes a task to the approval
queue as non-batchable, regardless of `requires_approval`, matching design
principle 3 exactly ("human before push to main, send, pay, publish,
mainnet"). `result_ref` points at a brain note path once the agent writes
one, not at task-local storage.

### Event (`office/events/log.jsonl`, one JSON object per line)

```json
{"ts":"2026-09-26T10:15:03Z","task_id":"2026-09-26T10-15-00Z-a1b2","agent":"tracking-audit","hook":"PreToolUse","tool":"Read","detail":"docs/gtm/container.json"}
```

Consumers (the floor UI) track their own read cursor into the file; the log
itself is never rewritten, only appended, so two readers never conflict and
a crash never loses history mid-write.

## Process model: local web app, not Electron

Recommendation: a local web app (a small server the orchestrator process
also runs, opened in a browser tab on localhost, LAN-reachable later for
phone access), not Electron. Reasons:

1. `plan.md` already states this preference explicitly ("local web app...
   rather than Electron"), and nothing in the prior-art review overturns it.
2. Both Electron prior-art repos (munder-difflin, the-office) carry real
   packaging costs that don't buy HQ anything it needs. Electron-specific
   files (`electron-builder.yml`, code signing, auto-update, per-OS installers
   per `the-office/README.md`) are entirely about shipping a desktop app to
   third parties. HQ Office has exactly one user; a browser tab has zero
   packaging cost and updates by refreshing.
3. `node-pty` (used by munder-difflin for real terminal panes) works the same
   from a Node backend serving a browser tab as it does from an Electron main
   process. Nothing about the "real CLI process" requirement needs Electron
   specifically; xterm.js in a browser tab, fed by the same backend over a
   WebSocket, gives the identical terminal experience.
4. Electron's main advantage over a local web app, native OS integration
   (menu bar, notifications, file dialogs), is not something `plan.md` asks
   for; alerts already go through `say` and PushNotification, both callable
   from a plain Node/Python backend with no Electron dependency.

## Mapping teams to Rad's domains

Direct application of `plan.md`'s roadmap section, one isometric platform per
existing domain, agents drawn from the existing ~430-agent registry rather
than invented per team:

| Team (floor platform) | Domain | Agents (existing registry) |
|---|---|---|
| Freelance / Compta | invoicing, accounting, fiscal | comptable, fiscaliste, controleur-fiscal, notaire (paperasse pack) |
| Career | job search, evaluation, writing | career-scanner, career-evaluator, career-writer, career-agent |
| AdTech | tracking, adserving, RGPD | taf-harness skills (tagging-plan, tracking-audit, sgtm-review, rgpd-audit, etc.) |
| Quant | rad-lab R&D, backtesting | radlab-agent |
| Research | RAG, veille, fact-checking | cherche, research, fact-checker, docs-lookup |
| HQ Ops | brain, automations, registry | brain-curator, continuous-learning, handoff-writer |

This is a read map for phase 1 (which teams and agents exist, what each is
doing right now), and a dispatch map for phase 2 (which team a new task
belongs to). No team is invented that doesn't already have agents doing that
work today.

## Enforcing the four design principles in code

Each principle becomes a specific mechanism in the orchestrator's dispatch
loop, not a line in a prompt an agent could ignore under pressure:

1. **One agent by default.** The orchestrator's task-creation step defaults
   to a single task with a single assigned agent. Fan-out (multiple tasks
   with the same `dependencies: []` parent) requires an explicit
   `parallel_group` field set by whoever created the task, so parallel work
   is an opt-in the orchestrator can log and budget for, not something an
   agent can trigger by simply calling the Agent tool more than once.
2. **Review by a different model.** A task's `status` cannot move directly
   from `in_progress` to `done`. It must pass through a `review_pending`
   state, and the review step's `model` field must differ from the
   producing task's `model` field; the orchestrator rejects a review task
   where both models match, so the check runs in code, not by convention.
3. **Human before the irreversible.** Enforced by the `irreversible` field
   on the task contract: the orchestrator refuses to mark such a task `done`
   without a corresponding approval record in the queue's own log, and the
   floor UI cannot batch-approve anything with that flag set. The kill
   switch and per-team budget cap (above) are the same kind of gate, checked
   before dispatch, not after the fact.
4. **One memory.** No task file, event log entry, or UI state is a place an
   agent is allowed to write durable facts. The orchestrator's own agent
   template (the boilerplate every dispatched task gets) tells the agent
   explicitly to write findings worth keeping to the brain, and nowhere
   else; there is simply no second memory store for it to write to instead.

## Diagram

```mermaid
flowchart TB
    Rad[Rad: briefs a task] --> UI[Floor UI]
    UI -->|create task| Orch[Orchestrator]
    Orch -->|check budget + kill switch| Gate{Budget OK?<br/>Not killed?}
    Gate -->|no| Blocked[Task blocked, surfaced in UI]
    Gate -->|yes| Dispatch[Spawn claude CLI process<br/>for the assigned agent]
    Dispatch --> Worker[Worker: existing HQ agent]
    Worker -->|hooks| EventLog[office/events/log.jsonl]
    Worker -->|reads/writes durable facts| Brain[(Obsidian brain, only memory)]
    Worker -->|task done| Review[Review: different model]
    Review -->|pass| Approval{Irreversible or public?}
    Review -->|fail| Orch
    Approval -->|yes| Queue[Approval queue: Rad approves item by item]
    Approval -->|no| Done[Task done]
    Queue -->|approved| Done
    EventLog --> UI
    Brain --> UI
```
