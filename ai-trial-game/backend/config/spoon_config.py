"""
SpoonOS configuration.

Centralized configuration for SpoonOS-related settings.
"""

import os


def get_spoon_config() -> dict:
    """
    Get SpoonOS configuration.

    Reads from environment variables with sensible defaults.

    Returns:
        {
            "llm_provider": str,
            "model": str,
            "api_key": str | None,
            "base_url": str | None,
            "use_spoon_agent": bool,
        }
    """
    return {
        "llm_provider": os.getenv("LLM_PROVIDER", "openai"),
        "model": os.getenv("OPENAI_COMPATIBLE_MODEL", "claude-sonnet-4-5-20250929"),
        "api_key": os.getenv("OPENAI_COMPATIBLE_API_KEY") or os.getenv("OPENAI_API_KEY"),
        "base_url": os.getenv("OPENAI_COMPATIBLE_BASE_URL") or os.getenv("OPENAI_BASE_URL"),
        "use_spoon_agent": os.getenv("USE_SPOON_AGENT", "true").lower() not in ("false", "0", "no"),
    }


# Convenience access
SPOON_CONFIG = get_spoon_config()
