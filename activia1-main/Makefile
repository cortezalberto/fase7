# ============================================================================
# AI-Native MVP - Makefile
# ============================================================================
# Shortcuts para operaciones comunes de desarrollo y deployment
#
# Uso:
#   make help          # Ver todos los comandos disponibles
#   make dev           # Iniciar development stack
#   make test          # Ejecutar tests
#   make build         # Build Docker image
# ============================================================================

.PHONY: help dev test build deploy clean

# Colores para output
GREEN  := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
RESET  := $(shell tput -Txterm sgr0)

# Variables
DOCKER_IMAGE := ai-native-mvp
DOCKER_TAG := latest
DOCKER_REGISTRY := localhost:5000
COMPOSE_FILE := docker-compose.yml

##@ General

help: ## Mostrar esta ayuda
	@awk 'BEGIN {FS = ":.*##"; printf "\n${GREEN}Uso:${RESET}\n  make ${YELLOW}<comando>${RESET}\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  ${YELLOW}%-15s${RESET} %s\n", $$1, $$2 } /^##@/ { printf "\n${GREEN}%s${RESET}\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Development

dev: ## Iniciar stack de desarrollo (Docker Compose)
	@echo "${GREEN}Iniciando stack de desarrollo...${RESET}"
	docker-compose up -d
	@echo "${GREEN}Stack iniciado. API: http://localhost:8000/docs${RESET}"

dev-debug: ## Iniciar stack de desarrollo con herramientas de debug (pgAdmin, Redis Commander)
	@echo "${GREEN}Iniciando stack de desarrollo con debug tools...${RESET}"
	docker-compose --profile debug up -d
	@echo "${GREEN}Stack iniciado:${RESET}"
	@echo "  - API Swagger:     http://localhost:8000/docs"
	@echo "  - pgAdmin:         http://localhost:5050 (admin@ai-native.local / admin)"
	@echo "  - Redis Commander: http://localhost:8081"

dev-monitoring: ## Iniciar stack completo con monitoreo (Prometheus + Grafana)
	@echo "${GREEN}Iniciando stack con monitoring tools...${RESET}"
	docker-compose --profile monitoring up -d
	@echo "${GREEN}Stack iniciado con monitoreo:${RESET}"
	@echo "  - API Swagger:     http://localhost:8000/docs"
	@echo "  - API Metrics:     http://localhost:8000/metrics"
	@echo "  - Prometheus UI:   http://localhost:9090"
	@echo "  - Grafana UI:      http://localhost:3001 (admin/admin)"

stop: ## Detener stack de desarrollo
	@echo "${YELLOW}Deteniendo stack...${RESET}"
	docker-compose stop

down: ## Detener y eliminar containers (mantiene volúmenes)
	@echo "${YELLOW}Deteniendo y eliminando containers...${RESET}"
	docker-compose down

down-volumes: ## ⚠️ DANGER: Detener y ELIMINAR volúmenes (borra datos!)
	@echo "${YELLOW}⚠️  ADVERTENCIA: Esto ELIMINARÁ todos los datos de PostgreSQL y Redis!${RESET}"
	@read -p "¿Estás seguro? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		echo "${GREEN}Volúmenes eliminados${RESET}"; \
	else \
		echo "${YELLOW}Operación cancelada${RESET}"; \
	fi

logs: ## Ver logs del stack completo
	docker-compose logs -f

logs-api: ## Ver logs solo del API
	docker-compose logs -f api

logs-postgres: ## Ver logs solo de PostgreSQL
	docker-compose logs -f postgres

logs-redis: ## Ver logs solo de Redis
	docker-compose logs -f redis

ps: ## Ver estado de servicios
	docker-compose ps

##@ Testing

test: ## Ejecutar todos los tests con coverage
	@echo "${GREEN}Ejecutando tests...${RESET}"
	pytest tests/ -v --cov --cov-report=term-missing

test-unit: ## Ejecutar solo tests unitarios
	@echo "${GREEN}Ejecutando tests unitarios...${RESET}"
	pytest tests/ -v -m "unit" --cov

test-integration: ## Ejecutar solo tests de integración
	@echo "${GREEN}Ejecutando tests de integración...${RESET}"
	pytest tests/ -v -m "integration" --cov

test-coverage: ## Generar reporte HTML de coverage
	@echo "${GREEN}Generando reporte de coverage...${RESET}"
	pytest tests/ -v --cov --cov-report=html
	@echo "${GREEN}Reporte generado en htmlcov/index.html${RESET}"

