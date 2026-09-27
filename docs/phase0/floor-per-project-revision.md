# Revision: one floor per HQ project (2026-09-28)

Revises `architecture.md` § "Components" and § "Mapping teams to Rad's domains"
(same branch). Does not replace `architecture.md`; the edits to apply there if Rad
validates are listed at the end. Input: Rad's proposal (floor = existing
`PROJECTS/<name>/`, one "boss" per floor under the global orchestrator, HQ Agency and
HQ Ecommerce become floors instead of separate offices).

## Verdict

**Holds, with reserves.** "Floor = project" is better than "team = hand-picked domain"
for one structural reason: a worker is a `claude` process, and the project directory is
its working directory, so the project's `CLAUDE.md`, project skills and brain folder
apply by construction. The domain mapping never said which directory a worker starts in.

**"One boss per floor" holds only as a policy and a queue lane of the single
orchestrator, not as an agent or a process.** As an LLM process it breaks principle 1
(details below), and it cannot be built with agent teams anyway.

**Services inside a floor (Rad, 2026-09-28): a grouping key, never a boss.** The
optional `service` field sits next to `project` in the task contract. It filters the UI
and the queue. It has no process, no LLM, no budget, no kill switch and no concurrency
lane of its own (§ 6).

## 1. Check against the four principles

**Principle 1: one agent by default. A floor boss process breaks it.**
- *Serial chain.* Each task would cross three LLM sessions in series: global boss
  (route) → floor boss (route or decompose) → worker. Two of the three do no work;
  they only route. That is the pattern `plan.md` § Design principles rejects: a
  chain where errors compound (5 steps at 95 % → 77 %), plus an extra cold start and
  its token cost per hop.
- *Hidden fan-out.* `architecture.md` § Enforcing, point 1, makes fan-out an explicit
  `parallel_group` field. The orchestrator logs it and budgets it. That gate only works
  if the orchestrator is the **only** thing that creates tasks. A floor boss that
  decomposes a brief, or calls the Agent tool N times, becomes a second task creator
  outside the gate. The fan-out then escapes the orchestrator's log, its budget check
  and its kill switch. This is the real problem, not a cosmetic one.
- *Floor = project does not break it by itself.* Principle 1 limits how many agents
  work on one task, not how many platforms are drawn. With a concurrency limit of 1 per
  floor by default, the floor model even gives principle 1 a simple mechanical form (see
  § 2).

**Principle 4: one memory. Floor = project fits better than domains.** The brain is
already partitioned by project: `KNOWLEDGE_BASE/projects/<p>/_overview.md`,
`brain.sh ls -p <project>`, per-project handoffs. The confidentiality rule is also keyed
on project names (`.claude/hooks/confidential-projects.sh`). A domain like "Quant" or
"Research" has no brain folder, so it would need a mapping the brain does not know.
There is one risk: a "boss" with its own notes ("what this floor knows"). That would be
a second memory. The floor manifest (§ 3) therefore holds configuration only (cap,
kill, mode), never facts.

**Principles 2 and 3: unchanged, slightly better.** The different-model review does
not depend on the floor model. A kill switch per project matches the actual blast
radius (one repo, one git history, one testnet or mainnet key) more closely than a
switch per domain.

## 2. What a floor boss must be

It must be **a role of the one orchestrator, filtered by project**, not a separate
process. Grounds:

1. `architecture.md` § Orchestrator: "the single persistent dispatcher". Every gate in
   § Enforcing (parallel_group, review model ≠ producer model, the irreversible flag,
   budget, kill) is checked in *its* dispatch loop. A second dispatcher per floor would
   need its own copy of every gate, or would bypass them.
2. `mvp.md` risk 3: an always-on orchestrator already eats into subscription limits.
   N floor processes multiply that by N. The Pro-plan constraint in the global config
   makes this binding, not theoretical.
3. Agent teams cannot model it. `agent-teams.md` notes: no nested teams (l. 88-89),
   one team per session (l. 116), no activation in headless `-p` (l. 37-40). A
   global lead with per-floor leads that have their own teammates is not possible.

