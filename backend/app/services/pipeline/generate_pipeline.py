"""Generate mode pipeline - 多层优化架构下的高保真图像生成.

升级后的生成架构（免费模型质量跃升方案）：
1. 多层 Prompt 工程（PromptEngine）：需求结构化 → 核心提示词 → 质量增强 → 风格融合
2. 多候选生成（Multi-Candidate）：一次生成 2 张，QualityEngine 择优
3. 负面提示词过滤（Negative Prompt）：排除模糊、变形、文字混乱等常见问题
4. 图像后处理增强（ImageEnhancer）：锐化、边缘增强、对比度、降噪
5. 光影质量校验引擎（QualityEngine）：7维度评估 + 最多2轮迭代
"""

import json
from typing import AsyncGenerator, Optional, Dict, Any, List

from app.services.pipeline.base import BasePipeline, PipelineContext, PipelineResult
from app.services.quality_engine import QualityEngine
from app.services.prompt_engine import PromptEngine
from app.services.image_enhancer import ImageEnhancer


class GeneratePipeline(BasePipeline):
    """Generate mode: 系统性质量提升后的直接生成模式.

    核心升级点：
    - PromptEngine 4层递进优化，让 CogView-3-Flash 理解更精准
    - n=2 多候选生成，避开单张生成的随机性陷阱
    - negative_prompt 主动排除低质量特征
    - ImageEnhancer 算法级锐化与边缘增强
    - QualityEngine 迭代闭环（保留原有能力）
    """

    # 多候选生成数量（免费模型建议 2，平衡配额与效果）
    MULTI_CANDIDATE_N = 2

    async def execute(self, context: PipelineContext) -> PipelineResult:
        """Execute generate pipeline with full optimization stack."""
        try:
            # Step 1: 多层 Prompt 工程优化
            prompt_engine = PromptEngine(self.llm)
            ref_analysis = None
            if context.reference_image:
                ref_analysis = await self._get_reference_analysis(context)

            prompt_result = await prompt_engine.optimize(
                user_prompt=context.prompt,
                style_reference=context.style_reference,
                reference_image_analysis=ref_analysis,
            )
            optimized_prompt = prompt_result["prompt"]
            negative_prompt = prompt_result["negative_prompt"]

            # Step 2: 多候选生成 + 负面提示词
            image_urls = await self.llm.generate_image_multi(
                prompt=optimized_prompt,
                size="1024x1024",
                quality="standard",
                n=self.MULTI_CANDIDATE_N,
                negative_prompt=negative_prompt,
            )

            if not image_urls:
                return PipelineResult(
                    success=False,
                    message="Failed to generate image: no URL returned"
                )

            # Step 3: 多候选择优（用 QualityEngine 快速评估选最佳）
            best_image_url = await self._select_best_candidate(
                image_urls, optimized_prompt
            )

            # Step 4: 图像后处理增强
            enhancer = ImageEnhancer()
            try:
                enhanced_image = enhancer.process(best_image_url)
            except Exception as e:
                # 增强失败不影响主流程，回退到原图
                print(f"Image enhancement failed: {e}")
                enhanced_image = best_image_url

            # Step 5: 光影质量校验 + 迭代优化
            quality_engine = QualityEngine(self.llm)
            final_image, report = await quality_engine.iterate_image_generation(
                enhanced_image,
                optimized_prompt,
                generate_fn=self._regenerate_image,
                iteration_round=1,
            )

            return PipelineResult(
                success=True,
                message="Image generated successfully",
                data={
                    "image_url": final_image,
                    "prompt": optimized_prompt,
                    "mode": "generate",
                    "quality_report": report.to_dict(),
                    "optimization_info": {
                        "candidates_generated": len(image_urls),
                        "negative_prompt_used": bool(negative_prompt),
                        "image_enhanced": enhanced_image != best_image_url,
                        "prompt_analysis": prompt_result.get("analysis"),
                    },
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
        """Execute with streaming including all optimization steps."""
        yield json.dumps({"step": "planning", "message": "正在分析需求并优化提示词..."})

        try:
            # Step 1: 多层 Prompt 工程
            prompt_engine = PromptEngine(self.llm)
            ref_analysis = None
            if context.reference_image:
                ref_analysis = await self._get_reference_analysis(context)

            prompt_result = await prompt_engine.optimize(
                user_prompt=context.prompt,
                style_reference=context.style_reference,
                reference_image_analysis=ref_analysis,
            )
            optimized_prompt = prompt_result["prompt"]
            negative_prompt = prompt_result["negative_prompt"]

            yield json.dumps({
                "step": "prompt_ready",
                "prompt": optimized_prompt,
                "message": "提示词优化完成，进入多候选生成...",
            })

            # Step 2: 多候选生成
            yield json.dumps({
                "step": "generating",
                "message": f"正在生成 {self.MULTI_CANDIDATE_N} 张候选图像并择优...",
            })

            image_urls = await self.llm.generate_image_multi(
                prompt=optimized_prompt,
                size="1024x1024",
                quality="standard",
                n=self.MULTI_CANDIDATE_N,
                negative_prompt=negative_prompt,
            )

            if not image_urls:
                yield json.dumps({"step": "error", "message": "Failed to generate image: no URL returned"})
                return

            # Step 3: 择优
            best_image_url = await self._select_best_candidate(
                image_urls, optimized_prompt
            )

            # Step 4: 图像增强
            yield json.dumps({"step": "enhancing", "message": "正在执行图像后处理增强..."})
            enhancer = ImageEnhancer()
            try:
                enhanced_image = enhancer.process(best_image_url)
            except Exception as e:
                print(f"Image enhancement failed: {e}")
                enhanced_image = best_image_url

            # Step 5: 质量校验
            yield json.dumps({"step": "quality_check", "message": "正在进行光影质量校验..."})

            quality_engine = QualityEngine(self.llm)
            final_image, report = await quality_engine.iterate_image_generation(
                enhanced_image,
                optimized_prompt,
                generate_fn=self._regenerate_image,
                iteration_round=1,
            )

            # 输出质量报告
            yield json.dumps({
                "step": "quality_report",
                "score": report.total_score,
                "passed": report.passed,
                "dimensions": report.to_dict()["dimensions"],
                "issues": report.issues,
                "iteration_round": report.iteration_round,
            })

            yield json.dumps({
                "step": "complete",
                "image_url": final_image,
                "prompt": optimized_prompt,
                "mode": "generate",
                "quality_report": report.to_dict(),
                "optimization_info": {
                    "candidates_generated": len(image_urls),
                    "negative_prompt_used": bool(negative_prompt),
                    "image_enhanced": enhanced_image != best_image_url,
                },
            })
        except Exception as e:
            yield json.dumps({"step": "error", "message": str(e)})

    async def _select_best_candidate(
        self, image_urls: List[str], original_prompt: str
    ) -> str:
        """从多候选中选择质量最高的一张.

        策略：
        1. 如果只有1张，直接返回
        2. 如果有2+张，用 QualityEngine 快速评估，选总分最高的
        """
        if len(image_urls) == 1:
            return image_urls[0]

        quality_engine = QualityEngine(self.llm)
        best_url = image_urls[0]
        best_score = -1

        for url in image_urls:
            try:
                report = await quality_engine.evaluate_image(
                    url, original_prompt, iteration_round=0
                )
                if report.total_score > best_score:
                    best_score = report.total_score
                    best_url = url
            except Exception as e:
                print(f"Candidate evaluation failed: {e}")
                continue

        print(f"Selected best candidate: score={best_score} among {len(image_urls)} images")
        return best_url

    async def _regenerate_image(self, prompt: str) -> str:
        """迭代重生成：使用负面提示词再次生成并增强."""
        prompt_engine = PromptEngine(self.llm)
        negative_prompt = prompt_engine.COGVIEW_NEGATIVE_PROMPT

        # 迭代时也生成多候选并择优
        image_urls = await self.llm.generate_image_multi(
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=self.MULTI_CANDIDATE_N,
            negative_prompt=negative_prompt,
        )

        if not image_urls:
            raise ValueError("Regeneration failed: no URL returned")

        best_url = await self._select_best_candidate(image_urls, prompt)

        # 增强
        enhancer = ImageEnhancer()
        try:
            return enhancer.process(best_url)
        except Exception:
            return best_url

    async def _optimize_prompt(self, context: PipelineContext) -> str:
        """兼容旧接口：内部已迁移到 PromptEngine，此处保留用于其他调用方."""
        prompt_engine = PromptEngine(self.llm)
        ref_analysis = None
        if context.reference_image:
            ref_analysis = await self._get_reference_analysis(context)

        result = await prompt_engine.optimize(
            user_prompt=context.prompt,
            style_reference=context.style_reference,
            reference_image_analysis=ref_analysis,
        )
        return result["prompt"]

    def _extract_image_url(self, result: Dict[str, Any]) -> Optional[str]:
        """Extract image URL from API response."""
        if not isinstance(result, dict):
            return None

        data = result.get("data", [])
        if data and isinstance(data, list) and len(data) > 0:
            return data[0].get("url") or data[0].get("b64_json")

        if "url" in result:
            return result["url"]
        if "b64_json" in result:
            return result["b64_json"]

        if "data" in result and isinstance(result["data"], dict):
            return result["data"].get("url", result["data"].get("b64_json"))

        return None
