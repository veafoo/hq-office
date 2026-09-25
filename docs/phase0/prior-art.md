# Prior art: three public repos

Cloned shallow (`git clone --depth 1`) into a scratchpad outside this repo, at
`/private/tmp/claude-501/-Users-radwanmezzi-HQ/ddfabc56-cbb4-463e-a46b-e8d3341a3db3/scratchpad/prior-art/`
(munder-difflin, the-office) plus the pre-existing local clone
`~/HQ/PROJECTS/pixel-agents` (read-only, not re-cloned). Commit hashes read at
clone time: munder-difflin `7de157f` (2026-09-26), the-office (default branch,
depth 1, no separate hash recorded), pixel-agents as already present locally.

---

## 1. chaitanyagiri/munder-difflin (MIT): most advanced

**What it is** (`SPEC.md:1-16`): an Electron desktop app that visualises and
controls **real `claude` CLI processes running in tmux panes**, "not a
replacement for the CLI... this app is a viewer/controller." 224 TypeScript
files under `src/`.

### Process model: one agent, one real CLI process
Each avatar maps to a `tmux {session}:{window}.{pane}` triple running an
actual `claude`/`codex`/etc. process (`SPEC.md:12-16, 45-63`). Two separate
data planes feed the UI (`SPEC.md:24-63`):
- Terminal plane: `tmux pipe-pane` tails raw bytes into a log file;
  `tmux send-keys` injects input. Byte-for-byte authentic terminal view.
- Event plane: Claude Code **hooks** (`UserPromptSubmit`, `PreToolUse`,
  `PostToolUse`, `Notification`, `Stop`, `SubagentStop`) POST JSON to a Unix
  domain socket (`~/.cth/events.sock`) via a small shim (`cth-hook`), driving
  the avatar state machine (walk to a "station" matching the tool in use).

### Orchestration / IPC: file-based mailboxes, single committer
Documented in `HIVE.md` as the design source of truth, and it **is actually
implemented** (`src/main/hive.ts`, 3494 lines; confirmed via
`grep -n "outbox|inbox|commit("`, hits at `hive.ts:7,11,705-706,763,988,1012,
1095,1120,1364,1373`, and `commit(): void` defined at `hive.ts:2750`):
- On-disk layout `hive/agents/<id>/{identity.md, memory.md, inbox/, outbox/,
  cursor.json}` (`HIVE.md:60-73`). One JSON file per message, atomic
  temp-file + `rename` (never a co-edited mailbox file).
- A **router** (the Electron main process) drains each agent's `outbox/`
  into recipients' `inbox/` (`HIVE.md:31-33, 76-81`).
- Single-writer-per-file / single committer: only the main process calls
  git; agents never do. Confirmed in code, `commit()` is a method on the
  main-process Hive class, called at every mutating step (`hive.ts:647`
  `this.commit('hive: init')`, `:763` on register, `:988` on role change,
  `:1012` on archive, `:1095` on rename, `:1120` on session change). Each
  agent also gets its own **git worktree**
  (`hive.ts:2926`: "defaults to true, giving the worker its own git worktree").
- **Message schema** (`HIVE.md:96-117`, FIPA-ACL-lite): `id, conversation,
  in_reply_to, from, to, act (request/inform/propose/query/agree/refuse/done),
  subject, body, hops, requires_reply, needs_human, created_at`. Anti-livelock:
  only request/query/propose obligate a reply; `hops` counter capped; a
  privileged "god" agent escalates past the cap or on `needs_human: true`.
- Autonomous loop: an agent drains its inbox via a `Stop` hook returning
  `{"decision":"block","reason":…}` to keep working, guarded by
  `stop_hook_active` against infinite loops (`HIVE.md:53-55`).
- Agents can self-spawn ephemeral workers by writing a JSON file to
  `spawn-requests/<id>.json` (objective + cwd; `isolate: true` default = own
  worktree), but a "hire" (a durable new agent role) requires human
  confirmation in the UI, so full autonomy is capped by design
  (`hive.ts:1484`).

