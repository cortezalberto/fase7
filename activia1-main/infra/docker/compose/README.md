# Docker Compose Modular Configuration

Cortez44: Modularized from `docker-compose.yml` (606 lines).

This directory contains modular Docker Compose files that can be combined for different deployment scenarios.

## Files

| File | Purpose | Size |
|------|---------|------|
| `docker-compose.base.yml` | Core services (API, Frontend, PostgreSQL, Redis) | ~150 lines |
| `docker-compose.llm.yml` | LLM provider configuration (Mistral, Gemini, OpenAI, Ollama) | ~45 lines |
| `docker-compose.debug.yml` | Debug tools (pgAdmin, Redis Commander) | ~50 lines |
| `docker-compose.monitoring.yml` | Monitoring stack (Prometheus, Grafana) | ~80 lines |
| `docker-compose.ollama.yml` | Local Ollama LLM with GPU support | ~70 lines |

## Usage

### Basic Development Stack

```bash
cd infra/docker/compose
docker-compose -f docker-compose.base.yml up -d
```

### With LLM Configuration

```bash
docker-compose -f docker-compose.base.yml -f docker-compose.llm.yml up -d
```

### With Debug Tools

```bash
docker-compose -f docker-compose.base.yml -f docker-compose.debug.yml up -d
```

### With Monitoring

```bash
docker-compose -f docker-compose.base.yml -f docker-compose.monitoring.yml up -d
```

### With Local Ollama (GPU Required)

```bash
docker-compose -f docker-compose.base.yml -f docker-compose.ollama.yml up -d
```

### Full Stack (Development)

```bash
docker-compose \
  -f docker-compose.base.yml \
  -f docker-compose.llm.yml \
  -f docker-compose.debug.yml \
  -f docker-compose.monitoring.yml \
  up -d
```

## Environment Variables

Required variables (set in `.env` file):

```bash
# Security (Required)
POSTGRES_PASSWORD=your_secure_password
REDIS_PASSWORD=your_secure_password
JWT_SECRET_KEY=your_jwt_secret_key_min_32_chars
SECRET_KEY=your_secret_key_min_32_chars

# LLM (Choose one)
LLM_PROVIDER=mistral  # or gemini, openai, ollama, mock
MISTRAL_API_KEY=your_api_key

# Debug Tools (Optional)
PGADMIN_PASSWORD=your_pgadmin_password
REDIS_COMMANDER_PASSWORD=your_commander_password

# Monitoring (Optional)
GRAFANA_PASSWORD=your_grafana_password
```

## Comparison with Original

| Aspect | Original | Modular |
|--------|----------|---------|
| Lines of code | 606 | ~400 total (split across 5 files) |
| Flexibility | Single file, profiles | Multiple files, composable |
| Maintenance | Edit large file | Edit small, focused files |
| Customization | Limited | Highly customizable |
| Documentation | Comments inline | Separate per file |

## Migration from Original

The original `docker-compose.yml` in the project root still works. To migrate:

1. Use `docker-compose.base.yml` for core services
2. Add override files as needed
3. Update your CI/CD to use the new structure

The original file is kept for backward compatibility.
