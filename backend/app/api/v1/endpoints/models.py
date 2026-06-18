"""Model management endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def list_models():
    """List all available models."""
    return {
        "success": True,
        "models": {
            "text": [
                {
                    "id": "glm-4-flash",
                    "name": "GLM-4-Flash",
                    "provider": "zhipu",
                    "description": "智谱AI免费文本模型，适合日常对话和文本生成",
                    "features": ["chat", "json_mode"],
                    "max_tokens": 128000,
                    "free": True
                },
                {
                    "id": "glm-4",
                    "name": "GLM-4",
                    "provider": "zhipu",
                    "description": "智谱AI旗舰文本模型，高性能",
                    "features": ["chat", "json_mode", "function_calling"],
                    "max_tokens": 128000,
                    "free": False
                },
                {
                    "id": "glm-4v-flash",
                    "name": "GLM-4V-Flash",
                    "provider": "zhipu",
                    "description": "智谱AI免费视觉模型，支持图像理解",
                    "features": ["vision", "chat"],
                    "max_tokens": 8000,
                    "free": True
                }
            ],
            "image": [
                {
                    "id": "cogview-3-flash",
                    "name": "CogView-3-Flash",
                    "provider": "zhipu",
                    "description": "智谱AI免费图像生成模型",
                    "features": ["text_to_image"],
                    "sizes": ["1024x1024", "768x1344", "1344x768"],
                    "free": True
                },
                {
                    "id": "cogview-3",
                    "name": "CogView-3",
                    "provider": "zhipu",
                    "description": "智谱AI图像生成模型，高质量",
                    "features": ["text_to_image"],
                    "sizes": ["1024x1024", "768x1344", "1344x768"],
                    "free": False
                }
            ]
        }
    }


@router.get("/providers")
async def list_providers():
    """List supported model providers."""
    return {
        "success": True,
        "providers": [
            {
                "id": "zhipu",
                "name": "智谱AI",
                "description": "智谱AI大模型平台",
                "base_url": "https://open.bigmodel.cn/api/paas/v4",
                "website": "https://bigmodel.cn"
            }
        ]
    }
