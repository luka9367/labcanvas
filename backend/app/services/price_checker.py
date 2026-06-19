"""Check whether Zhipu models are still officially marked as free.

Fetches the public markdown docs from docs.bigmodel.cn and inspects the
free/free-version sections. If a model is no longer listed as free, generation
is blocked and a warning is surfaced to the user.
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from typing import Dict, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 3600  # 1 hour

# Mapping from the model IDs we use to their official doc pages.
MODEL_DOC_CONFIG: Dict[str, Dict[str, Optional[str]]] = {
    "glm-4-flash": {
        "url": "https://docs.bigmodel.cn/cn/guide/models/text/glm-4.md",
        "section": "GLM-4-Flash-250414",
    },
    "glm-4v-flash": {
        "url": "https://docs.bigmodel.cn/cn/guide/models/vlm/glm-4v.md",
        "section": "GLM-4V-Flash",
    },
    "cogview-3-flash": {
        "url": "https://docs.bigmodel.cn/cn/guide/models/free/cogview-3-flash.md",
        "section": None,
    },
}

# Models we are willing to call.
TARGET_MODELS = set(MODEL_DOC_CONFIG.keys())

_status_cache: Dict[str, Tuple[bool, str, float]] = {}


async def _fetch(url: str, client: httpx.AsyncClient) -> Optional[str]:
    try:
        response = await client.get(url, timeout=15.0, follow_redirects=True)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.warning("Failed to fetch %s: %s", url, e)
        return None


def _extract_section(text: str, section_marker: str) -> Optional[str]:
    """Extract the markdown section starting with section_marker up to the next
    peer section (same-level heading or next peer Tab)."""
    lower_text = text.lower()
    lower_marker = section_marker.lower()

    # Try heading first.
    patterns = [
        rf"##\s+{re.escape(section_marker)}",
        rf"###\s+{re.escape(section_marker)}",
        rf'<Tab title="{re.escape(section_marker)}">',
        rf'<Tab title="{re.escape(section_marker)}[^"]*">',
    ]
    start = -1
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            start = m.end()
            break

    if start == -1:
        return None

    # Find next peer boundary.
    next_boundary = re.search(
        r"\n##\s+|\n###\s+|<Tab title=\"",
        text[start:],
        re.IGNORECASE,
    )
    if next_boundary:
        return text[start : start + next_boundary.start()]
    return text[start:]


def _is_section_free(section: str) -> Tuple[bool, str]:
    """Return (is_free, reason) for a markdown section."""
    section_lower = section.lower()

    # If the section says "免费版" / "免费模型" / "免费" clearly.
    has_free_label = any(
        kw in section_lower
        for kw in ["免费版", "免费模型", "免费图像生成模型", "是免费"]
    )

    # Price patterns: 元 / 千tokens, 元 / 张, etc.
    price_pattern = re.compile(
        r"(\d+\.?\d*)\s*[元￥/$]\s*/\s*(千tokens|千 Tokens|张|百万tokens|百万 Tokens|次)"
    )
    has_price = price_pattern.search(section) is not None

    if has_price:
        return False, "官方文档中该模型对应区域出现明确价格，已判定为付费模型。"

    if has_free_label:
        return True, "官方文档明确标注为免费模型。"

    return False, "官方文档未明确标注该模型为免费，已阻止生成以避免扣费。"


async def check_model_free(model_id: str) -> Tuple[bool, str]:
    """Return (is_free, message).

    is_free=True  -> the model is still listed as free on Zhipu's docs.
    is_free=False -> the model is detected as paid or no longer listed as free.
    """
    model_id = model_id.lower().strip()
    now = time.time()
    cached = _status_cache.get(model_id)
    if cached and (now - cached[2]) < CACHE_TTL_SECONDS:
        return cached[0], cached[1]

    config = MODEL_DOC_CONFIG.get(model_id)
    if not config:
        msg = f"未知模型 {model_id}，无法确认是否免费，已阻止生成。"
        _status_cache[model_id] = (False, msg, now)
        return False, msg

    async with httpx.AsyncClient() as client:
        text = await _fetch(config["url"], client)

    if text is None:
        msg = "无法访问智谱官方文档检查免费状态，默认允许生成（请自行关注官方定价）。"
        _status_cache[model_id] = (True, msg, now)
        return True, msg

    section_marker = config.get("section")
    if section_marker:
        section = _extract_section(text, section_marker)
        if section is None:
            msg = (
                f"官方文档中未找到 {section_marker} 相关说明，可能该模型已调整或下线，"
                "已阻止生成以避免扣费。"
            )
            _status_cache[model_id] = (False, msg, now)
            return False, msg
        is_free, reason = _is_section_free(section)
    else:
        is_free, reason = _is_section_free(text)

    _status_cache[model_id] = (is_free, reason, now)
    return is_free, reason


def clear_cache() -> None:
    _status_cache.clear()
