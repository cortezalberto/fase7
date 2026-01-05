"""
Router para gestión de contenido académico.

Cortez72: Implementación desde metodologia.md
Cortez79: Fix - Wrap responses in APIResponse format for frontend compatibility
Cortez80: Fix - Use actual unit count from DB instead of static total_units field

Endpoints para CRUD de materias, unidades, apuntes.
Uso exclusivo de profesores (rol teacher requerido) para modificaciones.
"""

import logging
from datetime import datetime, timezone
from typing import List, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..deps import get_db, get_current_user, require_role
from ..schemas.unidad import (
    UnidadCreate, UnidadUpdate, UnidadResponse, UnidadConApuntesResponse,
    ApuntesCreate, ApuntesUpdate, ApuntesResponse,
    MateriaCreate, MateriaUpdate, MateriaResponse, MateriaConUnidadesResponse
)
from ...database.models import SubjectDB
from ..exceptions import (
    NotFoundError, ValidationError, AuthorizationError
)
from ...database.repositories.unidad_repository import UnidadRepository
from ...database.repositories.profile_repository import SubjectRepository
from ...database.repositories.exercise_repository import ExerciseRepository

logger = logging.getLogger(__name__)


# FIX Cortez79: Helper to wrap responses in APIResponse format for frontend
def success_response(data: Any, message: str = None) -> dict:
    """Wrap data in standard APIResponse format expected by frontend."""
    return {
        "success": True,
        "data": data,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

router = APIRouter(prefix="/academic", tags=["Academic Content"])


# ==================== Materias ====================

@router.get("/materias")
async def listar_materias(
    solo_activas: bool = Query(True, description="Solo materias activas"),
    incluir_unidades: bool = Query(True, description="Incluir unidades"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Lista todas las materias con sus unidades.

    Accesible por profesores y estudiantes.
    FIX Cortez79: Returns APIResponse wrapper for frontend compatibility.
    """
    subject_repo = SubjectRepository(db)
    unidad_repo = UnidadRepository(db)
    exercise_repo = ExerciseRepository(db)

    materias = subject_repo.get_all()
    if solo_activas:
        materias = [m for m in materias if m.is_active]

    result = []
    for materia in materias:
        # FIX Cortez80: Check roles list (not singular role)
        user_roles = current_user.get("roles", [])
        es_profesor = "teacher" in user_roles or "instructor" in user_roles or "admin" in user_roles

        unidades = unidad_repo.get_unidades_by_materia(
            materia.code,
            solo_publicadas=not es_profesor
        )

        # Use actual count from database instead of static total_units field
        actual_unit_count = len(unidades)

        materia_data = MateriaConUnidadesResponse(
            code=materia.code,
            name=materia.name,
            description=materia.description,
            language=materia.language,
            total_units=actual_unit_count,  # FIX: Use real count
            is_active=materia.is_active,
            unidades=[]
        )

        if incluir_unidades:
            for unidad in unidades:
                # Contar ejercicios
                ejercicios = exercise_repo.get_by_language_and_unit(
                    materia.language,
                    unidad.numero
                )

                materia_data.unidades.append({
                    **UnidadResponse.model_validate(unidad).model_dump(),
                    "total_ejercicios": len(ejercicios),
                    "ejercicios_publicados": len([e for e in ejercicios if e.is_active])
                })

        result.append(materia_data)

    # FIX Cortez79: Wrap in APIResponse format
    return success_response([m.model_dump() for m in result])


@router.get("/materias/{materia_code}")
async def obtener_materia(
    materia_code: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Obtiene una materia con todas sus unidades."""
    subject_repo = SubjectRepository(db)
    unidad_repo = UnidadRepository(db)
    exercise_repo = ExerciseRepository(db)

    materia = subject_repo.get_by_code(materia_code)
    if not materia:
        raise NotFoundError("materia", materia_code)

    # FIX Cortez80: Check roles list (not singular role)
    user_roles = current_user.get("roles", [])
    es_profesor = "teacher" in user_roles or "instructor" in user_roles or "admin" in user_roles
    unidades = unidad_repo.get_unidades_by_materia(
        materia.code,
        solo_publicadas=not es_profesor
    )

    unidades_data = []
    for unidad in unidades:
        ejercicios = exercise_repo.get_by_language_and_unit(
            materia.language,
            unidad.numero
        )
        unidades_data.append({
            **UnidadResponse.model_validate(unidad).model_dump(),
            "total_ejercicios": len(ejercicios),
            "ejercicios_publicados": len([e for e in ejercicios if e.is_active])
        })

    # FIX Cortez80: Use actual count from database
    result = MateriaConUnidadesResponse(
        code=materia.code,
        name=materia.name,
        description=materia.description,
        language=materia.language,
        total_units=len(unidades),  # FIX: Use real count
        is_active=materia.is_active,
        unidades=unidades_data
    )
    return success_response(result.model_dump())


@router.post("/materias")
async def crear_materia(
    data: MateriaCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("teacher"))
):
    """
    Crea una nueva materia.

    Solo profesores pueden crear materias.
    """
    subject_repo = SubjectRepository(db)

    # Verificar que no existe materia con mismo código
    existente = subject_repo.get_by_code(data.code)
    if existente:
        raise ValidationError(f"Ya existe la materia con código {data.code}")

    try:
        materia = SubjectDB(
            code=data.code,
            name=data.name,
            description=data.description,
            language=data.language,
            total_units=data.total_units,
            is_active=data.is_active
        )
        created = subject_repo.create(materia)
        logger.info("Materia creada: %s (%s)", data.code, data.name)
        result = MateriaResponse.model_validate(created)
        return success_response(result.model_dump(), "Materia creada exitosamente")
    except Exception as e:
        db.rollback()
        logger.error("Error creando materia: %s", str(e))
        raise


@router.put("/materias/{materia_code}")
async def actualizar_materia(
    materia_code: str,
    data: MateriaUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("teacher"))
):
    """Actualiza una materia existente."""
    subject_repo = SubjectRepository(db)

    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise ValidationError("No hay datos para actualizar")

    try:
        materia = subject_repo.update(materia_code, update_data)
        if not materia:
            raise NotFoundError("materia", materia_code)
        logger.info("Materia actualizada: %s", materia_code)
        result = MateriaResponse.model_validate(materia)
        return success_response(result.model_dump(), "Materia actualizada exitosamente")
    except NotFoundError:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Error actualizando materia: %s", str(e))
        raise


@router.delete("/materias/{materia_code}")
async def eliminar_materia(
    materia_code: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("teacher"))
):
    """
    Elimina una materia.

    ADVERTENCIA: Esto elimina también todas las unidades y ejercicios asociados.
    """
    subject_repo = SubjectRepository(db)

    try:
        if not subject_repo.delete(materia_code):
            raise NotFoundError("materia", materia_code)
        logger.warning("Materia eliminada: %s", materia_code)
        return success_response({"code": materia_code}, "Materia eliminada")
    except NotFoundError:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Error eliminando materia: %s", str(e))
        raise


