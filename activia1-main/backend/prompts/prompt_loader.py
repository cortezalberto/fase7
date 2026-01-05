"""
Prompt Loader - Dynamic prompt loading from markdown files.

Cortez75: Extracted hardcoded prompts to maintainable .md files.

Provides:
- load_prompt(): Load a prompt template from /prompts directory
- load_simulator_prompt(): Load a simulator-specific prompt
- Caching for performance
- Template variable substitution
"""
import os
import logging
from functools import lru_cache
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Base path for prompts directory
PROMPTS_DIR = Path(__file__).parent


@lru_cache(maxsize=32)
def load_prompt(prompt_name: str) -> str:
    """
    Load a prompt template from the prompts directory.

    Args:
        prompt_name: Name of the prompt file (without .md extension)

    Returns:
        Prompt content as string

    Raises:
        FileNotFoundError: If prompt file doesn't exist
    """
    prompt_path = PROMPTS_DIR / f"{prompt_name}.md"

    if not prompt_path.exists():
        logger.error("Prompt file not found: %s", prompt_path)
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    with open(prompt_path, "r", encoding="utf-8") as f:
        content = f.read()

    logger.debug("Loaded prompt: %s (%d chars)", prompt_name, len(content))
    return content


def load_prompt_with_variables(
    prompt_name: str,
    variables: Dict[str, Any]
) -> str:
    """
    Load a prompt and substitute template variables.

    Uses {{variable_name}} syntax for placeholders.

    Args:
        prompt_name: Name of the prompt file
        variables: Dictionary of variables to substitute

    Returns:
        Prompt with variables substituted
    """
    template = load_prompt(prompt_name)

    for key, value in variables.items():
        placeholder = "{{" + key + "}}"
        template = template.replace(placeholder, str(value))

    return template


@lru_cache(maxsize=16)
def load_simulator_prompt(simulator_type: str) -> Optional[str]:
    """
    Load a simulator-specific system prompt.

    Args:
        simulator_type: Type of simulator (product_owner, scrum_master, etc.)

    Returns:
        System prompt string or None if not found
    """
    prompt_name = f"simulator_{simulator_type}_prompt"

    try:
        return load_prompt(prompt_name)
    except FileNotFoundError:
        logger.warning("Simulator prompt not found: %s, using fallback", simulator_type)
        return None


def get_simulator_config(simulator_type: str) -> Dict[str, Any]:
    """
    Get full configuration for a simulator including prompt, competencies, expects.

    Args:
        simulator_type: Type of simulator

    Returns:
        Dictionary with prompt, competencies, expects, fallback_message
    """
    config_name = f"simulator_{simulator_type}_config"

    try:
        content = load_prompt(config_name)

        # Parse YAML-like config from markdown
        config = {}
        current_section = None
        current_list = []

        for line in content.split("\n"):
            line = line.strip()

            if line.startswith("## SYSTEM_PROMPT"):
                current_section = "system_prompt"
                config["system_prompt"] = ""
            elif line.startswith("## COMPETENCIES"):
                if current_section == "system_prompt":
                    config["system_prompt"] = config.get("system_prompt", "").strip()
                current_section = "competencies"
                current_list = []
            elif line.startswith("## EXPECTS"):
                if current_section == "competencies":
                    config["competencies"] = current_list
                current_section = "expects"
                current_list = []
            elif line.startswith("## FALLBACK"):
                if current_section == "expects":
                    config["expects"] = current_list
                current_section = "fallback"
                config["fallback_message"] = ""
            elif current_section == "system_prompt" and line:
                config["system_prompt"] = config.get("system_prompt", "") + line + "\n"
            elif current_section in ("competencies", "expects") and line.startswith("- "):
                current_list.append(line[2:].strip())
            elif current_section == "fallback" and line:
                config["fallback_message"] = config.get("fallback_message", "") + line + "\n"

        # Handle last section
        if current_section == "expects":
            config["expects"] = current_list
        elif current_section == "fallback":
            config["fallback_message"] = config.get("fallback_message", "").strip()

        return config

    except FileNotFoundError:
        logger.warning("Simulator config not found: %s", simulator_type)
        return {}


def clear_prompt_cache():
    """Clear the prompt cache (useful for development/testing)."""
    load_prompt.cache_clear()
    load_simulator_prompt.cache_clear()
    logger.info("Prompt cache cleared")
