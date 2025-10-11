"""
Scraping-related Pydantic v2 schemas following CLAUDE.md standards.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, validator, ConfigDict
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum


# ScrapeMode removed - always use "auto" mode


class ExportFormat(str, Enum):
    """Enumeration for export formats"""
    CSV = "csv"
    JSON = "json"
    DB = "db"


class ScrapeRequest(BaseModel):
    """Unified scrape request schema with comprehensive validation"""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=True
    )
    
    url: str = Field(..., description="URL to scrape", min_length=1)
    question: Optional[str] = Field(None, description="Question for AI behavior analysis")
    max_depth: int = Field(1, description="Maximum scraping depth", ge=1, le=5)
# scrape_mode removed - always use "auto"
    categories: Optional[List[str]] = Field(None, description="AI behavior categories to analyze")
    export_format: ExportFormat = Field(ExportFormat.CSV, description="Output format")
    
    @validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v
    
    @validator('categories', pre=True)
    @classmethod
    def validate_categories(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Ensure categories are unique and valid"""
        if v is None:
            return v
        return list(set(v))


class RawScrapeData(BaseModel):
    """Raw scraped content with metadata"""
    
    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=True
    )
    
    url: str = Field(..., description="Source URL")
    text: str = Field(..., description="Extracted text content")
    html: Optional[str] = Field(None, description="Raw HTML content")
    source: str = Field(..., description="Content source identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Extraction timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('text')
    @classmethod
    def validate_text_not_empty(cls, v: str) -> str:
        """Ensure text content is not empty"""
        if not v.strip():
            raise ValueError('Text content cannot be empty')
        return v


class BehaviorClassification(BaseModel):
    """AI behavior classification with confidence scoring"""
    
    model_config = ConfigDict(validate_assignment=True)
    
    excerpt: str = Field(..., description="Text excerpt containing behavior", min_length=1)
    categories: List[str] = Field(..., description="Behavior categories", min_length=1)
    stance: Optional[str] = Field(None, description="Author's stance on the behavior")
    tone: Optional[str] = Field(None, description="Tone of the content")
    confidence: float = Field(0.8, description="Classification confidence", ge=0.0, le=1.0)
    
    @validator('categories')
    @classmethod
    def validate_categories_unique(cls, v: List[str]) -> List[str]:
        """Ensure categories are unique"""
        return list(set(v))


class AIBehaviorReport(BaseModel):
    """Structured AI behavior report"""
    
    model_config = ConfigDict(validate_assignment=True)
    
    url: str = Field(..., description="Source URL")
    excerpt: str = Field(..., description="Relevant text excerpt")
    full_text: str = Field(..., description="Complete text content for detailed viewing")
    categories: List[str] = Field(..., description="Behavior categories")
    source: str = Field(..., description="Content source")
    date: Optional[str] = Field(None, description="Content date")
    stance: Optional[str] = Field(None, description="Author stance")
    tone: Optional[str] = Field(None, description="Content tone")
    confidence: int = Field(..., description="Analysis confidence (1-100)", ge=1, le=100)
    keywords: List[str] = Field(default_factory=list, description="Detected keywords indicating behavior")
    reasoning: str = Field(..., description="LLM reasoning for detection")


class ScrapeResult(BaseModel):
    """Unified scrape result supporting both general and AI behavior analysis"""
    
    model_config = ConfigDict(validate_assignment=True)
    
    structured_data: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="General structured data"
    )
    ai_reports: Optional[List[AIBehaviorReport]] = Field(
        None, 
        description="AI behavior analysis reports"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Scraping metadata"
    )
    scrape_mode: str = Field(..., description="Scraping mode used")
    success: bool = Field(True, description="Operation success status")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    # @validator('ai_reports', always=True)
    # @classmethod
    # def validate_not_both_empty(cls, v, values):
    #     """Ensure at least one data type is present on success"""
    #     if values.get('success', True):
    #         structured_data = values.get('structured_data', [])
    #         if not v and not structured_data:
    #             raise ValueError('Success results must have either structured_data or ai_reports')
    #     return v


# Task orchestration schemas
class TaskStatus(str, Enum):
    """Task execution status for orchestrated operations"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed" 
    FAILED = "failed"
    PARTIAL = "partial"  # Completed with some failures
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    """Types of orchestrated tasks"""
    MULTI_DEPTH_SCRAPE = "multi_depth_scrape"
    BATCH_SCRAPE = "batch_scrape"
    AI_BEHAVIOR_ANALYSIS = "ai_behavior_analysis"


class TaskSubmissionResponse(BaseModel):
    """Response when submitting a task for async processing"""
    
    model_config = ConfigDict(validate_assignment=True)
    
    task_id: str = Field(..., description="Unique task identifier")
    status: TaskStatus = Field(..., description="Initial task status")
    message: str = Field(..., description="Submission confirmation message")
    estimated_duration_minutes: Optional[int] = Field(None, description="Estimated completion time")
    
    
class TaskProgress(BaseModel):
    """Real-time task progress information"""
    
    model_config = ConfigDict(validate_assignment=True)
    
    task_id: str = Field(..., description="Task identifier")
    status: TaskStatus = Field(..., description="Current task status")
    progress: float = Field(..., description="Progress percentage (0-100)", ge=0, le=100)
    total_items: int = Field(..., description="Total items to process", ge=0)
    completed_items: int = Field(..., description="Successfully completed items", ge=0)
    failed_items: int = Field(..., description="Failed items", ge=0)
    current_item: Optional[str] = Field(None, description="Currently processing item")
    created_at: datetime = Field(..., description="Task creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    duration_seconds: float = Field(..., description="Total execution time", ge=0)


class TaskResultSummary(BaseModel):
    """Summary of task execution results"""
    
    model_config = ConfigDict(validate_assignment=True)
    
    task_id: str = Field(..., description="Task identifier")
    status: TaskStatus = Field(..., description="Final task status")
    results_count: int = Field(..., description="Number of successful results", ge=0)
    errors_count: int = Field(..., description="Number of errors encountered", ge=0)
    success_rate: float = Field(..., description="Success percentage", ge=0, le=100)
    total_items: int = Field(..., description="Total items processed", ge=0)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Task metadata")
    duration_seconds: float = Field(..., description="Total execution time", ge=0)


class TaskResultsResponse(BaseModel):
    """Complete task results with data"""
    
    model_config = ConfigDict(validate_assignment=True)
    
    task_id: str = Field(..., description="Task identifier")
    status: TaskStatus = Field(..., description="Task status")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="Scraped data results")
    errors: Optional[List[str]] = Field(None, description="Error messages if requested")
    summary: TaskResultSummary = Field(..., description="Results summary")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Task metadata")


class AsyncScrapeRequest(ScrapeRequest):
    """Extended scrape request for async operations"""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=True
    )
    
    max_concurrent_articles: Optional[int] = Field(
        10, 
        description="Max articles to scrape concurrently",
        ge=1, 
        le=25
    )
    retry_attempts: Optional[int] = Field(
        3,
        description="Retry attempts per article", 
        ge=1,
        le=5
    )
    timeout_minutes: Optional[int] = Field(
        30,
        description="Overall task timeout in minutes",
        ge=5,
        le=120
    )
    partial_results_ok: bool = Field(
        True,
        description="Accept partial results on timeout/errors"
    )