"""Project management endpoints."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from app.core.config import DATA_DIR
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ProjectResponse,
    ProjectListResponse,
    ProjectDetailResponse,
)

router = APIRouter()

PROJECTS_DIR = DATA_DIR / "projects"


def ensure_projects_dir():
    """Ensure projects directory exists."""
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)


def get_project_path(project_id: str) -> Path:
    """Get path to project file."""
    return PROJECTS_DIR / f"{project_id}.json"


@router.get("", response_model=ProjectListResponse)
async def list_projects():
    """List all projects."""
    ensure_projects_dir()
    
    projects = []
    for file_path in PROJECTS_DIR.glob("*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                projects.append(ProjectResponse(**data))
        except (json.JSONDecodeError, IOError):
            continue
    
    # Sort by updated_at descending
    projects.sort(key=lambda p: p.updated_at, reverse=True)
    
    return ProjectListResponse(
        success=True,
        projects=projects,
        total=len(projects)
    )


@router.post("", response_model=ProjectDetailResponse)
async def create_project(request: ProjectCreateRequest):
    """Create a new project."""
    ensure_projects_dir()
    
    project_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    project = ProjectResponse(
        id=project_id,
        name=request.name,
        description=request.description,
        created_at=now,
        updated_at=now,
        thumbnail=None,
        diagram_data=None
    )
    
    # Save project
    project_path = get_project_path(project_id)
    with open(project_path, "w", encoding="utf-8") as f:
        json.dump(project.model_dump(mode="json"), f, ensure_ascii=False, indent=2)
    
    return ProjectDetailResponse(success=True, project=project)


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(project_id: str):
    """Get project by ID."""
    project_path = get_project_path(project_id)
    
    if not project_path.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        with open(project_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            project = ProjectResponse(**data)
        return ProjectDetailResponse(success=True, project=project)
    except (json.JSONDecodeError, IOError) as e:
        raise HTTPException(status_code=500, detail=f"Failed to load project: {str(e)}")


@router.put("/{project_id}", response_model=ProjectDetailResponse)
async def update_project(project_id: str, request: ProjectUpdateRequest):
    """Update project."""
    project_path = get_project_path(project_id)
    
    if not project_path.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        with open(project_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Update fields
        if request.name is not None:
            data["name"] = request.name
        if request.description is not None:
            data["description"] = request.description
        if request.diagram_data is not None:
            data["diagram_data"] = request.diagram_data
        if request.thumbnail is not None:
            data["thumbnail"] = request.thumbnail
        
        data["updated_at"] = datetime.utcnow().isoformat()
        
        with open(project_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        project = ProjectResponse(**data)
        return ProjectDetailResponse(success=True, project=project)
    except (json.JSONDecodeError, IOError) as e:
        raise HTTPException(status_code=500, detail=f"Failed to update project: {str(e)}")


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """Delete project."""
    project_path = get_project_path(project_id)
    
    if not project_path.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        project_path.unlink()
        return {"success": True, "message": "Project deleted"}
    except IOError as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")
