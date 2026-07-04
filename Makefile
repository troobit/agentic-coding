# Development tooling for agentic-coding.
#
# generate  rebuild the checked-in generated files (claude/CLAUDE.md,
#           copilot/instructions/copilot-instructions.md) and MCP configs
# sync      create the ~/.claude and VS Code profile symlinks
# align     align this repository's own agent configs
# test      run the Python unittest suite
# lint      shellcheck all shell scripts + fail if generated files drift
#           from their sources in shared/ and mcp/

.PHONY: generate sync align test lint lint-shell lint-drift

generate:
	python3 scripts/generate.py

sync:
	scripts/sync-claude.sh

align:
	python3 scripts/align.py

test:
	python3 -m unittest discover -s tests

lint: lint-shell lint-drift

lint-shell:
	@command -v shellcheck >/dev/null 2>&1 || { \
		echo "shellcheck is not installed (brew install shellcheck)"; exit 1; }
	shellcheck scripts/*.sh

# Generated-drift check: regenerate in a way that leaves the working tree
# untouched — snapshot the checked-in generated files, run the generator,
# diff, then restore the snapshots — and fail when the checked-in files are
# out of date. Any conventions warnings generate.py emits (e.g. tail content
# in claude/CLAUDE.md that belongs in shared/) surface in this run's output.
lint-drift:
	@tmp="$$(mktemp -d)"; \
	cp claude/CLAUDE.md "$$tmp/CLAUDE.md"; \
	cp copilot/instructions/copilot-instructions.md "$$tmp/copilot-instructions.md"; \
	python3 scripts/generate.py; \
	status=0; \
	diff -u "$$tmp/CLAUDE.md" claude/CLAUDE.md || status=1; \
	diff -u "$$tmp/copilot-instructions.md" copilot/instructions/copilot-instructions.md || status=1; \
	cp "$$tmp/CLAUDE.md" claude/CLAUDE.md; \
	cp "$$tmp/copilot-instructions.md" copilot/instructions/copilot-instructions.md; \
	rm -rf "$$tmp"; \
	if [ "$$status" -ne 0 ]; then \
		echo "Generated files drift from their sources; run 'make generate' and commit."; \
		exit 1; \
	fi; \
	echo "Generated files match their sources."
