# WazeCargo — Local Environment

Runs the full WazeCargo production stack on one machine, with no AWS account.
Replaces S3 + Glue + RDS + Secrets Manager with a local Postgres container and
the original DuckDB/CSV extracts as the raw source.

```
waze_cargo.duckdb + Chilean Customs CSVs (local disk)
        │
        │  local/02_load_structured.py          ← replaces S3 + Glue
        │  local/05_fix_import_years.py         ← repairs corrupt source years
        ▼
   structured.*        33.8M imports, 7.1M exports, 13 lookups
        │
        │  local/04_rebuild_clean_maritime_local.sh
        │     └─ extracts the SQL verbatim from
        │        modeling/03_rebuild_clean_maritime.sh
        ▼
   maritime.clean_maritime_imports (14.6M) / _exports (4.5M)
        │
        ├── modeling/04_ml_congestion.py  → ml.port_*
        └── modeling/05_ml_commodity.py   → ml.commodity_*
                    │
   waze_cargo.*  ───┤   weather layer (see "Weather" below)
                    ▼
        local/07_export_dashboard_json.py
                    ▼
   dashboard-2.0/public/data/*.json  →  npm start  →  localhost:3000
```

## Prerequisites

Docker, Python 3.11+, Node 18+, and `psql`. Roughly 15 GB free disk.

## Quick start

```bash
# 1. Postgres 17 (matches RDS 17.6)
docker run -d --name wazecargo-pg \
  -e POSTGRES_USER=wazecargo -e POSTGRES_PASSWORD=wazecargo_local \
  -e POSTGRES_DB=waze_cargo -p 5432:5432 \
  -v wazecargo_pgdata:/var/lib/postgresql/data --shm-size=1g \
  postgres:17 -c shared_buffers=1GB -c work_mem=64MB \
  -c maintenance_work_mem=512MB -c max_wal_size=4GB \
  -c checkpoint_timeout=30min -c synchronous_commit=off

source local/env.sh              # points the RDS_* vars at localhost

# 2. Python env
python3 -m venv .venv-local
.venv-local/bin/pip install -r local/requirements-local.txt

# 3. Schemas + raw layer
psql -f local/01_structured_ddl.sql
.venv-local/bin/python local/02_load_structured.py     # ~2 min
.venv-local/bin/python local/05_fix_import_years.py    # ~2 min

# 4. Clean layer  (~10 min)
psql -f local/03_maritime_ddl.sql
bash local/04_rebuild_clean_maritime_local.sh

# 5. ML
.venv-local/bin/python modeling/04_ml_congestion.py    # ~6 min
.venv-local/bin/python modeling/05_ml_commodity.py     # ~45 min

# 6. Weather
.venv-local/bin/python local/06_load_weather_reference.py
cd pipeline && ../.venv-local/bin/python 07_weather_ingest.py --backfill --start-year 2002
                ../.venv-local/bin/python 07_weather_ingest.py --aggregate

# 7. Dashboard
.venv-local/bin/python local/07_export_dashboard_json.py
cd dashboard-2.0 && npm install && npm start          # localhost:3000
```

Run the ML with `OMP_NUM_THREADS=2` on a machine with <8 GB RAM; the default
`n_jobs=-1` fan-out will exhaust memory during walk-forward CV.

## Changes made to existing code

Three one-line changes, all backward compatible — the AWS default is preserved:

| File | Change |
|------|--------|
| `modeling/04_ml_congestion.py` | `sslmode` now `os.environ["RDS_SSLMODE"]`, default `require` |
| `modeling/05_ml_commodity.py`  | same |
| `pipeline/07_weather_ingest.py`| same, plus `RDS_PORT` is honoured |

Nothing else in `modeling/` or `pipeline/` was modified. The clean-table
rebuild does not copy its SQL — `local/04_rebuild_clean_maritime_local.sh`
extracts the heredoc from `modeling/03_rebuild_clean_maritime.sh` at runtime,
so the local clean layer cannot silently drift from the AWS pipeline.

## Source data defects found and repaired

`waze_cargo.duckdb` disagrees with the source Chilean Customs (Aduanas) CSVs on three import years.
Years 2002–2023 match exactly; exports match exactly for all years.

| Year | DuckDB | CSV | Cause |
|------|--------|-----|-------|
| 2024 | 0 (+1,821,211 rows with NULL periodo) | 1,821,211 | `ingresos2024.csv` writes `PERIODO` as `2024,00` (decimal comma). The DuckDB build failed that cast, leaving the rows with NULL periodo/mes — invisible to the rebuild, which loops over `DISTINCT year`. |
| 2025 | 3,855,318 | 1,927,659 | loaded twice (exactly 2×) |
| 2026 | 305,576 | 152,788 | loaded twice (exactly 2×) |

