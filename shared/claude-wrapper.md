# Skills Usage

This project uses custom skills extensively. Available skills include: spec creation, PR review fixing, pre-push review, and explain-like. Check `.claude/skills/` for the full list before suggesting manual approaches.

When asked to analyze or document something, first check if there's an existing skill/workflow for that task (e.g., spec creation, review). Use the established workflow rather than doing ad-hoc analysis.

When managing tasks, prefer the rune skill over calling the CLI directly.

# Persisting Knowledge (Cross-Project)

**Before starting a task**: if it touches a framework, language, or domain you've worked in before, run `/recall-knowledge` to see if the vault already has notes — a quick check beats re-investigating something you already documented.

If what you learned would help on a *different* project (framework gotchas, integration recipes, reusable patterns, platform quirks), use the `/capture-knowledge` skill to write it into the Obsidian vault. This is the preferred destination for anything generalizable. Be proactive: when you've just solved something non-obvious that isn't tied to this one repo, offer to capture it even if the user didn't ask.

For knowledge that only makes sense inside this one repo, use `docs/agent-notes/` as described above rather than the vault.

# Asking the User Questions

- When an AskUserQuestion answer includes free-text notes, the notes are the real instruction — treat them as first-class steering, even when the selected option looks like a rejection.
- Ask clarifying questions one at a time, concretely, describing observable behavior — not implementation jargon.
- Approval gates for documents SHOULD offer an "explain it first" option (e.g. run /explain-like) alongside approve/reject.

# Claude-Specific Project Conventions

- If `.claude/scripts/README.md` exists in the project, you SHOULD use the tools mentioned in there for their intended purposes.

# Decision Log Format Reference

When creating or updating decision log entries, follow the format in `rules/references/decision-log-format.md`. Read the format file before creating entries.
