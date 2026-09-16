"""Contract tests for scripts/ui_corpus_ingest.py (smolspec ui-ux-corpus).

Four properties, one per requirement the corpus rests on:

  Req 2  the verbatim comment round-trips out of the file it was written into,
         including when the comment itself contained a fenced block;
  Req 4  ingestion is idempotent — a second run over identical input writes
         nothing and leaves every file byte-identical;
  Req 5  human triage survives re-ingestion, including when the upstream
         comment was edited in spadre;
  Req 6  the epoch splits the real 14-comment snapshot 1/13, and the two
         override lists invert a decision in either direction.

The Req 6 test runs against the archived snapshot of the live variant stores at
~/.openclaw/workspace/ui-corpus/raw when it is present, and skips when it is
not, so the suite passes on a machine that has never run spadre.

Run with: python3 -m unittest discover -s tests
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import ui_corpus_ingest as ingest  # noqa: E402

SNAPSHOT = Path.home() / ".openclaw" / "workspace" / "ui-corpus" / "raw"
READER = Path.home() / ".openclaw" / "workspace" / "bin" / "spadre-variant-comments.sh"


def record(**overrides):
    base = {
        "product": "spadre",
        "variant": "B",
        "port": 5175,
        "url": "http://100.82.39.26:5175/",
        "threadId": "01a0a32a-6c0c-7251-b5cf-6d4bb26cd96d",
        "commentId": "01a0a32a-6c0d-7308-b3fd-59b0939f0c47",
        "deployment": "localhost",
        "docId": "mobile-ui/mobile-ui-review.md",
        "versionId": "v1",
        "threadState": "open",
        "anchor": {"startLine": 18, "endLine": 18, "quote": "## 1. Landing screen"},
        "anchorLabel": "L18 — '## 1. Landing screen'",
        "authorId": "01a0963a-eda1-777a-bd47-c0e5094a9ba5",
        "displayName": "Gratin",
        "role": "user",
        "body": "i like the scroll",
        "createdAt": "2026-09-15T03:44:21.514Z",
        "editedAt": None,
    }
    base.update(overrides)
    return base


class CorpusCase(unittest.TestCase):
    """A throwaway corpus root with the real ingest.json copied in."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.corpus = Path(self.tmp) / "ui-ux"
        (self.corpus / "observations").mkdir(parents=True)
        shutil.copy(REPO_ROOT / "ui-ux" / "ingest.json", self.corpus / "ingest.json")

    def run_ingest(self, records, today="2026-09-16"):
        return ingest.ingest(records, str(self.corpus), today)

    def observations(self):
        return sorted((self.corpus / "observations").glob("*.md"))

    def only_observation(self):
        files = self.observations()
        self.assertEqual(len(files), 1, "expected exactly one observation, got %s" % files)
        return files[0]

    def set_config(self, **keys):
        path = self.corpus / "ingest.json"
        config = json.loads(path.read_text())
        config.update(keys)
        path.write_text(json.dumps(config))


class VerbatimTest(CorpusCase):
    """Req 2 — the comment is stored byte-for-byte and comes back out."""

    def test_plain_body_round_trips(self):
        self.run_ingest([record()])
        text = self.only_observation().read_text()
        self.assertEqual(ingest.read_verbatim(text), "i like the scroll")

    def test_body_containing_a_fence_round_trips(self):
        body = "the gap here:\n\n```css\ngap: 4px;\n```\n\nis too tight"
        self.run_ingest([record(body=body)])
        text = self.only_observation().read_text()
        self.assertEqual(ingest.read_verbatim(text), body)

    def test_nothing_is_guessed(self):
        self.run_ingest([record()])
        text = self.only_observation().read_text()
        self.assertIn("concerns: []", text)
        self.assertIn('sentiment: "unclear"', text)
        self.assertIn('status: "untriaged"', text)


