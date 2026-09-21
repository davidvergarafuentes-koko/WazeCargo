#!/usr/bin/env python3
"""
WazeCargo local mirror — Phase 1: DuckDB -> Postgres structured.*

Replaces the AWS S3 -> Glue -> RDS path. Streams the raw customs tables and
the 13 lookup tables out of the original waze_cargo.duckdb straight into the
local Postgres via DuckDB's postgres extension (no Python-side buffering).

Raw columns are cast to text and renamed to the quoted UPPERCASE contract that
modeling/03_rebuild_clean_maritime.sh expects, plus the `year` partition column.

Usage: python3 local/02_load_structured.py [--only imports|exports|lookups]
"""
import argparse, os, sys, time

import duckdb

DUCKDB_PATH = os.environ.get(
    "WZ_DUCKDB",
    "/mnt/windows/Users/koko/Desktop/Master IA & Data Solutions/Final Projet/Waze cargo/waze_cargo.duckdb",
)
PG = os.environ.get(
    "WZ_PG_DSN",
    "host=localhost port=5432 dbname=waze_cargo user=wazecargo password=wazecargo_local",
)

LOOKUPS = [
    "lkp_aduanas", "lkp_clausulas", "lkp_harmonized_system",
    "lkp_modalidades_venta", "lkp_moneda", "lkp_paises", "lkp_puertos",
    "lkp_regimen_importacion", "lkp_regiones", "lkp_tipos_carga",
    "lkp_tipos_operacion", "lkp_unidades_medida", "lkp_vias_transporte",
]

# source column -> target quoted column, for the raw fact tables.
IMPORT_MAP = [
    ("periodo",                 '"PERIODO"',                 "integer"),
    ("mes",                     '"MES"',                     "integer"),
    ("cod_aduana_tramitacion",  '"COD_ADUANA_TRAMITACION"',  "text"),
    ("cod_tipo_operacion",      '"COD_TIPO_OPERACION"',      "text"),
    ("cod_pais_origen",         '"COD_PAIS_ORIGEN"',         "text"),
    ("cod_pais_adquisicion",    '"COD_PAIS_ADQUISICION"',    "text"),
    ("cod_regimen_importacion", '"COD_REGIMEN_IMPORTACION"', "text"),
    ("cod_puerto_embarque",     '"COD_PUERTO_EMBARQUE"',     "text"),
    ("cod_puerto_desembarque",  '"COD_PUERTO_DESEMBARQUE"',  "text"),
    ("cod_via_transporte",      '"COD_VIA_TRANSPORTE"',      "text"),
    ("cl_compra",               '"CL_COMPRA"',               "text"),
    ("item_sa",                 '"ITEM_SA"',                 "text"),
    ("cif_us",                  '"CIF_US"',                  "text"),
    ("ad_valorem_us",           '"AD_VALOREM_US"',           "text"),
    ("moneda",                  '"MONEDA"',                  "text"),
    ("cantidad_mercancia",      '"CANTIDAD_MERCANCIA"',      "text"),
    ("cod_unidad_medida",       '"COD_UNIDAD_MEDIDA"',       "text"),
    ("tpo_carga",               '"TPO_CARGA"',               "text"),
]
EXPORT_MAP = [
    ("periodo",                 '"PERIODO"',                 "integer"),
    ("mes",                     '"MES"',                     "integer"),
    ("cod_aduana_tramitacion",  '"COD_ADUANA_TRAMITACION"',  "text"),
    ("cod_tipo_operacion",      '"COD_TIPO_OPERACION"',      "text"),
    ("cod_region_origen",       '"COD_REGION_ORIGEN"',       "text"),
    ("cod_via_transporte",      '"COD_VIA_TRANSPORTE"',      "text"),
    ("cod_puerto_embarque",     '"COD_PUERTO_EMBARQUE"',     "text"),
    ("cod_puerto_desembarque",  '"COD_PUERTO_DESEMBARQUE"',  "text"),
    ("cod_pais_destino",        '"COD_PAIS_DESTINO"',        "text"),
    ("cod_modalidad_venta",     '"COD_MODALIDAD_VENTA"',     "text"),
    ("moneda",                  '"MONEDA"',                  "text"),
    ("clausula_venta",          '"CLAUSULA_VENTA"',          "text"),
    ("cod_tipo_carga",          '"COD_TIPO_CARGA"',          "text"),
    ("item_sa",                 '"ITEM_SA"',                 "text"),
    ("fob_us_dusleg",           '"FOB_US_DUSLEG"',           "text"),
    ("fobus_ajustado_ivv",      '"FOBUS_AJUSTADO_IVV"',      "text"),
    ("peso_bruto_kg",           '"PESO_BRUTO_KG"',           "text"),
    ("cantidad_mercancia",      '"CANTIDAD_MERCANCIA"',      "text"),
    ("cod_unidad_medida",       '"COD_UNIDAD_MEDIDA"',       "text"),
]


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def select_list(colmap):
    """Build the SELECT projection: cast every column to its target type."""
    out = []
    for src, tgt, typ in colmap:
        if typ == "integer":
            out.append(f"CAST({src} AS INTEGER) AS {tgt}")
        else:
            # Cast through VARCHAR; DOUBLE -> text keeps the numeric literal,
            # which the rebuild SQL then REPLACE/NULLIF/::double back out.
            out.append(f"CAST({src} AS VARCHAR) AS {tgt}")
    out.append("CAST(periodo AS INTEGER) AS year")
    return ",\n           ".join(out)


