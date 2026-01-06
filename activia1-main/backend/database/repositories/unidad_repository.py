"""
Unidad Repository - Operaciones de base de datos para Unidades y Apuntes.

Cortez72: Implementación desde metodologia.md

Provee:
- CRUD para UnidadDB
- CRUD para ApuntesDB
- Operaciones de publicación y ordenamiento
"""

from typing import List, Optional
from datetime import datetime, timezone
import logging

from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import SQLAlchemyError

from .base import BaseRepository
from ..models.unidad import UnidadDB, ApuntesDB, ArchivoAdjuntoDB

logger = logging.getLogger(__name__)


class UnidadRepository(BaseRepository):
    """Repositorio para operaciones de Unidades académicas."""

    def __init__(self, db: Session):
        super().__init__(db)

    # ==================== Unidades ====================

    def create_unidad(
        self,
        materia_code: str,
        numero: int,
        titulo: str,
        descripcion: Optional[str] = None,
        objetivos_aprendizaje: Optional[List[str]] = None,
        tiempo_teoria_min: int = 60,
        tiempo_practica_min: int = 120,
        created_by: Optional[str] = None
    ) -> UnidadDB:
        """Crea una nueva unidad académica.

        Raises:
            SQLAlchemyError: If database operation fails
            ValueError: If materia_code doesn't exist or numero already exists
        """
        # FIX Cortez84 CRIT-REPO-003: Validate FK and uniqueness before insert
        from ..models.subject import SubjectDB

        # Validate materia_code FK exists
        materia_exists = self.db.execute(
            select(SubjectDB.code).where(SubjectDB.code == materia_code)
        ).scalar_one_or_none()
        if not materia_exists:
            raise ValueError(f"Materia '{materia_code}' no existe")

        # Validate numero uniqueness within materia
        existing_unidad = self.get_unidad_by_numero(materia_code, numero)
        if existing_unidad:
            raise ValueError(f"Unidad {numero} ya existe en materia '{materia_code}'")

        try:
            unidad = UnidadDB(
                materia_code=materia_code,
                numero=numero,
                titulo=titulo,
                descripcion=descripcion,
                objetivos_aprendizaje=objetivos_aprendizaje or [],
                tiempo_teoria_min=tiempo_teoria_min,
                tiempo_practica_min=tiempo_practica_min,
                orden=numero,
                created_by=created_by
            )
            self.db.add(unidad)
            self.db.commit()
            self.db.refresh(unidad)
            return unidad
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Failed to create unidad: %s", str(e), exc_info=True)
            raise

    def get_unidad_by_id(
        self,
        unidad_id: str,
        load_apuntes: bool = False,
        load_archivos: bool = False
    ) -> Optional[UnidadDB]:
        """Obtiene una unidad por su ID."""
        stmt = select(UnidadDB).where(
            UnidadDB.id == unidad_id,
            UnidadDB.deleted_at.is_(None)
        )
        if load_apuntes:
            stmt = stmt.options(selectinload(UnidadDB.apuntes))
        if load_archivos:
            stmt = stmt.options(selectinload(UnidadDB.archivos))
        return self.db.execute(stmt).scalar_one_or_none()

    def get_unidades_by_materia(
        self,
        materia_code: str,
        solo_publicadas: bool = False,
        load_apuntes: bool = False,
        load_archivos: bool = False
    ) -> List[UnidadDB]:
        """Obtiene todas las unidades de una materia."""
        stmt = select(UnidadDB).where(
            UnidadDB.materia_code == materia_code,
            UnidadDB.deleted_at.is_(None)
        )
        if solo_publicadas:
            # FIX Cortez88 HIGH-BOOL-001: Use .is_(True) instead of == True
            stmt = stmt.where(UnidadDB.esta_publicada.is_(True))
        if load_apuntes:
            stmt = stmt.options(selectinload(UnidadDB.apuntes))
        if load_archivos:
            stmt = stmt.options(selectinload(UnidadDB.archivos))
        stmt = stmt.order_by(UnidadDB.orden.asc())
        return list(self.db.execute(stmt).scalars().all())

    def get_unidad_by_numero(
        self,
        materia_code: str,
        numero: int
    ) -> Optional[UnidadDB]:
        """Obtiene una unidad por materia y número."""
        stmt = select(UnidadDB).where(
            UnidadDB.materia_code == materia_code,
            UnidadDB.numero == numero,
            UnidadDB.deleted_at.is_(None)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def update_unidad(
        self,
        unidad_id: str,
        **kwargs
    ) -> Optional[UnidadDB]:
        """Actualiza una unidad existente.

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            unidad = self.get_unidad_by_id(unidad_id)
            if unidad:
                for key, value in kwargs.items():
                    if hasattr(unidad, key):
                        setattr(unidad, key, value)
                self.db.commit()
                self.db.refresh(unidad)
            return unidad
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Failed to update unidad %s: %s", unidad_id, str(e), exc_info=True)
            raise

    def publicar_unidad(self, unidad_id: str) -> Optional[UnidadDB]:
        """Publica una unidad (la hace visible para estudiantes)."""
        return self.update_unidad(
            unidad_id,
            esta_publicada=True,
            published_at=datetime.now(timezone.utc)
        )

    def despublicar_unidad(self, unidad_id: str) -> Optional[UnidadDB]:
        """Despublica una unidad."""
        return self.update_unidad(
            unidad_id,
            esta_publicada=False,
            published_at=None
        )

    def delete_unidad(self, unidad_id: str) -> bool:
        """Soft delete de una unidad.

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            unidad = self.get_unidad_by_id(unidad_id)
            if unidad:
                unidad.deleted_at = datetime.now(timezone.utc)
                self.db.commit()
                return True
            return False
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Failed to delete unidad %s: %s", unidad_id, str(e), exc_info=True)
            raise

    def count_unidades_by_materia(self, materia_code: str) -> int:
        """Cuenta las unidades de una materia."""
        stmt = select(func.count(UnidadDB.id)).where(
            UnidadDB.materia_code == materia_code,
            UnidadDB.deleted_at.is_(None)
        )
        return self.db.execute(stmt).scalar_one() or 0

    # ==================== Apuntes ====================

    def create_apuntes(
        self,
        unidad_id: str,
        titulo: str,
        contenido_markdown: str,
        resumen: Optional[str] = None,
        recursos_externos: Optional[List[dict]] = None,
        tiempo_lectura_min: int = 15,
        nivel_dificultad: str = "basico",
        created_by: Optional[str] = None
    ) -> ApuntesDB:
        """Crea nuevos apuntes para una unidad.

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            # Determinar orden
            max_orden = self.db.execute(
                select(func.max(ApuntesDB.orden))
                .where(ApuntesDB.unidad_id == unidad_id)
            ).scalar_one_or_none() or 0

            apuntes = ApuntesDB(
                unidad_id=unidad_id,
                titulo=titulo,
                contenido_markdown=contenido_markdown,
                resumen=resumen,
                recursos_externos=recursos_externos or [],
                tiempo_lectura_min=tiempo_lectura_min,
                nivel_dificultad=nivel_dificultad,
                orden=max_orden + 1,
                created_by=created_by
            )
            self.db.add(apuntes)
            self.db.commit()
            self.db.refresh(apuntes)
            return apuntes
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Failed to create apuntes: %s", str(e), exc_info=True)
            raise

    def get_apuntes_by_id(
        self,
        apuntes_id: str,
        load_archivos: bool = False
    ) -> Optional[ApuntesDB]:
        """Obtiene apuntes por su ID."""
        stmt = select(ApuntesDB).where(
            ApuntesDB.id == apuntes_id,
            ApuntesDB.deleted_at.is_(None)
        )
        if load_archivos:
            stmt = stmt.options(selectinload(ApuntesDB.archivos_adjuntos))
        return self.db.execute(stmt).scalar_one_or_none()

    def get_apuntes_by_unidad(
        self,
        unidad_id: str,
        solo_publicados: bool = False,
        load_archivos: bool = False
    ) -> List[ApuntesDB]:
        """Obtiene todos los apuntes de una unidad."""
        stmt = select(ApuntesDB).where(
            ApuntesDB.unidad_id == unidad_id,
            ApuntesDB.deleted_at.is_(None)
        )
        if solo_publicados:
            # FIX Cortez88 HIGH-BOOL-001: Use .is_(True) instead of == True
            stmt = stmt.where(ApuntesDB.esta_publicado.is_(True))
        if load_archivos:
            stmt = stmt.options(selectinload(ApuntesDB.archivos_adjuntos))
        stmt = stmt.order_by(ApuntesDB.orden.asc())
        return list(self.db.execute(stmt).scalars().all())

    def update_apuntes(
        self,
        apuntes_id: str,
        **kwargs
    ) -> Optional[ApuntesDB]:
        """Actualiza apuntes existentes.

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            apuntes = self.get_apuntes_by_id(apuntes_id)
            if apuntes:
                for key, value in kwargs.items():
                    if hasattr(apuntes, key):
                        setattr(apuntes, key, value)
                self.db.commit()
                self.db.refresh(apuntes)
            return apuntes
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Failed to update apuntes %s: %s", apuntes_id, str(e), exc_info=True)
            raise

    def publicar_apuntes(self, apuntes_id: str) -> Optional[ApuntesDB]:
        """Publica apuntes."""
        return self.update_apuntes(
            apuntes_id,
            esta_publicado=True,
            published_at=datetime.now(timezone.utc)
        )

    def delete_apuntes(self, apuntes_id: str) -> bool:
        """Soft delete de apuntes.

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            apuntes = self.get_apuntes_by_id(apuntes_id)
            if apuntes:
                apuntes.deleted_at = datetime.now(timezone.utc)
                self.db.commit()
                return True
            return False
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Failed to delete apuntes %s: %s", apuntes_id, str(e), exc_info=True)
            raise

    def reordenar_apuntes(
        self,
        unidad_id: str,
        orden_ids: List[str]
    ) -> None:
        """Reordena los apuntes de una unidad.

        FIX Cortez84 HIGH-REPO-003: Use bulk update instead of N updates in loop.
        """
        from sqlalchemy import case, update

        if not orden_ids:
            return

        # Build CASE WHEN expression for single UPDATE statement
        orden_mapping = {apuntes_id: idx for idx, apuntes_id in enumerate(orden_ids, start=1)}

        try:
            # Single UPDATE with CASE WHEN instead of N queries
            stmt = (
                update(ApuntesDB)
                .where(ApuntesDB.id.in_(orden_ids))
                .values(
                    orden=case(
                        orden_mapping,
                        value=ApuntesDB.id
                    )
                )
            )
            self.db.execute(stmt)
            self.db.commit()
            logger.info("Reordered %d apuntes for unidad %s", len(orden_ids), unidad_id)
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Failed to reorder apuntes: %s", str(e), exc_info=True)
            raise

    # ==================== Archivos Adjuntos ====================

    def create_archivo(
        self,
        nombre_original: str,
        nombre_almacenado: str,
        tipo_archivo: str,
        mime_type: str,
        tamano_bytes: int,
        ruta_relativa: str,
        apuntes_id: Optional[str] = None,
        unidad_id: Optional[str] = None,
        descripcion: Optional[str] = None,
        checksum_sha256: Optional[str] = None
    ) -> ArchivoAdjuntoDB:
        """Crea un nuevo registro de archivo adjunto.

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            # Determinar orden
            if apuntes_id:
                max_orden = self.db.execute(
                    select(func.max(ArchivoAdjuntoDB.orden))
                    .where(ArchivoAdjuntoDB.apuntes_id == apuntes_id)
                ).scalar_one_or_none() or 0
            elif unidad_id:
                max_orden = self.db.execute(
                    select(func.max(ArchivoAdjuntoDB.orden))
                    .where(ArchivoAdjuntoDB.unidad_id == unidad_id)
                ).scalar_one_or_none() or 0
            else:
                max_orden = 0

            archivo = ArchivoAdjuntoDB(
                apuntes_id=apuntes_id,
                unidad_id=unidad_id,
                nombre_original=nombre_original,
                nombre_almacenado=nombre_almacenado,
                tipo_archivo=tipo_archivo,
                mime_type=mime_type,
                tamano_bytes=tamano_bytes,
                ruta_relativa=ruta_relativa,
                descripcion=descripcion,
                orden=max_orden + 1,
                checksum_sha256=checksum_sha256
            )
            self.db.add(archivo)
            self.db.commit()
            self.db.refresh(archivo)
            return archivo
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Failed to create archivo: %s", str(e), exc_info=True)
            raise

    def get_archivo_by_id(self, archivo_id: str) -> Optional[ArchivoAdjuntoDB]:
        """Obtiene un archivo por su ID."""
        stmt = select(ArchivoAdjuntoDB).where(
            ArchivoAdjuntoDB.id == archivo_id,
            ArchivoAdjuntoDB.deleted_at.is_(None)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_archivos_by_apuntes(self, apuntes_id: str) -> List[ArchivoAdjuntoDB]:
        """Obtiene todos los archivos de unos apuntes."""
        stmt = select(ArchivoAdjuntoDB).where(
            ArchivoAdjuntoDB.apuntes_id == apuntes_id,
            ArchivoAdjuntoDB.deleted_at.is_(None)
        ).order_by(ArchivoAdjuntoDB.orden.asc())
        return list(self.db.execute(stmt).scalars().all())

    def get_archivos_by_unidad(self, unidad_id: str) -> List[ArchivoAdjuntoDB]:
        """Obtiene todos los archivos de una unidad."""
        stmt = select(ArchivoAdjuntoDB).where(
            ArchivoAdjuntoDB.unidad_id == unidad_id,
            ArchivoAdjuntoDB.deleted_at.is_(None)
        ).order_by(ArchivoAdjuntoDB.orden.asc())
        return list(self.db.execute(stmt).scalars().all())

    def delete_archivo(self, archivo_id: str) -> bool:
        """Soft delete de un archivo.

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            archivo = self.get_archivo_by_id(archivo_id)
            if archivo:
                archivo.deleted_at = datetime.now(timezone.utc)
                self.db.commit()
                return True
            return False
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Failed to delete archivo %s: %s", archivo_id, str(e), exc_info=True)
            raise
