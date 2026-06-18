"""Bioicons endpoints for scientific SVG icons."""

from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.core.config import STATIC_DIR

router = APIRouter()

BIOICONS_DIR = STATIC_DIR / "bioicons" / "svgs"


@router.get("")
async def list_icons(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search query"),
):
    """List available SVG icons."""
    try:
        icons = []
        
        if BIOICONS_DIR.exists():
            for file_path in BIOICONS_DIR.rglob("*.svg"):
                # Get relative path as category
                rel_path = file_path.relative_to(BIOICONS_DIR)
                icon_category = rel_path.parent.name if rel_path.parent.name else "general"
                
                # Filter by category
                if category and icon_category != category:
                    continue
                
                # Filter by search
                if search and search.lower() not in file_path.stem.lower():
                    continue
                
                icons.append({
                    "id": file_path.stem,
                    "name": file_path.stem.replace("_", " ").title(),
                    "category": icon_category,
                    "url": f"/static/bioicons/svgs/{rel_path.as_posix()}",
                })
        
        return {
            "success": True,
            "icons": icons,
            "total": len(icons)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def get_categories():
    """Get icon categories."""
    try:
        categories = set()
        
        if BIOICONS_DIR.exists():
            for file_path in BIOICONS_DIR.rglob("*.svg"):
                rel_path = file_path.relative_to(BIOICONS_DIR)
                category = rel_path.parent.name if rel_path.parent.name else "general"
                categories.add(category)
        
        return {
            "success": True,
            "categories": sorted(list(categories))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{icon_id}")
async def get_icon(icon_id: str):
    """Get specific icon details."""
    try:
        # Search for icon
        for file_path in BIOICONS_DIR.rglob("*.svg"):
            if file_path.stem == icon_id:
                rel_path = file_path.relative_to(BIOICONS_DIR)
                category = rel_path.parent.name if rel_path.parent.name else "general"
                
                # Read SVG content
                with open(file_path, "r", encoding="utf-8") as f:
                    svg_content = f.read()
                
                return {
                    "success": True,
                    "icon": {
                        "id": icon_id,
                        "name": file_path.stem.replace("_", " ").title(),
                        "category": category,
                        "url": f"/static/bioicons/svgs/{rel_path.as_posix()}",
                        "svg": svg_content
                    }
                }
        
        raise HTTPException(status_code=404, detail="Icon not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
