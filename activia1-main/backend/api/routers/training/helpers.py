"""
Training Helpers - Utility functions for training.

Cortez46: Extracted from training.py (1,620 lines)
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# FIX Cortez53: Removed HTTPException, status - using custom exceptions
from ...exceptions import SubjectNotFoundError

logger = logging.getLogger(__name__)

# Cargar datos de materias y temas
TRAINING_DATA_PATH = Path(__file__).parent.parent.parent.parent / "data" / "training"


def cargar_materia_datos(codigo_materia: str) -> Dict[str, Any]:
    """Carga los datos de una materia desde JSON"""
    # Mapeo de códigos a nombres de archivo
    mapeo_archivos = {
        "PROG1": "programacion1_temas.json",
        "programacion1": "programacion1_temas.json"
    }

    nombre_archivo = mapeo_archivos.get(codigo_materia.upper())
    if not nombre_archivo:
        nombre_archivo = f"{codigo_materia.lower()}_temas.json"

    archivo = TRAINING_DATA_PATH / nombre_archivo

    if not archivo.exists():
        # FIX Cortez53: Use custom exception
        raise SubjectNotFoundError(codigo_materia)

    with open(archivo, 'r', encoding='utf-8') as f:
        return json.load(f)


def obtener_tema(codigo_materia: str, tema_id: str) -> Optional[Dict[str, Any]]:
    """Obtiene un tema específico de una materia"""
    datos = cargar_materia_datos(codigo_materia)

    for tema in datos['temas']:
        if tema['id'] == tema_id:
            return tema

    return None


# Nombres de lecciones por unit (usado en múltiples endpoints)
NOMBRES_LECCIONES = {
    1: "Estructuras Secuenciales",
    2: "Estructuras Condicionales",
    3: "Bucles y Repetición",
    4: "Funciones",
    5: "Estructuras de Datos",
    6: "Programación Orientada a Objetos",
    7: "Manejo de Archivos"
}
