# Bugfix Report: golden-test-markers

**Date:** 2026-07-25
**Status:** Fixed

## Description of the Issue

Five tests failed on `main` (and every branch descended from it) after commit
`0d0f3f4`: two golden-comparison tests in `tests/test_generate.py`, a seed-source
marker subtest (two subfailures), and an align convergence test in
`tests/test_align.py`.

**Reproduction steps:**
1. Check out `main` (or any branch at/after `0d0f3f4`).
2. Run `python3 -m pytest tests/test_generate.py tests/test_align.py`.
3. Observe 5 failures: generated output and seeded files carry the wrong
   managed-block markers, and align cannot converge a drifted managed block.

**Impact:** Medium. The failing tests are the guardrails for the generated layer.
Beyond the red suite, the underlying defect is functional: `generate.py` and
`align.py` wrap tool-owned content in `BEGIN_MARKER`/`END_MARKER`. With the
markers changed, every already-generated or already-seeded file (which still
carries the canonical `<!-- agentic:begin -->` / `<!-- agentic:end -->` markers)
would be treated as hand-written and skipped forever — orphaning the entire
managed layer on the next generate/align run.

## Investigation Summary

- **Symptoms examined:** golden diffs showing `<!-- LM -->` / `EOF` where the
  goldens expect `<!-- agentic:begin -->` / `<!-- agentic:end -->`; align leaving
  `STALE DRIFTED SEEDED CONTENT` in place instead of converging it.
- **Code inspected:** `scripts/agentic_lib.py` (marker definitions and
  managed-block writer/align logic), the golden fixtures under `tests/`.
- **Hypotheses tested:** (a) goldens are stale and need regenerating — ruled out,
  the goldens hold the correct canonical markers; (b) the code changed — confirmed:
  `git show 0d0f3f4 -- scripts/agentic_lib.py` shows the marker constants were
  overwritten.

## Discovered Root Cause

Commit `0d0f3f4` ("specs-overview: preservation-first regen; fork/personalisation
fixups") accidentally overwrote the managed-block marker constants in
`scripts/agentic_lib.py`:

- `BEGIN_MARKER`: `<!-- agentic:begin -->` → `<!-- LM -->`
- `END_MARKER`: `<!-- agentic:end -->` → `EOF`

`<!-- LM -->` is the *nextup* session marker and `EOF` is not a marker at all, so
the change was clearly an unintended paste, not a deliberate rename (the commit
message only notes "agentic_lib.py: section markers"). The goldens were never
wrong — the code was.

**Defect type:** Regression — a compatibility-contract constant changed by accident.

**Why it occurred:** A wide-ranging commit touched several skills plus
`agentic_lib.py`; the marker edit slipped in without regenerating goldens or
running the suite, so it landed unnoticed.

**Contributing factors:** The markers are a bare module-level constant with no test
pinning their exact string, so an accidental edit produced opaque golden diffs
rather than a self-explaining failure.

## Resolution for the Issue

**Changes made:**
- `scripts/agentic_lib.py:18-19` - restore `BEGIN_MARKER` / `END_MARKER` to the
  canonical `<!-- agentic:begin -->` / `<!-- agentic:end -->`.
- `tests/test_generate.py` - add `MarkerContractTests::test_managed_block_markers_are_stable`
  pinning the two marker strings with an explanatory docstring, so any future
  accidental change fails loudly with the reason instead of via golden diffs.

**Approach rationale:** The markers are a compatibility contract (Decision 15):
they must match the markers already embedded in every generated/seeded file across
consuming repos. Reverting to the canonical values is the only correct fix;
regenerating goldens to the new markers would have been wrong — it would have
codified the accident and orphaned existing managed files.

**Alternatives considered:**
- Regenerate the golden fixtures to expect `<!-- LM -->` / `EOF` - rejected: it
  treats the symptom, entrenches the accidental contract break, and would orphan
  every existing managed block in consuming repos.

## Regression Test

**Test file:** `tests/test_generate.py`
**Test name:** `MarkerContractTests::test_managed_block_markers_are_stable`

**What it verifies:** `agentic_lib.BEGIN_MARKER` and `END_MARKER` equal the
canonical `<!-- agentic:begin -->` / `<!-- agentic:end -->`. The docstring records
why the strings are a contract, so a future change fails with the explanation.

**Run command:** `python3 -m pytest tests/test_generate.py::MarkerContractTests -q`

## Affected Files

| File | Change |
|------|--------|
| `scripts/agentic_lib.py` | Restore canonical managed-block marker constants |
| `tests/test_generate.py` | Add marker-contract regression test |
| `specs/bugfixes/golden-test-markers/report.md` | This report |

## Verification

**Automated:**
- [x] Regression test passes
- [x] Full test suite passes
- [x] Linters/validators pass

**Manual verification:**
- Confirmed the goldens hold the canonical markers (so no golden regeneration was
  needed), and that the align convergence fixture passes once markers are restored.

## Prevention

**Recommendations to avoid similar bugs:**
- The new `MarkerContractTests` pins the marker strings so an accidental change
  surfaces as a clear, self-documenting failure rather than opaque golden diffs.
- Run the test suite (`make test` / `pytest`) before committing wide-ranging
  changes that touch `scripts/`.

## Related

- Introduced by commit `0d0f3f4`.
- Flagged as a follow-up in `specs/nextup-pure-router/tasks.md` task 7.
- Managed-block contract: Decision 15, `specs/toolset-agnostic-starwave`.
