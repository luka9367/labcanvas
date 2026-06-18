"""AI Assistant (NanaSoul) endpoints."""

import json
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from app.dependencies import LLMServiceDep
from app.services.settings_service import load_settings

router = APIRouter()


DEFAULT_NANASOUL_PROMPT = """你是 NanaSoul，LabCanvas 的智能助手。你擅长：

1. 帮助用户理解和使用 LabCanvas 的各种功能
2. 提供绘图建议和技术支持
3. 协助优化提示词和生成效果
4. 解答关于学术绘图的问题

你友好、专业，总是用中文回答用户的问题。"""


@router.post("/chat")
async def assistant_chat(
    messages: List[Dict[str, str]],
    llm_service: LLMServiceDep,
    stream: bool = False,
):
    """Chat with AI assistant."""
    try:
        # Get custom NanaSoul prompt from settings
        settings = load_settings()
        custom_prompt = settings.get("nanasoul_prompt", "")
        system_prompt = custom_prompt if custom_prompt else DEFAULT_NANASOUL_PROMPT
        
        # Prepare messages
        chat_messages = [{"role": "system", "content": system_prompt}]
        chat_messages.extend(messages)
        
        if stream:
            async def event_generator():
                try:
                    # Get streaming response
                    url = f"{llm_service.base_url}/chat/completions"
                    headers = await llm_service._auth_headers()
                    body = {
                        "model": llm_service.model,
                        "messages": chat_messages,
                        "temperature": 0.7,
                        "stream": True
                    }
                    
                    async for chunk in llm_service._post_stream(url, body, headers):
                        yield {"data": chunk}
                        
                except Exception as e:
                    yield {"data": json.dumps({"error": str(e)})}
            
            return EventSourceResponse(event_generator())
        else:
            # Non-streaming response
            response = await llm_service.chat_completion(
                messages=chat_messages,
                temperature=0.7,
                stream=False
            )
            
            content = await llm_service.extract_xml_from_response(response)
            return {
                "success": True,
                "message": content
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/canvas-command")
async def execute_canvas_command(
    command: str,
    canvas_state: Optional[Dict[str, Any]] = None,
    llm_service: LLMServiceDep = None,
):
    """Execute natural language command on canvas."""
    try:
        system_prompt = """你是一个画布操作助手。将用户的自然语言指令转换为结构化的画布操作命令。

可用操作：
- add_node: 添加节点
- add_edge: 添加连接线
- delete: 删除元素
- update_style: 更新样式
- layout: 重新布局
- group: 分组
- ungroup: 取消分组

输出JSON格式：
{
    "action": "操作类型",
    "params": {操作参数},
    "description": "操作描述"
}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"指令：{command}\n\n当前画布状态：{json.dumps(canvas_state or {}, ensure_ascii=False)}"}
        ]
        
        response = await llm_service.chat_completion(
            messages=messages,
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        content = await llm_service.extract_xml_from_response(response)
        command_data = json.loads(content)
        
        return {
            "success": True,
            "command": command_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
