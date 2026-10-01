# Auditoría de discrepancias geográficas

Fecha local: 2026-09-29 (America/Mexico_City). Ejecución UTC: 2026-09-30. Alcance: localidad 310500001 y 483 AGEB urbanas del Marco 2020. Fuente económica: DENUE mayo 2026.

## Método y reproducibilidad

Ejecutar desde la raíz: `.venv\Scripts\python.exe src/audit_discrepancies.py --config config/merida.json`.

El script coteja configuración y hashes originales contra el diagnóstico anterior; verifica unicidad y correspondencia de identificadores. Reúne los 148 casos sin cambiar sus coordenadas ni su asignación previa. Calcula distancias aproximadas en UTM 16N (EPSG:32616), examina otras AGEB urbanas de Yucatán 2020 y audita las intersecciones de los polígonos seleccionados. La zona UTM se estima según el territorio configurado.

Se conserva el detalle en `outputs/merida/phase1/discrepancy_audit.csv` y el resumen en `discrepancy_audit.json`. `polygon_overlaps.csv` registra superposiciones con área positiva; solo contiene encabezados porque no se encontraron. La AGEB más cercana es un diagnóstico, nunca una reasignación.

## 141 registros declarados en Mérida y fuera del área seleccionada

| Distancia al área | Registros |
|---|---:|
| Hasta 1 m | 2 |
| Más de 1 a 10 m | 18 |
| Más de 10 a 50 m | 40 |
| Más de 50 a 100 m | 29 |
| Más de 100 a 500 m | 52 |
| Más de 500 m | 0 |

Mediana: 59.12 m; máxima: 492.09 m. Los 141 quedan a menos de 500 m, y 89 a 100 m o menos.

- Seis caen dentro de otra AGEB urbana de Yucatán del Marco 2020.
- En 64, la clave AGEB declarada por DENUE no aparece en la capa de AGEB urbanas de Yucatán 2020.
- Los demás puntos sin AGEB urbana no están necesariamente fuera de un municipio o localidad: esta capa no representa todo el territorio rural.

**Interpretación:** hay evidencia de proximidad a los límites y de incompatibilidad entre algunas claves y la cartografía usada. No se ha demostrado que sean negocios nuevos, expansión urbana, errores de coordenadas o cambios cartográficos. No existe justificación para corregir automáticamente esos registros ni asignarlos por proximidad.

## Siete registros de otras localidades que caen dentro

| Localidad declarada | Registros | Distancia aproximada al borde del área seleccionada |
|---|---:|---|
| Kanasín | 1 | 0.44 m |
| Umán | 2 | 7.16 y 10.54 m |
| La Roca | 3 | 317.08 a 317.71 m |
| Progreso | 1 | 325.95 m |

Kanasín y Umán son casos especialmente sensibles a precisión y límites. La Roca y Progreso requieren revisar la procedencia y ubicación antes de interpretar los registros como negocios locales; estar dentro del polígono no prueba que las coordenadas sean correctas.

## Polígonos y conciliaciones

- Cero pares con intersección de superficie positiva entre las 483 AGEB seleccionadas. Los bordes compartidos sin superficie no son solapamientos.
- Esto no demuestra ausencia de huecos ni cobertura completa de la ciudad en 2026.
- 148 identificadores únicos en la auditoría, conciliados con 141+7 casos anteriores.
- Los siete casos interiores tienen distancia cero al área; sus distancias al borde son mayores que cero.
- Los originales conservan los hashes del diagnóstico inicial.

## Decisión operativa provisional

Mantener el alcance cartográfico 2020 y conservar la asignación espacial ya calculada: 54,925 registros dentro, incluyendo los siete con diferencias de localidad, explícitamente señalados. Los 141 exteriores permanecen sin asignación al área de estudio. No borrar registros ni corregir coordenadas o claves.

Para sensibilidad futura, comparar el conjunto espacial completo (54,925) con el conjunto interior que también coincide en localidad declarada (54,918). Este segundo conjunto no es automáticamente más correcto. No presentar ninguno como un KPI final mientras sigan pendientes la decisión temporal y la validación de fuentes.

La auditoría caracteriza los casos; la causa exacta queda pendiente de contrastar con otra edición cartográfica o evidencia de ubicación. No se necesitan correcciones especulativas para avanzar al diccionario de variables.
