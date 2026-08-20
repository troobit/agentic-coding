---
paths: **/*.py
---

# Python language rules

## Dataclasses

- Do not combine `@dataclass(frozen=True, slots=True)`. The `slots=True` path
  recreates the class, but the generated frozen `__setattr__` keeps a closure
  over the pre-slots class, so assigning an *unknown* attribute raises
  `TypeError: super(type, obj): obj must be an instance or subtype of type`
  instead of `FrozenInstanceError`/`AttributeError` (observed on CPython 3.12+
  via uv, August 2026). `frozen=True` alone already rejects every attribute
  assignment with a clean `FrozenInstanceError`; use it without `slots` unless
  the memory saving is measured to matter.
