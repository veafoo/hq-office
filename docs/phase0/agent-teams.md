# Claude Code "agent teams" (experimental)

Sourced from the official docs, fetched live today (2026-09-26):
https://code.claude.com/docs/en/agent-teams and
https://code.claude.com/docs/en/sub-agents (the second URL is a 301 redirect
target of https://docs.claude.com/en/docs/claude-code/sub-agents). Also
checked the local CLI: `claude --version` reports `2.1.280 (Claude Code)`;
`claude --help` lists no `team` flag at all (confirmed by `grep -i team` on
the full help text). The docs say why: `--teammate-mode` "is experimental and
doesn't appear in `claude --help`," and teams are enabled through an
environment variable, not a CLI flag.

## What it is

One Claude Code session (the "lead") spawns other Claude Code sessions
("teammates"), each with its own context window, running independently.
Teammates message each other directly and share a task list; the lead
coordinates and synthesizes. It formalizes exactly what `plan.md` described
from the Instagram post ("headless, all the logic lives in files, orchestrator
is Claude using the experimental feature agent teams and also sub agents") as
an actual, documented product feature, not just a claim from a screenshot.

## How to enable it

Off by default. Turn it on with an environment variable, in `settings.json`
or the shell:

```json
{ "env": { "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" } }
```

Two side effects worth flagging for HQ:
1. Once enabled, Claude can name a subagent on its own, and any named subagent
   launches as a teammate, so a team can form even when nobody asked for one.
   To keep ordinary subagent delegation working as before, set the variable
   back to `0`.
2. Teammates only spawn in interactive sessions. In headless mode (`-p`,
   including Agent SDK sessions), a named subagent still runs as an ordinary
   subagent even with the flag on. That matters directly for HQ: today's
   automations run via `claude -p` + launchd, so agent teams would not
   activate there even if turned on globally.

## Architecture (from the docs)

| Component | Role |
|---|---|
| Team lead | the main session; spawns teammates, coordinates, synthesizes |
| Teammates | separate Claude Code instances, each its own context window |
| Task list | shared work items, three states (pending/in progress/completed), can depend on each other |
| Mailbox | one JSON file per agent at `~/.claude/teams/{team}/inboxes/{agent}.json` |

Team state lives under `~/.claude/teams/{team-name}/config.json` (runtime,
regenerated, never hand-edit) and `~/.claude/tasks/{team-name}/` (the task
list, persists locally across `/resume`, never uploaded). The team name is
derived from the session id (`session-<first 8 chars>`). Task claiming uses
file locking to avoid two teammates grabbing the same task.

Each teammate loads the same project context a normal session would
(CLAUDE.md, MCP servers, skills) plus the spawn prompt from the lead. It does
**not** inherit the lead's conversation history. Teammates message each
other and the lead through the mailbox; the lead does not need to poll, since
delivery and idle notifications are automatic.

## Versus subagents

The docs give a direct comparison table (`code.claude.com/docs/en/agent-teams`
under "Compare with subagents"):

| | Subagents | Agent teams |
|---|---|---|
| Context | own window, results return to caller | own window, fully independent |
| Communication | returns a result to the caller | teammates message each other directly |
| Coordination | main agent manages all work | self-coordination + shared task list |
| Best for | focused tasks, only the result matters | discussion, collaboration |
| Token cost | lower (summarized back) | higher (each teammate a full instance) |

Practical read for HQ: subagents are the right shape for "one agent by
default" (principle 1); agent teams are the right shape only for the narrow
case the docs themselves flag as worthwhile, breadth-first research, parallel
code review with different lenses, or competing-hypothesis debugging, none of
which map to HQ's steady-state need (routing a single briefed task to one
team's agents).

One correction to carry back to the HQ CLAUDE.md invariant "subagents cannot
spawn subagents": per `code.claude.com/docs/en/sub-agents`, ordinary subagents
**can** nest, up to a configurable depth (default 3 layers,
`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`), with the `Agent` tool withheld once
the limit is hit. What genuinely cannot nest is agent teams specifically:
"No nested teams: teammates cannot spawn their own teammates. Only the lead
can manage the team" (agent-teams doc, Limitations section). This is a
finding, not a change Claude is authorized to make to Rad's own operating
rule; flagging it for Rad to decide whether the CLAUDE.md wording should be
narrowed to "teams" specifically.

## Versus `claude -p` chains

Not a head-to-head the docs make explicitly, but it follows from the
architecture: a `claude -p` chain (A produces a file, a script or launchd
invokes B on that file, B produces a file for C) is external orchestration
with each step a completely fresh, isolated process, coordinated by whatever
drives the chain (a script, cron, launchd). Agent teams keep everything inside
one interactive session's process tree, coordinated by the lead session
itself via mailboxes and a task list, and require that session to stay open
and interactive. HQ's automation model (`claude -p` + launchd, headless, no
standing session) is structurally the `claude -p` chain pattern, and per the
docs' own headless-mode carve-out, agent teams do not engage there at all.

