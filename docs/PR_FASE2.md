# Fase 2: DW PostGIS, ETL transaccional y vistas de los 14 indicadores

Base: `main`. Rama: `codex/fase-2-modelo-etl-postgis`.

La Fase 1 dejó fuentes y diagnósticos, pero aún no había datos en el DW. Este cambio carga los originales verificados a staging y a tres tablas de hechos, con dimensiones compartidas, trazabilidad, calidad y asignación espacial en PostGIS. Las vistas producen los 14 indicadores desde el DW sin multiplicar hechos.

## Implementación

- Migraciones con checksum, claves compuestas e índices espaciales.
- Carga atómica con COPY, bloqueo transaccional e identificación por hashes/configuración/código; repetirla verifica y omite una nueva inserción.
- Conservación de excluidos, fechas originales y reservados; candidate-v1 explícito.
- Vistas analíticas versionadas separadamente, exportador de sólo lectura y guía HANDOFF_FASE3.md.
- Pruebas de integración en base dedicada y workflow GitHub Actions preparado.

## Validación local

- 23 pruebas aprobadas, incluidas nueve de integración PostgreSQL/PostGIS.
- Carga: 2,431 AGEB; 474,328 negocios; 204,121 filas FGJ; 18 controles conciliados.
- 191,233 registros FGJ seleccionados con asignación; 11 controles de vistas aprobados.
- Paridad exacta con Fase 1 para todas las asignaciones y reglas de elegibilidad.
- Segunda ejecución sin duplicados. Reversión completa verificada en un intento fallido.
- Exportación de indicadores y geometría realizada exclusivamente desde el DW.

## Límites y revisión

El cargador está limitado a la descarga CDMX 2020 cerrada en Fase 1. Conserva las restricciones de cobertura, cohorte de inicio y precisión geográfica desconocida. Simulaciones y diagnósticos no validan por sí solos las conclusiones inferenciales.

Revisar ejecución de GitHub Actions y reproducir en otro equipo; esos resultados no se afirman como comprobados. No incluye análisis finales, Moran/LISA ni reporte final. No se fusiona automáticamente con main.
