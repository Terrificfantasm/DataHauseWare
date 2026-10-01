# Bitácora de DataHauseWare

Última actualización: 2026-09-30 (America/Mexico_City).

Este es el punto de entrada para retomar el proyecto entre sesiones. Mantener el estado actual arriba y agregar una entrada al historial al terminar cada sesión de trabajo. Registrar solo acciones realizadas y distinguirlas de propuestas. No guardar contraseñas ni datos personales.

## Retomar en dos minutos

- **Carpeta:** `C:\Users\IGNITER\Downloads\DataHauseWare`.
- **Territorio activo:** CDMX; el usuario activó Plan B porque el trámite de seguridad de Mérida rebasa el plazo. El profesor no es proveedor de datos.
- **Fase:** 1 cerrada para alcance operativo CDMX; documento rector docs/cierre_fase1.md. Siguiente fase: modelo y ETL.
- **Configuración:** `config/cdmx.json`; usar siempre `--config config/cdmx.json` para el evaluador geográfico (su valor por defecto conserva Mérida).
- **Resultados:** 2,431 polígonos válidos; 472,608 registros DENUE y 194,356 registros FGJ asignados. Seguridad: 9,111 coordenadas inválidas/ausentes y 654 filas fuera.
- **Límites:** dos AGEB censales sin polígono (7,108 habitantes); FGJ es cohorte de inicio 2020, no todos los hechos de 2020. Precisión, elegibilidad y cobertura pendientes. No interpretar todos los registros como delitos.
- **Siguiente acción:** cerrar modelo dimensional y preparar carga PostGIS/ETL. Las 80 simulaciones ya terminaron: docs/simulaciones_cdmx.md. Repetir sensibilidad sobre KPIs finales antes de interpretar focos locales.
- **Guía vigente y contrato:** [Plan B](docs/plan_b_cdmx.md). [Manifiesto](docs/cdmx_acquisition.json).
- **Validación:** 14 pruebas aprobadas; cero superposiciones de AGEB. Selección operativa candidate-v1: 199,650 candidatos FGJ, 191,233 asignados; competencia desconocida conservada y marcada.
- **PostGIS:** contenedor activo y healthy; PostgreSQL 17.5 / PostGIS 3.5.2, localhost:5433. Esquemas staging/dw/analytics creados; DW todavía sin tablas de hechos ni carga. Publicación de Fase 1 en rama codex/fase-1-recoleccion-validacion-cdmx; mantener contribuciones reales, sin atribuciones ficticias.
- **No rehacer:** originales y resultados de Mérida se conservan; originales CDMX ya descargados. No mezclar territorios ni inventar coordenadas. Los documentos de Mérida son antecedentes, no evidencia activa de CDMX.

## Decisiones vigentes

1. Alcance: AGEB urbanas de entidad 09; no toda la zona metropolitana ni zonas rurales. Dos claves sin geometría quedan explícitamente excluidas del diagnóstico espacial hasta revisión.
2. Periodo operativo: Censo/Marco 2020, DENUE 11/2020, carpetas iniciadas 2020; referencias temporales distintas documentadas.
3. Conservar originales, URLs, hashes, fechas y rechazos. Ausencia de datos no equivale a cero.
4. `_id` de FGJ identifica una fila del DataStore; no garantiza unicidad de carpeta. Conservar filas repetidas por atributos hasta aclaración.
5. Un repositorio para todas las fases y contribuciones reales. Los KPIs finales se calcularán desde el DW.

## Dónde encontrar cada cosa

- [README](README.md): instalación y comandos.
- [Arquitectura](docs/arquitectura.md): propuesta de granularidad, adaptación de seguridad y validaciones.
- [Configuración activa CDMX](config/cdmx.json) y [Mérida histórica](config/merida.json).
- `data/raw/`: originales. No modificarlos ni volver a descargarlos sin motivo.
- [Recolector inicial](src/download_inegi.py): todavía específico de Yucatán.
- [Evaluación geográfica](src/assess_geography.py) y [motor espacial](src/spatial.py).
- `outputs/merida/phase1/`: diagnóstico JSON, asignaciones, resumen por AGEB, GeoJSON y mapa.
- [Mapa de comprobación](outputs/merida/phase1/spatial_check.png).
- Enunciado original, fuera del repositorio: `D:\Downloads\Unit 2 - Project.pdf`.

Datos, entorno y salidas regenerables están ignorados por Git; la bitácora y los manifiestos sí deben versionarse. La carpeta temporal de preparación en el otro espacio de trabajo no es la fuente del proyecto: editar siempre DataHauseWare.

## Rutina de continuidad

Al comenzar una sesión: leer esta bitácora, revisar el estado real de los archivos y de Git, incorporar novedades del usuario y tomar el primer pendiente viable. Las instrucciones del usuario más recientes prevalecen sobre esta nota.

