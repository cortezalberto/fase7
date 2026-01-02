# ============================================================================
# AI-Native MVP - Production Dockerfile
# ============================================================================
# Multi-stage build para optimizar tamaño de imagen y seguridad
#
# Características:
# - Build stage: Compila dependencias
# - Runtime stage: Solo archivos necesarios para ejecución
# - Non-root user para seguridad
# - Health check incluido
# - Dynamic workers based on CPU cores
# - Security hardening (no shell, minimal packages)
#
# Build:
#   docker build -t ai-native-mvp:latest .
#   docker build -t ai-native-mvp:latest --build-arg VERSION=1.0.0 .
#
# Run:
#   docker run -p 8000:8000 --env-file .env ai-native-mvp:latest
# ============================================================================

# ============================================================================
# STAGE 1: Builder - Instalar dependencias
# ============================================================================
FROM python:3.11.9-slim AS builder

# Build arguments for versioning and traceability
ARG VERSION=0.1.0
ARG BUILD_DATE
ARG VCS_REF

# Variables de build
ARG DEBIAN_FRONTEND=noninteractive

# Instalar dependencias del sistema necesarias para compilación
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Crear directorio de trabajo
WORKDIR /app

# Copiar solo requirements.txt primero (para aprovechar cache de Docker)
COPY requirements.txt .

# Instalar dependencias de Python en user directory
# --user instala en ~/.local (sin necesidad de root)
# --no-cache-dir reduce tamaño de imagen
RUN pip install --user --no-cache-dir --upgrade pip && \
    pip install --user --no-cache-dir -r requirements.txt

# ============================================================================
# STAGE 2: Runtime - Imagen final ligera
# ============================================================================
FROM python:3.11.9-slim

# Build arguments (must be redeclared after FROM)
ARG VERSION=0.1.0
ARG BUILD_DATE
ARG VCS_REF

# OCI Image Labels (standard metadata)
LABEL org.opencontainers.image.title="AI-Native MVP Backend" \
      org.opencontainers.image.description="Sistema de Enseñanza-Aprendizaje con IA Generativa" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.vendor="Universidad" \
      org.opencontainers.image.authors="Alberto Cortez <alberto.cortez@example.com>" \
      org.opencontainers.image.source="https://github.com/your-org/ai-native-mvp" \
      org.opencontainers.image.documentation="https://github.com/your-org/ai-native-mvp#readme" \
      org.opencontainers.image.licenses="MIT"

# Variables de entorno para Python y aplicación
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH=/home/appuser/.local/bin:$PATH \
    # Application defaults (can be overridden)
    APP_PORT=8000 \
    APP_WORKERS=0 \
    LOG_LEVEL=info

# Instalar dependencias runtime (solo librerías, no compiladores)
# tini: init system for proper signal handling
# dumb-init alternative: for zombie process reaping
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    tini \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && apt-get autoremove -y

# Crear usuario no-root para seguridad
# UID 1000 es estándar para primer usuario en la mayoría de sistemas
# --no-log-init previene problemas con large UIDs
RUN useradd --no-log-init -m -u 1000 -s /sbin/nologin appuser

# Crear directorio de aplicación
WORKDIR /app

# Copiar dependencias instaladas desde builder al home del appuser
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Copiar código fuente (NO copiar .env - debe proporcionarse via --env-file o docker-compose)
COPY --chown=appuser:appuser backend/ backend/

# Crear directorios necesarios con permisos correctos
RUN mkdir -p /app/data /app/logs && \
    chown -R appuser:appuser /app/data /app/logs

# Copiar script de inicio
COPY --chown=appuser:appuser <<'EOF' /app/start.sh
#!/bin/sh
set -e

# Calculate workers: default to (2 * CPU cores) + 1 if APP_WORKERS is 0 or not set
if [ "${APP_WORKERS:-0}" = "0" ]; then
    CPU_CORES=$(nproc 2>/dev/null || echo 1)
    WORKERS=$((CPU_CORES * 2 + 1))
    # Cap at 8 workers max for memory considerations
    if [ "$WORKERS" -gt 8 ]; then
        WORKERS=8
    fi
else
    WORKERS="${APP_WORKERS}"
fi

echo "Starting uvicorn with ${WORKERS} workers on port ${APP_PORT:-8000}..."

exec uvicorn backend.api.main:app \
    --host 0.0.0.0 \
    --port "${APP_PORT:-8000}" \
    --workers "${WORKERS}" \
    --log-level "${LOG_LEVEL:-info}" \
    --proxy-headers \
    --forwarded-allow-ips='*'
EOF

RUN chmod +x /app/start.sh

# Cambiar a usuario no-root
USER appuser

# Exponer puerto 8000
EXPOSE 8000

# Health check (verifica que el servidor responde)
# Docker marca container como unhealthy si falla 3 veces consecutivas
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${APP_PORT:-8000}/api/v1/health || exit 1

# Use tini as init system for proper signal handling and zombie reaping
ENTRYPOINT ["/usr/bin/tini", "--"]

# Comando de inicio con script dinámico
CMD ["/app/start.sh"]

# ============================================================================
# Notas de Uso
# ============================================================================
#
# Build:
#   docker build -t ai-native-mvp:latest .
#
# Run (standalone):
#   docker run -d \
#     --name ai-native-api \
#     -p 8000:8000 \
#     --env-file .env \
#     ai-native-mvp:latest
#
# Run (con docker-compose):
#   docker-compose up -d
#
# Logs:
#   docker logs -f ai-native-api
#
# Shell interactivo:
#   docker exec -it ai-native-api /bin/bash
#
# Stop:
#   docker stop ai-native-api
#
# ============================================================================