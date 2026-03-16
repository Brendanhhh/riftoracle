# RiftOracle

RiftOracle is a League of Legends data-and-modeling repository for estimating match win probability from Riot Match-V5 payloads. The project now has a reusable Python package, baseline training entrypoints, raw collected match data, and a contributor workflow that is easier to extend safely.

## What this repo is for

- Collect ranked solo queue match payloads from the Riot API.
- Normalize raw JSON into supervised blue-vs-red training examples.
- Build baseline feature sets for win prediction experiments.
- Provide a clean starting point for stronger predictive models.

## Repository layout

- `src/riftoracle/`: reusable package code for loading data, generating features, and fitting baseline models.
- `scripts/train_baselines.py`: example CLI for training baseline classifiers against stored match payloads.
- `data-collection/`: collector scripts, schema exploration assets, and raw match JSON files.
- `tests/`: lightweight regression tests for the package surface area.
- `flattened_matches.csv`: legacy flat export retained for reference.

## Quickstart

### Create an environment

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Install the package

```bash
pip install -e .[dev]
```

Install collector dependencies too if you plan to hit the Riot API:

```bash
pip install -e .[dev,collector]
```

### Train baseline models

```bash
python scripts/train_baselines.py --matches-dir data-collection/matches --sample-size 500
```

The checked-in `data-collection/matches/` tree is bundled sample data for exploration and tests, not guaranteed training-ready data. The baseline training CLI may stop early if there are too few valid examples or not enough class balance to create a safe split.

## Current modeling baseline

`riftoracle.data` converts Match-V5 JSON into `MatchExample` records with blue-team and red-team aggregates. `riftoracle.features` then builds a small differential feature set, including:

- kills, deaths, and assists differentials
- gold and damage differentials
- vision and lane economy differentials
- simple KDA ratio differential

`riftoracle.models` currently exposes two baseline estimators:

- logistic regression for an interpretable linear baseline
- random forest for a quick nonlinear baseline

These are intentionally conservative scaffolds rather than final production models.

## Data notes

The stored sample payloads under `data-collection/matches/` follow the expected Riot Match-V5 shape:

- `metadata.matchId` identifies the match
- `info.participants` contains 10 player records
- `info.teams` contains team-level outcome metadata

This bundled data should be treated as reference/sample data. If you want repeatable training runs, plan to collect a larger local dataset first.

The current training code uses post-game aggregates, so the repo is best described as a modeling sandbox for outcome prediction baselines, not yet a live in-game win probability system.

## Collect More Data Locally

The supported collector entrypoint is `python -m riftoracle.collect`. It works on a normal local machine or on a server and writes data to `data-collection/` by default.

Set the following environment variables before collecting:

- `RIOT_API_KEY`
- `RIOT_REGION` (optional, defaults to `na1`)
- `RIOT_REGIONAL_ENDPOINT` (optional, defaults to `americas`)

Windows PowerShell:

```bash
$env:RIOT_API_KEY = "<your-key>"
python -m riftoracle.collect --matches-per-tier 100
```

Cross-platform shell:

```bash
export RIOT_API_KEY="<your-key>"
python -m riftoracle.collect --matches-per-tier 100
```

Optional custom output root:

```bash
python -m riftoracle.collect --matches-per-tier 100 --output-root data-collection
```

The legacy script `python data-collection/match-scraper-aws.py --matches-per-tier 100` still works as a compatibility wrapper.

## Development

Core local checks:

```bash
python -m unittest discover -s tests
python -m compileall src scripts data-collection
```

Optional checks with dev tooling installed:

```bash
ruff check .
mypy src
pytest
```

Exploratory notebooks in the repository are reference artifacts and are not part of the enforced Ruff lint surface.

See `CONTRIBUTING.md` for the contributor workflow.

## Roadmap

1. Separate post-game benchmarking features from live-available features.
2. Add calibration and better evaluation reporting.
3. Introduce experiment tracking and model artifact versioning.
4. Expand fixtures and tests around collector output assumptions.

## License

This repository is available under the terms in [LICENSE](LICENSE).
