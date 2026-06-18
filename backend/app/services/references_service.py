"""References service for managing reference images."""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from app.core.config import REFERENCES_DIR


# Default reference images metadata
DEFAULT_REFERENCES = [
    {
        "id": "ref_flowchart_basic",
        "name": "基础流程图",
        "category": "flowchart",
        "description": "标准流程图样式参考",
    },
    {
        "id": "ref_flowchart_process",
        "name": "业务流程图",
        "category": "flowchart",
        "description": "业务流程图样式参考",
    },
    {
        "id": "ref_architecture_microservices",
        "name": "微服务架构",
        "category": "architecture",
        "description": "微服务系统架构图",
    },
    {
        "id": "ref_architecture_cloud",
        "name": "云架构",
        "category": "architecture",
        "description": "云计算架构图",
    },
    {
        "id": "ref_network_topology",
        "name": "网络拓扑",
        "category": "network",
        "description": "网络拓扑结构图",
    },
    {
        "id": "ref_database_erd",
        "name": "数据库ER图",
        "category": "database",
        "description": "实体关系图",
    },
    {
        "id": "ref_ml_pipeline",
        "name": "机器学习流程",
        "category": "ml",
        "description": "机器学习训练流程图",
    },
    {
        "id": "ref_dl_architecture",
        "name": "深度学习架构",
        "category": "ml",
        "description": "深度学习网络架构",
    },
    {
        "id": "ref_timeline_project",
        "name": "项目时间线",
        "category": "timeline",
        "description": "项目进度时间线",
    },
    {
        "id": "ref_org_structure",
        "name": "组织架构",
        "category": "organization",
        "description": "公司组织架构图",
    },
    {
        "id": "ref_mindmap_concept",
        "name": "概念思维导图",
        "category": "mindmap",
        "description": "概念发散思维导图",
    },
    {
        "id": "ref_sequence_api",
        "name": "API时序图",
        "category": "sequence",
        "description": "API调用时序图",
    },
]


def create_placeholder_image(width: int, height: int, title: str, category: str, description: str) -> 'Image.Image':
    """Create a placeholder image with text."""
    from PIL import Image, ImageDraw, ImageFont
    
    # Create image with gradient background
    img = Image.new('RGB', (width, height), color='#f8fafc')
    draw = ImageDraw.Draw(img)
    
    # Draw border
    draw.rectangle([(0, 0), (width-1, height-1)], outline='#e2e8f0', width=2)
    
    # Try to load font, fallback to default
    try:
        # Try common system fonts
        font_paths = [
            "C:/Windows/Fonts/simhei.ttf",  # Windows Chinese font
            "C:/Windows/Fonts/msyh.ttc",     # Windows Microsoft YaHei
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",  # Linux
            "/System/Library/Fonts/PingFang.ttc",  # macOS
        ]
        font = None
        small_font = None
        for font_path in font_paths:
            try:
                font = ImageFont.truetype(font_path, 32 if width > 400 else 20)
                small_font = ImageFont.truetype(font_path, 20 if width > 400 else 14)
                break
            except:
                continue
        if font is None:
            raise Exception("No suitable font found")
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Draw title
    bbox = draw.textbbox((0, 0), title, font=font)
    text_width = bbox[2] - bbox[0]
    draw.text(((width - text_width) / 2, height * 0.25), title, fill='#1e293b', font=font)
    
    # Draw category
    cat_text = f"分类: {category}"
    bbox = draw.textbbox((0, 0), cat_text, font=small_font)
    text_width = bbox[2] - bbox[0]
    draw.text(((width - text_width) / 2, height * 0.45), cat_text, fill='#64748b', font=small_font)
    
    # Draw description
    bbox = draw.textbbox((0, 0), description, font=small_font)
    text_width = bbox[2] - bbox[0]
    draw.text(((width - text_width) / 2, height * 0.55), description, fill='#64748b', font=small_font)
    
    # Draw placeholder icon/text
    icon_text = "[参考图]"
    bbox = draw.textbbox((0, 0), icon_text, font=small_font)
    text_width = bbox[2] - bbox[0]
    draw.text(((width - text_width) / 2, height * 0.7), icon_text, fill='#94a3b8', font=small_font)
    
    return img


