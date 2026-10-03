# Continuación del proyecto: consumo del DW y Fase 3

Actualizado 2026-10-03. Implementación de Fase 2 lista para revisión. Cualquier herramienta o asistente puede continuar usando este archivo, el [modelo](docs/fase2_modelo_etl.md) y el [cierre de Fase 1](docs/cierre_fase1.md). No depender de la conversación para ejecutar.

## Qué está listo

Modelo, migraciones, ETL de originales a staging/DW, conciliaciones, vistas de los 14 indicadores y exportador desde el DW. Fuentes: CDMX 2020, DENUE 11/2020, FGJ inicio 2020. PostGIS local conserva un dataset confirmado; identificador local actual 2, pero consultar siempre el de la propia instalación.

## Desde un clon limpio

Requisitos: Python 3.12, Docker Desktop en ejecución, Git. Trabajar en la raíz DataHauseWare. Antes del merge, usar la rama codex/fase-2-modelo-etl-postgis; después, la rama que contenga ese PR.

1. Crear entorno e instalar requirements.txt.
2. Copiar .env.example a .env y sustituir el valor de POSTGRES_PASSWORD por una contraseña local. No subir .env; no reutilizar la contraseña de otra persona.
3. Ejecutar estos comandos en PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
docker compose up -d --wait
.\.venv\Scripts\python.exe src/restore_cdmx_sources.py
.\.venv\Scripts\python.exe src/database.py
.\.venv\Scripts\python.exe src/load_warehouse.py
.\.venv\Scripts\python.exe src/publish_analytics.py
.\.venv\Scripts\python.exe src/list_datasets.py
```

Si la descarga mutable ya no coincide con el SHA-256, detenerse y solicitar la copia archivada de esa edición. No cambiar el manifiesto sólo para hacer pasar la validación. El pipeline de Fase 2 no requiere regenerar las 80 simulaciones ni salidas de Fase 1.

Elige el dataset mostrado por list_datasets.py. Sustituye 2 en este ejemplo si el tuyo tiene otro ID:

```powershell
.\.venv\Scripts\python.exe src/validate_warehouse.py --dataset-id 2
.\.venv\Scripts\python.exe src/validate_analytics.py --dataset-id 2
.\.venv\Scripts\python.exe src/export_analysis.py --dataset-id 2
```

Repetir load_warehouse.py debe terminar con idempotent_skip=true si código e insumos siguen idénticos. Si hay varios datasets, seleccionar uno por fingerprint/edición; no sumar todos. Los resultados exportados quedan en outputs/cdmx/phase3_inputs/ID/: kpi_ageb.csv, age_distribution.csv, crime_by_type_month.csv, areas.geojson y manifest.json. Se generaron mediante consultas al DW, no directamente desde originales.

## Prueba de funcionamiento

- Validador DW: 18 controles aprobados; población 9,138,524; negocios asignados 472,608; seguridad seleccionada y asignada 191,233.
- Validador analítico: 11 controles, incluida ausencia de multiplicación de conteos, NULL por ceros y 77 empates de dominancia.
- Pruebas sin PostgreSQL: `python -m pytest tests -q` (14 pasan; integración se omite si no se configura base de prueba).
- Integración: crear una base vacía dedicada llamada urban_intelligence_test y establecer `$env:DW_TEST_DATABASE='urban_intelligence_test'` antes de pytest; la cuenta debe poder migrarla. La suite no borra la base ni toca el DW principal. 23 pruebas pasaron localmente con esa configuración.
- GitHub Actions levanta su propio servicio PostGIS de pruebas; no usa las fuentes voluminosas. Revisar su resultado por separado de las conciliaciones del dataset real.

## Qué consultar

`analytics.kpi_ageb`: una fila por AGEB y dataset. Claves de unión: dataset_id + geography_id; cvegeo es código textual. `analytics.age_distribution`: ocho filas por AGEB, con NULL cuando el conteo no es conocido. `analytics.crime_by_type_month`: grupos observados de tipo/mes, fecha de apertura.

`dw.dim_geography`: polígonos 4326, área geodésica. Reproyectar para distancias, no usar grados como metros. `meta.quality_issue`: motivos de exclusión o calidad. `dw.dataset_source` + `dw.dim_source_release`: hashes y procedencia. Ejemplos SQL en sql/examples/analysis.sql; consultas siempre filtradas por dataset.

No unir hechos crudos de población, negocios y FGJ entre sí. Usar las vistas o agregar cada uno antes de combinar. No convertir NULL en cero para hacer funcionar una correlación. Documentar número de observaciones tras cada exclusión.

## Paquetes de continuación

| Trabajo | Entrega verificable |
|---|---|
| Exploración y tres correlaciones requeridas | Script/notebook que consume DW o exportación documentada del DW; variables, exclusiones, gráficos e interpretación sin causalidad |
| Pesos, dos Moran global, LISA y relación bivariada requerida | Vecindad justificada, CRS, tratamiento de islas, pruebas/permutaciones y mapas; semilla reproducible |
| Visualización y reporte final | Figuras regenerables con leyendas, fuentes y periodos; reporte de 4–6 páginas conforme al enunciado |

Cada aportación debe tener cambios reales, documentación breve y su commit. Para análisis nuevos crear una rama desde la base acordada y abrir PR. No fabricar atribuciones ni cambios para cumplir una cuota.

## Decisiones que deben respetarse

2,431 AGEB comparables, sin reemplazar las dos localidades excluidas por polígonos rurales. FGJ es cohorte de inicio 2020; no toda la delincuencia ni todos los hechos ocurridos en ese año. `_id` es identificador de fila, no prueba de incidente único. Candidate-v1 conserva competencia desconocida por su patrón temporal; no cambiar regla sin versionarla.

La precisión espacial es desconocida; las simulaciones no la certifican. Repetir sensibilidad sobre tasas/focos inferenciales si se interpretan. La agrupación municipal debe conservar numeradores y denominadores del mismo universo urbano. No imputar coordenadas, celdas reservadas ni corregir ubicaciones por proximidad.

## Punto de reanudación

Primero revisar el PR y ejecutar la guía en el equipo que hará análisis. Después empezar por exploración y definición de vecindad. Si una comprobación falla, conservar su error y hashes; no cambiar fuentes o filtros para forzar los totales.
