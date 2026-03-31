"""Persistent configuration management for kon-verter.

Saves and loads user preferences to/from a JSON file in the user's home directory.
"""

import json
from pathlib import Path
from typing import Any

# Config directory and file
_CONFIG_DIR = Path.home() / ".konverter"
_CONFIG_FILE = _CONFIG_DIR / "config.json"

# Default settings
_DEFAULTS: dict[str, Any] = {
    "engine": "offline",       # Transcription: "offline" | "online"
    "model": "small",          # Transcription: "tiny" | "base" | "small" | "medium" | "large-v3"
    "language": "auto",        # Transcription: "auto" | "es" | "en"
    "llm_engine": "groq",      # Summarization: "groq" | "ollama"
    "groq_api_key": "",        # Groq Cloud API Key
    "ollama_model": "llama3.2",# Ollama Local Model
}


def load_config() -> dict[str, Any]:
    """Load configuration from disk, falling back to defaults for missing keys.

    Returns:
        A dictionary with the current configuration values.
    """
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if not _CONFIG_FILE.exists():
        return dict(_DEFAULTS)

    try:
        with _CONFIG_FILE.open("r", encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)
        # Merge with defaults to handle newly added keys
        merged = dict(_DEFAULTS)
        merged.update(data)
        return merged
    except (json.JSONDecodeError, OSError):
        return dict(_DEFAULTS)


def save_config(config: dict[str, Any]) -> None:
    """Persist configuration to disk.

    Args:
        config: Dictionary of setting key-value pairs to save.

    Raises:
        OSError: If the config file cannot be written.
    """
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with _CONFIG_FILE.open("w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
