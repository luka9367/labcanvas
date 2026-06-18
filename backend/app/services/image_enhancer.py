"""图像后处理增强引擎 — 用算法手段提升免费模型输出质量.

针对 CogView-3-Flash 生成的 1024x1024 图像，提供：
- 锐化与边缘增强（提升线条清晰度）
- 对比度与色彩增强（提升视觉冲击力）
- 轻微降噪（去除生成模型的纹理噪声）
- 自适应亮度调整

所有处理基于 Pillow + numpy，无需额外模型。
"""

import base64
import io
import logging
from typing import Optional, Union

import numpy as np
from PIL import Image, ImageFilter, ImageEnhance

logger = logging.getLogger(__name__)


class ImageEnhancer:
    """学术插图专用图像增强器."""

    # 针对学术图表的默认参数（经调优）
    DEFAULT_PARAMS = {
        "sharpen_radius": 2.0,
        "sharpen_percent": 150,
        "sharpen_threshold": 3,
        "contrast_factor": 1.15,
        "color_factor": 1.05,
        "brightness_factor": 1.02,
        "edge_enhance": True,
        "denoise_strength": 0.3,
    }

    def __init__(self, params: Optional[dict] = None) -> None:
        self.params = {**self.DEFAULT_PARAMS, **(params or {})}

    def process(
        self,
        image_input: Union[str, Image.Image],
        output_format: str = "PNG",
    ) -> str:
        """对输入图像执行完整的增强流程，返回 base64 编码结果.

        Args:
            image_input: URL、base64字符串或PIL Image对象
            output_format: 输出格式 PNG/JPEG

        Returns:
            base64 编码的图像字符串（带 data URI 前缀）
        """
        img = self._load_image(image_input)
        if img is None:
            raise ValueError("无法加载输入图像")

        # 确保 RGB 模式
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Step 1: 轻微降噪（中值滤波，保留边缘）
        if self.params.get("denoise_strength", 0) > 0:
            img = self._denoise(img)

        # Step 2: 锐化（Unsharp Mask）
        img = self._sharpen(img)

        # Step 3: 边缘增强
        if self.params.get("edge_enhance", True):
            img = self._edge_enhance(img)

        # Step 4: 对比度增强
        img = self._enhance_contrast(img)

        # Step 5: 色彩饱和度微调
        img = self._enhance_color(img)

        # Step 6: 亮度微调
        img = self._enhance_brightness(img)

        # 编码输出
        buffer = io.BytesIO()
        img.save(buffer, format=output_format)
        buffer.seek(0)
        b64 = base64.b64encode(buffer.read()).decode("utf-8")
        mime = "image/png" if output_format == "PNG" else "image/jpeg"
        return f"data:{mime};base64,{b64}"

    def process_to_pil(
        self,
        image_input: Union[str, Image.Image],
    ) -> Image.Image:
        """处理并返回 PIL Image 对象（用于 Pipeline 内部链式处理）."""
        img = self._load_image(image_input)
        if img is None:
            raise ValueError("无法加载输入图像")

        if img.mode != "RGB":
            img = img.convert("RGB")

        if self.params.get("denoise_strength", 0) > 0:
            img = self._denoise(img)
        img = self._sharpen(img)
        if self.params.get("edge_enhance", True):
            img = self._edge_enhance(img)
        img = self._enhance_contrast(img)
        img = self._enhance_color(img)
        img = self._enhance_brightness(img)
        return img

    def _load_image(self, image_input: Union[str, Image.Image]) -> Optional[Image.Image]:
        """加载图像."""
        if isinstance(image_input, Image.Image):
            return image_input.copy()

        if isinstance(image_input, str):
            # data URI
            if image_input.startswith("data:image"):
                try:
                    b64 = image_input.split(",", 1)[1]
                    data = base64.b64decode(b64)
                    return Image.open(io.BytesIO(data))
                except Exception as e:
                    logger.warning("解析 data URI 失败: %s", e)
                    return None

            # 假设是 base64（无前缀）
            try:
                data = base64.b64decode(image_input)
                return Image.open(io.BytesIO(data))
            except Exception:
                pass

            # URL 暂不直接下载（Pipeline 中通常已处理为 URL 或 base64）
            logger.warning("ImageEnhancer 不支持直接 URL 输入，请传入 base64 或 PIL Image")
            return None

        return None

    def _sharpen(self, img: Image.Image) -> Image.Image:
        """Unsharp Mask 锐化：提升线条和文字边缘清晰度."""
        radius = float(self.params.get("sharpen_radius", 2.0))
        percent = int(self.params.get("sharpen_percent", 150))
        threshold = int(self.params.get("sharpen_threshold", 3))
        return img.filter(
            ImageFilter.UnsharpMask(
                radius=radius, percent=percent, threshold=threshold
            )
        )

    def _edge_enhance(self, img: Image.Image) -> Image.Image:
        """边缘增强：让模块边界和箭头更清晰."""
        # 使用 FIND_EDGES 提取边缘后叠加
        edges = img.filter(ImageFilter.FIND_EDGES)
        # 降低边缘图层透明度后叠加
        blended = Image.blend(img, edges, alpha=0.08)
        return blended

    def _enhance_contrast(self, img: Image.Image) -> Image.Image:
        """对比度增强：让不同模块的区分度更明显."""
        factor = float(self.params.get("contrast_factor", 1.15))
        enhancer = ImageEnhance.Contrast(img)
        return enhancer.enhance(factor)

    def _enhance_color(self, img: Image.Image) -> Image.Image:
        """色彩饱和度微调：让学术配色更鲜明但不失真."""
        factor = float(self.params.get("color_factor", 1.05))
        enhancer = ImageEnhance.Color(img)
        return enhancer.enhance(factor)

    def _enhance_brightness(self, img: Image.Image) -> Image.Image:
        """亮度微调：提升整体通透感."""
        factor = float(self.params.get("brightness_factor", 1.02))
        enhancer = ImageEnhance.Brightness(img)
        return enhancer.enhance(factor)

    def _denoise(self, img: Image.Image) -> Image.Image:
        """轻微中值滤波降噪：去除生成模型的纹理噪声，保留边缘."""
        strength = float(self.params.get("denoise_strength", 0.3))
        if strength <= 0:
            return img
        # 中值滤波 size=3 对生成噪声有效且边缘损失小
        denoised = img.filter(ImageFilter.MedianFilter(size=3))
        # 按 strength 混合原图和降噪图
        return Image.blend(img, denoised, alpha=strength)

    @staticmethod
    def quick_enhance(image_base64: str) -> str:
        """快速增强接口 — 使用默认参数一键处理.

        Args:
            image_base64: base64 编码的图像（可带或不带 data URI 前缀）

        Returns:
            增强后的 base64 图像（带 data URI 前缀）
        """
        enhancer = ImageEnhancer()
        return enhancer.process(image_base64)
