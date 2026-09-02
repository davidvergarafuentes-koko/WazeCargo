#!/usr/bin/env python3
"""
WazeCargo local mirror — Phase 5: Postgres -> dashboard JSON.

dashboard-2.0 is a static React app: it fetches six files from public/data/.
On AWS those were produced by an export step that was never committed. This
rebuilds all six from the local ml.* and waze_cargo.* tables.

Recovered formulas (validated against the shipped files, see README_LOCAL.md):
  ci_raw      = clip((forecast_shipments - min_hist) / (max_hist - min_hist), 0, 1)
                per (port, direction) over the full port_monthly_agg history.
                Reproduces the shipped port_forecast.json on 666/666 rows,
                mean absolute error 0.0002.
  ci_adjusted = ci_raw * weather_multiplier   (exact in both shipped files)

The multiplier itself is carried forward from the published AWS forecast (see
local/06_load_weather_reference.py) because no branch contains the code that
derived it. Ports with no carried-forward factor get multiplier 1.0 and are
tagged NO_WEATHER_DATA, matching the shipped file's own convention.

Usage: python3 local/07_export_dashboard_json.py [--out DIR]
"""
import argparse, json, os
import psycopg2
from psycopg2.extras import RealDictCursor

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT = os.path.join(REPO, "dashboard-2.0", "public", "data")

CONN = dict(
    host=os.environ.get("RDS_HOST", "localhost"),
    port=int(os.environ.get("RDS_PORT", 5432)),
    user=os.environ.get("RDS_USER", "wazecargo"),
    password=os.environ.get("RDS_PASSWORD", "wazecargo_local"),
    dbname=os.environ.get("RDS_DBNAME", "waze_cargo"),
    sslmode=os.environ.get("RDS_SSLMODE", "disable"),
)

# ── shared CTE: historical shipment range per port+direction ──────────────
RANGE_CTE = """
WITH rng AS (
    SELECT port, direction,
           MIN(shipment_count)::double precision AS lo,
           MAX(shipment_count)::double precision AS hi
    FROM ml.port_monthly_agg
    GROUP BY port, direction
)
"""

Q_PORT_FORECAST = RANGE_CTE + """
SELECT f.port, f.direction, f.month::int AS month,
       f.forecast_shipments::int          AS forecast_shipments,
       round(f.pred_shipment_count::numeric, 1)::float8 AS pred_shipment_count,
       f.model,
       round(LEAST(1, GREATEST(0,
           (f.forecast_shipments - r.lo) / NULLIF(r.hi - r.lo, 0)))::numeric, 4)::float8 AS ci_raw,
       round((LEAST(1, GREATEST(0,
           (f.forecast_shipments - r.lo) / NULLIF(r.hi - r.lo, 0)))
           * COALESCE(w.weather_multiplier, 1.0))::numeric, 4)::float8 AS ci_adjusted,
       COALESCE(w.weather_multiplier, 1.0)::float8 AS weather_multiplier,
       COALESCE(w.adjustment_type, 'NO_WEATHER_DATA') AS adjustment_type,
       COALESCE(w.pct_hours_closed, 0)::float8  AS pct_hours_closed,
       COALESCE(w.pct_hours_warning, 0)::float8 AS pct_hours_warning,
       COALESCE(w.at_or_above_hist_peak, false) AS at_or_above_hist_peak
FROM ml.port_forecast_2026 f
JOIN rng r  ON r.port = f.port AND r.direction = f.direction
LEFT JOIN waze_cargo.port_congestion_weather_adjusted w
       ON w.port = f.port AND w.direction = f.direction AND w.month = f.month
ORDER BY f.port, f.direction, f.month
"""

Q_HISTORY = RANGE_CTE + """
SELECT a.year::int, a.month::int, a.port, a.port AS port_code, a.direction,
       a.shipment_count::int,
       round(LEAST(1, GREATEST(0,
           (a.shipment_count - r.lo) / NULLIF(r.hi - r.lo, 0)))::numeric, 4)::float8 AS ci_raw,
       round((LEAST(1, GREATEST(0,
           (a.shipment_count - r.lo) / NULLIF(r.hi - r.lo, 0)))
           * COALESCE(w.weather_multiplier, 1.0))::numeric, 4)::float8 AS ci_adjusted,
       COALESCE(w.weather_multiplier, 1.0)::float8 AS weather_multiplier,
       COALESCE(w.adjustment_type, 'NO_ADJUSTMENT') AS adjustment_type,
       COALESCE(w.pct_hours_closed, 0)::float8  AS pct_hours_closed,
       COALESCE(w.pct_hours_warning, 0)::float8 AS pct_hours_warning
FROM ml.port_monthly_agg a
JOIN rng r ON r.port = a.port AND r.direction = a.direction
LEFT JOIN waze_cargo.port_congestion_weather_adjusted w
       ON w.port = a.port AND w.direction = a.direction AND w.month = a.month
WHERE a.year BETWEEN 2006 AND 2025
ORDER BY a.year, a.month, a.port, a.direction
"""

