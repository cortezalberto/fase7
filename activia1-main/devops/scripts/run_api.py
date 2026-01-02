"""
Script para ejecutar la API REST del MVP AI-Native

Este script inicia el servidor FastAPI con uvicorn.

Uso:
    python devops/scripts/run_api.py              # Modo desarrollo
    python devops/scripts/run_api.py --production # Modo producción
    python devops/scripts/run_api.py --port 8080  # Puerto personalizado

Nota: Ejecutar desde el directorio raíz del proyecto (activia1-main/)
"""
import sys
import os
import argparse
import multiprocessing

# Agregar directorio raíz al path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT_DIR)


def calculate_workers():
    """Calcula el número óptimo de workers basado en CPU cores."""
    cpu_count = multiprocessing.cpu_count()
    # Fórmula recomendada: (2 * CPU cores) + 1, max 8
    workers = min((2 * cpu_count) + 1, 8)
    return workers


def run_dev_server(port: int = 8000):
    """Ejecuta servidor en modo desarrollo con auto-reload"""
    import uvicorn

    print("=" * 80)
    print("AI-Native MVP - Development Server")
    print("=" * 80)
    print("Starting FastAPI server in development mode...")
    print(f"Server: http://localhost:{port}")
    print(f"Swagger UI: http://localhost:{port}/docs")
    print(f"ReDoc: http://localhost:{port}/redoc")
    print(f"Health: http://localhost:{port}/api/v1/health")
    print("=" * 80)

    uvicorn.run(
        "backend.api.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,  # Auto-reload en cambios
        reload_dirs=[os.path.join(ROOT_DIR, "backend")],
        log_level="info",
        access_log=True,
    )


def run_production_server(port: int = 8000, workers: int = None):
    """Ejecuta servidor en modo producción"""
    import uvicorn

    if workers is None:
        workers = calculate_workers()

    print("=" * 80)
    print("AI-Native MVP - Production Server")
    print("=" * 80)
    print("Starting FastAPI server in production mode...")
    print(f"Server: http://localhost:{port}")
    print(f"Workers: {workers}")
    print("=" * 80)

    uvicorn.run(
        "backend.api.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Sin auto-reload
        workers=workers,
        log_level="warning",
        access_log=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run AI-Native MVP API Server")
    parser.add_argument(
        "--production",
        action="store_true",
        help="Run in production mode (no auto-reload, multiple workers)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run the server on (default: 8000)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of workers for production mode (default: auto)",
    )

    args = parser.parse_args()

    # Cambiar al directorio raíz del proyecto
    os.chdir(ROOT_DIR)

    if args.production:
        run_production_server(port=args.port, workers=args.workers)
    else:
        run_dev_server(port=args.port)