Concretely, the "boss of floor X" is three things, none of them an LLM:
- **Its rules** = `PROJECTS/X/CLAUDE.md`, loaded by the worker because its cwd is the
  project. The project already has a boss's policy. Nothing new to write.
- **Its manifest** = one entry in a central floors registry (§ 3): cap, kill flag,
  mode.
- **Its lane** = the orchestrator's queue filtered on `project == X`. Default
  concurrency is **1 task in progress per floor**; more only through `parallel_group`.
  In the UI, the boss sprite renders this lane: next task, budget left, killed or not.

Routing gets cheaper, not more expensive. When Rad briefs from a floor (clicks the
platform, then types), the project is known deterministically. Only the agent remains
to pick, with `scripts/find.py` first (0 tokens), then the orchestrator LLM if needed.
The global LLM routing hop is only needed for a brief typed outside any floor.

Side correction to `architecture.md` § Orchestrator: it justifies "never a subagent"
with "HQ's rule is subagents cannot spawn subagents". `agent-teams.md` l. 86 (same
branch) and the global config say subagents *can* nest (default depth 3). HQ's choice
is instead that multi-step chains are driven by a session or a script, so each step is
audited. The conclusion stands; only the reason changes: a subagent cannot outlive its
caller, and chains are audited step by step.

## 3. Contract, budget, kill switch

**Task file: `team` → `project`, not both.** Two fields that must agree will drift.
`project` is the floor id and sets the worker's cwd:

```json
{
  "id": "2026-09-28T10-15-00Z-a1b2",
  "project": "rad-lab",
  "service": null,
  "agent": "radlab-agent",
  "model": "sonnet",
  "brief": "…",
  "requires_approval": false,
  "irreversible": false,
  "parallel_group": null,
  "status": "pending",
  "dependencies": [],
  "budget_usd_cap": 2.0,
  "created_at": "2026-09-28T10:15:00Z",
  "result_ref": null
}
```

`project: "hq"` = the HQ root (`~/HQ`): brain, automations, registry and research
work that belongs to no project directory. The former "HQ Ops" and most of "Research"
live there. A task has exactly one floor, the one it writes in. Reading another project
is allowed; multi-floor tasks are out of scope for phase 2.

**Floors registry** = `office/floors.json` in hq-office, **central, never a file dropped
into each project**. `taf-harness` must stay self-contained, `Megakichta` is read-only,
and the confidential project must stay untouched. The registry is generated by a
deterministic script (`ls PROJECTS/` + the confidential list + a small override file),
not maintained by hand. Per floor: `id` (lowercase), `dir`, `mode`
(`active` | `read_only` | `excluded`), `cap_usd`, optional `domain`.
The id/dir split is needed because the directory names and the brain folder names
differ in case: `PROJECTS/Kyro`, `Canis-Majoris`, `Wolfdogz` versus
`KNOWLEDGE_BASE/projects/kyro`, `canis-majoris`, `wolfdogz`.

**Budget per project: simpler to attribute, but it needs one ledger change.**
- Simpler: the dispatcher knows the cwd, so it knows the project. No domain map to keep
  in sync.
- The catch applies equally to the old design. `.claude/logs/usage.tsv` has no team or
  project column today (header: `timestamp automation label models input cache_creation
  cache_read output cost_usd duration_ms num_turns`). So `mvp.md`'s "token panel grouped
  by team" was not computable either. Fix: add a `project` column. Writers are
  `scripts/career-morning.sh`, `scripts/agency-triggers.py`, `scripts/auto_handoff.py`;
  the reader is `scripts/usage-report.py`. Old rows are backfilled with a fixed
  `automation → project` map. This touches HQ scripts outside hq-office, so it needs
  Rad's go.
- **A global cap comes first, per-floor caps second.** The binding limit is the
  subscription, which is shared by all floors (`plan.md` conflict 3). 20 floor caps can
  each be respected while the plan is exhausted. Default: one global cap, one default
  floor cap, overrides only where needed.
