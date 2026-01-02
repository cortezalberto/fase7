# 🚀 Comandos Rápidos - AI-Native MVP

Referencia rápida de comandos para trabajar con el proyecto.

---

## 🐳 Docker Compose

### Iniciar/Detener

```bash
# Iniciar todos los servicios
docker-compose up -d

# Con herramientas de debug (pgAdmin + Redis Commander)
docker-compose --profile debug up -d

# Con monitoreo (Prometheus + Grafana)
docker-compose --profile monitoring up -d

# Detener servicios (mantiene datos)
docker-compose down

# Detener y eliminar volúmenes (⚠️ BORRA TODOS LOS DATOS)
docker-compose down -v
```

### Ver Estado y Logs

```bash
# Ver estado de servicios
docker-compose ps

# Ver logs de todos los servicios
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f api
docker-compose logs -f postgres
docker-compose logs -f redis
docker-compose logs -f frontend

# Ver últimas 100 líneas
docker-compose logs --tail=100 api
```

### Reiniciar Servicios

```bash
# Reiniciar un servicio
docker-compose restart api

# Reiniciar todos
docker-compose restart

# Rebuild y reiniciar
docker-compose up -d --build
docker-compose up -d --build api  # Solo API
```

---

## 🔍 Debugging

### Acceder a Contenedores

```bash
# Shell en API
docker-compose exec api bash

# Shell en PostgreSQL
docker-compose exec postgres psql -U ai_native

# Shell en Redis
docker-compose exec redis redis-cli -a $REDIS_PASSWORD

# Ver procesos en un contenedor
docker-compose top api
```

### Health Checks

```bash
# API Health
curl http://localhost:8000/api/v1/health

# API Docs
curl http://localhost:8000/docs

# PostgreSQL
docker-compose exec postgres pg_isready -U ai_native

# Redis
docker-compose exec redis redis-cli -a $REDIS_PASSWORD ping
```

---

## 🧪 Tests

### Ejecutar Tests

```bash
# Todos los tests
docker-compose exec api pytest backend/tests/

# Tests específicos
docker-compose exec api pytest backend/tests/integration/
docker-compose exec api pytest backend/tests/unit/

# Con coverage
docker-compose exec api pytest --cov=backend --cov-report=html backend/tests/

# Test específico
docker-compose exec api pytest backend/tests/integration/test_api_quick.py

# Con verbose
docker-compose exec api pytest -v backend/tests/
```

---

## 🗄️ Base de Datos

### PostgreSQL

```bash
# Conectar a PostgreSQL
docker-compose exec postgres psql -U ai_native -d ai_native

# Crear backup
docker-compose exec postgres pg_dump -U ai_native ai_native > backup.sql

# Restaurar backup
cat backup.sql | docker-compose exec -T postgres psql -U ai_native -d ai_native

# Ver tablas
docker-compose exec postgres psql -U ai_native -d ai_native -c "\dt"

# Ver usuarios conectados
docker-compose exec postgres psql -U ai_native -d ai_native -c "SELECT * FROM pg_stat_activity;"
```

### Redis

```bash
# Conectar a Redis
docker-compose exec redis redis-cli -a $REDIS_PASSWORD

# Ver todas las keys
docker-compose exec redis redis-cli -a $REDIS_PASSWORD KEYS '*'

# Ver info de Redis
docker-compose exec redis redis-cli -a $REDIS_PASSWORD INFO

# Flush cache (⚠️ BORRA TODO)
docker-compose exec redis redis-cli -a $REDIS_PASSWORD FLUSHALL
```

---

## 📦 Instalación de Dependencias

### Backend (Python)

```bash
# Instalar nueva dependencia
docker-compose exec api pip install <package>

# Actualizar requirements.txt
docker-compose exec api pip freeze > requirements.txt

# Reinstalar dependencias
docker-compose down
docker-compose build --no-cache api
docker-compose up -d
```

### Frontend (Node.js)

```bash
# Instalar dependencias
cd frontEnd
npm install

# Agregar nueva dependencia
npm install <package>

# Ejecutar desarrollo
npm run dev

# Build para producción
npm run build
```

---

## 🔧 Mantenimiento

