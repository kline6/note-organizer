import sys
import os
import logging
from pydantic_settings import BaseSettings
from pathlib import Path

logger = logging.getLogger(__name__)


def _get_data_dir() -> str:
    if getattr(sys, 'frozen', False):
        return str(Path(sys.executable).parent / "data")
    return str(Path(__file__).resolve().parent.parent / "data")


def _get_env_file() -> str:
    if getattr(sys, 'frozen', False):
        return str(Path(sys.executable).parent / ".env")
    return str(Path(__file__).resolve().parent.parent / ".env")


class Settings(BaseSettings):
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"
    data_dir: str = _get_data_dir()
    database_url: str = "sqlite+aiosqlite:///./data/app.db"

    class Config:
        env_file = _get_env_file()
        env_file_encoding = "utf-8"

    def apply_user_overrides(self):
        try:
            from app.settings_manager import get_settings
        except ImportError as e:
            logger.warning("Cannot import settings_manager: %s", e)
            return
        try:
            user = get_settings()
        except Exception as e:
            logger.warning("Failed to load user settings: %s", e)
            return
        uk = user.get("deepseek_api_key", "")
        if uk and not uk.startswith("sk-your-"):
            self.deepseek_api_key = uk
        if user.get("deepseek_base_url"):
            self.deepseek_base_url = user["deepseek_base_url"]
        if user.get("deepseek_model"):
            self.deepseek_model = user["deepseek_model"]


settings = Settings()
settings.apply_user_overrides()
os.makedirs(settings.data_dir, exist_ok=True)