# ==================== Unidades ====================

@router.post("/unidades", response_model=UnidadResponse)
async def crear_unidad(
    data: UnidadCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("teacher"))
):
    """
    Crea una nueva unidad académica.

    Solo profesores pueden crear unidades.
    """
    unidad_repo = UnidadRepository(db)
    subject_repo = SubjectRepository(db)

    # Verificar que la materia existe
    materia = subject_repo.get_by_code(data.materia_code)
    if not materia:
        raise NotFoundError("materia", data.materia_code)

    # Verificar que no existe unidad con mismo número
    existente = unidad_repo.get_unidad_by_numero(data.materia_code, data.numero)
    if existente:
        raise ValidationError(
            f"Ya existe la unidad {data.numero} en {data.materia_code}"
        )

    try:
        unidad = unidad_repo.create_unidad(
            materia_code=data.materia_code,
            numero=data.numero,
            titulo=data.titulo,
            descripcion=data.descripcion,
            objetivos_aprendizaje=data.objetivos_aprendizaje,
            tiempo_teoria_min=data.tiempo_teoria_min,
            tiempo_practica_min=data.tiempo_practica_min,
            created_by=current_user.get("user_id")
        )
        db.commit()
        logger.info(
            "Unidad creada: %s (materia=%s, numero=%d)",
            unidad.id, data.materia_code, data.numero
        )
        return unidad
    except Exception as e:
        db.rollback()
        logger.error("Error creando unidad: %s", str(e))
        raise


