# Urban Intelligence / DataHauseWare 

**Para retomar el proyecto:** leer la [bitácora de trabajo](BITACORA.md), con estado actual, decisiones, pendientes e historial por sesión.

Proyecto académico de Data Warehouse geoespacial. Alcance activo desde 2026-09-30: AGEB urbanas de CDMX, con dos claves censales pendientes de geometría. Se conservan Mérida y sus resultados como antecedente. Ver [Plan B y evidencia](docs/plan_b_cdmx.md).

## Estado

Fase 1 cerrada. **Fase 2 implementada y validada localmente**, pendiente revisión del PR: DW cargado, vistas de 14 indicadores y guía de continuación.

- [Modelo y ETL de Fase 2](docs/fase2_modelo_etl.md)
- [Instalación, consumo y continuación de Fase 3](HANDOFF_FASE3.md)
- [Cierre de Fase 1](docs/cierre_fase1.md)

Las instrucciones siguientes conservan la reproducción de los diagnósticos de Fase 1. Para cargar el DW no es necesario repetirlos: usar HANDOFF_FASE3.md.

## Ejecutar la comprobación geográfica

Python 3.12. Desde la raíz del repositorio, en PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe src/assess_geography.py --config config/cdmx.json
.\.venv\Scripts\python.exe src/assess_crime_cdmx.py
```

Si el entorno ya existe, usar sus comandos directamente. `requirements.txt` registra las versiones del entorno validado. Los archivos de entrada son los ZIP originales indicados en la configuración; no se editan ni se extraen sobre los originales. `src/download_inegi.py` es el recolector inicial de Yucatán (todavía no está parametrizado): conserva los archivos existentes. Censo y diccionario tienen sus URLs en `docs/censo2020_acquisition.json`; DENUE y cartografía en `docs/inegi_additional_acquisition.json`. Las descargas futuras de URLs mutables pueden ofrecer otra edición: comprobar metadatos y SHA-256.

Resultados activos en `outputs/cdmx/phase1/` (Mérida conserva sus salidas):

- `quality_report.json`: CRS, correspondencia de claves, integridad y asignaciones.
- `business_assignment.csv`: una fila por candidato estatal, con estado asignado/fuera/ambiguo/coordenadas inválidas.
- `area_diagnostics.csv`: población censal, área geodésica y conteos preliminares de registros.
- `areas.geojson` y `spatial_check.png`: evidencia espacial.

La salida se regenera al ejecutar; originales permanecen intactos. GeoJSON y mapa son diagnósticos de fase 1, no entregables analíticos finales.

CDMX: fuentes y hashes en `docs/cdmx_acquisition.json`; contrato y resultados de seguridad en `docs/plan_b_cdmx.md`. Los comandos posteriores específicos de Mérida son diagnósticos históricos.

## Cambiar de territorio

1. Copiar `config/cdmx.example.json` a una configuración nueva.
2. Definir alcaldías/localidades. Listas vacías seleccionan todas las unidades urbanas de la entidad, NO una zona metropolitana.
3. Descargar y registrar las tres fuentes de esa entidad; verificar nombres internos, hashes, ediciones y esquema.
4. Ajustar rutas, edición DENUE y activar `enabled`.
5. Ejecutar el mismo `assess_geography.py --config ...` y revisar rechazos y cobertura.

Las fuentes INEGI comparten un procesamiento configurable. Los delitos requieren un adaptador específico para el formato y significado de cada fuente: cambiar la ciudad no convierte automáticamente carpetas, llamadas y denuncias en la misma unidad de observación. Véase `docs/arquitectura.md`.

## PostgreSQL/PostGIS preparado

```powershell
Copy-Item .env.example .env
# Editar POSTGRES_PASSWORD en .env con una contraseña local.
docker compose up -d db
docker compose exec db psql -U urban -d urban_intelligence -c "SELECT PostGIS_Version();"
```

Se usa `postgis/postgis:17-3.5`, puerto local 5433 y volumen persistente. `.env` queda fuera de Git. Si cambian usuario/base, ajustar el comando psql. Los scripts de `sql/init` se ejecutan al inicializar un volumen nuevo. No borrar el volumen para aplicar cambios futuros: utilizar migraciones. Actualmente solo se crean extensión y esquemas `staging`, `dw`, `analytics`; no hay tablas de hechos cargadas. El arranque real requiere Docker Desktop activo. No se ha validado el contenedor en ejecución.

## Reglas de interpretación

- Seleccionar únicamente totales AGEB del censo: no sumarlos con manzanas ni totales de localidad.
- Claves INEGI como texto, conservando ceros iniciales.
- Superficies geodésicas WGS84 en km²; coordenadas DENUE interpretadas como WGS84, pendientes de cotejo con documentación de precisión de la fuente.
- Prueba espacial con `intersects`: un punto sobre límite compartido queda ambiguo; no se duplica ni se asigna por cercanía.
- Se evalúa DENUE estatal para detectar puntos dentro del área aunque sus claves de localidad estén desactualizadas. El reporte distingue el alcance declarado del espacial.
- DENUE 2026 / población 2020: no equivale a una tasa contemporánea de 2026. Decisión temporal pendiente.
- Ausencia de datos de delitos significa desconocido, no cero.

## Colaboración

Un repositorio para todas las fases; commits identificables por integrante. Datos brutos, entorno, credenciales y salidas regenerables quedan fuera de Git. Registrar código, configuraciones, documentación y manifiestos. Mapas finales seleccionados para entrega se incorporarán explícitamente después.

## Auditoría de discrepancias

El [reporte de discrepancias](docs/auditoria_discrepancias.md) caracteriza 141+7 casos y la revisión de solapamientos. Para regenerarlo después de la evaluación geográfica:

```powershell
.\.venv\Scripts\python.exe src/audit_discrepancies.py --config config/merida.json
```

Las distancias no se usan para reasignar puntos. Originales y asignaciones previas se conservan.

## Variables y perfil para KPIs

Consultar [diccionario de variables y KPIs](docs/diccionario_kpis.md). Para verificar insumos sin calcular indicadores finales:

```powershell
.\.venv\Scripts\python.exe src/profile_kpi_inputs.py --config config/merida.json
```

La salida `outputs/merida/phase1/kpi_input_profile.json` conserva faltantes y reporta denominadores cero y empates.

## Comparación histórica y SCIAN

[Resultados y límites](docs/comparacion_denue_historico.md). Se conservan candidatos históricos sin sustituir la configuración activa.

```powershell
.\.venv\Scripts\python.exe src/compare_denue_vintages.py
```

Requiere los originales del manifiesto `docs/historic_scian_acquisition.json`.

## Decisión geográfica y checkpoint

La [decisión de usar AGEB](docs/decision_geografica.md) compara alternativas, define el alcance y establece condiciones para seguridad. El [estado del checkpoint](docs/checkpoint_fase1.md) distingue evidencia disponible y requisitos pendientes.

## Perfil activo de indicadores

[Contrato de los 14 KPIs y sensibilidad CDMX](docs/kpis_cdmx.md): perfil ejecutado, SCIAN 2018 verificado por códigos y límites de precisión documentados.

[Simulaciones espaciales CDMX](docs/simulaciones_cdmx.md): 80 realizaciones reproducibles, comparación de conteos por AGEB y agregados urbanos por alcaldía.

## Servicio local en ejecución

PostgreSQL/PostGIS iniciado y verificado el 2026-09-30. [Conexión y operación](docs/docker_operacion.md). Puerto localhost:5433; esquemas y carga del DW verificados; ver estado actualizado de Fase 2.