class IdempotencyTest(CorpusCase):
    """Req 4 — re-running changes nothing, so a no-change run is a clean tree."""

    def test_second_run_is_unchanged_and_writes_nothing(self):
        first = self.run_ingest([record()])
        self.assertEqual(first["new"], 1)

        path = self.only_observation()
        before = path.read_bytes()
        stat = path.stat().st_mtime_ns

        # A later --today must not re-stamp an observation already ingested.
        second = self.run_ingest([record()], today="2026-10-01")
        self.assertEqual(second, {"new": 0, "updated": 0, "unchanged": 1, "excluded": 0})
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(path.stat().st_mtime_ns, stat)
        self.assertEqual(len(self.observations()), 1)

    def test_two_comments_in_one_thread_get_separate_files(self):
        # Sibling UUIDv7s share a long prefix, so the file name is built from the
        # random tail. Two comments a millisecond apart must not collide.
        self.run_ingest([
            record(commentId="01a0a32a-6c0d-7308-b3fd-59b0939f0c47"),
            record(commentId="01a0a32a-6c0d-7308-b3fd-59b0939f0c48", body="and the rail"),
        ])
        self.assertEqual(len(self.observations()), 2)


class TriagePreservationTest(CorpusCase):
    """Req 5 — the machine owns provenance, a human owns everything else."""

    TRIAGE = "## Reading\n\nThe caret handle is the thing being praised.\n"

    def triage(self, path):
        text = path.read_text()
        text = text.replace("concerns: []", 'concerns: ["scrolling", "touch-targets"]')
        text = text.replace('sentiment: "unclear"', 'sentiment: "affirm"')
        text = text.replace('status: "untriaged"', 'status: "triaged"')
        text = text.replace("principles: []", 'principles: ["UX-001"]')
        head, _ = text.split(ingest.TRIAGE_MARKER, 1)
        path.write_text(head + ingest.TRIAGE_MARKER + "\n\n" + self.TRIAGE)

    def test_triage_survives_an_unchanged_reingest(self):
        self.run_ingest([record()])
        path = self.only_observation()
        self.triage(path)

        summary = self.run_ingest([record()])
        self.assertEqual(summary["unchanged"], 1)

        text = path.read_text()
        self.assertIn('concerns: ["scrolling", "touch-targets"]', text)
        self.assertIn('sentiment: "affirm"', text)
        self.assertIn('principles: ["UX-001"]', text)
        self.assertIn("The caret handle is the thing being praised.", text)

    def test_triage_survives_an_upstream_edit(self):
        self.run_ingest([record()])
        path = self.only_observation()
        self.triage(path)

        edited = record(body="i like the scroll, on the doc page",
                        editedAt="2026-09-17T09:00:00.000Z")
        summary = self.run_ingest([edited], today="2026-10-01")
        self.assertEqual(summary["updated"], 1)

        text = path.read_text()
        # provenance follows the source...
        self.assertEqual(ingest.read_verbatim(text), "i like the scroll, on the doc page")
        self.assertIn('edited: "2026-09-17T09:00:00.000Z"', text)
        self.assertIn('ingested: "2026-09-16"', text)
        # ...and the human's work is untouched.
        self.assertIn('sentiment: "affirm"', text)
        self.assertIn("The caret handle is the thing being praised.", text)


class StickyProvenanceTest(CorpusCase):
    """All eight instances now share one store, so a thread records nothing about
    the port it was written on and the reader reports `variant: null`. An earlier
    run, reading the per-worktree stores, did know. Unknown must not overwrite
    known — that is evidence silently downgraded, not an update."""

    def test_null_variant_does_not_erase_a_recorded_one(self):
        self.run_ingest([record()])
        self.assertIn('source_variant: "B"', self.only_observation().read_text())

        result = self.run_ingest([record(variant=None, port=None, url=None)])
        text = self.only_observation().read_text()
        self.assertEqual(result["unchanged"], 1, "a null downgrade is not a change")
        self.assertIn('source_variant: "B"', text)
        self.assertIn('source_url: "http://100.82.39.26:5175/"', text)

    def test_a_first_sighting_with_no_variant_records_null(self):
        self.run_ingest([record(variant=None, port=None, url=None)])
        text = self.only_observation().read_text()
        self.assertIn("source_variant: null", text)
        self.assertIn("source_url: null", text)

    def test_a_known_variant_still_overwrites_a_different_known_one(self):
        self.run_ingest([record()])
        self.run_ingest([record(variant="F", port=5179, url="http://100.82.39.26:5179/")])
        self.assertIn('source_variant: "F"', self.only_observation().read_text())


