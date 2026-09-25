---
id: hq-office-plan
type: plan
project: hq-office
status: backlog
created: 2026-09-25
tags: [agents, orchestration, dashboard, multi-agent, design, munder-difflin, the-office]
---

# HQ Office: our own "office of agents" (Rad: later) — then HQ Agency, HQ Ecommerce

**Want (Rad, 2026-09-25):** an office view where he sees every agent at work, gives a task to ONE
agent and it dispatches. Built from zero, studying existing code, with HQ's safety layer and his
own design. Rad: "on fera plus tard".

**All references, fully transcribed (teams, workflows, files, UI):** `references` — keep, do not discard (Rad).

**Design reference:** ![](img/ref-design-isometric-teams.jpg) — Instagram post (instagram.com/p/DdRPD0RKhvG,
"6 Teams of AI Agents Helping Run This Agency", a recruitment agency): dark UI, isometric coloured
platforms, one per team with agent count; right panel "Task status" + task input; top bar with
agents and clock. Headless, "all the logic lives in files", orchestrator = Claude with the
experimental Claude Code **agent teams** feature + subagents (claim from the post, to verify).

## Prior art (checked via GitHub API, 2026-09-25)

| Repo | Licence | What to study |
|---|---|---|
| chaitanyagiri/munder-difflin (7.9 k★, created 2026-05-31, v0.4.6 pre-release) | MIT | Most advanced. Each agent = a real CLI process (claude, codex…) in node-pty; orchestrator "Michael" routes; atomic-file mailboxes (outbox → router → inbox), blackboard, append-only event log; kanban with dependencies, scheduled missions, Slack/webhooks. Own code (916 commits by author; not a fork). |
| shahar061/the-office (15★, 2026-03) | ISC | Same stack (Electron, PixiJS, TS), startup of agents via Claude Agent SDK, 4-phase pipeline. |
| pablodelucca/pixel-agents (9.4 k★, 2026-02; cloned in `PROJECTS/pixel-agents`) | — | First pixel office for Claude Code agents; visualisation only, no dispatch. |

Do NOT reuse: LimeZu *Modern Interiors* tiles (paid licence) — our isometric design avoids it.
Munder's download moved to harnessmd.com on 2026-09-17 (possible rebrand / paid tier; unverified).

## What conflicts with HQ in Munder (why not just install it)

1. Its own memory (per-agent markdown + "MemPalace") → a second memory next to the brain.
2. "Single-committer git": the harness commits → against "commit only when Rad asks"; would sweep
   uncommitted WIP (HQ, taf-harness).
3. N parallel Claude sessions + an always-on orchestrator → subscription hourly limits.
4. Pre-release; telemetry on by default (opt-out: Settings, `DO_NOT_TRACK`).

## Our layer (proposal)

- Brain = the only memory (confidential projects excluded). No MemPalace.
- Git read-only for agents: they propose commits, Rad validates; guard.py stays the gate.
- Each agent = a real `claude` process (so CLAUDE.md, hooks, skills, routing apply); model per
  agent from HQ's `model:` alias; token budget per team in `usage.tsv`; kill switch per team.
- Dispatch by a single orchestrator = separate processes, compatible with "subagents can't spawn
  subagents" (same pattern as `claude -p` chains). Use Claude Code agent teams if it already does it.
- Alerts: `say` / PushNotification only at decision points.
- Teams = Rad's domains: Freelance/Compta · Career · AdTech (taf-harness) · Quant (rad-lab, Wolfdogz)
  · Research (RAG, veille) · HQ Ops (brain, automations). Agents from the existing registry.
- Local web app (browser tab, later phone on LAN) rather than Electron; isometric render Pixi.js or
  Three.js; terminals xterm.js + node-pty.

## Reference model: generic multi-agent orchestration (techwith.ram infographic, 2026-09-25)

![](img/ref-multi-agent-orchestration.png) Loop: receive goal → plan & decompose → coordinate & execute
→ monitor & adapt → deliver. Roles: research, analysis, planning, execution, review; plus tools,
memory (short/long/shared) and evaluation. Its punchline fits HQ: "not more agents, better
orchestration" — HQ already has ~430 agents/skills; what it lacks is the loop and the view.

| Block | HQ today | Gap for HQ Office |
|---|---|---|
| Orchestrator | the main session (routing table) | a persistent dispatcher; must be a session or script, not a subagent |
| Plan & decompose | ad hoc, `Plan` agent | explicit task graph with dependencies, visible in "Task status" |
| Research / analysis / execution | docs-lookup, RAG, fact-checker · data-quality-monitor, career-evaluator · radlab-agent, web-builder, career-writer… | map each team's agents to these roles |
| Review | code-reviewer, fact-checker, verdict-synthesizer, Opus audit | make review a mandatory stage before "delivered" |
| Memory | context (short) · brain (long) · brain + RAG (shared) | none, by design: brain stays the only memory |
| Tools | skills, MCP, scripts | — |
| Monitor & adapt | automations.log, session-start hook | re-plan loop when a step fails or an audit rejects |
| Evaluation | usage.tsv (cost), eval sets (RAG recall@5), guard.py (safety) | per-agent quality over time (how often an output is corrected at audit) |

## Design principles (Rad validated, 2026-09-25)

Drawn from the critique of the generic model above: its linear 5-agent chain compounds errors
(5 steps at 95 % → 77 %) and multiplies cold starts and tokens (Anthropic reported multi-agent
research at ~15× the tokens of a chat, worth it only for parallelisable work — cited from memory,
to re-check); its review agent shares the producer's blind spots; its shared memory is a box that
hides the hard part; it has no human, budget or kill switch before an irreversible action.