def load_fact(con, src_table, tgt_table, colmap):
    years = [r[0] for r in con.execute(
        f"SELECT DISTINCT periodo FROM src.main.{src_table} WHERE periodo IS NOT NULL ORDER BY 1"
    ).fetchall()]
    total_src = con.execute(f"SELECT count(*) FROM src.main.{src_table}").fetchone()[0]
    log(f"{src_table}: {total_src:,} rows across {len(years)} years -> {tgt_table}")

    con.execute(f"DELETE FROM pg.{tgt_table}")
    proj = select_list(colmap)
    done = 0
    for y in years:
        t0 = time.time()
        con.execute(f"""
            INSERT INTO pg.{tgt_table}
            SELECT {proj}
            FROM src.main.{src_table}
            WHERE periodo = {y}
        """)
        n = con.execute(f"SELECT count(*) FROM src.main.{src_table} WHERE periodo = {y}").fetchone()[0]
        done += n
        log(f"   year {y}: {n:>10,} rows  ({time.time()-t0:5.1f}s)  cumulative {done:,}/{total_src:,}")
    return done, total_src


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["imports", "exports", "lookups"])
    args = ap.parse_args()

    if not os.path.exists(DUCKDB_PATH):
        sys.exit(f"DuckDB not found: {DUCKDB_PATH}")

    # In-memory root connection: a read_only source connection would force
    # every attached database (including Postgres) into read-only mode.
    con = duckdb.connect()
    con.execute("INSTALL postgres; LOAD postgres;")
    con.execute(f"ATTACH '{DUCKDB_PATH}' AS src (READ_ONLY)")
    con.execute(f"ATTACH '{PG}' AS pg (TYPE postgres)")
    con.execute("SET preserve_insertion_order=false")
    log("attached local Postgres")

    if args.only in (None, "lookups"):
        for t in LOOKUPS:
            con.execute(f"DELETE FROM pg.structured.{t}")
            con.execute(f"INSERT INTO pg.structured.{t} SELECT * FROM src.main.{t}")
            n = con.execute(f"SELECT count(*) FROM pg.structured.{t}").fetchone()[0]
            log(f"lookup {t:<26} {n:>7,} rows")

    if args.only in (None, "imports"):
        got, exp = load_fact(con, "raw_chile_imports", "structured.all_imports", IMPORT_MAP)
        log(f"all_imports done: {got:,}/{exp:,}")

    if args.only in (None, "exports"):
        got, exp = load_fact(con, "raw_chile_exports", "structured.all_exports", EXPORT_MAP)
        log(f"all_exports done: {got:,}/{exp:,}")

    log("Phase 1 complete.")


if __name__ == "__main__":
    main()
