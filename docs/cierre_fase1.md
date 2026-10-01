# Cierre de Fase 1 — Recolección y validación CDMX

Estado: **cerrada para el alcance operativo definido aquí**, por instrucción del usuario de consolidar la fase. Fecha: 2026-09-30 (America/Mexico_City). Este cierre documenta la preparación de insumos; no certifica precisión desconocida ni equivale a aprobación del profesor, implementación del DW o entrega final.

Este documento prevalece sobre estados abiertos de las notas históricas. Las limitaciones se conservan como restricciones para Fases 2 y 3, sin convertirlas en hechos resueltos.

## Objetivo y cambio de territorio

Preparar fuentes trazables de población, actividad económica, cartografía y seguridad para un Data Warehouse geoespacial. La solicitud local de seguridad en Mérida requería un trámite incompatible con el plazo; el usuario activó CDMX. El cambio respecto del territorio del enunciado debe explicitarse en la entrega. Mérida queda como antecedente, sin mezclar sus datos con los de CDMX. El profesor no es proveedor de datos.

## Alcance operativo adoptado

- Entidad 09, localidades urbanas, **2,431 AGEB** del Marco 2020 con correspondencia en Censo 2020. Son unidades comparables dentro de las 16 alcaldías; no toda la zona metropolitana ni toda la superficie de CDMX.
- Población del universo cartografiado: **9,138,524 habitantes**. Dos AGEB censales excluidas, `0901101101107` y `0901201351227`, suman 7,108 habitantes. Marco clasifica sus localidades como rurales; no hay correspondencia geométrica validada para sustituirlas.
- DENUE noviembre 2020, SCIAN 2018. Los atributos no comparten necesariamente fecha de referencia exacta con el censo; conservar edición y metodología.
- Seguridad: filas FGJ de carpetas **iniciadas en 2020**. Fecha de hecho independiente. No afirmar que el conjunto contiene todos los hechos ocurridos en 2020 ni que cada fila sea un incidente único.
- Regla de selección adoptada para la carga inicial: `candidate-v1`, descrita abajo. Cambios posteriores exigen nueva versión y recálculo trazable.
- AGEB es la unidad de integración y exploración. Las conclusiones locales posteriores requieren evaluar sensibilidad sobre los KPIs finales.

## Inventario y conciliación

| Fuente | Original adquirido | Resultado verificable |
|---|---:|---|
| Censo 2020 | Totales de 2,433 AGEB urbanas | 2,431 con polígono; 17 de ellas con población cero |
| Marco 2020 | Capas oficiales de entidad 09 | 2,431 AGEB válidas, únicas y sin superposiciones de área positiva |
| DENUE 11/2020 | 474,328 establecimientos | 472,608 asignados; 1,720 fuera de AGEB |
| FGJ inicio 2020 | 204,121 filas | 194,356 asignadas antes de selección; 9,111 sin coordenadas válidas y 654 fuera |
| FGJ candidate-v1 | 199,650 filas seleccionadas | 191,233 asignadas; 7,776 sin coordenadas válidas y 641 fuera |

Manifiestos: [cuatro fuentes](cdmx_acquisition.json), [catálogo SCIAN](cdmx_scian2018_acquisition.json). Registran URL y SHA-256; el manifiesto principal incluye fecha de verificación. Exportación FGJ obtenida del DataStore oficial debido al certificado vencido del enlace de archivo, sin desactivar validación TLS. Conteo conciliado contra la API.

No se interpreta un punto fuera de AGEB urbanas como fuera de CDMX: de los 654 FGJ externos antes de selección, 430 están dentro del polígono estatal. No se movieron puntos hacia polígonos cercanos.

## Contrato de seguridad candidate-v1

Prioridad de clasificación: excluir categoría o competencia HECHO NO DELICTIVO; después competencia INCOMPETENCIA; después tipos exactos DENUNCIA DE HECHOS o DDH INCOMPETENCIA. Conservar FUERO COMUN y competencia NA/vacía, marcando esta última como desconocida. Otras competencias requieren revisión. No filtrar por la palabra menores, que puede referirse a víctimas.

Exclusiones efectivas: 3,810 hechos no delictivos y 661 incompetencias, sin doble descuento. Entre candidatos, 70,105 tienen fuero común identificado y 129,545 competencia desconocida. Exigir competencia conocida descartaría casi enero-agosto; el patrón de incompletitud está documentado. La selección no equivale a la homologación SESNSP.

Identificador técnico: hash de la descarga + `_id` del DataStore. Mantener las 679 filas con atributos públicos repetidos: no prueban duplicación sustantiva de carpetas. Mantener fechas y anomalías por separado: 43 fechas de hecho no interpretables y una posterior al inicio en el conjunto original. Los candidatos con fecha de hecho problemática siguen sirviendo para la cohorte de inicio; no imputar fechas para análisis por ocurrencia.

