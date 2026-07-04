# Skills Usage

This project uses custom skills extensively. Available skills include: spec creation, PR review fixing, pre-push review, and explain-like. Check `.claude/skills/` for the full list before suggesting manual approaches.

When asked to analyze or document something, first check if there's an existing skill/workflow for that task (e.g., spec creation, review). Use the established workflow rather than doing ad-hoc analysis.

When managing tasks, prefer the rune skill over calling the CLI directly.

# Asking the User Questions

- When an AskUserQuestion answer includes free-text notes, the notes are the real instruction — treat them as first-class steering, even when the selected option looks like a rejection.
- Ask clarifying questions one at a time, concretely, describing observable behavior — not implementation jargon.
- Approval gates for documents SHOULD offer an "explain it first" option (e.g. run /explain-like) alongside approve/reject.

# Claude-Specific Project Conventions

- If `.claude/scripts/README.md` exists in the project, you SHOULD use the tools mentioned in there for their intended purposes.

# Decision Log Format Reference

When creating or updating decision log entries, follow the format in `rules/references/decision-log-format.md`. Read the format file before creating entries.
