"""Shared library for the agentic-coding generated layer.

Used by generate.py (and later align.py). Python 3 stdlib only (Decision 12).

Managed-block contract (Decision 15): every generated or seeded file wraps
tool-owned content between BEGIN_MARKER / END_MARKER. Writers rewrite only
the block; content outside it is preserved verbatim. A pre-existing target
file without markers is hand-written: reported and skipped, never overwritten.
"""

from __future__ import annotations

import datetime
import json
import shutil
from pathlib import Path

BEGIN_MARKER = "<!-- agentic:begin -->"
END_MARKER = "<!-- agentic:end -->"


class GenerationError(Exception):
    """Fatal generation problem (e.g. secret with no mechanism for a target)."""


class ReportEntry:
    """Structured report entry: kind + path + detail.

    Kinds: "changed" (file created/updated/block rewritten/CLI applied),
    "unchanged" (already converged, nothing done), "warning" (backup taken,
    CLI failure), "preserved" (non-canonical entries kept), "skipped"
    (markerless hand-written file left alone). str() gives the human line;
    align.py buckets entries by `kind` instead of parsing strings.
    """

    def __init__(self, kind: str, path, detail: str):
        self.kind = kind
        self.path = str(path)
        self.detail = detail

    def __str__(self):
        return f"{self.path}: {self.detail}"

    def __repr__(self):
        return f"ReportEntry({self.kind!r}, {self.path!r}, {self.detail!r})"


# ---------------------------------------------------------------------------
# Managed-block writer (markdown-ish text files)
# ---------------------------------------------------------------------------

def managed_file_text(block: str) -> str:
    """Full file text for a fresh managed file containing only the block."""
    return f"{BEGIN_MARKER}\n{block.rstrip()}\n{END_MARKER}\n"


def write_managed(path: Path, block: str, report: list) -> bool:
    """Write `block` between the managed markers at `path`.

    Returns True when the file changed. Markerless existing files are
    reported and skipped (Req 8.4 semantics).
    """
    path = Path(path)
    if path.exists():
        old = path.read_text()
        if BEGIN_MARKER not in old or END_MARKER not in old:
            report.append(ReportEntry(
                "skipped", path,
                "exists without agentic markers - treated as "
                "hand-written, skipped"))
            return False
        head, _, rest = old.partition(BEGIN_MARKER)
        _, _, tail = rest.partition(END_MARKER)
        new = head + BEGIN_MARKER + "\n" + block.rstrip() + "\n" + END_MARKER + tail
        if new == old:
            return False
        path.write_text(new)
        report.append(ReportEntry("changed", path, "managed block rewritten"))
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(managed_file_text(block))
    report.append(ReportEntry("changed", path, "created"))
    return True


# ---------------------------------------------------------------------------
# Verbatim seeding (spec-janitor Req 9.3, Decision 10)
# ---------------------------------------------------------------------------

def seed_verbatim(src: Path, dst: Path, report: list) -> bool:
    """Seed a tool-owned file verbatim: `dst` becomes a byte-identical copy
    of `src`.

    For files that carry no repo-local hand edits by contract (e.g. the
    spec-janitor auditor and its conventions reference) the managed-block
    mechanism does not apply — it is markdown-only by construction, and the
    markerless-file skip would freeze a seeded copy forever. Instead:
    destination missing -> copy; identical -> unchanged; differing -> back
    up (`.bak-<date>`, the same convention as align's JSON-validity step)
    and re-copy, reported as changed.

    Returns True when the destination changed.
    """
    src = Path(src)
    dst = Path(dst)
    content = src.read_bytes()
    if dst.exists():
        if dst.read_bytes() == content:
            report.append(ReportEntry(
                "unchanged", dst, "already identical to the seed source"))
            return False
        _backup(dst, report,
                "differed from the tool-owned seed source - re-copied "
                "verbatim; previous content remains only in the backup")
        shutil.copy2(src, dst)
        report.append(ReportEntry(
            "changed", dst, "re-copied verbatim from the seed source"))
        return True
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    report.append(ReportEntry("changed", dst, "seeded verbatim"))
    return True


