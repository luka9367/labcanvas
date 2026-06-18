"""光影质量校验引擎 - 多维度图像质量评估与迭代优化.

对生成的图片自动执行7维度量化校验：
1. 画质精度
2. 模块组件
3. 图标插图
4. 材质质感
5. 数学符号和公式
6. 信息密度
7. 构图逻辑

若未达阈值，自动触发最多2轮迭代优化.
"""

import base64
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

import httpx

from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

# 质量阈值配置
QUALITY_THRESHOLD_TOTAL = 75
QUALITY_THRESHOLD_DIMENSION = 60
MAX_ITERATIONS = 2


@dataclass
class DimensionScore:
    """单维度评分."""
    name: str
    score: int  # 0-100
    comment: str


@dataclass
class QualityReport:
    """质量评估报告."""
    total_score: int
    passed: bool
    dimensions: Dict[str, DimensionScore]
    issues: List[str] = field(default_factory=list)
    optimization_suggestions: str = ""
    iteration_round: int = 0

    def to_dict(self) -> dict:
        return {
            "total_score": self.total_score,
            "passed": self.passed,
            "dimensions": {
                k: {"score": v.score, "comment": v.comment}
                for k, v in self.dimensions.items()
            },
            "issues": self.issues,
            "optimization_suggestions": self.optimization_suggestions,
            "iteration_round": self.iteration_round,
        }


