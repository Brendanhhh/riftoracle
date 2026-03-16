# Data Collection

The files in this directory are for collecting and storing Riot Match-V5 payloads. The checked-in `matches/` directory should be treated as sample/reference data, not a guaranteed training-sized dataset.

## Prerequisites

- Python 3.10+
- collector dependencies installed with `pip install -e .[dev,collector]`
- a valid Riot API key

## Required environment variables

- `RIOT_API_KEY`: required
- `RIOT_REGION`: optional, defaults to `na1`
- `RIOT_REGIONAL_ENDPOINT`: optional, defaults to `americas`

## Run locally

PowerShell:

```bash
$env:RIOT_API_KEY = "<your-key>"
python -m riftoracle.collect --matches-per-tier 100
```

POSIX shell:

```bash
export RIOT_API_KEY="<your-key>"
python -m riftoracle.collect --matches-per-tier 100
```

To write to a different root directory:

```bash
python -m riftoracle.collect --matches-per-tier 100 --output-root data-collection
```

## Output layout

By default the collector writes:

- `data-collection/matches/<tier>/<division>/*.json`: raw match payloads
- `data-collection/match_ids.csv`: flat index of collected match IDs
- `data-collection/state.json`: resume state for paging progress
- `data-collection/match_scraper.log`: collector log output

## Compatibility

`match-scraper-aws.py` remains available as a legacy wrapper, but the canonical interface is `python -m riftoracle.collect`.

## Common failure modes

- Missing `RIOT_API_KEY`: the collector exits immediately with a clear error.
- Too few stored matches: training may fail fast because the bundled sample data is not large or balanced enough.
- Rate limiting: Riot can return HTTP 429 responses; the collector sleeps and retries based on `Retry-After`.
- Dependency errors: install the collector extra if `requests` is missing.
