# Verificación SCIAN — 2026-09-29

> Actualización 2026-09-29: se verificó la pertenencia de las 815 clases observadas al catálogo SCIAN 2023. Quedan 40 diferencias de descripción, no códigos desconocidos. Se descargó y comparó DENUE histórico; ver [comparación](comparacion_denue_historico.md). Las menciones a esa validación como pendiente en notas anteriores reflejan el estado previo.

La metodología oficial DENUE 05/2026, sección 4.2, nota 14 (página impresa 7, página 10 del PDF), declara SCIAN 2023 para la edición 05/2026. La referencia a SCIAN 2018 en el diccionario CSV empaquetado contradice esa declaración. Se adopta SCIAN 2023 como versión documentada; el origen editorial exacto de la discrepancia no está confirmado.

La sección 4.5 declara Marco Geoestadístico 2024 y ubicaciones aproximadas, con reglas particulares para frentes de calle, centros comerciales y localidades rurales. Esto aporta contexto a las diferencias con nuestra cartografía 2020, sin resolver cada registro.

La sección 4.3 distingue año de referencia de edición de publicación. Por tanto, mayo de 2026 no debe interpretarse como observación simultánea de todos los negocios.

Fuente preservada: `data/raw/inegi_denue/metodologia_052026.pdf`; URL y SHA-256 en `docs/metodologia_denue_acquisition.json`.

## Evidencia local complementaria

La inspección del ZIP de Yucatán encontró códigos y descripciones consistentes con categorías SCIAN 2023, por ejemplo 519212 (101 registros, bibliotecas públicas), 513210 (2, edición de software) y 516210 (6, streaming y otros proveedores de contenido). Los conteos son estatales y no KPIs de Mérida. Esta inspección no sustituye una validación exhaustiva de todas las clases contra el catálogo.

## Decisión

Conservar originales y registrar la discrepancia documental. No recodificar clases de 2023 mediante un catálogo 2018. Pendiente: validar todas las clases contra el catálogo oficial y buscar DENUE histórico para decidir coherencia temporal. El perfil generado previamente conserva su advertencia histórica; esta nota documenta su resolución a nivel de versión metodológica.
