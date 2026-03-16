from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import cast

from riftoracle.data import parse_match_payload
from riftoracle.features import build_feature_matrix

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_match.json"


class FeatureMatrixTests(unittest.TestCase):
    def test_build_feature_matrix_returns_expected_columns_and_label(self) -> None:
        payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        example = parse_match_payload(cast(dict[str, object], payload))

        matrix = build_feature_matrix([example])

        self.assertEqual(
            matrix.feature_names,
            [
                "kills_diff",
                "deaths_diff",
                "assists_diff",
                "damage_to_champions_diff",
                "gold_earned_diff",
                "vision_score_diff",
                "total_minions_killed_diff",
                "neutral_minions_killed_diff",
                "kda_ratio_diff",
            ],
        )
        self.assertEqual(matrix.y, [1])
        self.assertEqual(matrix.X[0][:4], [13.0, -8.0, 21.0, 23000.0])


if __name__ == "__main__":
    unittest.main()
