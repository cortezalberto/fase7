"""
Session Storage - Redis and memory session management for training.

Cortez46: Extracted from training.py (1,620 lines)
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, List

import redis

logger = logging.getLogger(__name__)

# Configurar Redis para sesiones
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
    logger.info("Redis conectado para sesiones de training")
    USE_REDIS = True
except Exception as e:
    logger.warning("Redis no disponible, usando memoria: %s", e)
    USE_REDIS = False
    redis_client = None


# Fallback en memoria si Redis no está disponible
sesiones_memoria: Dict[str, Dict[str, Any]] = {}


def guardar_sesion(session_id: str, datos: Dict[str, Any]) -> None:
    """Guarda una sesión en Redis o memoria"""
    # Convertir datetime a string para JSON
    datos_serializables = datos.copy()
    if 'inicio' in datos_serializables and isinstance(datos_serializables['inicio'], datetime):
        datos_serializables['inicio'] = datos_serializables['inicio'].isoformat()
    if 'fin_estimado' in datos_serializables and isinstance(datos_serializables['fin_estimado'], datetime):
        datos_serializables['fin_estimado'] = datos_serializables['fin_estimado'].isoformat()

    if USE_REDIS and redis_client:
        try:
            # Guardar en Redis con TTL de 2 horas
            redis_client.setex(
                f"training_session:{session_id}",
                7200,  # 2 horas
                json.dumps(datos_serializables)
            )
            logger.info("Sesión %s guardada en Redis", session_id)
        except Exception as e:
            logger.error("Error guardando en Redis: %s", e, exc_info=True)
            sesiones_memoria[session_id] = datos
    else:
        sesiones_memoria[session_id] = datos


def obtener_sesion(session_id: str) -> Optional[Dict[str, Any]]:
    """Obtiene una sesión de Redis o memoria"""
    if USE_REDIS and redis_client:
        try:
            datos_json = redis_client.get(f"training_session:{session_id}")
            if datos_json:
                datos = json.loads(datos_json)
                # Convertir strings de datetime de vuelta a datetime
                if 'inicio' in datos and isinstance(datos['inicio'], str):
                    datos['inicio'] = datetime.fromisoformat(datos['inicio'])
                if 'fin_estimado' in datos and isinstance(datos['fin_estimado'], str):
                    datos['fin_estimado'] = datetime.fromisoformat(datos['fin_estimado'])
                logger.info("Sesión %s recuperada de Redis", session_id)
                return datos
        except Exception as e:
            logger.error("Error obteniendo de Redis: %s", e, exc_info=True)

    return sesiones_memoria.get(session_id)


def listar_sesiones_activas() -> List[str]:
    """Lista los IDs de sesiones activas"""
    if USE_REDIS and redis_client:
        try:
            keys = redis_client.keys("training_session:*")
            return [k.replace("training_session:", "") for k in keys]
        except Exception as e:
            logger.warning("Redis keys() failed, falling back to in-memory storage: %s", e)
    return list(sesiones_memoria.keys())


def eliminar_sesion(session_id: str) -> bool:
    """Elimina una sesión de Redis o memoria"""
    if USE_REDIS and redis_client:
        try:
            result = redis_client.delete(f"training_session:{session_id}")
            if result:
                logger.info("Sesión %s eliminada de Redis", session_id)
                return True
        except Exception as e:
            logger.error("Error eliminando de Redis: %s", e, exc_info=True)

    if session_id in sesiones_memoria:
        del sesiones_memoria[session_id]
        return True
    return False
