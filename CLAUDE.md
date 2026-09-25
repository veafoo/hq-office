# hq-office — project instructions

HQ Office: Rad's own "office of agents" — an isometric view of every agent team at work, one
orchestrator that dispatches, an approval queue, budgets and a kill switch. It is the learning
ground before HQ Agency (content team) and HQ Ecommerce. Status: **phase 0 (study), no code yet.**

Context snapshot (source of truth = Rad's HQ brain, not this repo):
- `docs/context/plan.md` — need, prior art, conflicts, design principles, roadmap, phases.
- `docs/context/references.md` — every reference transcribed (teams, workflows, files, UI);
  images in `docs/context/img/`.

## Rules for any session in this repo (cloud sessions do not see Rad's global config)

- Language: internal docs in English; Rad reads French summaries.
- Design principles are non-negotiable (from `docs/context/plan.md`):
  1. One agent by default; fan out only for genuinely parallel work.
  2. Review = deterministic gate first, then a *different* model than the producer.
  3. Human approval before anything irreversible or public (push to main, send, pay, publish,
     mainnet); a token budget and a kill switch per team.
  4. One memory: Rad's brain (Obsidian vault, markdown + YAML frontmatter). No second memory store.
- Never invent facts about external tools (APIs, prices, features, licences): cite a URL or the
  file/line you read; otherwise write `UNVERIFIED:`.
- Licences: munder-difflin is MIT, the-office is ISC — study and quote with attribution only;
  never copy LimeZu tilesets (paid licence).
- Work on a branch; never push to `main`; no secrets in the repo; no new dependencies committed
  in phase 0.
- Stop and report instead of guessing when a step is blocked (e.g. network allowlist).
