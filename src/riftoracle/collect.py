from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


TIERS = ["IRON", "BRONZE", "SILVER", "GOLD", "PLATINUM", "EMERALD", "DIAMOND"]
DIVISIONS = ["I", "II", "III", "IV"]
REQUEST_LIMIT = 100
WINDOW_SECONDS = 120


@dataclass(frozen=True)
class CollectorSettings:
    api_key: str
    region: str = "na1"
    regional_endpoint: str = "americas"


@dataclass(frozen=True)
class CollectorPaths:
    output_root: Path
    state_file: Path
    csv_file: Path
    matches_dir: Path
    log_file: Path


def build_paths(output_root: str | Path) -> CollectorPaths:
    base = Path(output_root)
    return CollectorPaths(
        output_root=base,
        state_file=base / "state.json",
        csv_file=base / "match_ids.csv",
        matches_dir=base / "matches",
        log_file=base / "match_scraper.log",
    )


def load_settings_from_env() -> CollectorSettings:
    api_key = os.getenv("RIOT_API_KEY")
    if not api_key:
        raise SystemExit("RIOT_API_KEY is required to collect match data.")

    return CollectorSettings(
        api_key=api_key,
        region=os.getenv("RIOT_REGION", "na1"),
        regional_endpoint=os.getenv("RIOT_REGIONAL_ENDPOINT", "americas"),
    )


class RiotCollector:
    def __init__(self, settings: CollectorSettings, paths: CollectorPaths) -> None:
        self.settings = settings
        self.paths = paths
        self.request_timestamps: list[datetime] = []
        self.puuid_cache: dict[str, str | None] = {}
        self.logger = self._build_logger()

    def _build_logger(self) -> logging.Logger:
        self.paths.output_root.mkdir(parents=True, exist_ok=True)

        logger_name = f"riftoracle.collect.{self.paths.output_root.resolve()}"
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        logger.propagate = False

        if not logger.handlers:
            handler = logging.FileHandler(self.paths.log_file, encoding="utf-8")
            handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
            logger.addHandler(handler)

        return logger

    def load_state(self) -> dict[str, Any]:
        if self.paths.state_file.exists():
            return json.loads(self.paths.state_file.read_text(encoding="utf-8"))
        return {}

    def save_state(self, state: dict[str, Any]) -> None:
        self.paths.output_root.mkdir(parents=True, exist_ok=True)
        self.paths.state_file.write_text(json.dumps(state, indent=4), encoding="utf-8")

    def rate_limit_sleep(self) -> None:
        now = datetime.now()
        self.request_timestamps = [
            timestamp
            for timestamp in self.request_timestamps
            if timestamp > now - timedelta(seconds=WINDOW_SECONDS)
        ]
        if len(self.request_timestamps) >= REQUEST_LIMIT:
            oldest = self.request_timestamps[0]
            sleep_time = (oldest + timedelta(seconds=WINDOW_SECONDS)) - now
            self.logger.info("Rate limit reached. Sleeping %.1fs", sleep_time.total_seconds())
            time.sleep(max(sleep_time.total_seconds(), 0))
        self.request_timestamps.append(now)

    def make_api_call(self, url: str) -> Any:
        try:
            import requests
        except ImportError as exc:
            raise ImportError(
                "requests is required for data collection. Install with `pip install -e .[collector]`."
            ) from exc

        while True:
            self.rate_limit_sleep()
            try:
                response = requests.get(url, headers={"X-Riot-Token": self.settings.api_key}, timeout=30)
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 10))
                    self.logger.warning("429 received. Sleeping %ss", retry_after)
                    time.sleep(retry_after)
                    continue
                response.raise_for_status()
                return response.json()
            except Exception as exc:  # pragma: no cover - network path
                self.logger.error("API error: %s", exc)
                return None

    def get_players(self, tier: str, division: str, page: int = 1) -> Any:
        url = (
            f"https://{self.settings.region}.api.riotgames.com/lol/league/v4/entries/"
            f"RANKED_SOLO_5x5/{tier}/{division}?page={page}"
        )
        return self.make_api_call(url)

    def get_puuid(self, summoner_id: str) -> str | None:
        if summoner_id in self.puuid_cache:
            return self.puuid_cache[summoner_id]

        url = (
            f"https://{self.settings.region}.api.riotgames.com/lol/summoner/v4/"
            f"summoners/{summoner_id}"
        )
        data = self.make_api_call(url)
        puuid = data.get("puuid") if data else None
        self.puuid_cache[summoner_id] = puuid
        return puuid

    def get_matches(self, puuid: str, count: int = 10) -> list[str]:
        url = (
            f"https://{self.settings.regional_endpoint}.api.riotgames.com/lol/match/v5/"
            f"matches/by-puuid/{puuid}/ids?queue=420&count={count}"
        )
        return self.make_api_call(url) or []

    def save_match_id_csv(self, match_id: str, tier: str, division: str) -> None:
        self.paths.output_root.mkdir(parents=True, exist_ok=True)
        file_exists = self.paths.csv_file.exists()
        with self.paths.csv_file.open("a", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            if not file_exists:
                writer.writerow(["match_id", "tier", "division"])
            writer.writerow([match_id, tier, division])

    def save_match(self, match_id: str, tier: str, division: str) -> bool:
        folder_path = self.paths.matches_dir / tier.lower() / division
        folder_path.mkdir(parents=True, exist_ok=True)
        file_path = folder_path / f"{match_id}.json"

        if file_path.exists():
            return False

        url = (
            f"https://{self.settings.regional_endpoint}.api.riotgames.com/lol/match/v5/"
            f"matches/{match_id}"
        )
        data = self.make_api_call(url)
        if data:
            file_path.write_text(json.dumps(data), encoding="utf-8")
            self.save_match_id_csv(match_id, tier, division)
            self.logger.info("Saved match %s for %s %s", match_id, tier, division)
            return True
        return False

    def collect_data(self, matches_per_tier: int = 5) -> None:
        state = self.load_state()

        for tier in TIERS:
            divisions_to_process = list(reversed(DIVISIONS)) if tier == "DIAMOND" else DIVISIONS
            for division in divisions_to_process:
                self.logger.info("Processing %s %s", tier, division)
                collected = 0
                page = state.get(tier, {}).get(division, 1)
                done = False

                while collected < matches_per_tier and not done:
                    players = self.get_players(tier, division, page)
                    if not players:
                        break

                    for player in players:
                        if collected >= matches_per_tier:
                            done = True
                            break
                        puuid = self.get_puuid(player["summonerId"])
                        if not puuid:
                            continue
                        matches = self.get_matches(puuid, count=10)
                        for match_id in matches[:5]:
                            if collected >= matches_per_tier:
                                done = True
                                break
                            if self.save_match(match_id, tier, division):
                                collected += 1
                                self.logger.info(
                                    "Collected %s/%s for %s %s",
                                    collected,
                                    matches_per_tier,
                                    tier,
                                    division,
                                )
                    state.setdefault(tier, {})[division] = page
                    self.save_state(state)
                    page += 1
                    time.sleep(0.5)

                if tier == "DIAMOND" and division == "I":
                    self.logger.info("Finished processing Diamond I. Stopping further processing.")
                    return


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect Riot ranked match payloads for local or server-side use."
    )
    parser.add_argument("--matches-per-tier", type=int, default=100)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("data-collection"),
        help="Directory that will contain matches/, state.json, match_ids.csv, and logs.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    collector = RiotCollector(
        settings=load_settings_from_env(),
        paths=build_paths(args.output_root),
    )
    collector.collect_data(matches_per_tier=args.matches_per_tier)


if __name__ == "__main__":
    main()
