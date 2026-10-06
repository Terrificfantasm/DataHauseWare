# Urban Intelligence / DataHauseWare

Proyecto académico de **Business Intelligence - Unit 2** de la Universidad Politécnica de Yucatán. La implementación final usa **AGEB urbanas de Ciudad de México (CDMX)** como unidad geográfica común para integrar información demográfica, económica, territorial y de seguridad pública en un Data Warehouse reproducible con PostgreSQL/PostGIS.

La implementación activa y los resultados finales corresponden a **CDMX urbano 2020**. El material previo de Mérida se conserva únicamente como antecedente histórico y no se mezcla con el Data Warehouse final.

## Estado final

- **Fase 1 - Data & Geography:** completada y validada.
- **Fase 2 - ETL & PostgreSQL/PostGIS DW:** completada y validada.
- **Fase 3 - Spatial Analytics:** completada y ejecutada con el dataset real.
- **Dataset final:** `dataset_id = 2`
- **Fingerprint:** `cf1717a7ad473908601293c7f72ac73de3d2e854f384c4e7e2e434fe8620cd4c`
- **Regla FGJ:** `candidate-v1`
- **Unidad de análisis:** AGEB urbana, CDMX.

Los resultados finales de Fase 3 están versionados en `docs/phase3/`.

## Objetivo analítico

Construir un Data Warehouse geoespacial reproducible que permita transformar datos públicos en indicadores territoriales y análisis espaciales para apoyar interpretación y toma de decisiones.

El flujo completo es:

```text
RAW
  -> STAGING
  -> CLEAN
  -> SPATIAL JOIN
  -> POSTGRESQL / POSTGIS DW
  -> ANALYTICS
  -> PHASE 3 EXPORT
  -> CORRELATION + MORAN + LISA
```

## Fuentes de datos

| Dominio | Fuente / edición | Uso principal |
|---|---|---|
| Demografía | INEGI Censo de Población y Vivienda 2020 | población, grupos de edad, PEA y denominadores |
| Geografía | INEGI Marco Geoestadístico 2020 | polígonos AGEB, identificadores y superficie |
| Economía | DENUE noviembre 2020, SCIAN 2018 | establecimientos, actividad económica y coordenadas |
| Seguridad | FGJ CDMX, investigaciones iniciadas en 2020 | categoría/tipo, temporalidad y coordenadas |

Las URLs, hashes y metadatos de adquisición se conservan en `docs/cdmx_acquisition.json` y archivos relacionados. Los datos RAW no se versionan en Git.

## Estrategia geográfica

La unidad final es **AGEB urbana**.

El universo validado contiene:

- **2,431 AGEB urbanas**
- **9,138,524 habitantes mapeados**
- 2 AGEB censales excluidas por no contar con geometría urbana validada
- 16 alcaldías de CDMX cubiertas

AGEB permite suficiente detalle para comparar patrones locales sin reducir el análisis a solo 16 alcaldías.

Los puntos DENUE y FGJ se asignan mediante intersección espacial. Los registros inválidos, fuera de cobertura o ambiguos conservan su estado; **no se fuerza una asignación por cercanía**.

## Arquitectura del Data Warehouse

Dimensiones principales:

- `dw.dim_geography`
- `dw.dim_date`
- `dw.dim_economic_activity`
- `dw.dim_crime_type`
- `dw.dim_source_release`

Tablas de hechos:

- `dw.fact_population`
- `dw.fact_business_snapshot`
- `dw.fact_crime_record`

El detalle del modelo, grain y relaciones está documentado en `docs/fase2_modelo_etl.md`.

## ETL y reglas de calidad

Principios principales:

- conservar fuentes originales sin modificación;
- validar hashes y ediciones;
- mantener claves INEGI como texto;
- preservar faltantes como `NULL`, nunca convertirlos automáticamente a cero;
- transformar coordenadas a geometrías espaciales;
- documentar rechazos y registros fuera de cobertura;
- separar los hechos por grain antes de agregarlos;
- generar KPIs desde PostgreSQL/PostGIS, no desde los archivos RAW.

## Totales validados del Data Warehouse

La ejecución final reconcilia:

- **2,431 AGEB**
- **9,138,524 habitantes**
- **474,328 registros DENUE**
- **472,608 establecimientos DENUE asignados**
- **204,121 registros FGJ publicados**
- **199,650 registros FGJ bajo `candidate-v1`**
- **191,233 registros candidate-v1 con asignación AGEB única**
- **202,829 establecimientos de retail asignados**
- **18 controles del DW aprobados**
- **11 controles de la capa analítica aprobados**

## KPIs

La capa analítica implementa los 14 KPIs requeridos.

### Demográficos

- total population
- population density
- PEA rate
- population by age group

### Económicos

- total businesses
- business density
- businesses per 1,000 residents
- retail density
- service density
- dominant economic activity

### Seguridad

- total selected security records
- security records per 1,000 residents
- records by type and time
- security records relative to business activity

Las fórmulas y reglas de denominadores se encuentran en `docs/kpis_cdmx.md`.

## Fase 3 - Resultados reales

La Fase 3 consume únicamente el export generado desde PostgreSQL/PostGIS mediante `src/export_analysis.py`.

### Correlaciones

Las tres relaciones seleccionaron **Spearman** debido a skewness y/o presencia de outliers.

