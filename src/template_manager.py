"""Manages LLM templates for summarizing and extracting data.

Templates are stored as JSON files in ~/.konverter/templates/
"""

import json
from pathlib import Path
from typing import Any

_TEMPLATES_DIR = Path.home() / ".konverter" / "templates"

_DEFAULT_TEMPLATES = [
    {
        "id": "resumen_general",
        "name": "General",
        "body": "Eres un asistente experto en síntesis. Proporciona un resumen ejecutivo del siguiente texto en formato de bullet points, capturando los puntos más importantes.",
    },
    {
        "id": "daily_standup",
        "name": "Daily Standup",
        "body": "Analiza la siguiente transcripción de una reunión diaria (Daily) y extrae los siguientes puntos:\n1. Tareas completadas ayer.\n2. Tareas planeadas para hoy.\n3. Impedimentos o bloqueos mencionados.",
    },
    {
        "id": "reunion_equipo",
        "name": "Reunión de Equipo",
        "body": "Resume la siguiente reunión capturando:\n- Objetivos discutidos.\n- Decisiones tomadas.\n- Tareas asignadas y responsables.\n- Próximos pasos.",
    },
]


def init_templates() -> None:
    """Initialize default templates if they don't exist."""
    _TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    for template in _DEFAULT_TEMPLATES:
        path = _TEMPLATES_DIR / f"{template['id']}.json"
        if not path.exists():
            with path.open("w", encoding="utf-8") as f:
                json.dump(template, f, indent=2, ensure_ascii=False)


def get_all_templates() -> list[dict[str, Any]]:
    """List all available templates."""
    init_templates()
    templates = []
    for path in _TEMPLATES_DIR.glob("*.json"):
        try:
            with path.open("r", encoding="utf-8") as f:
                template = json.load(f)
                templates.append(template)
        except (json.JSONDecodeError, OSError):
            continue
    return templates


def save_template(template_id: str, name: str, body: str) -> None:
    """Save or update a template."""
    _TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    data = {"id": template_id, "name": name, "body": body}
    path = _TEMPLATES_DIR / f"{template_id}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def delete_template(template_id: str) -> None:
    """Delete a template by ID."""
    path = _TEMPLATES_DIR / f"{template_id}.json"
    if path.exists():
        path.unlink()
