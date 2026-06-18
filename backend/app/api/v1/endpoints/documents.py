"""Document processing endpoints (PDF, etc.)."""

import io
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form

router = APIRouter()


@router.post("/parse")
async def parse_document(
    file: UploadFile = File(...),
    mineru_token: Optional[str] = Form(None),
):
    """Parse uploaded document (PDF, etc.)."""
    try:
        # Read file
        contents = await file.read()
        
        # For now, return a placeholder response
        # In production, this would integrate with MinerU or similar
        
        return {
            "success": True,
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(contents),
            "content": "Document parsing is not fully implemented. Please paste text directly.",
            "sections": []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract-text")
async def extract_text(file: UploadFile = File(...)):
    """Extract text from document."""
    try:
        contents = await file.read()
        
        # Simple text extraction based on file type
        if file.content_type == "text/plain":
            text = contents.decode("utf-8")
        elif file.content_type == "text/markdown":
            text = contents.decode("utf-8")
        else:
            text = f"Text extraction for {file.content_type} is not implemented."
        
        return {
            "success": True,
            "text": text,
            "filename": file.filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
