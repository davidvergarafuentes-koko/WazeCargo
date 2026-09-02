-- WazeCargo local mirror — maritime schema (clean layer)
-- Column contract per docs/er_ddl_reference.md; target of
-- modeling/03_rebuild_clean_maritime.sh.

DROP TABLE IF EXISTS maritime.clean_maritime_imports;
CREATE UNLOGGED TABLE maritime.clean_maritime_imports (
    periodo              smallint,
    mes                  smallint,
    aduana               text,
    regimen_importacion  text,
    sigla_regimen        text,
    pais_origen          text,
    continente_origen    text,
    puerto_embarque      text,
    zona_geo_embarque    text,
    puerto_desembarque   text,
    tipo_carga           text,
    clausula_compra      text,
    sigla_clausula       text,
    item_sa              text,
    hs6_subpartida       text,
    hs4_partida          text,
    hs2_capitulo         text,
    descripcion_producto text,
    cif_us               double precision,
    cantidad_mercancia   double precision,
    unidad_medida        text,
    sigla_unidad         text
);

DROP TABLE IF EXISTS maritime.clean_maritime_exports;
CREATE UNLOGGED TABLE maritime.clean_maritime_exports (
    periodo              smallint,
    mes                  smallint,
    aduana               text,
    region_origen        text,
    puerto_embarque      text,
    zona_geo_embarque    text,
    pais_destino         text,
    continente_destino   text,
    puerto_desembarque   text,
    tipo_carga           text,
    clausula_venta       text,
    sigla_clausula       text,
    item_sa              text,
    hs6_subpartida       text,
    hs4_partida          text,
    hs2_capitulo         text,
    descripcion_producto text,
    fob_us               double precision,
    peso_bruto_kg        double precision,
    cantidad_mercancia   double precision,
    unidad_medida        text,
    sigla_unidad         text
);
