# Fase 1: estado de la recolección

Fecha de revisión: 2026-09-29. No se contempla al profesor como proveedor de datos.

> Este apartado conserva el inventario inicial. La validación posterior se documenta en `validacion_geografica.md`; ya se instalaron dependencias y se ejecutó la prueba con DENUE. Seguridad sigue pendiente.

## Fuentes descargadas

| Fuente | Edición | Archivo original | Inspección inicial |
|---|---|---|---|
| Censo INEGI, AGEB y manzana urbana de Yucatán | 2020 | data/raw/inegi_censo2020/ageb_mza_urbana_31_cpv2020_csv.zip | 40,140 filas, 230 columnas; incluye agregados y desgloses |
| DENUE Yucatán | Mayo 2026, metadatos modificados 2026-05-20 | data/raw/inegi_denue/denue_31_csv.zip | 146,384 filas; 56,909 con cve_mun=050 |
| Marco Geoestadístico, Censo 2020, Yucatán | 2020 | data/raw/inegi_marco2020/31_yucatan.zip | ZIP íntegro, 16 capas SHP con archivos auxiliares |

DENUE y cartografía se descargan con `python src/download_inegi.py`. El script conserva los originales existentes y verifica el CRC de los ZIP. Los registros JSON de docs guardan URLs, tamaños y SHA-256. La URL de DENUE puede cambiar su contenido; para reproducir esta adquisición hay que conservar el original y verificar su hash. Una descarga futura no garantiza la misma edición.

## Hallazgos y límites

- Censo: filtro MUN=050, LOC=0001, MZA=000, AGEB distinto de 0000 produce 483 filas de totales por AGEB y 921,771 habitantes. Es una inspección preliminar, pendiente de cotejar las claves con polígonos y el total de localidad. No sumar estas filas junto con las manzanas.
- Los 56,909 negocios corresponden al municipio, no exclusivamente a la localidad urbana. Aún no son el numerador de un KPI de la ciudad.
- DENUE incluye id, clee, codigo_act, per_ocu, claves geográficas, latitud y longitud. fecha_alta no equivale necesariamente a fecha de apertura del negocio ni permite reconstruir por sí sola el universo de 2020.
- El PRJ de 31a indica MEXICO_ITRF_2008_LCC (Lambert conformal cónica, unidades metros). Falta cargar la geometría, validar topología y confirmar su correspondencia con el censo. La lectura del PRJ no constituye una prueba de integración espacial.
- Existe desfase Censo/Marco 2020 frente a DENUE 2026. Buscar edición histórica compatible o justificar explícitamente un análisis con población censal de referencia. No presentar población 2020 como población observada en 2026.
- No se han instalado dependencias geoespaciales ni construido el warehouse.

## Investigación de seguridad

| Fuente consultada | URL | Resultado y pertinencia |
|---|---|---|
| CEISP Yucatán | https://www.ceisp.gob.mx/ObservatorioDatos/SeguridadPublica | Página indexada como catálogo de informes; aperturas directas fallaron por timeout/502. No se confirmó archivo de incidentes con coordenadas. |
| SESNSP | https://www.gob.mx/sesnsp/acciones-y-programas/datos-abiertos-de-incidencia-delictiva | Publica incidencia estatal y municipal. Los agregados municipales no resuelven la asignación de incidentes a AGEB. |
| Ayuntamiento de Mérida | https://www.merida.gob.mx/copladem/content/documents/programas/2024-2027/PMP_SEGURIDAD_2427.pdf | Resultado de búsqueda muestra diagnóstico basado en SESNSP municipal; no se identificó microdato descargable con coordenadas. |
| FGJ CDMX, alternativa | https://datos.cdmx.gob.mx/pt_PT/dataset/carpetas-de-investigacion-fgj-de-la-ciudad-de-mexico | Catálogo previamente localizado con coordenadas y fechas. No descargado ni validado en este proyecto. Alternativa territorial, no sustituto de delitos de Mérida. |

La búsqueda no demuestra inexistencia de microdatos públicos de Mérida. Seguridad permanece pendiente; no fabricar ubicaciones, no repartir totales municipales entre AGEB como si fueran observaciones.

## Próximas comprobaciones

1. Cargar polígonos y verificar claves, CRS, geometrías vacías/inválidas y correspondencia con censo.
2. Perfilar coordenadas y duplicados de DENUE; realizar prueba punto-polígono y registrar puntos sin asignación o ambiguos.
3. Continuar la búsqueda pública de delitos locales; si no aparece una fuente verificable, presentar una alternativa territorial completa y documentar el cambio de alcance.
4. Elegir periodos y unidad geográfica finales solo con evidencia suficiente.

La Fase 1 NO está completa: falta la capa de delitos georreferenciados y la prueba espacial exigida.
