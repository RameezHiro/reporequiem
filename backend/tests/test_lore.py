"""Tests for the voice, the grounding boundary and the archaeology engine.

Run from the backend directory:

    python -m unittest discover -s tests -v

The suite builds the bundled haunted fixture once and needs git, but no model,
no network and no API key.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import lore
from archaeology import _normalize_public_url, analyze, record_facts

BACKEND = Path(__file__).resolve().parents[1]
DEMO_SCRIPT = BACKEND.parent / "scripts" / "make_demo_repo.py"


def _fixture_env() -> dict[str, str]:
    return {
        **os.environ,
        "GIT_AUTHOR_NAME": "Fixture",
        "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
        "GIT_COMMITTER_NAME": "Fixture",
        "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
        "GIT_AUTHOR_DATE": "2019-02-14T09:00:00+00:00",
        "GIT_COMMITTER_DATE": "2019-02-14T09:00:00+00:00",
    }


@unittest.skipUnless(shutil.which("git"), "git is required")
class FixtureRecordTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.mkdtemp(prefix="requiem-test-")
        cls.repo = Path(cls.tmp) / "lumen-mail"
        subprocess.run(
            [sys.executable, str(DEMO_SCRIPT), str(cls.repo)],
            check=True,
            capture_output=True,
            timeout=180,
            env=_fixture_env(),
        )
        cls.record = analyze(str(cls.repo), 1000)

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    # ---- archaeology ---------------------------------------------------

    def test_commits_and_souls_are_read(self) -> None:
        self.assertEqual(self.record["totals"]["commits"], 18)
        self.assertEqual(self.record["totals"]["souls"], 3)
        self.assertGreater(self.record["life"]["lifespan_days"], 1000)

    def test_buried_files_have_lifespans_and_killers(self) -> None:
        self.assertTrue(self.record["ghosts"])
        for ghost in self.record["ghosts"]:
            self.assertTrue(ghost["path"])
            self.assertIn("killed_by", ghost)
            self.assertGreaterEqual(ghost["age_days"], 0)
            self.assertEqual(ghost["kind"], "buried")

    def test_the_fixture_has_a_revenant_and_an_extinct_language(self) -> None:
        self.assertTrue(self.record["revenants"])
        languages = {item["language"] for item in self.record["extinct"]}
        self.assertIn("CoffeeScript", languages)

    def test_cursed_commits_are_detected(self) -> None:
        titles = {item["title"] for item in self.record["cursed"]}
        self.assertTrue(titles)
        self.assertTrue(any("3 A.M." in title for title in titles))

    def test_facts_are_plain_text_not_json(self) -> None:
        facts = record_facts(self.record)
        self.assertIn("REPOSITORY:", facts)
        self.assertIn("THE BURIED", facts)
        self.assertNotIn("{", facts)
        self.assertIn(self.record["ghosts"][0]["path"], facts)


class PublicUrlTest(unittest.TestCase):
    def test_bare_owner_repo_defaults_to_github(self) -> None:
        self.assertEqual(
            _normalize_public_url("pallets/flask"), "https://github.com/pallets/flask"
        )

    def test_host_prefixed_input_gains_a_scheme(self) -> None:
        self.assertEqual(
            _normalize_public_url("github.com/octocat/Hello-World"),
            "https://github.com/octocat/Hello-World",
        )
        self.assertEqual(
            _normalize_public_url("gitlab.com/group/project"),
            "https://gitlab.com/group/project",
        )

    def test_full_https_url_is_unchanged(self) -> None:
        url = "https://codeberg.org/forgejo/forgejo"
        self.assertEqual(_normalize_public_url(url), url)

    def test_other_schemes_are_not_rewritten(self) -> None:
        self.assertEqual(
            _normalize_public_url("http://github.com/a/b"), "http://github.com/a/b"
        )
        self.assertEqual(
            _normalize_public_url("git@github.com:a/b.git"), "git@github.com:a/b.git"
        )


class ModelPickerTest(unittest.TestCase):
    def test_vision_model_alone_is_skipped(self) -> None:
        self.assertIsNone(lore._pick_model(["qwen3-vl:4b"]))

    def test_coder_alone_is_skipped(self) -> None:
        self.assertIsNone(lore._pick_model(["qwen2.5-coder:7b"]))

    def test_instruct_model_beats_coder(self) -> None:
        self.assertEqual(
            lore._pick_model(["qwen2.5-coder:7b", "gemma3:4b"]), "gemma3:4b"
        )

    def test_text_thinking_model_is_usable(self) -> None:
        self.assertEqual(lore._pick_model(["qwen3:8b"]), "qwen3:8b")


class JsonBoundaryTest(unittest.TestCase):
    RECORD = {
        "meta": {
            "name": "demo", "branch": "main", "head": "4d58a2fbb6",
            "commit_count": 18, "truncated": False, "max_commits": 1000,
            "root": "/tmp/demo", "remote": "", "scanned_at": "2026-01-01T00:00:00+00:00",
        },
        "life": {
            "first_commit": "2019-02-14T09:00:00+00:00",
            "last_commit": "2022-03-15T21:00:00+00:00",
            "lifespan_days": 1125,
            "silent_for_days": 1689,
            "abandoned": True,
            "last_words": "Final cleanup.",
            "last_author": "Ana Ruiz",
            "last_date": "2022-03-15T21:00:00+00:00",
        },
        "totals": {
            "commits": 18, "souls": 3, "files_live": 9, "files_vanished": 8,
            "added": 100, "deleted": 40, "unmerged_branches": 1,
        },
        "ghosts": [
            {
                "path": "src/sync.coffee", "kind": "buried", "age_days": 82,
                "commits": 7, "lines": 5, "churn": 20, "added": 10, "deleted": 10,
                "author": "Tomás Vega", "killed_by": "Mira Chen",
                "last_subject": "Retire CoffeeScript, port parser to JavaScript",
                "commit": "05346136c3", "born": "2019-04-18T09:00:00+00:00",
                "died": "2019-07-09T12:00:00+00:00", "language": "CoffeeScript",
                "last_lines": "", "buried_note": "",
            },
            {
                "path": "src/parser.coffee", "kind": "buried", "age_days": 145,
                "commits": 4, "lines": 9, "churn": 18, "added": 9, "deleted": 9,
                "author": "Mira Chen", "killed_by": "Mira Chen",
                "last_subject": "Retire CoffeeScript, port parser to JavaScript",
                "commit": "05346136c3", "born": "2019-02-14T09:00:00+00:00",
                "died": "2019-07-09T12:00:00+00:00", "language": "CoffeeScript",
                "last_lines": "", "buried_note": "",
            },
        ],
        "revenants": [], "forgotten": [], "cursed": [], "extinct": [],
        "authors": [], "branches": [], "timeline": [],
    }

    def test_extracts_plain_json(self) -> None:
        self.assertEqual(lore._extract_json('{"a": 1}'), {"a": 1})

    def test_extracts_fenced_json(self) -> None:
        raw = '```json\n{"a": 1}\n```'
        self.assertEqual(lore._extract_json(raw), {"a": 1})

    def test_extracts_json_from_surrounding_prose(self) -> None:
        raw = 'Here is the record:\n{"a": 1}\nThe archive is quiet.'
        self.assertEqual(lore._extract_json(raw), {"a": 1})

    def test_rejects_unparseable_output(self) -> None:
        with self.assertRaises(lore.ModelUnavailable):
            lore._extract_json("no object here")

    def test_validation_drops_unknown_lament_paths(self) -> None:
        payload = {
            "epitaph": "demo: 2019 - 2022",
            "inscription": "Eight files were removed and never returned.",
            "haunting": [
                {"title": "First", "text": "x" * 150},
                {"title": "Second", "text": "y" * 150},
                {"title": "Third", "text": "z" * 150},
            ],
            "laments": [
                {"path": "src/sync.coffee", "text": "I was sync."},
                {"path": "../../etc/passwd", "text": "I was never here."},
            ],
        }
        out = lore._validate_lore(payload, self.RECORD)
        self.assertEqual(set(out["laments"]), {"src/sync.coffee"})

    def test_validation_rejects_a_thin_reply(self) -> None:
        with self.assertRaises(lore.ModelUnavailable):
            lore._validate_lore(
                {"epitaph": "x", "inscription": "y", "haunting": []},
                self.RECORD,
            )

    def test_fallback_lore_is_grounded_and_complete(self) -> None:
        out = lore.fallback_lore(self.RECORD)
        self.assertEqual(out["source"]["engine"], "fallback")
        self.assertTrue(out["epitaph"])
        self.assertGreaterEqual(len(out["haunting"]), 2)
        known = {g["path"] for g in self.RECORD["ghosts"]}
        self.assertTrue(set(out["laments"]) <= known)


class FallbackPathTest(unittest.TestCase):
    """The model may be absent; the record must still be spoken."""

    def test_generate_lore_falls_back_when_chat_fails(self) -> None:
        record = JsonBoundaryTest.RECORD
        with mock.patch.object(lore, "chat", side_effect=lore.ModelUnavailable("no model")):
            out = lore.generate_lore(record)
        self.assertEqual(out["source"]["engine"], "fallback")
        self.assertIn("no model", out["source"]["reason"])
        self.assertTrue(out["epitaph"])

    def test_seance_falls_back_to_the_retrieved_file(self) -> None:
        record = JsonBoundaryTest.RECORD
        question = "Who deleted src/sync.coffee?"
        with mock.patch.object(lore, "chat", side_effect=lore.ModelUnavailable("no model")):
            out = lore.answer_seance(record, question)
        self.assertEqual(out["engine"], "fallback")
        self.assertIn("src/sync.coffee", out["matched"])
        self.assertIn("src/sync.coffee", out["answer"])


if __name__ == "__main__":
    unittest.main()
