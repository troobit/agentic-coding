# Runbook: rune task files

How task files are created, where they live, the commands sessions use day
to day, and what the `rune-drift` status flag means. Ground truth for the
file format: `rune list <file>` parses it.

## When task files are created

- **Starwave tasks phase** — the `starwave-tasks` skill (step 3 of the gated
  spec lane) writes `specs/<feature>/tasks.md` after requirements and design
  are approved.
- **Engage derivation** — `/engage` derives one task file per PRD context
  from `specs/<prd-name>/prd.md`, named `specs/<prd-name>/tasks-<context>.md`
  (e.g. `specs/agreement-invoice-skills/tasks-process-guardrails.md`).

## Where they live

Always under the feature's folder in `specs/`: `specs/<feature>/tasks.md` or
`specs/<feature>/tasks-*.md`. Committed feature work requires its spec
documents (design or PRD, plus the task file) to exist in `specs/` first —
see the task-management rule in `shared/conventions.md`.

## Day-to-day commands

All examples below run as written from this repository's root against this
PRD's own task file.

List tasks (add `--format json` for structured output, `--all` for details):

```sh
rune list specs/agreement-invoice-skills/tasks-process-guardrails.md
```

Next ready work — the next incomplete task, or the next incomplete phase's
ready tasks with `--phase`:

```sh
rune next specs/agreement-invoice-skills/tasks-process-guardrails.md --phase --format json
```

Stream status for multi-agent parallel execution:

```sh
rune streams specs/agreement-invoice-skills/tasks-process-guardrails.md
```

Add a task (top-level, or under a parent with `--parent <id>`; `--phase`
targets a named phase). `--dry-run` previews any mutating command without
writing:

```sh
rune add specs/agreement-invoice-skills/tasks-process-guardrails.md --title "New task" --dry-run
```

Status updates as work proceeds:

```sh
rune progress specs/agreement-invoice-skills/tasks-process-guardrails.md 1 --dry-run
rune complete specs/agreement-invoice-skills/tasks-process-guardrails.md 1 --dry-run
rune uncomplete specs/agreement-invoice-skills/tasks-process-guardrails.md 1 --dry-run
```

Drop the `--dry-run` flag to apply. Other useful commands: `rune find`
(search), `rune update` (title/details/dependencies), `rune renumber` (fix
numbering), `rune create` (start a fresh file). `rune <command> --help`
documents each.

## The rune-drift status flag

`make status` (`scripts/process_status.py`) runs `rune list` over every
`specs/**` task file (`tasks.md` and `tasks-*.md`) in each participating
repo. A file rune cannot parse — typically a hand-written checklist without
task numbers — flags the repo row `rune-drift`, and the spec folder's detail
line names the failing file:

```text
specs/feat: tasks.md [rune-drift: tasks.md]
```

The check is read-only; a missing rune binary degrades to a
`warning: rune binary not found` detail line instead of a flag.

To clear the flag, make the named file rune-parseable:

1. Recreate it with `rune create <file> --title "<Feature> tasks"` and
   re-add the tasks with `rune add`, or hand-edit it into rune's format
   (numbered `- [ ] 1. Title` checkboxes; `rune renumber <file>` fixes
   numbering).
2. Verify with `rune list <file>` (exit 0), then re-run `make status` — the
   flag and detail annotation disappear.

If `which rune` fails, run `make bootstrap`: it go-installs rune, and on a
machine with a local build at `~/repos/rune/rune` it symlinks that build
into `~/.local/bin`.
