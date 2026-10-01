> Actualización 2026-09-30: CDMX es el territorio activo. Este documento conserva la evaluación/propuesta previa de Mérida; consultar [Plan B y evidencia vigente](plan_b_cdmx.md) antes de reutilizar cifras o criterios.

# Decisión geográfica de la Fase 1

Fecha: 2026-09-29. Estado: decisión operativa sustentada para demografía, economía y geografía; su adecuación a seguridad queda condicionada a la fuente obtenida.

## Decisión y alcance

Utilizar las 483 AGEB urbanas de la localidad geoestadística de Mérida (entidad 31, municipio 050, localidad 0001), según el Marco Geoestadístico del Censo 2020. El universo son estos polígonos, no todo el municipio ni la zona metropolitana ni una delimitación de la ciudad actual en 2026.

La clave territorial es la concatenación ENTIDAD (2), MUN (3), LOC (4) y AGEB (4), almacenada como texto de 13 caracteres. La versión cartográfica forma parte de la identidad de la geografía: la misma clave no garantiza límites idénticos en otra edición. No equiparar AGEB y colonia.

## Alternativas evaluadas

| Unidad | Integración y utilidad | Limitaciones para este proyecto | Decisión |
|---|---|---|---|
| Municipio | Hay claves en las fuentes; útil para contexto y control | Mérida sería una sola observación, insuficiente para comparar zonas internas y evaluar asociaciones espaciales dentro de ella | Usar como contexto, no como unidad principal |
| Colonia | Facilita comunicar resultados locales; podría coincidir con reportes de seguridad | No se ha validado un catálogo de límites y equivalencias con censo. No puede trasladarse población desde AGEB sin comprobar correspondencia | No seleccionada con la evidencia actual |
| Manzana | Mayor detalle y disponibilidad censal/cartográfica | Exige evaluar reserva estadística y estabilidad de conteos pequeños. Los puntos aproximados y frentes de calle pueden complicar asignación; no se midió aún su tasa de error | Mantener como opción de detalle, no como unidad principal |
| AGEB urbana | Totales censales con claves, polígonos compatibles y múltiples zonas internas; integración espacial con negocios comprobada | Persisten faltantes, precisión de puntos, denominadores cero y diferencias temporales. No garantiza suficiente cantidad de delitos por zona | Seleccionada de forma operativa |

La selección no se basa en que exista más información de cualquier tipo, sino en la posibilidad ya demostrada de integrar las variables necesarias sobre un mismo conjunto de zonas. No se han asignado puntuaciones arbitrarias a las alternativas.

## Evidencia local comprobada

- 483 claves únicas del censo coinciden exactamente con 483 polígonos. Cero geometrías inválidas, vacías o nulas.
- Suma de POBTOT por AGEB: 921,771, conciliada con el total de la localidad.
- Cero pares de polígonos con intersección de superficie positiva. No se demostró ausencia de huecos ni cobertura del crecimiento urbano posterior.
- DENUE mayo 2026: 54,925 registros asignados, sin asignaciones múltiples. Hay 141 puntos declarados locales fuera y siete de otras claves dentro, caracterizados pero sin causa individual demostrada.
- Cinco AGEB con población cero y once sin negocios asignados. Se conservan en el universo geográfico; se excluyen únicamente de un cálculo cuyo denominador sea inválido, registrando la razón.
- Algunas variables censales contienen símbolos no numéricos. No tratarlos como cero ni ocultar la cobertura de los cálculos.

Evidencia: [validación geográfica](validacion_geografica.md), [auditoría](auditoria_discrepancias.md), [diccionario y perfil de insumos](diccionario_kpis.md). Resultados regenerables en outputs/merida/phase1/.

## Regla de integración

1. Censo: seleccionar totales AGEB y enlazar por clave completa y versión. No sumar manzanas junto con sus totales.
2. Puntos: conservar coordenadas originales, fuente, edición y CRS. Transformar al CRS de polígonos antes de la unión espacial.
3. Asignación única mediante intersección. Si el punto toca varias AGEB, marcar ambiguo; no duplicarlo ni elegir una al azar. Si no cae en ninguna, mantenerlo fuera del área seleccionada.
4. Conservar geografía declarada y asignada por separado. No asumir que una diferencia demuestra un error en uno de los campos.
5. Calcular superficies con un método geodésico adecuado; no usar grados cuadrados como km².
6. No asignar por cercanía, inventar coordenadas ni convertir totales municipales en observaciones puntuales.

## Condiciones para integrar seguridad

- Si hay coordenadas del lugar de los hechos y precisión compatible: probar el mismo motor, medir cobertura, errores y ambigüedad, y evaluar cantidad de observaciones por AGEB y periodo.
- Si solo hay AGEB: una unión por clave puede servir, pero no satisface la prueba específica de conversión punto-polígono de delitos del enunciado.
- Si solo hay direcciones: primero evaluar geocodificación, calidad y sesgos; no confundir resultados aproximados con ubicaciones precisas.
- Si solo hay colonias: revisar delimitación y posibilidad de integración, sin repartir casos entre AGEB ni usar el centroide como lugar observado.
- Si solo hay totales municipales: no es suficiente para comparar seguridad entre zonas internas de Mérida. Mantener como contexto o evaluar otra ciudad con las cuatro capas.

Si los incidentes son muy escasos o la ubicación demasiado imprecisa, reconsiderar el periodo, agrupaciones justificadas de zonas o el territorio. No hay un umbral de suficiencia inventado antes de conocer la distribución real. Cualquier agrupación deberá conservar trazabilidad y comprobarse mediante análisis de sensibilidad.

## Consecuencias para análisis y warehouse

Se propone una dimensión geográfica versionada, compartida por hechos separados de población, establecimientos y seguridad. La edición de publicación y los periodos de referencia se guardan aparte. No mezclar observaciones de distintas fechas como si fueran simultáneas.

Los resultados por AGEB pueden cambiar al usar otra escala o delimitación; no atribuir patrones de áreas a personas individuales. Las asociaciones espaciales no prueban causalidad. En la fase analítica habrá que definir vecindad, revisar polígonos sin vecinos y evaluar sensibilidad de Moran/LISA a esa elección. No elegir una regla de vecindad definitiva antes de comprobarla.

La elección geográfica está documentada, pero la Fase 1 sigue abierta: falta integrar delitos reales y cerrar la compatibilidad temporal.