- Kill switch: `office/kill/<project>.flag`, plus `office/kill/_all.flag` for the global
  boss. Same check in the dispatch loop, before dispatch.

## 4. Roadmap: HQ Agency and HQ Ecommerce as floors

**Real gain.** There is no second office codebase. Orchestrator, approval queue, review
gate, budget and kill switch are all reused as they are. HQ Agency becomes
`PROJECTS/hq-agency/` with its own `CLAUDE.md`, and the same goes for HQ Ecommerce.
`plan.md`'s roadmap shrinks from "three offices" to "HQ Office phases 1-3, then new
floors". The order stays the same: neither floor can run before phase 2 dispatch
works. The gain is in architecture, not in schedule.

**What the floor model does not capture yet (to add, still not a separate office):**
1. **Spend outside Claude tokens.** Agency pays per use for Higgsfield, voice and
   Metricool. Ecommerce has ad spend and its reference image frames a "$5,000 token
   budget". A floor cap read only from `usage.tsv` would show Agency as cheap while it
   spends. The floor budget needs a second source (an external-spend ledger), otherwise
   its kill switch gives a false sense of control. Pricing figures in `plan.md` are
   still `UNVERIFIED:` (from blogs).
2. **Outcome metrics per floor.** Agency needs a UTM/attribution report; Ecommerce needs
   revenue and margin. The floor view shows activity and cost, not results. Add an
   optional read-only metrics panel per floor later. The Ecommerce reference's "Chief
   Intelligence Officer" agent is itself a floor-boss LLM: the same § 1 critique
   applies, and it should be a report, not an agent.
3. **Internal pipelines.** Agency's research → script → video → voice → assembly →
   approval → publish, and Ecommerce's departments, become task chains inside one floor.
   The orchestrator creates each next task, as `architecture.md` already specifies.
   Zones inside a floor are a UI detail, not a new concept.
4. If Agency ever becomes something sold to clients, living inside HQ ties it to Rad's
   brain and hooks. It would then have to be extracted, like taf-harness. Not a concern
   before that happens.

## 5. Risks and how the model handles them

- **Empty floors: floor ≠ team roster.** Of the 26 directories in `PROJECTS/`, one has
  its own agents (`prod-docu`, 2) and six have project skills (checked 2026-09-28).
  Almost all work is done by global agents (fact-checker, code-reviewer, …) visiting
  a project. So a floor shows **the agents working there now** (from the event log's
  cwd) plus the project's skills. The badge counts active agents, not a fixed roster.
  Otherwise the view would show 25 empty platforms.
- **Too many floors.** 26 directories, 15 with a `CLAUDE.md`, 13 with a brain folder;
  the reference image has 6 platforms. Rad wants "all visible at once": keep them all,
  but render the dormant ones (no recent activity, by a deterministic rule set in phase
  1) as a collapsed strip rather than full platforms. Optional `domain` tag to group
  floors into wings (Quant alone spans at least rad-lab and Wolfdogz per `plan.md`,
  plus the Megakichta family).