# ---------------------------------------------------------------------------
# Conventions assembly (Req 3.3, Decision 13)
# ---------------------------------------------------------------------------

def build_claude_block(shared_dir: Path) -> str:
    """claude/CLAUDE.md block = conventions + claude wrapper."""
    shared_dir = Path(shared_dir)
    conventions = (shared_dir / "conventions.md").read_text().strip()
    wrapper = (shared_dir / "claude-wrapper.md").read_text().strip()
    return conventions + "\n\n" + wrapper


def build_copilot_block(shared_dir: Path) -> str:
    """copilot-instructions.md block = copilot wrapper + conventions."""
    shared_dir = Path(shared_dir)
    conventions = (shared_dir / "conventions.md").read_text().strip()
    wrapper = (shared_dir / "copilot-wrapper.md").read_text().strip()
    return wrapper + "\n\n" + conventions


def generate_conventions(repo_root: Path, report: list) -> None:
    """Regenerate the checked-in conventions outputs."""
    repo_root = Path(repo_root)
    shared = repo_root / "shared"
    write_managed(repo_root / "claude" / "CLAUDE.md",
                  build_claude_block(shared), report)
    write_managed(repo_root / "copilot" / "instructions" /
                  "copilot-instructions.md",
                  build_copilot_block(shared), report)


# ---------------------------------------------------------------------------
# Shared JSON helpers
# ---------------------------------------------------------------------------

def _backup(path: Path, report: list, warning: str) -> None:
    content = path.read_bytes()
    for existing in sorted(path.parent.glob(path.name + ".bak-*")):
        if existing.is_file() and existing.read_bytes() == content:
            report.append(ReportEntry(
                "warning", path,
                f"{warning} (identical backup already at {existing.name})"))
            return
    stamp = datetime.date.today().isoformat()
    bak = path.with_name(path.name + f".bak-{stamp}")
    n = 1
    while bak.exists():
        bak = path.with_name(path.name + f".bak-{stamp}.{n}")
        n += 1
    shutil.copy2(path, bak)
    report.append(ReportEntry(
        "warning", path, f"{warning} (backed up to {bak.name})"))


def _load_json_or_backup(path: Path, report: list) -> dict:
    """Parse JSON at path; invalid JSON (or a non-dict root such as a
    top-level array) is backed up and treated as empty."""
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, UnicodeDecodeError):
        data = None
    if isinstance(data, dict):
        return data
    _backup(path, report,
            "invalid JSON - regenerated; non-canonical entries may "
            "remain only in the backup")
    return {}


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


# ---------------------------------------------------------------------------
# MCP generation (Req 4)
# ---------------------------------------------------------------------------

def load_servers(path: Path) -> dict:
    """Load canonical server definitions, dropping _comment keys."""
    data = json.loads(Path(path).read_text())
    return {name: spec for name, spec in data.items()
            if not name.startswith("_")}


def _secret_var(server: str, secret: str) -> str:
    return f"{server}_{secret}".upper().replace("-", "_")


def _input_id(server: str, secret: str) -> str:
    return f"{server}-{secret}".lower().replace("_", "-")


def _select(defs: dict, subset, surface: str) -> dict:
    if subset is not None:
        unknown = sorted(set(subset) - set(defs))
        if unknown:
            raise GenerationError(
                f"unknown server name(s): {', '.join(unknown)}; "
                f"canonical names: {', '.join(sorted(defs))}")
        names = sorted(subset)
    else:
        names = sorted(defs)
    return {n: defs[n] for n in names
            if surface in defs[n].get("surfaces", [])}


