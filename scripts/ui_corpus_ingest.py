#!/usr/bin/env python3
"""Turn spadre review comments into UI/UX corpus observations, idempotently.

Reads the JSON feed produced by the spadre variant comment reader:

    ~/.openclaw/workspace/bin/spadre-variant-comments.sh --json --all \\
      | python3 scripts/ui_corpus_ingest.py

This script contains no knowledge of spadre's thread schema — the reader is the
only place that knows it (see specs/ui-ux-corpus/decision_log.md, Decision 5).
What it knows is the corpus: how an observation file is laid out, which half of
it the machine owns, and which half a human owns.

The contract, in one paragraph. Each source comment becomes one file under
ui-ux/observations/, named from the comment's own stable id, so re-running is a
no-op. The machine owns the provenance frontmatter and the verbatim block; a
human owns `concerns`, `sentiment`, `status`, `principles` and everything below
the `<!-- triage -->` marker, and re-ingestion carries all of that across
untouched. Nothing is guessed: a new observation lands untriaged with no
concerns and no sentiment. Nothing is dropped silently: a comment the epoch rule
declines is written to ui-ux/excluded.md with its reason.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CORPUS = os.path.join(REPO, "ui-ux")

TRIAGE_MARKER = "<!-- triage -->"
HUMAN_KEYS = ("concerns", "sentiment", "status", "principles")

# Provenance the reader can lose but never re-derive. All instances now share one
# store, so a thread no longer records which port it was written on and the reader
# reports null. Null must not overwrite a value an earlier, better-informed run
# recorded — losing "variant B" to "unknown" is a silent downgrade of evidence.
STICKY_KEYS = ("source_variant", "source_url")

DEFAULT_TRIAGE = """## Reading

_Untriaged._ Set `concerns` and `sentiment` in the frontmatter, then write what this
tells us about the interface — and what it does not. A thin comment stays thin; do
not invent rationale it does not contain.

## Uncertain

_Nothing recorded yet._
"""

LEDGER_HEADER = """# Excluded comments

Comments the ingest declined, and why. Nothing is dropped silently
(`../specs/ui-ux-corpus/decision_log.md`, Decision 4).

To overturn a decision, add the comment id to `force_include` in `ingest.json` and
re-run; to decline something the epoch rule admitted, add it to `force_exclude`.
Comment ids are stable, so an override is a permanent correction.

| Created | Author | Variant | Comment id | Reason | Body |
|---|---|---|---|---|---|
"""


# --------------------------------------------------------------------------
# classification


def load_config(corpus):
    path = os.path.join(corpus, "ingest.json")
    with open(path) as fh:
        return json.load(fh)


def classify(record, config):
    """('review', None) or ('excluded', reason).

    The split is by time, not identity — see decision_log.md Decision 2. The two
    override lists key on comment id, which is stable, so a correction sticks.
    """
    comment_id = record.get("commentId") or ""
    if comment_id in config.get("force_exclude", []):
        return "excluded", "force_exclude in ingest.json"
    if comment_id in config.get("force_include", []):
        return "review", None

    created = (record.get("createdAt") or "")[:10]
    if not created:
        return "excluded", "no createdAt on the comment"

    epoch = config.get("epoch") or ""
    if epoch and created < epoch:
        return "excluded", "before the %s epoch (pre-corpus seed data)" % epoch
    return "review", None


# --------------------------------------------------------------------------
# rendering


def scalar(value):
    """A YAML scalar we can round-trip. JSON string syntax is a valid YAML
    double-quoted scalar, which saves hand-rolling an escaper."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    return json.dumps(str(value), ensure_ascii=False)


def fence_for(body):
    """A backtick fence longer than any run inside the body, so the verbatim
    block round-trips whatever the comment contained."""
    longest = max([len(m) for m in re.findall(r"`+", body)] or [0])
    return "`" * max(3, longest + 1)


def observation_name(record):
    """<created date>-<last 12 of the comment id>. The tail of a UUIDv7 is the
    random part; the head is a millisecond timestamp two comments in one thread
    can share."""
    created = (record.get("createdAt") or "")[:10]
    tail = (record.get("commentId") or "").replace("-", "")[-12:]
    return "%s-%s" % (created, tail)


