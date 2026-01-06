"""
Script de Ingesta de Documentos para RAG.

Cortez87: Implementacion de RAG para enriquecer respuestas de agentes.

Este script facilita la carga de contenido academico al sistema RAG,
transformando archivos de texto y markdown en documentos vectorizados
listos para busqueda semantica.

Usage:
    # Cargar toda la teoria de una materia
    python -m backend.scripts.ingest_knowledge --source ./docs/materiales --materia PROG1

    # Cargar una unidad especifica
    python -m backend.scripts.ingest_knowledge --source ./teoria --materia PROG1 --unit algoritmos

    # Cargar ejemplos con dificultad avanzada
    python -m backend.scripts.ingest_knowledge --source ./ejemplos --materia PROG1 --type ejemplo --difficulty avanzado

    # Modo dry-run (no inserta, solo muestra que se procesaria)
    python -m backend.scripts.ingest_knowledge --source ./docs --materia PROG1 --dry-run
"""
import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.core.embeddings import get_embedding_provider, EMBEDDING_DIMENSIONS
from backend.database.config import get_db_session
from backend.database.repositories.knowledge_repository import KnowledgeRepository

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Extensiones de archivo soportadas
SUPPORTED_EXTENSIONS = {".txt", ".md", ".json"}

# Limite de caracteres para embeddings
MAX_EMBEDDING_CHARS = 2000


def read_file_content(file_path: Path) -> Optional[str]:
    """
    Lee el contenido de un archivo con manejo de encoding.

    Intenta UTF-8 primero, luego latin-1 como fallback.
    """
    encodings = ['utf-8', 'latin-1', 'cp1252']

    for encoding in encodings:
        try:
            return file_path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue

    logger.warning(f"Could not decode file with any encoding: {file_path}")
    return None


def extract_title_from_content(content: str, file_path: Path) -> str:
    """
    Extrae un titulo del contenido o del nombre del archivo.

    Para archivos Markdown, busca el primer encabezado.
    Para otros, usa el nombre del archivo.
    """
    # Intentar extraer de Markdown heading
    lines = content.split('\n')
    for line in lines[:10]:  # Solo primeras 10 lineas
        line = line.strip()
        if line.startswith('# '):
            return line[2:].strip()

    # Fallback: nombre del archivo
    return file_path.stem.replace('_', ' ').replace('-', ' ').title()


def infer_content_type(file_path: Path, content: str) -> str:
    """
    Infiere el tipo de contenido basado en el path y contenido.
    """
    path_lower = str(file_path).lower()

    # Patrones en path
    type_patterns = {
        'ejemplo': ['ejemplo', 'example', 'sample', 'demo'],
        'ejercicio': ['ejercicio', 'exercise', 'problem', 'practica'],
        'faq': ['faq', 'pregunta', 'question'],
        'consigna': ['consigna', 'assignment', 'tarea', 'tp'],
        'teoria': ['teoria', 'theory', 'concepto', 'concept', 'doc'],
    }

    for content_type, patterns in type_patterns.items():
        for pattern in patterns:
            if pattern in path_lower:
                return content_type

    # Patrones en contenido
    content_lower = content[:500].lower()
    if 'ejemplo:' in content_lower or 'example:' in content_lower:
        return 'ejemplo'
    if 'ejercicio' in content_lower or 'exercise' in content_lower:
        return 'ejercicio'

    # Default
    return 'teoria'


def infer_unit_from_path(file_path: Path, source_root: Path) -> Optional[str]:
    """
    Infiere la unidad tematica de la estructura de carpetas.

    Si el archivo esta en /docs/algoritmos/quicksort.md,
    la unidad seria 'algoritmos'.
    """
    try:
        relative = file_path.relative_to(source_root)
        parts = relative.parts

        if len(parts) > 1:
            # Usar la primera carpeta como unidad
            return parts[0]
    except ValueError:
        pass

    return None


async def process_file(
    file_path: Path,
    source_root: Path,
    embedding_provider,
    materia_code: str,
    unit: Optional[str] = None,
    content_type: Optional[str] = None,
    difficulty: str = "intermedio"
) -> Optional[Dict[str, Any]]:
    """
    Procesa un archivo y genera su documento para ingesta.
    """
    # Leer contenido
    content = read_file_content(file_path)
    if not content or len(content.strip()) < 50:
        logger.debug(f"Skipping empty or too short file: {file_path}")
        return None

    # Extraer metadatos
    title = extract_title_from_content(content, file_path)
    inferred_unit = unit or infer_unit_from_path(file_path, source_root)
    inferred_type = content_type or infer_content_type(file_path, content)

    # Generar embedding (usando primeros N caracteres)
    text_for_embedding = content[:MAX_EMBEDDING_CHARS]
    try:
        embedding = await embedding_provider.embed(text_for_embedding)
    except Exception as e:
        logger.error(f"Failed to generate embedding for {file_path}: {e}")
        return None

    # Construir documento
    doc = {
        "content": content,
        "title": title,
        "content_type": inferred_type,
        "unit": inferred_unit,
        "difficulty": difficulty,
        "materia_code": materia_code,
        "source_file": str(file_path),
        "embedding": embedding,
        "metadata": {
            "file_size": len(content),
            "embedding_chars": len(text_for_embedding),
        }
    }

    return doc


