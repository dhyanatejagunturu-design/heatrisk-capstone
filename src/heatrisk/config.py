"""Load project settings from config/settings.yaml."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SETTINGS_FILE = PROJECT_ROOT / "config" / "settings.yaml"


@lru_cache(maxsize=1)
def load_settings(path: str | Path = SETTINGS_FILE) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def data_path(kind: str) -> Path:
    """Absolute path for a data folder: 'raw', 'interim', 'processed' or 'external'."""
    return PROJECT_ROOT / load_settings()["paths"][kind]