1. **One agent by default.** The orchestrator hands a task to a single agent; it fans out only when
   the work is genuinely parallelisable (breadth research, independent files, several corpora).
2. **Review = deterministic gate first, then a different model** than the producer (tests, eval
   sets, detectors → then Opus/other). Never the same model reviewing itself.
   See `verificateur-non-verifie`.
3. **Human before the irreversible.** Any irreversible action (push, commit, send, pay, mainnet,
   booking) waits for Rad. Each team has a token budget and a kill switch.
4. **One memory: the brain**, with its rules (supersedes, verdict discipline, confidential
   exclusion). No per-agent or third-party memory store.

## UI reference: "Restructure AI — Social media OS" (demo screens shared by Rad, 2026-09-25)

Demo with fictional data (Glow Co., "Maya Collins"); figures are illustrative, nothing proves it runs.
Screens: ![](img/ref-ui-research.png) ![](img/ref-ui-research-why-it-worked.png) ![](img/ref-ui-content-approval.png)
![](img/ref-ui-community.png) ![](img/ref-ui-revenue.png) ![](img/ref-ui-morning-brief.png) · architecture diagram
![](img/ref-social-team-diagram.png) (4 teams: Research, Content Studio, Posting & Community, Growth;
Brain = Claude Code: triage, route, prioritise, check; "What interrupts the loop" = escalation events).

Patterns to reuse in HQ Office:
- Left sidebar = modules with a badge counting **what needs Rad** (8, 14, 178, 1); top "All agents
  running" + search (Ctrl K). Pairs with the isometric floor: floor = overview, modules = work views.
- Each module opens with a one-sentence insight banner and ONE handoff button to the next module
  ("Send to Content") — the file handoff between teams, made visible.
- Producer/checker pair shown on every item: "Claude writes · Jev checks", badges Passed / Fixed,
  toast "Rewritten and passed, re-check in 451 ms"; originality check vs the source ("same pattern
  kept 73 %, copied words 2 %") = principle 2 (different model reviews).
- Approval queue with per-item checks (on-brand score, no over-promise, original) before Approve.
- Explicit **never-automated** bucket: "39 need you personally — refunds, reactions, lost orders.
  Never auto-replied." = escalation rules made visible.
- Results over vanity: funnel views → followers → clicks → customers, "most liked post made $0";
  the nightly Claude Code cron shown as a terminal log; one-page morning brief at 7:00.

Do NOT copy:
- **"Approve all"** turns human approval into a rubber stamp. HQ: approve item by item for anything
  public; bulk approval only for internal items.
- DMs answered automatically with a price and a checkout link, lead pushed to HubSpot: outward
  messages sent without approval, contradicting their own "nothing public without the owner".
- Pseudo-precise confidence ("100 % sure · ready to buy 2.0/2").
- Last-click UTM attribution presented as truth: misses in-app browser/iOS losses, cross-device,
  view-through and dark social, so "made $0" can be false. This is Rad's expertise (server-side
  tracking, CAPI, attribution) — the differentiator if this ever becomes a freelance offer.

## Roadmap (Rad, 2026-09-25): HQ Office → HQ Agency → HQ Ecommerce — all parked

1. **HQ Office** — the learning ground: orchestration, dispatch, approval queue, per-agent review,
   budgets, on Rad's own domains. Everything below reuses what it teaches.
2. **HQ Agency** — a content team for **Rad's own** Insta/TikTok (Rad: "c'est pour moi").
   Pipeline sketched 2026-09-25: Claude = trend research + script + per-shot video prompts →
   **Higgsfield** as the test bench (one API for 50+ models: Kling 3.0, Seedance 2.5, Wan, MiniMax…;
   Soul ID = consistent own avatar; camera presets; lip-sync; pay-per-use API, subscriptions
   $9-129/mo) → voice = Rad's cloned voice (ElevenLabs or Voicebox) → assembly in **Remotion**
   (code-built video, 9:16, burned-in captions) → Rad approves each video → Metricool publishes →
   UTM/attribution report. Figures from blogs, to verify on official pages: Kling 3.0 ~$0.084/s
   direct vs ~$0.112/s via Higgsfield; Veo 3.1 = best overall + native audio ($0.03-0.50/s), Veo on
   Higgsfield unconfirmed; Sora 2 API shut down 2026-09-24. Limits: AI-content labelling on
   Insta/TikTok; fully generated video still looks generated → mix own avatar/voice + generated
   shots. Open questions for Rad: the account's topic; face (Soul ID avatar) / voice only / faceless.
   First test when resumed: one video end to end, same script on Kling vs Seedance (vs Veo).
3. **HQ Ecommerce** — idea: an agent org for an online store. Reference ![](img/ref-ecommerce-36-agents.png)
   ("36 AI agents for an e-commerce store on a $5,000 token budget"): owner sets goals, a "Chief
   Intelligence Officer" agent ties every department to revenue / margin / budget; departments
   Market Intelligence, Marketing, Sales & Conversion, Retention, Performance; shared knowledge
   layer, unified data, agent memory. Same critique as the other diagrams applies (36 agents ≠
   better; one agent by default, review by a different model, human before anything public).

## Phases (stakes 4/5: design Opus, build Sonnet, audit Opus)

0. Study: Munder + the-office architecture, verify "agent teams" → comparison note + architecture
   proposal (read-only).
1. Read-only office: visualises HQ as it is (teams, agents, running automations, backlog, tokens).
2. Dispatch: brief → orchestrator → headless workers → results as files; budget + kill switch.
3. In-app terminals, voice.

Open: project name (proposed `PROJECTS/hq-office`), web vs Electron confirmation.
