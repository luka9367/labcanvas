"""Base pipeline class and types."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any, AsyncGenerator
from enum import Enum


class PipelineMode(str, Enum):
    """Pipeline generation modes."""
    AUTO = "auto"
    DRAFT = "draft"
    GENERATE = "generate"
    ASSEMBLY = "assembly"


@dataclass
class PipelineResult:
    """Result from pipeline execution."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    
    # For streaming results
    is_stream: bool = False
    stream_content: Optional[str] = None


@dataclass
class PipelineContext:
    """Context for pipeline execution."""
    prompt: str
    mode: PipelineMode
    reference_image: Optional[str] = None  # base64
    style_reference: Optional[str] = None
    language: str = "zh"
    user_settings: Optional[Dict[str, Any]] = None


class BasePipeline(ABC):
    """Base class for all pipelines."""
    
    def __init__(self, llm_service):
        self.llm = llm_service
    
    async def _get_reference_analysis(self, context: PipelineContext) -> str:
        """Analyze reference image using vision model and return text description.
        
        glm-4-flash does not support image_url in chat_completion messages,
        so we use vision_analysis (glm-4v-flash) to get a text description first.
        """
        if not context.reference_image:
            return ""
        try:
            vision_result = await self.llm.vision_analysis(
                image_base64=context.reference_image,
                prompt="请详细描述这张图片的内容、风格、颜色、布局和构图特点。",
            )
            description = await self.llm.extract_xml_from_response(vision_result)
            return description.strip() if description else ""
        except Exception as e:
            print(f"Vision analysis error: {e}")
            return ""
    
    @abstractmethod
    async def execute(self, context: PipelineContext) -> PipelineResult:
        """Execute the pipeline."""
        pass
    
    @abstractmethod
    async def execute_stream(self, context: PipelineContext) -> AsyncGenerator[str, None]:
        """Execute the pipeline with streaming output."""
        pass