@router.get("/unidades/{unidad_id}", response_model=UnidadConApuntesResponse)
async def obtener_unidad(
    unidad_id: str,
    incluir_apuntes: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Obtiene una unidad con sus apuntes."""
    unidad_repo = UnidadRepository(db)
    unidad = unidad_repo.get_unidad_by_id(unidad_id, load_apuntes=incluir_apuntes)

    if not unidad:
        raise NotFoundError("unidad", unidad_id)

    # Verificar acceso si no está publicada
    if not unidad.esta_publicada and current_user.get("role") != "teacher":
        raise AuthorizationError("No tiene acceso a esta unidad")

    return unidad


@router.put("/unidades/{unidad_id}", response_model=UnidadResponse)
async def actualizar_unidad(
    unidad_id: str,
    data: UnidadUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("teacher"))
):
    """Actualiza una unidad existente."""
    unidad_repo = UnidadRepository(db)

    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise ValidationError("No hay datos para actualizar")

    try:
        unidad = unidad_repo.update_unidad(unidad_id, **update_data)
        if not unidad:
            raise NotFoundError("unidad", unidad_id)
        db.commit()
        return unidad
    except NotFoundError:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Error actualizando unidad: %s", str(e))
        raise


@router.post("/unidades/{unidad_id}/publicar", response_model=UnidadResponse)
async def publicar_unidad(
    unidad_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("teacher"))
):
    """Publica una unidad para que sea visible por estudiantes."""
    unidad_repo = UnidadRepository(db)

    try:
        unidad = unidad_repo.publicar_unidad(unidad_id)
        if not unidad:
            raise NotFoundError("unidad", unidad_id)
        db.commit()
        logger.info("Unidad publicada: %s", unidad_id)
        return unidad
    except NotFoundError:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Error publicando unidad: %s", str(e))
        raise


@router.delete("/unidades/{unidad_id}")
async def eliminar_unidad(
    unidad_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("teacher"))
):
    """Elimina una unidad (soft delete)."""
    unidad_repo = UnidadRepository(db)

    try:
        if not unidad_repo.delete_unidad(unidad_id):
            raise NotFoundError("unidad", unidad_id)
        db.commit()
        return {"message": "Unidad eliminada", "id": unidad_id}
    except NotFoundError:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Error eliminando unidad: %s", str(e))
        raise


# ==================== Apuntes ====================

@router.post("/unidades/{unidad_id}/apuntes", response_model=ApuntesResponse)
async def crear_apuntes(
    unidad_id: str,
    data: ApuntesCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("teacher"))
):
    """Crea apuntes para una unidad."""
    unidad_repo = UnidadRepository(db)

    # Verificar que la unidad existe
    unidad = unidad_repo.get_unidad_by_id(unidad_id)
    if not unidad:
        raise NotFoundError("unidad", unidad_id)

    try:
        apuntes = unidad_repo.create_apuntes(
            unidad_id=unidad_id,
            titulo=data.titulo,
            contenido_markdown=data.contenido_markdown,
            resumen=data.resumen,
            recursos_externos=[r.model_dump() for r in data.recursos_externos],
            tiempo_lectura_min=data.tiempo_lectura_min,
            nivel_dificultad=data.nivel_dificultad,
            created_by=current_user.get("user_id")
        )
        db.commit()
        logger.info("Apuntes creados: %s (unidad=%s)", apuntes.id, unidad_id)
        return apuntes
    except Exception as e:
        db.rollback()
        logger.error("Error creando apuntes: %s", str(e))
        raise


@router.get("/apuntes/{apuntes_id}", response_model=ApuntesResponse)
async def obtener_apuntes(
    apuntes_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Obtiene apuntes por ID."""
    unidad_repo = UnidadRepository(db)
    apuntes = unidad_repo.get_apuntes_by_id(apuntes_id)

    if not apuntes:
        raise NotFoundError("apuntes", apuntes_id)

    # Verificar acceso
    if not apuntes.esta_publicado and current_user.get("role") != "teacher":
        raise AuthorizationError("No tiene acceso a estos apuntes")

    return apuntes


@router.put("/apuntes/{apuntes_id}", response_model=ApuntesResponse)
async def actualizar_apuntes(
    apuntes_id: str,
    data: ApuntesUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("teacher"))
):
    """Actualiza apuntes existentes."""
    unidad_repo = UnidadRepository(db)

    update_data = data.model_dump(exclude_unset=True)
    if "recursos_externos" in update_data and update_data["recursos_externos"]:
        update_data["recursos_externos"] = [
            r.model_dump() if hasattr(r, 'model_dump') else r
            for r in update_data["recursos_externos"]
        ]

    try:
        apuntes = unidad_repo.update_apuntes(apuntes_id, **update_data)
        if not apuntes:
            raise NotFoundError("apuntes", apuntes_id)
        db.commit()
        return apuntes
    except NotFoundError:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Error actualizando apuntes: %s", str(e))
        raise


@router.post("/apuntes/{apuntes_id}/publicar", response_model=ApuntesResponse)
async def publicar_apuntes(
    apuntes_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("teacher"))
):
    """Publica apuntes."""
    unidad_repo = UnidadRepository(db)

    try:
        apuntes = unidad_repo.publicar_apuntes(apuntes_id)
        if not apuntes:
            raise NotFoundError("apuntes", apuntes_id)
        db.commit()
        return apuntes
    except NotFoundError:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Error publicando apuntes: %s", str(e))
        raise


@router.delete("/apuntes/{apuntes_id}")
async def eliminar_apuntes(
    apuntes_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("teacher"))
):
    """Elimina apuntes (soft delete)."""
    unidad_repo = UnidadRepository(db)

    try:
        if not unidad_repo.delete_apuntes(apuntes_id):
            raise NotFoundError("apuntes", apuntes_id)
        db.commit()
        return {"message": "Apuntes eliminados", "id": apuntes_id}
    except NotFoundError:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Error eliminando apuntes: %s", str(e))
        raise
