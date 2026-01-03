"""
Health Check Utilities

Cortez66: Extracted from health.py

Provides shared utilities for health checks:
- Process memory measurement
- Garbage collector statistics
"""
import gc
import os
import sys
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def get_process_memory_mb() -> Optional[float]:
    """
    Get current process memory usage in MB.

    Attempts to use psutil first, falls back to /proc on Linux.

    Returns:
        Memory usage in MB, or None if unable to determine
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return round(process.memory_info().rss / 1024 / 1024, 2)
    except ImportError:
        # psutil not installed, try alternative
        try:
            if sys.platform == 'linux':
                with open(f'/proc/{os.getpid()}/status', 'r') as f:
                    for line in f:
                        if line.startswith('VmRSS:'):
                            return round(int(line.split()[1]) / 1024, 2)
        except (IOError, OSError, ValueError) as e:
            logger.debug("Failed to read /proc memory stats: %s", e)
        return None
    except (OSError, AttributeError) as e:
        logger.debug("Failed to get process memory via psutil: %s", e)
        return None


def get_gc_stats() -> Dict[str, Any]:
    """
    Get garbage collector statistics.

    Returns:
        Dict with generation counts and total objects
    """
    try:
        counts = gc.get_count()
        return {
            "generation_0": counts[0],
            "generation_1": counts[1],
            "generation_2": counts[2],
            "total_objects": len(gc.get_objects()),
        }
    except (RuntimeError, AttributeError) as e:
        logger.debug("Failed to get GC stats: %s", e)
        return {}
