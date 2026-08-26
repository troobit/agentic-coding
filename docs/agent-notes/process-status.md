# process_status.py (make status)

The module docstring in `scripts/process_status.py` is the authoritative
spec (columns, drift flags, read-only discipline). Non-obvious points:

- BACKLOG column (spec backlog-skill) is a hybrid check: `-` when
  `specs/BACKLOG.md` is absent (never drift), else `ok` or `drift`. Drift
  covers a failed `rune list` parse, H2 phases other than exactly `Idea`
  then `Needs Spec`, a non-pending entry (including a nested subtask), or
  a missing leading H1 — the `backlog-drift` flag names the reason in the
  repo's detail line. Drift flags overall are spec-gap, rune-drift,
  backlog-drift, and no-agentic-json.
- rune-drift (PRD agreement-invoice-skills Req 1): `collect()` runs
  `rune list` over every `tasks.md` / `tasks-*.md` found by `rglob` under
  each `specs/` subfolder. Non-zero exit = drift; the spec's detail line
  gets ` [rune-drift: <files>]` appended. Gotcha: `rune list` exits 0 on a
  file with NO task lines at all ("No tasks found") — only malformed task
  lines (e.g. unnumbered `- [ ]` checkboxes) fail, so a placeholder
  `# tasks.md` fixture is NOT flagged.
- Missing rune binary (`shutil.which` up front, plus OSError from the
  subprocess mid-run): sets `rune_missing`, which renders a per-repo
  `warning: rune binary not found; task-file parsing not checked` detail
  line and never a flag or crash.
- prd.md visibility (Req 5) needed no collection change — `prd.md` was
  already in `SPEC_DOCS`, so prd.md-only folders always rendered; the
  docstring now states it explicitly.
- Tests (`tests/test_process_status.py`): `make_repo` gained a `files`
  kwarg (repo-relative path -> exact text) for content-sensitive fixtures.
  `RuneDriftTest` needs the real rune binary on PATH; the missing-binary
  case is `mock.patch("process_status.shutil.which", return_value=None)`.
- Runbook for users/agents: `docs/runbooks/rune-usage.md`.