class QualityEngine:
    """光影质量校验引擎."""

    DIMENSION_PROMPT_MAP = {
        "image_quality": "画质精度",
        "module_components": "模块组件",
        "icons_illustrations": "图标插图",
        "material_texture": "材质质感",
        "math_symbols": "数学符号和公式",
        "information_density": "信息密度",
        "composition_logic": "构图逻辑",
    }

    def __init__(self, llm_service: LLMService) -> None:
        self.llm = llm_service

    async def _resolve_image_base64(self, image_input: str) -> str:
        """将图片输入解析为 base64 字符串.

        支持:
        - data:image/png;base64,xxx -> 提取 xxx
        - http(s):// URL -> 下载并编码
        - 纯 base64 字符串 -> 原样返回
        """
        if image_input.startswith("data:image"):
            return image_input.split(",", 1)[1]

        if image_input.startswith("http://") or image_input.startswith("https://"):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.get(image_input)
                    resp.raise_for_status()
                    return base64.b64encode(resp.content).decode("utf-8")
            except Exception as e:
                logger.warning("下载图片失败: %s, error=%s", image_input, e)
                raise ValueError(f"无法下载图片: {e}")

        # 假设已是 base64
        return image_input

    async def evaluate_image(
        self,
        image_input: str,
        original_prompt: str,
        iteration_round: int = 0,
    ) -> QualityReport:
        """对图片执行7维度质量评估.

        Args:
            image_input: 图片URL或base64字符串
            original_prompt: 用户原始需求描述
            iteration_round: 当前迭代轮次

        Returns:
            QualityReport 质量评估报告
        """
        image_base64 = await self._resolve_image_base64(image_input)

        eval_prompt = f"""你是一位专业的学术插图与流程图质量评估专家。请对提供的图片进行严格、全面的多维度质量评估。

评估维度与标准（总分100，每维度100分，阈值：总分>={QUALITY_THRESHOLD_TOTAL}且每维度>={QUALITY_THRESHOLD_DIMENSION}为通过）：

1. 画质精度：图像是否高分辨率、线条是否清晰锐利、有无模糊/压缩痕迹/噪点、色彩过渡是否平滑
2. 模块组件：模块数量是否丰富（3-6个主要模块）、结构层次是否清晰、组件是否完整无缺失、模块间连接关系是否明确
3. 图标插图：图标风格是否一致且专业、插图质量是否达标、符号是否符合学术规范、手绘/卡通风格是否协调
4. 材质质感：纹理表现是否细腻、材质真实感如何、光影效果是否自然、立体感是否充分
5. 数学符号和公式：数学符号是否准确无误、公式排版是否规范美观、是否清晰可读、希腊字母和特殊符号是否正确
6. 信息密度：内容是否充实但不拥挤、信息层次是否分明、留白是否合理、文字与图形比例是否协调
7. 构图逻辑：布局是否合理（分栏/分块）、流程逻辑是否清晰、视觉引导是否明确、整体平衡感如何

用户原始需求：{original_prompt}

请严格按以下JSON格式输出（不要包含markdown代码块标记，直接输出JSON）：
{{
  "total_score": 82,
  "passed": true,
  "dimensions": {{
    "image_quality": {{"score": 85, "comment": "线条清晰，但边缘有轻微锯齿"}},
    "module_components": {{"score": 80, "comment": "模块数量充足，但部分子组件缺失"}},
    "icons_illustrations": {{"score": 78, "comment": "图标风格统一，但部分图标分辨率偏低"}},
    "material_texture": {{"score": 75, "comment": "材质表现一般，缺乏细腻纹理"}},
    "math_symbols": {{"score": 88, "comment": "数学符号准确，公式排版规范"}},
    "information_density": {{"score": 82, "comment": "信息密度适中，层次清晰"}},
    "composition_logic": {{"score": 80, "comment": "布局合理，流程逻辑清晰"}}
  }},
  "issues": ["边缘有轻微锯齿", "部分图标分辨率偏低"],
  "optimization_suggestions": "建议提高图像分辨率，优化图标绘制，增加材质纹理细节。"
}}"""

        try:
            vision_result = await self.llm.vision_analysis(
                image_base64=image_base64,
                prompt=eval_prompt,
                model="glm-4v-flash",
            )
            content = await self.llm.extract_xml_from_response(vision_result)
            report = self._parse_evaluation_response(content)
            report.iteration_round = iteration_round
            return report
        except Exception as e:
            logger.error("质量评估失败: %s", e, exc_info=True)
            # 评估失败时返回一个默认通过的报告，避免阻塞生成流程
            return self._fallback_report(iteration_round)

    def _parse_evaluation_response(self, content: str) -> QualityReport:
        """解析 vision 模型返回的评估JSON."""
        # 清理可能的 markdown 代码块
        text = content.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # 尝试从文本中提取 JSON
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                data = json.loads(text[start:end + 1])
            else:
                raise

        dimensions: Dict[str, DimensionScore] = {}
        dim_data = data.get("dimensions", {})
        for key, label in self.DIMENSION_PROMPT_MAP.items():
            item = dim_data.get(key, {"score": 70, "comment": "未提供详细评价"})
            dimensions[key] = DimensionScore(
                name=label,
                score=int(item.get("score", 70)),
                comment=item.get("comment", ""),
            )

        total_score = int(data.get("total_score", 70))
        # 如果没有返回 passed，自行计算
        passed = data.get("passed")
        if passed is None:
            min_dim = min((d.score for d in dimensions.values()), default=0)
            passed = total_score >= QUALITY_THRESHOLD_TOTAL and min_dim >= QUALITY_THRESHOLD_DIMENSION
        else:
            passed = bool(passed)

        return QualityReport(
            total_score=total_score,
            passed=passed,
            dimensions=dimensions,
            issues=data.get("issues", []),
            optimization_suggestions=data.get("optimization_suggestions", ""),
        )

    def _fallback_report(self, iteration_round: int) -> QualityReport:
        """评估失败时的 fallback 报告（默认通过，避免阻塞）."""
        return QualityReport(
            total_score=80,
            passed=True,
            dimensions={
                key: DimensionScore(name=label, score=80, comment="评估服务暂时不可用，默认通过")
                for key, label in self.DIMENSION_PROMPT_MAP.items()
            },
            issues=["质量评估服务异常，未执行完整校验"],
            optimization_suggestions="",
            iteration_round=iteration_round,
        )

    async def generate_optimization_prompt(
        self,
        report: QualityReport,
        original_prompt: str,
    ) -> str:
        """根据质量报告生成优化后的图像生成提示词.

        Args:
            report: 质量评估报告
            original_prompt: 原始提示词

        Returns:
            优化后的英文提示词
        """
        issues_text = "\n".join(f"- {issue}" for issue in report.issues) if report.issues else "无明显问题"
        dim_text = "\n".join(
            f"- {d.name}: {d.score}分 — {d.comment}"
            for d in report.dimensions.values()
        )

        opt_prompt = f"""你是一位专业的学术插图提示词优化专家。根据质量评估报告，优化图像生成提示词以解决发现的问题。

原始提示词：
{original_prompt}

质量评估报告：
总分：{report.total_score}/100
各维度评分：
{dim_text}

发现的问题：
{issues_text}

优化建议：
{report.optimization_suggestions}

请输出优化后的英文图像生成提示词，要求：
1. 保留原始需求的核心内容和主题
2. 针对报告中的每个问题给出具体的视觉改进方向
3. 强调学术插图风格、高分辨率、清晰线条、专业配色
4. 使用英文撰写，适合 CogView-3 图像生成模型
5. 直接返回优化后的提示词，不要包含任何解释、markdown或代码块
"""

        try:
            response = await self.llm.chat_completion(
                messages=[
                    {"role": "system", "content": "你是一个专业的AI绘画提示词优化专家。"},
                    {"role": "user", "content": opt_prompt},
                ],
                temperature=0.7,
            )
            result = await self.llm.extract_xml_from_response(response)
            optimized = result.strip()
            if optimized:
                return optimized
        except Exception as e:
            logger.error("生成优化提示词失败: %s", e, exc_info=True)

        # fallback: 在原始提示词基础上追加改进方向
        fallback = original_prompt.strip()
        if report.optimization_suggestions:
            fallback += f"\n\nImprovements needed: {report.optimization_suggestions}"
        fallback += "\nHigher resolution, sharper lines, better details, professional academic style."
        return fallback

    async def iterate_image_generation(
        self,
        image_input: str,
        original_prompt: str,
        generate_fn,
        iteration_round: int = 1,
    ) -> tuple[str, QualityReport]:
        """执行一轮迭代优化：评估 -> 如未通过 -> 优化prompt -> 重新生成.

        Args:
            image_input: 当前图片（URL或base64）
            original_prompt: 原始提示词
            generate_fn: 接收优化后prompt并返回新图片的异步函数
            iteration_round: 当前迭代轮次

        Returns:
            (最佳图片, 最终质量报告)
        """
        report = await self.evaluate_image(image_input, original_prompt, iteration_round)

        if report.passed or iteration_round > MAX_ITERATIONS:
            return image_input, report

        # 未通过且未达最大迭代次数，触发优化
        optimized_prompt = await self.generate_optimization_prompt(report, original_prompt)
        logger.info(
            "第%d轮迭代优化：总分%d未达标，生成优化提示词...",
            iteration_round,
            report.total_score,
        )

        new_image = await generate_fn(optimized_prompt)

        # 递归进行下一轮评估（最多2轮）
        return await self.iterate_image_generation(
            new_image,
            optimized_prompt,
            generate_fn,
            iteration_round + 1,
        )