class EpochTest(CorpusCase):
    """Req 6 — real review separated from seed data by time, not identity."""

    def test_epoch_admits_and_declines(self):
        seed = record(commentId="01a09656-3897-754d-a721-a7b1d4094738",
                      createdAt="2026-09-12T15:57:08.117Z", body="Does the rail show this?")
        summary = self.run_ingest([record(), seed])
        self.assertEqual(summary["new"], 1)
        self.assertEqual(summary["excluded"], 1)
        self.assertIn("01a09656-3897-754d-a721-a7b1d4094738",
                      (self.corpus / "excluded.md").read_text())

    def test_same_author_lands_on_both_sides_of_the_epoch(self):
        # The case that kills every author allowlist: Gratin wrote one seeded
        # note and one real comment. Only the real one is ingested.
        seed = record(commentId="01a09656-3897-754d-a721-a7b1d4094738",
                      createdAt="2026-09-12T15:57:08.117Z")
        self.run_ingest([record(), seed])
        kept = self.only_observation().read_text()
        self.assertIn('author: "Gratin"', kept)
        self.assertIn('created: "2026-09-15', kept)

    def test_force_include_overrides_the_epoch(self):
        seed = record(commentId="01a09656-3897-754d-a721-a7b1d4094738",
                      createdAt="2026-09-12T15:57:08.117Z")
        self.set_config(force_include=["01a09656-3897-754d-a721-a7b1d4094738"])
        summary = self.run_ingest([seed])
        self.assertEqual(summary["new"], 1)
        self.assertEqual(summary["excluded"], 0)

    def test_force_exclude_overrides_the_epoch(self):
        self.set_config(force_exclude=["01a0a32a-6c0d-7308-b3fd-59b0939f0c47"])
        summary = self.run_ingest([record()])
        self.assertEqual(summary["new"], 0)
        self.assertEqual(summary["excluded"], 1)
        self.assertIn("force_exclude", (self.corpus / "excluded.md").read_text())

    def test_nothing_is_dropped_silently(self):
        seeds = [record(commentId="01a09656-3897-754d-a721-a7b1d409473%d" % n,
                        createdAt="2026-09-12T15:57:08.117Z") for n in range(4)]
        self.run_ingest(seeds)
        ledger = (self.corpus / "excluded.md").read_text()
        for seed in seeds:
            self.assertIn(seed["commentId"], ledger)


class SnapshotTest(CorpusCase):
    """Req 6 against the real archived threads, through the real reader."""

    def setUp(self):
        if not SNAPSHOT.is_dir() or not READER.is_file():
            self.skipTest("no spadre snapshot or reader on this machine")
        super().setUp()

    def test_fourteen_threads_split_one_and_thirteen(self):
        feed = subprocess.run(
            [str(READER), "--json", "--all", "--archive", str(SNAPSHOT)],
            capture_output=True, text=True, check=True).stdout
        records = json.loads(feed)
        self.assertEqual(len(records), 14)

        summary = self.run_ingest(records)
        self.assertEqual(summary["new"], 1)
        self.assertEqual(summary["excluded"], 13)

        text = self.only_observation().read_text()
        self.assertEqual(
            ingest.read_verbatim(text),
            "The thumb tap for caret here is good, but vertically not in the "
            "middle of the text to which it refers.")


if __name__ == "__main__":
    unittest.main()
