"""Generate mode pipeline - generates high-fidelity images."""

import json
from typing import AsyncGenerator, Optional, Dict, Any

from app.services.pipeline.base import BasePipeline, PipelineContext, PipelineResult


class GeneratePipeline(BasePipeline):
    """Generate mode: Directly generate high-fidelity images.
    
    Steps:
    1. Analyze user prompt and generate image generation prompt
    2. Call image generation API (CogView)
    3. Return image URL/data
    """
    
    async def execute(self, context: PipelineContext) -> PipelineResult:
        """Execute generate pipeline."""
        try:
            # Step 1: Optimize prompt for image generation
            optimized_prompt = await self._optimize_prompt(context)
            
            # Step 2: Generate image
            image_result = await self.llm.generate_image(
                prompt=optimized_prompt,
                size="1024x1024",
                quality="standard"
            )
            
            # Extract image URL from response
            image_url = self._extract_image_url(image_result)
            
            if not image_url:
                return PipelineResult(
                    success=False,
                    message="Failed to generate image: no URL returned"
                )
            
            return PipelineResult(
                success=True,
                message="Image generated successfully",
                data={
                    "image_url": image_url,
                    "prompt": optimized_prompt,
                    "mode": "generate"
                }
            )
        except Exception as e:
            import traceback
            print(f"Generate pipeline error: {e}")
            print(traceback.format_exc())
            return PipelineResult(
                success=False,
                message=f"Image generation failed: {str(e)}"
            )
    
    async def execute_stream(self, context: PipelineContext) -> AsyncGenerator[str, None]:
        """Execute with streaming."""
        yield json.dumps({"step": "planning", "message": "Optimizing prompt..."})
        
        try:
            optimized_prompt = await self._optimize_prompt(context)
            yield json.dumps({"step": "prompt_ready", "prompt": optimized_prompt})
            
            yield json.dumps({"step": "generating", "message": "Generating image..."})
            
            image_result = await self.llm.generate_image(
                prompt=optimized_prompt,
                size="1024x1024",
                quality="standard"
            )
            
            image_url = self._extract_image_url(image_result)
            
            if not image_url:
                yield json.dumps({"step": "error", "message": "Failed to generate image: no URL returned"})
                return
            
            yield json.dumps({
                "step": "complete",
                "image_url": image_url,
                "prompt": optimized_prompt,
                "mode": "generate"
            })
        except Exception as e:
            yield json.dumps({"step": "error", "message": str(e)})
    
    async def _optimize_prompt(self, context: PipelineContext) -> str:
        """Optimize user prompt for image generation."""
        system_prompt = """你是一个专业的学术插图提示词优化专家。

将用户的描述转换为高质量的图像生成提示词，必须达到以下质量基准（参考优秀学术论文插图样张）：

1. 使用英文撰写（图像生成模型对英文理解更好）
2. 包含详细的视觉描述
3. 指定风格：
   - 学术论文风格 (academic paper style)
   - 技术插图风格 (technical illustration)
   - 流程图风格 (flowchart style)
   - 系统架构风格 (system architecture)
4. 质量基准要求（必须满足）：
   - 视觉质量：高分辨率、线条清晰锐利、无模糊或压缩痕迹
   - 文字清晰度：所有文字必须清晰可读，中英文混合标注，字号层次分明
   - 信息密度：高密度但不拥挤，包含3-6个主要模块，每个模块有详细子组件
   - 细节表现：精确的数据标注（精确到小数点）、完整的数学符号和公式
   - 模块数量：丰富的模块和流程框图，模块间有清晰的连接关系和数据流
   - 色彩还原度：专业学术配色（蓝色、黄色、灰色、绿色、粉色等），色彩对比度适中
   - 整体风格：学术论文图表风格，手绘/卡通风格图标和插图，清晰的分块和边框
   - 布局构图：清晰的分栏或分块布局，流程逻辑明确，留白合理
5. 包含构图、色彩、光影等细节
6. 适合 CogView 等图像生成模型

输出格式：直接返回优化后的英文提示词，不要包含解释。"""

        style_hint = context.style_reference or "academic paper style, technical illustration"
        user_prompt = f"""描述：{context.prompt}

风格参考：{style_hint}

请优化为图像生成提示词。"""

        if context.reference_image:
            ref_desc = await self._get_reference_analysis(context)
            if ref_desc:
                user_prompt = f"""描述：{context.prompt}

参考图片风格描述：{ref_desc}

风格参考：{style_hint}

请结合参考图片的风格，优化为图像生成提示词。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = await self.llm.chat_completion(
                messages,
                temperature=0.7,
            )
            
            result = await self.llm.extract_xml_from_response(response)
            return result.strip()
        except Exception as e:
            print(f"Prompt optimization error: {e}")
            # Return basic prompt
            return f"Academic paper style technical illustration: {context.prompt}. Clean, professional, high quality, suitable for publication."
    
    def _extract_image_url(self, result: Dict[str, Any]) -> Optional[str]:
        """Extract image URL from API response."""
        if not isinstance(result, dict):
            return None
            
        # OpenAI-compatible format
        data = result.get("data", [])
        if data and isinstance(data, list) and len(data) > 0:
            return data[0].get("url") or data[0].get("b64_json")
        
        # Alternative format - direct URL
        if "url" in result:
            return result["url"]
        if "b64_json" in result:
            return result["b64_json"]
        
        # Zhipu AI format
        if "data" in result and isinstance(result["data"], dict):
            return result["data"].get("url", result["data"].get("b64_json"))
        
        return None
