#!/usr/bin/env python3
"""Generate office/floors.json: the central floors registry.

Deterministic, 0 model tokens. Per floor-per-project-revision.md § 3: one
floor per `~/HQ/PROJECTS/<name>/` directory, plus a fixed "hq" floor for
root-level work (brain, automations, registry) that belongs to no project
directory. Never hand-maintained, never written into a project directory
(taf-harness stays self-contained, Megakichta stays read-only).

Confidentiality is read from `~/HQ/.claude/hooks/confidential-projects.sh`
at generation time, never hardcoded here (same rule as hq-rag's
sources/brain.py). A confidential project gets no floor at all: not an
entry marked "excluded", just absent from the file, so no floor data, no
task, no event, no usage line anywhere in HQ Office ever names it.

Fields per floor: id (lowercase; directory casing varies, e.g. `Kyro` vs
`kyro`), dir (actual directory name, or null for "hq"), mode
("active" | "read_only" | "excluded"), cap_usd (per-floor budget cap; null
until a week of real usage has been measured, per Rad 2026-09-27 — never
guessed), domain (optional grouping tag, null by default: flat list for v1,
per Rad 2026-09-28).

Usage: python3 gen_floors.py [--out office/floors.json]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HQ_ROOT = os.path.expanduser("~/HQ")
PROJECTS_DIR = os.path.join(HQ_ROOT, "PROJECTS")
CONFIDENTIAL_SCRIPT = os.path.join(HQ_ROOT, ".claude", "hooks", "confidential-projects.sh")
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OVERRIDE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "floors_override.json")
DEFAULT_OUT = os.path.join(REPO_ROOT, "office", "floors.json")


def parse_confidential_projects(script_path: str = CONFIDENTIAL_SCRIPT) -> list[str]:
    """Same parser as hq-rag's sources/brain.py: read the bash array,
    never hardcode the list. Raises if the array itself is missing (a
    read error must not silently produce "nothing confidential")."""
    with open(script_path, encoding="utf-8") as f:
        content = f.read()
    m = re.search(r"CONFIDENTIAL_PROJECTS=\(([^)]*)\)", content)
    if not m:
        raise RuntimeError(f"CONFIDENTIAL_PROJECTS array not found in {script_path}")
    items = re.findall(r'"([^"]*)"|\'([^\']*)\'', m.group(1))
    return [a or b for a, b in items if (a or b)]


def load_overrides(path: str = OVERRIDE_FILE) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_floors() -> list[dict]:
    confidential = {p.lower() for p in parse_confidential_projects()}
    overrides = load_overrides()

    floors = [{
        "id": "hq",
        "dir": None,
        "mode": "active",
        "cap_usd": None,
        "domain": None,
    }]

    if not os.path.isdir(PROJECTS_DIR):
        raise RuntimeError(f"PROJECTS directory not found: {PROJECTS_DIR}")

    for name in sorted(os.listdir(PROJECTS_DIR)):
        path = os.path.join(PROJECTS_DIR, name)
        if not os.path.isdir(path) or name.startswith("."):
            continue
        fid = name.lower()
        if fid in confidential:
            continue  # no entry at all, not "mode: excluded" — see module docstring
        entry = {"id": fid, "dir": name, "mode": "active", "cap_usd": None, "domain": None}
        entry.update(overrides.get(fid, {}))
        floors.append(entry)

    return floors


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args()

    floors = build_floors()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"generated_by": "scripts/gen_floors.py", "floors": floors}, f, indent=2)
        f.write("\n")

    print(f"{len(floors)} floors written to {args.out}")


if __name__ == "__main__":
    main()