def _render_server(name: str, spec: dict, target: str) -> dict:
    """Render one server for a target: claude, vscode, or cloud.

    Secret references use each target's native mechanism (Req 4.3):
    claude -> ${VAR} env expansion, vscode -> ${input:id} prompt inputs,
    cloud -> COPILOT_MCP_* Actions-secret names. No secret values ever.
    """
    transport = spec["transport"]
    env = dict(transport.get("env", {}))
    headers: dict = {}

    if transport["type"] == "stdio":
        entry = {"type": "local" if target == "cloud" else "stdio",
                 "command": transport["command"]}
        if transport.get("args"):
            entry["args"] = list(transport["args"])
    else:
        entry = {"type": "http", "url": transport["url"]}

    for secret, mech in sorted(spec.get("secrets", {}).items()):
        var = _secret_var(name, secret)
        if target == "claude":
            ref = f"${{{var}}}"
        elif target == "vscode":
            ref = f"${{input:{_input_id(name, secret)}}}"
        elif target == "cloud":
            ref = f"COPILOT_MCP_{var}"
        else:
            raise GenerationError(f"unknown target {target!r}")
        if "header" in mech:
            # Cloud header references need the $ prefix; env names do not.
            headers[mech["header"]] = f"${ref}" if target == "cloud" else ref
        elif "env" in mech:
            env[mech["env"]] = ref
        else:
            raise GenerationError(
                f"server {name!r}: secret {secret!r} has no supported "
                f"secret mechanism for target {target!r}")

    if env:
        entry["env"] = env
    if headers:
        entry["headers"] = headers
    if target == "cloud":
        entry["tools"] = ["*"]
    return entry


def _render_all(defs: dict, subset, target: str) -> dict:
    return {name: _render_server(name, spec, target)
            for name, spec in _select(defs, subset, target).items()}


def emit_repo_mcp(defs: dict, subset=None) -> dict:
    """Claude-shaped MCP config: user ~/.claude.json entries / repo .mcp.json."""
    return {"mcpServers": _render_all(defs, subset, "claude")}


def _vscode_inputs(defs: dict, names) -> list:
    inputs = []
    for name in sorted(names):
        for secret, mech in sorted(defs[name].get("secrets", {}).items()):
            description = mech.get("description") or \
                f"Secret {secret} for MCP server {name}"
            inputs.append({
                "id": _input_id(name, secret),
                "type": "promptString",
                "description": description,
                "password": True,
            })
    return inputs


def emit_vscode_mcp(defs: dict, subset=None) -> dict:
    """VS Code mcp.json shape: servers plus promptString inputs for secrets."""
    servers = _render_all(defs, subset, "vscode")
    return {"servers": servers, "inputs": _vscode_inputs(defs, servers)}


def emit_cloud_config(defs: dict, subset=None) -> dict:
    """Cloud coding agent MCP config with COPILOT_MCP_* secret names (Req 6.2)."""
    return {"mcpServers": _render_all(defs, subset, "cloud")}


def emit_cloud_json(defs: dict, subset=None) -> str:
    """Paste-ready JSON for github.com repo settings (consumed by align --cloud-mcp)."""
    return json.dumps(emit_cloud_config(defs, subset), indent=2)


# ---------------------------------------------------------------------------
# Managed JSON merge (Req 4.5)
# ---------------------------------------------------------------------------

def _merge_servers_into(path: Path, key: str, rendered: dict, defs: dict,
                        target: str, report: list, inputs=None) -> None:
    """Merge rendered server entries into the JSON file at `path`.

    Canonical-named entries are converged to canonical; everything else
    (non-canonical servers, unrelated top-level keys, foreign inputs) is
    preserved and preserved servers are reported.
    """
    path = Path(path)
    data = _load_json_or_backup(path, report)
    original = json.dumps(data, sort_keys=True)

    existing = data.get(key, {})
    if not isinstance(existing, dict):
        existing = {}
    preserved = sorted(n for n in existing if n not in defs)
    merged = {n: existing[n] for n in preserved}
    merged.update(rendered)
    # Canonical-named entries present but outside the emitted set are
    # converged too (Req 4.5), never silently dropped.
    for name in sorted(existing):
        if name in defs and name not in merged:
            merged[name] = _render_server(name, defs[name], target)
    data[key] = dict(sorted(merged.items()))

    if inputs is not None:
        managed_ids = {i["id"] for i in inputs}
        kept = [i for i in data.get("inputs", [])
                if i.get("id") not in managed_ids]
        data["inputs"] = kept + inputs

    if preserved:
        report.append(ReportEntry(
            "preserved", path,
            f"preserved non-canonical entries: {', '.join(preserved)}"))
    if json.dumps(data, sort_keys=True) != original or not path.exists():
        existed = path.exists()
        _write_json(path, data)
        report.append(ReportEntry(
            "changed", path, "updated" if existed else "created"))


