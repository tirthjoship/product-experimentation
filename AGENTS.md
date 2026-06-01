# Coding Standards — Product Experimentation Analytics

## Python

- Python 3.12+
- Formatting: `black` (line-length 88)
- Type checking: `mypy` with strict mode enabled
- Linting: `ruff`
- Import sorting: `isort` (profile: black)
- No bare `except` — use specific exception types
- Type hints on all public function signatures
- Prefer `X | None` over `Optional[X]` (Python 3.12 syntax)

## Naming Conventions

- **Variables and functions**: `snake_case` (e.g., `compute_conversion`, `assign_variant`)
- **Classes**: `PascalCase` (e.g., `ExperimentAnalyzer`, `MetricCalculator`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `RANDOM_SEED`, `SIGNIFICANCE_LEVEL`)
- **Modules**: `snake_case` (e.g., `experiment.py`, `metrics.py`)
- **Test functions**: `test_<description>` (e.g., `test_conversion_rate_matches_sql`)
- **Private methods**: prefix with `_`

## Architecture Rules (NON-NEGOTIABLE)

- Clean `src/` layout — NOT full hexagonal (YAGNI for this project)
- `src/metrics/` — Python wrappers calling SQL in `sql/`
- `src/experiment/` — assignment, analysis, power calculations
- `src/report/` — markdown report generator
- `src/io/` — DuckDB loader, Parquet cache
- SQL lives in `sql/` — versioned, tested against fixtures
- No business logic duplication between Python and SQL

## Data Integrity Rules (NON-NEGOTIABLE)

- **Experiment integrity:** No peeking at post-assignment outcomes during assignment
- **Simulated experiment** must be labeled with `SIMULATED_EFFECT` constant
- Random seed pinned to `42` everywhere (assignment, bootstrap)
- Fixture-only testing — never load full Olist dataset in pytest
- All metrics must have SQL equivalents in `sql/metrics/`
- README and reports must state experiment is simulated on historical data

## Testing Rules (NON-NEGOTIABLE)

- Tests use small fixtures in `tests/fixtures/` (100 rows max)
- DuckDB in-memory from fixtures — never disk DB in tests
- pytest with `-v --tb=short` default
- Test categories: happy path, error path, boundary, edge case
- One logical assertion per test function
- Metric tests verify Python output matches SQL output on same fixture

## Project Layout

```
src/                    Application logic
├── metrics/            Conversion, AOV, D7 repeat wrappers
├── experiment/         Assignment, analysis, power
├── report/             Markdown report generator
└── io/                 DuckDB loader, Parquet cache

sql/                    Versioned SQL
├── metrics/            conversion.sql, aov.sql, d7_repeat.sql
└── experiment/         cohort.sql, variant_assignment.sql

tests/                  Mirrors src layout
├── fixtures/           Tiny CSV/Parquet samples
├── conftest.py         Shared fixtures (DuckDB in-memory)
└── test_metrics.py

app/                    Streamlit dashboard (Phase 2)
notebooks/              EDA only — no production logic
data/raw/               Olist CSVs (gitignored)
docs/                   Metrics definitions, experiment design
reports/                Generated experiment reports
```

## Git (NON-NEGOTIABLE)

- Commit format: `feat:` / `fix:` / `docs:` / `chore:` / `test:` followed by lowercase description, no period
- Keep commits small and focused
- Never commit directly to `main` or `dev` — use feature branches
- Branch naming: `feat/<slug>` or `fix/<slug>`
- PR target: `dev` (confirm with user before targeting `main`)
- Never commit secrets, raw data, or `.env` files
- Prefer new commits over `--amend` on pushed branches

## Commands

```bash
make test        # pytest -v --tb=short
make test-cov    # pytest with coverage
make lint        # pre-commit run --all-files
make typecheck   # mypy src/ --strict
make check       # lint + typecheck + test-cov
make setup       # install deps + pre-commit
```

## Strong Preferences

- Use structured logging over `print()` (loguru when added)
- Pin `random_seed=42` for all stochastic operations
- Every metric defined in SQL first, Python wraps SQL
- No invented metrics — every number from reproducible command
