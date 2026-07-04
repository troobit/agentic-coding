#!/bin/bash
# One-script new-machine setup (Req 8, toolset-agnostic-starwave).
#
# Order (per design.md, "Bootstrap" section):
#   1. Homebrew (install if missing)
#   2. brew bundle against the repo Brewfile
#   3. Claude Code via its documented installer (if missing)
#   4. go install: orbit, mcp-devtools, and rune (rune's brew tap formula
#      is a broken placeholder — see the Brewfile comment)
#   5. mkdir -p ~/.claude and the VS Code User/ settings dir
#   6. scripts/sync-claude.sh (symlinks)
#   7. generate.py --user (user MCP configs, conventions, VS Code settings
#      merge — ALL JSON work is delegated to generate.py; this script does
#      no JSON manipulation, per Decision 12's rationale)
#   8. remove the superseded ~/.copilot/agents/prd.agent.md (Req 1.4)
#   9. print the remaining manual (authentication) steps
#
# Contract:
#   - Idempotent (Req 8.2): every step is safe to re-run; a second run on a
#     configured machine reports "already done" / "no changes" throughout.
#   - Per-step failure is reported and independent later steps still run
#     (Req 8.1); steps that need authentication that does not exist yet are
#     skipped with a report and appended to the manual-steps list.
#   - Preserve-don't-clobber (Req 8.4): the shell parts only create
#     directories and symlink via sync-claude.sh; the only removal is the
#     known stale ~/.copilot/agents/prd.agent.md. Managed-file merging is
#     generate.py's job.
#   - --dry-run prints what would happen without mutating anything.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VSCODE_USER_DIR="$HOME/Library/Application Support/Code/User"
STALE_PRD_AGENT="$HOME/.copilot/agents/prd.agent.md"

DRY_RUN=0
ANY_FAILED=0
MANUAL_STEPS=()

usage() {
    echo "usage: scripts/bootstrap.sh [--dry-run]"
    echo "  --dry-run   print what would happen without doing anything"
}

for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=1 ;;
        -h|--help) usage; exit 0 ;;
        *) echo "unknown argument: $arg" >&2; usage >&2; exit 2 ;;
    esac
done

step()    { printf '\n== %s\n' "$*"; }
did()     { echo "did: $*"; }
already() { echo "already done: $*"; }
would()   { echo "dry-run: would $*"; }
failed()  { echo "FAILED: $*"; ANY_FAILED=1; }
skipped() { echo "skipped: $*"; }

# Skip a step that cannot run yet (e.g. authentication does not exist);
# report it and add it to the manual-steps list so the closing message
# ("re-run scripts/bootstrap.sh after authenticating") picks it up.
skip_for_auth() {
    skipped "$1"
    MANUAL_STEPS+=("$2")
}

# ---------------------------------------------------------------- 1. Homebrew
step "Homebrew"
find_brew() {
    command -v brew && return 0
    # Fresh installs are not on PATH until the user's shell profile is set
    # up; look in the standard prefixes (Apple Silicon, then Intel).
    for b in /opt/homebrew/bin/brew /usr/local/bin/brew; do
        [ -x "$b" ] && { echo "$b"; return 0; }
    done
    return 1
}
BREW="$(find_brew || true)"
if [ -n "$BREW" ]; then
    already "Homebrew installed ($BREW)"
elif [ "$DRY_RUN" -eq 1 ]; then
    would "install Homebrew via the official installer"
else
    echo "installing Homebrew (official installer)"
    if /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"; then
        BREW="$(find_brew || true)"
        if [ -n "$BREW" ]; then
            did "installed Homebrew ($BREW)"
        else
            failed "Homebrew installer ran but brew was not found"
        fi
    else
        failed "Homebrew install (see output above)"
    fi
fi
# Make brew (and anything it installed) visible to the rest of this run.
[ -n "$BREW" ] && eval "$("$BREW" shellenv)"

# ------------------------------------------------------------- 2. brew bundle
# The Brewfile currently has no third-party taps. If one is ever added, it
# must be tapped AND trusted here before `brew bundle`, or the untrusted-tap
# prompt/failure blocks the whole bundle (brew bundle fetches everything up
# front and installs nothing if anything fails). Pattern:
#   brew tap <user/repo>
#   brew trust <user/repo> 2>/dev/null || true   # `brew trust` is newer brew only
step "brew bundle ($REPO_ROOT/Brewfile)"
if [ -z "$BREW" ]; then
    skipped "brew bundle (Homebrew not available)"
elif [ "$DRY_RUN" -eq 1 ]; then
    if brew bundle check --file="$REPO_ROOT/Brewfile" >/dev/null 2>&1; then
        already "all Brewfile dependencies installed"
    else
        would "run brew bundle to install missing Brewfile dependencies"
    fi
elif brew bundle check --file="$REPO_ROOT/Brewfile" >/dev/null 2>&1; then
    already "all Brewfile dependencies installed"
elif brew bundle --file="$REPO_ROOT/Brewfile"; then
    did "brew bundle installed missing dependencies"
else
    # Modern brew bundle is all-or-nothing: it fetches every formula first
    # and installs NOTHING if any fetch fails, so one broken formula blocks
    # the entire bundle. Report and keep going — a bundle failure must not
    # block the symlink steps.
    failed "brew bundle reported errors (see output above)"