## Criterios de calidad y preparación de indicadores

Los originales se conservan sin cambios. Claves INEGI como texto, ceros iniciales normalizados sólo en derivados. Reservados censales como NULL con valor original y estado, nunca cero. Divisiones por denominador cero/desconocido producen NULL. Doce AGEB sin negocios; 77 empates sectoriales se conservan. Los 937 códigos SCIAN observados pertenecen al catálogo 2018; la comparación textual de descripciones queda pendiente sin impedir identificación por código/version.

Los [14 KPIs](kpis_cdmx.md) tienen campos, fórmulas y reglas documentados. Se calcularán desde PostgreSQL/PostGIS; los conteos y perfiles de esta fase son diagnósticos, no el producto analítico final.

## Precisión y simulaciones

Coordenadas FGJ interpretadas provisionalmente como WGS84; datum y precisión posicional no certificados por la documentación revisada. Se ejecutaron 80 simulaciones: dos fuentes, cuatro radios máximos (10/25/50/100 m), diez semillas. Desplazamientos independientes uniformes en disco; no representan errores observados ni intervalos de confianza.

En seguridad, con radio máximo 50 m cambió la asignación del 17.89% de los puntos inicialmente asignados en promedio. Unas 195 AGEB por repetición presentaron cambios de conteo >=20% entre las de base >=20. La estabilidad del orden global no asegura estabilidad local. Estos escenarios no validan tasas, relaciones entre variables, Moran o LISA; deben evaluarse al construir los análisis definitivos.

## Evidencia de cierre

| Requisito | Evidencia versionada |
|---|---|
| Fuentes, procedencia y ediciones | cdmx_acquisition.json; plan_b_cdmx.md; evaluacion_denue_202011.md |
| Claves, CRS, integridad y enlace censal | cdmx_quality_report.json; auditoria_cdmx.md |
| Conversión y asignación punto-polígono de seguridad real | src/assess_crime_cdmx.py; cdmx_crime_quality_report.json |
| Cobertura y selección | cdmx_coverage_audit.json; auditoria_cdmx.md |
| Variables y definiciones de 14 KPIs | kpis_cdmx.md; cdmx_kpi_input_profile.json |
| Catálogo económico | cdmx_scian2018_check.json |
| Sensibilidad | simulaciones_cdmx.md; cdmx_simulation_report.json |
| Verificación automatizada | 14 pruebas aprobadas en tests/ |
| Preparación técnica siguiente fase | Docker activo, consulta PostGIS verificada; docker_runtime_check.json |

La carpeta outputs contiene detalle regenerable y no se versiona. Los JSON de evidencia son fotografías de las ejecuciones descritas; los campos `phase1_complete: false` en diagnósticos previos no se reescriben retroactivamente: expresan el estado de cada ejecución. El estado de cierre y decisiones vigentes está en este documento.

## Reproducción desde un clon

Python 3.12 y dependencias de requirements.txt. Crear entorno, recuperar insumos con `src/restore_cdmx_sources.py` y ejecutar en orden:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe src/restore_cdmx_sources.py
.\.venv\Scripts\python.exe src/assess_geography.py --config config/cdmx.json
.\.venv\Scripts\python.exe src/assess_crime_cdmx.py
.\.venv\Scripts\python.exe src/audit_cdmx_coverage.py
.\.venv\Scripts\python.exe src/profile_kpi_inputs.py --config config/cdmx.json
.\.venv\Scripts\python.exe src/profile_spatial_sensitivity.py
.\.venv\Scripts\python.exe src/simulate_spatial_cdmx.py
.\.venv\Scripts\python.exe src/report_simulations.py
.\.venv\Scripts\python.exe -m pytest tests -q
```

La restauración verifica hashes y rechaza ediciones cambiadas: una URL mutable no garantiza recuperar la misma descarga en el futuro. Conservar copia de los originales fuera de Git. La comprobación opcional SCIAN por PDF requiere pypdf; ejecución y evidencia en kpis_cdmx.md. Docker se configura siguiendo docker_operacion.md; no subir `.env`.

## Paso a Fase 2

1. Definir y aplicar migraciones del modelo dimensional, con hechos de población, establecimientos por edición y registros FGJ separados.
2. Cargar staging y DW con trazabilidad, rechazos y validaciones de conteos; conservar las dos fechas y las reglas versionadas.
3. Construir vistas de 14 KPIs desde el DW y repetir sensibilidad pertinente antes de análisis inferencial.
4. Mantener commits reales por integrante y documentar contribuciones. Este cierre no reemplaza ese requisito de evaluación.

PostGIS está operativo; no hay hechos/dimensiones ni datos cargados. No se fusiona esta rama con main como parte del cierre.
