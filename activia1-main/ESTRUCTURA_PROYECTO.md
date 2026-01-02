# 📁 Estructura del Proyecto - AI-Native MVP

## 📂 Organización de Directorios

```
activia1-main/
│
├── 📁 backend/                    # Backend Python/FastAPI
│   ├── agents/                    # Agentes IA especializados
│   ├── api/                       # Endpoints y routers
│   ├── core/                      # Configuración y utilidades
│   ├── database/                  # Conexión y sesión de BD
│   ├── llm/                       # Integración con LLMs
│   ├── models/                    # Modelos SQLAlchemy
│   ├── prompts/                   # Templates de prompts
│   ├── services/                  # Lógica de negocio
│   ├── scripts/                   # Scripts de mantenimiento
│   └── tests/                     # Tests del backend
│       ├── unit/                  # Tests unitarios
│       ├── integration/           # Tests de integración
│       └── e2e/                   # Tests end-to-end
│
├── 📁 frontEnd/                   # Frontend React + Vite
│   ├── src/
│   │   ├── app/                   # Configuración de la app
│   │   ├── components/            # Componentes React
│   │   ├── features/              # Características por módulo
│   │   ├── hooks/                 # Custom hooks
│   │   ├── services/              # Servicios de API
│   │   └── utils/                 # Utilidades
│   ├── e2e/                       # Tests E2E Playwright
│   ├── public/                    # Archivos estáticos
│   └── Dockerfile                 # Dockerfile del frontend
│
├── 📁 infra/                      # Infraestructura y DevOps
│   └── docker/                    # Configuraciones Docker
│       ├── grafana/               # Dashboards y configuración Grafana
│       ├── prometheus/            # Configuración de métricas
│       ├── nginx/                 # Configuración Nginx
│       ├── docker-compose.*.yml   # Compose files alternativos
│       ├── Dockerfile.backend     # Dockerfile alternativo backend
│       └── Dockerfile.frontend    # Dockerfile alternativo frontend
│
├── 📁 docs/                       # Documentación del proyecto
│   ├── architecture/              # Documentos de arquitectura
│   │   ├── ANALISIS_*.md          # Análisis del sistema
│   │   ├── REPORTE_*.md           # Reportes técnicos
│   │   └── RESUMEN_*.md           # Resúmenes ejecutivos
│   ├── setup/                     # Guías de instalación
│   │   ├── INICIO_RAPIDO*.md      # Guías de inicio rápido
│   │   ├── DOCKER_SETUP*.md       # Setup de Docker
│   │   ├── DEPLOY_*.md            # Guías de deployment
│   │   └── CONFIGURAR_*.md        # Configuraciones
│   ├── product/                   # Documentación de producto
│   │   ├── SISTEMA_*.md           # Documentación de sistemas
│   │   ├── INTEGRACION_*.md       # Integraciones
│   │   ├── ENTRENADOR_*.md        # Features del entrenador
│   │   └── GEMINI*.md             # Documentación de Gemini
│   ├── FIX_*.md                   # Fixes y parches
│   ├── CHECKLIST_*.md             # Checklists
│   └── GUIA_*.md                  # Guías generales
│
├── 📁 scripts/                    # Scripts de utilidad
│   ├── maintenance/               # Scripts de mantenimiento
│   ├── *.ps1                      # Scripts PowerShell
│   └── *.sh                       # Scripts Shell
│
├── 📁 tests/                      # Tests globales (deprecated)
├── 📁 uat/                        # User Acceptance Testing
├── 📁 devops/                     # DevOps adicional
├── 📁 examples/                   # Ejemplos de uso
│
├── 📄 docker-compose.yml          # Orquestador principal
├── 📄 Dockerfile                  # Dockerfile principal (backend)
├── 📄 .env                        # Variables de entorno (no commitear)
├── 📄 .env.example                # Template de variables
├── 📄 requirements.txt            # Dependencias Python
├── 📄 Makefile                    # Comandos rápidos
└── 📄 README.md                   # Documentación principal
```

---

## 🎯 Arquitectura del Proyecto

### Backend (Python/FastAPI)

