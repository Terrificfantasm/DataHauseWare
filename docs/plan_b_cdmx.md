> Estado vigente: [cierre de Fase 1 y alcance operativo](cierre_fase1.md). Este documento conserva antecedentes; el DW sigue pendiente.

# Plan B activo: Ciudad de México

Actualizado: 2026-09-30 (America/Mexico_City).

## Decisión y alcance

El usuario informó que conseguir seguridad local exige una carta y la entrega llegaría después del plazo académico. Se activa CDMX por disponibilidad pública. El alcance difiere de Mérida en el enunciado y debe explicitarse en la entrega. No se espera información del profesor. Los insumos, configuraciones y resultados de Mérida se conservan como antecedente.

La selección operativa comprende las AGEB urbanas de la entidad 09, en sus 16 alcaldías; no toda la zona metropolitana ni las áreas rurales. Censo y Marco 2020, DENUE noviembre 2020 (SCIAN 2018), carpetas FGJ iniciadas en 2020. La coincidencia de año no implica igual fecha de referencia: DENUE utiliza cartografía de septiembre 2019 y referencias por atributo descritas en evaluacion_denue_202011.md. 2020 es además un periodo de pandemia; no representar estos resultados como patrón actual de seguridad.

## Fuentes efectivamente adquiridas

URLs, tamaños, SHA-256 y fechas UTC: [manifiesto](cdmx_acquisition.json). Originales: `data/raw/cdmx/`. La descarga original de FGJ falló por certificado TLS vencido; se obtuvo la exportación CSV del DataStore oficial, sin desactivar la validación TLS. La API declara 204,121 filas y el CSV tiene exactamente esa cantidad. Metadatos de recurso y conteo conservados junto al original. [Portal FGJ](https://datos.cdmx.gob.mx/dataset/carpetas-de-investigacion-fgj-de-la-ciudad-de-mexico), licencia publicada CC-BY-4.0-ESP; INEGI: términos de libre uso.

| Fuente | Resultado del perfil/integración |
|---|---|
| Censo 2020 | 2,433 AGEB; 9,145,632 habitantes; suma igual a totales de localidades urbanas |
| Marco 2020 | 2,431 polígonos; cero geometrías inválidas, vacías, nulas o claves duplicadas |
| DENUE 11/2020 | 474,328 filas: 472,608 asignadas y 1,720 fuera; cero IDs duplicados |
| FGJ inicio 2020 | 204,121 filas: 194,356 asignadas, 9,111 coordenadas inválidas/ausentes, 654 fuera; cero asignaciones ambiguas |

Censo sin polígono: `0901101101107` (La Ciénega, 3,050 habitantes) y `0901201351227` (Lomas de Tepemecatl, 4,058). No se inventó geometría ni se repartió población. La prueba usa los 2,431 polígonos coincidentes y 9,138,524 habitantes; 7,108 quedan fuera por esta discrepancia. La configuración enumera las dos excepciones; cualquier cambio de claves provoca error. Debe investigarse su correspondencia antes de cerrar la cobertura definitiva. Auditoría posterior: cero superposiciones positivas; las dos localidades aparecen como rurales en Marco 2020. Ver [auditoría CDMX](auditoria_cdmx.md).

## Contrato y límites de seguridad

- Unidad: fila publicada de FGJ. `_id` es identificador del DataStore, no un número de carpeta cuya unicidad sustantiva esté demostrada. Clave técnica: SHA-256 del archivo + `_id`.
- Todas las fechas de inicio pertenecen a 2020. Sólo 190,570 fechas de hechos pertenecen a 2020; 43 no son interpretables y una es posterior a la fecha de inicio. Conservar ambas fechas; no presentar esta cohorte como todos los hechos ocurridos en 2020.
- 679 filas comparten todos sus atributos públicos con otras filas. Se conservan: no hay fundamento para deduplicar carpetas por coincidencia de atributos.
- 3,810 filas marcadas como hechos no delictivos, 661 con competencia INCOMPETENCIA y 132,146 con competencia NA. Flags separados; no sumar como categorías excluyentes sin comprobar sus cruces. Elegibilidad final pendiente.
- Coordenadas decimales interpretadas provisionalmente como WGS84. Datum y precisión posicional no están acreditados por la documentación examinada. Que un punto caiga dentro de una AGEB no demuestra precisión a esa escala.
- `intersects` asigna sólo coincidencia única; rechazos conservados con motivo. Fuera de AGEB urbanas no equivale automáticamente a fuera de CDMX.
- Conteos espaciales incluyen todas las filas como diagnóstico de cobertura. Ningún conteo es todavía KPI final de delitos ni incidencia real: subregistro, elegibilidad y cobertura deben declararse.
- Original sin modificar; salidas de asignación omiten domicilios y coordenadas puntuales. Preservar categorías originales.

## Adaptaciones verificadas

Se corrigió el sumatorio censal para excluir totales de entidad y municipio al seleccionar varias localidades. DENUE histórico entrega claves sin ceros iniciales: se validan y completan anchos entidad/municipio/localidad antes del filtro. Se impide aceptar cero candidatos por un fallo de formato. La lectura Latin1 de DENUE conserva dos caracteres de control C1 que no admite CP1252; no se eliminan bytes ni se declara resuelta la limpieza textual. El original permanece intacto.

Se ejecutaron nueve pruebas automatizadas (9 aprobadas), incluyendo límites espaciales, reproyección, totales censales, codificación, claves, cohorte temporal e IDs. Se conciliaron conteos por AGEB y totales de asignación en las ejecuciones reales. No se ha iniciado ni cargado PostgreSQL/PostGIS.

## Reproducir diagnósticos

Desde la raíz, con el entorno existente:

```powershell
.\.venv\Scripts\python.exe src/assess_geography.py --config config/cdmx.json
.\.venv\Scripts\python.exe src/assess_crime_cdmx.py
.\.venv\Scripts\python.exe -m pytest tests -q
```

Evidencia: `outputs/cdmx/phase1/quality_report.json`, `crime_quality_report.json`, asignaciones completas, `crime_category_coverage.csv`, `areas.geojson` y mapa DENUE `spatial_check.png`. El reporte de seguridad comprueba hashes de insumos y configuración antes de usar las áreas generadas. Las salidas son regenerables; los resultados resumidos aquí y los manifiestos se versionan.

## Avance posterior: cobertura y elegibilidad

Auditoría ejecutada y selección candidate-v1 documentadas en [auditoria_cdmx.md](auditoria_cdmx.md). 199,650 candidatos; 191,233 asignados. Competencia desconocida se conserva con marca por su fuerte diferencia de completitud mensual. Diez pruebas aprobadas.

## Pendientes originales (consultar auditoría para los ya atendidos)

1. Auditar las dos AGEB sin polígono y cobertura de los puntos fuera; comprobar superposiciones.
2. Revisar precisión geográfica de FGJ y acordar elegibilidad (categorías y competencia), con tabulación de exclusiones y fechas. Si la precisión no respalda AGEB, evaluar agregación a alcaldía.
3. Ejecutar perfil de variables de los 14 KPIs con fuentes CDMX y catálogo SCIAN 2018. Los perfiles de Mérida no sirven como evidencia de CDMX.
4. Actualizar diccionario y modelo dimensional con cohorte de inicio y fecha de hecho separadas. Después iniciar PostGIS y ETL del DW.

La Fase 1 permanece abierta hasta resolver/documentar estas limitaciones. La descarga y la primera integración de las cuatro fuentes ya están realizadas.