## Limits (verbatim from the docs' own "Limitations" section)

- No session resumption with in-process teammates: `/resume` and `/rewind` do
  not bring them back.
- Task status can lag: a teammate can fail to mark a task complete, blocking
  dependents.
- Shutdown can be slow: a teammate finishes its current tool call before
  exiting.
- One team per session, no additional named teams, no sharing a team across
  sessions.
- No nested teams (see correction above).
- No background subagents from an in-process teammate; a teammate's own
  subagent runs in the foreground only.
- The lead is fixed for the session's lifetime; no promoting a teammate to
  lead.
- Permission mode is set at spawn time per teammate and can be changed after,
  but not chosen per teammate at spawn time.
- Split-pane mode needs tmux or iTerm2 with the `it2` CLI; not supported in
  VS Code's integrated terminal, Windows Terminal, or Ghostty.

Cost: "agent teams use significantly more tokens than a single session," and
token usage scales roughly linearly with the number of active teammates
(their own guidance: start with 3 to 5 teammates, size tasks so 5 to 6 land
per teammate).

## Should HQ Office build on it

No, not as the standing orchestration layer, for three reasons grounded in
the doc itself rather than a guess:

1. It requires an interactive session and does not activate in headless mode.
   HQ's automations are headless by design (`claude -p` + launchd); building
   the persistent dispatcher on agent teams would mean keeping an interactive
   session open at all times, which is a different, heavier operating model
   than what HQ runs today.
2. Its stated sweet spot (breadth-first research, adversarial debugging,
   parallel code review) is explicitly the exception case for HQ too:
   `plan.md`'s design principle 1 is "one agent by default, fan out only when
   genuinely parallelisable." Agent teams are the right tool for that fan-out
   case specifically, not for routine single-task dispatch.
3. Token cost scales with team size and the docs recommend against using it
   for "routine tasks," which describes most of what HQ Office's phase 2
   dispatch would actually do (hand one briefed task to one team).

Where it likely fits later: as an optional escalation inside a team, when a
task genuinely needs adversarial investigation or multi-angle review, the
orchestrator could enable agent teams for that one sub-task rather than
building the whole dispatcher on top of it. That is a phase-3-or-later
refinement, not part of the phase-1/phase-2 MVP in `mvp.md`.

## What could not be verified

- Whether `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` is reachable/allowed in this
  sandboxed session's own settings was not tested (enabling it and spawning a
  live team was out of scope: the task brief says read-only research on this
  feature, no code, no dependencies). Everything above is read from the
  fetched docs and the local CLI's own help/version output, not from a live
  run.
- The Instagram reference's specific claim ("orchestrator is Claude using the
  experimental feature agent teams and also sub agents") cannot be verified
  beyond noting that the feature it names is real and matches the docs'
  description; there is no way to confirm that a public recruitment-agency
  post actually built on this exact feature rather than describing its own
  home-grown equivalent.
