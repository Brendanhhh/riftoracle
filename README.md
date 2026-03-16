# RiftOracle

RiftOracle is a League of Legends match-data project focused on building **win chance prediction models** from Riot Match-V5 JSON payloads.

This repository now includes:

- raw match collection scripts and stored match JSON files,
- a documented project layout,
- a lightweight Python package with feature extraction helpers,
- baseline model skeletons for win-probability prediction.

## Repository layout

- `data-collection/` - data acquisition assets and raw match JSON files
  - `match-scraper-aws.py` - Riot API collector script
  - `match-data-structure.json` - flattened JSON key scaffold
  - `matches/<tier>/<division>/*.json` - collected match payloads
- `src/riftoracle/` - reusable package code
  - `data.py` - read/parse Match-V5 files into examples
  - `features.py` - basic team-differential feature engineering
  - `models.py` - model interfaces + baseline model skeletons
- `scripts/train_baselines.py` - example training entrypoint
- `flattened_matches.csv` - large flat export (legacy)

## Quickstart

### 1) Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Train baseline skeleton models

```bash
python scripts/train_baselines.py --matches-dir data-collection/matches --sample-size 500
```

## Data notes (JSON skim)

Based on a skim of representative files under `data-collection/matches/`:

- each match has top-level `metadata` and `info` objects,
- `info.participants` has 10 participant records (5 per team),
- `info.teams` contains team outcomes (`teamId`, `win`) and objectives,
- participant records expose rich combat/objective/vision stats suitable for pre-game, in-game, or post-game modeling depending on feature policy.

The current feature skeleton intentionally uses a **small stable subset** of participant aggregates per team:

- kills, deaths, assists,
- total damage dealt to champions,
- gold earned,
- vision score,
- total minions killed,
- neutral minions killed.

## Modeling approach

`riftoracle.models` provides:

- `WinChanceModel` protocol (common API)
- `LogisticRegressionWinModel` baseline (linear probability estimator)
- `RandomForestWinModel` baseline (nonlinear tree ensemble)

These are intentionally minimal and designed as scaffolding for:

- richer feature transforms (champion embeddings, role-aware features, draft context),
- temporal snapshots for live win chance,
- calibrated probabilities and confidence intervals.

## Collector script setup

Set required environment variables before running the collector:

- `RIOT_API_KEY`
- optional: `RIOT_REGION` (default `na1`)
- optional: `RIOT_REGIONAL_ENDPOINT` (default `americas`)

Example:

```bash
export RIOT_API_KEY="<your-key>"
python data-collection/match-scraper-aws.py --matches-per-tier 100
```

## Next recommended improvements

1. Add unit tests for `data.py` and `features.py` using a tiny fixture set.
2. Add train/validation/test split utilities with leakage checks.
3. Add probability calibration (Platt / isotonic).
4. Add model artifact versioning + metrics tracking.
5. Add CI for linting, tests, and type checks.

## License

MIT-style usage under the repository `LICENSE`.
