#!/usr/bin/env python3
"""
Script para detectar y reportar imports no utilizados en el proyecto.

Uso:
    python devops/scripts/fix_unused_imports.py
    python devops/scripts/fix_unused_imports.py --dir backend
    python devops/scripts/fix_unused_imports.py --dir frontEnd/src

Nota: Ejecutar desde el directorio raíz del proyecto (activia1-main/)
"""
import os
import re
import sys
import argparse
from pathlib import Path
from typing import List, Dict


# Windows encoding fix
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def find_python_files(root_dir: str) -> List[Path]:
    """Encuentra todos los archivos .py en el directorio."""
    root = Path(root_dir)
    if not root.exists():
        return []
    return list(root.rglob("*.py"))


def analyze_file(file_path: Path) -> Dict[str, List]:
    """Analiza un archivo Python y detecta imports potencialmente no utilizados."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return {"error": str(e)}

    # Extraer imports
    import_pattern = r'^(?:from\s+[\w.]+\s+)?import\s+([\w\s,]+)(?:\s+as\s+\w+)?'
    imports = []

    for match in re.finditer(import_pattern, content, re.MULTILINE):
        import_line = match.group(0)
        imported_names = match.group(1)

        # Separar imports múltiples (e.g., "a, b, c")
        names = [n.strip() for n in imported_names.split(',')]

        for name in names:
            if not name:
                continue

            # Verificar si el nombre se usa en el código (fuera del import)
            # Buscar referencias al nombre importado
            usage_pattern = rf'\b{re.escape(name)}\b'

            # Contar ocurrencias (excluyendo la línea de import)
            lines = content.split('\n')
            import_line_num = content[:match.start()].count('\n')

            usage_count = 0
            for i, line in enumerate(lines):
                if i == import_line_num:
                    continue  # Skip import line
                if re.search(usage_pattern, line):
                    usage_count += 1

            if usage_count == 0:
                imports.append({
                    'name': name,
                    'line': import_line,
                    'line_num': import_line_num + 1
                })

    return {'unused': imports}


def main():
    """Ejecuta el análisis."""
    parser = argparse.ArgumentParser(
        description="Detectar imports no utilizados en archivos Python"
    )
    parser.add_argument(
        '--dir', '-d',
        default='backend',
        help='Directorio a analizar (default: backend)'
    )
    args = parser.parse_args()

    print("Analizando archivos Python...")
    print("=" * 80)

    # Obtener directorio raíz del proyecto
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent  # devops/scripts -> devops -> project root

    # Directorio a analizar
    src_dir = project_root / args.dir

    if not src_dir.exists():
        # Intentar rutas alternativas
        alt_paths = [
            project_root / "backend",
            project_root / "src" / "ai_native_mvp",
            project_root / "frontEnd" / "src",
        ]

        for alt_path in alt_paths:
            if alt_path.exists():
                src_dir = alt_path
                break
        else:
            print(f"Error: Directorio no encontrado: {args.dir}")
            print(f"Rutas buscadas:")
            print(f"  - {project_root / args.dir}")
            for p in alt_paths:
                print(f"  - {p}")
            return 1

    print(f"Analizando: {src_dir}")
    print()

    files = find_python_files(str(src_dir))
    print(f"Archivos encontrados: {len(files)}")
    print()

    total_unused = 0
    files_with_unused = []

    for file_path in files:
        try:
            rel_path = file_path.relative_to(project_root)
        except ValueError:
            rel_path = file_path

        result = analyze_file(file_path)

        if 'error' in result:
            print(f"⚠️  Error en {rel_path}: {result['error']}")
            continue

        if result['unused']:
            files_with_unused.append((str(rel_path), result['unused']))
            total_unused += len(result['unused'])

    # Reporte
    if files_with_unused:
        print(f"\n{'=' * 80}")
        print(f"ARCHIVOS CON IMPORTS POTENCIALMENTE NO UTILIZADOS: {len(files_with_unused)}")
        print(f"{'=' * 80}\n")

        for file_path, unused in files_with_unused:
            print(f"\n📄 {file_path}")
            print("-" * 80)
            for item in unused:
                print(f"  Línea {item['line_num']}: {item['name']}")
                print(f"    {item['line']}")
    else:
        print("\n✅ No se encontraron imports no utilizados!")

    print(f"\n{'=' * 80}")
    print(f"TOTAL: {total_unused} imports potencialmente no utilizados")
    print(f"{'=' * 80}")

    print("\n⚠️  NOTA: Este es un análisis básico. Verifica manualmente antes de eliminar.")
    print("   Algunos imports pueden ser usados dinámicamente o para re-exportación.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
