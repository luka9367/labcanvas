"""Schemas for generation endpoints."""

from typing import Literal, Optional
from pydantic import BaseModel


class GenerateRequest(BaseModel):
    """Request schema for generation."""
    prompt: str
    mode: Literal["auto", "draft", "generate", "assembly"] = "auto"
    reference_image: Optional[str] = None  # base64 encoded image
    style_reference: Optional[str] = None
    language: str = "zh"


class GenerateResponse(BaseModel):
    """Response schema for generation."""
    success: bool
    message: str
    data: Optional[dict] = None


class ElementGenerateRequest(BaseModel):
    """Request schema for element generation."""
    prompt: str
    element_type: str = "icon"
    style: Optional[str] = None
    size: str = "512x512"


class ElementGenerateResponse(BaseModel):
    """Response schema for element generation."""
    success: bool
    message: str
    image_url: Optional[str] = None
    svg_content: Optional[str] = None
