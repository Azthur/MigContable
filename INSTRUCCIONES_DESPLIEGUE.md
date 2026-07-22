# Instrucciones de Despliegue en Red

## Arquitectura

- **Servidor BD (192.168.2.1)**: Solo PostgreSQL y Redis
- **Servidor App (192.168.2.90)**: Aplicación completa (app, celery-worker, celery-beat, flower)

## Despliegue en Servidor BD (192.168.2.1)

1. Crear directorio para el proyecto BD:
```bash
mkdir /srv/migconta-db
cd /srv/migconta-db
```

2. Crear directorios de persistencia:
```bash
mkdir postgres_data redis_data
```

3. Copiar archivo `docker-compose-db-only.yml` del proyecto principal a este directorio

4. Levantar servicios:
```bash
docker-compose -f docker-compose-db-only.yml up -d
```

5. Verificar:
```bash
docker ps
# Debería mostrar sistemamigconta-db y sistemamigconta-redis
```

## Despliegue en Servidor App (192.168.2.90)

1. Clonar/copiar el proyecto completo (sin postgres_data)

2. Configurar `.env` (ya está configurado):
```env
POSTGRES_CONNECTION_STRING=postgresql://postgres:postgres@192.168.2.1:5434/migconta_db
REDIS_URL=redis://192.168.2.1:6379/0
CELERY_BROKER_URL=redis://192.168.2.1:6379/0
CELERY_RESULT_BACKEND=redis://192.168.2.1:6379/1
```

3. Levantar aplicación:
```bash
docker-compose up -d
```

4. Verificar conexión:
```bash
docker-compose logs app
# Debería conectar exitosamente a 192.168.2.1:5434
```

## Resumen de Archivos

### Servidor BD (192.168.2.1)
- `docker-compose-db-only.yml`
- `postgres_data/` (bind mount)
- `redis_data/` (bind mount)

### Servidor App (192.168.2.90)
- `docker-compose.yml` (sin servicios db/redis)
- `.env` (apuntando a 192.168.2.1)
- Todo el código de la aplicación

## Conexión Directa a BD desde Servidor App

Para conectar directamente desde 192.168.2.90:
```bash
psql -h 192.168.2.1 -p 5434 -U postgres -d migconta_db
```

## Firewall

Asegurar que el firewall en 192.168.2.1 permita:
- Puerto 5434 (PostgreSQL)
- Puerto 6379 (Redis)
- Desde 192.168.2.90 (o toda la red local si es necesario)
