"""
FastAPI router for workflow operations following CLAUDE.md standards.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any, List
import logging

from app.schemas import WorkflowInput, WorkflowOutput, UnifiedState
from app.services.workflow_service import WorkflowService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/workflow", tags=["workflow"])


def get_workflow_service() -> WorkflowService:
    """Dependency injection for workflow service"""
    return WorkflowService()


@router.post("/execute", response_model=WorkflowOutput)
async def execute_workflow(
    workflow_input: WorkflowInput,
    background_tasks: BackgroundTasks,
    workflow_service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowOutput:
    """
    Execute unified DOTbot workflow with comprehensive orchestration.
    
    Args:
        workflow_input: Workflow configuration and parameters
        background_tasks: FastAPI background task handler
        workflow_service: Injected workflow service
        
    Returns:
        Workflow execution results
        
    Raises:
        HTTPException: On validation or execution errors
    """
    
    logger.info(f"Workflow execution requested for URL: {workflow_input.url}")
    
    try:
        # Execute workflow with full orchestration
        result = await workflow_service.execute_unified_workflow(workflow_input)
        
        if not result.success:
            logger.error(f"Workflow execution failed: {result.error}")
            raise HTTPException(
                status_code=400,
                detail=f"Workflow failed: {result.error}"
            )
        
        # Schedule background cleanup if needed
        if result.export_path:
            background_tasks.add_task(
                workflow_service.schedule_cleanup,
                result.export_path
            )
        
        logger.info(f"Workflow completed successfully for {workflow_input.url}")
        return result
        
    except ValueError as e:
        logger.error(f"Workflow validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid workflow parameters: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Workflow execution error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Workflow execution error: {str(e)}"
        )


@router.post("/ai-behavior", response_model=WorkflowOutput)
async def execute_ai_behavior_workflow(
    workflow_input: WorkflowInput,
    workflow_service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowOutput:
    """
    Execute specialized AI behavior analysis workflow.
    
    Args:
        workflow_input: Analysis configuration with required question
        workflow_service: Injected workflow service
        
    Returns:
        AI behavior analysis results
        
    Raises:
        HTTPException: On validation or processing errors
    """
    
    if not workflow_input.question:
        raise HTTPException(
            status_code=400,
            detail="Question parameter is required for AI behavior workflow"
        )
    
    logger.info(f"AI behavior workflow requested for URL: {workflow_input.url}")
    
    try:
        result = await workflow_service.execute_ai_behavior_workflow(workflow_input)
        
        if not result.success:
            raise HTTPException(
                status_code=400,
                detail=f"AI behavior workflow failed: {result.error}"
            )
        
        return result
        
    except Exception as e:
        logger.error(f"AI behavior workflow error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"AI behavior analysis error: {str(e)}"
        )


@router.post("/general-scrape", response_model=WorkflowOutput) 
async def execute_general_scrape_workflow(
    workflow_input: WorkflowInput,
    workflow_service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowOutput:
    """
    Execute general purpose scraping workflow.
    
    Args:
        workflow_input: Scraping configuration
        workflow_service: Injected workflow service
        
    Returns:
        General scraping results
        
    Raises:
        HTTPException: On processing errors
    """
    
    logger.info(f"General scraping workflow requested for URL: {workflow_input.url}")
    
    try:
        result = await workflow_service.execute_general_scrape_workflow(workflow_input)
        
        if not result.success:
            raise HTTPException(
                status_code=400,
                detail=f"General scrape workflow failed: {result.error}"
            )
        
        return result
        
    except Exception as e:
        logger.error(f"General scrape workflow error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"General scraping error: {str(e)}"
        )


@router.get("/status/{workflow_id}")
async def get_workflow_status(
    workflow_id: str,
    workflow_service: WorkflowService = Depends(get_workflow_service)
) -> Dict[str, Any]:
    """
    Get status of a running workflow.
    
    Args:
        workflow_id: Workflow execution identifier
        workflow_service: Injected workflow service
        
    Returns:
        Workflow status and progress information
        
    Raises:
        HTTPException: If workflow not found
    """
    
    try:
        status = await workflow_service.get_workflow_status(workflow_id)
        
        if not status:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow {workflow_id} not found"
            )
        
        return status
        
    except Exception as e:
        logger.error(f"Workflow status error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Status retrieval error: {str(e)}"
        )


@router.post("/cancel/{workflow_id}")
async def cancel_workflow(
    workflow_id: str,
    workflow_service: WorkflowService = Depends(get_workflow_service)
) -> Dict[str, Any]:
    """
    Cancel a running workflow.
    
    Args:
        workflow_id: Workflow execution identifier
        workflow_service: Injected workflow service
        
    Returns:
        Cancellation confirmation
        
    Raises:
        HTTPException: If workflow not found or cannot be cancelled
    """
    
    try:
        result = await workflow_service.cancel_workflow(workflow_id)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow {workflow_id} not found or cannot be cancelled"
            )
        
        return {
            "workflow_id": workflow_id,
            "status": "cancelled",
            "message": "Workflow cancellation initiated"
        }
        
    except Exception as e:
        logger.error(f"Workflow cancellation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Cancellation error: {str(e)}"
        )


@router.get("/available")
async def get_available_workflows(
    workflow_service: WorkflowService = Depends(get_workflow_service)
) -> Dict[str, Any]:
    """
    Get information about available workflow types.
    
    Args:
        workflow_service: Injected workflow service
        
    Returns:
        Available workflow types and their capabilities
    """
    
    try:
        workflows = await workflow_service.get_available_workflows()
        
        return {
            "available_workflows": workflows,
            "status": "operational"
        }
        
    except Exception as e:
        logger.error(f"Available workflows error: {e}")
        return {
            "available_workflows": {},
            "status": "error",
            "error": str(e)
        }