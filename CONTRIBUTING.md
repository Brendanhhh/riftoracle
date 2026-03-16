# Contributing

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev,collector]
```

## Development workflow

Use the reusable package in `src/riftoracle/` for parsing, feature engineering, and modeling logic.
Keep one-off exploration in notebooks or scripts small, and move reusable logic into the package.

## Quality checks

```bash
python -m unittest discover -s tests
python -m compileall src scripts data-collection
```

Optional checks if dev dependencies are installed:

```bash
ruff check .
mypy src
pytest
```

## Data expectations

- Store raw Riot payloads under `data-collection/matches/<tier>/<division>/`.
- Avoid committing secrets; the collector reads credentials from environment variables.
- Prefer small fixture files in `tests/fixtures/` over adding more large sample payloads.
