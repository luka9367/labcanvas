"""Settings endpoints."""

from fastapi import APIRouter, HTTPException

from app.schemas.settings import Settings, SettingsResponse, SettingsUpdateRequest
from app.services.settings_service import load_settings, save_settings

router = APIRouter()


@router.get("", response_model=SettingsResponse)
async def get_settings():
    """Get current settings."""
    try:
        settings_dict = load_settings()
        # Mask sensitive values
        if settings_dict.get("llm_api_key"):
            settings_dict["llm_api_key"] = "*" * 8 + settings_dict["llm_api_key"][-4:] if len(settings_dict["llm_api_key"]) > 4 else "****"
        if settings_dict.get("image_api_key"):
            settings_dict["image_api_key"] = "*" * 8 + settings_dict["image_api_key"][-4:] if len(settings_dict["image_api_key"]) > 4 else "****"
        if settings_dict.get("vision_api_key"):
            settings_dict["vision_api_key"] = "*" * 8 + settings_dict["vision_api_key"][-4:] if len(settings_dict["vision_api_key"]) > 4 else "****"
        if settings_dict.get("mineru_token"):
            settings_dict["mineru_token"] = "*" * 8 + settings_dict["mineru_token"][-4:] if len(settings_dict["mineru_token"]) > 4 else "****"
        
        return SettingsResponse(success=True, settings=Settings(**settings_dict))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=SettingsResponse)
async def update_settings(request: SettingsUpdateRequest):
    """Update settings."""
    try:
        current = load_settings()
        
        # Update only provided fields
        # Use dict() for Pydantic v1 compatibility, model_dump() for v2
        if hasattr(request, 'model_dump'):
            update_dict = request.model_dump(exclude_unset=True)
        else:
            update_dict = request.dict(exclude_unset=True)
        
        # Don't overwrite API keys with masked values
        for key in ["llm_api_key", "image_api_key", "vision_api_key", "mineru_token"]:
            if key in update_dict and update_dict[key] and update_dict[key].startswith("*"):
                # Keep existing value
                update_dict.pop(key)
        
        current.update(update_dict)
        save_settings(current)
        
        return SettingsResponse(success=True, settings=Settings(**current))
    except Exception as e:
        import traceback
        print(f"Settings update error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def get_available_models():
    """Get list of available models."""
    return {
        "text_models": [
            {"id": "glm-4-flash", "name": "GLM-4-Flash", "description": "智谱免费文本模型"},
            {"id": "glm-4", "name": "GLM-4", "description": "智谱旗舰文本模型"},
            {"id": "glm-4v-flash", "name": "GLM-4V-Flash", "description": "智谱免费视觉模型"},
        ],
        "image_models": [
            {"id": "cogview-3-flash", "name": "CogView-3-Flash", "description": "智谱免费图像生成"},
            {"id": "cogview-3", "name": "CogView-3", "description": "智谱图像生成"},
        ]
    }