`local/05_fix_import_years.py` reloads those three years from the CSVs. The
files do not share an encoding (2024 is latin-1, 2026 is UTF-8) and spell
column 16 three different ways (`CANTIDAD_MERCANCIA` / `CANTIDAD_MERCANCÍA`),
so it reads them positionally with per-file encoding fallback.

**Impact:** before the repair, 2025 carried double volume and 2024 was absent,
which inflated the 2026 import forecast to 1,868,789. After the repair it is
854,753 — against the 856,350 recorded in `modeling/INDEX.md`, a 0.19% gap.

## Fidelity vs AWS production

| Metric | AWS | Local | Δ |
|---|---|---|---|
| `structured.all_imports` | ~33.8M | 33,833,770 | match |
| `maritime.clean_maritime_imports` | ~14.6M | 14,568,849 | match |
| `maritime.clean_maritime_exports` | ~4.5M | 4,455,078 | match |
| clean imports table size | 4.9 GB | 4,896 MB | match |
| 2026 import forecast | 856,350 | 854,753 | −0.19% |
| 2026 export forecast | 186,207 | 185,849 | −0.19% |

`port_forecast.json` reproduces all 666 AWS rows. On rows where the hybrid
selected the deterministic Baseline (the high-volume ports), **92.3% are
bit-identical, mean |Δci_raw| = 0.0001**. Divergence elsewhere tracks CV
picking a different model, which is expected under different library versions
(scikit-learn 1.9, LightGBM 4.7, XGBoost 3.4).

## Weather

Two different weather systems exist in this project. They are not the same.

**1. `pipeline/07_weather_ingest.py`** — recovered from branch `master`, which
was never merged. 14 ports, thresholds in knots, exposure derived from
port-mouth bearing and protected arc. Fetches live from Open-Meteo (free, no
key) back to 2002 and writes `port_weather_hourly`, `port_operability_score`,
`port_weather_monthly`. This works and is the way to refresh weather going
forward.

**2. The layer that produced the shipped dashboard numbers** — 43 ports,
thresholds in km/h, stored `exposure_factor` / `swell_sensitivity`. Its code
was never committed anywhere, but two artefacts were, and they carry the
expensive part (25 years of hourly data distilled to a monthly climatology):

- `port_meta.json` → `waze_cargo.port_risk_config` (43 ports)
- `weather_seasonal.json` → `waze_cargo.port_weather_seasonal` (516 port-months)

`local/06_load_weather_reference.py` loads these under distinct table names so
both systems coexist without overwriting each other.

### The one genuinely missing piece

No branch contains the code that produced `weather_multiplier` / `ci_adjusted`
(`waze_cargo.port_congestion_weather_adjusted`). `App.jsx` consumes it and the
ER docs describe the table, but nothing produces it. The obvious candidate
formula — month operability ÷ annual mean operability — fits only 1.6% of
published rows, and the multiplier varies slightly by direction, so it is not
pure weather climatology.

Rather than invent a formula, the published per-(port, direction, month)
factors are carried forward verbatim from the AWS `port_forecast.json` and
re-applied to freshly computed `ci_raw`. Every such row is tagged
`provenance = 'carried_forward_from_aws_port_forecast'`. Rows with no factor
get multiplier 1.0 and `adjustment_type = 'NO_WEATHER_DATA'`, matching the
shipped file's own convention.

If you need this to be live rather than carried forward, that step has to be
rewritten from the methodology in `docs/Congestion_Index_Methodology.docx`,
and the result will not reproduce current dashboard numbers exactly.

## Recovered formulas

Both validated against the shipped JSON, not assumed:

```
ci_raw      = clip((forecast_shipments − min_hist) / (max_hist − min_hist), 0, 1)
              per (port, direction) over all of ml.port_monthly_agg
              → reproduces port_forecast.json on 666/666 rows, mean |err| 0.0002

ci_adjusted = ci_raw × weather_multiplier
              → exact in both port_forecast.json and delay_risk_history.json
```

The historical Congestion Index (Stage 1, the weighted composite in
`docs/Congestion_Index_Methodology.docx`) is a different metric and is not what
the dashboard plots; the dashboard uses the re-normalised forecast above.

## Reference data

`local/aws_reference_data/` holds the six JSON files exactly as they came from
AWS. They are the regression baseline — `07_export_dashboard_json.py` overwrites
`dashboard-2.0/public/data/`, so diff against this directory to check drift.

## Notes

- `structured.*` and `maritime.*` are `UNLOGGED`: they are rebuildable, and
  this avoids WAL overhead on a laptop. They do not survive a Postgres crash;
  re-run steps 3–4 if that happens.
- Postgres data lives in the Docker volume `wazecargo_pgdata` (~14 GB).
  `docker volume rm wazecargo_pgdata` resets everything.
- `local/env.sh` sets `RDS_SSLMODE=disable`; the container serves no TLS.
