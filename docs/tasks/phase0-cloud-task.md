# CONTEXT
Repo: this one (hq-office), phase 0, no code. Read first, fully: `CLAUDE.md`,
`docs/context/plan.md`, `docs/context/references.md` (look at the images in `docs/context/img/`
it cites). Rad wants an "office of agents": an isometric floor showing every team (reference:
`img/ref-design-isometric-teams.jpg`), one orchestrator he briefs and that dispatches, an approval
queue, per-team budgets and a kill switch — built on Claude Code, with his rules (CLAUDE.md
design principles). His HQ today: ~430 agents/skills as markdown files with a `model:` alias,
automations run by `claude -p` + launchd, a token ledger TSV, an Obsidian brain.

# OBJECTIVE
A decision-ready study: what to reuse from prior art, and the architecture + MVP for HQ Office.

# DELIVERABLE (on a new branch `phase0-study`, files in `docs/phase0/`)
1. `prior-art.md` — clone and read (shallow, `git clone --depth 1`) these public repos:
   https://github.com/chaitanyagiri/munder-difflin (MIT, most advanced),
   https://github.com/shahar061/the-office (ISC),
   https://github.com/pablodelucca/pixel-agents.
   For each: architecture (processes, how an agent = a CLI process, IPC/mailboxes, router/
   orchestrator, memory, event log, git behaviour, UI stack and rendering), what is reusable for
   HQ Office, what conflicts with the design principles. Cite file paths + line ranges.
2. `agent-teams.md` — what Claude Code's "agent teams" feature is (experimental), how it is
   enabled, what it does and its limits, vs subagents and vs `claude -p` chains; whether HQ Office
   should build on it. Cite official docs URLs (docs.claude.com / code.claude.com). If the network
   allowlist blocks them, say so and mark claims `UNVERIFIED:`.
3. `architecture.md` — proposal: components (floor UI, orchestrator, workers, task files /
   mailboxes, approval queue, budget + kill switch, event log, brain as only memory), data
   contracts (task file format, event format), process model (local web app vs Electron:
   recommend one, with reasons), how teams map to Rad's domains (plan.md), how the 4 design
   principles are enforced in code, not just in prompts. One diagram (mermaid).
4. `mvp.md` — phase 1 = read-only office: screens, data it reads, what it must NOT do yet; then
   phase 2 dispatch at the smallest useful scope. Effort estimate per phase in hours, and the 5
   biggest risks with mitigations.
5. `SUMMARY.fr.md` — 15 lines max in French for Rad: recommendation, what we reuse, what we
   build, first 3 steps, open decisions for him (max 3).

# VALIDATION
- Every claim about a repo cites a file path; every claim about a Claude Code feature cites a URL
  or is marked `UNVERIFIED:`.
- The design principles in CLAUDE.md appear as enforcement mechanisms in `architecture.md`.
- No code, no dependencies, nothing outside `docs/phase0/`.

# SCOPE
Write only in `docs/phase0/` on branch `phase0-study`; push that branch. Never push to `main`,
never open or merge a PR yourself. No secrets. Clones of other repos go to /tmp, never committed.

# HONESTY
If a repo can't be cloned or a doc can't be reached, say so; don't fill gaps from memory. Say what
you skipped or are unsure about at the end of `SUMMARY.fr.md`.

# REPORT BACK
The branch name, the 5 files, and the SUMMARY.fr.md content.