def init_default_references():
    """Initialize default reference images if they don't exist."""
    # Create references directory if not exists
    REFERENCES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check if already initialized
    marker_file = REFERENCES_DIR / ".initialized"
    if marker_file.exists():
        # Still check if all default references exist
        all_exist = all(
            (REFERENCES_DIR / f"{ref['id']}.json").exists() and
            (REFERENCES_DIR / f"{ref['id']}.png").exists()
            for ref in DEFAULT_REFERENCES
        )
        if all_exist:
            return
    
    print("Initializing default reference images...")
    
    # Create default reference metadata files and images
    for ref in DEFAULT_REFERENCES:
        metadata_path = REFERENCES_DIR / f"{ref['id']}.json"
        image_path = REFERENCES_DIR / f"{ref['id']}.png"
        thumb_path = REFERENCES_DIR / f"{ref['id']}_thumb.png"
        
        # Create metadata
        if not metadata_path.exists():
            metadata = {
                "id": ref["id"],
                "name": ref["name"],
                "category": ref["category"],
                "description": ref["description"],
                "created_at": datetime.now().isoformat(),
                "is_default": True
            }
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        # Create placeholder image
        if not image_path.exists():
            try:
                from PIL import Image
                
                # Create full size image
                img = create_placeholder_image(800, 600, ref["name"], ref["category"], ref["description"])
                img.save(image_path, 'PNG')
                
                # Create thumbnail
                thumb = img.copy()
                thumb.thumbnail((200, 200))
                thumb.save(thumb_path, 'PNG')
                
                print(f"Created placeholder image for {ref['name']}")
            except Exception as e:
                print(f"Warning: Could not create placeholder image for {ref['name']}: {e}")
                # Create a simple colored placeholder if PIL fails
                try:
                    from PIL import Image, ImageDraw
                    img = Image.new('RGB', (800, 600), color='#e2e8f0')
                    img.save(image_path, 'PNG')
                    thumb = img.copy()
                    thumb.thumbnail((200, 200))
                    thumb.save(thumb_path, 'PNG')
                except:
                    pass
    
    # Mark as initialized
    marker_file.touch()
    print(f"Default reference images initialized in {REFERENCES_DIR}")


def get_references(category: Optional[str] = None) -> List[dict]:
    """Get all reference images, optionally filtered by category."""
    init_default_references()
    
    references = []
    
    # Scan references directory
    for metadata_file in REFERENCES_DIR.glob("*.json"):
        if metadata_file.name.endswith("_thumb.json"):
            continue
            
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            ref_id = metadata.get("id")
            if not ref_id:
                continue
            
            # Filter by category
            if category and metadata.get("category") != category:
                continue
            
            # Check if image files exist
            image_path = REFERENCES_DIR / f"{ref_id}.png"
            thumb_path = REFERENCES_DIR / f"{ref_id}_thumb.png"
            
            if image_path.exists():
                references.append({
                    "id": ref_id,
                    "name": metadata.get("name", "未命名"),
                    "category": metadata.get("category", "其他"),
                    "thumbnail_url": f"/api/v1/references/{ref_id}/thumbnail",
                    "full_url": f"/api/v1/references/{ref_id}/image",
                    "created_at": metadata.get("created_at", datetime.now().isoformat()),
                    "is_default": metadata.get("is_default", False)
                })
        except Exception as e:
            print(f"Error loading reference {metadata_file}: {e}")
            continue
    
    # Sort by created_at, default references first
    references.sort(key=lambda x: (not x.get("is_default", False), x.get("created_at", "")))
    
    return references


def get_categories() -> List[str]:
    """Get all unique categories."""
    init_default_references()
    
    categories = set()
    for metadata_file in REFERENCES_DIR.glob("*.json"):
        if metadata_file.name.endswith("_thumb.json"):
            continue
            
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            categories.add(metadata.get("category", "其他"))
        except:
            continue
    
    return sorted(list(categories))


def delete_reference(ref_id: str) -> bool:
    """Delete a reference image."""
    try:
        # Check if it's a default reference
        metadata_path = REFERENCES_DIR / f"{ref_id}.json"
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Don't allow deletion of default references
            if metadata.get("is_default", False):
                return False
        
        # Delete files
        image_path = REFERENCES_DIR / f"{ref_id}.png"
        thumb_path = REFERENCES_DIR / f"{ref_id}_thumb.png"
        
        if image_path.exists():
            image_path.unlink()
        if thumb_path.exists():
            thumb_path.unlink()
        if metadata_path.exists():
            metadata_path.unlink()
        
        return True
    except Exception as e:
        print(f"Error deleting reference {ref_id}: {e}")
        return False


def get_reference_image_path(ref_id: str, thumbnail: bool = False) -> Optional[Path]:
    """Get the path to a reference image."""
    init_default_references()
    
    if thumbnail:
        path = REFERENCES_DIR / f"{ref_id}_thumb.png"
        if path.exists():
            return path
        # Fallback to full image
        path = REFERENCES_DIR / f"{ref_id}.png"
        if path.exists():
            return path
    else:
        path = REFERENCES_DIR / f"{ref_id}.png"
        if path.exists():
            return path
    
    return None
