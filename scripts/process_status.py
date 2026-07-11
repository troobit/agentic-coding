#!/usr/bin/env python3
"""Read-only process-status report over participating repos.

(PRD: nextup-starwave-refinement, "Process status"; rune-drift and PRD-lane
visibility from PRD agreement-invoice-skills, "Process guardrails".)

Prints one summary row per repo — nextup.md presence, machine-zone marker
and newest note date, nextup.example.md / .agentic.json presence, current
branch, dirty/clean tree, last commit date — followed by indented detail
lines listing each specs/ subfolder and which spec documents it contains.
Folders carrying only a prd.md (PRD-lane work) appear like any other spec
folder, so autonomous PRD work is visible alongside starwave specs.

Drift flags per row:

- machine-zone      nextup.md missing, no machine-zone marker, or a zone
                    with no parseable `- YYYY-MM-DD — ...` note line
- stale-nextup      newest note older than 14 days while the tree is dirty
- spec-gap          a specs/ subfolder has requirements.md but neither
                    design.md nor tasks.md
- rune-drift        a specs/** task file (tasks.md or tasks-*.md) fails
                    `rune list` parsing; the spec's detail line names the
                    failing file(s)
- no-agentic-json   .agentic.json missing

The machine zone starts at the first line matching any known marker:
`<!-- LM -->`, legacy `<!-- ML -->`, `<!-- nextup:machine -->`, or the
`# What I want` heading.

Strictly read-only against target repos: only `git --no-optional-locks -C
<repo>` porcelain reads (branch/status/log) are used, so not even the git
index is refreshed, and task files are checked with `rune list`, a pure
parse. A missing repo path is reported on its row, never a crash; a
missing rune binary degrades to a per-repo warning detail line.

CLI: process_status.py [repo ...]. With no arguments it reports this repo
plus the checked-in default list below (resolved via ${HOME}, matching
align.py's path-portability conventions).

Python 3 stdlib only (Decision 12). Tests: tests/test_process_status.py.
"""

from __future__ import annotations

import argparse
import datetime
import os
import re
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

# Machine-zone markers, matched against stripped lines in file order;
# the first hit wins (Req 2).
MACHINE_MARKERS = (
    ("<!-- LM -->", "LM"),
    ("<!-- ML -->", "ML"),
    ("<!-- nextup:machine -->", "machine"),
    ("# What I want", "what-i-want"),
)

# Spec documents tracked per specs/ subfolder (Req 2).
SPEC_DOCS = ("requirements.md", "design.md", "tasks.md", "smolspec.md",
             "prd.md")

# A note line inside the machine zone: `- 2026-07-10 — did a thing`.
_NOTE_DATE_RE = re.compile(r"^-\s+(\d{4}-\d{2}-\d{2})\b")

STALE_NOTE_DAYS = 14


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


def _machine_zone(path: Path):
    """Return (zone_label, newest_note_date) for a nextup.md file.

    zone_label is None when no marker line exists; newest_note_date is the
    newest parseable ISO date on a note line at or after the marker (None
    when the zone carries no dated note — treated as malformed).
    """
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    start = label = None
    for index, line in enumerate(lines):
        stripped = line.strip()
        for marker, name in MACHINE_MARKERS:
            if stripped == marker:
                start, label = index, name
                break
        if start is not None:
            break
    if start is None:
        return None, None
    newest = None
    for line in lines[start + 1:]:
        match = _NOTE_DATE_RE.match(line.strip())
        if not match:
            continue
        try:
            found = datetime.date.fromisoformat(match.group(1))
        except ValueError:
            continue  # shaped like a date but not one (e.g. 2026-13-40)
        if newest is None or found > newest:
            newest = found
    return label, newest


def collect(repo_path) -> dict:
    """Gather every report column for one repo. Never raises for a missing
    or non-git path — the row reports the problem instead (Req 1, Req 4)."""
    repo = Path(repo_path)
    info = {
        "path": str(repo),
        "name": repo.resolve().name,  # stable even for "." or trailing "/"
        "exists": repo.is_dir(),
        "git": False,
        "nextup": False,
        "zone": None,          # marker label, e.g. "LM"
        "newest_note": None,   # datetime.date
        "example": False,
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

    nextup = repo / "nextup.md"
    info["nextup"] = nextup.is_file()
    if info["nextup"]:
        info["zone"], info["newest_note"] = _machine_zone(nextup)
    info["example"] = (repo / "nextup.example.md").is_file()
    info["agentic_json"] = (repo / ".agentic.json").is_file()

    specs_dir = repo / "specs"
    if specs_dir.is_dir():
        rune = shutil.which("rune")
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

def drift_flags(info: dict, today: datetime.date = None) -> list:
    """Drift conditions for one collected row, in report order."""
    if not info["exists"]:
        return []
    if today is None:
        today = datetime.date.today()
    flags = []
    if info["zone"] is None or info["newest_note"] is None:
        flags.append("machine-zone")
    elif (info["dirty"]
          and (today - info["newest_note"]).days > STALE_NOTE_DAYS):
        flags.append("stale-nextup")
    if any("requirements.md" in docs
           and "design.md" not in docs and "tasks.md" not in docs
           for docs in info["specs"].values()):
        flags.append("spec-gap")
    if info["rune_drift"]:
        flags.append("rune-drift")
    if not info["agentic_json"]:
        flags.append("no-agentic-json")
    return flags


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

_HEADER = ("REPO", "BRANCH", "TREE", "COMMIT", "NEXTUP", "ZONE", "NOTE",
           "EXAMPLE", "AGENTIC", "FLAGS")


def _yes_no(value) -> str:
    return "yes" if value else "no"


def _row(info: dict, today) -> tuple:
    if not info["exists"]:
        return (info["name"], "-", "-", "-", "-", "-", "-", "-", "-",
                "missing-path")
    flags = drift_flags(info, today)
    return (
        info["name"],
        info["branch"] or "-",
        "-" if info["dirty"] is None else
        ("dirty" if info["dirty"] else "clean"),
        info["last_commit"] or "-",
        _yes_no(info["nextup"]),
        info["zone"] or "-",
        info["newest_note"].isoformat() if info["newest_note"] else "-",
        _yes_no(info["example"]),
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
    for name, docs in info["specs"].items():
        line = f"specs/{name}: {' '.join(docs) or '(no spec docs)'}"
        failing = info["rune_drift"].get(name)
        if failing:
            line += f" [rune-drift: {' '.join(failing)}]"
        lines.append(line)
    return lines


def render(infos, today: datetime.date = None) -> str:
    """One aligned summary row per repo, spec details indented beneath."""
    rows = [(_row(info, today), _details(info)) for info in infos]
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
                    "repos (nextup/specs/git state plus drift flags).")
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