### Memory
Markdown-first: per-agent `memory.md` + shared `board.md` blackboard
(single-scribe, edited only through the god agent to avoid conflicts),
optional SQLite FTS. An optional **MemPalace** semantic layer
(`src/main/memory.ts:2-12`) is a separate CLI (`mempalace init/mine/search/
wake-up`) that "degrades silently to no-op when the `mempalace` CLI isn't
installed, the markdown memory still works" (`memory.ts:8`). Explicitly
scoped out of v1 topic clustering in `MEMORY_GRAPH_SPEC.md:101,201` because
its retrieval is heuristic, not validated as semantic.

### UI stack
Electron + Pixi.js canvas (`package.json:55` `"pixi.js": "^8.5.1"`) for the
avatar floor, xterm.js + `node-pty` for the terminal pane
(`package.json:54` `"node-pty": "^1.0.0"`, plus a `postinstall` step patching
node-pty's ConPTY).

### Telemetry (plan.md's claim, verified)
`TELEMETRY.md:1-30` confirms telemetry is on by default, allowlisted events
only (`app_launched`, `agent_spawned`, `message_sent`, counts only, message
content "never read, measured, or hashed", etc.), disabled via `DO_NOT_TRACK`
or the app's own setting (`TELEMETRY.md:95-99`). No sign of the harnessmd.com
rebrand in the repo itself, that claim from `plan.md` stays unverified here.

### Reusable for HQ Office
- The two-plane split (structured events via hooks vs raw terminal bytes),
  directly applicable, HQ Office would use the same Claude Code hooks.
- Atomic-file mailbox pattern (temp+rename, one file per message), solves
  concurrent-write safety without a database.
- Message schema fields (`act`, `hops`, `requires_reply`, `needs_human`) are a
  clean, minimal vocabulary worth borrowing almost verbatim.
- "God agent surfaces to the human natively in his own Claude Code session,
  no separate approval queue" is one legitimate design (contrast with our
  plan's explicit approval-queue UI panel, see conflicts below).

### Conflicts with HQ's design principles
1. **Single committer, but the committer is the harness, not Rad.** HQ rule:
   "commit only when Rad asks." Munder's main process commits on every hive
   mutation automatically (init, register, role change, rename...). This
   would sweep or interleave with Rad's own uncommitted WIP if pointed at an
   HQ repo. Not reusable as-is; the pattern (single writer to avoid git lock
   corruption) is reusable, the auto-commit policy is not.
2. **Own memory (`memory.md` + optional MemPalace) is a second memory store**
   next to Rad's Obsidian brain. It violates principle 4 ("One memory: the
   brain"). Would need to be redirected entirely to brain writes, dropping
   MemPalace.
3. **N parallel `claude` processes + an always-on hive.** Plan.md's concern
   about subscription hourly limits is not verifiable from the repo (no
   rate-limit handling found in the files read), stays as Rad's own
   operational judgment, not a repo fact.
4. **Pre-release, v0.4.6.** API/on-disk formats (`HIVE.md`,
   `MEMORY_GRAPH_SPEC.md`) are explicitly "what we're building toward," not
   frozen; `SPEC.md:5-7` itself says "Code is the source of truth for what's
   built; [HIVE.md] is the source of truth for what we're building toward." So some of the mailbox/message-schema detail above may be ahead of what
   ships in `0.4.6`; treat the schema as a design reference, not a proven API.

---

## 2. shahar061/the-office (ISC): SDK-driven, phase pipeline

**What it is** (`README.md:1-15`): an Electron + React + PixiJS app that runs
a **project generator**: pitch an idea, and a four-phase pipeline (Imagine →
War Room → Build → Complete) produces docs, a plan, and committed code, with
agents visualised as pixel-art characters walking a Tiled-map office.

### Process model: agents are in-process SDK calls, not CLI processes
Dependency confirmed: `package.json:58`
`"@anthropic-ai/claude-agent-sdk": "^0.2.76"`. Agents are **markdown
definitions** under `agents/*.md` (e.g. `agents/team-lead.md:1-13`: YAML
frontmatter `name, description, model: inherit, color, allowedTools`, body =
system prompt), structurally identical to Claude Code's own subagent
definition format, but invoked here through the Agent SDK's `query()` inside
the Electron main process, not as separate `claude` CLI processes in ptys.
This is the key architectural difference from munder-difflin.

### Orchestration
`electron/orchestrator/phase-machine.ts` (76 lines) drives the four-phase
state machine; `electron/orchestrator/worker-pool.ts` (43 lines) is a plain
`Promise`-based concurrency-limited pool (`runPool(items, concurrency, fn)`)
used to run several engineer agents in parallel during Build, no IPC, no
mailboxes: since everything runs in-process, "communication" between agents
is just function calls and shared JS objects, with the router/orchestrator
persisting state to files (`tasks.yaml`, `plan.md`, per-phase docs).

### Memory / event log
No dedicated event log or blackboard found in the files read; state is the
docs and YAML artifacts on disk (`01-vision-brief.md` … `tasks.yaml`) plus a
kanban view. `README.md:33` "each acted artifact is idempotent: if you close
the app mid-imagine and come back, the orchestrator skips what's already on
disk", file presence is the resumability mechanism, not a separate log.

### Git behaviour
`README.md:52-54`: "Greenfield projects get an automatic git repo with one
commit per phase... Every restart creates an `office/iteration-N` backup
branch first." The harness commits automatically and frequently (also
confirmed in `agents/team-lead.md:29` "Frequent Commits: Every task ends with
a commit" as an instruction baked into the agent's own system prompt).

### UI stack
Electron, React 19, PixiJS 8, TypeScript, a Tiled map (`office.tmj`) for the
pixel-art office, sprite sheets reused across 15 roles (`README.md:114`).

### Reusable for HQ Office
- The phase-machine / worker-pool split is a clean, small pattern for "one
  agent by default, fan out only for genuinely parallel work" (principle 1):
  `runPool` with `concurrency` param is exactly the shape needed to cap
  fan-out.
- Idempotent artifacts-on-disk as the resume mechanism (no separate
  checkpoint DB) fits "one memory: the brain" if the artifacts are written
  under the brain instead of a project folder.
- Markdown agent definitions with YAML frontmatter (`allowedTools`, `model`)
  are structurally the same shape as HQ's existing ~430 agents/skills, no
  new format to invent.

### Conflicts with HQ's design principles
1. **Automatic, frequent commits** ("every task ends with a commit",
   backup branches on every restart) directly violates "commit only when Rad
   asks" and "human before anything irreversible." Not reusable as-is.
2. **In-process SDK execution** means agents do **not** run as real `claude`
   CLI processes, so HQ's CLAUDE.md, hooks, skills, and model-alias routing
   (which live in the CLI's config discovery, not the SDK by default) would
   need to be explicitly re-wired; it's not "free" the way munder-difflin's
   pty-spawned real CLI processes are. This matters for HQ Office's stated
   requirement ("each agent = a real `claude` process... so CLAUDE.md, hooks,
   skills, routing apply").
3. No explicit approval-queue / budget / kill-switch mechanism found in the
   files read (mockups are approved via a review dialog, but that is
   per-artifact, not a standing queue or a budget gate), principle 3 would
   need to be built from scratch, not adapted from here.

---

## 3. pablodelucca/pixel-agents (local clone, `~/HQ/PROJECTS/pixel-agents`):
visualisation only, no dispatch

Read from the existing local clone's `README.md` and `CLAUDE.md` (its own
condensed architecture reference), not re-cloned.

**What it is**: a VS Code extension (not a standalone app) that renders each
Claude Code **terminal** as an animated pixel-art character. "Right now it
works as a VS Code extension with Claude Code... purely observational... no
modifications to Claude Code are needed" (`README.md:27-29, 105-109`).

### Architecture
- **One agent = one VS Code terminal running `claude --session-id <uuid>`**
  (`CLAUDE.md:95`), tracked 1:1 by a webview character.
- **Dual-mode detection** (`CLAUDE.md:99-113`): a preferred **hooks mode**
  (11 Claude Code hook events posted to a local HTTP server discovered via
  `~/.pixel-agents/server.json`) with a **heuristic fallback** that polls the
  JSONL transcript file at `~/.claude/projects/<hash>/<session-id>.jsonl`
  every 500 ms when hooks aren't available or haven't fired yet.
- **No IPC between agents, no orchestrator, no dispatch**, explicitly out of
  scope today; the roadmap section (`README.md:129-146`) describes a desired
  future ("Kanban board... idle agents can pick up tasks autonomously") but
  that is **not built**: "we're actively working on the core module and
  adapter architecture that makes this possible."
- Sub-agents (Task tool) are visualised as separate linked characters
  (negative IDs), spawned on `agentToolStart` with a "Subtask:" prefix
  (`CLAUDE.md:129`), purely a rendering detail, not a coordination mechanism.

### Explicit lesson learned (from its own condensed notes)
`CLAUDE.md:194`: **"Hook-based IPC failed (hooks captured at startup, env
vars don't propagate). JSONL watching works"**, a directly transferable
warning for HQ Office if it plans to rely on hooks alone for the event plane;
a JSONL-polling fallback (as munder-difflin's terminal plane does with raw
bytes, and as pixel-agents does for status) should be budgeted for from the
start rather than treated as an edge case.

### UI stack
VS Code Webview API + esbuild (extension host), React 19 + Vite + Canvas 2D
(webview), BFS pathfinding for character movement, all furniture/character
assets shipped as open PNGs, explicitly **not** LimeZu (per its own asset
docs), consistent with HQ's licence constraint.

### Reusable for HQ Office
- The dual-mode hooks-with-JSONL-fallback pattern for status detection is the
  single most concrete, battle-tested piece of engineering here, worth
  reusing directly for HQ Office's "read-only office" phase (visualising
  agents without needing to modify them).
- Open, custom pixel-art asset pipeline (manifest.json per furniture item),
  avoids the LimeZu licence problem outright; could be a reference for HQ's
  own isometric asset format even though HQ's design reference
  (`ref-design-isometric-teams.jpg`) is isometric, not top-down.

### Conflicts with HQ's design principles
None found, it has no orchestrator, no memory store, no git behaviour, and
no dispatch, so none of the four principles are in tension with it. Its
narrowness (visualisation only) is exactly why it maps cleanly onto HQ
Office's phase-1 scope ("read-only office").

---

## Cross-repo comparison

| Axis | munder-difflin | the-office | pixel-agents |
|---|---|---|---|
| Agent = | real `claude`/`codex` CLI process (pty) | in-process Agent SDK call | real `claude` CLI (VS Code terminal), observed only |
| IPC | file-based mailboxes (inbox/outbox, atomic rename) | none (in-process function calls + files on disk) | none (no cross-agent comms at all) |
| Orchestrator | "god" agent + main-process router | phase-machine + worker-pool | none |
| Memory | markdown + optional MemPalace (semantic, optional) | files/artifacts on disk, no dedicated store | none |
| Git | main process auto-commits every hive mutation | auto-commit per phase + per task | not applicable |
| UI | Electron + Pixi.js + xterm.js/node-pty | Electron + React + PixiJS + Tiled map | VS Code webview + React + Canvas 2D |
| Licence | MIT | ISC | MIT |
| Closest to HQ's "real CLI process" requirement | yes | no | yes (but no dispatch) |
