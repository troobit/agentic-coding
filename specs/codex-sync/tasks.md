---
references:
    - specs/codex-sync/requirements.md
    - specs/codex-sync/design.md
    - specs/codex-sync/decision_log.md
---
# Codex Sync

- [x] 1. Codex sync exposes valid skills and user configuration independently of Claude, with isolated regression coverage

- [x] 2. GitHub and Terraform stay disabled for Codex while unrelated TOML and custom services are preserved

- [x] 3. Makefile and bootstrap run the separate sync paths, and native discovery verifies skills and server state

- [x] 4. Retired Awesome Copilot entries are removed across generated configs and exact Starwave invocation names are documented