def generate_repo_configs(repo_path: Path, defs: dict, subset,
                          report: list) -> None:
    """Per-repo .mcp.json and .vscode/mcp.json (Req 4.2, 4.4)."""
    repo_path = Path(repo_path)
    repo = emit_repo_mcp(defs, subset)
    _merge_servers_into(repo_path / ".mcp.json", "mcpServers",
                        repo["mcpServers"], defs, "claude", report)
    vscode = emit_vscode_mcp(defs, subset)
    _merge_servers_into(repo_path / ".vscode" / "mcp.json", "servers",
                        vscode["servers"], defs, "vscode", report,
                        inputs=vscode["inputs"])


def build_claude_cli_commands(defs: dict, subset=None) -> list:
    """`claude mcp add-json` invocations for the user scope."""
    commands = []
    for name, entry in emit_repo_mcp(defs, subset)["mcpServers"].items():
        commands.append(["claude", "mcp", "add-json", name,
                         json.dumps(entry), "--scope", "user"])
    return commands


def _read_claude_user_server(path: Path, name: str):
    """Read one server definition from the Claude user config, read-only.

    Used only for comparison on the CLI path (`claude mcp get` has no
    machine-readable output); returns None when the file, the mcpServers
    key, or the entry is missing or unparseable.
    """
    try:
        data = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    servers = data.get("mcpServers")
    if not isinstance(servers, dict):
        return None
    return servers.get(name)


def _normalized_server(entry):
    """Normalize a server entry for idempotence comparison.

    `claude mcp add-json` persists explicit empty fields that the canonical
    render omits (observed: "args": []), so a converged entry would compare
    unequal on every run and be removed/re-added forever. Treat missing
    args/env as their empty values on both sides.
    """
    if not isinstance(entry, dict):
        return entry
    normalized = dict(entry)
    normalized.setdefault("args", [])
    normalized.setdefault("env", {})
    return normalized


def update_claude_user_config(path: Path, defs: dict, subset, report: list,
                              use_cli=None) -> None:
    """Converge the Claude user-level MCP config.

    Prefers the claude CLI when it is on PATH (avoids racing a running
    Claude Code instance that rewrites ~/.claude.json); falls back to a
    managed merge that preserves every unrelated key and non-canonical
    server.

    CLI path idempotence: the existing definition is read from `path`
    (read-only, comparison only) and compared after normalization
    (_normalized_server — claude persists "args": [] where the canonical
    entry omits args). Identical -> reported as already configured,
    nothing run. Different -> `claude mcp remove --scope user`
    (failure ignored) then `claude mcp add-json --scope user`. Every
    CalledProcessError becomes a "warning" report entry, never a traceback.
    """
    if use_cli is None:
        use_cli = shutil.which("claude") is not None
    if not use_cli:
        rendered = emit_repo_mcp(defs, subset)["mcpServers"]
        _merge_servers_into(Path(path), "mcpServers", rendered, defs,
                            "claude", report)
        return

    import subprocess

    def remove(name):
        # Best-effort: a missing entry makes remove fail, which is fine.
        try:
            subprocess.run(["claude", "mcp", "remove", name,
                            "--scope", "user"],
                           check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError:
            pass

    def add(name, entry):
        subprocess.run(["claude", "mcp", "add-json", name,
                        json.dumps(entry), "--scope", "user"],
                       check=True, capture_output=True, text=True)

    for name, entry in emit_repo_mcp(defs, subset)["mcpServers"].items():
        existing = _read_claude_user_server(path, name)
        if _normalized_server(existing) == _normalized_server(entry):
            report.append(ReportEntry(
                "unchanged", path,
                f"claude mcp server {name}: already configured"))
            continue
        if existing is not None:
            remove(name)
        try:
            add(name, entry)
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or "") + (exc.stdout or "")
            if "already exists" in stderr:
                remove(name)
                try:
                    add(name, entry)
                except subprocess.CalledProcessError as exc2:
                    report.append(ReportEntry(
                        "warning", path,
                        f"claude mcp add-json {name} --scope user failed "
                        f"after remove: {(exc2.stderr or '').strip()}"))
                    continue
            else:
                report.append(ReportEntry(
                    "warning", path,
                    f"claude mcp add-json {name} --scope user failed: "
                    f"{stderr.strip()}"))
                continue
        report.append(ReportEntry(
            "changed", path,
            f"claude mcp add-json {name} --scope user: applied"))