def anchor_fields(record):
    anchor = record.get("anchor")
    if not anchor:
        return None, None
    start, end = anchor.get("startLine"), anchor.get("endLine")
    lines = str(start) if start == end else "%s-%s" % (start, end)
    return lines, (anchor.get("quote") or "").strip()


def machine_frontmatter(record, classification, ingested, sticky=None):
    lines, quote = anchor_fields(record)
    pairs = [
        ("id", record.get("commentId")),
        ("thread", record.get("threadId")),
        ("author", record.get("displayName")),
        ("author_id", record.get("authorId")),
        ("role", record.get("role")),
        ("created", record.get("createdAt")),
        ("edited", record.get("editedAt")),
        ("classification", classification),
        ("ingested", ingested),
        ("source_product", record.get("product")),
        ("source_variant", record.get("variant")),
        ("source_url", record.get("url")),
        ("source_deployment", record.get("deployment")),
        ("source_doc_id", record.get("docId")),
        ("source_version_id", record.get("versionId")),
        ("source_thread_state", record.get("threadState")),
        ("source_anchor_lines", lines),
        ("source_anchor_quote", quote),
    ]
    sticky = sticky or {}
    out = []
    for key, value in pairs:
        if value is None and key in sticky:
            out.append("%s: %s" % (key, sticky[key]))
        else:
            out.append("%s: %s" % (key, scalar(value)))
    return out


def default_human_frontmatter():
    return [
        "concerns: []",
        'sentiment: "unclear"',
        'status: "untriaged"',
        "principles: []",
    ]


def machine_body(record, name):
    body = record.get("body", "")
    fence = fence_for(body)
    return "# Observation %s\n\n## Verbatim\n\n%stext\n%s\n%s\n" % (name, fence, body, fence)


def render(record, classification, ingested, human_frontmatter, human_body, sticky=None):
    name = observation_name(record)
    front = machine_frontmatter(record, classification, ingested, sticky) + list(human_frontmatter)
    return "---\n%s\n---\n\n%s\n%s\n\n%s" % (
        "\n".join(front),
        machine_body(record, name),
        TRIAGE_MARKER,
        human_body.lstrip("\n"),
    )


# --------------------------------------------------------------------------
# reading an existing observation back


def split_existing(text):
    """(human frontmatter lines, human body, ingested date, sticky provenance).

    The human-owned half is recovered because the machine half is rebuilt from the
    source record every run. STICKY_KEYS come back too: those are machine-owned but
    the reader can no longer supply them, so the file on disk is the better source.
    Frontmatter lines are carried across verbatim rather than parsed, so a human
    can put whatever YAML they like in their own keys.
    """
    human_front = list(default_human_frontmatter())
    human_body = DEFAULT_TRIAGE
    ingested = None
    sticky = {}

    if not text.startswith("---\n"):
        return human_front, human_body, ingested, sticky

    _, front, rest = text.split("---\n", 2)
    kept = {}
    for line in front.splitlines():
        key = line.split(":", 1)[0].strip()
        if key in HUMAN_KEYS:
            kept[key] = line
        elif key in STICKY_KEYS:
            value = line.split(":", 1)[1].strip()
            if value and value not in ('""', "null"):
                sticky[key] = value
        elif key == "ingested":
            ingested = json.loads(line.split(":", 1)[1].strip() or '""') or None
    if kept:
        human_front = [kept.get(k, d) for k, d in zip(HUMAN_KEYS, default_human_frontmatter())]

    if TRIAGE_MARKER in rest:
        human_body = rest.split(TRIAGE_MARKER, 1)[1].lstrip("\n")
    return human_front, human_body, ingested, sticky


def read_verbatim(text):
    """The comment body exactly as ingested. Proves the fenced block round-trips."""
    match = re.search(r"## Verbatim\n\n(`{3,})text\n(.*?)\n\1\n", text, re.DOTALL)
    return match.group(2) if match else None


# --------------------------------------------------------------------------
# the excluded ledger


