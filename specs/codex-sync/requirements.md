# Codex Sync Requirements

1. `scripts/sync-codex.sh` MUST expose every visible, top-level repo directory
   containing `SKILL.md` through per-skill links in `~/.agents/skills`.
   Non-skill containers and hidden directories MUST be excluded.
2. Existing skills and foreign links MUST be preserved and conflicts reported.
   Dangling links into this repo's skills directory MUST be pruned.
3. Codex sync MUST generate user instructions and MCP settings from the existing
   shared sources, without changing Claude or VS Code configuration. `CODEX_HOME`
   MUST select the Codex config directory when set.
4. GitHub and Terraform MCP servers MUST be disabled for Codex, including after
   repeated syncs and full user-config generation. Other surfaces retain their
   existing server definitions.
   Transit MUST default to disabled for Codex while its local app is unavailable.
   Awesome Copilot MUST be removed from the canonical definitions and old
   generated entries MUST be deleted rather than preserved as custom servers.
5. `sync-claude.sh` MUST retain its Claude and VS Code links and stop modifying
   Codex configuration. `make sync` and bootstrap MUST run both sync scripts;
   `make sync-codex` MUST support Codex-only setup.
6. MCP updates MUST preserve unrelated TOML sections and custom MCP servers.
   Instructions without managed markers MUST be left alone and reported.
7. Validation MUST include Codex's native `skills/list` discovery and MCP listing,
   in addition to isolated filesystem regression tests and `make test`/`make lint`.
8. The known dangling `~/.codex/skills -> claude/skills` link and its legacy
   backup MUST be removed, and the directory restored for bundled system skills.
