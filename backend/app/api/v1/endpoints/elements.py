"""Element generation endpoints."""

import base64
import io
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException, UploadFile, File
from PIL import Image

from app.dependencies import LLMServiceDep
from app.schemas.generate import ElementGenerateRequest, ElementGenerateResponse

router = APIRouter()

# Predefined element library
PREDEFINED_ELEMENTS = [
    {
        "id": "server",
        "name": "Server",
        "category": "infrastructure",
        "type": "icon",
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><line x1="6" y1="6" x2="6" y2="6"/><line x1="6" y1="18" x2="6" y2="18"/></svg>'
    },
    {
        "id": "database",
        "name": "Database",
        "category": "infrastructure",
        "type": "icon",
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>'
    },
    {
        "id": "cloud",
        "name": "Cloud",
        "category": "infrastructure",
        "type": "icon",
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"/></svg>'
    },
    {
        "id": "user",
        "name": "User",
        "category": "user",
        "type": "icon",
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'
    },
    {
        "id": "arrow-right",
        "name": "Arrow Right",
        "category": "arrow",
        "type": "arrow",
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>'
    },
    {
        "id": "arrow-down",
        "name": "Arrow Down",
        "category": "arrow",
        "type": "arrow",
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><polyline points="19 12 12 19 5 12"/></svg>'
    },
    {
        "id": "process",
        "name": "Process",
        "category": "flowchart",
        "type": "shape",
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/></svg>'
    },
    {
        "id": "decision",
        "name": "Decision",
        "category": "flowchart",
        "type": "shape",
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 22 12 12 22 2 12"/></svg>'
    },
]


@router.get("", response_model=Dict[str, Any])
async def get_elements(
    category: Optional[str] = None,
    element_type: Optional[str] = None,
):
    """Get predefined elements library."""
    elements = PREDEFINED_ELEMENTS
    
    # Filter by category if provided
    if category:
        elements = [e for e in elements if e["category"] == category]
    
    # Filter by type if provided
    if element_type:
        elements = [e for e in elements if e["type"] == element_type]
    
    return {
        "success": True,
        "elements": elements,
        "total": len(elements),
        "categories": list(set(e["category"] for e in PREDEFINED_ELEMENTS)),
        "types": list(set(e["type"] for e in PREDEFINED_ELEMENTS)),
    }


@router.post("/generate", response_model=ElementGenerateResponse)
async def generate_element(
    request: ElementGenerateRequest,
    llm_service: LLMServiceDep,
):
    """Generate a single element (icon, image, etc.)."""
    try:
        # Optimize prompt for element generation
        element_prompt = f"""Simple, clean {request.element_type} illustration: {request.prompt}

Requirements:
- White or transparent background
- Minimal, flat design style
- Suitable for technical diagrams
- Clear and recognizable
- No text or labels
"""
        
        # Generate image
        result = await llm_service.generate_image(
            prompt=element_prompt,
            size=request.size,
            quality="standard"
        )
        
        # Extract image URL
        data = result.get("data", [])
        image_url = ""
        if data:
            image_url = data[0].get("url", "")
        
        return ElementGenerateResponse(
            success=True,
            message="Element generated successfully",
            image_url=image_url
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/remove-background")
async def remove_background(file: UploadFile = File(...)):
    """Remove background from uploaded image."""
    try:
        # Read image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Convert to RGBA if needed
        if image.mode != "RGBA":
            image = image.convert("RGBA")
        
        # Simple background removal (make white/close-to-white pixels transparent)
        datas = image.getdata()
        new_data = []
        for item in datas:
            # If pixel is close to white, make it transparent
            if item[0] > 240 and item[1] > 240 and item[2] > 240:
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(item)
        
        image.putdata(new_data)
        
        # Save to bytes
        output = io.BytesIO()
        image.save(output, format="PNG")
        output.seek(0)
        
        # Encode to base64
        base64_image = base64.b64encode(output.getvalue()).decode()
        
        return {
            "success": True,
            "image_base64": base64_image,
            "format": "png"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/svg-trace")
async def trace_svg(file: UploadFile = File(...)):
    """Convert image to SVG (simplified version)."""
    try:
        # For now, return a placeholder SVG
        # In production, this would use potrace or similar
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
            <rect width="100" height="100" fill="none" stroke="black"/>
            <text x="50" y="50" text-anchor="middle" dominant-baseline="middle">
                SVG Placeholder
            </text>
        </svg>"""
        
        return {
            "success": True,
            "svg": svg_content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
