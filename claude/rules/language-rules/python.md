---
paths: **/*.py
---

# Python language rules

## Interpreter compatibility

- A script that anything might invoke as bare `python3` should open with
  `from __future__ import annotations`. PEP 604 unions (`list | None`,
  `str | None`) in signatures are evaluated **at def time**, so a module that
  merely *imports* raises `TypeError: unsupported operand type(s) for |` on
  CPython 3.9 — which is what `/usr/bin/python3` still is on macOS 15/26.
  `compile()` succeeds on such a file, so a syntax sweep will not find the
  problem; only importing or running it will. Observed August 2026: a Swift
  end-to-end test shelling out to `python3` failed on a generator script whose
  signatures had drifted to PEP 604 while every human ran it under Homebrew's
  3.13.
- On Apple's Python, subprocesses with an isolated `HOME` can create bytecode
  caches under `~/Library/Caches/com.apple.python`. Tests asserting which user
  config directories were written should set `PYTHONDONTWRITEBYTECODE=1` for
  those subprocesses so interpreter caches do not look like client writes.

## Filesystem paths

- Validate raw CLI path strings before constructing `Path` objects: `Path("")`
  becomes the current directory, so `resolve(strict=True)` accepts it. Preserve
  the raw argparse string long enough to reject blank input, then check
  `is_file()` before looking up a file's repository or parent directory.
- When a Python CLI is installed as a symlink, use `Path(__file__).resolve()`
  to locate resources beside its source. Resolve user-supplied relative paths
  against the caller's working directory instead.

## Dataclasses

- Do not combine `@dataclass(frozen=True, slots=True)`. The `slots=True` path
  recreates the class, but the generated frozen `__setattr__` keeps a closure
  over the pre-slots class, so assigning an *unknown* attribute raises
  `TypeError: super(type, obj): obj must be an instance or subtype of type`
  instead of `FrozenInstanceError`/`AttributeError` (observed on CPython 3.12+
  via uv, August 2026). `frozen=True` alone already rejects every attribute
  assignment with a clean `FrozenInstanceError`; use it without `slots` unless
  the memory saving is measured to matter.

## sqlite3

- For atomic multi-statement work (schema migrations), open the connection with
  `sqlite3.connect(path, autocommit=True)` (3.12+) and issue `BEGIN IMMEDIATE`,
  `COMMIT` and `ROLLBACK` yourself. In the default legacy mode,
  `executescript()` first commits any open transaction and then runs each
  statement in its own transaction. A script that fails halfway therefore
  leaves its earlier statements and the caller's prior writes committed.
  Verified on CPython 3.12, November 2026.

## Subprocesses

- `python -m pkg.module` puts the current working directory first on
  `sys.path`. A launcher or detached worker started that way from inside a
  checkout's `src/` imports the checkout instead of the installed package. Pass
  `-I` (no cwd, no `PYTHON*` variables, no user site) when the installed version
  must be the one that runs; site-packages, including editable `.pth` installs,
  still load.
- `os.kill(pid, 0)` succeeds for a zombie. A test that kills a child it spawned
  through `subprocess.Popen` must `wait()` on it before checking whether the pid
  is gone, or any "leader still alive" logic sees the zombie.

## Tooling

- `ruff format .` also formats ```` ```python ```` blocks inside Markdown files
  (ruff 0.17). It will rewrite code sketches in specs and design documents.
  Add those folders to `extend-exclude` under `[tool.ruff]`.
