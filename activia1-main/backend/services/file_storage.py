"""
Servicio de almacenamiento de archivos.

Cortez72: Implementación desde metodologia.md
FIX Cortez84 HIGH-SEC-002: Added magic bytes validation

Soporta almacenamiento local (desarrollo) y S3 (producción).
"""

import os
import hashlib
import uuid
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, BinaryIO
from abc import ABC, abstractmethod

from fastapi import UploadFile

logger = logging.getLogger(__name__)


# Configuración
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
ALLOWED_MIME_TYPES = {
    "application/pdf": "pdf",
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/gif": "gif",
}

# FIX Cortez84 HIGH-SEC-002: Magic bytes for file type validation
MAGIC_BYTES = {
    "application/pdf": [b"%PDF"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/gif": [b"GIF87a", b"GIF89a"],
}


def _validate_magic_bytes(content: bytes, mime_type: str) -> bool:
    """
    Validate file content matches declared MIME type using magic bytes.

    FIX Cortez84 HIGH-SEC-002: Prevents file type spoofing.

    Args:
        content: File content bytes
        mime_type: Declared MIME type

    Returns:
        True if magic bytes match, False otherwise
    """
    if mime_type not in MAGIC_BYTES:
        return True  # No magic bytes defined, skip validation

    expected_signatures = MAGIC_BYTES[mime_type]
    for signature in expected_signatures:
        if content.startswith(signature):
            return True

    return False


class StorageProvider(ABC):
    """Interfaz abstracta para proveedores de almacenamiento."""

    @abstractmethod
    async def save(
        self,
        file: BinaryIO,
        filename: str,
        content_type: str,
        path_prefix: str = ""
    ) -> str:
        """Guarda archivo y retorna ruta relativa."""
        pass

    @abstractmethod
    async def delete(self, path: str) -> bool:
        """Elimina archivo por ruta."""
        pass

    @abstractmethod
    async def get_url(self, path: str) -> str:
        """Retorna URL de acceso al archivo."""
        pass

    @abstractmethod
    async def exists(self, path: str) -> bool:
        """Verifica si el archivo existe."""
        pass


class LocalStorageProvider(StorageProvider):
    """Almacenamiento local en disco (desarrollo)."""

    def __init__(self, base_dir: str = UPLOAD_DIR):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save(
        self,
        file: BinaryIO,
        filename: str,
        content_type: str,
        path_prefix: str = ""
    ) -> str:
        # Crear estructura de directorios por fecha
        date_path = datetime.now().strftime("%Y/%m")
        full_prefix = f"{path_prefix}/{date_path}" if path_prefix else date_path

        dir_path = self.base_dir / full_prefix
        dir_path.mkdir(parents=True, exist_ok=True)

        file_path = dir_path / filename

        # Escribir archivo
        content = file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        relative_path = f"{full_prefix}/{filename}"
        logger.info("Archivo guardado: %s", relative_path)
        return relative_path

    async def delete(self, path: str) -> bool:
        file_path = self.base_dir / path
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info("Archivo eliminado: %s", path)
                return True
            return False
        except Exception as e:
            logger.error("Error eliminando archivo: %s", str(e))
            return False

    async def get_url(self, path: str) -> str:
        # En desarrollo, servimos archivos via endpoint
        return f"/api/v1/files/{path}"

    async def exists(self, path: str) -> bool:
        return (self.base_dir / path).exists()


class FileStorageService:
    """Servicio principal de almacenamiento de archivos."""

    def __init__(self, provider: Optional[StorageProvider] = None):
        self.provider = provider or LocalStorageProvider()

    async def upload_file(
        self,
        file: UploadFile,
        path_prefix: str = "apuntes"
    ) -> dict:
        """
        Sube un archivo y retorna metadata.

        Args:
            file: Archivo a subir (FastAPI UploadFile)
            path_prefix: Prefijo de ruta (ej: "apuntes", "ejercicios")

        Returns:
            dict con metadata del archivo guardado

        Raises:
            ValueError: Si el archivo no es válido
        """
        # Validar tipo MIME
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise ValueError(
                f"Tipo de archivo no permitido: {file.content_type}. "
                f"Permitidos: {list(ALLOWED_MIME_TYPES.keys())}"
            )

        # Leer contenido para validar tamaño
        content = await file.read()
        size_mb = len(content) / (1024 * 1024)

        if size_mb > MAX_FILE_SIZE_MB:
            raise ValueError(
                f"Archivo demasiado grande: {size_mb:.1f}MB. "
                f"Maximo: {MAX_FILE_SIZE_MB}MB"
            )

        # FIX Cortez84 HIGH-SEC-002: Validate magic bytes match MIME type
        if not _validate_magic_bytes(content, file.content_type):
            logger.warning(
                "Magic bytes mismatch for file %s (claimed: %s)",
                file.filename, file.content_type
            )
            raise ValueError(
                f"El contenido del archivo no coincide con el tipo declarado: {file.content_type}"
            )

        # Generar nombre único
        extension = ALLOWED_MIME_TYPES[file.content_type]
        unique_filename = f"{uuid.uuid4()}.{extension}"

        # Calcular checksum
        checksum = hashlib.sha256(content).hexdigest()

        # Guardar archivo
        from io import BytesIO
        file_buffer = BytesIO(content)
        relative_path = await self.provider.save(
            file_buffer,
            unique_filename,
            file.content_type,
            path_prefix
        )

        return {
            "nombre_original": file.filename,
            "nombre_almacenado": unique_filename,
            "tipo_archivo": extension,
            "mime_type": file.content_type,
            "tamano_bytes": len(content),
            "ruta_relativa": relative_path,
            "checksum_sha256": checksum,
        }

    async def delete_file(self, path: str) -> bool:
        """Elimina un archivo por ruta."""
        return await self.provider.delete(path)

    async def get_file_url(self, path: str) -> str:
        """Obtiene URL de acceso al archivo."""
        return await self.provider.get_url(path)


# Singleton
_storage_service: Optional[FileStorageService] = None


def get_file_storage() -> FileStorageService:
    """Obtiene instancia del servicio de almacenamiento."""
    global _storage_service
    if _storage_service is None:
        _storage_service = FileStorageService()
    return _storage_service