- **Confidential project (`vente-butte-pinson`).** `mode: excluded`, read from
  `confidential-projects.sh` at generation time and never hardcoded (same rule as
  hq-rag's `sources/brain.py`). No floor, no task, no event, no usage line in
  hq-office. Second leak path: a global worker running elsewhere may touch a path under
  the confidential directory, and hooks record tool paths. The event writer must drop
  any event whose cwd or path falls under an excluded project. A visible "locked" floor
  (files kept inside its own directory, UI showing only a lock) is at best phase 3, and
  only if Rad asks.
- **Read-only and protected projects.** `Megakichta` (canonical engine v10.2) →
  `mode: read_only`: visible, and it only accepts tasks that write nothing.
  `career-ops` (upstream push forbidden) is already covered by `irreversible`.
  `taf-harness`: no office file is written into it.

## 6. Services inside a floor

Rad's addition: a floor can hold several services, a level between the project and
the agents. Examples: `hq-rag` → ingestion/indexing vs retrieval/eval; a large AdTech
client floor → tracking vs reporting. That gives the proposed chain global boss → floor
boss → service → agents.

**Verdict: a service is a grouping key, not an active role.** It adds one optional
field, `service`, to the existing task contract. It is handled by the same single
orchestrator. It gets no boss, no process, no budget, no kill switch, and does not raise
the floor's concurrency.

Why not a service boss:
- § 1 applies again, one level deeper. A third routing hop per task makes the chain
  4 sessions long (3 of them routing only) and adds a third place where tasks can be
  created outside the `parallel_group` gate. Each extra boss level multiplies the
  chances of hidden fan-out; none of them does the work.
- **A service must not be a parallel lane either.** If each service got its own
  "1 task in progress" slot, a floor with 3 services would run 3 tasks at once by
  default. That is fan-out through configuration, which principle 1 forbids.
  Concurrency stays per floor (default 1); parallel work still requires
  `parallel_group`, whatever the services involved. hq-rag's own `CLAUDE.md` shows the
  concrete cost. An ingestion job (`embed_index.py`) and a retrieval query
  (`search.py --hybrid`) both write the `emb_cache` table in `index/hq.db`. The first
  time two writers ran at once, the precompute job crashed ("database is locked",
  2026-09-26). Two parallel service lanes on that floor would reproduce this incident
  by design.
- **Budget and kill switch stay at floor level.** The blast radius that justifies a
  kill switch is the repo, its git history and its keys: the project, not a sub-part of
  it. The risk a service might seem to need its own switch for is a public or
  irreversible action, for example a "reporting" service that emails a client. That is
  already covered per task by `irreversible` and the approval queue. A per-service cap
  would also split a budget that is already hard to attribute (§ 3). If Rad wants to see
  spend per service, it is a `GROUP BY` on the ledger, not a cap.

What a service is, concretely:
- An entry under its floor in `office/floors.json`: `name`, plus optional path globs
  (hq-rag: ingestion = `sources/`, `build_index.py`, `embed_index.py`; retrieval/eval =
  `search.py`, `rerank.py`, `eval/`). The value must be one declared for that floor, so
  it cannot drift into free text. Declared only where it helps: a floor with no services
  is the default.
- It is used for four things: a UI zone on the platform, a queue filter, a routing hint
  (`find.py` + the service's paths narrow the agent choice, at 0 tokens), and a
  path → service tag on events so the floor shows which part of the project is active.
  None of these writes state or makes a decision.
- **It is not an agent roster.** Agents stay global and visit the floor (§ 5). A
  service is a slice of the project's work, not a team of agents.

## 7. Edits to apply if Rad validates

- `architecture.md` § Floor UI: "one platform per team" → "per project floor (floors
  registry)"; badge = active agents.
- `architecture.md` § Orchestrator: fix the subagent justification (§ 2); add the
  per-floor lane and the default concurrency of 1.
- `architecture.md` § Budget and kill switch: per project + global cap + `_all.flag`;
  `usage.tsv` `project` column.
- `architecture.md` § Task file: `team` → `project`, add optional `service`, add
  `parallel_group` (already required by § Enforcing but missing from the example).
  State that services never create a concurrency lane, a budget or a kill switch.
- `architecture.md` § Mapping teams to Rad's domains: replace the table with the floors
  registry rule of § 3, `domain` as an optional grouping tag.
- `mvp.md` phase 1 token panel: grouped by `project`. Phase 2 "one real task per team
  (six teams)" → one real task on 4-6 active floors, including `hq`.
- `plan.md` § Our layer ("Teams = Rad's domains") and § Roadmap, plus `backlog.md`
  Ideas: Agency and Ecommerce = future floors.

## Open questions for Rad

1. Confidential project: fully absent (recommended) or a locked placeholder later?
2. OK to add a `project` column to `usage.tsv` (3 HQ scripts + the report)?
3. Keep an optional `domain` tag to group floors into wings, or a flat list?
   (Services are the level *below* a floor, domains the level *above*. Both are tags;
   neither gets a boss.)
