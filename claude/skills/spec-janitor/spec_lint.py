#!/usr/bin/env python3
"""spec_lint.py - mechanical auditor for specs/ directories (spec-janitor).

Stdlib-only, runs on a stock Python 3. The normative rules (SJ-* identifiers)
live in references/spec-conventions.md, distributed alongside this script;
every rule ID emitted here exists there (pinned by a parity test).

Usage:
    spec_lint.py <repo-path> [--json] [--fix] [--fix-dirty]
    spec_lint.py <repo-path> exclude (--spec <spec-path> | --finding <finding-id>)
    spec_lint.py <repo-path> mark-raised --finding <finding-id>

Exit codes: 0 no findings (including a repo with no specs/, which prints a
notice); 1 findings exist; 2 usage or internal error. Consumers treat exit 1
as success-with-findings.

The JSON output (--json) matches the design schema for the spec-janitor
feature and additionally carries a "notices" list of human-report strings.
Without --fix / exclude / mark-raised the tool never writes anything.
"""

from __future__ import annotations

import datetime
import json
import random
import re
import shutil
import string
import subprocess
import sys
from pathlib import Path

VERSION = 1
STORE_NAME = ".janitor.json"

# Mechanical rules emitted by this auditor, with their repair dispositions.
# The disposition enum is closed: auto-fix | gated | detect-only.
RULES = {
    "SJ-MODE-001": "detect-only",
    "SJ-MODE-002": "detect-only",
    "SJ-MODE-003": "detect-only",
    "SJ-REF-001": "gated",
    "SJ-REF-002": "auto-fix",
    "SJ-TASK-001": "detect-only",
    "SJ-TASK-002": "auto-fix",
    "SJ-TASK-003": "detect-only",
}

BUGFIX_SECTIONS = (
    "Description of the Issue",
    "Investigation Summary",
    "Discovered Root Cause",
    "Resolution for the Issue",
    "Regression Test",
)

_ID_CHARS = string.ascii_lowercase + string.digits

_TASK_RE = re.compile(
    r"^- \[[ xX]\] (\d+)\. (.+?)(?:\s*<!-- id:([a-z0-9]{7}) -->)?\s*$"
)
_ATTEMPT_RE = re.compile(r"^[-*+] {0,2}\[")
_REQ_LINE_RE = re.compile(r"^\s+- Requirements?:\s*(.*\S)\s*$")
_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)#\s]+\.md)#([^)\s]+)\)")
_ANAME_RE = re.compile(r'<a\s+name="([^"]+)"')
_HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.M)
_H2_RE = re.compile(r"^##\s+(.+?)\s*$", re.M)


class SpecLintError(Exception):
    """Usage or internal error - maps to exit code 2."""


# --------------------------------------------------------------------------
# rune seams (module-level so tests can monkeypatch them)


def _rune_available():
    return shutil.which("rune") is not None


def _rune_list(path):
    """Run `rune list` on a task file. Returns (ok, error-text)."""
    proc = subprocess.run(
        ["rune", "list", str(path)], capture_output=True, text=True
    )
    err = (proc.stderr or proc.stdout).strip()
    return proc.returncode == 0, err


# --------------------------------------------------------------------------
# small helpers


def _excerpt(text):
    return text.strip()[:200]


