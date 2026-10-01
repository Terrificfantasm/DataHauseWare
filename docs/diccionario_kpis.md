> Especificación activa CDMX y evidencia de los 14 indicadores: [kpis_cdmx.md](kpis_cdmx.md).

> Actualización 2026-09-30: CDMX es el territorio activo. Este documento conserva la evaluación/propuesta previa de Mérida; consultar [Plan B y evidencia vigente](plan_b_cdmx.md) antes de reutilizar cifras o criterios.

# Diccionario de variables y KPIs — Fase 1

> Actualización 2026-09-29: se verificó la pertenencia de las 815 clases observadas al catálogo SCIAN 2023. Quedan 40 diferencias de descripción, no códigos desconocidos. Se descargó y comparó DENUE histórico; ver [comparación](comparacion_denue_historico.md). Las menciones a esa validación como pendiente en notas anteriores reflejan el estado previo.

Fecha: 2026-09-29, America/Mexico_City. Especificación para el futuro DW, no resultados analíticos finales. Seguridad permanece pendiente. Alcance actual: 483 AGEB urbanas 2020 de la localidad de Mérida, con DENUE mayo 2026.

## Fuentes de las definiciones

- Diccionario original incluido en `data/raw/inegi_censo2020/ageb_mza_urbana_31_cpv2020_csv.zip`, miembro `diccionario_de_datos/diccionario_datos_ageb_urbana_31_cpv2020.csv` dentro de la carpeta principal del ZIP.
- Diccionario original incluido en `data/raw/inegi_denue/denue_31_csv.zip`, miembro `diccionario_de_datos/denue_diccionario_de_datos.csv`, fechado 20/05/2026.
- Clases, sectores y versiones: [catálogo SCIAN del INEGI](https://www.inegi.org.mx/scian/default.html) y [estructura sectorial oficial](https://naics-scian.inegi.org.mx/naics_scian/Trip_esp.htm), consultados 2026-09-29.
- Requisitos analíticos: página 4 del enunciado original `D:/Downloads/Unit 2 - Project.pdf`, revisado al inicio del proyecto.

**Actualización 2026-09-29:** la metodología específica DENUE 05/2026 confirma SCIAN 2023 (sección 4.2, nota 14). Se adopta esa versión documentada; falta validar exhaustivamente cada clase. Ver [verificación](verificacion_scian.md).

**Observación inicial, resuelta a nivel metodológico:** el diccionario empaquetado con DENUE mayo 2026 describe `codigo_act` y `nombre_act` como SCIAN 2018, mientras que el catálogo público ofrece SCIAN 2023. No se ha probado la versión efectiva de cada código contra la metodología de esta edición. Conservar edición de fuente, código y descripción original; no etiquetarlos automáticamente como SCIAN 2023. La forma de seis dígitos no demuestra pertenencia a un catálogo.

## Convenciones generales

Una fila censal seleccionada representa un total de AGEB, no una manzana. Una fila DENUE representa un establecimiento en una edición, no una empresa ni un empleo. La unidad de cada registro de seguridad se definirá cuando llegue la fuente.

Guardar claves e identificadores como texto. Medidas censales: enteros anulables con indicador de calidad y valor original. No sustituir `*`, vacío u otro símbolo por cero. Revisar la nota metodológica antes de atribuir a cada símbolo una causa específica. Los cálculos con insumos desconocidos producen NULL y una razón; no interpolar ni reconstruir celdas reservadas.

Los cocientes con denominador nulo o cero producen NULL, no cero ni infinito. Agregaciones con faltantes deben informar cobertura y no presentar una suma parcial como total completo. Para comparar periodos y zonas deben coincidir territorio y definición, y explicitarse los años del numerador y denominador.

## Variables censales seleccionadas

| Variable | Interpretación y uso |
|---|---|
| ENTIDAD, MUN, LOC, AGEB | Clave concatenada de 13 caracteres de AGEB, conservando ceros; versionar con cartografía |
| MZA | Seleccionar 000 y AGEB distinto de 0000 para totales AGEB |
| POBTOT | Población residente total; incluye edad no especificada |
| P_12YMAS | Población de 12 años y más; base propuesta para proporción PEA |
| PEA | Población de 12 años y más que trabajó, tenía trabajo o buscó trabajo en la semana de referencia |
| PE_INAC | Población de 12 años y más no económicamente activa; control de consistencia, no sustituto del denominador |
| P_0A2, P_3A5, P_6A11, P_12A14, P_15A17 | Intervalos de edad mutuamente excluyentes |
| P_18A24, P_18YMAS, P_60YMAS | Edades de 18–24, 18+ y 60+; se superponen y no deben sumarse directamente |
| VIVTOT | Total de viviendas, incluidas distintas condiciones de ocupación |
| TVIVHAB | Viviendas particulares y colectivas habitadas |
| VIVPAR_HAB | Viviendas particulares habitadas; su universo no equivale automáticamente a VIVPARH_CV |
| VIVPARH_CV | Viviendas particulares habitadas con características captadas |
| VPH_INTER | Viviendas particulares habitadas que disponen de Internet; indicador complementario, no obligatorio |

Para grupos de edad se propone mostrar 0–2, 3–5, 6–11, 12–14, 15–17, 18–24, 25–59 y 60+. Derivar 25–59 como P_18YMAS − P_18A24 − P_60YMAS SOLO cuando los tres valores sean conocidos y el resultado no negativo. No utilizar la resta para recuperar un insumo oculto. Las proporciones respecto de POBTOT pueden sumar menos de 100% por edad no especificada; no forzar el cierre.

## Variables económicas y geográficas

| Variable | Tratamiento |
|---|---|
| id | Identificador DENUE; llave natural junto con edición |
| clee | Identificación estadística complementaria; conservar sin interpretar substrings sin documentación |
| codigo_act / nombre_act | Clase SCIAN y descripción original; conservar versión pendiente |
| per_ocu | Estrato de personal ocupado, no número exacto de empleados; no sumar etiquetas ni puntos medios como empleo observado |
| cve_ent, cve_mun, cve_loc, ageb, manzana | Geografía declarada; conservar separada de la asignación espacial |
| latitud, longitud | Punto original; mantener CRS y precisión documentados |
| fecha_alta | Incorporación al DENUE/RENEM; no fecha de apertura ni historial completo del negocio |
| CVEGEO asignada | Resultado espacial con estado de asignación y versión cartográfica |
| area_km2 | Área geodésica derivada del polígono; debe ser positiva |
| assignment_status | assigned, ambiguous, outside_selected_areas, invalid_coordinates; no perder rechazados |

## Definición de los 14 KPIs requeridos

B = establecimientos únicos de una edición asignados a la AGEB. P = POBTOT. A = área en km². C = registros de seguridad de un periodo y definición documentados.

| KPI | Fórmula / campos | Regla |
|---|---|---|
| Población total | P | Edición censal explícita |
| Densidad de población | P / A | Habitantes/km²; A > 0 |
| Proporción económicamente activa | 100 × PEA / P_12YMAS | Porcentaje sobre 12+; no sobre toda la población. Es la definición del proyecto, no afirmar equivalencia con indicadores de otras encuestas |
| Población por edades | Conteos anteriores o 100 × grupo / P | No sumar grupos que se superponen; conservar faltantes |
| Total de negocios | COUNT de id únicos por edición y AGEB | No sumar distintas ediciones como negocios diferentes |
| Densidad de negocios | B / A | Establecimientos/km² |
| Negocios por 1,000 habitantes | 1,000 × B / P | NULL si P = 0; etiquetar desfase 2026/2020 |
| Densidad de comercio minorista | B con prefijo 46 / A | Sector 46; excluir mayoristas 43 |
| Densidad de servicios | B en sectores definidos abajo / A | Definición operativa explícita |
| Actividad económica dominante | Sector con mayor conteo de negocios | Conservar todos los empates; NULL si B = 0 |
| Total de incidentes | C | Pendiente: no llamar incidentes a carpetas o llamadas sin justificar su unidad |
| Tasa de delitos por 1,000 habitantes | 1,000 × C / P | Periodo y cobertura institucional; pendiente de fuente |
| Incidentes por tipo y tiempo | COUNT agrupado por categoría y periodo | Conservar tipo original, fecha de hechos/apertura separadas y precisión temporal |
| Delitos relativos a negocios | 100 × C / B | Escala propuesta: registros por 100 establecimientos; NULL si B = 0; compatibilidad temporal pendiente |

### Clasificación económica operativa propuesta

Minoristas: prefijo 46. Para servicios se propone incluir 48–49, 51, 52, 53, 54, 55, 56, 61, 62, 71, 72 y 81 (incluye transporte y servicios financieros; no equivale a la categoría estadística de servicios privados no financieros). Excluir comercio 43/46, producción y administración pública 93 de este indicador. Es una decisión analítica del proyecto a justificar, no una nueva definición oficial.

Para actividad dominante, agrupar prefijos 31, 32 y 33 como sector 31–33; 48 y 49 como 48–49. Comparar todos los sectores, incluido 93. No declarar dominante la primera clase devuelta por un ordenamiento cuando existan empates.

## Perfil observado de insumos

Ejecutar `.venv\Scripts\python.exe src/profile_kpi_inputs.py --config config/merida.json`. Evidencia: `outputs/merida/phase1/kpi_input_profile.json`, con configuración y hashes originales.

- 483 valores numéricos en POBTOT; cinco son cero.
- PEA y P_12YMAS tienen tres `*` cada una y cinco ceros cada una. Es necesario evaluar ambas columnas antes de dividir.
- Las variables de edad seleccionadas tienen entre tres y diez `*` por variable. El grupo derivado 25–59 no es evaluable en 12 AGEB.
- La partición 0–2 + 3–5 + 6–11 + 12–14 + 15–17 + 18+ no es evaluable en 18 AGEB; en 155 queda diferencia positiva con POBTOT. El residuo suma 1,614 personas SOLO en filas evaluables; no es un total completo de edad no especificada de la ciudad.
- PEA + PE_INAC deja residuo positivo respecto a 12+ en 370 AGEB; suma 1,967 en filas evaluables. Puede reflejar condición no especificada; no imputarlo a PEA ni a población inactiva.
- No hubo PEA mayor que 12+, residuos negativos ni valores numéricos negativos/fraccionarios en los 17 campos perfilados.
- Todas las áreas son positivas. Once AGEB no tienen negocios asignados en esta edición y alcance; no significa ausencia histórica de actividad.
- Los 54,925 registros asignados tienen códigos de actividad con seis dígitos; esto no valida su correspondencia con la edición del SCIAN.
- `per_ocu` contiene siete categorías: 0–5, 6–10, 11–30, 31–50, 51–100, 101–250 y 251 o más personas.
- Hay 24 AGEB con empate en sector dominante. Once sin negocios deben tener actividad dominante no definida.

## Estado de preparación

Insumos demográficos, económicos y geográficos identificados y perfilados inicialmente. La versión SCIAN 2023 está documentada; falta validar las clases, resolver/justificar la diferencia temporal, aprobar la definición operativa de servicios al cerrar el diseño y obtener seguridad real. La Fase 1 continúa abierta. La implementación y cálculo final de indicadores corresponderán al DW PostgreSQL/PostGIS.
