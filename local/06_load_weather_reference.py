#!/usr/bin/env python3
"""
WazeCargo local mirror — Phase 4b: production weather reference layer.

Two different weather systems exist in this project, and they are NOT the same:

  1. pipeline/07_weather_ingest.py (recovered from branch `master`)
     14 ports, thresholds in knots, exposure derived from port-mouth bearing.
     Live Open-Meteo backfill. This is the EARLIER prototype.

  2. The layer that actually produced the shipped dashboard numbers.
     43 ports, thresholds in km/h, a stored exposure_factor / swell_sensitivity.
     Its code was never committed to any branch, but its two artefacts were:
        dashboard-2.0/public/data/port_meta.json        -> port_risk_config
        dashboard-2.0/public/data/weather_seasonal.json -> monthly climatology
     built from 25 years of hourly data (n_years: 25).

This script loads (2) so the dashboard reproduces production figures. It writes
to distinct table names so the live pipeline in (1) can run alongside without
either overwriting the other.

Also carries forward the per-(port, direction, month) weather_multiplier from the
shipped port_forecast.json. That final ci_adjusted step is the one piece of the
weather chain with no surviving code on any branch; rather than invent a formula,
the published factors are stored verbatim and re-applied to freshly computed
ci_raw. Rows are tagged with their provenance.
"""
import json, os
import psycopg2
from psycopg2.extras import execute_values

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "dashboard-2.0", "public", "data")

CONN = dict(
    host=os.environ.get("RDS_HOST", "localhost"),
    port=int(os.environ.get("RDS_PORT", 5432)),
    user=os.environ.get("RDS_USER", "wazecargo"),
    password=os.environ.get("RDS_PASSWORD", "wazecargo_local"),
    dbname=os.environ.get("RDS_DBNAME", "waze_cargo"),
    sslmode=os.environ.get("RDS_SSLMODE", "disable"),
)

DDL = """
CREATE SCHEMA IF NOT EXISTS waze_cargo;

-- Production 43-port risk configuration (from port_meta.json).
DROP TABLE IF EXISTS waze_cargo.port_risk_config;
CREATE TABLE waze_cargo.port_risk_config (
    port_code            text PRIMARY KEY,
    port_name            text,
    zone                 text,
    swell_sensitivity    real,
    exposure_factor      real,
    hs_threshold_m       real,
    hs_closure_m         real,
    wind_threshold_kmh   real,
    wind_closure_kmh     real,
    gusts_threshold_kmh  real,
    gusts_closure_kmh    real,
    notes                text
);

-- Monthly climatology distilled from 25 years of hourly marine data.
DROP TABLE IF EXISTS waze_cargo.port_weather_seasonal;
CREATE TABLE waze_cargo.port_weather_seasonal (
    port_code              text,
    port_name              text,
    zone                   text,
    month                  smallint,
    n_years                smallint,
    rw_pct_hours_closed    real,
    rw_pct_hours_warning   real,
    rw_operability_index   real,
    rw_closure_days        real,
    med_pct_hours_closed   real,
    med_pct_hours_warning  real,
    med_operability_index  real,
    min_pct_hours_closed   real,
    max_pct_hours_closed   real,
    min_operability_index  real,
    max_operability_index  real,
    rw_avg_wave_height_m   real,
    max_wave_height_m      real,
    rw_avg_swell_height_m  real,
    max_swell_height_m     real,
    rw_avg_wind_speed_kmh  real,
    max_wind_gusts_kmh     real,
    tot_closed_by_swell    real,
    tot_closed_by_wind     real,
    tot_closed_by_wave     real,
    tot_closed_by_gust     real,
    share_closure_swell    real,
    share_closure_wind     real,
    PRIMARY KEY (port_code, month)
);

-- Weather adjustment factors carried forward from the published forecast.
DROP TABLE IF EXISTS waze_cargo.port_congestion_weather_adjusted;
CREATE TABLE waze_cargo.port_congestion_weather_adjusted (
    port                 text,
    direction            text,
    month                smallint,
    weather_multiplier   real,
    adjustment_type      text,
    pct_hours_closed     real,
    pct_hours_warning    real,
    at_or_above_hist_peak boolean,
    provenance           text,
    PRIMARY KEY (port, direction, month)
);
"""

SEASONAL_COLS = [
    "port_code","port_name","zone","month","n_years","rw_pct_hours_closed",
    "rw_pct_hours_warning","rw_operability_index","rw_closure_days",
    "med_pct_hours_closed","med_pct_hours_warning","med_operability_index",
    "min_pct_hours_closed","max_pct_hours_closed","min_operability_index",
    "max_operability_index","rw_avg_wave_height_m","max_wave_height_m",
    "rw_avg_swell_height_m","max_swell_height_m","rw_avg_wind_speed_kmh",
    "max_wind_gusts_kmh","tot_closed_by_swell","tot_closed_by_wind",
    "tot_closed_by_wave","tot_closed_by_gust","share_closure_swell",
    "share_closure_wind",
]
META_COLS = ["port_code","port_name","zone","swell_sensitivity","exposure_factor",
             "hs_threshold_m","hs_closure_m","wind_threshold_kmh","wind_closure_kmh",
             "gusts_threshold_kmh","gusts_closure_kmh","notes"]


def main():
    conn = psycopg2.connect(**CONN); conn.autocommit = True
    cur = conn.cursor()
    cur.execute(DDL)
    print("weather reference DDL applied")

    meta = json.load(open(os.path.join(DATA, "port_meta.json")))
    execute_values(cur,
        f"INSERT INTO waze_cargo.port_risk_config ({','.join(META_COLS)}) VALUES %s",
        [[r.get(c) for c in META_COLS] for r in meta])
    print(f"port_risk_config:             {len(meta):>5} ports")

    seas = json.load(open(os.path.join(DATA, "weather_seasonal.json")))
    execute_values(cur,
        f"INSERT INTO waze_cargo.port_weather_seasonal ({','.join(SEASONAL_COLS)}) VALUES %s",
        [[r.get(c) for c in SEASONAL_COLS] for r in seas])
    print(f"port_weather_seasonal:        {len(seas):>5} port-months")

    pf = json.load(open(os.path.join(DATA, "port_forecast.json")))
    seen, rows = set(), []
    for r in pf:
        k = (r["port"], r["direction"], r["month"])
        if k in seen:
            continue
        seen.add(k)
        rows.append([r["port"], r["direction"], r["month"], r["weather_multiplier"],
                     r["adjustment_type"], r["pct_hours_closed"], r["pct_hours_warning"],
                     r.get("at_or_above_hist_peak"), "carried_forward_from_aws_port_forecast"])
    execute_values(cur,
        "INSERT INTO waze_cargo.port_congestion_weather_adjusted "
        "(port,direction,month,weather_multiplier,adjustment_type,pct_hours_closed,"
        "pct_hours_warning,at_or_above_hist_peak,provenance) VALUES %s", rows)
    print(f"port_congestion_weather_adjusted: {len(rows):>3} port-direction-months")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