##@ Docker

build: ## Build imagen Docker
	@echo "${GREEN}Building Docker image...${RESET}"
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .
	@echo "${GREEN}Imagen creada: $(DOCKER_IMAGE):$(DOCKER_TAG)${RESET}"

build-no-cache: ## Build imagen Docker sin cache (rebuild completo)
	@echo "${GREEN}Building Docker image (no cache)...${RESET}"
	docker build --no-cache -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

push: ## Push imagen a registry
	@echo "${GREEN}Pushing imagen a registry...${RESET}"
	docker tag $(DOCKER_IMAGE):$(DOCKER_TAG) $(DOCKER_REGISTRY)/$(DOCKER_IMAGE):$(DOCKER_TAG)
	docker push $(DOCKER_REGISTRY)/$(DOCKER_IMAGE):$(DOCKER_TAG)

pull: ## Pull imagen desde registry
	@echo "${GREEN}Pulling imagen desde registry...${RESET}"
	docker pull $(DOCKER_REGISTRY)/$(DOCKER_IMAGE):$(DOCKER_TAG)

##@ Database

db-init: ## Inicializar base de datos (solo desarrollo local)
	@echo "${GREEN}Inicializando base de datos...${RESET}"
	python scripts/init_database.py

db-shell: ## Abrir shell de PostgreSQL
	@echo "${GREEN}Abriendo shell de PostgreSQL...${RESET}"
	docker-compose exec postgres psql -U ai_native -d ai_native

db-backup: ## Crear backup de PostgreSQL
	@echo "${GREEN}Creando backup de PostgreSQL...${RESET}"
	docker-compose exec -T postgres pg_dump -U ai_native ai_native > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "${GREEN}Backup creado: backup_$(shell date +%Y%m%d_%H%M%S).sql${RESET}"

db-restore: ## Restaurar backup de PostgreSQL (requiere: make db-restore FILE=backup.sql)
	@echo "${GREEN}Restaurando backup: $(FILE)${RESET}"
	docker-compose exec -T postgres psql -U ai_native -d ai_native < $(FILE)

##@ Redis

redis-cli: ## Abrir Redis CLI
	@echo "${GREEN}Abriendo Redis CLI...${RESET}"
	docker-compose exec redis redis-cli -a "$${REDIS_PASSWORD}"

redis-flush: ## ⚠️ Limpiar TODA la data de Redis (cache, rate limits)
	@echo "${YELLOW}⚠️  Esto limpiará TODO el cache y rate limits!${RESET}"
	@read -p "¿Estás seguro? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose exec redis redis-cli -a "$${REDIS_PASSWORD}" FLUSHALL; \
		echo "${GREEN}Redis limpiado${RESET}"; \
	else \
		echo "${YELLOW}Operación cancelada${RESET}"; \
	fi

redis-info: ## Ver información de Redis
	@echo "${GREEN}Redis Info:${RESET}"
	docker-compose exec redis redis-cli -a "$${REDIS_PASSWORD}" INFO | grep -E "used_memory_human|connected_clients|keys"

##@ Code Quality

lint: ## Ejecutar linter (pylint + flake8)
	@echo "${GREEN}Ejecutando linters...${RESET}"
	pylint backend/ --max-line-length=120 --disable=C0114,C0115,C0116 || true
	flake8 backend/ --max-line-length=120 --ignore=E501,W503

format: ## Formatear código con black
	@echo "${GREEN}Formateando código con black...${RESET}"
	black backend/ tests/

format-check: ## Verificar formato sin modificar
	@echo "${GREEN}Verificando formato...${RESET}"
	black --check --diff backend/ tests/

type-check: ## Verificar type hints con mypy
	@echo "${GREEN}Verificando type hints...${RESET}"
	mypy backend/ --ignore-missing-imports || true

security-check: ## Verificar vulnerabilidades de seguridad
	@echo "${GREEN}Verificando seguridad...${RESET}"
	bandit -r backend/ -ll || true
	safety check -r requirements.txt || true

##@ Utilities

shell: ## Abrir shell en container del API
	@echo "${GREEN}Abriendo shell en container API...${RESET}"
	docker-compose exec api /bin/bash

