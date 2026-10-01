# PostgreSQL/PostGIS local

Verificado 2026-09-30: servicio db healthy, PostgreSQL 17.5, PostGIS 3.5.2. Esquemas staging, dw y analytics creados. Evidencia: docker_runtime_check.json. El DW aún no contiene hechos ni dimensiones.

Conexión: host 127.0.0.1, puerto 5433, base urban_intelligence, usuario urban. Contraseña local en .env (excluido de Git); no copiar a reportes ni subir al repositorio.

Desde la raíz del proyecto:

```powershell
docker compose up -d --wait
docker compose ps
docker compose exec db psql -U urban -d urban_intelligence
docker compose stop
```

`stop` detiene el servicio conservando los datos. El volumen datahouseware_postgres_data persiste independientemente del contenedor. No usar `down -v` para apagar: elimina el volumen.

Los SQL de sql/init se ejecutan sólo al inicializar un volumen vacío. Los cambios futuros del modelo deben aplicarse mediante migraciones explícitas; reiniciar el contenedor no las aplica automáticamente.

Comprobado: autenticación TCP dentro del contenedor, puerto del host accesible, consulta espacial ST_Contains y disponibilidad de esquemas. No equivale a una carga ETL ni una prueba de integración completa del DW.
