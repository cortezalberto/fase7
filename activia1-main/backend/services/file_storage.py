"""
Servicio de almacenamiento de archivos.

Cortez72: Implementación desde metodologia.md
FIX Cortez84 HIGH-SEC-002: Added magic bytes validation
FIX Cortez88 CRIT-004: Added path traversal protection

Soporta almacenamiento local (desarrollo) y S3 (producción).
"""

import os
import hashlib
import uuid
import logging
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, BinaryIO
from abc import ABC, abstractmethod

from fastapi import UploadFile

logger = logging.getLogger(__name__)


# Cortez88: Path validation patterns
# Only allow alphanumeric, underscore, hyphen, dot, and forward slash
SAFE_PATH_PATTERN = re.compile(r'^[a-zA-Z0-9_\-./]+$')


def _validate_path_component(path: str, component_name: str = "path") -> None:
    """
    Validate a path component is safe and doesn't contain traversal sequences.

    FIX Cortez88 CRIT-004: Prevents path traversal attacks.

    Args:
        path: Path component to validate
        component_name: Name for error messages

    Raises:
        ValueError: If path contains dangerous patterns
    """
    if not path:
        return  # Empty paths are OK (will use defaults)

    # Check for path traversal sequences
    if '..' in path:
        logger.warning(
            "Path traversal attempt blocked: %s contained '..'",
            component_name
        )
        raise ValueError(f"Invalid {component_name}: path traversal not allowed")

    # Check for absolute paths
    if path.startswith('/') or (len(path) > 1 and path[1] == ':'):
        logger.warning(
            "Absolute path attempt blocked: %s started with root",
            component_name
        )
        raise ValueError(f"Invalid {component_name}: absolute paths not allowed")

    # Check for safe characters only
    if not SAFE_PATH_PATTERN.match(path):
        logger.warning(
            "Invalid characters in %s: %s",
            component_name, path[:50]
        )
        raise ValueError(
            f"Invalid {component_name}: only alphanumeric, underscore, hyphen, "
            f"dot, and forward slash allowed"
        )


def _ensure_path_within_base(base_dir: Path, full_path: Path) -> None:
    """
    Ensure the resolved path is within the base directory.

    FIX Cortez88 CRIT-004: Secondary check using path resolution.

    Args:
        base_dir: Base directory that should contain all files
        full_path: Full path to validate

    Raises:
        ValueError: If path escapes base directory
    """
    try:
        resolved_base = base_dir.resolve()
        resolved_path = full_path.resolve()

        # Check if resolved path is within base
        if not str(resolved_path).startswith(str(resolved_base)):
            logger.error(
                "Path escape attempt: %s is not within %s",
                resolved_path, resolved_base
            )
            raise ValueError("Path escapes allowed directory")
    except (OSError, ValueError) as e:
        logger.error("Path resolution failed: %s", str(e))
        raise ValueError(f"Invalid path: {str(e)}")


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
        # Cortez88: Validate path_prefix and filename for path traversal
        _validate_path_component(path_prefix, "path_prefix")
        _validate_path_component(filename, "filename")

        # Crear estructura de directorios por fecha
        date_path = datetime.now().strftime("%Y/%m")
        full_prefix = f"{path_prefix}/{date_path}" if path_prefix else date_path

        dir_path = self.base_dir / full_prefix
        file_path = dir_path / filename

        # Cortez88: Ensure final path is within base_dir
        _ensure_path_within_base(self.base_dir, file_path)

        dir_path.mkdir(parents=True, exist_ok=True)

        # Escribir archivo
        content = file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        relative_path = f"{full_prefix}/{filename}"
        logger.info("Archivo guardado: %s", relative_path)
        return relative_path

    async def delete(self, path: str) -> bool:
        # Cortez88: Validate path for traversal attacks
        _validate_path_component(path, "path")

        file_path = self.base_dir / path

        # Cortez88: Ensure path is within base_dir
        _ensure_path_within_base(self.base_dir, file_path)

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
        # Cortez88: Validate path
        _validate_path_component(path, "path")
        # En desarrollo, servimos archivos via endpoint
        return f"/api/v1/files/{path}"

    async def exists(self, path: str) -> bool:
        # Cortez88: Validate path for traversal attacks
        _validate_path_component(path, "path")
        file_path = self.base_dir / path
        _ensure_path_within_base(self.base_dir, file_path)
        return file_path.exists()


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
        # Cortez88: Validate path_prefix for traversal attacks
        _validate_path_component(path_prefix, "path_prefix")

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


# Singleton with thread safety (FIX Cortez91 HIGH-S01)
import threading
_storage_service: Optional[FileStorageService] = None
_storage_lock = threading.Lock()


def get_file_storage() -> FileStorageService:
    """
    Obtiene instancia del servicio de almacenamiento.

    FIX Cortez91 HIGH-S01: Added thread safety with double-checked locking pattern.
    """
    global _storage_service
    if _storage_service is None:
        with _storage_lock:
            if _storage_service is None:
                _storage_service = FileStorageService()
    return _storage_service