def _kebab(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _heading_slug(heading):
    heading = re.sub(r"[^\w\- ]", "", heading.strip().lower())
    return heading.replace(" ", "-")


def _rel(repo, path):
    return path.relative_to(repo).as_posix()


class _FindingSet:
    """Findings keyed by id; identical ids merge into one finding with
    multiple evidence entries (design: finding model)."""

    def __init__(self):
        self._items = {}

    def add(self, rule, spec, file, subject, evidence_file, excerpt,
            demoted=False):
        fid = f"{rule}:{spec}:{file}:{subject}"
        item = self._items.get(fid)
        if item is None:
            item = {
                "id": fid,
                "rule": rule,
                "disposition": RULES[rule],
                "spec": spec,
                "subject": subject,
                "evidence": [],
                "fix_applied": False,
                "demoted": demoted,
            }
            self._items[fid] = item
        item["evidence"].append({"file": evidence_file, "excerpt": excerpt})
        return item

    def mark_fixed(self, fid):
        self._items[fid]["fix_applied"] = True

    def drop(self, ids):
        for fid in list(self._items):
            if fid in ids:
                del self._items[fid]

    def list(self):
        return sorted(self._items.values(), key=lambda f: f["id"])


# --------------------------------------------------------------------------
# discovery (janitor-owned: every leaf directory under specs/)


def _discover(specs_dir):
    leaves = []

    def walk(directory):
        subdirs = sorted(
            child for child in directory.iterdir()
            if child.is_dir() and not child.name.startswith(".")
        )
        if directory is not specs_dir and not subdirs:
            leaves.append(directory)
        for sub in subdirs:
            walk(sub)

    walk(specs_dir)
    return leaves


def _recognize_mode(names):
    if "requirements.md" in names and "design.md" in names:
        return "full"
    if "smolspec.md" in names:
        return "smol"
    if "prd.md" in names:
        return "prd"
    if "report.md" in names:
        return "bugfix"
    return None


# --------------------------------------------------------------------------
# task-file parsing


def _front_matter(lines):
    """Return (end_index, refs) where refs is a list of
    (line_index, indent, value) for references: entries; end_index is the
    line index of the closing --- or 0 when there is no front matter."""
    if not lines or lines[0].strip() != "---":
        return 0, []
    end = 0
    for j in range(1, len(lines)):
        if lines[j].strip() == "---":
            end = j
            break
    if end == 0:
        return 0, []
    refs = []
    in_refs = False
    for i in range(1, end):
        line = lines[i]
        if re.match(r"^references\s*:\s*$", line):
            in_refs = True
            continue
        if in_refs:
            match = re.match(r"^(\s+)-\s+(.+?)\s*$", line)
            if match:
                refs.append((i, match.group(1), match.group(2)))
            else:
                in_refs = False
    return end, refs


def _parse_tasks(lines, body_start):
    """Parse top-level task lines. Returns (tasks, violations) where tasks is
    a list of dicts (index, number, title, id, line) and violations is a list
    of (line_index, description, excerpt) structure problems."""
    tasks = []
    violations = []
    for i in range(body_start, len(lines)):
        line = lines[i]
        if _ATTEMPT_RE.match(line):
            match = _TASK_RE.match(line)
            if match:
                tasks.append({
                    "index": i,
                    "number": int(match.group(1)),
                    "title": match.group(2),
                    "id": match.group(3),
                    "line": line,
                })
            else:
                violations.append(
                    (i, "malformed task line", _excerpt(line))
                )
        else:
            req = _REQ_LINE_RE.match(line)
            if req and "](" not in req.group(1):
                violations.append(
                    (i, "plain-text requirement reference (must be a "
                        "markdown anchor link)", _excerpt(line))
                )
    return tasks, violations


def _anchors(path, cache):
    key = str(path)
    if key not in cache:
        text = path.read_text(encoding="utf-8", errors="replace")
        names = set(_ANAME_RE.findall(text))
        for heading in _HEADING_RE.findall(text):
            names.add(_heading_slug(heading))
        cache[key] = names
    return cache[key]


# --------------------------------------------------------------------------
# per-spec audit


def _audit_spec(repo, specs_dir, leaf, findings, rune_avail, anchor_cache,
                ops):
    spec = leaf.relative_to(specs_dir).as_posix()
    names = {f.name for f in leaf.iterdir() if f.is_file()}
    task_files = sorted(
        n for n in names
        if n == "tasks.md" or (n.startswith("tasks-") and n.endswith(".md"))
    )
    listing = ", ".join(sorted(names)) if names else "(empty folder)"

    if spec.startswith("bugfixes/"):
        _check_bugfix_shape(repo, leaf, spec, names, findings, listing)
    else:
        mode = _recognize_mode(names)
        if mode is None:
            findings.add(
                "SJ-MODE-001", spec, "-", spec,
                _rel(repo, leaf), f"no recognized primary document; contains: {listing}",
            )
        elif mode != "bugfix" and not task_files:
            findings.add(
                "SJ-MODE-002", spec, "-", "tasks.md",
                _rel(repo, leaf),
                f"{mode} spec has no tasks.md or tasks-<context>.md; "
                f"contains: {listing}",
            )

    for name in task_files:
        _audit_task_file(
            repo, leaf, spec, leaf / name, findings, rune_avail,
            anchor_cache, ops,
        )


def _check_bugfix_shape(repo, leaf, spec, names, findings, listing):
    report = leaf / "report.md"
    if "report.md" not in names:
        findings.add(
            "SJ-MODE-003", spec, "report.md", "report.md",
            _rel(repo, leaf),
            f"bugfix entry has no report.md; contains: {listing}",
        )
        return
    text = report.read_text(encoding="utf-8", errors="replace")
    sections = set(_H2_RE.findall(text))
    missing = [s for s in BUGFIX_SECTIONS if s not in sections]
    if missing:
        findings.add(
            "SJ-MODE-003", spec, "report.md", "report.md",
            _rel(repo, report),
            "report.md missing required sections: " + ", ".join(missing),
        )


def _audit_task_file(repo, leaf, spec, path, findings, rune_avail,
                     anchor_cache, ops):
    rel_path = _rel(repo, path)
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.split("\n")
    fm_end, refs = _front_matter(lines)
    body_start = fm_end + 1 if fm_end else 0

    # SJ-REF-002: references front-matter entries resolve from the repo root.
    for _, _, entry in refs:
        if (repo / entry).is_file():
            continue
        demoted = True
        if "/" not in entry:
            candidates = [
                f for f in leaf.iterdir() if f.is_file() and f.name == entry
            ]
            demoted = len(candidates) != 1
        item = findings.add(
            "SJ-REF-002", spec, path.name, entry,
            rel_path, f"references entry does not resolve from the repo "
            f"root: {entry}",
            demoted=demoted,
        )
        if not demoted and not any(o["fid"] == item["id"] for o in ops):
            ops.append({
                "kind": "ref", "fid": item["id"], "path": path,
                "spec": spec, "entry": entry,
            })

    # SJ-REF-001: markdown anchor links in the body.
    for i in range(body_start, len(lines)):
        for match in _LINK_RE.finditer(lines[i]):
            target_rel, fragment = match.group(1), match.group(2)
            subject = f"{target_rel}#{fragment}"
            target = (path.parent / target_rel).resolve()
            if not target.is_file():
                target = (repo / target_rel).resolve()
            if not target.is_file():
                findings.add(
                    "SJ-REF-001", spec, path.name, subject,
                    rel_path, _excerpt(lines[i]),
                )
            elif fragment not in _anchors(target, anchor_cache):
                findings.add(
                    "SJ-REF-001", spec, path.name, subject,
                    rel_path, _excerpt(lines[i]),
                )

    # SJ-TASK-001: structure violations.
    tasks, violations = _parse_tasks(lines, body_start)
    for _, description, excerpt in violations:
        findings.add(
            "SJ-TASK-001", spec, path.name, path.name,
            rel_path, f"{description}: {excerpt}",
        )

    # SJ-TASK-002: mixed stable-ID presence.
    marked = [t for t in tasks if t["id"]]
    unmarked = [t for t in tasks if not t["id"]]
    if marked and unmarked:
        item = None
        for task in unmarked:
            item = findings.add(
                "SJ-TASK-002", spec, path.name, path.name,
                rel_path, f"task without stable ID: {_excerpt(task['line'])}",
            )
        ops.append({"kind": "mint", "fid": item["id"], "path": path})

    # SJ-TASK-003: out-of-sequence numbering.
    expected = 1
    for task in tasks:
        if task["number"] != expected:
            findings.add(
                "SJ-TASK-003", spec, path.name, _kebab(task["title"]),
                rel_path, f"task numbered {task['number']}, expected "
                f"{expected}: {_excerpt(task['line'])}",
            )
        expected = task["number"] + 1

    # rune verification (Req 1.3): failures become SJ-TASK-001.
    if rune_avail:
        ok, err = _rune_list(path)
        if not ok:
            findings.add(
                "SJ-TASK-001", spec, path.name, path.name,
                rel_path, f"rune list failed: {_excerpt(err)}",
            )


# --------------------------------------------------------------------------
# exclusion store - specs/.janitor.json (Req 5)
#
# The exclude / mark-raised subcommands are the ONLY writers of the store;
# the audit path reads it and never writes. A corrupt store is backed up to
# .janitor.json.bak-<date> and rebuilt on the next subcommand write; an audit
# run reports the corruption prominently and ignores the store's content.


def _default_store():
    return {
        "version": 1,
        "exclude_specs": [],
        "exclude_findings": [],
        "raised": [],
        "last_run": None,
    }


def _valid_store(data):
    if not isinstance(data, dict) or data.get("version") != 1:
        return False
    for key in ("exclude_specs", "exclude_findings", "raised"):
        value = data.get(key)
        if not isinstance(value, list):
            return False
        if not all(isinstance(item, str) for item in value):
            return False
    last_run = data.get("last_run")
    return last_run is None or isinstance(last_run, str)


def _load_store(specs_dir):
    """Return (store, corrupt). A missing store is the default, not corrupt."""
    path = specs_dir / STORE_NAME
    if not path.is_file():
        return _default_store(), False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return _default_store(), True
    if not _valid_store(data):
        return _default_store(), True
    return data, False


def _backup_store(specs_dir):
    date = datetime.date.today().isoformat()
    backup = specs_dir / f"{STORE_NAME}.bak-{date}"
    counter = 2
    while backup.exists():
        backup = specs_dir / f"{STORE_NAME}.bak-{date}-{counter}"
        counter += 1
    shutil.copy2(specs_dir / STORE_NAME, backup)
    return backup


def _cmd_store_write(repo, command, args):
    spec = finding = None
    remaining = list(args)
    while remaining:
        arg = remaining.pop(0)
        if arg == "--spec" and remaining and command == "exclude":
            spec = remaining.pop(0)
        elif arg == "--finding" and remaining:
            finding = remaining.pop(0)
        else:
            raise SpecLintError(f"unknown argument for {command}: {arg}")
    if command == "exclude":
        if (spec is None) == (finding is None):
            raise SpecLintError(
                "exclude requires exactly one of --spec or --finding"
            )
    elif finding is None:
        raise SpecLintError("mark-raised requires --finding <finding-id>")

    specs_dir = repo / "specs"
    if not specs_dir.is_dir():
        raise SpecLintError(f"no specs/ directory in {repo}")

    store, corrupt = _load_store(specs_dir)
    if corrupt:
        backup = _backup_store(specs_dir)
        sys.stdout.write(
            f"WARNING: {STORE_NAME} was corrupt; backed up to "
            f"{backup.name} and rebuilt from this recording.\n"
        )
    if command == "exclude" and spec is not None:
        key, value = "exclude_specs", spec
    elif command == "exclude":
        key, value = "exclude_findings", finding
    else:
        key, value = "raised", finding
    if value not in store[key]:
        store[key].append(value)
    store["last_run"] = datetime.date.today().isoformat()
    assert _valid_store(store)
    (specs_dir / STORE_NAME).write_text(
        json.dumps(store, indent=2) + "\n", encoding="utf-8"
    )
    sys.stdout.write(f"recorded {key} entry: {value}\n")
    return 0


# --------------------------------------------------------------------------
# --fix pipeline (Req 3.2-3.4, 4.1-4.3)


def _dirty_specs(repo):
    """Return git's porcelain status for specs/ ('' when clean), or None
    when there is no git oracle (not a repo, git missing)."""
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain", "--", "specs/"],
            cwd=repo, capture_output=True, text=True,
        )
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def _mint_id(existing):
    while True:
        candidate = "".join(random.choice(_ID_CHARS) for _ in range(7))
        if candidate not in existing:
            return candidate


