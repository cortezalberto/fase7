"""
Router para gestión de archivos adjuntos.

Cortez72: Implementación desde metodologia.md

Endpoints para subir, descargar y eliminar archivos PDF y otros.
"""

import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, UploadFile, File, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..deps import get_db, get_current_user, require_role
from ..exceptions import (
    FileNotFoundError as FileNotFoundAPIError,
    FileUploadError,
    FileAccessDeniedError,
    FileStorageError,
)
# FIX Cortez73 (MED-001): Add pagination constants
from ..config import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, MIN_PAGE_SIZE
from ...database.models.unidad import ArchivoAdjuntoDB
from ...services.file_storage import get_file_storage, UPLOAD_DIR

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["Archivos"])


# ==================== Schemas ====================

class ArchivoUploadResponse(BaseModel):
    """Respuesta al subir un archivo."""
    id: str
    nombre_original: str
    tipo_archivo: str
    tamano_bytes: int
    ruta_relativa: str
    url: str


class ArchivoListResponse(BaseModel):
    """Archivo en lista."""
    id: str
    nombre_original: str
    tipo_archivo: str
    tamano_bytes: int
    descripcion: Optional[str]
    orden: int
    url: str


# ==================== Endpoints ====================

@router.post(
    "/upload/apuntes/{apuntes_id}",
    response_model=ArchivoUploadResponse,
    summary="Subir archivo a apuntes"
)
async def upload_file_to_apuntes(
    apuntes_id: UUID,
    file: UploadFile = File(...),
    descripcion: Optional[str] = Query(None, max_length=500),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("teacher"))
):
    """
    Sube un archivo PDF o imagen a un apunte específico.

    Requiere rol de profesor.
    """
    storage = get_file_storage()

    try:
        # Subir archivo
        file_metadata = await storage.upload_file(file, path_prefix="apuntes")

        # Obtener orden máximo actual
        max_orden = db.query(ArchivoAdjuntoDB).filter(
            ArchivoAdjuntoDB.apuntes_id == str(apuntes_id),
            ArchivoAdjuntoDB.deleted_at.is_(None)
        ).count()

        # Crear registro en DB
        archivo_db = ArchivoAdjuntoDB(
            apuntes_id=str(apuntes_id),
            nombre_original=file_metadata["nombre_original"],
            nombre_almacenado=file_metadata["nombre_almacenado"],
            tipo_archivo=file_metadata["tipo_archivo"],
            mime_type=file_metadata["mime_type"],
            tamano_bytes=file_metadata["tamano_bytes"],
            ruta_relativa=file_metadata["ruta_relativa"],
            checksum_sha256=file_metadata["checksum_sha256"],
            descripcion=descripcion,
            orden=max_orden + 1
        )

        db.add(archivo_db)
        db.commit()
        db.refresh(archivo_db)

        url = await storage.get_file_url(file_metadata["ruta_relativa"])

        return ArchivoUploadResponse(
            id=archivo_db.id,
            nombre_original=archivo_db.nombre_original,
            tipo_archivo=archivo_db.tipo_archivo,
            tamano_bytes=archivo_db.tamano_bytes,
            ruta_relativa=archivo_db.ruta_relativa,
            url=url
        )

    except ValueError as e:
        raise FileUploadError(details=str(e))
    except Exception as e:
        db.rollback()
        logger.error("Error subiendo archivo: %s", str(e), exc_info=True)
        raise FileStorageError(operation="upload", details=str(e))


@router.post(
    "/upload/unidad/{unidad_id}",
    response_model=ArchivoUploadResponse,
    summary="Subir archivo a unidad"
)
async def upload_file_to_unidad(
    unidad_id: UUID,
    file: UploadFile = File(...),
    descripcion: Optional[str] = Query(None, max_length=500),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("teacher"))
):
    """
    Sube un archivo PDF o imagen directamente a una unidad.

    Útil para material complementario no asociado a apuntes específicos.
    """
    storage = get_file_storage()

    try:
        file_metadata = await storage.upload_file(file, path_prefix="unidades")

        max_orden = db.query(ArchivoAdjuntoDB).filter(
            ArchivoAdjuntoDB.unidad_id == str(unidad_id),
            ArchivoAdjuntoDB.deleted_at.is_(None)
        ).count()

        archivo_db = ArchivoAdjuntoDB(
            unidad_id=str(unidad_id),
            nombre_original=file_metadata["nombre_original"],
            nombre_almacenado=file_metadata["nombre_almacenado"],
            tipo_archivo=file_metadata["tipo_archivo"],
            mime_type=file_metadata["mime_type"],
            tamano_bytes=file_metadata["tamano_bytes"],
            ruta_relativa=file_metadata["ruta_relativa"],
            checksum_sha256=file_metadata["checksum_sha256"],
            descripcion=descripcion,
            orden=max_orden + 1
        )

        db.add(archivo_db)
        db.commit()
        db.refresh(archivo_db)

        url = await storage.get_file_url(file_metadata["ruta_relativa"])

        return ArchivoUploadResponse(
            id=archivo_db.id,
            nombre_original=archivo_db.nombre_original,
            tipo_archivo=archivo_db.tipo_archivo,
            tamano_bytes=archivo_db.tamano_bytes,
            ruta_relativa=archivo_db.ruta_relativa,
            url=url
        )

    except ValueError as e:
        raise FileUploadError(details=str(e))
    except Exception as e:
        db.rollback()
        logger.error("Error subiendo archivo: %s", str(e), exc_info=True)
        raise FileStorageError(operation="upload", details=str(e))


