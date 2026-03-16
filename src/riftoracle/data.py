from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TeamAggregate:
    """Aggregated team-level post-game stats derived from participant rows."""

    team_id: int
    win: int
    kills: float
    deaths: float
    assists: float
    total_damage_to_champions: float
    gold_earned: float
    vision_score: float
    total_minions_killed: float
    neutral_minions_killed: float


@dataclass(frozen=True)
class MatchExample:
    """Single supervised example for binary win prediction.

    Convention: `blue` corresponds to teamId 100 and `red` to teamId 200.
    Label is 1 when blue wins, 0 when red wins.
    """

    match_id: str
    blue: TeamAggregate
    red: TeamAggregate
    label_blue_win: int


def _team_from_participants(
    participants: list[dict[str, Any]], team_id: int, team_win_flag: bool
) -> TeamAggregate:
    team_rows = [p for p in participants if int(p.get("teamId", -1)) == team_id]
    if not team_rows:
        raise ValueError(f"No participants found for team_id={team_id}")

    def _sum(field: str) -> float:
        return float(sum(float(r.get(field, 0.0) or 0.0) for r in team_rows))

    return TeamAggregate(
        team_id=team_id,
        win=1 if team_win_flag else 0,
        kills=_sum("kills"),
        deaths=_sum("deaths"),
        assists=_sum("assists"),
        total_damage_to_champions=_sum("totalDamageDealtToChampions"),
        gold_earned=_sum("goldEarned"),
        vision_score=_sum("visionScore"),
        total_minions_killed=_sum("totalMinionsKilled"),
        neutral_minions_killed=_sum("neutralMinionsKilled"),
    )


def parse_match_payload(payload: dict[str, Any]) -> MatchExample:
    """Convert a Riot Match-V5 payload into a supervised blue-vs-red example."""
    metadata = payload.get("metadata", {})
    info = payload.get("info", {})
    participants = info.get("participants", [])
    teams = info.get("teams", [])

    if len(participants) != 10:
        raise ValueError("Expected exactly 10 participants in ranked match payload")

    team_outcome = {int(t.get("teamId")): bool(t.get("win")) for t in teams}

    blue = _team_from_participants(
        participants,
        team_id=100,
        team_win_flag=team_outcome.get(100, False),
    )
    red = _team_from_participants(
        participants,
        team_id=200,
        team_win_flag=team_outcome.get(200, False),
    )

    return MatchExample(
        match_id=str(metadata.get("matchId", "unknown")),
        blue=blue,
        red=red,
        label_blue_win=blue.win,
    )


def iter_match_files(matches_dir: Path) -> Iterable[Path]:
    yield from sorted(matches_dir.rglob("*.json"))


def load_match_examples(
    matches_dir: str | Path,
    sample_size: int | None = None,
) -> list[MatchExample]:
    base = Path(matches_dir)
    if not base.exists():
        raise FileNotFoundError(f"Matches directory does not exist: {base}")

    files = list(iter_match_files(base))
    if sample_size is not None:
        files = files[:sample_size]

    examples: list[MatchExample] = []
    for path in files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            examples.append(parse_match_payload(payload))
        except Exception:
            continue
    return examples