async def ingest_directory(
    source_path: Path,
    materia_code: str,
    unit: Optional[str] = None,
    content_type: Optional[str] = None,
    difficulty: str = "intermedio",
    dry_run: bool = False,
    batch_size: int = 10
) -> int:
    """
    Ingesta todos los documentos de un directorio.

    Args:
        source_path: Directorio con los archivos
        materia_code: Codigo de materia (ej: PROG1)
        unit: Unidad tematica (opcional, se infiere de carpetas)
        content_type: Tipo de contenido (opcional, se infiere)
        difficulty: Nivel de dificultad
        dry_run: Si True, no inserta, solo muestra
        batch_size: Tamano de lotes para procesamiento

    Returns:
        Cantidad de documentos procesados
    """
    logger.info("=" * 60)
    logger.info(f"RAG Knowledge Ingestion - Cortez87")
    logger.info("=" * 60)
    logger.info(f"Source: {source_path}")
    logger.info(f"Materia: {materia_code}")
    logger.info(f"Unit: {unit or 'auto-detect'}")
    logger.info(f"Type: {content_type or 'auto-detect'}")
    logger.info(f"Difficulty: {difficulty}")
    logger.info(f"Dry run: {dry_run}")
    logger.info("=" * 60)

    # Obtener proveedor de embeddings
    embedding_provider = get_embedding_provider(provider_type="ollama")

    # Recolectar archivos
    files: List[Path] = []
    for ext in SUPPORTED_EXTENSIONS:
        files.extend(source_path.glob(f"**/*{ext}"))

    if not files:
        logger.warning(f"No files found with extensions: {SUPPORTED_EXTENSIONS}")
        return 0

    logger.info(f"Found {len(files)} files to process")

    # Procesar archivos
    documents_to_create = []
    processed = 0
    failed = 0

    for file_path in files:
        logger.info(f"Processing: {file_path.name}")

        doc = await process_file(
            file_path=file_path,
            source_root=source_path,
            embedding_provider=embedding_provider,
            materia_code=materia_code,
            unit=unit,
            content_type=content_type,
            difficulty=difficulty
        )

        if doc:
            documents_to_create.append(doc)
            processed += 1

            if dry_run:
                logger.info(
                    f"  [DRY-RUN] Would create: {doc['title'][:50]}... "
                    f"(type={doc['content_type']}, unit={doc['unit']})"
                )
        else:
            failed += 1

    # Insertar en base de datos (si no es dry-run)
    if not dry_run and documents_to_create:
        logger.info(f"\nInserting {len(documents_to_create)} documents into database...")

        with get_db_session() as session:
            repo = KnowledgeRepository(session)

            # Insertar en lotes
            for i in range(0, len(documents_to_create), batch_size):
                batch = documents_to_create[i:i + batch_size]
                try:
                    count = repo.bulk_create(batch)
                    logger.info(f"  Inserted batch {i//batch_size + 1}: {count} documents")
                except Exception as e:
                    logger.error(f"  Failed to insert batch: {e}")
                    failed += len(batch)

    # Limpiar recursos
    await embedding_provider.close()

    # Resumen
    logger.info("=" * 60)
    logger.info("Ingestion Summary")
    logger.info("=" * 60)
    logger.info(f"Total files found: {len(files)}")
    logger.info(f"Successfully processed: {processed}")
    logger.info(f"Failed: {failed}")
    if dry_run:
        logger.info("(Dry run - no documents were actually inserted)")
    logger.info("=" * 60)

    return processed


def main():
    parser = argparse.ArgumentParser(
        description="Ingest academic documents for RAG knowledge base",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Load all theory from a folder
  python -m backend.scripts.ingest_knowledge --source ./docs/teoria --materia PROG1

  # Load examples for a specific unit
  python -m backend.scripts.ingest_knowledge --source ./ejemplos --materia PROG1 --unit algoritmos --type ejemplo

  # Preview what would be loaded (dry run)
  python -m backend.scripts.ingest_knowledge --source ./docs --materia PROG1 --dry-run

Content Types:
  teoria    - Conceptual explanations, theory
  ejemplo   - Code examples, demonstrations
  ejercicio - Practice exercises
  faq       - Frequently asked questions
  consigna  - Assignment instructions

Difficulty Levels:
  basico      - Beginner level
  intermedio  - Intermediate level
  avanzado    - Advanced level
        """
    )

    parser.add_argument(
        "--source", "-s",
        required=True,
        help="Source directory containing documents"
    )
    parser.add_argument(
        "--materia", "-m",
        required=True,
        help="Subject/course code (e.g., PROG1, ALG2)"
    )
    parser.add_argument(
        "--unit", "-u",
        help="Thematic unit (default: auto-detect from folder structure)"
    )
    parser.add_argument(
        "--type", "-t",
        choices=["teoria", "ejemplo", "ejercicio", "faq", "consigna"],
        help="Content type (default: auto-detect)"
    )
    parser.add_argument(
        "--difficulty", "-d",
        default="intermedio",
        choices=["basico", "intermedio", "avanzado"],
        help="Difficulty level (default: intermedio)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be processed without inserting"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Batch size for database insertions (default: 10)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate source directory
    source = Path(args.source)
    if not source.exists():
        logger.error(f"Source directory does not exist: {source}")
        sys.exit(1)
    if not source.is_dir():
        logger.error(f"Source is not a directory: {source}")
        sys.exit(1)

    # Run ingestion
    try:
        count = asyncio.run(ingest_directory(
            source_path=source,
            materia_code=args.materia.upper(),
            unit=args.unit,
            content_type=args.type,
            difficulty=args.difficulty,
            dry_run=args.dry_run,
            batch_size=args.batch_size
        ))

        if count > 0:
            logger.info(f"Successfully processed {count} documents")
        else:
            logger.warning("No documents were processed")

    except KeyboardInterrupt:
        logger.info("\nIngestion cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
