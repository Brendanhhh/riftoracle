from __future__ import annotations

import json
import unittest
from pathlib import Path

from riftoracle.data import load_match_examples, parse_match_payload


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_match.json"
WORKSPACE_TMP = Path(__file__).parent / "tmp"


class DataLoadingTests(unittest.TestCase):
    def test_parse_match_payload_builds_expected_label_and_aggregates(self) -> None:
        payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

        example = parse_match_payload(payload)

        self.assertEqual(example.match_id, "NA1_TEST_MATCH")
        self.assertEqual(example.label_blue_win, 1)
        self.assertEqual(example.blue.kills, 20.0)
        self.assertEqual(example.red.kills, 7.0)

    def test_load_match_examples_ignores_invalid_json_files(self) -> None:
        matches_dir = WORKSPACE_TMP / "matches"
        matches_dir.mkdir(parents=True, exist_ok=True)

        valid_path = matches_dir / "valid.json"
        valid_path.write_text(FIXTURE_PATH.read_text(encoding="utf-8"), encoding="utf-8")

        invalid_path = matches_dir / "invalid.json"
        invalid_path.write_text("{not json}", encoding="utf-8")

        examples = load_match_examples(matches_dir)

        invalid_path.unlink()
        valid_path.unlink()
        matches_dir.rmdir()
        WORKSPACE_TMP.rmdir()

        self.assertEqual(len(examples), 1)
        self.assertEqual(examples[0].match_id, "NA1_TEST_MATCH")

    def test_load_match_examples_requires_existing_directory(self) -> None:
        with self.assertRaises(FileNotFoundError):
            load_match_examples("does-not-exist")


if __name__ == "__main__":
    unittest.main()
