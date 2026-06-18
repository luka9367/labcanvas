"""API v1 router."""

from fastapi import APIRouter

from app.api.v1.endpoints import generate, elements, projects, settings, gallery, bioicons, assistant, documents, models, references

api_router = APIRouter()

api_router.include_router(generate.router, prefix="/generate", tags=["generate"])
api_router.include_router(elements.router, prefix="/elements", tags=["elements"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(gallery.router, prefix="/gallery", tags=["gallery"])
api_router.include_router(bioicons.router, prefix="/bioicons", tags=["bioicons"])
api_router.include_router(assistant.router, prefix="/assistant", tags=["assistant"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(models.router, prefix="/models", tags=["models"])
api_router.include_router(references.router, prefix="/references", tags=["references"])