def _apply_ref_fix(op):
    """Rewrite a folder-relative references entry to the unique candidate's
    repo-relative path. Purely a retarget of the recorded entry."""
    path, entry, spec = op["path"], op["entry"], op["spec"]
    lines = path.read_text(encoding="utf-8").split("\n")
    _, refs = _front_matter(lines)
    changed = False
    for index, indent, value in refs:
        if value == entry:
            lines[index] = f"{indent}- specs/{spec}/{entry}"
            changed = True
    if not changed:
        raise RuntimeError(
            f"references entry disappeared between detection and fix: {entry}"
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def _apply_mint_fix(op):
    """Mint stable IDs for unmarked tasks only - purely additive."""
    path = op["path"]
    lines = path.read_text(encoding="utf-8").split("\n")
    fm_end, _ = _front_matter(lines)
    tasks, _ = _parse_tasks(lines, fm_end + 1 if fm_end else 0)
    existing = {t["id"] for t in tasks if t["id"]}
    changed = False
    for task in tasks:
        if task["id"]:
            continue
        new_id = _mint_id(existing)
        existing.add(new_id)
        lines[task["index"]] = (
            lines[task["index"]].rstrip() + f" <!-- id:{new_id} -->"
        )
        changed = True
    if changed:
        path.write_text("\n".join(lines), encoding="utf-8")


def _apply_fixes(findings, ops, notices):
    """Apply computed fixes in one pass, SJ-REF-002 before SJ-TASK-002.
    A mid-apply failure aborts the remainder; already-applied fixes stay
    reported."""
    ordered = sorted(
        ops, key=lambda op: (0 if op["kind"] == "ref" else 1, op["fid"])
    )
    for op in ordered:
        try:
            if op["kind"] == "ref":
                _apply_ref_fix(op)
            else:
                _apply_mint_fix(op)
        except Exception as exc:
            notices.append(
                f"fix aborted while applying {op['fid']}: {exc}; "
                "remaining fixes were not applied"
            )
            return
        findings.mark_fixed(op["fid"])
        notices.append(f"applied {op['fid']}")


# --------------------------------------------------------------------------
# audit entry point


def audit(repo_path, *, fix=False, fix_dirty=False):
    repo = Path(repo_path).resolve()
    if not repo.is_dir():
        raise SpecLintError(f"not a directory: {repo_path}")
    rune_avail = _rune_available()
    notices = []
    findings = _FindingSet()
    anchor_cache = {}
    specs_dir = repo / "specs"
    ops = []
    store = _default_store()
    if not specs_dir.is_dir():
        notices.append(
            "no specs/ directory found; nothing to audit"
        )
    else:
        store, corrupt = _load_store(specs_dir)
        if corrupt:
            notices.append(
                f"WARNING: specs/{STORE_NAME} is corrupt; exclusions are "
                "ignored for this run. The next exclude/mark-raised "
                "recording will back it up and rebuild it."
            )
        excluded_specs = set(store["exclude_specs"])
        for leaf in _discover(specs_dir):
            if leaf.relative_to(specs_dir).as_posix() in excluded_specs:
                continue
            _audit_spec(
                repo, specs_dir, leaf, findings, rune_avail, anchor_cache,
                ops,
            )
        suppressed = set(store["exclude_findings"]) | set(store["raised"])
        if suppressed:
            findings.drop(suppressed)
            ops = [op for op in ops if op["fid"] not in suppressed]
    if fix and ops:
        refusal = None
        if not fix_dirty:
            dirty = _dirty_specs(repo)
            if dirty is None:
                refusal = ("not a git repository; refusing --fix "
                           "(use --fix-dirty to override)")
            elif dirty:
                refusal = ("specs/ has uncommitted changes; refusing --fix "
                           "(use --fix-dirty to override)")
        if refusal:
            notices.append(refusal)
        else:
            _apply_fixes(findings, ops, notices)
    if not rune_avail:
        notices.append("rune verification skipped (rune not found on PATH)")

    data = {
        "version": VERSION,
        "repo": str(repo),
        "rune_available": rune_avail,
        "excluded": {
            "specs": sorted(store["exclude_specs"]),
            "findings": sorted(store["exclude_findings"]),
        },
        "findings": findings.list(),
        "notices": notices,
    }
    return data


# --------------------------------------------------------------------------
# reporting


def render_report(data):
    lines = [f"spec_lint report - {data['repo']}", ""]
    for notice in data["notices"]:
        lines.append(f"NOTE: {notice}")
    if data["notices"]:
        lines.append("")
    by_spec = {}
    for finding in data["findings"]:
        by_spec.setdefault(finding["spec"], []).append(finding)
    for spec in sorted(by_spec):
        lines.append(f"{spec}:")
        for finding in by_spec[spec]:
            tag = f"{finding['rule']} | {finding['disposition']}"
            if finding["demoted"]:
                tag += " | demoted"
            if finding["fix_applied"]:
                tag += " | fixed"
            lines.append(f"  [{tag}] {finding['subject']}")
            for entry in finding["evidence"]:
                lines.append(f"      {entry['file']}: {entry['excerpt']}")
        lines.append("")
    if data["excluded"]["specs"]:
        lines.append(
            "Excluded specs: " + ", ".join(data["excluded"]["specs"])
        )
    if data["excluded"]["findings"]:
        lines.append(
            "Excluded findings: " + ", ".join(data["excluded"]["findings"])
        )
    count = len(data["findings"])
    lines.append("No findings." if count == 0 else f"{count} finding(s).")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# CLI


USAGE = """\
usage: spec_lint.py <repo-path> [--json] [--fix] [--fix-dirty]
       spec_lint.py <repo-path> exclude (--spec <spec-path> | --finding <finding-id>)
       spec_lint.py <repo-path> mark-raised --finding <finding-id>
"""


def _main(argv):
    if not argv:
        sys.stderr.write(USAGE)
        return 2
    if argv[0] in ("-h", "--help"):
        sys.stdout.write(USAGE)
        return 0
    repo = Path(argv[0])
    if not repo.is_dir():
        raise SpecLintError(f"not a directory: {argv[0]}")
    rest = argv[1:]

    if rest[:1] == ["exclude"] or rest[:1] == ["mark-raised"]:
        return _cmd_store_write(repo, rest[0], rest[1:])

    json_out = fix = fix_dirty = False
    for arg in rest:
        if arg == "--json":
            json_out = True
        elif arg == "--fix":
            fix = True
        elif arg == "--fix-dirty":
            fix_dirty = True
        else:
            raise SpecLintError(f"unknown argument: {arg}")

    data = audit(repo, fix=fix, fix_dirty=fix_dirty)
    if json_out:
        sys.stdout.write(json.dumps(data, indent=2) + "\n")
    else:
        sys.stdout.write(render_report(data))
    return 1 if data["findings"] else 0


def main(argv=None):
    argv = list(sys.argv[1:]) if argv is None else list(argv)
    try:
        return _main(argv)
    except SpecLintError as exc:
        sys.stderr.write(f"spec_lint: error: {exc}\n")
        return 2
    except Exception as exc:  # internal error -> exit 2
        sys.stderr.write(f"spec_lint: internal error: {exc}\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
