---
references:
    - specs/nextup-pure-router/smolspec.md
    - specs/nextup-pure-router/decision_log.md
---
# Nextup Pure Router

- [ ] 1. The nextup skill routes without tracking status: claude/skills/nextup/SKILL.md is a pure router under 120 lines <!-- id:va6owt0 -->
  - Keep: user-zone contract, seeding a missing nextup.md verbatim from nextup.example.md, feature detection (explicit reference, branch, specs/ contents - no machine-zone fallback), the four lanes, job splitting/fan-out, autonomy flag, slimmed close-out sweep (rune tasks, decision_log, /specs-overview).
  - Drop: machine-zone template, the update-the-machine-zone step, machine-zone hard rules, legacy-marker state parsing; frontmatter description no longer claims a plain-English progress record.
  - Replacements: fan-out outcomes, undispatched gated jobs, interrupt handoffs, and loose ends without a tasks file are reported in the closing message; a /nextup run after /sendit with no change requests counts as approval.
  - Verify: grep of the file finds no machine-zone maintenance instructions; wc -l is under 120.
  - References: specs/nextup-pure-router/smolspec.md

- [ ] 2. Session templates carry no status block: nextup.example.md and root nextup.md hold only the user zone plus an inert LM marker line <!-- id:va6owt1 -->
  - Below the <!-- LM --> marker only one inert line, e.g. reserved marker for tooling - no session status is kept here. Marker must survive for scripts/align.py convergence (decision 2).
  - Verify: both files contain the marker, no progress/notes template below it; user-zone placeholder in nextup.example.md still documents the act autonomously flag.
  - Blocked-by: va6owt0 (The nextup skill routes without tracking status: claude/skills/nextup/SKILL.md is a pure router under 120 lines)
  - References: specs/nextup-pure-router/smolspec.md

- [ ] 3. sendit closes out without touching nextup.md: no machine-notes step, no machine-zone feature resolution, frontmatter updated <!-- id:va6owt4 -->
  - Close-out becomes: copy docs to Prism, report loose ends in the plain-English closing message, stop. Feature resolution keeps explicit reference and branch only.
  - Verify: grep -i "machine" on claude/skills/sendit/SKILL.md returns nothing.
  - References: specs/nextup-pure-router/smolspec.md

- [ ] 4. Downstream skills resolve features without the machine zone: make-it-so and next-task drop the fallback; starwave gate boilerplate no longer mentions nextup machine notes <!-- id:va6owt5 -->
  - make-it-so/SKILL.md:13 and next-task/SKILL.md:13: ambiguity resolution falls back to listing candidates and asking the user (already present).
  - starwave-requirements:81, starwave-design:104, starwave-tasks:167, starwave-smolspec:171 and 195: reword /sendit gate boilerplate to drop updates-the-nextup-machine-notes.
  - Verify: grep -ri "machine zone\|machine notes" claude/skills/ returns nothing.
  - References: specs/nextup-pure-router/smolspec.md

- [ ] 5. make status reports without machine-zone health: process_status.py drops zone parsing, columns, and the machine-zone/stale-nextup flags, with its tests passing <!-- id:va6owt2 -->
  - Remove _machine_zone(), the marker table and note regex, the zone/newest-note columns, and the machine-zone/stale-nextup drift flags; keep nextup.md and nextup.example.md presence, spec-gap, no-agentic-json.
  - Update module docstring and tests/test_process_status.py in step.
  - Verify: python3 -m pytest tests/test_process_status.py passes; make status output shows no zone or note-date columns and never emits machine-zone/stale-nextup.
  - References: specs/nextup-pure-router/smolspec.md

- [ ] 6. Project docs describe the new contract: scripts/README.md, process-onboarding runbook, and agent notes no longer claim nextup maintains a machine zone <!-- id:va6owt3 -->
  - scripts/README.md:118-131 (status tool description), docs/runbooks/process-onboarding.md:58-62, docs/agent-notes/process-status.md, docs/agent-notes/align-tooling.md (machine-zone framing only - align behaviour is unchanged).
  - Verify: grep of these files shows no claim that nextup or sendit writes a machine zone; align docs still describe marker-based convergence accurately.
  - Blocked-by: va6owt0 (The nextup skill routes without tracking status: claude/skills/nextup/SKILL.md is a pure router under 120 lines), va6owt2 (make status reports without machine-zone health: process_status.py drops zone parsing, columns, and the machine-zone/stale-nextup flags, with its tests passing)
  - References: specs/nextup-pure-router/smolspec.md

- [ ] 7. Repo-wide sweep confirms removal and the change is logged in CHANGELOG.md <!-- id:va6owt6 -->
  - Verify: grep -ri "machine zone\|machine-zone" across the repo hits only scripts/align.py, tests/test_align.py and its fixtures, and specs/ history; full test suite passes (make test if present, else python3 -m pytest tests/).
  - Add a CHANGELOG.md entry describing the nextup-pure-router change.
  - Blocked-by: va6owt0 (The nextup skill routes without tracking status: claude/skills/nextup/SKILL.md is a pure router under 120 lines), va6owt1 (Session templates carry no status block: nextup.example.md and root nextup.md hold only the user zone plus an inert LM marker line), va6owt4 (sendit closes out without touching nextup.md: no machine-notes step, no machine-zone feature resolution, frontmatter updated), va6owt5 (Downstream skills resolve features without the machine zone: make-it-so and next-task drop the fallback; starwave gate boilerplate no longer mentions nextup machine notes), va6owt2 (make status reports without machine-zone health: process_status.py drops zone parsing, columns, and the machine-zone/stale-nextup flags, with its tests passing), va6owt3 (Project docs describe the new contract: scripts/README.md, process-onboarding runbook, and agent notes no longer claim nextup maintains a machine zone)
  - References: specs/nextup-pure-router/smolspec.md, specs/nextup-pure-router/decision_log.md
