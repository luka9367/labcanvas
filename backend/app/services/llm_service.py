"""LLM Service for Zhipu AI (智谱AI) integration.

Replaces original GPT-image2 and nano banana with Zhipu AI models:
- Text: GLM-4-Flash (free)
- Image: CogView-3-Flash (free)
"""

import asyncio
import base64
import json
import logging
from typing import AsyncGenerator, Optional, List, Dict, Any

import httpx

from app.core.config import LLM_MAX_RETRIES
from app.services.settings_service import load_settings

logger = logging.getLogger(__name__)

RETRY_DELAYS = [5, 15]
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504, 524}
RETRYABLE_EXCEPTIONS = (
    httpx.ReadTimeout,
    httpx.ConnectTimeout,
    httpx.RemoteProtocolError,
    httpx.ConnectError,
    httpx.ReadError,
)

TIMEOUT_DEFAULT = httpx.Timeout(connect=10.0, read=200.0, write=10.0, pool=10.0)
TIMEOUT_IMAGE_GEN = httpx.Timeout(connect=10.0, read=240.0, write=10.0, pool=10.0)

# 智谱AI默认配置
ZHIPU_DEFAULT_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
ZHIPU_DEFAULT_TEXT_MODEL = "glm-4-flash"
ZHIPU_DEFAULT_IMAGE_MODEL = "cogview-3-flash"


