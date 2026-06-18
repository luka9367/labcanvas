"""Schemas for settings endpoints."""

from typing import Optional
from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Application settings schema."""
    llm_api_key: str = Field(default="", description="智谱AI API Key")
    llm_base_url: str = Field(default="https://open.bigmodel.cn/api/paas/v4", description="API Base URL")
    llm_model: str = Field(default="glm-4-flash", description="文本模型")
    llm_image_model: str = Field(default="cogview-3-flash", description="图像生成模型")
    llm_component_model: str = Field(default="glm-4-flash", description="组件生成模型")
    image_api_key: str = Field(default="", description="图像API Key（可选）")
    vision_api_key: str = Field(default="", description="视觉API Key（可选）")
    image_base_url: str = Field(default="", description="图像API Base URL（可选）")
    vision_base_url: str = Field(default="", description="视觉API Base URL（可选）")
    api_format: str = Field(default="openai", description="API格式")
    nanasoul_prompt: str = Field(default="", description="NanaSoul AI助手角色设定")
    mineru_token: str = Field(default="", description="MinerU PDF解析Token")
    theme: str = Field(default="light", description="界面主题")
    language: str = Field(default="zh", description="界面语言")


class SettingsResponse(BaseModel):
    """Settings response schema."""
    success: bool
    settings: Settings


class SettingsUpdateRequest(BaseModel):
    """Settings update request schema."""
    llm_api_key: Optional[str] = None
    llm_base_url: Optional[str] = None
    llm_model: Optional[str] = None
    llm_image_model: Optional[str] = None
    llm_component_model: Optional[str] = None
    image_api_key: Optional[str] = None
    vision_api_key: Optional[str] = None
    image_base_url: Optional[str] = None
    vision_base_url: Optional[str] = None
    api_format: Optional[str] = None
    nanasoul_prompt: Optional[str] = None
    mineru_token: Optional[str] = None
    theme: Optional[str] = None
    language: Optional[str] = None
