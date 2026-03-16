from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from riftoracle.collect import CollectorSettings, build_paths, main, parse_args


class CollectorCliTests(unittest.TestCase):
    def test_parse_args_uses_local_default_output_root(self) -> None:
        args = parse_args(["--matches-per-tier", "25"])

        self.assertEqual(args.matches_per_tier, 25)
        self.assertEqual(args.output_root, Path("data-collection"))

    def test_build_paths_derives_expected_files(self) -> None:
        paths = build_paths("custom-data")

        self.assertEqual(paths.state_file, Path("custom-data") / "state.json")
        self.assertEqual(paths.csv_file, Path("custom-data") / "match_ids.csv")
        self.assertEqual(paths.matches_dir, Path("custom-data") / "matches")

    @patch("riftoracle.collect.RiotCollector.collect_data")
    @patch("riftoracle.collect.load_settings_from_env")
    def test_main_uses_parsed_arguments(self, mock_load_settings, mock_collect_data) -> None:
        mock_load_settings.return_value = CollectorSettings(api_key="test-key")

        main(["--matches-per-tier", "7", "--output-root", "local-data"])

        mock_load_settings.assert_called_once()
        mock_collect_data.assert_called_once_with(matches_per_tier=7)


if __name__ == "__main__":
    unittest.main()