```
backend/
├── api/           → Capa de entrada HTTP (routers, endpoints)
├── core/          → Configuración global, seguridad, logging
├── models/        → Modelos de base de datos (SQLAlchemy)
├── services/      → Lógica de negocio pura
├── llm/           → Integración con LLMs (Factory pattern)
├── agents/        → Agentes IA especializados
└── tests/         → Testing organizado por tipo
```

### Frontend (React + Vite)

```
frontEnd/src/
├── app/           → Configuración global (router, store)
├── features/      → Módulos por característica
│   ├── auth/      → Todo lo de autenticación
│   ├── tutor/     → Chat socrático
│   ├── exercises/ → IDE y resolución
│   └── analytics/ → Dashboards
├── components/    → Componentes reusables
└── services/      → Servicios de API
```

---

## 🚀 Comandos Principales

### Levantar el Proyecto

```bash
# Stack completo
docker-compose up -d

# Con herramientas de debug (pgAdmin + Redis Commander)
docker-compose --profile debug up -d

# Con monitoreo (Prometheus + Grafana)
docker-compose --profile monitoring up -d
```

### Ver Logs

```bash
# Todos los servicios
docker-compose logs -f

# Servicios específicos
docker-compose logs -f api
docker-compose logs -f postgres
docker-compose logs -f redis
```

### Ejecutar Tests

```bash
# Tests del backend
docker-compose exec api pytest backend/tests/

# Tests unitarios
docker-compose exec api pytest backend/tests/unit/

# Tests de integración
docker-compose exec api pytest backend/tests/integration/
```

### Detener el Proyecto

```bash
# Detener servicios (mantiene datos)
docker-compose down

# Detener y eliminar volúmenes (⚠️ DANGER)
docker-compose down -v
```

---

## 📋 Limpieza Realizada

### Archivos Movidos

1. **Documentación (41 archivos .md)** → `docs/`
   - Análisis y reportes → `docs/architecture/`
   - Guías de setup → `docs/setup/`
   - Documentación de producto → `docs/product/`

2. **Tests (35 archivos .py)** → `backend/tests/integration/`
   - Tests de API
   - Tests de LLM
   - Tests de integración

3. **Scripts** → `scripts/`
   - Scripts PowerShell (.ps1)
   - Scripts Shell (.sh)
   - Scripts de mantenimiento

4. **Infraestructura** → `infra/docker/`
   - Configuraciones de Prometheus
   - Configuraciones de Grafana
   - Configuraciones de Nginx
   - Docker compose alternativos

### Archivos Eliminados

- Archivos temporales (.json de salida)
- Carpetas de export (export_output/)
- Archivos Word temporales (~$*.docx)

---

## 🔧 Notas Importantes

### Rutas Actualizadas

Las siguientes rutas fueron actualizadas en `docker-compose.yml`:

- `./prometheus.yml` → `./infra/docker/prometheus/prometheus.yml`
- `./prometheus-alerts.yml` → `./infra/docker/prometheus/prometheus-alerts.yml`
- `./grafana/provisioning` → `./infra/docker/grafana/provisioning`

### Archivos en Raíz

Solo permanecen en la raíz los archivos esenciales:

- `docker-compose.yml` - Orquestador principal
- `Dockerfile` - Dockerfile principal (backend)
- `.env` / `.env.example` - Variables de entorno
- `requirements.txt` - Dependencias Python
- `Makefile` - Comandos rápidos
- `README.md` - Documentación principal

---

## 📚 Documentación Adicional

- **Setup rápido**: [docs/setup/INICIO_RAPIDO.md](docs/setup/INICIO_RAPIDO.md)
- **Configuración Docker**: [docs/setup/DOCKER_SETUP_COMPLETO.md](docs/setup/DOCKER_SETUP_COMPLETO.md)
- **Arquitectura**: [docs/architecture/ANALISIS_PROYECTO_COMPLETO.md](docs/architecture/ANALISIS_PROYECTO_COMPLETO.md)
- **Testing**: [docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md)

---

## ✅ Beneficios de la Nueva Estructura

1. **Organización Clara**: Separación por responsabilidades
2. **Fácil Navegación**: Estructura intuitiva
3. **Escalabilidad**: Preparado para crecer
4. **Mantenibilidad**: Código y documentación separados
5. **Limpieza**: Sin archivos temporales ni duplicados

---

**Última actualización**: 29 de Diciembre, 2025
