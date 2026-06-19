"""多层 Prompt 工程架构 — 系统性提升免费图像模型输出质量.

基于 CogView-3-Flash 的特性，设计 4 层渐进式提示词优化：
1. 需求结构化分析：识别场景类型（学术/日常）、提取关键元素、选择构图模板
2. 核心提示词生成：构建主体描述与视觉规范
3. 质量增强层：负面排除 + 细节强化 + CogView 技巧
4. 参考图风格融合：提取并注入参考图的风格特征
"""

import json
import logging
from typing import Dict, List, Optional

from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class RequirementAnalysis:
    """需求结构化分析结果."""

    def __init__(
        self,
        scene_type: str,
        chart_type: str,
        key_elements: List[str],
        composition_template: str,
        style_tags: List[str],
        detail_level: str,
    ) -> None:
        self.scene_type = scene_type
        self.chart_type = chart_type
        self.key_elements = key_elements
        self.composition_template = composition_template
        self.style_tags = style_tags
        self.detail_level = detail_level


class PromptEngine:
    """多层 Prompt 工程引擎."""

    # CogView-3-Flash 优化技巧与负面排除词库
    COGVIEW_NEGATIVE_PROMPT = (
        "blurry, low resolution, compressed, jpeg artifacts, "
        "deformed, distorted, ugly, bad anatomy, wrong proportions, "
        "text gibberish, unreadable text, misspelled words, "
        "watermark, signature, cropped, out of frame, "
        "duplicate, morbid, mutilated, extra fingers, mutated hands, "
        "poorly drawn hands, poorly drawn face, mutation, deformed iris, "
        "bad art, bad sketch, amateur drawing, childish style, "
        "oversaturated, underexposed, overexposed, noise, grainy"
    )

    # 学术图表构图模板库
    ACADEMIC_COMPOSITION_TEMPLATES: Dict[str, str] = {
        "system_architecture": (
            "system architecture diagram with clear hierarchical layers, "
            "top-down or left-right flow, modules arranged in logical groups, "
            "clean connecting arrows with data flow labels"
        ),
        "flowchart": (
            "flowchart with rectangular process boxes, diamond decision nodes, "
            "oval start/end nodes, directional arrows showing sequential logic, "
            "organized in swimlanes or linear progression"
        ),
        "algorithm": (
            "algorithm illustration with step-by-step pseudocode blocks, "
            "loop indicators, conditional branches, input/output boxes, "
            "mathematical formulas integrated into the layout"
        ),
        "data_visualization": (
            "data visualization with coordinated charts (bar, line, scatter), "
            "legends, axis labels, grid lines, annotated data points, "
            "consistent color scheme across all subplots"
        ),
        "neural_network": (
            "neural network architecture diagram with layered node groups, "
            "weighted connection lines, activation function annotations, "
            "tensor shape labels, forward/backward flow arrows"
        ),
        "framework": (
            "methodology framework with central concept surrounded by components, "
            "radial or modular layout, clear boundary definitions, "
            "bidirectional relationship arrows"
        ),
        "comparison": (
            "comparison diagram with side-by-side columns or rows, "
            "aligned feature checklists, visual contrast indicators, "
            "summary conclusion block at bottom"
        ),
    }

    # 日常场景构图模板库
    DAILY_COMPOSITION_TEMPLATES: Dict[str, str] = {
        "animal": (
            "adorable animal portrait or scene with natural pose, "
            "soft natural lighting, shallow depth of field feel, "
            "warm and friendly atmosphere"
        ),
        "festival": (
            "festive celebration scene with seasonal decorations, "
            "warm inviting lighting, rich colors, joyful atmosphere, "
            "balanced composition with clear focal point"
        ),
        "portrait": (
            "natural portrait with soft flattering lighting, "
            "authentic expression, clean background, "
            "warm skin tones and lifelike details"
        ),
        "campus": (
            "scenic campus view with iconic architecture, "
            "pleasant outdoor lighting, green landscaping, "
            "balanced composition showing the spirit of the place"
        ),
        "nature": (
            "natural landscape with clear depth, soft natural light, "
            "vibrant but realistic colors, serene and refreshing mood"
        ),
        "lifestyle": (
            "everyday life scene with natural composition, "
            "soft ambient lighting, relatable atmosphere, "
            "clean and pleasant visual style"
        ),
    }

    # 风格标签映射
    STYLE_ENHANCEMENTS: Dict[str, str] = {
        "academic": (
            "academic paper figure style, IEEE/ACM publication quality, "
            "professional technical illustration, clean vector-like appearance, "
            "precise geometric shapes, consistent line weights"
        ),
        "technical": (
            "technical documentation illustration, engineering blueprint aesthetic, "
            "orthogonal projections, dimension annotations, standardized symbols"
        ),
        "minimalist": (
            "minimalist information design, flat design style, "
            "generous white space, restrained color palette (2-4 colors), "
            "icon-based visual communication"
        ),
        "vibrant": (
            "vibrant scientific illustration, gradient accents, "
            "3D isometric perspective, glossy material effects, "
            "dynamic composition with depth"
        ),
        "realistic": (
            "photorealistic style, natural lighting and shadows, "
            "true-to-life colors, fine surface details, "
            "authentic textures and materials"
        ),
        "cute": (
            "cute and charming style, rounded soft shapes, "
            "warm pastel colors, friendly and approachable mood, "
            "appealing characterful details"
        ),
        "festive": (
            "festive and cheerful style, rich warm colors, "
            "decorative details, celebratory atmosphere, "
            "inviting and joyful visual tone"
        ),
        "casual": (
            "casual everyday illustration style, relaxed composition, "
            "natural colors, approachable and down-to-earth mood"
        ),
    }

    # 用于判断是否为学术场景的关键词
    ACADEMIC_KEYWORDS = {
        "图", "图表", "流程图", "架构图", "算法", "神经网络", "框架",
        "数据", "可视化", "对比", "系统", "模块", "论文", "学术", "研究",
        "方法", "模型", "流程", "结构", "关系", "逻辑", "分析", "统计",
        "函数", "公式", "定理", "证明", "矩阵", "向量", "分类", "回归",
        "clustering", "machine learning", "deep learning", "neural",
        "architecture", "flowchart", "diagram", "framework", "algorithm",
        "data visualization", "chart", "graph", "system", "model",
    }

    def __init__(self, llm_service: LLMService) -> None:
        self.llm = llm_service

    def _detect_scene_type(self, user_prompt: str) -> str:
        """启发式判断场景类型：academic 或 daily."""
        text = user_prompt.lower()
        for kw in self.ACADEMIC_KEYWORDS:
            if kw.lower() in text:
                return "academic"
        return "daily"

    async def optimize(
        self,
        user_prompt: str,
        style_reference: Optional[str] = None,
        reference_image_analysis: Optional[str] = None,
    ) -> Dict[str, str]:
        """执行完整的4层提示词优化.

        Returns:
            {
                "prompt": 最终优化后的英文提示词,
                "negative_prompt": 负面提示词,
                "analysis": 结构化分析摘要(JSON字符串),
            }
        """
        # Level 1: 需求结构化分析
        analysis = await self._analyze_requirement(user_prompt, style_reference)

        # Level 2: 核心提示词生成
        base_prompt = self._build_base_prompt(user_prompt, analysis)

        # Level 3: 质量增强层
        enhanced_prompt = self._apply_quality_boost(base_prompt, analysis)

        # Level 4: 参考图风格融合
        if reference_image_analysis:
            enhanced_prompt = self._apply_style_anchor(
                enhanced_prompt, reference_image_analysis, analysis
            )

        return {
            "prompt": enhanced_prompt,
            "negative_prompt": self.COGVIEW_NEGATIVE_PROMPT,
            "analysis": json.dumps(
                {
                    "scene_type": analysis.scene_type,
                    "chart_type": analysis.chart_type,
                    "key_elements": analysis.key_elements,
                    "composition_template": analysis.composition_template,
                    "style_tags": analysis.style_tags,
                    "detail_level": analysis.detail_level,
                },
                ensure_ascii=False,
            ),
        }

    async def _analyze_requirement(
        self, user_prompt: str, style_reference: Optional[str]
    ) -> RequirementAnalysis:
        """Level 1: 需求结构化分析 — 使用 LLM 识别场景类型与关键元素."""
        system_prompt = """你是一位图像需求分析专家。请对用户描述进行结构化分析。

首先判断场景类型：
- academic（学术/技术图表）: 用户需要流程图、架构图、算法图、数据可视化、神经网络图、框架图、对比图等
- daily（日常生活场景）: 用户描述的是动物、节日、人物、校园风景、自然风光、生活日常等

必须按以下JSON格式输出（直接输出JSON，不要markdown代码块）：
{
  "scene_type": "academic|daily",
  "chart_type": "system_architecture|flowchart|algorithm|data_visualization|neural_network|framework|comparison|animal|festival|portrait|campus|nature|lifestyle|other",
  "key_elements": ["元素1", "元素2", "元素3"],
  "composition_template": "简短描述推荐的构图方式",
  "style_tags": ["标签1", "标签2"],
  "detail_level": "high|medium|low"
}

chart_type 必须从以下选择：
学术类：system_architecture, flowchart, algorithm, data_visualization, neural_network, framework, comparison, other
日常类：animal, festival, portrait, campus, nature, lifestyle, other

style_tags 从以下选择（可多选）：
academic, technical, minimalist, vibrant, realistic, cute, festive, casual

注意：
- 如果是 daily 场景，不要返回 academic/technical 标签
- 如果是 academic 场景，不要返回 cute/festive/casual 标签
- 标签数量建议 1-2 个"""

        user_text = f"用户描述：{user_prompt}"
        if style_reference:
            user_text += f"\n风格参考：{style_reference}"

        try:
            response = await self.llm.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text},
                ],
                temperature=0.3,
            )
            content = await self.llm.extract_xml_from_response(response)
            data = json.loads(content.strip())

            scene_type = data.get("scene_type", self._detect_scene_type(user_prompt))
            chart_type = data.get("chart_type", "other")
            style_tags = data.get("style_tags", ["realistic" if scene_type == "daily" else "academic"])

            # 防御性清洗：日常场景强制移除学术标签
            if scene_type == "daily":
                style_tags = [t for t in style_tags if t not in ("academic", "technical")]
                if not style_tags:
                    style_tags = ["realistic"]
            else:
                style_tags = [t for t in style_tags if t not in ("cute", "festive", "casual")]
                if not style_tags:
                    style_tags = ["academic"]

            return RequirementAnalysis(
                scene_type=scene_type,
                chart_type=chart_type,
                key_elements=data.get("key_elements", [user_prompt[:50]]),
                composition_template=data.get(
                    "composition_template", "clear balanced composition"
                ),
                style_tags=style_tags,
                detail_level=data.get("detail_level", "medium"),
            )
        except Exception as e:
            logger.warning("需求结构化分析失败: %s，使用默认分析", e)
            scene_type = self._detect_scene_type(user_prompt)
            return RequirementAnalysis(
                scene_type=scene_type,
                chart_type="other",
                key_elements=[user_prompt[:50]],
                composition_template="clear balanced composition",
                style_tags=["realistic" if scene_type == "daily" else "academic"],
                detail_level="medium",
            )

    def _build_base_prompt(
        self, user_prompt: str, analysis: RequirementAnalysis
    ) -> str:
        """Level 2: 核心提示词生成."""
        if analysis.scene_type == "daily":
            composition = self.DAILY_COMPOSITION_TEMPLATES.get(
                analysis.chart_type,
                "natural everyday scene with balanced composition",
            )
        else:
            composition = self.ACADEMIC_COMPOSITION_TEMPLATES.get(
                analysis.chart_type,
                f"professional {analysis.chart_type.replace('_', ' ')} diagram",
            )

        # 风格增强
        style_parts: List[str] = []
        for tag in analysis.style_tags:
            if tag in self.STYLE_ENHANCEMENTS:
                style_parts.append(self.STYLE_ENHANCEMENTS[tag])
        if analysis.scene_type == "daily":
            default_style = self.STYLE_ENHANCEMENTS["realistic"]
        else:
            default_style = self.STYLE_ENHANCEMENTS["academic"]
        style_text = " ".join(style_parts) if style_parts else default_style

        # 关键元素描述
        elements_text = ", ".join(analysis.key_elements) if analysis.key_elements else user_prompt

        # 细节等级
        detail_map = {
            "high": (
                "rich details, fine textures, crisp edges, "
                "vivid yet natural colors, high visual fidelity"
            ),
            "medium": (
                "clear details, balanced textures, natural colors, "
                "pleasant visual quality"
            ),
            "low": (
                "clean and simple, soft details, minimal clutter, "
                "gentle colors"
            ),
        }
        detail_text = detail_map.get(analysis.detail_level, detail_map["medium"])

        base = (
            f"A high-quality {composition}. "
            f"The image depicts: {elements_text}. "
            f"{style_text}. "
            f"{detail_text}. "
            f"The original subject matter is: {user_prompt}."
        )
        return base

    def _apply_quality_boost(
        self, base_prompt: str, analysis: RequirementAnalysis
    ) -> str:
        """Level 3: 质量增强层 — CogView-3 专属技巧 + 场景化细节强化."""
        # CogView-3 优化后缀
        cogview_boost = (
            "Rendered in high resolution concept art style. "
            "Crisp edges, anti-aliased lines, "
            "subtle depth and dimension, "
            "professionally color-graded with natural contrast, "
            "clean digital illustration."
        )

        # 学术场景额外强化
        academic_boost = (
            "All text elements use clean sans-serif typography, "
            "mathematical symbols rendered in proper LaTeX style, "
            "formulas enclosed in boxes with clear notation, "
            "arrows have consistent arrowheads and orthogonal routing, "
            "modules use rounded rectangles with subtle fill gradients, "
            "background is clean white or very light gray (#f8f9fa)."
        )

        # 日常场景额外强化
        daily_boost = (
            "Natural and lifelike appearance, "
            "avoid artificial or overly staged look, "
            "soft and harmonious color palette, "
            "no harsh artificial filters, "
            "maintain a warm and approachable mood."
        )

        # 构图强化
        composition_boost = (
            f"Composition follows {analysis.composition_template}. "
            "Balanced visual weight distribution, "
            "clear visual hierarchy with primary and secondary elements, "
            "adequate margins and gutters between components."
        )

        if analysis.scene_type == "daily":
            enhanced = (
                f"{base_prompt}\n\n"
                f"Quality specifications: {cogview_boost}\n\n"
                f"Natural look requirements: {daily_boost}\n\n"
                f"Layout requirements: {composition_boost}"
            )
        else:
            enhanced = (
                f"{base_prompt}\n\n"
                f"Quality specifications: {cogview_boost}\n\n"
                f"Academic figure standards: {academic_boost}\n\n"
                f"Layout requirements: {composition_boost}"
            )
        return enhanced

    def _apply_style_anchor(
        self,
        prompt: str,
        reference_analysis: str,
        analysis: RequirementAnalysis,
    ) -> str:
        """Level 4: 参考图风格融合 — 将参考图分析结果注入提示词."""
        anchor = (
            f"Style reference: The illustration should closely match the visual style of the reference image. "
            f"Reference characteristics: {reference_analysis}. "
            f"Maintain consistency in color palette, line style, icon design, and overall aesthetic."
        )
        return f"{prompt}\n\n{anchor}"

    def build_negative_prompt(self, issues: Optional[List[str]] = None) -> str:
        """根据已知问题生成针对性负面提示词."""
        base = self.COGVIEW_NEGATIVE_PROMPT
        if not issues:
            return base

        issue_mapping = {
            "模糊": "blurry, out of focus, soft edges",
            "噪点": "noise, grainy, speckled",
            "文字不清": "gibberish text, unreadable text, scrambled characters",
            "变形": "distorted, deformed, warped",
            "低分辨率": "low resolution, pixelated, low quality",
            "色彩问题": "oversaturated, washed out, color bleeding",
            "构图混乱": "cluttered, chaotic layout, poor composition",
        }

        extras: List[str] = []
        for issue in issues:
            for keyword, neg in issue_mapping.items():
                if keyword in issue:
                    extras.append(neg)

        if extras:
            return f"{base}, {', '.join(extras)}"
        return base
