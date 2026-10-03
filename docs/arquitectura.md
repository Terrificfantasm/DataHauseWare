> Implementación vigente: [modelo y ETL de Fase 2](fase2_modelo_etl.md). Este archivo conserva la propuesta previa.

> Estado vigente: [cierre de Fase 1 y alcance operativo](cierre_fase1.md). Este documento conserva antecedentes; el DW sigue pendiente.

# Arquitectura adaptable (propuesta, no DW terminado)

## Separación de responsabilidades

1. `config/`: territorio, filtros, periodos y rutas. Mérida activa, CDMX ejemplo desactivado.
2. `data/raw/`: originales inmutables, uno por fuente/edición; manifiestos en docs.
3. `src/`: adaptadores de fuentes, normalización y motor de asignación espacial.
4. `outputs/<territorio>/phase1/`: diagnósticos regenerables, sin mezclar ciudades.
5. PostgreSQL `staging`: datos normalizados y trazabilidad futura.
6. PostgreSQL `dw`: hechos con granularidades distintas y dimensiones compartidas.
7. PostgreSQL `analytics`: consultas/vistas para indicadores y exportación analítica final.

## Contrato previsto de seguridad

Cada adaptador deberá producir `source_record_id`, `source_release`, `record_kind`, `crime_type_original`, `occurred_at` (nullable), `reported_at` (nullable), `time_precision`, `longitude`/`latitude` (nullable), `location_method`, `location_precision`, `source_crs`. Antes de asignar puntos, transformar al CRS de entrada del motor, EPSG:4326.

`record_kind` distingue incidente, carpeta, llamada y denuncia. La fecha de apertura no reemplaza silenciosamente la fecha de hechos. La precisión puede ser día, mes o año: no inventar un día para datos mensuales. Conservar la taxonomía original; cualquier equivalencia entre delitos requiere una tabla explícita de correspondencias. Ningún dato sintético entra en resultados.

Estados espaciales: assigned, invalid_coordinates, outside_selected_areas, ambiguous. Si solo hay AGEB, registrar integración por clave y no afirmar prueba punto-polígono. Si hay direcciones, geocodificación y evaluación de calidad son una etapa adicional. Datos por colonia requieren replantear el modelo territorial; no usar centroides como ubicaciones observadas.

## Granularidad propuesta para Fase 2

| Tabla | Una fila representa |
|---|---|
| dim_geography | Una clave INEGI con su versión cartográfica y geometría |
| dim_source_release | Una edición de una fuente, con URL y hash |
| dim_economic_activity | Un código SCIAN de una versión del catálogo |
| dim_crime_type | Una categoría con catálogo/fuente de origen |
| fact_population | Una AGEB por edición censal |
| fact_business_snapshot | Un establecimiento por edición de DENUE |
| fact_crime_record | Un registro identificable de una fuente, según su unidad de observación |

Se definirán claves sustitutas, dimensiones de fecha y actualización de registros después de conocer la fuente de seguridad. No unir filas crudas de las tres tablas de hechos: agregar cada hecho al nivel de comparación antes de combinarlos. Territorio y edición siempre deben formar parte del filtro y del linaje; ciudades distintas no se mezclan.

## Puertas de validación

- Censo: unicidad de totales AGEB, reservados/faltantes, conciliación con localidad.
- Geografía: claves, CRS, geometrías válidas/no vacías, cobertura y futura revisión de superposiciones topológicas.
- DENUE: identificadores duplicados, coordenadas, tasa de asignación y diferencias de claves declaradas.
- Seguridad: disponibilidad, cobertura institucional/temporal, ubicación de hechos, unidad de registro y deduplicación documentada.
- Comparabilidad: años y límites coherentes; denominadores cero tratados como no definido.

El motor espacial probado con establecimientos puede reutilizarse con delitos, pero esa prueba NO satisface por sí sola el requisito de integrar delitos reales.
