#!/usr/bin/env python3
"""Read-only process-status report over participating repos.

(rune-drift and PRD-lane visibility from PRD agreement-invoice-skills,
"Process guardrails".)

Prints one summary row per repo — BACKLOG.md schema status, .agentic.json
presence, current branch, dirty/clean tree, last commit date — followed
by indented detail lines listing each specs/ subfolder and which spec
documents it contains. Folders carrying only a prd.md (PRD-lane work)
appear like any other spec folder, so autonomous PRD work is visible
alongside starwave specs.

Drift flags per row:

- spec-gap          a specs/ subfolder has requirements.md but neither
                    design.md nor tasks.md
- rune-drift        a specs/** task file (tasks.md or tasks-*.md) fails
                    `rune list` parsing; the spec's detail line names the
                    failing file(s)
- backlog-drift     specs/BACKLOG.md fails rune's parser, its H2 phases
                    are not exactly Idea, Needs Spec, Outstanding, it has a
                    non-pending entry (including a nested subtask), or it
                    lacks a leading H1 title; the repo's detail line names
                    the reason. BACKLOG.md's absence is not drift — the
                    BACKLOG column reads `-`.
- no-agentic-json   .agentic.json missing

Strictly read-only against target repos: only `git --no-optional-locks -C
<repo>` porcelain reads (branch/status/log) are used, so not even the git
index is refreshed, and task files and BACKLOG.md are checked with `rune
list`, a pure parse. A missing repo path is reported on its row, never a
crash; a missing rune binary degrades to a per-repo warning detail line.

CLI: process_status.py [repo ...]. With no arguments it reports this repo
plus the checked-in default list below (resolved via ${HOME}, matching
align.py's path-portability conventions).

Python 3 stdlib only (Decision 12). Tests: tests/test_process_status.py.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Checked-in default list (Req 1): ${HOME}-anchored so the list stays
# portable across machines, expanded at run time.
DEFAULT_REPOS = (
    "${HOME}/repos/medata",
    "${HOME}/repos/netmap",
    "${HOME}/repos/tocs",
    "${HOME}/repos/rtob",
    "${HOME}/repos/localml",
    "${HOME}/repos/loshop",
)

# Spec documents tracked per specs/ subfolder (Req 2).
SPEC_DOCS = ("requirements.md", "design.md", "tasks.md", "smolspec.md",
             "prd.md")

# specs/BACKLOG.md H2 phases, in required order. "Idea"/"Needs Spec" hold
# captured entries; "Outstanding" is rebuilt from spec state on every
# /backlog run. All three must be present even when empty.
BACKLOG_PHASES = ["Idea", "Needs Spec", "Outstanding"]


def default_repos() -> list[Path]:
    """This repo first, then the checked-in default list."""
    return [REPO_ROOT] + [Path(os.path.expandvars(p)) for p in DEFAULT_REPOS]


# ---------------------------------------------------------------------------
# Collection (read-only)
# ---------------------------------------------------------------------------

def _git(repo: Path, *args: str):
    """Read-only git query; None when git fails (not a repo, no commits).

    --no-optional-locks stops even `status` from refreshing the index, so
    target trees stay bit-identical (Req 4).
    """
    proc = subprocess.run(
        ["git", "--no-optional-locks", "-C", str(repo), *args],
        capture_output=True, text=True)
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def _task_files(sub: Path) -> list:
    """tasks.md / tasks-*.md files anywhere under one specs/ subfolder."""
    return sorted(set(sub.rglob("tasks.md")) | set(sub.rglob("tasks-*.md")))


def _rune_parses(rune: str, path: Path):
    """Whether `rune list` parses the file (a read-only check).

    Returns True/False, or None when the binary could not be executed
    (vanished since the `shutil.which` probe) — never raises.
    """
    try:
        proc = subprocess.run([rune, "list", str(path)],
                              capture_output=True, text=True)
    except OSError:
        return None
    return proc.returncode == 0


def _backlog_status(rune: str, path: Path):
    """BACKLOG.md schema status: `"-"` (absent), `"ok"`, or `"drift"`,
    plus a reason string used in the detail line (None unless drifting).

    Hybrid check (Decision 7, Req 3.5) — each layer covers a hole the
    others miss:

    1. Parse gate (`_rune_parses`). A vanished/unusable rune binary is
       treated like the absent-file case — never checked, never drift.
    2. Phase set/order: raw-text scan of `## ` headings, right-trimmed,
       case-sensitive, must equal exactly ["Idea", "Needs Spec",
       "Outstanding"]. Raw scan rather than rune's JSON because an
       empty-but-valid backlog (the normal post-reconciliation state)
       has no PhaseMarkers at all. All three are required even when
       empty: "Outstanding" is rebuilt from spec state every run, so an
       absent phase means a stale file, not an idle one.
    3. Pending-only invariant via `rune list --format json` Stats:
       Pending must equal Total. Authoritative over a raw checkbox scan
       because rune counts nested subtask checkboxes a `^- \\[` scan
       would miss. The parse gate already ran, so fenced-content evasion
       of the raw scans is not possible.
    4. H1 presence: raw scan for a leading `# ` title.
    """
    if not path.is_file():
        return "-", None
    parsed = _rune_parses(rune, path)
    if parsed is None:
        return "-", None
    if not parsed:
        return "drift", "unparseable by rune"

    text = path.read_text()
    lines = text.splitlines()
    phases = [line[3:].rstrip() for line in lines if line.startswith("## ")]
    if phases != BACKLOG_PHASES:
        return "drift", f"phases {phases!r} != {BACKLOG_PHASES!r}"

    proc = subprocess.run([rune, "list", "--format", "json", str(path)],
                          capture_output=True, text=True)
    stats = json.loads(proc.stdout).get("Stats", {})
    if stats.get("Pending", 0) != stats.get("Total", 0):
        return "drift", "entries are not all pending"

    if not any(line.startswith("# ") for line in lines):
        return "drift", "missing H1 title"

    return "ok", None


def collect(repo_path) -> dict:
    """Gather every report column for one repo. Never raises for a missing
    or non-git path — the row reports the problem instead (Req 1, Req 4)."""
    repo = Path(repo_path)
    info = {
        "path": str(repo),
        "name": repo.resolve().name,  # stable even for "." or trailing "/"
        "exists": repo.is_dir(),
        "git": False,
        "backlog": "-",         # "-" (absent), "ok", or "drift"
        "backlog_reason": None,  # drift reason, for the detail line
        "agentic_json": False,
        "specs": {},           # subfolder name -> [present spec docs]
        "rune_drift": {},      # subfolder name -> [unparseable task files]
        "rune_missing": False,  # task files exist but rune is not on PATH
        "branch": None,
        "dirty": None,
        "last_commit": None,   # "YYYY-MM-DD"
    }
    if not info["exists"]:
        return info

    info["agentic_json"] = (repo / ".agentic.json").is_file()

    specs_dir = repo / "specs"
    if specs_dir.is_dir():
        rune = shutil.which("rune")
        backlog_path = specs_dir / "BACKLOG.md"
        if backlog_path.is_file() and rune is None:
            info["rune_missing"] = True
        else:
            info["backlog"], info["backlog_reason"] = _backlog_status(
                rune, backlog_path)
        for sub in sorted(p for p in specs_dir.iterdir() if p.is_dir()):
            info["specs"][sub.name] = [
                doc for doc in SPEC_DOCS if (sub / doc).is_file()]
            task_files = _task_files(sub)
            if task_files and rune is None:
                info["rune_missing"] = True
                continue
            failing = []
            for path in task_files:
                parsed = _rune_parses(rune, path)
                if parsed is None:
                    info["rune_missing"] = True
                elif not parsed:
                    failing.append(path.relative_to(sub).as_posix())
            if failing:
                info["rune_drift"][sub.name] = failing

    branch = _git(repo, "branch", "--show-current")
    if branch is not None:
        info["git"] = True
        info["branch"] = branch or "(detached)"
        info["dirty"] = bool(_git(repo, "status", "--porcelain"))
        info["last_commit"] = _git(repo, "log", "-1", "--format=%cs") or None
    return info


# ---------------------------------------------------------------------------
# Drift flags (Req 3)
# ---------------------------------------------------------------------------

def drift_flags(info: dict) -> list:
    """Drift conditions for one collected row, in report order."""
    if not info["exists"]:
        return []
    flags = []
    if any("requirements.md" in docs
           and "design.md" not in docs and "tasks.md" not in docs
           for docs in info["specs"].values()):
        flags.append("spec-gap")
    if info["rune_drift"]:
        flags.append("rune-drift")
    if info["backlog"] == "drift":
        flags.append("backlog-drift")
    if not info["agentic_json"]:
        flags.append("no-agentic-json")
    return flags


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

_HEADER = ("REPO", "BRANCH", "TREE", "COMMIT", "BACKLOG", "AGENTIC", "FLAGS")


def _yes_no(value) -> str:
    return "yes" if value else "no"


def _row(info: dict) -> tuple:
    if not info["exists"]:
        return (info["name"], "-", "-", "-", "-", "-", "missing-path")
    flags = drift_flags(info)
    return (
        info["name"],
        info["branch"] or "-",
        "-" if info["dirty"] is None else
        ("dirty" if info["dirty"] else "clean"),
        info["last_commit"] or "-",
        info["backlog"],
        _yes_no(info["agentic_json"]),
        ",".join(flags) or "-",
    )


def _details(info: dict) -> list:
    if not info["exists"]:
        return [f"path not found: {info['path']}"]
    lines = []
    if not info["git"]:
        lines.append(f"not a git repository: {info['path']}")
    if info["rune_missing"]:
        lines.append("warning: rune binary not found; "
                     "task-file parsing not checked")
    if info["backlog"] == "drift":
        lines.append(
            f"specs/BACKLOG.md: {info['backlog_reason']} [backlog-drift]")
    for name, docs in info["specs"].items():
        line = f"specs/{name}: {' '.join(docs) or '(no spec docs)'}"
        failing = info["rune_drift"].get(name)
        if failing:
            line += f" [rune-drift: {' '.join(failing)}]"
        lines.append(line)
    return lines


def render(infos) -> str:
    """One aligned summary row per repo, spec details indented beneath."""
    rows = [(_row(info), _details(info)) for info in infos]
    widths = [max(len(cell) for cell in column)
              for column in zip(_HEADER, *(row for row, _ in rows))]
    lines = ["  ".join(cell.ljust(width)
                       for cell, width in zip(_HEADER, widths)).rstrip()]
    for row, details in rows:
        lines.append("  ".join(cell.ljust(width)
                               for cell, width in zip(row, widths)).rstrip())
        lines.extend(f"    {detail}" for detail in details)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only process-status report over participating "
                    "repos (specs/git state, BACKLOG.md schema, and "
                    "drift flags).")
    parser.add_argument(
        "repos", nargs="*",
        help="repo paths to report on (default: this repo plus "
             + ", ".join(DEFAULT_REPOS))
    args = parser.parse_args(argv)
    paths = [Path(p) for p in args.repos] if args.repos else default_repos()
    print(render([collect(path) for path in paths]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
