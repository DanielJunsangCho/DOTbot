"""
FastAPI router for evaluation operations following CLAUDE.md standards.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, List, Optional
import logging

from app.schemas import EvaluationRequest, EvaluationResponse, MetricsSummary
from app.services.evaluation_service import EvaluationService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/evaluation", tags=["evaluation"])


def get_evaluation_service() -> EvaluationService:
    """Dependency injection for evaluation service"""
    return EvaluationService()


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_data(
    request: EvaluationRequest,
    evaluation_service: EvaluationService = Depends(get_evaluation_service)
) -> EvaluationResponse:
    """
    Evaluate scraping or analysis results.
    
    Args:
        request: Evaluation configuration and data
        evaluation_service: Injected evaluation service
        
    Returns:
        Evaluation results with calculated metrics
        
    Raises:
        HTTPException: On validation or processing errors
    """
    
    logger.info(f"Evaluation request received for mode: {request.mode}")
    
    try:
        response = await evaluation_service.evaluate(request)
        
        if not response.success:
            logger.warning(f"Evaluation completed with issues: {response.error}")
        
        return response
        
    except ValueError as e:
        logger.error(f"Evaluation validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Evaluation processing error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Processing error: {str(e)}"
        )


@router.get("/metrics/summary", response_model=MetricsSummary)
async def get_metrics_summary(
    days: int = Query(30, description="Number of days to include", ge=1, le=365),
    metric_types: Optional[List[str]] = Query(None, description="Specific metric types to include"),
    evaluation_service: EvaluationService = Depends(get_evaluation_service)
) -> MetricsSummary:
    """
    Get aggregated metrics summary for specified time period.
    
    Args:
        days: Number of days to analyze
        metric_types: Optional filter for specific metrics
        evaluation_service: Injected evaluation service
        
    Returns:
        Aggregated metrics summary with trends
        
    Raises:
        HTTPException: On processing errors
    """
    
    logger.info(f"Metrics summary requested for {days} days")
    
    try:
        summary = await evaluation_service.get_metrics_summary(
            days=days,
            metric_types=metric_types
        )
        
        return summary
        
    except Exception as e:
        logger.error(f"Metrics summary error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Summary generation error: {str(e)}"
        )


@router.get("/metrics/trends")
async def get_metrics_trends(
    metric_name: str = Query(..., description="Metric name to analyze"),
    days: int = Query(30, description="Time period in days", ge=1, le=365),
    evaluation_service: EvaluationService = Depends(get_evaluation_service)
) -> Dict[str, Any]:
    """
    Get trend analysis for a specific metric.
    
    Args:
        metric_name: Name of the metric to analyze
        days: Number of days to analyze
        evaluation_service: Injected evaluation service
        
    Returns:
        Trend analysis data and visualizations
        
    Raises:
        HTTPException: On processing errors
    """
    
    logger.info(f"Trend analysis requested for {metric_name} over {days} days")
    
    try:
        trends = await evaluation_service.analyze_metric_trends(
            metric_name=metric_name,
            days=days
        )
        
        return {
            "metric_name": metric_name,
            "time_period_days": days,
            "trends": trends
        }
        
    except ValueError as e:
        logger.error(f"Trend analysis validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid metric name or parameters: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Trend analysis error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Trend analysis error: {str(e)}"
        )


@router.post("/benchmark")
async def run_benchmark(
    test_data: Dict[str, Any],
    evaluation_service: EvaluationService = Depends(get_evaluation_service)
) -> Dict[str, Any]:
    """
    Run evaluation benchmark on test dataset.
    
    Args:
        test_data: Benchmark test data configuration
        evaluation_service: Injected evaluation service
        
    Returns:
        Benchmark results and performance metrics
        
    Raises:
        HTTPException: On processing errors
    """
    
    logger.info("Evaluation benchmark requested")
    
    try:
        benchmark_results = await evaluation_service.run_benchmark(test_data)
        
        return {
            "benchmark": "evaluation_performance",
            "status": "completed",
            "results": benchmark_results
        }
        
    except Exception as e:
        logger.error(f"Benchmark error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Benchmark error: {str(e)}"
        )


@router.get("/status")
async def get_evaluation_status(
    evaluation_service: EvaluationService = Depends(get_evaluation_service)
) -> Dict[str, Any]:
    """
    Get current evaluation service status.
    
    Args:
        evaluation_service: Injected evaluation service
        
    Returns:
        Service status and configuration
    """
    
    try:
        status = await evaluation_service.get_status()
        return {
            "service": "evaluation",
            "status": "operational",
            "configuration": status
        }
        
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return {
            "service": "evaluation", 
            "status": "error",
            "error": str(e)
        }