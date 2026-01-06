# ============================================================================
# AI-Native MVP - Frontend Dockerfile
# ============================================================================
# Build optimizado para React 19 + Vite con TypeScript
# Updated: Cortez94 - January 2026
# ============================================================================

# Build arguments for versioning
ARG NODE_VERSION=22
ARG NGINX_VERSION=1.27

# Stage 1: Build
FROM node:${NODE_VERSION}-alpine AS builder

# Build args for metadata
ARG VERSION=2.0.0
ARG BUILD_DATE
ARG VCS_REF

WORKDIR /app

# Install build dependencies for native modules
RUN apk add --no-cache python3 make g++

# Copiar package files primero para aprovechar cache de Docker
COPY package*.json ./

# Instalar dependencias con cache mount para builds más rápidos
RUN --mount=type=cache,target=/root/.npm \
    npm ci --prefer-offline

# Copiar el resto del código
COPY . .

# Build de producción con optimizaciones
ENV NODE_ENV=production
RUN npm run build

# Stage 2: Production
FROM nginx:${NGINX_VERSION}-alpine

# OCI Image Labels
LABEL org.opencontainers.image.title="AI-Native MVP Frontend" \
      org.opencontainers.image.description="React 19 + Vite Frontend" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.vendor="Universidad" \
      org.opencontainers.image.authors="Alberto Cortez"

# Create non-root user for nginx (uid 101 is nginx default)
RUN chown -R nginx:nginx /var/cache/nginx /var/log/nginx /etc/nginx/conf.d && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

# Copiar archivos compilados desde builder
COPY --from=builder --chown=nginx:nginx /app/dist /usr/share/nginx/html

# Copiar configuración de nginx personalizada
COPY --chown=nginx:nginx nginx.conf /etc/nginx/conf.d/default.conf

# Switch to non-root user
USER nginx

# Exponer puerto
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://127.0.0.1/health || exit 1

# Nginx se ejecuta automáticamente como comando por defecto
CMD ["nginx", "-g", "daemon off;"]
