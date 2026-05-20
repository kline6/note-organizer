from fastapi import APIRouter, Request
from pydantic import BaseModel
from app.settings_manager import get_settings, update_settings
from app.config import settings as app_settings

router = APIRouter(prefix="/api/settings", tags=["settings"])


class UserSettingsUpdate(BaseModel):
    deepseek_api_key: str | None = None
    deepseek_base_url: str | None = None
    deepseek_model: str | None = None


@router.get("")
async def get_user_settings():
    """Get current user settings (API key masked)."""
    s = get_settings()
    key = s.get("deepseek_api_key", "")
    masked = ""
    if key:
        masked = key[:4] + "*" * (len(key) - 8) + key[-4:] if len(key) > 8 else "****"
    return {
        "deepseek_api_key": masked,
        "deepseek_base_url": s.get("deepseek_base_url", "https://api.deepseek.com/v1"),
        "deepseek_model": s.get("deepseek_model", "deepseek-chat"),
        "has_api_key": bool(key),
    }


@router.put("")
async def update_user_settings(data: UserSettingsUpdate):
    """Update user settings. Only provided fields are changed."""
    updates = {}
    if data.deepseek_api_key is not None:
        updates["deepseek_api_key"] = data.deepseek_api_key
    if data.deepseek_base_url is not None:
        updates["deepseek_base_url"] = data.deepseek_base_url
    if data.deepseek_model is not None:
        updates["deepseek_model"] = data.deepseek_model

    if updates:
        update_settings(updates)
        # Reload app config so changes take effect immediately
        app_settings.deepseek_api_key = updates.get("deepseek_api_key", app_settings.deepseek_api_key)
        app_settings.deepseek_base_url = updates.get("deepseek_base_url", app_settings.deepseek_base_url)
        app_settings.deepseek_model = updates.get("deepseek_model", app_settings.deepseek_model)

    return {"ok": True}


@router.post("/test")
async def test_api_connection(request: Request = None):
    """Test the DeepSeek API connection."""
    from openai import AsyncOpenAI

    # Use test key from header if provided, else server key
    test_key = ""
    if request:
        test_key = request.headers.get("X-Test-Key", "")
    key = test_key or app_settings.deepseek_api_key
    if not key or key.startswith("sk-your-"):
        return {"ok": False, "error": "请先设置 DeepSeek API Key"}

    try:
        client = AsyncOpenAI(api_key=key, base_url=app_settings.deepseek_base_url)
        resp = await client.chat.completions.create(
            model=app_settings.deepseek_model,
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=10,
        )
        return {"ok": True, "message": "连接成功"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
