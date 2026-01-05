"""
Schemas Pydantic para Unidades y Apuntes académicos.

Cortez72: Implementación desde metodologia.md
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ==================== Recursos ====================

class RecursoExterno(BaseModel):
    """Recurso externo (video, PDF, link)."""
    url: str
    titulo: str
    tipo: str = Field(default="link", pattern="^(video|pdf|link)$")


# ==================== Apuntes ====================

class ApuntesCreate(BaseModel):
    """Request para crear apuntes."""
    titulo: str = Field(..., min_length=3, max_length=300)
    contenido_markdown: str = Field(..., min_length=10)
    resumen: Optional[str] = None
    recursos_externos: List[RecursoExterno] = []
    tiempo_lectura_min: int = Field(default=15, ge=1, le=180)
    nivel_dificultad: str = Field(default="basico", pattern="^(basico|intermedio|avanzado)$")


class ApuntesUpdate(BaseModel):
    """Request para actualizar apuntes."""
    titulo: Optional[str] = Field(None, min_length=3, max_length=300)
    contenido_markdown: Optional[str] = Field(None, min_length=10)
    resumen: Optional[str] = None
    recursos_externos: Optional[List[RecursoExterno]] = None
    tiempo_lectura_min: Optional[int] = Field(None, ge=1, le=180)
    nivel_dificultad: Optional[str] = Field(None, pattern="^(basico|intermedio|avanzado)$")


class ApuntesResponse(BaseModel):
    """Response de apuntes."""
    id: str
    unidad_id: str
    titulo: str
    contenido_markdown: str
    resumen: Optional[str]
    recursos_externos: List[RecursoExterno]
    tiempo_lectura_min: int
    nivel_dificultad: str
    orden: int
    esta_publicado: bool
    created_by: Optional[str]
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Unidades ====================

class UnidadCreate(BaseModel):
    """Request para crear una unidad."""
    materia_code: str = Field(..., min_length=2, max_length=50)
    numero: int = Field(..., ge=1)
    titulo: str = Field(..., min_length=3, max_length=200)
    descripcion: Optional[str] = None
    objetivos_aprendizaje: List[str] = []
    tiempo_teoria_min: int = Field(default=60, ge=0)
    tiempo_practica_min: int = Field(default=120, ge=0)


class UnidadUpdate(BaseModel):
    """Request para actualizar una unidad."""
    titulo: Optional[str] = Field(None, min_length=3, max_length=200)
    descripcion: Optional[str] = None
    objetivos_aprendizaje: Optional[List[str]] = None
    tiempo_teoria_min: Optional[int] = Field(None, ge=0)
    tiempo_practica_min: Optional[int] = Field(None, ge=0)
    requiere_unidad_anterior: Optional[bool] = None


class UnidadResponse(BaseModel):
    """Response de unidad (sin apuntes)."""
    id: str
    materia_code: str
    numero: int
    titulo: str
    descripcion: Optional[str]
    objetivos_aprendizaje: List[str]
    tiempo_teoria_min: int
    tiempo_practica_min: int
    orden: int
    esta_publicada: bool
    requiere_unidad_anterior: bool
    created_by: Optional[str]
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UnidadConApuntesResponse(UnidadResponse):
    """Response de unidad con sus apuntes."""
    apuntes: List[ApuntesResponse] = []


class UnidadConEjerciciosResponse(UnidadResponse):
    """Response de unidad con conteo de ejercicios."""
    total_ejercicios: int = 0
    ejercicios_publicados: int = 0


# ==================== Materias ====================

class MateriaCreate(BaseModel):
    """Request para crear una materia."""
    code: str = Field(..., min_length=2, max_length=50, pattern="^[A-Z0-9_]+$")
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    language: str = Field(..., pattern="^(python|java)$")
    total_units: int = Field(default=0, ge=0)
    is_active: bool = True


class MateriaUpdate(BaseModel):
    """Request para actualizar una materia."""
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = None
    total_units: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class MateriaResponse(BaseModel):
    """Response de materia sin unidades."""
    code: str
    name: str
    description: Optional[str]
    language: str
    total_units: int
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MateriaConUnidadesResponse(BaseModel):
    """Response de materia con todas sus unidades."""
    code: str
    name: str
    description: Optional[str]
    language: str
    total_units: int
    is_active: bool
    unidades: List[UnidadConEjerciciosResponse] = []

    class Config:
        from_attributes = True


# ==================== Archivos Adjuntos ====================

class ArchivoAdjuntoResponse(BaseModel):
    """Response de archivo adjunto."""
    id: str
    nombre_original: str
    tipo_archivo: str
    mime_type: str
    tamano_bytes: int
    descripcion: Optional[str]
    orden: int
    created_at: datetime

    class Config:
        from_attributes = True


class ArchivoUploadResponse(BaseModel):
    """Response después de subir un archivo."""
    id: str
    nombre_original: str
    tipo_archivo: str
    tamano_bytes: int
    url: str
