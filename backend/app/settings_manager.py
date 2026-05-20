import json
import os
import sys
from pathlib import Path
from threading import Lock


def _get_default_settings_path() -> Path:
    """Get settings file path, respecting frozen (PyInstaller) mode."""
    # Check if running in PyInstaller bundle
    if getattr(sys, 'frozen', False):
        # Write settings next to the executable
        return Path(sys.executable).parent / "data" / "user_settings.json"
    return Path(__file__).parent.parent / "data" / "user_settings.json"


SETTINGS_FILE = _get_default_settings_path()
_lock = Lock()

DEFAULTS = {
    "deepseek_api_key": "",
    "deepseek_base_url": "https://api.deepseek.com/v1",
    "deepseek_model": "deepseek-chat",
}


def _load() -> dict:
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Merge with defaults for any missing keys
            merged = {**DEFAULTS, **data}
            return merged
        except (json.JSONDecodeError, OSError):
            pass
    return dict(DEFAULTS)


def _save(data: dict) -> None:
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# In-memory cache
_cache: dict | None = None


def get_settings() -> dict:
    global _cache
    with _lock:
        if _cache is None:
            _cache = _load()
        return dict(_cache)


def update_settings(updates: dict) -> dict:
    global _cache
    with _lock:
        current = _load()
        current.update(updates)
        # Only persist known keys
        to_save = {k: v for k, v in current.items() if k in DEFAULTS}
        _save(to_save)
        _cache = to_save
        return dict(_cache)


def reload_settings() -> dict:
    global _cache
    with _lock:
        _cache = _load()
        return dict(_cache)
