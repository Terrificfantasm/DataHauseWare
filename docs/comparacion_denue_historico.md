# Comparación de fuentes DENUE y validación SCIAN

Fecha local: 2026-09-29. La configuración activa sigue siendo Mérida con DENUE mayo 2026. Esta comparación no altera los originales, la asignación activa ni la selección temporal del proyecto.

## Fuentes y trazabilidad

Se conservaron el catálogo oficial SCIAN 2023 en XLSX y dos ZIP históricos servidos por INEGI. URLs, tamaños, fecha de comprobación y SHA-256: `docs/historic_scian_acquisition.json`. Los originales permanecen en `data/raw/inegi_scian2023`, `inegi_denue_202004` e `inegi_denue_202011`.

El enlace al catálogo se obtuvo del propio portal del INEGI mediante su API de información del proyecto 14: `https://www.inegi.org.mx/app/api/clasificadores/interna_v2/estructura/info/proyecto/?proy=14`.

Script: `.venv\Scripts\python.exe src/compare_denue_vintages.py`. Lee los originales y produce `outputs/merida/source_comparison/comparison.json` y `scian_2023_class_check.csv`. La lectura del catálogo usa XML/ZIP de la biblioteca estándar, sin modificar el XLSX.

## SCIAN 2023: resultado de la comprobación exhaustiva de códigos observados

- Catálogo: 1,086 clases de seis dígitos en la hoja CLASE.
- DENUE Yucatán mayo 2026: 815 clases distintas entre 146,384 registros.
- Las 815 clases existen en el catálogo. Cero registros con códigos ajenos al catálogo.
- Cuarenta pares de código/descripción difieren después de normalizar Unicode, mayúsculas y espacios: afectan 4,251 registros estatales, de los cuales 1,527 están asignados a las AGEB de Mérida. El cotejo no elimina diferencias de acentos o puntuación para ocultarlas.
- Un segundo lector independiente del XLSX confirmó los 815 pares código/título y la conciliación de los 146,384 registros.

Ejemplos de diferencias: 465211 usa “discos y casetes” en DENUE frente a “grabaciones de audio y video en medios físicos” en el catálogo. En 562111, DENUE contiene una descripción amplia de manejo y remediación de residuos peligrosos, mientras el catálogo especifica recolección por el sector privado. No todas las diferencias son puramente ortográficas y no se ha verificado la actividad real de esos establecimientos.

**Decisión de modelado:** mantener `codigo_act`, `nombre_act_original`, `titulo_catalogo` y `version_scian` como atributos separados, además de una bandera de diferencia textual. Utilizar códigos para agrupaciones, pero no afirmar que pertenecer al catálogo prueba la correcta clasificación de cada negocio. No reescribir el original ni recodificar automáticamente según el texto. La incongruencia del diccionario empaquetado respecto a SCIAN 2018 queda documentada en `verificacion_scian.md`.

## Disponibilidad y comparación territorial

Mismo ámbito de comparación: los 483 polígonos urbanos 2020 seleccionados para Mérida. Se reutilizó el motor de asignación espacial con candidatos de todo Yucatán, con conciliación de estados por fila y unicidad de id.

| Archivo / edición | Registros Yucatán | Declarados en localidad Mérida | Asignados espacialmente | Declarados en Mérida pero no asignados | Asignados con otras claves |
|---|---:|---:|---:|---:|---:|
| URL abril 2020, edición pendiente de resolver | 128,720 | 52,355 | 51,993 | 468 | 106 |
| Noviembre 2020 | 130,626 | 53,778 | 53,378 | 504 | 104 |
| Mayo 2026 | 146,384 | 55,059 | 54,925 | 141 | 7 |

Las tres ejecuciones no produjeron puntos inválidos por rango ni asignaciones ambiguas. Esto no certifica precisión posicional. En ambos históricos hay 21 AGEB sin negocios asignados; en mayo 2026 son 11.

**Abril 2020:** la ruta oficial y fecha_alta hasta 2020-04 respaldan la necesidad de examinar esta descarga como candidato histórico, pero el archivo de metadatos interno dice DENUE 11_2019 y modificación 2019-11-14. Se conserva como `2020-04_URL_EDITION_UNRESOLVED`; no se declara abril 2020 como edición validada ni se utiliza como fuente activa.

**Noviembre 2020:** los metadatos internos dicen DENUE 11_2020 y modificación 2020-11-19, coherentes con la URL; mencionan resultados definitivos de Censos Económicos 2019. Es el candidato histórico con procedencia temporal más clara entre los dos evaluados. Aun así, no implica una observación simultánea de todos los establecimientos ni compatibilidad cartográfica exacta.

## Codificación de archivos históricos

Ambos históricos fallan al decodificarse estrictamente como UTF-8 y Windows-1252. Para la inspección se usó Latin-1, que conserva todos los bytes sin reemplazarlos y expone un carácter de control C1 en cada archivo. Se registra esta elección en comparison.json; no se ocultó con `errors=ignore` ni se modificaron los originales. La revisión localizó ese carácter en `raz_social` en ambos archivos, sin afectar los campos usados en esta prueba espacial. Antes de activar un histórico, implementar un adaptador documentado; no descartar la fila por un problema de texto en ese campo. Evidencia adicional: `outputs/merida/source_comparison/additional_checks.json`.

## Recomendación

Conservar mayo 2026 como configuración activa mientras se define el periodo de seguridad. Noviembre 2020 queda como alternativa real descargada, con menor distancia temporal al censo, pero más discrepancias espaciales por auditar. No cambiar automáticamente de edición por compartir el año 2020.

Si los delitos obtenidos son cercanos a 2020, evaluar noviembre 2020 con su metodología, clasificación histórica y controles de codificación. Si son recientes, valorar mantener DENUE reciente y población censal como referencia claramente etiquetada. Las diferencias de conteos entre ediciones no se interpretan como aperturas, cierres ni crecimiento: también cambian cobertura, actualización, clasificaciones y georreferenciación.

## Pendientes específicos

1. Revisar la metodología de noviembre 2020, su marco geográfico y periodo real de referencia.
2. Auditar sus 504+104 discrepancias si se elige como candidato activo, sin forzar puntos a los polígonos.
3. Validar sus códigos con su propio catálogo SCIAN histórico antes de comparar sectores entre ediciones.
4. Documentar las diferencias de descripción en 2026 y conservar original/catálogo separados.
5. Elegir temporalidad final cuando se conozca la disponibilidad de seguridad.

## Seguimiento metodológico

La metodología histórica ya fue revisada: ver [evaluación DENUE 11/2020](evaluacion_denue_202011.md). La alternativa utiliza SCIAN 2018 y cartografía septiembre 2019. La elección temporal permanece abierta.
