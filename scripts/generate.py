#!/usr/bin/env python3
"""Generate per-tool configuration from this repository's sources.

Sources: shared/*.md fragments and mcp/servers.json.
Python 3 stdlib only (Decision 12). Reusable logic lives in agentic_lib.py
so align.py can import it.

Usage:
  generate.py                 regenerate checked-in conventions outputs
  generate.py --user          user-level targets (Claude MCP, VS Code
                              mcp.json, VS Code settings merge)
  generate.py --repo PATH     per-repo .mcp.json + .vscode/mcp.json
  generate.py --cloud         print paste-ready cloud-agent MCP JSON
  generate.py --servers a,b   subset of canonical servers (default: all
                              applicable to the surface)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import agentic_lib  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user", action="store_true",
                        help="generate user-level configs")
    parser.add_argument("--repo", metavar="PATH",
                        help="generate per-repo MCP configs into PATH")
    parser.add_argument("--cloud", action="store_true",
                        help="print paste-ready cloud-agent MCP JSON")
    parser.add_argument("--servers", metavar="A,B",
                        help="comma-separated subset of canonical servers")
    args = parser.parse_args(argv)

    report: list = []
    subset = args.servers.split(",") if args.servers else None

    try:
        if args.repo:
            defs = agentic_lib.load_servers(REPO_ROOT / "mcp" / "servers.json")
            agentic_lib.generate_repo_configs(Path(args.repo), defs, subset,
                                              report)
        elif args.cloud:
            defs = agentic_lib.load_servers(REPO_ROOT / "mcp" / "servers.json")
            print(agentic_lib.emit_cloud_json(defs, subset))
        elif args.user:
            defs = agentic_lib.load_servers(REPO_ROOT / "mcp" / "servers.json")
            agentic_lib.generate_user_configs(defs, subset, report,
                                              repo_root=REPO_ROOT)
        else:
            agentic_lib.generate_conventions(REPO_ROOT, report)
    except agentic_lib.GenerationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    for line in report:
        print(line)
    if not report and not args.cloud:
        print("no changes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
