"""Schemas for project endpoints."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ProjectCreateRequest(BaseModel):
    """Request schema for project creation."""
    name: str
    description: Optional[str] = None
    template: Optional[str] = None


class ProjectUpdateRequest(BaseModel):
    """Request schema for project update."""
    name: Optional[str] = None
    description: Optional[str] = None
    diagram_data: Optional[Dict[str, Any]] = None
    thumbnail: Optional[str] = None


class ProjectResponse(BaseModel):
    """Response schema for project."""
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    thumbnail: Optional[str] = None
    diagram_data: Optional[Dict[str, Any]] = None


class ProjectListResponse(BaseModel):
    """Response schema for project list."""
    success: bool
    projects: List[ProjectResponse]
    total: int


class ProjectDetailResponse(BaseModel):
    """Response schema for project detail."""
    success: bool
    project: Optional[ProjectResponse] = None
    message: Optional[str] = None