@router.get(
    "/apuntes/{apuntes_id}",
    response_model=List[ArchivoListResponse],
    summary="Listar archivos de apuntes"
)
async def list_files_by_apuntes(
    apuntes_id: UUID,
    # FIX Cortez73 (MED-001): Add pagination parameters
    page: int = Query(1, ge=MIN_PAGE_SIZE, description="Número de página"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=MIN_PAGE_SIZE, le=MAX_PAGE_SIZE, description="Elementos por página"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Lista todos los archivos adjuntos de un apunte.

    FIX Cortez73 (MED-001): Added pagination support
    """
    storage = get_file_storage()

    # FIX Cortez73 (MED-001): Apply pagination at query level
    offset = (page - 1) * page_size
    archivos = db.query(ArchivoAdjuntoDB).filter(
        ArchivoAdjuntoDB.apuntes_id == str(apuntes_id),
        ArchivoAdjuntoDB.deleted_at.is_(None)
    ).order_by(ArchivoAdjuntoDB.orden).offset(offset).limit(page_size).all()

    result = []
    for archivo in archivos:
        url = await storage.get_file_url(archivo.ruta_relativa)
        result.append(ArchivoListResponse(
            id=archivo.id,
            nombre_original=archivo.nombre_original,
            tipo_archivo=archivo.tipo_archivo,
            tamano_bytes=archivo.tamano_bytes,
            descripcion=archivo.descripcion,
            orden=archivo.orden,
            url=url
        ))

    return result


@router.get(
    "/unidad/{unidad_id}",
    response_model=List[ArchivoListResponse],
    summary="Listar archivos de unidad"
)
async def list_files_by_unidad(
    unidad_id: UUID,
    # FIX Cortez73 (MED-001): Add pagination parameters
    page: int = Query(1, ge=MIN_PAGE_SIZE, description="Número de página"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=MIN_PAGE_SIZE, le=MAX_PAGE_SIZE, description="Elementos por página"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Lista todos los archivos adjuntos de una unidad.

    FIX Cortez73 (MED-001): Added pagination support
    """
    storage = get_file_storage()

    # FIX Cortez73 (MED-001): Apply pagination at query level
    offset = (page - 1) * page_size
    archivos = db.query(ArchivoAdjuntoDB).filter(
        ArchivoAdjuntoDB.unidad_id == str(unidad_id),
        ArchivoAdjuntoDB.deleted_at.is_(None)
    ).order_by(ArchivoAdjuntoDB.orden).offset(offset).limit(page_size).all()

    result = []
    for archivo in archivos:
        url = await storage.get_file_url(archivo.ruta_relativa)
        result.append(ArchivoListResponse(
            id=archivo.id,
            nombre_original=archivo.nombre_original,
            tipo_archivo=archivo.tipo_archivo,
            tamano_bytes=archivo.tamano_bytes,
            descripcion=archivo.descripcion,
            orden=archivo.orden,
            url=url
        ))

    return result


@router.get(
    "/download/{path:path}",
    summary="Descargar archivo"
)
async def download_file(
    path: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Descarga un archivo por su ruta.

    La ruta incluye prefijo y fecha: apuntes/2026/01/abc123.pdf
    """
    # FIX Cortez74 (CRIT-SEC-002): Enhanced path traversal protection
    # Reject paths with directory traversal sequences BEFORE path construction
    if ".." in path or path.startswith("/") or path.startswith("\\"):
        logger.warning(
            "Path traversal attempt detected: %s",
            path[:100],
            extra={"user_id": current_user.get("user_id")}
        )
        raise FileAccessDeniedError(path=path)

    # Also reject backslashes (Windows path separator) for cross-platform safety
    sanitized_path = path.replace("\\", "/")

    # Reject paths with null bytes (can bypass path checks in some systems)
    if "\x00" in sanitized_path:
        raise FileAccessDeniedError(path=path)

    file_path = Path(UPLOAD_DIR) / sanitized_path

    # FIX Cortez74: Use strict resolve to detect symlink attacks
    try:
        resolved_path = file_path.resolve(strict=True)
    except FileNotFoundError:
        raise FileNotFoundAPIError(path=path)
    except Exception as e:
        logger.error("Path resolution error: %s", str(e), extra={"path": path[:100]})
        raise FileAccessDeniedError(path=path)

    # Verify the resolved path is within uploads directory
    upload_dir_resolved = Path(UPLOAD_DIR).resolve()
    try:
        resolved_path.relative_to(upload_dir_resolved)
    except ValueError:
        logger.warning(
            "Path escape attempt detected: %s resolved to %s",
            path[:100], str(resolved_path)[:100],
            extra={"user_id": current_user.get("user_id")}
        )
        raise FileAccessDeniedError(path=path)

    return FileResponse(
        path=str(resolved_path),
        filename=resolved_path.name,
        media_type="application/octet-stream"
    )


@router.delete(
    "/{archivo_id}",
    summary="Eliminar archivo"
)
async def delete_file(
    archivo_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("teacher"))
):
    """
    Elimina un archivo adjunto (soft delete).

    También elimina el archivo físico del almacenamiento.
    """
    archivo = db.query(ArchivoAdjuntoDB).filter(
        ArchivoAdjuntoDB.id == str(archivo_id),
        ArchivoAdjuntoDB.deleted_at.is_(None)
    ).first()

    if not archivo:
        raise FileNotFoundAPIError(file_id=str(archivo_id))

    storage = get_file_storage()

    # Eliminar archivo físico
    await storage.delete_file(archivo.ruta_relativa)

    # Soft delete en DB
    archivo.deleted_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": "Archivo eliminado", "id": str(archivo_id)}
