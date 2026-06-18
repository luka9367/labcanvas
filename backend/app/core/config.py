"""Minimal static configuration. LLM values are fallbacks; runtime overrides come from settings_service."""

import os
from pathlib import Path
from types import SimpleNamespace

PROJECT_NAME = "LabCanvas"
VERSION = "0.19.0"
API_V1_PREFIX = "/api/v1"

# 生产环境可设置 CORS_ALLOW_ALL=true 允许所有来源（适合公网部署）
# 或设置 CORS_ORIGINS=https://a.com,https://b.com 指定白名单
_cors_env = os.environ.get("CORS_ORIGINS", "")
if os.environ.get("CORS_ALLOW_ALL", "").lower() in ("true", "1", "yes"):
    CORS_ORIGINS: list[str] = ["*"]
elif _cors_env:
    CORS_ORIGINS: list[str] = [o.strip() for o in _cors_env.split(",") if o.strip()]
else:
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://embed.diagrams.net",
    ]

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
# Use project directory for data storage instead of user home
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
REFERENCES_DIR = DATA_DIR / "references"

# Ensure data directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
REFERENCES_DIR.mkdir(parents=True, exist_ok=True)

# Fallback LLM settings (overridden by settings_service at runtime)
# 智谱AI默认配置
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
LLM_MODEL = os.environ.get("LLM_MODEL", "glm-4-flash")
LLM_IMAGE_MODEL = os.environ.get("LLM_IMAGE_MODEL", "cogview-3-flash")
LLM_IMAGE_MODEL_BACKUP = os.environ.get("LLM_IMAGE_MODEL_BACKUP", "")
LLM_IMAGE_MODEL_FLASH = os.environ.get("LLM_IMAGE_MODEL_FLASH", "cogview-3-flash")
LLM_COMPONENT_MODEL = os.environ.get("LLM_COMPONENT_MODEL", "glm-4-flash")

LLM_MAX_RETRIES = int(os.environ.get("LLM_MAX_RETRIES", "3"))
LLM_GLOBAL_IMAGE_CONCURRENCY = int(os.environ.get("LLM_GLOBAL_IMAGE_CONCURRENCY", "8"))

GALLERY_CDN_BASE = os.environ.get("GALLERY_CDN_BASE", "")

ENABLE_AI_ASSISTANT = os.environ.get("ENABLE_AI_ASSISTANT", "true").lower() in (
    "1",
    "true",
    "yes",
)

# Logical key prefix for project/image storage paths (not cloud credentials)
S3_PREFIX = os.environ.get("LABCANVAS_STORAGE_PREFIX", "labcanvas")

settings = SimpleNamespace(
    PROJECT_NAME=PROJECT_NAME,
    VERSION=VERSION,
    API_V1_PREFIX=API_V1_PREFIX,
    CORS_ORIGINS=CORS_ORIGINS,
    STATIC_DIR=STATIC_DIR,
    DATA_DIR=DATA_DIR,
    LLM_API_KEY=LLM_API_KEY,
    LLM_BASE_URL=LLM_BASE_URL,
    LLM_MODEL=LLM_MODEL,
    LLM_IMAGE_MODEL=LLM_IMAGE_MODEL,
    LLM_IMAGE_MODEL_BACKUP=LLM_IMAGE_MODEL_BACKUP,
    LLM_IMAGE_MODEL_FLASH=LLM_IMAGE_MODEL_FLASH,
    LLM_COMPONENT_MODEL=LLM_COMPONENT_MODEL,
    LLM_MAX_RETRIES=LLM_MAX_RETRIES,
    LLM_GLOBAL_IMAGE_CONCURRENCY=LLM_GLOBAL_IMAGE_CONCURRENCY,
    GALLERY_CDN_BASE=GALLERY_CDN_BASE,
    ENABLE_AI_ASSISTANT=ENABLE_AI_ASSISTANT,
    S3_PREFIX=S3_PREFIX,
    s3_configured=False,
)
