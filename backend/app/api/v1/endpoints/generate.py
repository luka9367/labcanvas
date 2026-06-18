"""Generation endpoints."""

import json
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from app.dependencies import LLMServiceDep
from app.schemas.generate import GenerateRequest, GenerateResponse
from app.services.pipeline.base import PipelineContext, PipelineMode
from app.services.pipeline.factory import create_pipeline

router = APIRouter()


@router.post("", response_model=GenerateResponse)
async def generate(
    request: GenerateRequest,
    llm_service: LLMServiceDep,
):
    """Generate diagram/image based on prompt and mode."""
    try:
        # Map mode string to enum
        mode_map = {
            "auto": PipelineMode.AUTO,
            "draft": PipelineMode.DRAFT,
            "generate": PipelineMode.GENERATE,
            "assembly": PipelineMode.ASSEMBLY,
        }
        mode = mode_map.get(request.mode, PipelineMode.AUTO)
        
        # Create context
        context = PipelineContext(
            prompt=request.prompt,
            mode=mode,
            reference_image=request.reference_image,
            style_reference=request.style_reference,
            language=request.language,
        )
        
        # Create and execute pipeline
        pipeline = create_pipeline(mode, llm_service)
        result = await pipeline.execute(context)
        
        return GenerateResponse(
            success=result.success,
            message=result.message,
            data=result.data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def generate_stream(
    request: GenerateRequest,
    llm_service: LLMServiceDep,
):
    """Generate with streaming progress updates."""
    async def event_generator():
        try:
            mode_map = {
                "auto": PipelineMode.AUTO,
                "draft": PipelineMode.DRAFT,
                "generate": PipelineMode.GENERATE,
                "assembly": PipelineMode.ASSEMBLY,
            }
            mode = mode_map.get(request.mode, PipelineMode.AUTO)
            
            context = PipelineContext(
                prompt=request.prompt,
                mode=mode,
                reference_image=request.reference_image,
                style_reference=request.style_reference,
                language=request.language,
            )
            
            pipeline = create_pipeline(mode, llm_service)
            
            async for chunk in pipeline.execute_stream(context):
                yield {"data": chunk}
                
        except Exception as e:
            yield {"data": json.dumps({"step": "error", "message": str(e)})}
    
    return EventSourceResponse(event_generator())


@router.post("/chat")
async def chat_completion(
    messages: list,
    model: Optional[str] = None,
    temperature: float = 0.7,
    stream: bool = False,
    llm_service: LLMServiceDep = None,
):
    """Direct chat completion endpoint."""
    try:
        if model:
            llm_service.model = model
        
        response = await llm_service.chat_completion(
            messages=messages,
            temperature=temperature,
            stream=stream
        )
        
        if stream:
            async def stream_generator():
                async for chunk in llm_service._post_stream(
                    f"{llm_service.base_url}/chat/completions",
                    {"messages": messages, "model": model or llm_service.model, "temperature": temperature, "stream": True},
                    await llm_service._auth_headers()
                ):
                    yield {"data": chunk}
            
            return EventSourceResponse(stream_generator())
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
