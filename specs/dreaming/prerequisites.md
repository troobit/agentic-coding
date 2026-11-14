# Prerequisites for Dreaming

These tasks must be completed by the user before or during implementation. The tasks assume a new repository with a branch named `dreaming` checked out, containing this spec under `specs/dreaming/`.

## Before Starting
- [ ] Create the repository, check out the branch `dreaming`, copy `specs/dreaming/` into it, and decide whether it is public or private; scan rules for public repositories apply to it as a target repository (9.12).
- [ ] Confirm `uv`, Python 3.12+, `rune`, `apsis` and `git` are on `PATH` for the shell that runs the agent.

## During Implementation
- [ ] Before task 4.3 (live probes) and task 17 (reader trial): Claude Code and Codex are logged in, LM Studio's server is running with a model loaded, and a few recorded sessions exist for apsis to read.
- [ ] Before task 3.2 (snapshot) is exercised against real data: create the private names file for the public-repository scan at a path outside every repository and set its path in `~/.dreaming/config.toml` (9.12).
- [ ] Before task 24 (adoption): list the target repositories in `~/.dreaming/config.toml` with their generate, lint, test and deploy commands, and mark which repositories are public. A repository without lint and test commands is proposal-only (9.8).

## Before Testing
- [ ] Before task 31 (end-to-end): `make install` has linked `~/.local/bin/dream`, and the `dream` skill from `skills/dream/` is installed where your harness reads skills.