Q_META = """
SELECT port_code, port_name, zone, swell_sensitivity, exposure_factor,
       hs_threshold_m, hs_closure_m, wind_threshold_kmh, wind_closure_kmh,
       gusts_threshold_kmh, gusts_closure_kmh, notes
FROM waze_cargo.port_risk_config ORDER BY port_code
"""

Q_SEASONAL = "SELECT * FROM waze_cargo.port_weather_seasonal ORDER BY port_code, month"

# share_of_month and rank_in_month are not stored on the table — the AWS export
# derived them, so recompute: each commodity's share of that port-direction-month
# total, and its rank within the month by forecast volume.
Q_COMMODITY = """
SELECT port, direction, month, hs2, commodity_description,
       forecast_shipments, pred_shipment_count, model,
       share_of_month, rank_in_month
FROM (
    SELECT port, direction, month::int AS month, hs2, commodity_description,
           forecast_shipments::int AS forecast_shipments,
           round(pred_shipment_count::numeric, 2)::float8 AS pred_shipment_count,
           model,
           round((forecast_shipments::numeric
                  / NULLIF(SUM(forecast_shipments) OVER (PARTITION BY port, direction, month), 0)
                 ), 4)::float8 AS share_of_month,
           RANK() OVER (PARTITION BY port, direction, month
                        ORDER BY forecast_shipments DESC)::int AS rank_in_month
    FROM ml.commodity_forecast_2026
) t
ORDER BY port, direction, month, rank_in_month
"""

# port_compare: per (hs2, port, direction), aggregate the 12 monthly commodity
# forecasts and attach that port's mean congestion, then rank ports within each
# commodity by a volume x availability score.
Q_COMPARE = """
WITH cf AS (
    SELECT hs2, MIN(commodity_description) AS commodity_description,
           port, direction, SUM(forecast_shipments) AS total_forecast_shipments
    FROM ml.commodity_forecast_2026
    GROUP BY hs2, port, direction
),
ci AS (
    SELECT port, direction,
           AVG(ci_raw) AS avg_ci_raw,
           AVG(weather_multiplier) AS avg_weather_mult,
           AVG(ci_adjusted) AS avg_ci_adjusted,
           AVG(pct_hours_closed) AS avg_pct_hours_closed
    FROM ( {pf} ) t
    GROUP BY port, direction
)
SELECT cf.hs2, cf.commodity_description, cf.port, cf.direction,
       cf.total_forecast_shipments::int,
       round(ci.avg_ci_raw::numeric,4)::float8          AS avg_ci_raw,
       round(ci.avg_weather_mult::numeric,4)::float8    AS avg_weather_mult,
       round(ci.avg_ci_adjusted::numeric,4)::float8     AS avg_ci_adjusted,
       round(ci.avg_pct_hours_closed::numeric,4)::float8 AS avg_pct_hours_closed,
       round((cf.total_forecast_shipments * (1 - ci.avg_ci_adjusted))::numeric,1)::float8 AS score,
       RANK() OVER (PARTITION BY cf.hs2, cf.direction
                    ORDER BY cf.total_forecast_shipments * (1 - ci.avg_ci_adjusted) DESC)::int
              AS rank_in_commodity
FROM cf JOIN ci ON ci.port = cf.port AND ci.direction = cf.direction
ORDER BY cf.hs2, cf.direction, rank_in_commodity
""".replace("{pf}", Q_PORT_FORECAST)


def table_exists(cur, schema, name):
    cur.execute("""SELECT 1 FROM information_schema.tables
                   WHERE table_schema=%s AND table_name=%s""", (schema, name))
    return cur.fetchone() is not None


def dump(cur, sql, path, label):
    cur.execute(sql)
    rows = [dict(r) for r in cur.fetchall()]
    with open(path, "w") as fh:
        json.dump(rows, fh, ensure_ascii=False, separators=(",", ":"), default=str)
    size = os.path.getsize(path) / 1024
    print(f"  {label:<26} {len(rows):>7,} rows  {size:>8.1f} KB  -> {os.path.basename(path)}")
    return len(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    conn = psycopg2.connect(**CONN)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    print(f"Exporting dashboard JSON -> {args.out}")

    dump(cur, Q_PORT_FORECAST, os.path.join(args.out, "port_forecast.json"), "port_forecast")
    dump(cur, Q_HISTORY,       os.path.join(args.out, "delay_risk_history.json"), "delay_risk_history")
    dump(cur, Q_META,          os.path.join(args.out, "port_meta.json"), "port_meta")
    dump(cur, Q_SEASONAL,      os.path.join(args.out, "weather_seasonal.json"), "weather_seasonal")

    if table_exists(cur, "ml", "commodity_forecast_2026"):
        dump(cur, Q_COMMODITY, os.path.join(args.out, "commodity_forecast.json"), "commodity_forecast")
        dump(cur, Q_COMPARE,   os.path.join(args.out, "port_compare.json"), "port_compare")
    else:
        print("  ml.commodity_forecast_2026 not present — skipped "
              "commodity_forecast.json / port_compare.json "
              "(run modeling/05_ml_commodity.py first)")

    cur.close(); conn.close()
    print("Export complete.")


if __name__ == "__main__":
    main()
