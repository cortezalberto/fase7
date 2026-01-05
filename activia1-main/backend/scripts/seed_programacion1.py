"""
Script para cargar datos iniciales de Programacion 1.

Cortez72: Implementacion desde metodologia.md

Ejecutar: python -m backend.scripts.seed_programacion1
"""

import logging
from backend.database.config import get_db
from backend.database.repositories.profile_repository import SubjectRepository
from backend.database.repositories.unidad_repository import UnidadRepository

logger = logging.getLogger(__name__)

PROGRAMACION1_DATA = {
    "code": "PROG1",
    "name": "Programacion 1",
    "description": "Introduccion a la programacion con Python",
    "language": "python",
    "total_units": 8,
    "unidades": [
        {
            "numero": 1,
            "titulo": "Variables y Tipos de Datos",
            "descripcion": "Fundamentos de almacenamiento de informacion en Python",
            "objetivos_aprendizaje": [
                "Comprender el concepto de variable como contenedor de datos",
                "Identificar y usar los tipos de datos primitivos (int, float, str, bool)",
                "Aplicar operadores aritmeticos y de asignacion",
                "Realizar conversiones entre tipos de datos"
            ],
            "tiempo_teoria_min": 45,
            "tiempo_practica_min": 90
        },
        {
            "numero": 2,
            "titulo": "Estructuras de Control: Condicionales",
            "descripcion": "Toma de decisiones en programas",
            "objetivos_aprendizaje": [
                "Comprender el flujo de control condicional",
                "Implementar estructuras if, elif, else",
                "Usar operadores de comparacion y logicos",
                "Anidar condicionales de forma efectiva"
            ],
            "tiempo_teoria_min": 60,
            "tiempo_practica_min": 120
        },
        {
            "numero": 3,
            "titulo": "Estructuras de Control: Bucles",
            "descripcion": "Repeticion y automatizacion de tareas",
            "objetivos_aprendizaje": [
                "Comprender el concepto de iteracion",
                "Implementar bucles for y while",
                "Usar range() y enumerate()",
                "Controlar el flujo con break y continue"
            ],
            "tiempo_teoria_min": 60,
            "tiempo_practica_min": 120
        },
        {
            "numero": 4,
            "titulo": "Funciones",
            "descripcion": "Modularizacion y reutilizacion de codigo",
            "objetivos_aprendizaje": [
                "Definir y llamar funciones",
                "Comprender parametros y valores de retorno",
                "Usar argumentos posicionales y con nombre",
                "Aplicar el concepto de scope (alcance)"
            ],
            "tiempo_teoria_min": 90,
            "tiempo_practica_min": 150
        },
        {
            "numero": 5,
            "titulo": "Listas y Tuplas",
            "descripcion": "Colecciones ordenadas de datos",
            "objetivos_aprendizaje": [
                "Crear y manipular listas",
                "Aplicar metodos de listas (append, remove, sort)",
                "Entender la diferencia entre listas y tuplas",
                "Usar slicing para acceder a subconjuntos"
            ],
            "tiempo_teoria_min": 60,
            "tiempo_practica_min": 120
        },
        {
            "numero": 6,
            "titulo": "Diccionarios y Conjuntos",
            "descripcion": "Estructuras de datos clave-valor y conjuntos",
            "objetivos_aprendizaje": [
                "Crear y manipular diccionarios",
                "Iterar sobre claves, valores y items",
                "Comprender el concepto de conjunto (set)",
                "Aplicar operaciones de conjuntos"
            ],
            "tiempo_teoria_min": 60,
            "tiempo_practica_min": 120
        },
        {
            "numero": 7,
            "titulo": "Manejo de Strings",
            "descripcion": "Procesamiento de texto",
            "objetivos_aprendizaje": [
                "Aplicar metodos de string",
                "Usar f-strings para formateo",
                "Validar y transformar texto",
                "Trabajar con expresiones regulares basicas"
            ],
            "tiempo_teoria_min": 45,
            "tiempo_practica_min": 90
        },
        {
            "numero": 8,
            "titulo": "Archivos y Excepciones",
            "descripcion": "Entrada/salida y manejo de errores",
            "objetivos_aprendizaje": [
                "Leer y escribir archivos de texto",
                "Usar context managers (with)",
                "Implementar manejo de excepciones try/except",
                "Crear excepciones personalizadas"
            ],
            "tiempo_teoria_min": 60,
            "tiempo_practica_min": 120
        }
    ]
}


def seed_programacion1():
    """Carga los datos de Programacion 1."""
    db = next(get_db())
    subject_repo = SubjectRepository(db)
    unidad_repo = UnidadRepository(db)

    try:
        # Crear o actualizar materia
        materia = subject_repo.get_by_code(PROGRAMACION1_DATA["code"])
        if not materia:
            materia = subject_repo.create(
                code=PROGRAMACION1_DATA["code"],
                name=PROGRAMACION1_DATA["name"],
                description=PROGRAMACION1_DATA["description"],
                language=PROGRAMACION1_DATA["language"],
                total_units=PROGRAMACION1_DATA["total_units"]
            )
            logger.info("Materia PROG1 creada")
        else:
            logger.info("Materia PROG1 ya existe")

        # Crear unidades
        for unidad_data in PROGRAMACION1_DATA["unidades"]:
            existente = unidad_repo.get_unidad_by_numero(
                PROGRAMACION1_DATA["code"],
                unidad_data["numero"]
            )
            if not existente:
                unidad_repo.create_unidad(
                    materia_code=PROGRAMACION1_DATA["code"],
                    numero=unidad_data["numero"],
                    titulo=unidad_data["titulo"],
                    descripcion=unidad_data["descripcion"],
                    objetivos_aprendizaje=unidad_data["objetivos_aprendizaje"],
                    tiempo_teoria_min=unidad_data["tiempo_teoria_min"],
                    tiempo_practica_min=unidad_data["tiempo_practica_min"],
                    created_by="system"
                )
                logger.info("Unidad %d creada", unidad_data["numero"])
            else:
                logger.info("Unidad %d ya existe", unidad_data["numero"])

        db.commit()
        logger.info("Seed completado exitosamente")

    except Exception as e:
        db.rollback()
        logger.error("Error en seed: %s", e)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_programacion1()
