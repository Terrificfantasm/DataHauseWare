# Validación geográfica ejecutada: Mérida

Ejecución: 2026-09-29. Configuración: config/merida.json. Versiones Python fijadas en requirements.txt.

## Resultados medidos

- 483 totales censales por AGEB y 483 polígonos: correspondencia exacta de claves, sin duplicados.
- Geometrías: cero inválidas, vacías o nulas. Falta auditoría de superposiciones entre polígonos; validez individual no equivale a validez topológica del conjunto.
- Población AGEB: 921,771; coincide con el total de la localidad. POBTOT sin faltantes en esos totales.
- DENUE: 146,384 candidatos estatales; cero filas con id duplicado.
- Asignación espacial única: 54,925 registros; conteo conciliado con la suma por AGEB.
- Fuera de las áreas seleccionadas: 91,459 (principalmente fuera de la localidad). No son todos errores de coordenadas.
- Coordenadas inválidas según rango numérico: cero. Este control no demuestra precisión posicional.
- Asignaciones ambiguas: cero.
- Registros con claves declaradas de la localidad de Mérida: 55,059. De ellos, 54,918 dentro y 141 fuera del área censal 2020.
- Siete registros con otras claves de localidad están físicamente dentro de las áreas seleccionadas.

No se han explicado todavía las discrepancias: pueden relacionarse con versiones territoriales, precisión o codificación. No se corrigen ni se fuerzan ubicaciones.

## Comprobaciones del software

Tres pruebas automatizadas aprobadas: bordes compartidos/externos y coordenadas inválidas; reproyección; rechazo de claves geográficas duplicadas. Docker Compose aceptó la configuración con el archivo de ejemplo. Docker no tiene servicio activo, por lo que el arranque del contenedor y los scripts SQL NO fueron probados en una base real.

## Evidencia regenerable

`outputs/merida/phase1/quality_report.json` contiene hashes, configuración, CRS y conteos. `business_assignment.csv`, `area_diagnostics.csv`, `areas.geojson` y `spatial_check.png` permiten inspeccionar resultados. No se ha implementado ni cargado el modelo dimensional; son diagnósticos de Fase 1, no consultas analíticas finales.

## Pendientes

Seguridad real con ubicación; revisión de 141+7 discrepancias; decisión temporal (2020/2026); perfil completo de variables para KPIs y denominadores; validación topológica y criterios finales de elección de unidad. La prueba con negocios demuestra funcionamiento del motor, pero no reemplaza la prueba requerida con delitos.
