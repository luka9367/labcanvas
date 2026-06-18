"""Reference images endpoints."""

import os
import uuid
import base64
from typing import List, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from app.services import references_service

router = APIRouter()


class ReferenceImage(BaseModel):
    id: str
    name: str
    category: str
    thumbnail_url: str
    full_url: str
    created_at: str
    is_default: bool = False


class ReferenceImagesResponse(BaseModel):
    success: bool
    images: List[ReferenceImage]
    categories: List[str]


class ReferenceImageResponse(BaseModel):
    success: bool
    image: Optional[ReferenceImage] = None
    message: Optional[str] = None


@router.get("", response_model=ReferenceImagesResponse)
async def get_reference_images(category: Optional[str] = None):
    """Get all reference images."""
    try:
        # Initialize default references
        references_service.init_default_references()
        
        # Get references
        images = references_service.get_references(category)
        categories = references_service.get_categories()
        
        return ReferenceImagesResponse(
            success=True,
            images=[ReferenceImage(**img) for img in images],
            categories=categories
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def get_categories():
    """Get all reference categories."""
    try:
        references_service.init_default_references()
        categories = references_service.get_categories()
        return {"success": True, "categories": categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload", response_model=ReferenceImageResponse)
async def upload_reference_image(
    file: UploadFile = File(...),
    name: str = Form(...),
    category: str = Form("custom"),
):
    """Upload a new reference image."""
    try:
        from app.core.config import REFERENCES_DIR
        from datetime import datetime
        from PIL import Image
        import io
        
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Generate unique ID
        image_id = str(uuid.uuid4())
        
        # Read file content
        content = await file.read()
        
        # Save image
        image_path = REFERENCES_DIR / f"{image_id}.png"
        with open(image_path, 'wb') as f:
            f.write(content)
        
        # Create thumbnail
        try:
            img = Image.open(io.BytesIO(content))
            img.thumbnail((200, 200))
            thumbnail_path = REFERENCES_DIR / f"{image_id}_thumb.png"
            img.save(thumbnail_path, 'PNG')
        except Exception as e:
            print(f"Thumbnail creation failed: {e}")
            # Use full image as thumbnail
            thumbnail_path = image_path
        
        # Save metadata
        metadata = {
            'id': image_id,
            'name': name,
            'category': category,
            'original_filename': file.filename,
            'created_at': datetime.now().isoformat(),
            'is_default': False
        }
        
        metadata_path = REFERENCES_DIR / f"{image_id}.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            import json
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return ReferenceImageResponse(
            success=True,
            image=ReferenceImage(
                id=image_id,
                name=name,
                category=category,
                thumbnail_url=f"/api/v1/references/{image_id}/thumbnail",
                full_url=f"/api/v1/references/{image_id}/image",
                created_at=metadata['created_at'],
                is_default=False
            ),
            message="Image uploaded successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{image_id}/image")
async def get_image(image_id: str):
    """Get full image."""
    try:
        references_service.init_default_references()
        image_path = references_service.get_reference_image_path(image_id, thumbnail=False)
        
        if not image_path:
            raise HTTPException(status_code=404, detail="Image not found")
        
        from fastapi.responses import FileResponse
        return FileResponse(image_path, media_type="image/png")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{image_id}/thumbnail")
async def get_thumbnail(image_id: str):
    """Get thumbnail image."""
    try:
        references_service.init_default_references()
        image_path = references_service.get_reference_image_path(image_id, thumbnail=True)
        
        if not image_path:
            raise HTTPException(status_code=404, detail="Image not found")
        
        from fastapi.responses import FileResponse
        return FileResponse(image_path, media_type="image/png")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{image_id}")
async def delete_reference_image(image_id: str):
    """Delete a reference image."""
    try:
        success = references_service.delete_reference(image_id)
        
        if not success:
            raise HTTPException(status_code=403, detail="Cannot delete default reference images")
        
        return {"success": True, "message": "Image deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