Al terminar: actualizar estado y siguiente acción; agregar una entrada fechada con cambios, comprobaciones, decisiones y pendientes. Conservar entradas anteriores; corregir datos erróneos con una nota explícita. No repetir pruebas ya aprobadas salvo cambios relevantes o dudas nuevas. No marcar completa la Fase 1 sin la evidencia que falta.

## Historial

### 2026-09-29 — Recolección y estructura inicial

- Se revisó el enunciado y se eligió evaluar AGEB urbanas de Mérida.
- Se descargaron Censo 2020, diccionario, Marco Geoestadístico 2020 y DENUE mayo 2026 de INEGI, con manifiestos y hashes.
- Se investigaron CEISP, SESNSP y fuentes municipales. No se confirmó microdato local con coordenadas; fallos de acceso a CEISP no prueban que los datos no existan.
- Se creó estructura configurable, entorno Python, motor espacial, pruebas, Compose y documentación.
- Se ejecutó la integración: 483 AGEB, 921,771 habitantes y 54,925 negocios asignados; discrepancias pendientes 141+7.
- Tres pruebas pasaron. Compose aceptó la configuración; el contenedor no se ejecutó porque el servicio Docker no estaba activo. No hay warehouse poblado.

### 2026-09-29 — Bitácora de continuidad

- A petición del usuario, se creó este archivo y se enlazó desde README.
- Se cotejó el estado con README, validación geográfica y estado Git. No se modificaron datos, lógica de procesamiento ni resultados.
- Siguiente sesión: comenzar por la revisión de discrepancias espaciales y continuar con variables de KPIs; incorporar novedades sobre seguridad si las hay.

### 2026-09-29 — Auditoría espacial de continuidad

- Se retomó la bitácora y se comprobó el estado Git; no se hicieron commits ni cambios en datos originales.
- Se creó y ejecutó `src/audit_discrepancies.py`, configurable por territorio y con verificación de hashes contra el diagnóstico previo.
- Los 141 exteriores están a menos de 500 m; 89 a 100 m o menos. En 64 la clave AGEB declarada no aparece en la capa urbana 2020; seis caen en otra AGEB urbana del estado.
- Los siete interiores con otras claves declaran Kanasín (1), Umán (2), La Roca (3) y Progreso (1). Se conservaron señalados y sin corrección.
- Se verificaron 148 identificadores únicos, conciliación 141+7 y distancias cero al área en los siete interiores. Cero pares de polígonos con intersección de superficie positiva.
- Reporte: `docs/auditoria_discrepancias.md`. Evidencia por registro y resumen en `outputs/merida/phase1/discrepancy_audit.csv` y `.json`.
- No se repitieron las tres pruebas previas: el motor de asignación no cambió. No se demostró la causa exacta de las discrepancias ni ausencia de huecos cartográficos.
- Siguiente acción: diccionario de variables/KPIs y perfil de faltantes; seguridad y decisión temporal siguen pendientes.

### 2026-09-29 — Gestión presencial de datos de seguridad

- El usuario visitó su estación de policía cercana; según informó, le indicaron acudir a la sede central ubicada por Periférico.
- No se recibieron archivos ni confirmación de que exista una base georreferenciada accesible para el proyecto.
- El usuario estima informalmente 60% de posibilidad de que exista la información y 30% de que exista y se la proporcionen. Son expectativas personales, no probabilidades verificadas ni criterios técnicos de decisión.
- Seguridad sigue pendiente. No se contactó a ninguna institución desde este proyecto.
- El próximo trabajo técnico permanece: diccionario de variables para KPIs y perfil de faltantes/denominadores; CDMX sigue como alternativa sin activar.

### 2026-09-29 — Diccionario y perfil de insumos para KPIs

- Se contrastaron variables con los diccionarios originales de los ZIP y la estructura sectorial del INEGI.
- Creados `src/profile_kpi_inputs.py` y `docs/diccionario_kpis.md`; README enlaza el comando y el documento.
- Perfil ejecutado con verificación de hashes/configuración: cinco AGEB con población cero, once sin negocios asignados, símbolos `*` en variables censales y 24 empates de sector dominante.
- Los estratos DENUE de personal ocupado no son conteos exactos de empleos. PEA usa 12+ como denominador propuesto. Faltantes no se convierten a cero y los grupos de edad no deben superponerse.
- El diccionario DENUE mayo 2026 menciona SCIAN 2018; la versión efectiva necesita verificación. No etiquetar automáticamente los códigos como SCIAN 2023.
- No se calcularon KPIs finales ni se modificaron asignaciones. Evidencia: `outputs/merida/phase1/kpi_input_profile.json`.
- Próximo paso: versión SCIAN y coherencia temporal. Seguridad sigue pendiente de la gestión en sede central y fuentes públicas.