def read_ledger(path):
    """{comment id: row cells}. The ledger is merged rather than rewritten, so a
    run against one source does not forget what another source excluded."""
    rows = {}
    if not os.path.isfile(path):
        return rows
    with open(path) as fh:
        for line in fh:
            if not line.startswith("| ") or line.startswith("|---"):
                continue
            cells = [c.strip().replace("\\|", "|") for c in line.strip().strip("|").split("|")]
            if len(cells) == 6 and cells[0] != "Created":
                rows[cells[3]] = cells
    return rows


def ledger_row(record, reason):
    body = " ".join((record.get("body") or "").split())
    if len(body) > 70:
        body = body[:69] + "…"
    cells = [
        (record.get("createdAt") or "")[:16] + "Z",
        record.get("displayName") or "?",
        record.get("variant") or "?",
        record.get("commentId") or "?",
        reason,
        body,
    ]
    return [c.replace("|", "\\|") for c in cells]


def render_ledger(rows):
    ordered = sorted(rows.values(), key=lambda c: (c[0], c[3]))
    body = "".join("| %s |\n" % " | ".join(cells) for cells in ordered)
    return LEDGER_HEADER + (body or "| _(none)_ | | | | | |\n")


# --------------------------------------------------------------------------
# ingest


def count_untriaged(observations_dir):
    total = untriaged = 0
    for name in sorted(os.listdir(observations_dir)):
        if not name.endswith(".md"):
            continue
        total += 1
        with open(os.path.join(observations_dir, name)) as fh:
            if re.search(r'^status:\s*"?untriaged"?\s*$', fh.read(), re.MULTILINE):
                untriaged += 1
    return untriaged, total


def ingest(records, corpus, today, dry_run=False):
    config = load_config(corpus)
    observations = os.path.join(corpus, "observations")
    ledger_path = os.path.join(corpus, "excluded.md")
    if not dry_run:
        os.makedirs(observations, exist_ok=True)

    summary = {"new": 0, "updated": 0, "unchanged": 0, "excluded": 0}
    ledger = read_ledger(ledger_path)
    seen = {}

    for record in records:
        classification, reason = classify(record, config)
        comment_id = record.get("commentId") or ""

        if classification == "excluded":
            summary["excluded"] += 1
            ledger[comment_id] = ledger_row(record, reason)
            continue

        ledger.pop(comment_id, None)
        name = observation_name(record)
        path = os.path.join(observations, name + ".md")

        if name in seen and seen[name] != comment_id:
            raise SystemExit(
                "observation name collision: %s claimed by both %s and %s"
                % (name, seen[name], comment_id)
            )
        seen[name] = comment_id

        existing = None
        if os.path.isfile(path):
            with open(path) as fh:
                existing = fh.read()

        human_front, human_body, ingested, sticky = split_existing(existing or "")
        rendered = render(record, classification, ingested or today, human_front, human_body, sticky)

        if existing is None:
            summary["new"] += 1
        elif existing != rendered:
            summary["updated"] += 1
        else:
            summary["unchanged"] += 1
            continue

        if not dry_run:
            with open(path, "w") as fh:
                fh.write(rendered)

    if not dry_run:
        with open(ledger_path, "w") as fh:
            fh.write(render_ledger(ledger))

    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--from", dest="source", default="-",
                        help="JSON feed from spadre-variant-comments.sh --json (default: stdin)")
    parser.add_argument("--corpus", default=DEFAULT_CORPUS, help="corpus root (default: ui-ux/)")
    parser.add_argument("--today", default=date.today().isoformat(),
                        help="date stamped on new observations")
    parser.add_argument("--dry-run", action="store_true", help="report, write nothing")
    args = parser.parse_args(argv)

    if args.source == "-":
        records = json.load(sys.stdin)
    else:
        with open(args.source) as fh:
            records = json.load(fh)

    summary = ingest(records, args.corpus, args.today, dry_run=args.dry_run)

    print("ui-corpus ingest%s — %d records in" % (" (dry run)" if args.dry_run else "", len(records)))
    for key in ("new", "updated", "unchanged", "excluded"):
        print("  %-10s %d" % (key, summary[key]))

    observations = os.path.join(args.corpus, "observations")
    if os.path.isdir(observations):
        untriaged, total = count_untriaged(observations)
        print("  %-10s %d of %d observations" % ("untriaged", untriaged, total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
