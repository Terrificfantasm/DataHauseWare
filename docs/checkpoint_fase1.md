> Estado vigente: [cierre de Fase 1 y alcance operativo](cierre_fase1.md). Este documento conserva antecedentes; el DW sigue pendiente.

> Actualización 2026-09-30: CDMX es el territorio activo. Este documento conserva la evaluación/propuesta previa de Mérida; consultar [Plan B y evidencia vigente](plan_b_cdmx.md) antes de reutilizar cifras o criterios.

# Evidencia del checkpoint de Fase 1

Estado al 2026-09-29. Esta tabla distingue trabajo ejecutado de requisitos todavía abiertos.

| Requisito | Evidencia | Estado |
|---|---|---|
| Inventario y procedencia | Manifiestos de adquisición en docs; originales conservados | Cubiertas demografía, economía y geografía; seguridad pendiente |
| Perfil inicial de fuentes | quality_report.json y kpi_input_profile.json en outputs/merida/phase1 | Ejecutado para las tres capas disponibles |
| Evaluación y decisión de unidad geográfica | [Decisión geográfica](decision_geografica.md) | Documentada; adecuación a seguridad condicionada |
| Inspección de CRS, claves y geometrías | [Validación](validacion_geografica.md) y [auditoría](auditoria_discrepancias.md) | Ejecutada |
| Evidencia punto-polígono | business_assignment.csv y spatial_check.png | Ejecutada con negocios; NO sustituye prueba con delitos |
| Conversión e integración de delitos | Falta fuente con ubicación | Pendiente |
| Variables para métricas | [Diccionario](diccionario_kpis.md) | Identificadas; seguridad es contrato previsto |
| Temporalidad y limitaciones | [Comparación](comparacion_denue_historico.md), [evaluación histórica](evaluacion_denue_202011.md) | Alternativas evaluadas; elección temporal pendiente |
| Reproducibilidad y colaboración | Scripts, configuraciones, requisitos y bitácora | Scripts presentes; historial de commits pendiente de organizar |

Próximo trabajo independiente: preparar un contrato de entrada verificable para seguridad (campos, significado por fila, precisión de fecha/ubicación y validaciones), para poder evaluar el archivo cuando llegue sin rehacer la arquitectura. No hace falta crear datos ficticios para cerrar el checkpoint.
