# 🚀 Quick Start - Proyecto Reorganizado

## ✅ ¿Qué se hizo?

El proyecto **AI-Native MVP** fue completamente reorganizado y limpiado:

- ✅ **76+ archivos en raíz** → **16 archivos esenciales** (reducción del 79%)
- ✅ **41 documentos MD** dispersos → **organizados en docs/**
- ✅ **35 tests Python** sueltos → **organizados en backend/tests/**
- ✅ **Scripts y configs** → **organizados en scripts/ e infra/**
- ✅ **Docker funcionando** sin warnings ni errores
- ✅ **Estructura profesional** lista para producción

---

## 🎯 Inicio Rápido (30 segundos)

### 1. Levantar el Proyecto

```bash
docker-compose up -d
```

### 2. Verificar Estado

```bash
docker-compose ps
```

Deberías ver algo como:
```
ai-native-api        Up (healthy)      0.0.0.0:8000->8000/tcp
ai-native-frontend   Up                0.0.0.0:3000->80/tcp
ai-native-postgres   Up (healthy)      0.0.0.0:5433->5432/tcp
ai-native-redis      Up (healthy)      0.0.0.0:6379->6379/tcp
```

### 3. Probar la API

Abre en tu navegador: http://localhost:8000/docs

O desde la terminal:
```bash
curl http://localhost:8000/api/v1/health
```

### 4. Ver el Frontend

Abre en tu navegador: http://localhost:3000

---

## 📁 Estructura Nueva

```
activia1-main/
├── backend/              ← Código del backend
│   └── tests/           ← TODOS los tests aquí
├── frontEnd/            ← Código del frontend
├── docs/                ← TODA la documentación aquí
│   ├── architecture/
│   ├── setup/
│   └── product/
├── infra/               ← Configs de Docker, Prometheus, Grafana
├── scripts/             ← Scripts de utilidad
└── docker-compose.yml   ← Orquestador principal
```

---

## 📚 Documentación Importante

### Para Empezar

- **README.md** - Documentación principal del proyecto
- **ESTRUCTURA_PROYECTO.md** - Guía completa de la estructura
- **COMANDOS_RAPIDOS_ACTUALIZADOS.md** - Todos los comandos útiles

### Guías de Setup

- **docs/setup/INICIO_RAPIDO.md** - Guía rápida de inicio
- **docs/setup/DOCKER_SETUP_COMPLETO.md** - Setup completo de Docker
- **docs/setup/CONFIGURAR_GEMINI.md** - Configurar Gemini API

### Arquitectura y Análisis

- **docs/architecture/ANALISIS_PROYECTO_COMPLETO.md**
- **docs/architecture/RESUMEN_EJECUTIVO.md**

---

## 🔧 Comandos Más Usados

### Docker

```bash
# Iniciar
docker-compose up -d

# Ver logs
docker-compose logs -f api

# Ver estado
docker-compose ps

# Reiniciar un servicio
docker-compose restart api

# Detener todo
docker-compose down

# Rebuild
docker-compose up -d --build
```

### Tests

```bash
# Ejecutar todos los tests
docker-compose exec api pytest backend/tests/

# Solo tests de integración
docker-compose exec api pytest backend/tests/integration/

# Con verbose
docker-compose exec api pytest -v backend/tests/
```

### Debugging

```bash
# Acceder al contenedor API
docker-compose exec api bash

# Ver salud de PostgreSQL
docker-compose exec postgres pg_isready -U ai_native

# Ver Redis
docker-compose exec redis redis-cli -a $REDIS_PASSWORD ping
```

---

## 🎨 Mejoras Realizadas

### 1. Raíz Limpia
Solo archivos esenciales: docker-compose.yml, Dockerfile, README.md, .env, requirements.txt, etc.

### 2. Documentación Organizada
Todo en `docs/` separado por categorías:
- **architecture/** - Análisis técnicos
- **setup/** - Guías de instalación
- **product/** - Docs de producto

### 3. Tests Centralizados
Todo en `backend/tests/`:
- **integration/** - 37 tests de integración
- **unit/** - Tests unitarios (preparado)
- **e2e/** - Tests E2E (preparado)

### 4. Infraestructura Separada
Configs de DevOps en `infra/docker/`:
- Prometheus
- Grafana
- Nginx
- Docker composes alternativos

### 5. Sin Archivos Temporales
Eliminados todos los archivos temporales, exports y basura

---

## ✨ Beneficios

1. **Navegación Fácil** - Estructura clara e intuitiva
2. **Mantenible** - Código y docs separados
3. **Escalable** - Preparado para crecer
4. **Profesional** - Como un proyecto de producción
5. **Rápido** - Mejor performance de Git/IDE

---

## 🆘 ¿Problemas?

### API no inicia
```bash
docker-compose logs api
docker-compose restart api
```

### PostgreSQL no conecta
```bash
docker-compose exec postgres pg_isready -U ai_native
docker-compose restart postgres
```

### Redis no conecta
```bash
docker-compose exec redis redis-cli -a $REDIS_PASSWORD ping
docker-compose restart redis
```

### Rebuild completo
```bash
docker-compose down
docker-compose up -d --build
```

---

## 📞 Más Ayuda

Ver documentación completa:
- [ESTRUCTURA_PROYECTO.md](ESTRUCTURA_PROYECTO.md)
- [RESUMEN_LIMPIEZA.md](RESUMEN_LIMPIEZA.md)
- [COMANDOS_RAPIDOS_ACTUALIZADOS.md](COMANDOS_RAPIDOS_ACTUALIZADOS.md)

---

## ✅ Checklist Post-Reorganización

- [x] Archivos organizados por responsabilidad
- [x] Docker funcionando sin errores
- [x] API respondiendo correctamente
- [x] Frontend accesible
- [x] Tests organizados
- [x] Documentación centralizada
- [x] Configs de infra separadas
- [x] Sin archivos temporales
- [x] Estructura profesional
- [x] README actualizado

---

**¡Todo listo para trabajar! 🚀**

*Última actualización: 29 de Diciembre, 2025*
