# Arquitectura de Base de Datos Externa

## Resumen
El sistema ahora soporta múltiples instancias de la aplicación conectadas a una sola base de datos PostgreSQL y Redis externos.

## Estructura de Archivos

- `docker-compose.yml` - Servicios de la aplicación (app, celery-worker, celery-beat, flower)
- `docker-compose.db.yml` - Servicios de infraestructura (PostgreSQL, Redis)
- `.env` - Variables de conexión configurables

## Servicios que usan la BD

- **app** - API principal
- **celery-worker** - Procesamiento de tareas ETL
- **celery-beat** - Scheduler de tareas
- **flower** - Monitoreo de Celery

## Modos de Operación

### Modo 1: BD Local (mismo equipo)
En el servidor donde corre la BD:

```bash
# Levantar BD y Redis
docker-compose -f docker-compose.db.yml up -d

# Levantar aplicación
docker-compose up -d
```

### Modo 2: BD en Red (servidor dedicado)
En el servidor dedicado de BD:

```bash
# Solo levantar BD y Redis
docker-compose -f docker-compose.db.yml up -d
```

En cada equipo con la aplicación:

1. Editar `.env`:
```env
POSTGRES_CONNECTION_STRING=postgresql://postgres:postgres@IP_DEL_SERVIDOR:5434/migconta_db
REDIS_URL=redis://IP_DEL_SERVIDOR:6379/0
CELERY_BROKER_URL=redis://IP_DEL_SERVIDOR:6379/0
CELERY_RESULT_BACKEND=redis://IP_DEL_SERVIDOR:6379/1
```

2. Levantar la aplicación:
```bash
docker-compose up -d
```

## Credenciales

- **PostgreSQL**: `postgres` / `postgres`
- **Base de datos**: `migconta_db`
- **Puerto PostgreSQL**: 5434 (mapeado desde 5432 interno)
- **Puerto Redis**: 6379

## Persistencia de Datos

La BD usa bind mount en `./postgres_data/`, por lo que:
- La data viaja con el proyecto
- Es portable entre equipos
- Se puede hacer backup simplemente copiando el directorio

## Migración desde Volumen Docker

Si ya tenías datos en el volumen Docker anterior:

1. Detener contenedores
2. Copiar datos del volumen al directorio local
3. Levantar con la nueva configuración

## Backup y Restore

### Backup
```bash
docker exec sistemamigconta-db pg_dump -U postgres migconta_db > backup.sql
```

### Restore
```bash
docker exec -i sistemamigconta-db psql -U postgres migconta_db < backup.sql
```

## Conexión Directa a la BD

Desde el host:
```bash
psql -h localhost -p 5434 -U postgres -d migconta_db
```

Desde Docker:
```bash
docker exec -it sistemamigconta-db psql -U postgres -d migconta_db
```