| Relación | Método | Coeficiente | p-value | n |
|---|---|---:|---:|---:|
| Population density vs. business density | Spearman | **0.4012** | `1.139e-94` | 2431 |
| Population density vs. crime records per 1,000 | Spearman | **-0.3663** | `1.572e-77` | 2414 |
| Business density vs. crime records per 1,000 | Spearman | **0.3007** | `1.245e-51` | 2414 |

Interpretación:

- la densidad poblacional presenta una asociación positiva moderada con la densidad de negocios;
- la densidad poblacional presenta una asociación negativa moderada con la tasa de registros FGJ por 1,000 habitantes;
- la densidad de negocios presenta una asociación positiva más débil con esa tasa.

Estas relaciones **no prueban causalidad**.

### Global Moran's I

Se usa **Queen contiguity**, 999 permutaciones y `seed = 42`.

| Indicador | Moran's I | p permutacional | n |
|---|---:|---:|---:|
| Crime records per 1,000 | **0.0250** | **0.022** | 2414 |
| Business density | **0.4398** | **0.001** | 2431 |

`business_density` muestra una autocorrelación espacial positiva clara. `crime_records_per_1000` también presenta autocorrelación positiva estadísticamente significativa, pero con una magnitud mucho menor.

### Local Moran / LISA

#### Crime records per 1,000

- Significant AGEB: **141**
- High-High: **20**
- Low-Low: **11**
- Low-High: **110**
- High-Low: **0**
- Not significant: **2272**

#### Business density

- Significant AGEB: **170**
- High-High: **121**
- Low-Low: **25**
- Low-High: **23**
- High-Low: **1**
- Not significant: **2260**

Se reporta una isla espacial (`geography_id = 4081`) en lugar de conectarla artificialmente.

### Bivariate Moran's I

Relación:

```text
local business_density
        ->
spatial lag(crime_records_per_1000)
```

Resultado:

- Bivariate Moran's I = **0.0261**
- permutation p-value = **0.047**
- n = **2414**

La asociación espacial bivariada es positiva pero pequeña y apenas significativa al nivel de 0.05. No debe interpretarse como evidencia causal.

## Scripts de Fase 3

- `src/phase3_common.py`
- `src/phase3_geographic_distribution.py`
- `src/phase3_correlations.py`
- `src/phase3_global_moran.py`
- `src/phase3_lisa.py`
- `src/phase3_bivariate_moran.py`
- `src/phase3_run_all.py`

## Reproducibilidad

### 1. Crear entorno

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
# Configurar POSTGRES_PASSWORD en .env
docker compose up -d --wait
```

### 2. Restaurar fuentes y construir el DW

```powershell
.\.venv\Scripts\python.exe src/restore_cdmx_sources.py
.\.venv\Scripts\python.exe src/database.py
.\.venv\Scripts\python.exe src/load_warehouse.py
.\.venv\Scripts\python.exe src/publish_analytics.py
.\.venv\Scripts\python.exe src/list_datasets.py
```

### 3. Validar el dataset

```powershell
.\.venv\Scripts\python.exe src/validate_warehouse.py --dataset-id <ID>
.\.venv\Scripts\python.exe src/validate_analytics.py --dataset-id <ID>
```

No se debe asumir que el ID será siempre `2` en una instalación nueva. Identificar el dataset mediante `list_datasets.py` y su fingerprint.

### 4. Exportar desde el DW

```powershell
.\.venv\Scripts\python.exe src/export_analysis.py --dataset-id <ID>
```

Esto genera:

```text
outputs/cdmx/phase3_inputs/<ID>/
├── kpi_ageb.csv
├── age_distribution.csv
├── crime_by_type_month.csv
├── areas.geojson
└── manifest.json
```

### 5. Ejecutar Fase 3 completa

```powershell
.\.venv\Scripts\python.exe src/phase3_run_all.py --dataset-id <ID> --permutations 999 --seed 42
```

### 6. Tests

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

GitHub Actions ejecuta además los tests con un servicio temporal de PostGIS.

## Resultados versionados

Los resultados seleccionados para la entrega final están en:

```text
docs/phase3/
├── README.md
├── input_manifest.json
├── checksums.json
├── figures/
├── tables/
└── summaries/
```

Los outputs completos regenerables permanecen fuera de Git mediante `.gitignore`.

## Estructura principal

```text
.
├── README.md
├── requirements.txt
├── compose.yaml
├── config/
├── docs/
│   └── phase3/
├── sql/
├── src/
└── tests/
```

## Limitaciones

- El universo corresponde a AGEB urbanas de CDMX, no a toda la Zona Metropolitana.
- Dos AGEB censales no tienen geometría urbana validada dentro del alcance activo.
- Los registros FGJ son filas publicadas de investigaciones iniciadas en 2020; no deben interpretarse como un censo completo de incidentes criminales únicos.
- La precisión posicional de las coordenadas FGJ no está completamente documentada.
- Las simulaciones muestran sensibilidad de asignaciones cercanas a límites AGEB.
- 17 AGEB tienen denominadores que hacen indefinida la tasa `crime_records_per_1000`; se excluyen de esos análisis y no se imputan como cero.
- Correlaciones, Moran y LISA describen asociación, no causalidad.
- Los resultados dependen del grain geográfico y de la definición de vecindad (MAUP y sensibilidad espacial).

## Documentación

- `docs/cierre_fase1.md`
- `docs/plan_b_cdmx.md`
- `docs/fase2_modelo_etl.md`
- `docs/kpis_cdmx.md`
- `docs/diccionario_kpis.md`
- `docs/simulaciones_cdmx.md`
- `HANDOFF_FASE3.md`
- `docs/phase3/README.md`
