#!/usr/bin/env python3
"""Per-repo alignment command (spec: toolset-agnostic-starwave, Req 5 & 6).

Fixes agentic drift in a target repo, in pipeline order:

1. JSON validity  - unparseable managed config backed up (.bak-<date>) and
   regenerated from canonical + manifest, with a warning that non-canonical
   entries may remain only in the backup.
2. Path portability - user-specific absolute paths (/Users/<name>/...) in
   managed JSON rewritten to $HOME-anchored forms - never a literal
   substitution of the current username.
3. MCP convergence - canonical-named server entries converged to
   mcp/servers.json; non-canonical entries preserved and reported
   (same writer as generate.py).
4. Stale-pack deletion - files under .github/agents/ whose SHA-256 matches
   any hash in scripts/stale-packs.json are deleted; anything else is left
   and reported. Zero matches with candidate files present warns (a
   near-miss must not silently no-op).
5. Cloud seeding (cloud_assets: true) - seeds .github/agents/prd.agent.md,
   .github/copilot-instructions.md, and .github/skills/prd/** with managed
   blocks; later runs converge only the block. A markerless pre-existing
   target is hand-written: reported and skipped, never overwritten.

Managed files only (design Data Models): .mcp.json, .vscode/mcp.json,
.agentic.json, .github/copilot-instructions.md, .github/agents/prd.agent.md,
.github/skills/prd/**, plus stale-pack files under .github/agents/.

First run with no .agentic.json: the manifest is inferred from default_for
rules and written, and the plan is reported WITHOUT applying - the user
reviews/commits the manifest and the next run (or --yes) applies.

CLI: align.py <repo-path> [--yes] [--cloud-mcp]. --cloud-mcp prints the
paste-ready cloud-agent MCP JSON (COPILOT_MCP_* secret names) and exits.

Python 3 stdlib only (Decision 12). Tests: tests/test_align.py.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

import agentic_lib as lib

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SERVERS_JSON = REPO_ROOT / "mcp" / "servers.json"
DEFAULT_STALE_PACKS_JSON = REPO_ROOT / "scripts" / "stale-packs.json"

MANAGED_JSON = (".mcp.json", ".vscode/mcp.json")
PRD_AGENT_REL = ".github/agents/prd.agent.md"

# A macOS home prefix like /Users/ronan; rewritten to $HOME (portable),
# never to the current user's own /Users/<name> (Req 5.1).
_USER_HOME_RE = re.compile(r"/Users/[^/]+")


class AlignError(Exception):
    """Fatal alignment problem (e.g. the target is not a git checkout)."""


class AlignReport:
    """Outcome of one align run (plan-only or applied)."""

    def __init__(self):
        self.applied = False
        self.changes = []    # dicts: "path" (repo-relative posix), "action"
        self.warnings = []
        self.skipped = []    # repo-relative paths of hand-written files
        self.preserved = []  # free-text reports of preserved entries/files


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _rel(path, base) -> str:
    try:
        return Path(path).relative_to(base).as_posix()
    except ValueError:
        return str(path)


def _harvest(log: list, base: Path, report: AlignReport) -> None:
    """Sort agentic_lib report strings into the AlignReport buckets."""
    for entry in log:
        path_str, _, rest = entry.partition(": ")
        rel = _rel(path_str, base)
        if "exists without agentic markers" in entry:
            report.skipped.append(rel)
        elif "invalid JSON" in entry:
            report.warnings.append(f"{rel}: {rest}")
        elif "preserved non-canonical entries" in entry:
            report.preserved.append(f"{rel}: {rest}")
        else:  # created / updated / managed block rewritten
            report.changes.append({"path": rel, "action": rest})


def _fix_user_paths(value):
    """Recursively rewrite /Users/<name> prefixes in strings to $HOME."""
    if isinstance(value, str):
        return _USER_HOME_RE.sub("$HOME", value)
    if isinstance(value, list):
        return [_fix_user_paths(item) for item in value]
    if isinstance(value, dict):
        return {key: _fix_user_paths(item) for key, item in value.items()}
    return value


def _managed_block_of(text: str, src: Path) -> str:
    if lib.BEGIN_MARKER not in text or lib.END_MARKER not in text:
        raise AlignError(f"seed source {src} lacks agentic markers")
    _, _, rest = text.partition(lib.BEGIN_MARKER)
    block, _, _ = rest.partition(lib.END_MARKER)
    return block.strip("\n")


# ---------------------------------------------------------------------------
# Pipeline steps (each reports per file; `repo` may be the plan shadow copy)
# ---------------------------------------------------------------------------

def _fix_json_validity(repo: Path, report: AlignReport) -> None:
    """Step 1: back up unparseable managed JSON; step 3 regenerates it."""
    log = []
    for rel in MANAGED_JSON:
        path = repo / rel
        if not path.is_file():
            continue
        try:
            json.loads(path.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            lib._backup(path, log,
                        "invalid JSON - regenerated; non-canonical entries "
                        "may remain only in the backup")
            path.unlink()
    _harvest(log, repo, report)


def _fix_path_portability(repo: Path, report: AlignReport) -> None:
    """Step 2: portable command/path forms in managed JSON (Req 5.1)."""
    for rel in MANAGED_JSON:
        path = repo / rel
        if not path.is_file():
            continue
        data = json.loads(path.read_text())  # valid after step 1
        fixed = _fix_user_paths(data)
        if fixed != data:
            lib._write_json(path, fixed)
            report.changes.append({
                "path": rel,
                "action": "rewrote user-specific absolute paths to "
                          "portable $HOME forms",
            })


def _converge_mcp(repo: Path, manifest: dict, defs: dict,
                  report: AlignReport) -> None:
    """Step 3: converge canonical entries, preserve the rest (Req 4.5)."""
    log = []
    lib.generate_repo_configs(repo, defs, manifest.get("servers", []), log)
    _harvest(log, repo, report)


def _delete_stale_packs(repo: Path, stale_packs: dict,
                        report: AlignReport) -> None:
    """Step 4: delete .github/agents files matching a known stale hash."""
    agents_dir = repo / ".github" / "agents"
    if not agents_dir.is_dir():
        return
    known = {value for hashes in stale_packs.get("packs", {}).values()
             for value in hashes}
    matched, unmatched = [], []
    for path in sorted(agents_dir.iterdir()):
        rel = _rel(path, repo)
        if not path.is_file() or rel == PRD_AGENT_REL:
            continue  # align's own seed target is not a stale-pack candidate
        if _sha256(path) in known:
            path.unlink()
            matched.append(rel)
            report.changes.append(
                {"path": rel, "action": "deleted stale agent-pack file"})
        else:
            unmatched.append(rel)
            report.preserved.append(
                f"{rel}: no stale-pack checksum match, left in place")
    if unmatched and not matched:
        report.warnings.append(
            ".github/agents has files but zero stale-pack checksum matches "
            f"({', '.join(unmatched)}); check scripts/stale-packs.json for "
            "a missing hash")


def _seed_cloud_assets(repo: Path, seed_root: Path,
                       report: AlignReport) -> None:
    """Step 5: seed repo-level Copilot assets with managed blocks (Req 6.1)."""
    pairs = [
        (seed_root / "copilot" / "agents" / "prd.agent.md",
         repo / ".github" / "agents" / "prd.agent.md"),
        (seed_root / "copilot" / "instructions" / "copilot-instructions.md",
         repo / ".github" / "copilot-instructions.md"),
    ]
    skills_src = seed_root / "claude" / "skills" / "prd"
    if skills_src.is_dir():
        for src in sorted(p for p in skills_src.rglob("*") if p.is_file()):
            pairs.append((src, repo / ".github" / "skills" / "prd"
                          / src.relative_to(skills_src)))
    for src, dst in pairs:
        _seed_file(src, dst, repo, report)


def _seed_file(src: Path, dst: Path, repo: Path, report: AlignReport) -> None:
    rel = _rel(dst, repo)
    seed_text = src.read_text()
    if not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)  # verbatim: markers plus any front matter
        report.changes.append({"path": rel, "action": "seeded"})
        return
    existing = dst.read_text()
    if lib.BEGIN_MARKER not in existing or lib.END_MARKER not in existing:
        report.skipped.append(rel)  # hand-written: never overwritten
        return
    block = _managed_block_of(seed_text, src)
    if lib.write_managed(dst, block, []):
        report.changes.append(
            {"path": rel, "action": "managed block converged to seed"})


def _align_repo(repo: Path, manifest: dict, defs: dict, stale_packs: dict,
                seed_root: Path, report: AlignReport) -> None:
    _fix_json_validity(repo, report)
    _fix_path_portability(repo, report)
    _converge_mcp(repo, manifest, defs, report)
    _delete_stale_packs(repo, stale_packs, report)
    if manifest.get("cloud_assets"):
        _seed_cloud_assets(repo, seed_root, report)


# ---------------------------------------------------------------------------
# Manifest handling
# ---------------------------------------------------------------------------

def _infer_manifest(repo: Path, defs: dict) -> dict:
    """First-run inference from default_for rules ("*" = always; otherwise
    marker-file globs against the repo root). cloud_assets defaults to
    False - seeding .github/ stays an explicit opt-in."""
    servers = []
    for name in sorted(defs):
        for rule in defs[name].get("default_for", []):
            if rule == "*" or next(iter(repo.glob(rule)), None) is not None:
                servers.append(name)
                break
    return {"servers": servers, "cloud_assets": False}


def _shadow_copy(repo: Path, shadow: Path) -> None:
    """Copy only the managed file set so a plan run has no side effects."""
    shadow.mkdir(parents=True)
    for rel in MANAGED_JSON:
        src = repo / rel
        if src.is_file():
            dst = shadow / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    github = repo / ".github"
    if github.is_dir():
        shutil.copytree(github, shadow / ".github")


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------

def run(repo_path, *, assume_yes=False, servers_json=None,
        stale_packs_json=None, seed_root=None) -> AlignReport:
    """Align one repo. See the module docstring for the pipeline."""
    repo = Path(repo_path)
    if not (repo / ".git").exists():
        raise AlignError(
            f"{repo} is not a git checkout; align refuses to touch "
            "non-git directories")

    defs = lib.load_servers(servers_json or DEFAULT_SERVERS_JSON)
    stale_packs = json.loads(
        Path(stale_packs_json or DEFAULT_STALE_PACKS_JSON).read_text())
    seed_root = Path(seed_root or REPO_ROOT)

    report = AlignReport()
    manifest_path = repo / ".agentic.json"
    first_run = not manifest_path.exists()
    if first_run:
        manifest = _infer_manifest(repo, defs)
        lib._write_json(manifest_path, manifest)
        report.changes.append({
            "path": ".agentic.json",
            "action": "created (manifest inferred from default_for rules)",
        })
    else:
        try:
            manifest = json.loads(manifest_path.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise AlignError(
                f"{manifest_path}: manifest is not valid JSON: {exc}"
            ) from exc

    unknown = sorted(set(manifest.get("servers", [])) - set(defs))
    if unknown:
        raise AlignError(
            f"unknown server name(s) in .agentic.json: {', '.join(unknown)}; "
            f"canonical names: {', '.join(sorted(defs))}")

    if first_run and not assume_yes:
        # Plan-only: run the pipeline against a shadow copy so the report
        # lists the pending fixes while nothing but the manifest changes.
        with tempfile.TemporaryDirectory(prefix="align-plan-") as tmp:
            shadow = Path(tmp) / "repo"
            _shadow_copy(repo, shadow)
            _align_repo(shadow, manifest, defs, stale_packs, seed_root,
                        report)
        report.applied = False
        return report

    _align_repo(repo, manifest, defs, stale_packs, seed_root, report)
    report.applied = True
    return report


def _print_report(report: AlignReport) -> None:
    if report.applied:
        print(f"align: applied {len(report.changes)} change(s)")
    else:
        print(f"align: plan only - {len(report.changes)} pending change(s); "
              "review/commit .agentic.json, then re-run (or use --yes)")
    for change in report.changes:
        detail = f" ({change['detail']})" if "detail" in change else ""
        print(f"  {change['path']}: {change['action']}{detail}")
    for warning in report.warnings:
        print(f"warning: {warning}")
    for path in report.skipped:
        print(f"skipped (hand-written, no agentic markers): {path}")
    for item in report.preserved:
        print(f"preserved: {item}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Align a repo's agentic config with the canonical "
                    "sources (MCP servers, stale packs, cloud assets).")
    parser.add_argument("repo", help="path to the target git repo")
    parser.add_argument("--yes", action="store_true",
                        help="apply immediately, even on a first "
                             "(manifest-inferring) run")
    parser.add_argument("--cloud-mcp", action="store_true",
                        help="print paste-ready cloud-agent MCP JSON with "
                             "COPILOT_MCP_* secret names, then exit")
    parser.add_argument("--servers-json", type=Path, default=None,
                        help=f"canonical MCP definitions "
                             f"(default: {DEFAULT_SERVERS_JSON})")
    parser.add_argument("--stale-packs-json", type=Path, default=None,
                        help=f"stale-pack checksums "
                             f"(default: {DEFAULT_STALE_PACKS_JSON})")
    parser.add_argument("--seed-root", type=Path, default=None,
                        help=f"root holding the cloud seed assets "
                             f"(default: {REPO_ROOT})")
    args = parser.parse_args(argv)

    try:
        if args.cloud_mcp:
            defs = lib.load_servers(args.servers_json or DEFAULT_SERVERS_JSON)
            manifest_path = Path(args.repo) / ".agentic.json"
            if manifest_path.is_file():
                subset = json.loads(manifest_path.read_text()).get("servers")
            else:
                subset = _infer_manifest(Path(args.repo), defs)["servers"]
            print(lib.emit_cloud_json(defs, subset))
            return 0
        report = run(args.repo, assume_yes=args.yes,
                     servers_json=args.servers_json,
                     stale_packs_json=args.stale_packs_json,
                     seed_root=args.seed_root)
    except (AlignError, lib.GenerationError) as exc:
        print(f"align: error: {exc}", file=sys.stderr)
        return 1
    _print_report(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
