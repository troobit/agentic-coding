# Development tooling for agentic-coding.
#
# bootstrap one-script new-machine setup (scripts/bootstrap.sh)
# generate  rebuild the checked-in generated files (claude/CLAUDE.md,
#           copilot/instructions/copilot-instructions.md, codex/AGENTS.md)
#           and MCP configs
# sync      sync Claude/VS Code links plus Codex skills, instructions, and MCP
# align     align this repository's own agent configs
# status    read-only process-status report over participating repos
#           (this repo plus the checked-in default list; pass explicit
#           paths via REPOS="path1 path2")
# test      run the Python unittest suite
# lint      shellcheck all shell scripts + fail if generated files drift
#           from their sources in shared/ and mcp/

.PHONY: bootstrap generate sync sync-claude sync-codex align status local-next-task test test-local-next-task test-codex lint lint-shell lint-drift

bootstrap:
	scripts/bootstrap.sh

generate:
	python3 scripts/generate.py

sync:
	$(MAKE) sync-claude
	$(MAKE) sync-codex

sync-claude:
	scripts/sync-claude.sh

sync-codex:
	scripts/sync-codex.sh

align:
	python3 scripts/align.py

status:
	python3 scripts/process_status.py $(REPOS)

# TASKS is an explicit path, including when the target is in another repo.
local-next-task:
	python3 scripts/local_next_task.py "$(TASKS)" $(ARGS)

test:
	python3 -m unittest discover -s tests
	cd scripts && python3 -m unittest discover -s tests -t .

test-local-next-task:
	python3 -m unittest discover -s tests -p 'test_local_next_task.py'

# Opt-in native skill discovery through the installed Codex app server.
test-codex:
	AGENTIC_CODEX_INTEGRATION=1 python3 -m unittest discover -s tests -p 'test_sync_codex.py'

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
	cp codex/AGENTS.md "$$tmp/AGENTS.md"; \
	python3 scripts/generate.py; \
	status=0; \
	diff -u "$$tmp/CLAUDE.md" claude/CLAUDE.md || status=1; \
	diff -u "$$tmp/copilot-instructions.md" copilot/instructions/copilot-instructions.md || status=1; \
	diff -u "$$tmp/AGENTS.md" codex/AGENTS.md || status=1; \
	cp "$$tmp/CLAUDE.md" claude/CLAUDE.md; \
	cp "$$tmp/copilot-instructions.md" copilot/instructions/copilot-instructions.md; \
	cp "$$tmp/AGENTS.md" codex/AGENTS.md; \
	rm -rf "$$tmp"; \
	if [ "$$status" -ne 0 ]; then \
		echo "Generated files drift from their sources; run 'make generate' and commit."; \
		exit 1; \
	fi; \
	echo "Generated files match their sources."