# ---------------------------------------------------------------------------
# VS Code user settings merge (Req 7.2, generate.py --user)
# ---------------------------------------------------------------------------

LOCALML_BASE_URL = "http://127.0.0.1:8080/v1"
# The key under customOAIModels is the model id VS Code requests from the
# provider; the user replaces it with the id localml actually serves
# (see the localml runbook).
LOCALML_PLACEHOLDER_MODEL_ID = "REPLACE-WITH-SERVED-MODEL-ID"

LOCALML_MODEL_ENTRY = {
    "name": "localml (local MLX)",
    "url": LOCALML_BASE_URL,
    "toolCalling": True,
    "vision": False,
    "maxInputTokens": 32768,
    "maxOutputTokens": 8192,
    "requiresAPIKey": True,
}


def merge_vscode_settings(settings_path: Path, repo_root: Path,
                          report: list) -> bool:
    """Merge the managed keys into the VS Code user settings.json.

    Preserves every unrelated key. JSONC (comments, trailing commas) is
    handled conservatively: an unparseable file is backed up and reported,
    never clobbered. `chat.useClaudeMdFile` is never enabled — it would
    deliver the Claude wrapper to Copilot (Req 3.3).

    Returns True when the file changed.
    """
    settings_path = Path(settings_path)
    repo_root = Path(repo_root)

    if settings_path.exists():
        try:
            data = json.loads(settings_path.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            data = None
        if not isinstance(data, dict):
            _backup(settings_path, report,
                    "not a strict JSON object (JSONC comments/trailing "
                    "commas, or a non-object root?) - left unchanged; "
                    "merge the managed keys manually")
            return False
    else:
        data = {}
    original = json.dumps(data, sort_keys=True)

    locations = data.setdefault("chat.instructionsFilesLocations", {})
    locations[str(repo_root / "copilot" / "instructions")] = True

    models = data.setdefault("github.copilot.chat.customOAIModels", {})
    models[LOCALML_PLACEHOLDER_MODEL_ID] = dict(LOCALML_MODEL_ENTRY)

    if json.dumps(data, sort_keys=True) == original:
        return False
    _write_json(settings_path, data)
    report.append(ReportEntry("changed", settings_path,
                              "managed keys merged"))
    return True


def default_vscode_user_dir() -> Path:
    return Path.home() / "Library" / "Application Support" / "Code" / "User"


def generate_user_configs(defs: dict, subset, report: list, repo_root: Path,
                          claude_config_path: Path = None,
                          vscode_mcp_path: Path = None,
                          vscode_settings_path: Path = None,
                          use_cli=None) -> None:
    """User-level targets: Claude MCP config, VS Code mcp.json, VS Code
    settings merge. Paths are injectable so tests never touch real files."""
    claude_config_path = Path(claude_config_path
                              or Path.home() / ".claude.json")
    vscode_dir = default_vscode_user_dir()
    vscode_mcp_path = Path(vscode_mcp_path or vscode_dir / "mcp.json")
    vscode_settings_path = Path(vscode_settings_path
                                or vscode_dir / "settings.json")

    update_claude_user_config(claude_config_path, defs, subset, report,
                              use_cli=use_cli)
    vscode = emit_vscode_mcp(defs, subset)
    _merge_servers_into(vscode_mcp_path, "servers", vscode["servers"], defs,
                        "vscode", report, inputs=vscode["inputs"])
    merge_vscode_settings(vscode_settings_path, repo_root, report)
