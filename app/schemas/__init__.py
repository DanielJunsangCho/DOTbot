"""
Pydantic v2 Schema Definitions for DOTbot

Following CLAUDE.md standards for FastAPI + Pydantic v2 schemas.
"""

from __future__ import annotations

from .scrape_schemas import (
    ScrapeRequest,
    RawScrapeData, 
    ScrapeResult,
    BehaviorClassification,
    AIBehaviorReport,
    AsyncScrapeRequest,
    TaskStatus,
    TaskType,
    TaskSubmissionResponse,
    TaskProgress,
    TaskResultSummary,
    TaskResultsResponse
)
from .workflow_schemas import (
    UnifiedState,
    WorkflowInput,
    WorkflowOutput
)
from .evaluation_schemas import (
    EvaluationMetrics,
    EvaluationRequest,
    EvaluationResponse,
    MetricsSummary
)

__all__ = [
    "ScrapeRequest",
    "RawScrapeData",
    "ScrapeResult", 
    "BehaviorClassification",
    "AIBehaviorReport",
    "AsyncScrapeRequest",
    "TaskStatus",
    "TaskType",
    "TaskSubmissionResponse",
    "TaskProgress",
    "TaskResultSummary",
    "TaskResultsResponse",
    "UnifiedState",
    "WorkflowInput",
    "WorkflowOutput",
    "EvaluationMetrics",
    "EvaluationRequest",
    "EvaluationResponse",
    "MetricsSummary"
]