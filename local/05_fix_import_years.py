#!/usr/bin/env python3
"""
WazeCargo local mirror — repair 2024/2025/2026 in structured.all_imports.

The source waze_cargo.duckdb has three defects in the import fact table that
do not exist in the original Chilean Customs (Aduanas) CSVs:

  2024  ingresos2024.csv writes PERIODO as "2024,00" (decimal comma). Whatever
        built the DuckDB failed that cast, leaving 1,821,211 rows with NULL
        periodo/mes — invisible to the rebuild, which loops over DISTINCT year.
  2025  ingresos2025.csv was loaded twice (3,855,318 = 2 x 1,927,659).
  2026  ingresos2026.csv was loaded twice (305,576 = 2 x 152,788).

Years 2002-2023 match the CSVs exactly and are left untouched.

This reloads those three years straight from the CSVs. Columns are kept as raw
text, which is what the AWS structured contract expects: the rebuild SQL does
SPLIT_PART(TRIM(col), ',', 1) on the code columns and REPLACE(col, ',', '.')
on the numerics precisely because of this European decimal format.
"""
import os, time
import duckdb

CSV_DIR = os.environ.get(
    "WZ_CSV_IMPO",
    "/mnt/windows/Users/koko/Desktop/Master IA & Data Solutions/Final Projet/Waze cargo/data/impo",
)
PG = os.environ.get(
    "WZ_PG_DSN",
    "host=localhost port=5432 dbname=waze_cargo user=wazecargo password=wazecargo_local",
)
YEARS = [2024, 2025, 2026]

COLS = ["PERIODO","MES","COD_ADUANA_TRAMITACION","COD_TIPO_OPERACION",
        "COD_PAIS_ORIGEN","COD_PAIS_ADQUISICION","COD_REGIMEN_IMPORTACION",
        "COD_PUERTO_EMBARQUE","COD_PUERTO_DESEMBARQUE","COD_VIA_TRANSPORTE",
        "CL_COMPRA","ITEM_SA","CIF_US","AD_VALOREM_US","MONEDA",
        "CANTIDAD_MERCANCIA","COD_UNIDAD_MEDIDA","TPO_CARGA"]


def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def main():
    con = duckdb.connect()
    con.execute("INSTALL postgres; LOAD postgres;")
    con.execute(f"ATTACH '{PG}' AS pg (TYPE postgres)")
    con.execute("SET preserve_insertion_order=false")

    # Clear the corrupt partitions: the three bad years plus the NULL-year
    # rows that are really the unparsed 2024 file.
    con.execute("DELETE FROM pg.structured.all_imports WHERE year IN (2024,2025,2026) OR year IS NULL")
    log("cleared years 2024/2025/2026 and NULL-year rows")

    # Column 16 is spelled three different ways across these files
    # (CANTIDAD_MERCANCIA / CANTIDAD_MERCANCÍA in latin-1 / UTF-8), and the
    # files do not share one encoding: 2024 is latin-1, 2026 is UTF-8. So read
    # positionally with header=false + skip=1 and never reference a CSV name.
    proj = [
        'CAST(SPLIT_PART(column00, \',\', 1) AS INTEGER)',   # PERIODO
        'CAST(SPLIT_PART(column01, \',\', 1) AS INTEGER)',   # MES
    ]
    proj += [f"column{i:02d}" for i in range(2, 18)]
    proj.append('CAST(SPLIT_PART(column00, \',\', 1) AS INTEGER)')  # year
    projection = ", ".join(proj)
    target_cols = ", ".join(f'"{c}"' for c in COLS) + ", year"

    total = 0
    for y in YEARS:
        path = os.path.join(CSV_DIR, f"ingresos{y}.csv")
        if not os.path.exists(path):
            log(f"!! missing {path} — skipped")
            continue
        t0 = time.time()
        last_err = None
        for enc in ("utf-8", "latin-1"):
            try:
                con.execute(f"""
                    INSERT INTO pg.structured.all_imports ({target_cols})
                    SELECT {projection}
                    FROM read_csv('{path}', delim=';', header=false, skip=1,
                                  quote='"', all_varchar=true,
                                  ignore_errors=false, encoding='{enc}')
                """)
                last_err = None
                break
            except Exception as e:
                last_err = e
                con.execute("DELETE FROM pg.structured.all_imports WHERE year = ?", [y])
        if last_err is not None:
            raise last_err
        n = con.execute(
            "SELECT count(*) FROM pg.structured.all_imports WHERE year = ?", [y]
        ).fetchone()[0]
        total += n
        log(f"year {y}: {n:>10,} rows loaded via {enc} ({time.time()-t0:.1f}s)")

    log(f"repair complete, {total:,} rows across {len(YEARS)} years")


if __name__ == "__main__":
    main()