generate-secrets: ## Generar secrets para .env (JWT_SECRET_KEY, CACHE_SALT)
	@echo "${GREEN}Generando secrets...${RESET}"
	@echo ""
	@echo "${YELLOW}JWT_SECRET_KEY:${RESET}"
	@python -c "import secrets; print(secrets.token_urlsafe(32))"
	@echo ""
	@echo "${YELLOW}CACHE_SALT:${RESET}"
	@python -c "import secrets; print(secrets.token_hex(32))"
	@echo ""
	@echo "${GREEN}Copia estos valores a tu archivo .env${RESET}"

health-check: ## Verificar health de servicios
	@echo "${GREEN}Verificando health de servicios...${RESET}"
	@echo ""
	@echo "${YELLOW}API Health:${RESET}"
	@curl -s http://localhost:8000/api/v1/health | python -m json.tool || echo "❌ API no disponible"
	@echo ""
	@echo "${YELLOW}PostgreSQL:${RESET}"
	@docker-compose exec postgres pg_isready -U ai_native || echo "❌ PostgreSQL no disponible"
	@echo ""
	@echo "${YELLOW}Redis:${RESET}"
	@docker-compose exec redis redis-cli ping || echo "❌ Redis no disponible"

load-test: ## Ejecutar load test básico
	@echo "${GREEN}Ejecutando load test (1000 requests, 50 concurrent)...${RESET}"
	ab -n 1000 -c 50 http://localhost:8000/api/v1/health

##@ Cleanup

clean: ## Limpiar archivos temporales
	@echo "${YELLOW}Limpiando archivos temporales...${RESET}"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".coverage" -delete 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@echo "${GREEN}Archivos temporales eliminados${RESET}"

clean-docker: ## Limpiar imágenes y containers huérfanos
	@echo "${YELLOW}Limpiando Docker...${RESET}"
	docker system prune -f
	@echo "${GREEN}Docker limpiado${RESET}"

##@ Deployment

deploy-staging: ## Deploy a staging environment (Kubernetes)
	@echo "${GREEN}Deploying to staging...${RESET}"
	kubectl apply -f devops/kubernetes/staging/
	kubectl rollout status deployment/ai-native-backend -n ai-native-staging --timeout=300s
	@echo "${GREEN}Staging deployment complete!${RESET}"

deploy-production: ## Deploy a production environment
	@echo "${GREEN}Deploying to production...${RESET}"
	@echo "${YELLOW}⚠️  Production deployment requires manual approval${RESET}"
	@read -p "Are you sure you want to deploy to PRODUCTION? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose -f docker-compose.prod.yml up -d; \
		echo "${GREEN}Production deployment complete!${RESET}"; \
	else \
		echo "${YELLOW}Deployment cancelled${RESET}"; \
	fi

prod-up: ## Start production stack
	@echo "${GREEN}Starting production stack...${RESET}"
	docker-compose -f docker-compose.prod.yml up -d
	@echo "${GREEN}Production stack started${RESET}"

prod-down: ## Stop production stack
	@echo "${YELLOW}Stopping production stack...${RESET}"
	docker-compose -f docker-compose.prod.yml down

prod-logs: ## View production logs
	docker-compose -f docker-compose.prod.yml logs -f

prod-monitoring: ## Start production with monitoring
	@echo "${GREEN}Starting production with monitoring...${RESET}"
	docker-compose -f docker-compose.prod.yml --profile monitoring up -d

##@ CI/CD

ci-test: ## Run tests in CI mode (no coverage report)
	@echo "${GREEN}Running CI tests...${RESET}"
	pytest tests/ -v --cov=backend --cov-report=xml --cov-fail-under=70

ci-lint: ## Run linting in CI mode
	@echo "${GREEN}Running CI linting...${RESET}"
	black --check backend/
	flake8 backend/ --max-line-length=120 --ignore=E501,W503

ci-security: ## Run security checks in CI mode
	@echo "${GREEN}Running CI security checks...${RESET}"
	bandit -r backend/ -f json -o bandit-report.json || true
	safety check -r requirements.txt --json > safety-report.json || true

ci-build: ## Build Docker images for CI
	@echo "${GREEN}Building Docker images for CI...${RESET}"
	docker build -t $(DOCKER_IMAGE)-backend:$(DOCKER_TAG) .
	docker build -t $(DOCKER_IMAGE)-frontend:$(DOCKER_TAG) ./frontEnd

.DEFAULT_GOAL := help