-- WazeCargo local mirror — structured schema (raw customs layer)
-- Mirrors the AWS RDS structured.* contract expected by
-- modeling/03_rebuild_clean_maritime.sh: quoted UPPERCASE text columns + year.
-- UNLOGGED: this is a rebuildable local mirror, durability not required.

DROP TABLE IF EXISTS structured.all_imports;
CREATE UNLOGGED TABLE structured.all_imports (
    "PERIODO"                 integer,
    "MES"                     integer,
    "COD_ADUANA_TRAMITACION"  text,
    "COD_TIPO_OPERACION"      text,
    "COD_PAIS_ORIGEN"         text,
    "COD_PAIS_ADQUISICION"    text,
    "COD_REGIMEN_IMPORTACION" text,
    "COD_PUERTO_EMBARQUE"     text,
    "COD_PUERTO_DESEMBARQUE"  text,
    "COD_VIA_TRANSPORTE"      text,
    "CL_COMPRA"               text,
    "ITEM_SA"                 text,
    "CIF_US"                  text,
    "AD_VALOREM_US"           text,
    "MONEDA"                  text,
    "CANTIDAD_MERCANCIA"      text,
    "COD_UNIDAD_MEDIDA"       text,
    "TPO_CARGA"               text,
    year                      integer
);

DROP TABLE IF EXISTS structured.all_exports;
CREATE UNLOGGED TABLE structured.all_exports (
    "PERIODO"                 integer,
    "MES"                     integer,
    "COD_ADUANA_TRAMITACION"  text,
    "COD_TIPO_OPERACION"      text,
    "COD_REGION_ORIGEN"       text,
    "COD_VIA_TRANSPORTE"      text,
    "COD_PUERTO_EMBARQUE"     text,
    "COD_PUERTO_DESEMBARQUE"  text,
    "COD_PAIS_DESTINO"        text,
    "COD_MODALIDAD_VENTA"     text,
    "MONEDA"                  text,
    "CLAUSULA_VENTA"          text,
    "COD_TIPO_CARGA"          text,
    "ITEM_SA"                 text,
    "FOB_US_DUSLEG"           text,
    "FOBUS_AJUSTADO_IVV"      text,
    "PESO_BRUTO_KG"           text,
    "CANTIDAD_MERCANCIA"      text,
    "COD_UNIDAD_MEDIDA"       text,
    year                      integer
);

-- Lookup tables (column names must match the rebuild SQL exactly,
-- including the upstream 'rgimen' spelling).
DROP TABLE IF EXISTS structured.lkp_aduanas;
CREATE TABLE structured.lkp_aduanas (
    cod_aduana_tramitacion integer PRIMARY KEY, nombre_aduana text);

DROP TABLE IF EXISTS structured.lkp_clausulas;
CREATE TABLE structured.lkp_clausulas (
    cl_compra integer PRIMARY KEY, nombre_clausula text, sigla_clausula text);

DROP TABLE IF EXISTS structured.lkp_harmonized_system;
CREATE TABLE structured.lkp_harmonized_system (
    section text, hscode text, description text, parent text, level text);

DROP TABLE IF EXISTS structured.lkp_modalidades_venta;
CREATE TABLE structured.lkp_modalidades_venta (
    cod_modalidad_venta integer PRIMARY KEY, nombre_modalidad_venta text,
    descripcion_modalidad_venta text);

DROP TABLE IF EXISTS structured.lkp_moneda;
CREATE TABLE structured.lkp_moneda (
    moneda integer PRIMARY KEY, moneda_1 text, pais_moneda text);

DROP TABLE IF EXISTS structured.lkp_paises;
CREATE TABLE structured.lkp_paises (
    cod_pais integer PRIMARY KEY, nombre_pais text, nombre_continente text);

DROP TABLE IF EXISTS structured.lkp_puertos;
CREATE TABLE structured.lkp_puertos (
    cod_puerto integer PRIMARY KEY, nombre_puerto text, tipo_puerto text,
    cod_pais double precision, pais text, zona_geografica text);

DROP TABLE IF EXISTS structured.lkp_regimen_importacion;
CREATE TABLE structured.lkp_regimen_importacion (
    cod_rgimen_importacion integer PRIMARY KEY,
    nombre_rgimen_importacion text, sigla_rgimen_importacion text);

DROP TABLE IF EXISTS structured.lkp_regiones;
CREATE TABLE structured.lkp_regiones (
    cod_region_origen integer PRIMARY KEY, nombre_region text);

DROP TABLE IF EXISTS structured.lkp_tipos_carga;
CREATE TABLE structured.lkp_tipos_carga (
    cod_tipo_carga text PRIMARY KEY, nombre_tipo_carga text,
    descripcion_tipo_carga text);

DROP TABLE IF EXISTS structured.lkp_tipos_operacion;
CREATE TABLE structured.lkp_tipos_operacion (
    cod_tipo_operacion integer PRIMARY KEY, nombre_tipo_operacion text,
    nombre_a_consignar text, ingreso_salida text, operacion text);

DROP TABLE IF EXISTS structured.lkp_unidades_medida;
CREATE TABLE structured.lkp_unidades_medida (
    cod_unidad_medida integer PRIMARY KEY, unidad_medida text,
    nombre_unidad_medida text);

DROP TABLE IF EXISTS structured.lkp_vias_transporte;
CREATE TABLE structured.lkp_vias_transporte (
    cod_via_transporte integer PRIMARY KEY, nombre_via_transporte text);
