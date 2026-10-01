# Simulaciones de sensibilidad espacial — CDMX

Fecha: 2026-09-30. Ochenta ejecuciones: dos fuentes × cuatro radios × diez semillas. Catorce pruebas aprobadas. Los originales permanecen intactos.

## Método y universo

Desplazamiento independiente por punto, uniforme en el área de un disco de radio máximo 10, 25, 50 o 100 m, en EPSG:32614. Distancia = radio × raíz de U; dirección uniforme. Semillas 20260930–20260939, emparejadas entre radios para cada fuente. No todos los puntos se desplazan exactamente el radio máximo. No se modela un error observado, sistemático ni correlacionado. Diez repeticiones son una exploración, no una prueba de convergencia ni intervalos de confianza.

La asignación de radio cero se verificó contra la salida previa para todos los puntos válidos. Cada nueva asignación exige una sola intersección; múltiples coincidencias se separan como ambiguas. Se comprueba que los conteos concilien. Se incluyen puntos válidos inicialmente fuera de AGEB para permitir entradas, además de salidas. Los puntos sin coordenadas válidas no se inventan ni simulan.

```json
{
  "crime": {
    "source_rows": 199650,
    "valid_points": 191874,
    "invalid_unperturbed": 7776,
    "initial_assigned": 191233,
    "initial_outside": 641
  },
  "business": {
    "source_rows": 474328,
    "valid_points": 474328,
    "invalid_unperturbed": 0,
    "initial_assigned": 472608,
    "initial_outside": 1720
  }
}
```

## Resultados medios

Cambios de punto incluyen traslado a otra AGEB o pérdida de asignación. L1 = suma de diferencias absolutas de conteos / total inicial asignado; una transferencia entre AGEB contribuye dos veces. No equivale al porcentaje de ubicaciones incorrectas. La agregación por alcaldía usa exclusivamente las AGEB urbanas seleccionadas, no el territorio municipal completo.

| Fuente | Radio | Puntos con asignación distinta | L1 conteos AGEB | L1 agregados urbanos por alcaldía | Correlación de rangos de conteos |
|---|---:|---:|---:|---:|---:|
| crime | 10 m | 6.91% | 3.99% | 0.10% | 0.9963 |
| crime | 25 m | 12.50% | 6.25% | 0.20% | 0.9920 |
| crime | 50 m | 17.89% | 8.07% | 0.29% | 0.9875 |
| crime | 100 m | 25.53% | 9.97% | 0.40% | 0.9810 |
| business | 10 m | 4.14% | 2.83% | 0.06% | 0.9976 |
| business | 25 m | 11.15% | 6.26% | 0.19% | 0.9913 |
| business | 50 m | 17.37% | 8.74% | 0.38% | 0.9853 |
| business | 100 m | 25.16% | 11.62% | 0.61% | 0.9766 |

## Cambios locales y cobertura

| Fuente | Radio | Entradas medias | Salidas medias | AGEB con cambio ≥20%, entre las de base ≥20 |
|---|---:|---:|---:|---:|
| crime | 10 | 61.0 | 139.5 | 37.8 |
| crime | 25 | 88.9 | 332.5 | 114.6 |
| crime | 50 | 116.1 | 522.5 | 195.1 |
| crime | 100 | 153.4 | 782.6 | 307.7 |
| business | 10 | 16.3 | 197.3 | 48.8 |
| business | 25 | 23.6 | 577.1 | 180.1 |
| business | 50 | 31.7 | 1059.0 | 320.1 |
| business | 100 | 53.6 | 1653.3 | 490.3 |

Los extremos por AGEB son mínimo y máximo observados en diez realizaciones; no son límites garantizados. Se excluyen bases menores de 20 sólo del recuento de cambios porcentuales locales, para evitar porcentajes dominados por denominadores pequeños; esas AGEB siguen incluidas en todas las demás métricas.

## Interpretación y decisión de trabajo

Conservar AGEB como unidad de integración y análisis exploratorio; mostrar sensibilidad junto a mapas y no declarar robustos focos locales a partir de una correlación global alta. Las compensaciones entre entradas y salidas pueden estabilizar los conteos agregados aunque cambien muchos puntos. La comparación municipal es diagnóstico de agregación del mismo universo urbano, no un nuevo KPI municipal.

Estas pruebas no validan tasas, categorías específicas, cocientes delitos/negocios, Moran ni LISA. Antes de interpretar esos resultados finales habrá que repetir la sensibilidad sobre sus valores calculados desde el DW. Un escenario isotrópico no cubre desplazamientos sistemáticos, coordenadas repetidas por geocodificación, centroides ni errores de datum.

El paso siguiente es cerrar el modelo dimensional y preparar la carga a PostGIS conservando originales, asignación, estado de calidad, selección candidate-v1 y fechas separadas. Guardar sensibilidad como diagnóstico separado. La precisión real de FGJ continúa desconocida; estas simulaciones no la sustituyen.

## Evidencia y reproducción

`outputs/cdmx/phase1/simulations/`: report.json con hashes y semillas; runs.csv con las 80 ejecuciones; ocho tablas de resultados por AGEB; sensitivity_scenarios.png. Copia portable: docs/cdmx_simulation_report.json.

```powershell
.\.venv\Scripts\python.exe src/simulate_spatial_cdmx.py
.\.venv\Scripts\python.exe src/report_simulations.py
.\.venv\Scripts\python.exe -m pytest tests -q
```
