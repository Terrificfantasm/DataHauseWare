# Evaluación de DENUE noviembre 2020

Revisión: 2026-09-29. Fuente preservada: data/raw/inegi_denue_202011/metodologia_112020.pdf. URL y hash en docs/metodologia_denue_202011_acquisition.json. Identificación por portada y contenido: DENUE Interactivo 11/2020; el título indexado por el buscador menciona abril y no se tomó como autoridad.

## Hallazgos de metodología

- Sección 4.2 (página impresa 7): SCIAN 2018.
- Sección 4.3 (página 8): datos de identificación referidos a 2019 para incorporaciones de 2010 a abril 2020, y a 2020 para incorporaciones de noviembre 2020.
- Nota 15: el estrato de personal se basa en personal ocupado de 2018. No interpretarlo como empleo medido en noviembre 2020.
- Sección 4.5 (página 9): Marco Geoestadístico de septiembre de 2019. Advierte posibles ausencias de manzanas de crecimiento posterior.
- Coordenadas aproximadas; hay reglas de ubicación en frentes de calle, inmuebles comerciales y centroides de localidades rurales.

## Implicaciones para el proyecto

La publicación en 2020 no garantiza que cada variable describa ese año. Esta alternativa es temporalmente más cercana al censo que la descarga de 2026, pero requiere conservar versión de clasificación, fecha de edición y referencias temporales por separado.

La diferencia cartográfica aporta una explicación posible de las discrepancias con nuestros polígonos 2020, no una causa demostrada para cada punto. Se mantienen los resultados comparativos ya medidos: 53,378 registros interiores; 504 declarados locales fuera y 104 con otras claves dentro. No se repitió la integración ni se cambiaron asignaciones.

## Decisión provisional

Conservar esta edición como candidata histórica. No cambiar aún la configuración activa ni afirmar que representa una fotografía de noviembre 2020. La elección final depende del periodo y cobertura de seguridad. No hace falta detener la arquitectura por esa espera: el DW debe separar publicación, referencia temporal y versión cartográfica.

## Siguiente trabajo independiente

Formalizar la elección de AGEB frente a manzana, colonia y municipio con la evidencia disponible. Si se activa la alternativa 2020: validar todas sus clases contra SCIAN 2018, documentar diferencias de cartografía y adaptar la codificación preservando originales. No unir etiquetas/clases de 2018 y 2023 sin correspondencias verificadas.
