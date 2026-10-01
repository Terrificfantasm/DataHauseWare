# Auditoría CDMX: cobertura y selección de seguridad

Fecha: 2026-09-30. Evidencia reproducible: `src/audit_cdmx_coverage.py`; resumen con hashes en [cdmx_coverage_audit.json](cdmx_coverage_audit.json). Ejecutar después de las dos comprobaciones de Fase 1. Diez pruebas automatizadas aprobadas.

## Dos claves censales sin polígono urbano

En el ZIP oficial Marco 2020, `09l.shp` clasifica La Ciénega (`090110110`) y Lomas de Tepemecatl (`090120135`) como **Rural**. `09ar.shp` contiene claves rurales `090111107` y `090121227`. El censo, en cambio, contiene totales de AGEB urbanas `0901101101107` y `0901201351227`.

La discrepancia urbano/rural está comprobada; su causa histórica y la equivalencia de superficies no están demostradas. No sustituimos una AGEB urbana por el polígono rural: compartir parte de una clave no prueba igualdad territorial. Se conserva la intersección de 2,431 AGEB con población comparable y la exclusión explícita de 7,108 habitantes. Recuperar ambas áreas requeriría cartografía compatible o una correspondencia geográfica validada.

## Cobertura espacial

Cero pares de AGEB urbanas con área de intersección positiva, medidos en UTM 14N (EPSG:32614). Esto no demuestra ausencia de huecos ni precisión de los puntos.

| Registros fuera de AGEB urbanas | Total | Dentro del polígono estatal | Fuera del polígono estatal |
|---|---:|---:|---:|
| DENUE | 1,720 | 1,149 | 571 |
| FGJ | 654 | 430 | 224 |

De los 654 FGJ externos a AGEB urbanas, 467 están a no más de 100 m de su unión y 576 a no más de 500 m. Para DENUE son 223 y 677, respectivamente. Son distancias diagnósticas, no permiso para mover puntos ni prueba de errores de captura. La causa puede depender de cobertura o localización y no se ha demostrado individualmente. Se conservaron los rechazos sin reasignación al polígono más cercano. Las coordenadas FGJ siguen interpretadas provisionalmente como WGS84; no se ha encontrado una precisión posicional certificada en la página consultada.

## Regla operativa de selección: candidate-v1

La [nota metodológica oficial FGJ](https://datos.cdmx.gob.mx/dataset/carpetas-de-investigacion-fgj-de-la-ciudad-de-mexico) explica que la base difiere de las estadísticas homologadas del Secretariado, que excluyen diversos tipos de registros. Nuestra selección es propia del proyecto; no reproduce dicha homologación.

Prioridad de motivos excluyentes, para que cada fila tenga una sola clasificación:

1. Categoría o competencia HECHO NO DELICTIVO: excluido.
2. Competencia INCOMPETENCIA: excluido.
3. Tipo exacto DENUNCIA DE HECHOS o DDH INCOMPETENCIA: excluido si no estaba en los anteriores.
4. Competencia FUERO COMUN: candidato identificado.
5. Competencia vacía o NA: candidato con competencia desconocida, conservando marca.
6. Otra competencia: revisión, nunca inclusión automática.

No excluir delitos por contener la palabra menores: puede referirse a víctimas. La fuente examinada no permite reconstruir automáticamente todas las reglas del Secretariado.

| Clasificación | Filas | Asignadas a AGEB | Coordenadas inválidas/ausentes | Fuera de AGEB |
|---|---:|---:|---:|---:|
| Candidatos, fuero común identificado | 70,105 | 67,527 | 2,353 | 225 |
| Candidatos, competencia desconocida | 129,545 | 123,706 | 5,423 | 416 |
| Hechos no delictivos | 3,810 | 3,044 | 754 | 12 |
| Incompetencias | 661 | 79 | 581 | 1 |

Los tipos DENUNCIA DE HECHOS y DDH INCOMPETENCIA ya quedan comprendidos en las exclusiones anteriores en esta descarga; no se descuentan dos veces. Resultado: 199,650 candidatos, de los cuales **191,233** tienen asignación espacial. Ninguna fila se borra del original.

## Por qué no exigir competencia conocida

En enero-agosto, el campo competencia contiene NA en casi todos los registros: 132,146 en total. En septiembre-diciembre hay cero NA. Sólo 24 registros de enero-agosto tienen FUERO COMUN, frente a 70,081 en septiembre-diciembre. Este cambio de completitud está observado; no se ha confirmado su causa administrativa.

Exigir FUERO COMUN produciría una selección temporal muy desigual. La regla principal conserva candidatos con competencia desconocida y los identifica por separado; el subconjunto estricto (67,527 asignados) sirve como análisis de sensibilidad, no como estimación anual comparable sin advertencias. Debe estudiarse también la cobertura por categoría y alcaldía antes de cerrar indicadores.

## Límites y continuación

Cohorte de **inicio 2020**, con fecha de hecho independiente. No se convierte en cohorte de hechos ocurridos en 2020. Se conservan filas de atributos repetidos y anomalías de fecha. Ningún resultado de este documento es aún un KPI del DW.

La selección candidate-v1 es provisional y verificable; la Fase 1 sigue abierta. Próximo paso: perfilar los insumos de los 14 KPIs de CDMX, validar catálogo SCIAN 2018 y cuantificar sensibilidad a precisión espacial antes de confirmar AGEB para análisis final. No se cargó PostGIS.

```powershell
.\.venv\Scripts\python.exe src/audit_cdmx_coverage.py
.\.venv\Scripts\python.exe -m pytest tests -q
```

Salidas: `coverage_audit.json`, `cdmx_polygon_overlaps.csv`, `business_outside_coverage.csv`, `crime_outside_coverage.csv`, `crime_eligibility.csv`, `crime_eligibility_coverage.csv` y `crime_competence_month.csv` bajo `outputs/cdmx/phase1/`.
