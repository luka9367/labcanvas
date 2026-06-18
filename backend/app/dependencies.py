"""FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends

from app.services.llm_service import LLMService
from app.services.settings_service import SettingsService


async def get_llm_service() -> LLMService:
    """Dependency to get LLM service instance."""
    return LLMService()


async def get_settings_service() -> SettingsService:
    """Dependency to get settings service instance."""
    return SettingsService()


LLMServiceDep = Annotated[LLMService, Depends(get_llm_service)]
SettingsServiceDep = Annotated[SettingsService, Depends(get_settings_service)]