### Limpieza de Docker

```bash
# Limpiar contenedores detenidos
docker container prune -f

# Limpiar imágenes no usadas
docker image prune -a -f

# Limpiar volúmenes no usados (⚠️ CUIDADO)
docker volume prune -f

# Limpieza completa
docker system prune -a --volumes -f
```

### Ver uso de recursos

```bash
# Uso de recursos por contenedor
docker stats

# Tamaño de imágenes
docker images

# Tamaño de volúmenes
docker volume ls
docker system df
```

---

## 🌐 URLs Útiles

### Desarrollo

| Servicio | URL | Notas |
|----------|-----|-------|
| **API Swagger** | http://localhost:8000/docs | Documentación interactiva |
| **API ReDoc** | http://localhost:8000/redoc | Documentación alternativa |
| **Health Check** | http://localhost:8000/api/v1/health | Estado del sistema |
| **Frontend** | http://localhost:3000 | React App |

### Debug Tools (con `--profile debug`)

| Servicio | URL | Credenciales |
|----------|-----|--------------|
| **pgAdmin** | http://localhost:5050 | admin@ai-native.local / (ver .env) |
| **Redis Commander** | http://localhost:8081 | admin / (ver .env) |

### Monitoring (con `--profile monitoring`)

| Servicio | URL | Credenciales |
|----------|-----|--------------|
| **Prometheus** | http://localhost:9090 | - |
| **Grafana** | http://localhost:3001 | admin / (ver .env) |

---

## 📝 Variables de Entorno

### Configurar

```bash
# Copiar ejemplo
cp .env.example .env

# Editar variables
nano .env  # o tu editor favorito

# Variables críticas:
# - POSTGRES_PASSWORD
# - REDIS_PASSWORD
# - JWT_SECRET_KEY
# - SECRET_KEY
# - MISTRAL_API_KEY
# - GEMINI_API_KEY
```

### Regenerar secretos

```bash
# Generar secret aleatorio
openssl rand -base64 32

# En Python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 🔄 CI/CD

### Rebuild Completo

```bash
# Detener todo
docker-compose down

# Rebuild sin cache
docker-compose build --no-cache

# Levantar nuevamente
docker-compose up -d

# Verificar
docker-compose ps
docker-compose logs -f api
```

### Deploy a Producción

```bash
# 1. Configurar variables de entorno
# Asegurarse de tener .env con valores de producción

# 2. Build de producción
docker-compose -f docker-compose.yml build

# 3. Deploy
docker-compose -f docker-compose.yml up -d

# 4. Verificar
docker-compose ps
curl http://localhost:8000/api/v1/health
```

---

## 🆘 Troubleshooting

### API no inicia

```bash
# Ver logs detallados
docker-compose logs api

# Verificar variables de entorno
docker-compose exec api env | grep -E "(DATABASE|REDIS|LLM)"

# Reiniciar desde cero
docker-compose down
docker-compose up -d --build
```

### PostgreSQL no conecta

```bash
# Verificar que está corriendo
docker-compose ps postgres

# Ver logs
docker-compose logs postgres

# Probar conexión
docker-compose exec postgres pg_isready -U ai_native

# Reiniciar
docker-compose restart postgres
```

### Redis no conecta

```bash
# Verificar que está corriendo
docker-compose ps redis

# Ver logs
docker-compose logs redis

# Probar conexión
docker-compose exec redis redis-cli -a $REDIS_PASSWORD ping

# Reiniciar
docker-compose restart redis
```

### Frontend no carga

```bash
# Verificar que está corriendo
docker-compose ps frontend

# Ver logs
docker-compose logs frontend

# Rebuild frontend
docker-compose up -d --build frontend

# Verificar Nginx
docker-compose exec frontend cat /etc/nginx/conf.d/default.conf
```

---

## 📚 Más Información

- [README.md](README.md) - Documentación principal
- [ESTRUCTURA_PROYECTO.md](ESTRUCTURA_PROYECTO.md) - Guía de estructura
- [docs/setup/](docs/setup/) - Guías de instalación detalladas
- [docs/architecture/](docs/architecture/) - Documentación técnica

---

**Última actualización**: 29 de Diciembre, 2025