class LLMService:
    """智谱AI LLM client with OpenAI-compatible API."""

    def __init__(self) -> None:
        self._model_override: Optional[str] = None
        self._base_url_override: Optional[str] = None
        self._image_model_override: Optional[str] = None
        self.log_tag: str = ""
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def model(self) -> str:
        # Defense-in-depth: always use the free text model
        return ZHIPU_DEFAULT_TEXT_MODEL

    @model.setter
    def model(self, value: Optional[str]) -> None:
        # Ignore any override that could point to a paid model
        self._model_override = None

    @property
    def base_url(self) -> str:
        if self._base_url_override is not None:
            return self._base_url_override.rstrip("/")
        settings = load_settings()
        url = settings.get("llm_base_url", "")
        if not url:
            return ZHIPU_DEFAULT_BASE_URL
        return url.rstrip("/")

    @base_url.setter
    def base_url(self, value: Optional[str]) -> None:
        self._base_url_override = value

    @property
    def image_model(self) -> str:
        # Defense-in-depth: always use the free image model
        return ZHIPU_DEFAULT_IMAGE_MODEL

    @image_model.setter
    def image_model(self, value: Optional[str]) -> None:
        # Ignore any override that could point to a paid model
        self._image_model_override = None

    def _require_api_key(self) -> str:
        """Get API key from settings."""
        settings = load_settings()
        key = settings.get("llm_api_key", "").strip()
        if not key:
            raise ValueError(
                "智谱AI API Key 未配置。请在设置中配置您的 API Key。"
            )
        return key

    def _require_image_api_key(self) -> str:
        """Get image API key (falls back to main API key)."""
        settings = load_settings()
        key = settings.get("image_api_key", "").strip()
        if not key:
            key = settings.get("llm_api_key", "").strip()
        if not key:
            raise ValueError(
                "图像生成 API Key 未配置。请在设置中配置您的 API Key。"
            )
        return key

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=TIMEOUT_DEFAULT)
        return self._client

    async def _post_with_retry(
        self,
        url: str,
        body: dict,
        headers: dict,
        *,
        timeout: Optional[httpx.Timeout] = None,
        max_retries: int = LLM_MAX_RETRIES,
    ) -> dict:
        """POST request with retry logic."""
        model = body.get("model", "?")
        last_err: Optional[Exception] = None
        
        for attempt in range(max_retries):
            is_last = attempt == max_retries - 1
            t0 = asyncio.get_event_loop().time()
            
            try:
                response = await self.client.post(
                    url, json=body, headers=headers, timeout=timeout or TIMEOUT_DEFAULT
                )
                elapsed_ms = int((asyncio.get_event_loop().time() - t0) * 1000)
                
                if response.status_code in RETRYABLE_STATUS_CODES:
                    last_err = httpx.HTTPStatusError(
                        f"HTTP {response.status_code}",
                        request=response.request,
                        response=response,
                    )
                    if is_last:
                        logger.warning(
                            "%s[non-stream] HTTP %d from %s model=%s (%dms) — all %d attempts exhausted",
                            self.log_tag, response.status_code, url, model, elapsed_ms, max_retries
                        )
                        break
                    delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                    logger.warning(
                        "%s[non-stream] HTTP %d from %s model=%s (%dms, attempt %d/%d), retrying in %ds",
                        self.log_tag, response.status_code, url, model, elapsed_ms, attempt + 1, max_retries, delay
                    )
                    await asyncio.sleep(delay)
                    continue
                
                if response.status_code >= 400:
                    err_text = response.text[:400]
                    raise httpx.HTTPStatusError(
                        f"HTTP {response.status_code} from {url} model={model}: {err_text}",
                        request=response.request,
                        response=response,
                    )
                
                return response.json()
                
            except RETRYABLE_EXCEPTIONS as e:
                elapsed_ms = int((asyncio.get_event_loop().time() - t0) * 1000)
                last_err = e
                if is_last:
                    logger.warning(
                        "%s[non-stream] %s model=%s (%dms, %s) — all %d attempts exhausted",
                        self.log_tag, url, model, elapsed_ms, type(e).__name__, max_retries
                    )
                    break
                delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                logger.warning(
                    "%s[non-stream] %s model=%s attempt %d/%d failed (%s, %dms), retrying in %ds",
                    self.log_tag, url, model, attempt + 1, max_retries, type(e).__name__, elapsed_ms, delay
                )
                await asyncio.sleep(delay)
        
        raise last_err or Exception("All retries failed")

    async def _auth_headers(self, channel: str = "text") -> Dict[str, str]:
        """Build authorization headers."""
        if channel == "image":
            key = self._require_image_api_key()
        else:
            key = self._require_api_key()
        return {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        response_format: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Send chat completion request.
        
        Compatible with OpenAI API format for Zhipu AI.
        """
        url = f"{self.base_url}/chat/completions"
        headers = await self._auth_headers("text")
        
        body: Dict[str, Any] = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream,
        }
        
        if max_tokens:
            body["max_tokens"] = max_tokens
        
        if response_format:
            body["response_format"] = response_format
        
        if stream:
            return await self._post_stream(url, body, headers)
        
        return await self._post_with_retry(url, body, headers)

    async def _post_stream(
        self,
        url: str,
        body: dict,
        headers: dict,
    ) -> AsyncGenerator[str, None]:
        """Stream POST request."""
        async with self.client.stream(
            "POST", url, json=body, headers=headers, timeout=TIMEOUT_DEFAULT
        ) as response:
            if response.status_code >= 400:
                err_text = await response.aread()
                raise httpx.HTTPStatusError(
                    f"HTTP {response.status_code}: {err_text.decode()[:400]}",
                    request=response.request,
                    response=response,
                )
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:].strip()
                    if data == "[DONE]":
                        break
                    yield data

    async def generate_image(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        size: str = "1024x1024",
        quality: str = "standard",
        n: int = 1,
        negative_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate image using CogView model.

        Uses Zhipu AI's CogView-3-Flash (free tier available).
        Supports negative_prompt for quality control.
        """
        url = f"{self.base_url}/images/generations"
        headers = await self._auth_headers("image")

        body: Dict[str, Any] = {
            "model": model or self.image_model,
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "n": n,
        }

        # 智谱 CogView 支持 negative_prompt（非标准 OpenAI 字段）
        if negative_prompt:
            body["negative_prompt"] = negative_prompt

        return await self._post_with_retry(
            url, body, headers, timeout=TIMEOUT_IMAGE_GEN
        )

    async def generate_image_multi(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        size: str = "1024x1024",
        quality: str = "standard",
        n: int = 2,
        negative_prompt: Optional[str] = None,
    ) -> List[str]:
        """生成多张候选图，返回所有图片 URL/base64 列表.

        用于多候选择优策略，在免费模型配额内一次生成多张，
        通过 quality_engine 评估选择最佳结果。
        """
        result = await self.generate_image(
            prompt=prompt,
            model=model,
            size=size,
            quality=quality,
            n=n,
            negative_prompt=negative_prompt,
        )

        urls: List[str] = []
        data = result.get("data", [])
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    url = item.get("url") or item.get("b64_json")
                    if url:
                        urls.append(url)
        elif isinstance(data, dict):
            url = data.get("url") or data.get("b64_json")
            if url:
                urls.append(url)

        if result.get("url"):
            urls.append(result["url"])
        if result.get("b64_json"):
            urls.append(result["b64_json"])

        # 去重
        seen = set()
        unique: List[str] = []
        for u in urls:
            if u not in seen:
                seen.add(u)
                unique.append(u)
        return unique

    async def vision_analysis(
        self,
        image_base64: str,
        prompt: str,
        *,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze image with vision model.
        
        Uses GLM-4V for image understanding.
        """
        url = f"{self.base_url}/chat/completions"
        headers = await self._auth_headers("text")
        
        vision_model = model or "glm-4v-flash"
        
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_base64}"}
                    }
                ]
            }
        ]
        
        body = {
            "model": vision_model,
            "messages": messages,
            "temperature": 0.7,
        }
        
        return await self._post_with_retry(url, body, headers)

    async def extract_xml_from_response(self, response: Dict[str, Any]) -> str:
        """Extract content from chat completion response."""
        try:
            choices = response.get("choices", [])
            if choices:
                content = choices[0].get("message", {}).get("content", "")
                return content
        except (KeyError, IndexError):
            pass
        return ""

    async def generate_drawio_xml(
        self,
        prompt: str,
        reference_image: Optional[str] = None,
        style_hint: Optional[str] = None,
    ) -> str:
        """Generate draw.io XML from prompt.
        
        Used for draft mode - generates editable flowchart XML.
        """
        system_prompt = """你是一个专业的流程图生成专家。根据用户的描述生成 draw.io (diagrams.net) 格式的 XML 流程图。

要求：
1. 生成的 XML 必须是有效的 draw.io 格式
2. 使用标准的 mxGraph 格式
3. 包含清晰的节点和连接线
4. 布局整齐美观
5. 使用合适的颜色和样式
6. 质量基准（参考优秀学术论文插图样张）：
   - 视觉质量：高分辨率、线条清晰锐利
   - 信息密度：高密度但不拥挤，包含3-6个主要模块
   - 模块数量：丰富的节点和流程框图，模块间有清晰的连接关系和数据流
   - 色彩还原度：专业学术配色（蓝色、黄色、灰色、绿色、粉色等）
   - 整体风格：学术论文图表风格，清晰的分块和边框
   - 布局构图：清晰的分栏或分块布局，流程逻辑明确，留白合理
   - 文字清晰度：所有标签必须清晰可读，字号层次分明

直接返回 XML 内容，不要包含任何解释文字。"""

        if style_hint:
            system_prompt += f"\n\n风格参考：{style_hint}"

        user_prompt = prompt
        if reference_image:
            # Use vision model to analyze image, then incorporate description into prompt
            try:
                vision_result = await self.vision_analysis(
                    image_base64=reference_image,
                    prompt="请详细描述这张图片的内容、风格、颜色、布局和构图特点。",
                )
                ref_desc = await self.extract_xml_from_response(vision_result)
                if ref_desc:
                    user_prompt = f"参考图片风格描述：{ref_desc}\n\n基于以上参考风格，{prompt}"
            except Exception as e:
                print(f"Vision analysis error in generate_drawio_xml: {e}")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.chat_completion(
            messages,
            temperature=0.3,
            response_format={"type": "text"}
        )
        
        content = await self.extract_xml_from_response(response)
        return content

    async def generate_image_prompt(
        self,
        description: str,
        style_reference: Optional[str] = None,
    ) -> str:
        """Generate optimized image generation prompt.
        
        Used for generation mode - creates high-quality image prompts.
        """
        system_prompt = """你是一个专业的学术插图提示词优化专家。

将用户的描述转换为高质量的图像生成提示词，要求：
1. 使用英文撰写（图像生成模型对英文理解更好）
2. 包含详细的视觉描述
3. 指定风格（学术论文风格、技术插图风格等）
4. 包含构图、色彩、光影等细节
5. 适合 CogView 等图像生成模型

直接返回优化后的提示词，不要包含解释。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": description}
        ]
        
        response = await self.chat_completion(
            messages,
            temperature=0.7,
        )
        
        return await self.extract_xml_from_response(response)
