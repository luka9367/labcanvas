"""Auto mode pipeline - automatically selects the best mode."""

import json
from typing import AsyncGenerator, Dict, Any

from app.services.pipeline.base import BasePipeline, PipelineContext, PipelineResult, PipelineMode
from app.services.pipeline.draft_pipeline import DraftPipeline
from app.services.pipeline.generate_pipeline import GeneratePipeline
from app.services.pipeline.assembly_pipeline import AssemblyPipeline


class AutoPipeline(BasePipeline):
    """Auto mode: Automatically select the best pipeline based on user input."""
    
    async def execute(self, context: PipelineContext) -> PipelineResult:
        """Execute auto-selection pipeline."""
        try:
            # Analyze prompt to determine best mode
            mode = await self._analyze_and_select_mode(context)
            
            # Execute appropriate pipeline
            if mode == PipelineMode.DRAFT:
                pipeline = DraftPipeline(self.llm)
            elif mode == PipelineMode.GENERATE:
                pipeline = GeneratePipeline(self.llm)
            else:
                pipeline = AssemblyPipeline(self.llm)
            
            result = await pipeline.execute(context)
            
            # Add auto-selected mode info
            if result.data is None:
                result.data = {}
            result.data["auto_selected_mode"] = mode.value
            return result
        except Exception as e:
            import traceback
            print(f"Auto pipeline error: {e}")
            print(traceback.format_exc())
            # Fallback to draft mode
            pipeline = DraftPipeline(self.llm)
            result = await pipeline.execute(context)
            if result.data is None:
                result.data = {}
            result.data["auto_selected_mode"] = "draft"
            return result
    
    async def execute_stream(self, context: PipelineContext) -> AsyncGenerator[str, None]:
        """Execute with streaming."""
        yield json.dumps({"step": "analyzing", "message": "Analyzing your request..."})
        
        try:
            mode = await self._analyze_and_select_mode(context)
            yield json.dumps({"step": "mode_selected", "mode": mode.value})
            
            # Delegate to selected pipeline
            if mode == PipelineMode.DRAFT:
                pipeline = DraftPipeline(self.llm)
            elif mode == PipelineMode.GENERATE:
                pipeline = GeneratePipeline(self.llm)
            else:
                pipeline = AssemblyPipeline(self.llm)
            
            async for chunk in pipeline.execute_stream(context):
                try:
                    data = json.loads(chunk)
                    data["auto_selected_mode"] = mode.value
                    yield json.dumps(data)
                except:
                    yield chunk
        except Exception as e:
            yield json.dumps({"step": "error", "message": str(e)})
    
    async def _analyze_and_select_mode(self, context: PipelineContext) -> PipelineMode:
        """Analyze prompt and select best mode."""
        system_prompt = """你是一个智能模式选择器。分析用户的需求并选择最合适的生成模式。

可选模式：
1. draft - 草稿模式：适合快速生成可编辑的流程图草图，用于早期构思和逻辑梳理
2. generate - 生成模式：适合快速生成完整的高保真图像，用于灵感探索和预览
3. assembly - 组装模式：适合生成高质量、可编辑的正式图表，用于论文和演示

选择依据：
- 如果用户提到"草图"、"草稿"、"快速"、"框架"、"简单" → draft
- 如果用户提到"图片"、"效果图"、"预览"、"灵感"、"图像" → generate
- 如果用户提到"正式"、"论文"、"发表"、"高质量"、"可编辑"、"详细" → assembly

只返回模式名称（draft/generate/assembly），不要解释。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context.prompt}
        ]
        
        try:
            response = await self.llm.chat_completion(
                messages,
                temperature=0.1,
            )
            
            content = await self.llm.extract_xml_from_response(response)
            content = content.strip().lower()
            
            # Map response to mode
            if "draft" in content:
                return PipelineMode.DRAFT
            elif "generate" in content:
                return PipelineMode.GENERATE
            elif "assembly" in content:
                return PipelineMode.ASSEMBLY
        except Exception as e:
            print(f"Mode analysis error: {e}")
        
        # Default to assembly for complex requests
        return PipelineMode.ASSEMBLY
