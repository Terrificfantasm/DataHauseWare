"""Render and document completed simulation outputs."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'outputs/cdmx/phase1/simulations'
r=json.loads((out/'report.json').read_text(encoding='utf-8'))
fig,axes=plt.subplots(1,2,figsize=(12,4.8))
for name,label,color in [('crime','Seguridad candidata','#b04d35'),('business','Negocios','#237a8a')]:
    rows=[s for s in r['summaries'] if s['source']==name]
    x=[s['radius_m'] for s in rows]
    for ax,key in zip(axes,['changed_initially_assigned_percent','count_l1_percent']):
        y=[s[key+'_mean'] for s in rows]
        ax.plot(x,y,'o-',label=label,color=color)
        if key=='count_l1_percent':
            ax.fill_between(x,[s[key+'_min'] for s in rows],[s[key+'_max'] for s in rows],color=color,alpha=.15)
        ax.set_xlabel('Radio máximo del desplazamiento (m)');ax.set_ylabel('%');ax.grid(alpha=.2);ax.legend()
axes[0].set_title('Puntos con asignación distinta (media)')
axes[1].set_title('Suma de cambios absolutos / total inicial')
fig.suptitle('CDMX · Escenarios sintéticos de sensibilidad por AGEB')
fig.text(.5,.01,'10 repeticiones por radio · No representan errores medidos ni intervalos de confianza',ha='center',fontsize=9)
fig.tight_layout(rect=[0,.04,1,.94]);fig.savefig(out/'sensitivity_scenarios.png',dpi=160);plt.close(fig)
lines=['# Simulaciones de sensibilidad espacial — CDMX','',
'Fecha: 2026-09-30. Ochenta ejecuciones: dos fuentes × cuatro radios × diez semillas. Catorce pruebas aprobadas. Los originales permanecen intactos.','',
'## Método y universo','',
'Desplazamiento independiente por punto, uniforme en el área de un disco de radio máximo 10, 25, 50 o 100 m, en EPSG:32614. Distancia = radio × raíz de U; dirección uniforme. Semillas 20260930–20260939, emparejadas entre radios para cada fuente. No todos los puntos se desplazan exactamente el radio máximo. No se modela un error observado, sistemático ni correlacionado. Diez repeticiones son una exploración, no una prueba de convergencia ni intervalos de confianza.','',
'La asignación de radio cero se verificó contra la salida previa para todos los puntos válidos. Cada nueva asignación exige una sola intersección; múltiples coincidencias se separan como ambiguas. Se comprueba que los conteos concilien. Se incluyen puntos válidos inicialmente fuera de AGEB para permitir entradas, además de salidas. Los puntos sin coordenadas válidas no se inventan ni simulan.','',
'```json',json.dumps(r['cohorts'],indent=2),'```','',
'## Resultados medios','',
'Cambios de punto incluyen traslado a otra AGEB o pérdida de asignación. L1 = suma de diferencias absolutas de conteos / total inicial asignado; una transferencia entre AGEB contribuye dos veces. No equivale al porcentaje de ubicaciones incorrectas. La agregación por alcaldía usa exclusivamente las AGEB urbanas seleccionadas, no el territorio municipal completo.','',
'| Fuente | Radio | Puntos con asignación distinta | L1 conteos AGEB | L1 agregados urbanos por alcaldía | Correlación de rangos de conteos |',
'|---|---:|---:|---:|---:|---:|']
for s in r['summaries']:
    lines.append(f"| {s['source']} | {s['radius_m']} m | {s['changed_initially_assigned_percent_mean']:.2f}% | {s['count_l1_percent_mean']:.2f}% | {s['municipal_urban_l1_percent_mean']:.2f}% | {s['ageb_rank_correlation_mean']:.4f} |")
lines+=['','## Cambios locales y cobertura','','| Fuente | Radio | Entradas medias | Salidas medias | AGEB con cambio ≥20%, entre las de base ≥20 |','|---|---:|---:|---:|---:|']
for s in r['summaries']:
    lines.append(f"| {s['source']} | {s['radius_m']} | {s['entries_mean']:.1f} | {s['exits_mean']:.1f} | {s['ageb_abs_change_ge_20pct_baseline_ge20_mean']:.1f} |")
lines+=['','Los extremos por AGEB son mínimo y máximo observados en diez realizaciones; no son límites garantizados. Se excluyen bases menores de 20 sólo del recuento de cambios porcentuales locales, para evitar porcentajes dominados por denominadores pequeños; esas AGEB siguen incluidas en todas las demás métricas.','',
'## Interpretación y decisión de trabajo','',
'Conservar AGEB como unidad de integración y análisis exploratorio; mostrar sensibilidad junto a mapas y no declarar robustos focos locales a partir de una correlación global alta. Las compensaciones entre entradas y salidas pueden estabilizar los conteos agregados aunque cambien muchos puntos. La comparación municipal es diagnóstico de agregación del mismo universo urbano, no un nuevo KPI municipal.','',
'Estas pruebas no validan tasas, categorías específicas, cocientes delitos/negocios, Moran ni LISA. Antes de interpretar esos resultados finales habrá que repetir la sensibilidad sobre sus valores calculados desde el DW. Un escenario isotrópico no cubre desplazamientos sistemáticos, coordenadas repetidas por geocodificación, centroides ni errores de datum.','',
'El paso siguiente es cerrar el modelo dimensional y preparar la carga a PostGIS conservando originales, asignación, estado de calidad, selección candidate-v1 y fechas separadas. Guardar sensibilidad como diagnóstico separado. La precisión real de FGJ continúa desconocida; estas simulaciones no la sustituyen.','',
'## Evidencia y reproducción','',
'`outputs/cdmx/phase1/simulations/`: report.json con hashes y semillas; runs.csv con las 80 ejecuciones; ocho tablas de resultados por AGEB; sensitivity_scenarios.png. Copia portable: docs/cdmx_simulation_report.json.','',
'```powershell',r'.\.venv\Scripts\python.exe src/simulate_spatial_cdmx.py',r'.\.venv\Scripts\python.exe src/report_simulations.py',r'.\.venv\Scripts\python.exe -m pytest tests -q','```']
(ROOT/'docs/simulaciones_cdmx.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
(ROOT/'docs/cdmx_simulation_report.json').write_bytes((out/'report.json').read_bytes())
print('Simulation report and figure saved')
