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

## Dataclasses

- Do not combine `@dataclass(frozen=True, slots=True)`. The `slots=True` path
  recreates the class, but the generated frozen `__setattr__` keeps a closure
  over the pre-slots class, so assigning an *unknown* attribute raises
  `TypeError: super(type, obj): obj must be an instance or subtype of type`
  instead of `FrozenInstanceError`/`AttributeError` (observed on CPython 3.12+
  via uv, August 2026). `frozen=True` alone already rejects every attribute
  assignment with a clean `FrozenInstanceError`; use it without `slots` unless
  the memory saving is measured to matter.
