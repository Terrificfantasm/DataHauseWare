> Continuación ejecutada: [80 simulaciones espaciales](simulaciones_cdmx.md). Consultar sus resultados para la decisión de escala; los radios de distancia de este documento son el diagnóstico previo.

# Preparación de los 14 KPIs de CDMX y sensibilidad espacial

Fecha: 2026-09-30. Alcance: 2,431 AGEB urbanas con correspondencia censal. Ediciones: Censo/Marco 2020, DENUE noviembre 2020 (SCIAN 2018), FGJ inicio 2020 con selección candidate-v1. Sustituye la especificación territorial de Mérida para el trabajo activo; conserva sus convenciones de faltantes y denominadores. Son insumos y definiciones para el DW, no resultados finales de indicadores.

## Evidencia ejecutada

- [Perfil completo](cdmx_kpi_input_profile.json): 17 campos censales, denominadores, sectores y estratos.
- [SCIAN 2018](cdmx_scian2018_check.json): las 937 clases observadas en todo DENUE CDMX pertenecen a los 1,084 códigos extraídos de la [estructura oficial](https://www.inegi.org.mx/contenidos/app/scian/estructura2018.pdf). Validación de pertenencia, no comparación de descripciones. Original y hash en cdmx_scian2018_acquisition.json.
- [Sensibilidad](cdmx_spatial_sensitivity.json): escenarios de distancia a límites, con hashes de fuentes.
- 12 pruebas automatizadas aprobadas. Originales y coordenadas intactos; no hubo carga a PostGIS.

## Contrato operativo de los indicadores

P = población censal de AGEB; A = área geodésica en km²; B = establecimientos DENUE de una edición, con ID único y asignación espacial única; C = filas FGJ candidatas con asignación única y fecha de inicio en 2020. C conserva competencia desconocida identificada. No representa delitos reales totales ni una cohorte completa de hechos ocurridos en 2020.

| # | Indicador | Definición para el DW | Preparación y condición |
|---|---|---|---|
| 1 | Población total | P | Insumo completo en 2,431 AGEB |
| 2 | Densidad poblacional | P / A | Todas las superficies son positivas |
| 3 | Proporción PEA | 100 × PEA / P_12YMAS | Ambos insumos deben ser conocidos; denominador > 0 |
| 4 | Población por edades | Conteos y proporciones sobre P | Preservar reservados; 25–59 = 18+ − 18–24 − 60+ sólo con tres valores conocidos |
| 5 | Total de negocios | COUNT de ID DENUE por edición y AGEB | 472,608 asignados; 12 AGEB sin registros |
| 6 | Densidad de negocios | B / A | Insumos disponibles; sensibilidad espacial documentada |
| 7 | Negocios por 1,000 habitantes | 1,000 × B / P | NULL en 17 AGEB con P=0; referencias de 2020 no son la misma fecha |
| 8 | Densidad minorista | B del sector 46 / A | 202,829 registros asignados del sector 46; códigos validados |
| 9 | Densidad de servicios | B de sectores operativos / A | Usar definición de servicios indicada abajo |
| 10 | Actividad dominante | Sector(es) con mayor B | Conservar 77 empates; NULL en 12 AGEB sin B |
| 11 | Total de registros de seguridad | C | 191,233 candidatos asignados; selección provisional, no llamarlos incidentes únicos |
| 12 | Registros de seguridad por 1,000 habitantes | 1,000 × C / P | NULL si P=0; cobertura institucional y espacial incompleta |
| 13 | Registros por tipo y tiempo | COUNT por categoría y mes de inicio | Conservar fecha de hecho aparte; no mezclar ambos calendarios |
| 14 | Seguridad relativa a negocios | 100 × C / B | NULL si B=0; no interpreta que los hechos hayan ocurrido contra esos negocios |

Servicios: sectores 48–49, 51, 52, 53, 54, 55, 56, 61, 62, 71, 72 y 81. Definición operativa del proyecto, no categoría oficial de servicios privados no financieros. Excluye 43/46, producción y administración pública 93. Para dominancia, agrupar manufacturas 31–33 y transporte 48–49 y comparar todos los sectores, incluido 93.

Los cuatro indicadores de seguridad tienen insumos disponibles pero interpretación condicionada a selección y precisión. El nombre del requisito académico se conserva como referencia; el título publicado debe describir registros de carpetas iniciadas, no prometer conteos de incidentes únicos. Los resultados finales se calcularán desde el DW.

## Faltantes y denominadores

POBTOT es numérico en todas las AGEB y cero en 17. PEA y población 12+ tienen diez valores `*` cada una; población 12+ tiene 17 ceros. No convertir `*` en cero. Toda división necesita comprobar ambos insumos y un denominador positivo, sin asumir que los faltantes de diferentes columnas coinciden.

La partición de edades no es evaluable en 44 AGEB. El grupo derivado 25–59 no puede calcularse en 20. En 454 AGEB evaluables la suma de edades deja un residuo positivo; no forzar que las proporciones sumen 100%. No se encontraron residuos negativos ni PEA mayor que población 12+. Estratos de personal ocupado son categorías, no empleo exacto.

## Sensibilidad espacial: qué se midió

Se calculó, en UTM 14N (EPSG:32614), la distancia de cada punto asignado al límite de **su propio polígono**, incluidos límites internos. No se usó sólo el borde exterior de la ciudad. Radios ilustrativos acumulados: 10, 25, 50 y 100 metros. No son errores medidos ni intervalos de confianza.

| Radio | Negocios cerca del límite (de 472,608) | Seguridad candidata cerca del límite (de 191,233) |
|---|---:|---:|
| 10 m | 117,463 (24.85%) | 49,705 (25.99%) |
| 25 m | 200,012 (42.32%) | 77,563 (40.56%) |
| 50 m | 260,997 (55.22%) | 103,471 (54.11%) |
| 100 m | 358,683 (75.89%) | 145,923 (76.31%) |

Estar dentro del radio significa que un desplazamiento podría cruzar el límite; no implica que efectivamente lo cruce, ni que entre en otra AGEB (podría salir de la cobertura). Estar más lejos protege la asignación frente a desplazamientos de hasta ese radio, bajo las hipótesis de CRS y geometría usadas. La precisión real de FGJ sigue sin estar acreditada; la concentración cerca de límites puede reflejar calles o localización aproximada y no demuestra una causa por sí sola.

No se movieron puntos, imputaron AGEB ni descartaron registros cercanos al borde. El análisis es una señal de fragilidad de la escala, no un nuevo filtro de elegibilidad.

## Decisión de uso y siguiente paso

Mantener AGEB para integración y análisis exploratorio, con esta limitación visible. No dar aún por robustos rankings o agrupamientos locales de seguridad. Antes de cerrar la escala analítica, comparar sensibilidad de conteos bajo perturbaciones controladas o una agregación coherente mayor; una agregación por alcaldía debe conservar el mismo universo y denominadores, sin mezclar población municipal completa con cobertura urbana parcial. Dieciséis alcaldías, por sí solas, también ofrecen pocas unidades para análisis espacial inferencial.

Los 14 indicadores ya tienen contrato e insumos identificados. Permanecen pendientes robustez espacial, revisión textual de descripciones SCIAN y cierre del modelo dimensional/ETL. La Fase 1 no se declara completa por la sola existencia de datos.

## Reproducibilidad

```powershell
.\.venv\Scripts\python.exe src/profile_kpi_inputs.py --config config/cdmx.json
.\.venv\Scripts\python.exe src/profile_spatial_sensitivity.py
.\.venv\Scripts\python.exe -m pytest tests -q
```

`src/check_scian2018_pdf.py` requiere pypdf; se ejecutó con el Python del runtime incluido de Codex. No se agregó esa dependencia al entorno ETL. Sus rutas se resuelven desde el propio script. Las distancias por registro y resúmenes por AGEB están en `outputs/cdmx/phase1/`; las copias JSON de evidencia en docs se actualizan después de una nueva ejecución revisada.
