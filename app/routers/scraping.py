"""
FastAPI router for scraping operations following CLAUDE.md standards.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from app.schemas import (
    ScrapeRequest, 
    ScrapeResult, 
    WorkflowOutput, 
    AsyncScrapeRequest,
    TaskSubmissionResponse,
    TaskProgress,
    TaskStatus
)
from app.services.scraping_service import ScrapingService
from app.services.storage_service import StorageService
from app.services.task_orchestrator import get_task_orchestrator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scraping", tags=["scraping"])


def get_scraping_service() -> ScrapingService:
    """Dependency injection for scraping service"""
    return ScrapingService()


def get_storage_service() -> StorageService:
    """Dependency injection for storage service"""
    return StorageService()


def get_orchestrator():
    """Dependency injection for task orchestrator"""
    return get_task_orchestrator()


@router.post("/scrape", response_model=WorkflowOutput)
async def scrape_url(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    scraping_service: ScrapingService = Depends(get_scraping_service),
    storage_service: StorageService = Depends(get_storage_service)
) -> WorkflowOutput:
    """
    Scrape data from a URL with comprehensive error handling.
    
    Args:
        request: Scraping configuration and parameters
        background_tasks: FastAPI background task handler
        scraping_service: Injected scraping service
        storage_service: Injected storage service
        
    Returns:
        Workflow output with results and export information
        
    Raises:
        HTTPException: On validation or processing errors
    """
    
    logger.info(f"Scraping request received for URL: {request.url}")
    
    try:
        # Execute scraping workflow
        result = await scraping_service.execute_scrape(request)
        
        if not result.success:
            logger.error(f"Scraping failed: {result.error}")
            raise HTTPException(
                status_code=400,
                detail=f"Scraping failed: {result.error}"
            )
        
        # Store results in background if requested
        if request.export_format in ["csv", "json"]:
            background_tasks.add_task(
                storage_service.store_result,
                result.result,
                request.export_format
            )
        
        logger.info(f"Scraping completed successfully for {request.url}")
        return result
        
    except Exception as e:
        logger.error(f"Unexpected error during scraping: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/analyze-ai-behavior", response_model=WorkflowOutput)
async def analyze_ai_behavior(
    request: ScrapeRequest,
    scraping_service: ScrapingService = Depends(get_scraping_service)
) -> WorkflowOutput:
    """
    Specialized endpoint for AI behavior analysis.
    
    Args:
        request: Analysis configuration with required question
        scraping_service: Injected scraping service
        
    Returns:
        Analysis results with AI behavior reports
        
    Raises:
        HTTPException: On validation or processing errors
    """
    
    if not request.question:
        raise HTTPException(
            status_code=400,
            detail="Question parameter is required for AI behavior analysis"
        )
    
    logger.info(f"AI behavior analysis requested for URL: {request.url}")
    
    try:
        result = await scraping_service.execute_ai_behavior_analysis(request)
        
        if not result.success:
            raise HTTPException(
                status_code=400,
                detail=f"AI behavior analysis failed: {result.error}"
            )
        
        return result
        
    except Exception as e:
        logger.error(f"AI behavior analysis error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis error: {str(e)}"
        )


@router.post("/batch-scrape", response_model=List[WorkflowOutput])
async def batch_scrape(
    requests: List[ScrapeRequest],
    scraping_service: ScrapingService = Depends(get_scraping_service)
) -> List[WorkflowOutput]:
    """
    Process multiple URLs in batch with rate limiting.
    
    Args:
        requests: List of scraping requests
        scraping_service: Injected scraping service
        
    Returns:
        List of workflow outputs for each request
        
    Raises:
        HTTPException: On validation errors
    """
    
    if not requests:
        raise HTTPException(
            status_code=400,
            detail="Request list cannot be empty"
        )
    
    if len(requests) > 10:  # Rate limiting
        raise HTTPException(
            status_code=400,
            detail="Batch size limited to 10 requests"
        )
    
    logger.info(f"Batch scraping requested for {len(requests)} URLs")
    
    try:
        results = await scraping_service.execute_batch_scrape(requests)
        return results
        
    except Exception as e:
        logger.error(f"Batch scraping error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Batch processing error: {str(e)}"
        )


@router.get("/export/{export_id}")
async def download_export(
    export_id: str,
    storage_service: StorageService = Depends(get_storage_service)
) -> FileResponse:
    """
    Download exported scraping results.
    
    Args:
        export_id: Export file identifier
        storage_service: Injected storage service
        
    Returns:
        File download response
        
    Raises:
        HTTPException: If export not found
    """
    
    try:
        file_path = await storage_service.get_export_path(export_id)
        
        if not file_path or not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Export file not found"
            )
        
        return FileResponse(
            path=str(file_path),
            filename=file_path.name,
            media_type='application/octet-stream'
        )
        
    except Exception as e:
        logger.error(f"Export download error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Download error: {str(e)}"
        )


@router.post("/async-scrape", response_model=TaskSubmissionResponse)
async def async_scrape_url(
    request: AsyncScrapeRequest,
    orchestrator = Depends(get_orchestrator)
) -> TaskSubmissionResponse:
    """
    Submit a multi-depth scraping task for async background processing.
    
    This endpoint immediately returns a task ID and processes the scraping
    in the background to handle long-running operations (25+ articles).
    
    Args:
        request: Async scraping configuration with concurrency settings
        orchestrator: Injected task orchestrator service
        
    Returns:
        Task submission response with task ID for status tracking
        
    Raises:
        HTTPException: On validation or submission errors
    """
    
    logger.info(f"Async scraping request received for URL: {request.url}")
    logger.info(f"DEBUG: Received question='{request.question}' (type: {type(request.question)})")
    logger.info(f"DEBUG: Received categories={request.categories}")
    
    try:
        # Convert AsyncScrapeRequest to base ScrapeRequest for orchestrator
        base_request = ScrapeRequest(
            url=request.url,
            question=request.question,
            max_depth=request.max_depth,
            categories=request.categories,
            export_format=request.export_format
        )
        
        logger.info(f"DEBUG: Base request question='{base_request.question}' (type: {type(base_request.question)})")
        
        # Submit to orchestrator for background processing
        task_id = await orchestrator.submit_multi_depth_scrape(
            base_request, 
            timeout_minutes=request.timeout_minutes
        )
        
        # Estimate duration based on max_depth and expected articles
        estimated_articles = min(25, 5 * request.max_depth)  # Conservative estimate
        estimated_duration = max(5, estimated_articles // request.max_concurrent_articles)
        
        logger.info(f"Submitted async scraping task {task_id} for {request.url}")
        
        return TaskSubmissionResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            message=f"Multi-depth scraping task submitted successfully. Expected to process {estimated_articles} articles.",
            estimated_duration_minutes=estimated_duration
        )
        
    except Exception as e:
        logger.error(f"Failed to submit async scraping task: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit scraping task: {str(e)}"
        )


@router.get("/tasks/{task_id}/status", response_model=TaskProgress)
async def get_task_status(
    task_id: str,
    orchestrator = Depends(get_orchestrator)
) -> TaskProgress:
    """
    Get real-time status and progress of an async scraping task.
    
    Args:
        task_id: Task identifier from async-scrape response
        orchestrator: Injected task orchestrator service
        
    Returns:
        Current task progress and status
        
    Raises:
        HTTPException: If task not found or access error
    """
    
    try:
        task_status = await orchestrator.get_task_status(task_id)
        
        if not task_status:
            raise HTTPException(
                status_code=404,
                detail=f"Task {task_id} not found"
            )
        
        # Convert orchestrator response to TaskProgress schema
        return TaskProgress(
            task_id=task_status["task_id"],
            status=TaskStatus(task_status["status"]),
            progress=task_status["progress"],
            total_items=task_status["total_items"],
            completed_items=task_status["completed_items"], 
            failed_items=task_status["failed_items"],
            created_at=datetime.fromisoformat(task_status["created_at"]),
            updated_at=datetime.fromisoformat(task_status["updated_at"]),
            completed_at=datetime.fromisoformat(task_status["completed_at"]) if task_status["completed_at"] else None,
            duration_seconds=task_status["duration_seconds"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task status for {task_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving task status: {str(e)}"
        )


@router.get("/tasks/{task_id}/results")
async def get_task_results(
    task_id: str,
    include_errors: bool = False,
    orchestrator = Depends(get_orchestrator)
) -> Dict[str, Any]:
    """
    Get complete results from a completed async scraping task.
    
    Args:
        task_id: Task identifier from async-scrape response
        include_errors: Whether to include detailed error information
        orchestrator: Injected task orchestrator service
        
    Returns:
        Complete task results with scraped data
        
    Raises:
        HTTPException: If task not found or not completed
    """
    
    try:
        results = await orchestrator.get_task_results(task_id, include_errors=include_errors)
        
        if not results:
            raise HTTPException(
                status_code=404,
                detail=f"Task {task_id} not found"
            )
        
        # Extract summary data for processing
        summary_data = results.get("summary", {})
        
        # Convert raw scraped data to WorkflowOutput format for frontend compatibility
        from app.schemas import WorkflowOutput, ScrapeResult
        
        # Extract AI reports from metadata (added by task orchestrator)
        ai_reports_data = results.get("metadata", {}).get("ai_reports", [])
        logger.info(f"DEBUG: Retrieved {len(ai_reports_data)} AI reports from task metadata")
        logger.info(f"DEBUG: Full metadata keys: {list(results.get('metadata', {}).keys())}")
        
        # Convert to proper AI behavior report objects
        from app.schemas import AIBehaviorReport
        ai_reports = []
        for i, report_data in enumerate(ai_reports_data):
            try:
                logger.debug(f"DEBUG: Processing AI report {i}: {report_data}")
                ai_report = AIBehaviorReport(
                    url=report_data["url"],
                    excerpt=report_data["excerpt"],
                    categories=report_data["categories"],
                    severity=report_data["severity"],
                    source=report_data["source"],
                    confidence=report_data["confidence"],
                    stance=report_data.get("stance"),
                    tone=report_data.get("tone"),
                    date=report_data.get("date")
                )
                ai_reports.append(ai_report)
                logger.debug(f"DEBUG: Successfully converted AI report {i}")
            except Exception as e:
                logger.warning(f"Failed to convert AI report {i}: {e}")
                logger.warning(f"DEBUG: Failed report data: {report_data}")
        
        logger.info(f"DEBUG: Successfully converted {len(ai_reports)} AI behavior reports")
        
        # Create WorkflowOutput with both raw data and AI reports
        scrape_result = ScrapeResult(
            structured_data=results["results"],  # Raw scraped content
            ai_reports=ai_reports,  # Processed AI behavior reports
            metadata={
                "analysis_type": "ai_behavior" if ai_reports else "general",
                "pages_analyzed": len(results["results"]),
                "reports_generated": len(ai_reports),
                "processing_time": summary_data.get("duration_seconds", 0)
            },
            scrape_mode="auto",
            success=results["status"] in ["completed", "partial"]
        )
        
        workflow_output = WorkflowOutput(
            success=results["status"] in ["completed", "partial"],
            result=scrape_result,
            metadata={
                "task_id": task_id,
                "analysis_mode": "ai_behavior" if ai_reports else "general",
                "processing_time": summary_data.get("duration_seconds", 0)
            }
        )
        
        
        # Return in format expected by frontend
        return {
            "task_id": task_id,
            "status": results["status"],
            "results": workflow_output,  # WorkflowOutput object
            "summary": {
                "total_pages": len(results["results"]),
                "successful_pages": len(results["results"]) - len(results.get("errors", [])),
                "failed_pages": len(results.get("errors", [])),
                "ai_reports_found": len(ai_reports),
                "total_processing_time": summary_data.get("duration_seconds", 0)
            },
            "errors": results.get("errors") if include_errors else None,
            "metadata": results["metadata"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task results for {task_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving task results: {str(e)}"
        )


@router.get("/debug/test-ai-analysis")
async def test_ai_analysis() -> Dict[str, Any]:
    """Debug endpoint to test AI behavior analysis"""
    
    # Test data
    test_content = {
        "url": "https://example.com/test",
        "text": "This AI system shows deceptive behavior by misleading users about its capabilities. It also demonstrates reward gaming by optimizing for metrics rather than actual performance.",
        "full_text": "This AI system shows deceptive behavior by misleading users about its capabilities. It also demonstrates reward gaming by optimizing for metrics rather than actual performance.",
        "source": "test",
        "timestamp": "2024-01-01T00:00:00"
    }
    
    test_categories = ["Deceptive Behaviour", "Reward Gaming", "Sycophancy"]
    test_question = "What AI behaviors are concerning?"
    
    try:
        # Import and test the analysis
        from app.services.scraping_service import ScrapingService
        scraping_service = ScrapingService()
        
        reports = []
        for category in test_categories:
            if scraping_service._detect_behavior_in_content(test_content["text"], category, test_question):
                report = {
                    "url": test_content["url"],
                    "excerpt": scraping_service._extract_relevant_excerpt(test_content["text"], category),
                    "categories": [category],
                    "severity": scraping_service._calculate_severity(test_content["text"], category),
                    "source": test_content["source"],
                    "confidence": 0.75,
                    "stance": "concerning",
                    "tone": "analytical"
                }
                reports.append(report)
        
        return {
            "success": True,
            "test_content": test_content,
            "categories_tested": test_categories,
            "reports_generated": len(reports),
            "reports": reports
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.delete("/tasks/{task_id}")
async def cancel_task(
    task_id: str,
    orchestrator = Depends(get_orchestrator)
) -> Dict[str, str]:
    """
    Cancel a running async scraping task.
    
    Args:
        task_id: Task identifier to cancel
        orchestrator: Injected task orchestrator service
        
    Returns:
        Cancellation confirmation
        
    Raises:
        HTTPException: If task not found or cannot be cancelled
    """
    
    try:
        success = await orchestrator.cancel_task(task_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Task {task_id} not found or cannot be cancelled"
            )
        
        logger.info(f"Task {task_id} cancelled successfully")
        return {"message": f"Task {task_id} cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling task {task_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error cancelling task: {str(e)}"
        )


@router.get("/tasks", response_model=List[TaskProgress])
async def list_tasks(
    status_filter: Optional[TaskStatus] = None,
    limit: int = 50,
    orchestrator = Depends(get_orchestrator)
) -> List[TaskProgress]:
    """
    List all tasks with optional status filtering.
    
    Args:
        status_filter: Filter tasks by status (optional)
        limit: Maximum number of tasks to return
        orchestrator: Injected task orchestrator service
        
    Returns:
        List of task progress information
    """
    
    try:
        tasks = await orchestrator.get_all_tasks(status_filter=status_filter, limit=limit)
        
        # Convert to TaskProgress objects
        progress_list = []
        for task in tasks:
            progress_list.append(TaskProgress(
                task_id=task["task_id"],
                status=TaskStatus(task["status"]),
                progress=task["progress"],
                total_items=task["total_items"],
                completed_items=task["completed_items"],
                failed_items=task["failed_items"],
                created_at=datetime.fromisoformat(task["created_at"]),
                updated_at=datetime.fromisoformat(task["updated_at"]),
                completed_at=datetime.fromisoformat(task["completed_at"]) if task["completed_at"] else None,
                duration_seconds=task["duration_seconds"]
            ))
        
        return progress_list
        
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving task list: {str(e)}"
        )


@router.get("/status")
async def get_scraping_status(
    scraping_service: ScrapingService = Depends(get_scraping_service),
    orchestrator = Depends(get_orchestrator)
) -> Dict[str, Any]:
    """
    Get current scraping service status and capabilities.
    
    Args:
        scraping_service: Injected scraping service
        orchestrator: Injected task orchestrator service
        
    Returns:
        Service status and available capabilities
    """
    
    try:
        status = await scraping_service.get_status()
        orchestrator_health = await orchestrator.health_check()
        
        return {
            "service": "scraping",
            "status": "operational",
            "capabilities": status,
            "orchestrator": orchestrator_health
        }
        
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return {
            "service": "scraping",
            "status": "error",
            "error": str(e)
        }