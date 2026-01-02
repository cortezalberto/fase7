"""
Secure Python code execution sandbox.

FIX Cortez36: Consolidated from duplicate implementations in:
- backend/api/routers/exercises.py
- backend/tests/integration/test_tabla_multiplicar.py
- backend/tests/integration/test_temperaturas.py
- backend/tests/integration/test_temperaturas_fixed.py

This module provides a secure sandbox for executing student Python code
with restricted builtins and resource limits.
"""
import os
import subprocess
import tempfile
import time
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# ==========================================================================
# Security Constants
# ==========================================================================

DANGEROUS_IMPORTS = [
    'os', 'subprocess', 'sys', 'shutil', 'pathlib',
    'socket', 'requests', 'urllib', 'http',
    'multiprocessing', 'threading', 'asyncio',
    'pickle', 'marshal', 'shelve',
    'ctypes', 'cffi', 'importlib',
    'builtins', '__builtins__',
    'code', 'codeop', 'compile',
]

DANGEROUS_PATTERNS = [
    '__import__', 'exec(', 'eval(', 'compile(',
    'open(', 'file(',
    # 'input(' - PERMITTED: required for user input exercises
    'globals(', 'locals(', 'vars(',
    'getattr(', 'setattr(', 'delattr(',
    '__class__', '__bases__', '__subclasses__',
    '__mro__', '__code__', '__globals__',
    'breakpoint(', 'help(',
]


def validate_code_security(code: str) -> Tuple[bool, str]:
    """
    Validate code for dangerous patterns before execution.

    Args:
        code: The Python code to validate

    Returns:
        Tuple of (is_safe, error_message)
    """
    code_lower = code.lower()

    # Check for dangerous imports
    for dangerous_import in DANGEROUS_IMPORTS:
        patterns = [
            f'import {dangerous_import}',
            f'from {dangerous_import}',
            f'__import__("{dangerous_import}"',
            f"__import__('{dangerous_import}'",
        ]
        for pattern in patterns:
            if pattern.lower() in code_lower:
                return False, f"Error de seguridad: Import '{dangerous_import}' no permitido"

    # Check for dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if pattern.lower() in code_lower:
            return False, f"Error de seguridad: Patrón '{pattern}' no permitido"

    return True, ""


def create_sandbox_wrapper(timeout_seconds: int) -> str:
    """
    Create the sandbox wrapper script that restricts builtins and resources.

    Args:
        timeout_seconds: Maximum execution time in seconds

    Returns:
        The sandbox wrapper code as a string
    """
    return f'''
import sys

# Limit resources (Linux/Mac only)
try:
    import resource
    # Limit memory to 50MB
    resource.setrlimit(resource.RLIMIT_AS, (50 * 1024 * 1024, 50 * 1024 * 1024))
    # Limit CPU time to timeout + 1 second
    resource.setrlimit(resource.RLIMIT_CPU, ({timeout_seconds}, {timeout_seconds} + 1))
    # Disable file creation
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
    # Limit number of processes
    resource.setrlimit(resource.RLIMIT_NPROC, (0, 0))
except (ImportError, AttributeError, ValueError):
    pass  # Windows doesn't have resource module or doesn't support some limits

# Restrict builtins
import math
restricted_builtins = {{
    'print': print,
    'input': input,  # Required for user input exercises
    'math': math,    # Required for math exercises
    'len': len,
    'range': range,
    'int': int,
    'float': float,
    'str': str,
    'bool': bool,
    'list': list,
    'dict': dict,
    'set': set,
    'tuple': tuple,
    'abs': abs,
    'max': max,
    'min': min,
    'sum': sum,
    'sorted': sorted,
    'reversed': reversed,
    'enumerate': enumerate,
    'zip': zip,
    'map': map,
    'filter': filter,
    'any': any,
    'all': all,
    'isinstance': isinstance,
    'type': type,
    'round': round,
    'pow': pow,
    'divmod': divmod,
    'chr': chr,
    'ord': ord,
    'hex': hex,
    'bin': bin,
    'oct': oct,
    'format': format,
    'repr': repr,
    'hash': hash,
    'id': id,
    'slice': slice,
    'iter': iter,
    'next': next,
    'True': True,
    'False': False,
    'None': None,
    'Exception': Exception,
    'ValueError': ValueError,
    'TypeError': TypeError,
    'IndexError': IndexError,
    'KeyError': KeyError,
    'ZeroDivisionError': ZeroDivisionError,
}}

# User code below (executed with restricted builtins)
__builtins__ = restricted_builtins

'''


def execute_python_code(code: str, test_input: str, timeout_seconds: int = 5) -> Tuple[str, str, int]:
    """
    Execute Python code securely with sandbox restrictions.

    SECURITY MEASURES:
    1. Blocks dangerous imports (os, subprocess, sys, etc.)
    2. Blocks dangerous functions (exec, eval, open, etc.)
    3. Limits execution time
    4. Limits memory (on Linux/Mac)
    5. Runs in separate process without network access

    Args:
        code: The Python code to execute
        test_input: Input to provide via stdin
        timeout_seconds: Maximum execution time in seconds (default: 5)

    Returns:
        Tuple of (stdout, stderr, execution_time_ms)
    """
    # Validate code security
    is_safe, error_message = validate_code_security(code)
    if not is_safe:
        return "", error_message, 0

    # Create sandboxed code
    sandbox_wrapper = create_sandbox_wrapper(timeout_seconds)
    sandboxed_code = sandbox_wrapper + code

    # Write to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(sandboxed_code)
        temp_file = f.name

    try:
        start_time = time.time()
        result = subprocess.run(
            ['python', '-I', temp_file],  # -I: isolated mode
            input=test_input,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env={  # Minimal environment
                'PATH': os.environ.get('PATH', ''),
                'PYTHONDONTWRITEBYTECODE': '1',
                'PYTHONUNBUFFERED': '1',
            }
        )
        execution_time = int((time.time() - start_time) * 1000)

        return result.stdout.strip(), result.stderr.strip(), execution_time
    except subprocess.TimeoutExpired:
        logger.warning("Code execution timed out after %d seconds", timeout_seconds)
        return "", "Error: Tiempo de ejecución excedido", timeout_seconds * 1000
    except Exception as e:
        # FIX Cortez36: Added exc_info for stack trace
        logger.error("Code execution failed: %s", str(e), exc_info=True)
        return "", f"Error: {str(e)}", 0
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)
