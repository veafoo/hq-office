# MVP: phase 1 (read-only) then phase 2 (smallest useful dispatch)

Per `plan.md`'s own phase list ("1. Read-only office... 2. Dispatch: brief,
orchestrator, headless workers, results as files; budget + kill switch").
This file cuts each phase down to the smallest thing worth shipping and
estimates it in hours, on the assumption that build work (once phase 0 ends)
runs on Sonnet per the routing table, with an Opus audit pass at the end of
each phase.

## Phase 1: read-only office

### Screens
- The isometric floor: one platform per team (from `architecture.md`'s
  mapping table), agent count and a live/idle/waiting badge per platform,
  reading the event log's most recent state per agent.
- A team detail panel: click a platform, see its agents, each agent's
  current status and its last few event-log lines (a lightweight transcript
  tail, not the full JSONL).
- A backlog/automations panel: reads `KNOWLEDGE_BASE/registry/backlog.md` and
  `automations.md` as plain text, no new data model.
- A token panel: reads `.claude/logs/usage.tsv` directly, grouped by team
  using the mapping table; no new cost-tracking system.

### Data it reads
Existing files only: the agent/skill registry (`scripts/find.py`'s index),
`usage.tsv`, `KNOWLEDGE_BASE/registry/*.md`, and each running agent's own
Claude Code hooks output (piped to `office/events/log.jsonl` as specified in
`architecture.md`) plus a JSONL-transcript-polling fallback for when hooks
misfire, per the lesson from pixel-agents.

### What it must not do yet
- No task creation, no dispatch, no writing to any agent's working
  directory. The floor UI has zero write paths in phase 1; it is a pure
  reader, matching munder-difflin's own MVP scoping decision ("not an
  agent-to-agent message bus yet... viewer/controller" per `SPEC.md:12-16`).
- No approval queue actions (nothing to approve yet, since nothing is
  dispatched).
- No budget enforcement (nothing to gate yet); the token panel is read-only
  reporting, not a cap.
- No new agent definitions. Every agent shown on the floor already exists in
  the registry.

### Effort estimate
- Backend: read the four data sources above, expose them over a small local
  HTTP/WebSocket API. 8 to 12 hours.
- Frontend: isometric floor render (reusing pixel-agents' open asset
  pipeline as a reference, not its top-down tileset directly, since HQ's
  reference is isometric), team/agent panels, backlog and token panels. 16
  to 24 hours.
- Hooks wiring and the JSONL-fallback poller, tested against at least one
  real running agent. 6 to 10 hours.
- Opus audit pass against the four design principles and against this brief.
  2 to 3 hours.
- **Total: roughly 32 to 49 hours.**

## Phase 2: dispatch at the smallest useful scope

### Smallest useful scope
One text box in the floor UI ("brief a team"), one team selectable, the
orchestrator creates exactly one task (no fan-out in the first version),
dispatches it to one existing agent in that team as a real `claude -p`
process, and the result lands as a task file plus, if the agent judged it
worth keeping, a brain note. No mailboxes, no multi-agent handoff chains yet;
those are phase 3 additions per `plan.md`'s own phase list, not part of this
cut.

### What it adds over phase 1
- The task contract and event contract from `architecture.md`, implemented
  for real (not just documented).
- The orchestrator process: reads the task queue, checks budget cap and kill
  switch per team, dispatches, watches for completion via the same hooks/
  JSONL mechanism phase 1 already built for reading.
- The approval queue, but scoped to exactly the fields `architecture.md`
  defines (`requires_approval`, `irreversible`); no batch-approve UI for
  anything irreversible, per design principle 3.
- The kill switch as a flag file per team, checked by the orchestrator
  before every dispatch.

### What it must still not do
- No agent-to-agent messaging (a task either finishes or fails; chaining two
  tasks together is a human or orchestrator decision each time, not an
  automatic handoff).
- No auto-commit of anything, anywhere; any git action a dispatched agent
  might want to take goes through the same permission prompts and approval
  queue as everything else irreversible.
- No second memory store; the orchestrator's task template instructs the
  agent to write durable findings to the brain and nowhere else.

### Effort estimate
- Task/event contract implementation plus the orchestrator's dispatch loop
  (budget check, kill switch check, spawn, watch). 12 to 18 hours.
- Approval queue UI and its backing logic (irreversible-flag enforcement,
  no batch approve on flagged items). 8 to 12 hours.
- Wiring one real end-to-end task per team (six teams from the mapping
  table) to prove the loop actually works per team, not just in the
  abstract. 6 to 10 hours.
- Opus audit pass, specifically checking that principle 2 (different-model
  review) and principle 3 (human before irreversible) are enforced in code
  as designed, not just present in the UI copy. 2 to 3 hours.
- **Total: roughly 28 to 43 hours.**

## The five biggest risks

1. **Hooks are not reliable enough on their own.** Pixel-agents' own
   condensed notes report exactly this failure mode ("hook-based IPC failed,
   hooks captured at startup, env vars don't propagate") and shipped a JSONL
   polling fallback instead. Mitigation: build the JSONL-poll fallback in
   phase 1, not as a later patch; treat hooks as an optimization for
   latency, not the only source of truth.
2. **Scope creep toward munder-difflin's Hive (mailboxes, blackboard,
   MemPalace).** It is the most feature-complete prior art and it is
   tempting to port more of it than HQ actually needs, reintroducing the
   two things `plan.md` explicitly rejects (a second memory store, an
   auto-committing harness). Mitigation: the task/event contract in
   `architecture.md` is deliberately thinner than the Hive; resist adding a
   mailbox system until a real phase-3 use case needs peer-to-peer
   coordination, not before.
3. **The orchestrator itself becomes a always-on process that eats into
   Claude subscription limits**, the same concern `plan.md` raises about
   munder-difflin's own model (N parallel sessions, always-on orchestrator).
   Mitigation: phase 2's orchestrator should poll a queue on an interval
   (or run via launchd like every other HQ automation) rather than holding
   an interactive session open continuously; this also sidesteps agent
   teams' own headless-mode limitation (see `agent-teams.md`).
4. **Approval fatigue turning the queue into a rubber stamp.** The UI
   reference in `references.md` explicitly names "Approve all" as an
   anti-pattern to avoid; if phase 2 ships batch-approve too broadly, Rad
   stops reading what he's approving. Mitigation: the `irreversible` flag on
   the task contract is a hard gate the UI cannot route around, not a
   default users can weaken by clicking a checkbox.
5. **Under-verified claims about the reference features leaking into the
   design as fact.** Two things in `plan.md` are explicitly flagged
   unverified (the "15x tokens for multi-agent research" figure, the
   harnessmd.com rebrand); this study adds no new unverified claims to
   `architecture.md` or `mvp.md`, but a future contributor extending this
   design should re-check any number pulled from a blog post before wiring
   a budget cap or a team-size default around it. Mitigation: the budget
   caps and team-size guidance in this file cite the official agent-teams
   doc's own numbers (3 to 5 teammates, 5 to 6 tasks each) rather than a
   blog estimate, precisely to avoid this.
