"""Settings service for managing application configuration."""

import json
import os
from pathlib import Path
from typing import Optional

from app.core.config import DATA_DIR

SETTINGS_FILE = DATA_DIR / "settings.json"

DEFAULT_SETTINGS = {
    "llm_api_key": "",
    "llm_base_url": "https://open.bigmodel.cn/api/paas/v4",
    "llm_model": "glm-4-flash",
    "llm_image_model": "cogview-3-flash",
    "llm_component_model": "glm-4-flash",
    "image_api_key": "",
    "vision_api_key": "",
    "image_base_url": "",
    "vision_base_url": "",
    "api_format": "openai",
    "nanasoul_prompt": "",
    "mineru_token": "",
    "theme": "light",
    "language": "zh",
}


def ensure_data_dir():
    """Ensure data directory exists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_settings() -> dict:
    """Load settings from file or return defaults."""
    ensure_data_dir()
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                settings = json.load(f)
                # Merge with defaults to ensure all keys exist
                merged = DEFAULT_SETTINGS.copy()
                merged.update(settings)
                return merged
        except (json.JSONDecodeError, IOError):
            pass
    return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict) -> bool:
    """Save settings to file."""
    ensure_data_dir()
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        return True
    except IOError:
        return False


class SettingsService:
    """Settings service class."""
    
    def get_settings(self) -> dict:
        """Get current settings."""
        return load_settings()
    
    def update_settings(self, updates: dict) -> dict:
        """Update settings with new values."""
        current = load_settings()
        current.update(updates)
        save_settings(current)
        return current
    
    def get_setting(self, key: str, default=None):
        """Get a specific setting value."""
        settings = load_settings()
        return settings.get(key, default)