### 2026-09-29 — Versión SCIAN confirmada documentalmente

- Metodología específica DENUE 05/2026: SCIAN 2023, sección 4.2 nota 14. Las menciones a 2018 en el diccionario empaquetado son inconsistentes con esa declaración; texto heredado es una hipótesis editorial, no un hecho confirmado.
- Documento descargado y registrado con hash. Nota: docs/verificacion_scian.md.
- Detectado Marco Geoestadístico 2024 y advertencias de precisión/periodo de referencia en la metodología; no equivalen a una explicación individual de las 148 discrepancias.
- Próximo paso: validar catálogo completo y explorar edición histórica. Sin cambios a datos ni asignaciones.

### 2026-09-29 — Catálogo y alternativas históricas

- Descargados catálogo SCIAN 2023 oficial (XLSX) y ZIP de URLs DENUE abril/noviembre 2020; procedencia y hashes en docs/historic_scian_acquisition.json.
- Validadas 815 clases de 2026 contra 1,086 clases oficiales; cero códigos desconocidos. Cuarenta descripciones difieren y afectan 4,251 registros estatales: no todas son diferencias solo tipográficas.
- Comprobación independiente del XLSX y conciliación de 146,384 registros. Sin edición del catálogo ni de los originales.
- Noviembre 2020: 130,626 registros estatales y 53,378 asignados al área; 504+104 discrepancias. Metadatos coherentes con noviembre 2020.
- URL abril 2020: metadatos internos dicen 11_2019; edición marcada pendiente. No se adopta como fuente activa.
- Los históricos requieren adaptación de codificación; contienen un carácter C1 cada uno. Script de comparación preserva bytes con Latin-1 y reporta esta limitación.
- Configuración activa conservada en mayo 2026. No interpretar diferencias entre ediciones como crecimiento/aperturas/cierres.
- Siguiente acción: metodología y clasificación histórica de noviembre 2020; decisión temporal sigue abierta con seguridad pendiente.

### 2026-09-29 — Metodología histórica revisada

- Se descargó e identificó por portada y contenido la metodología DENUE 11/2020, aunque el buscador presenta un título de abril.
- SCIAN 2018 y Marco Geoestadístico septiembre 2019 confirmados documentalmente.
- Separar edición de publicación de periodo de referencia. No interpretar los estratos como empleo exacto ni observado en noviembre 2020.
- Se preserva la alternativa histórica; no se cambió la configuración activa ni se repitieron pruebas espaciales.
- Evaluación: docs/evaluacion_denue_202011.md. Siguiente acción independiente: justificación de unidad geográfica; seguridad y elección temporal siguen pendientes.

### 2026-09-29 — Decisión geográfica y checkpoint

- Se documentó la selección operativa de 483 AGEB urbanas de la localidad de Mérida, Marco 2020, comparándola con municipio, colonia y manzana.
- Se explicitó alcance, clave versionada, regla de asignación y límites para seguridad. No hubo nuevas ejecuciones de datos ni cambios de configuración.
- Se creó matriz de evidencia: la prueba con negocios no reemplaza la de delitos. La Fase 1 no está completa.
- Documentos: docs/decision_geografica.md y docs/checkpoint_fase1.md; enlazados desde README.
- Siguiente acción: contrato de entrada de seguridad, sin datos ficticios. Elección temporal pendiente.

### 2026-09-30 — Activación de Plan B y primera integración CDMX

- Usuario confirma que la gestión local no entregaría seguridad a tiempo. Se cambia territorio a CDMX, preservando Mérida como antecedente.
- Descargadas cuatro fuentes con hashes. FGJ obtenido mediante exportación DataStore oficial por certificado vencido del servidor de archivo; 204,121 filas conciliadas con API.
- Creada configuración CDMX y adaptador `src/assess_crime_cdmx.py`; originales inalterados.
- Corregidos sumatorio de niveles censales y ceros iniciales DENUE; codificación histórica explícita. Nueve pruebas aprobadas.
- Censo: 2,433 AGEB; Marco: 2,431. Dos claves sin geometría y 7,108 habitantes excluidos del diagnóstico espacial, pendientes de revisión.
- DENUE: 474,328 filas, 472,608 asignadas. FGJ: 204,121 filas, 194,356 asignadas, 9,111 coordenadas inválidas/ausentes y 654 fuera.
- Contrato, evidencias y límites en `docs/plan_b_cdmx.md`. Fase 1 no cerrada; precisión, elegibilidad, cobertura y perfil KPI CDMX pendientes. No se cargó el DW ni se hicieron commits.

### 2026-09-30 — Auditoría de cobertura y selección candidate-v1

