from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .data import MatchExample


@dataclass(frozen=True)
class FeatureMatrix:
    X: list[list[float]]
    y: list[int]
    feature_names: list[str]


def _diff(blue: float, red: float) -> float:
    return float(blue - red)


def build_feature_matrix(examples: Iterable[MatchExample]) -> FeatureMatrix:
    """Build simple blue-minus-red differential features."""
    feature_names = [
        "kills_diff",
        "deaths_diff",
        "assists_diff",
        "damage_to_champions_diff",
        "gold_earned_diff",
        "vision_score_diff",
        "total_minions_killed_diff",
        "neutral_minions_killed_diff",
        "kda_ratio_diff",
    ]

    rows: list[list[float]] = []
    labels: list[int] = []

    for ex in examples:
        blue_kda = (ex.blue.kills + ex.blue.assists) / max(ex.blue.deaths, 1.0)
        red_kda = (ex.red.kills + ex.red.assists) / max(ex.red.deaths, 1.0)

        rows.append(
            [
                _diff(ex.blue.kills, ex.red.kills),
                _diff(ex.blue.deaths, ex.red.deaths),
                _diff(ex.blue.assists, ex.red.assists),
                _diff(ex.blue.total_damage_to_champions, ex.red.total_damage_to_champions),
                _diff(ex.blue.gold_earned, ex.red.gold_earned),
                _diff(ex.blue.vision_score, ex.red.vision_score),
                _diff(ex.blue.total_minions_killed, ex.red.total_minions_killed),
                _diff(ex.blue.neutral_minions_killed, ex.red.neutral_minions_killed),
                _diff(blue_kda, red_kda),
            ]
        )
        labels.append(ex.label_blue_win)

    return FeatureMatrix(X=rows, y=labels, feature_names=feature_names)
