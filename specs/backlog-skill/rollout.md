# Rollout: backlog-skill

Post-build administration for the backlog-skill feature. Nothing here is a system requirement — these are one-time actions performed after the skill lands (see requirements [6.6](requirements.md#6.6) for the ordering constraint the build itself carries). Sequencing follows Decision 11: skill first, migrate, then the sunset commit.

This document is committed, so it names roles, not repos: the operator's concrete repo list is session-local state, held outside the repository.

## 1. Enrollment

- [ ] Enroll each repo the operator designates as a new align participant (a `.agentic.json` and a passing align run per repo)
- [ ] Correct `process_status.py`'s hardcoded `DEFAULT_REPOS` to the enrolled participating set (it currently contains non-participants and omits participants)

## 2. decision_mode configuration

- [ ] Set `decision_mode: overwrite` by hand-editing `.agentic.json` in each repo the operator designates (align does not backfill keys into existing manifests; a newly enrolled repo needs enrollment first)

All other repos stay in default `supersede` mode.

## 3. nextup.md migration

- [ ] Run `/backlog` in every participating repo — sweep all of them rather than trusting a remembered list; a zone may exist where none is expected
- [ ] Expect the full range of outcomes: untranslated idea dumps (mostly `needs-spec` filings), fully consumed zones (all-duplicate drop, then delete), repos with no `specs/` directory yet (first capture creates it), and any tracked `nextup.md` (reported as retained per requirements 4.4/4.5 — remove it via git in that repo's migration commit)
- [ ] Migration complete in every participating repo — the sunset commit (requirements §6) may now land

## 4. Residual file cleanup

Per repo during its migration visit:

- [ ] Delete stale generated `SPOUT.md` files
- [ ] Remove `SPOUT.md` and `nextup.md` gitignore entries left by the retired tooling
- [ ] Confirm no `nextup.example.md` remains (none were seeded as of spec time; this is a verification, not expected work)

## 5. Out-of-scope strays (manual)

- [ ] Intent files outside any participating repo are not covered by any automated sweep; the operator handles or consciously drops them

## 6. Toolchain refresh

- [ ] Re-run `scripts/generate.py --user` after the conventions change lands — Codex reads `~/.codex/AGENTS.md`, which only that command refreshes; without it Codex sessions keep the pre-decision_mode text indefinitely

## 7. Exit criteria

- [ ] Every participating repo: no `nextup.md`, no `nextup.example.md`, no stale `SPOUT.md`
- [ ] Every participating repo with backlog content: `specs/BACKLOG.md` parses under `rune list`
- [ ] `make status` reports the new BACKLOG column cleanly across the corrected repo list
- [ ] The sunset commit (requirements §6) is merged