fi

# -------------------------------------------------- 3. Claude Code installer
step "Claude Code"
if command -v claude >/dev/null 2>&1; then
    already "claude on PATH ($(command -v claude))"
elif [ "$DRY_RUN" -eq 1 ]; then
    would "install Claude Code via its documented installer (curl -fsSL https://claude.ai/install.sh | bash)"
else
    echo "installing Claude Code (documented installer)"
    if curl -fsSL https://claude.ai/install.sh | bash; then
        did "installed Claude Code"
    else
        failed "Claude Code installer (see output above)"
    fi
fi

# ------------------------------------ 4. go install orbit/devtools/rune
step "Go tools (orbit, mcp-devtools, rune)"
go_tool() { # go_tool <binary-name> <module@version>
    local bin="$1" module="$2" gobin
    if ! command -v go >/dev/null 2>&1; then
        skipped "go install $module (go not available; brew bundle installs it)"
        return
    fi
    gobin="$(go env GOPATH)/bin"
    if command -v "$bin" >/dev/null 2>&1 || [ -x "$gobin/$bin" ]; then
        already "$bin installed"
        return
    fi
    if [ "$DRY_RUN" -eq 1 ]; then
        would "go install $module"
        return
    fi
    if go install "$module"; then
        did "go install $module"
        command -v "$bin" >/dev/null 2>&1 \
            || echo "note: add $gobin to PATH so $bin is runnable"
    else
        # Public modules today, but a failure here is most likely network
        # or (for a future private module) missing authentication: report,
        # add to the manual list, and keep going.
        skip_for_auth "go install $module failed (network or auth?)" \
            "re-run 'go install $module' (or just re-run bootstrap)"
    fi
}
go_tool orbit "github.com/arjenschwarz/orbit/cmd/orbit@latest"
go_tool mcp-devtools "github.com/sammcj/mcp-devtools@latest"
# rune is a go install, not brew: its brew tap formula is a broken v0.0.0
# placeholder that blocked the whole bundle (see the Brewfile comment).
# Main package at the module root; public tags exist (verified 2026-07-04).
go_tool rune "github.com/arjenschwarz/rune@latest"

# ------------------------------------------------------ 5. target directories
step "Target directories"
make_dir() {
    if [ -d "$1" ]; then
        already "$1 exists"
    elif [ "$DRY_RUN" -eq 1 ]; then
        would "mkdir -p $1"
    elif mkdir -p "$1"; then
        did "created $1"
    else
        failed "mkdir -p $1"
    fi
}
make_dir "$HOME/.claude"
make_dir "$VSCODE_USER_DIR"

# ------------------------------------------------------------ 6. sync-claude
step "Symlinks (scripts/sync-claude.sh)"
if [ "$DRY_RUN" -eq 1 ]; then
    would "run scripts/sync-claude.sh (idempotent ln -sfn symlinks)"
elif "$SCRIPT_DIR/sync-claude.sh"; then
    did "sync-claude.sh"
else
    failed "sync-claude.sh (see output above)"
fi

# ------------------------------------------------------ 7. generate.py --user
step "User-level configs (scripts/generate.py --user)"
if ! command -v python3 >/dev/null 2>&1; then
    skipped "generate.py --user (python3 not available)"
elif [ "$DRY_RUN" -eq 1 ]; then
    would "run python3 scripts/generate.py --user (user MCP configs + VS Code settings merge; preserves unmanaged entries)"
elif python3 "$SCRIPT_DIR/generate.py" --user; then
    did "generate.py --user (per-file report above)"
else
    failed "generate.py --user (see output above)"
fi

# -------------------------------------------- 8. stale ~/.copilot PRD agent
step "Stale ~/.copilot PRD agent (Req 1.4)"
if [ -e "$STALE_PRD_AGENT" ] || [ -L "$STALE_PRD_AGENT" ]; then
    if [ "$DRY_RUN" -eq 1 ]; then
        would "remove $STALE_PRD_AGENT (superseded by copilot/agents/prd.agent.md in this repo)"
    elif rm "$STALE_PRD_AGENT"; then
        did "removed $STALE_PRD_AGENT (superseded by copilot/agents/prd.agent.md in this repo)"
    else
        failed "removing $STALE_PRD_AGENT"
    fi
else
    already "no stale $STALE_PRD_AGENT"
fi

# ------------------------------------------------------- 9. remaining manual
step "Remaining manual steps (Req 8.3)"
MANUAL_STEPS+=(
    "gh auth login                     # GitHub CLI"
    "claude                            # Claude Code login on first run"
    "Sign in to GitHub Copilot in VS Code"
    "export GITHUB_AUTH_TOKEN=\"Bearer <PAT>\"   # github MCP server for Claude; the 'Bearer ' prefix is required"
    "Provide the GitHub MCP token when a Copilot/VS Code MCP prompt asks for it (same 'Bearer <PAT>' value)"
    "codex login                       # restores peer review (peer-review-validator)"
    "Optional: install the gemini CLI for a second peer reviewer"
)
for s in "${MANUAL_STEPS[@]}"; do
    echo "  - $s"
done
echo
echo "re-run scripts/bootstrap.sh after authenticating"

exit "$ANY_FAILED"