- Censo urbano vs Marco rural comprobado para las dos localidades excluidas; no se asumió equivalencia con polígonos rurales.
- Cero superposiciones con área positiva. De 654 FGJ fuera de AGEB, 430 están dentro del polígono estatal; DENUE: 1,149 de 1,720.
- Regla candidate-v1: excluye hechos no delictivos e incompetencias, conserva competencia desconocida con marca. 199,650 candidatos, 191,233 asignados. No son KPIs definitivos.
- Competencia NA casi generalizada de enero a agosto y ausente de septiembre a diciembre: exigir fuero común conocido sesgaría la cobertura temporal.
- Script y pruebas añadidos; 10 pruebas aprobadas. Evidencia y contrato en docs/auditoria_cdmx.md y docs/cdmx_coverage_audit.json.
- Siguiente: perfil KPI CDMX, catálogo SCIAN 2018 y sensibilidad a precisión; no se cargó DW ni se hicieron commits.

### 2026-09-30 — Perfil KPI CDMX y sensibilidad espacial

- Perfil ejecutado sobre las 2,431 AGEB comparables: 17 con población cero, 12 sin negocios, 77 empates de dominancia; reservados censales conservados.
- 937 clases observadas validadas contra 1,084 clases extraídas del catálogo SCIAN 2018; cero códigos ajenos, sin comparación textual de descripciones.
- Distancias a límites propios: seguridad candidata 25.99% dentro de 10 m y 54.11% dentro de 50 m. Radios ilustrativos, no errores observados; no se reasignaron puntos.
- Contrato de los 14 indicadores actualizado en docs/kpis_cdmx.md; evidencia JSON portable y scripts reproducibles guardados. Doce pruebas aprobadas.
- Pendiente: robustez de la escala, modelo/ETL y revisión textual SCIAN. No se cargó DW ni se realizaron commits.

### 2026-09-30 — Simulaciones de desplazamiento

- Ejecutadas 80 realizaciones: seguridad candidata y negocios, radios máximos 10/25/50/100 m, 10 semillas reproducibles. Distribución uniforme en disco, desplazamientos independientes; escenarios sintéticos, no error estimado.
- Se incluyeron puntos válidos originalmente fuera para permitir entradas; inválidos no simulados. Radio cero coincide con asignaciones anteriores. Originales intactos.
- Seguridad: cambios medios de asignación 6.91%, 12.50%, 17.89%, 25.53%. Con 50 m, unas 195 AGEB por repetición cambian conteo >=20% entre las de base >=20; orden global más estable no garantiza estabilidad local.
- Evidencia: docs/simulaciones_cdmx.md y docs/cdmx_simulation_report.json; 80 filas de ejecución, 8 tablas por AGEB y gráfica en outputs/cdmx/phase1/simulations.
- Catorce pruebas aprobadas. Pendiente DW/modelo/ETL y sensibilidad de KPIs finales; no se hicieron commits ni carga a PostGIS.

### 2026-09-30 — Primer arranque Docker/PostGIS

- Docker Desktop disponible (motor 29.8.1). Levantado servicio db con volumen persistente y puerto 127.0.0.1:5433.
- Configuración .env creada con contraseña aleatoria, excluida de Git; no registrar su contenido en documentación.
- Contenedor healthy; PostgreSQL 17.5 y PostGIS 3.5.2 verificados mediante SQL. Esquemas staging/dw/analytics presentes; consulta espacial correcta, autenticación TCP interna y puerto del host verificados.
- Evidencia sin secretos e imagen identificada por digest: docs/docker_runtime_check.json.
- Próximo paso: modelo dimensional y migraciones explícitas, luego carga reproducible. No hay hechos/dimensiones cargados; no se realizaron commits.

### 2026-09-30 — Cierre operativo de Fase 1

- Consolidado docs/cierre_fase1.md, rector del alcance y criterios de calidad. La precisión desconocida y sensibilidad pasan como restricciones explícitas a la siguiente fase.
- Adoptados 2,431 AGEB y candidate-v1 para la carga inicial; no se alteraron retrospectivamente diagnósticos ni originales.
- Incorporadas copias de evidencia geográfica/seguridad y restaurador de fuentes con verificación SHA-256 para reproducir desde un clon.
- Publicado commit de cierre 690e2e2 en origin/codex/fase-1-recoleccion-validacion-cdmx. Originales, salidas y credenciales excluidos. Primera publicación del repositorio; no había rama remota main ni se realizó merge.
- Siguiente: migraciones del modelo dimensional y ETL. No hay datos cargados en el DW.

### Plantilla para futuras entradas

Copiar este formato con fecha real, sin marcar trabajo pendiente como realizado:

- Fecha y tema:
- Trabajo realizado / archivos cambiados:
- Comprobaciones y resultados:
- Decisiones o cambios de alcance:
- Bloqueos y limitaciones:
- Siguiente acción concreta:
