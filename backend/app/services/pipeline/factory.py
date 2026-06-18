"""Pipeline factory for creating pipeline instances."""

from app.services.pipeline.base import BasePipeline, PipelineMode
from app.services.pipeline.draft_pipeline import DraftPipeline
from app.services.pipeline.generate_pipeline import GeneratePipeline
from app.services.pipeline.assembly_pipeline import AssemblyPipeline
from app.services.pipeline.auto_pipeline import AutoPipeline


def create_pipeline(mode: PipelineMode, llm_service) -> BasePipeline:
    """Create a pipeline instance based on mode.
    
    Args:
        mode: The pipeline mode to create
        llm_service: The LLM service instance
        
    Returns:
        A pipeline instance
    """
    pipelines = {
        PipelineMode.AUTO: AutoPipeline,
        PipelineMode.DRAFT: DraftPipeline,
        PipelineMode.GENERATE: GeneratePipeline,
        PipelineMode.ASSEMBLY: AssemblyPipeline,
    }
    
    pipeline_class = pipelines.get(mode, AutoPipeline)
    return pipeline_class(llm_service)
