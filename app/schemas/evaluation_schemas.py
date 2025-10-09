"""
Evaluation and metrics schemas following CLAUDE.md standards.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class EvaluationMode(str, Enum):
    """Evaluation strategy enumeration"""
    GENERAL = "general"
    BEHAVIOR = "behavior"
    AUTO = "auto"


class EvaluationRequest(BaseModel):
    """Request schema for evaluation operations"""
    
    model_config = ConfigDict(validate_assignment=True)
    
    data: Dict[str, Any] = Field(..., description="Data to evaluate")
    mode: EvaluationMode = Field(EvaluationMode.AUTO, description="Evaluation strategy")
    reference: Optional[Dict[str, Any]] = Field(None, description="Reference data for comparison")
    metrics: Optional[List[str]] = Field(None, description="Specific metrics to calculate")


class EvaluationMetrics(BaseModel):
    """Comprehensive evaluation metrics following CLAUDE.md standards"""
    
    model_config = ConfigDict(validate_assignment=True)
    
    # AI Behavior Analysis Metrics
    recall: Optional[float] = Field(None, description="Behavior detection recall", ge=0.0, le=1.0)
    precision_llm: Optional[float] = Field(None, description="LLM classification precision", ge=0.0, le=1.0)
    semantic_fidelity: Optional[float] = Field(None, description="Semantic accuracy", ge=0.0, le=1.0)
    faithfulness: Optional[float] = Field(None, description="Content faithfulness", ge=0.0, le=1.0)
    coverage: Optional[float] = Field(None, description="Content coverage", ge=0.0, le=1.0)
    novelty_score: Optional[float] = Field(None, description="Novel insight score", ge=0.0, le=1.0)
    llm_agreement: Optional[float] = Field(None, description="Multi-LLM agreement", ge=0.0, le=1.0)
    
    # General Scraping Metrics
    extraction_accuracy: Optional[float] = Field(None, description="Data extraction accuracy", ge=0.0, le=1.0)
    runtime: Optional[float] = Field(None, description="Processing runtime in seconds", ge=0.0)
    success_rate: Optional[float] = Field(None, description="Operation success rate", ge=0.0, le=1.0)
    
    # Quality Metrics
    completeness: Optional[float] = Field(None, description="Data completeness score", ge=0.0, le=1.0)
    consistency: Optional[float] = Field(None, description="Data consistency score", ge=0.0, le=1.0)
    
    # Metadata
    evaluation_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Evaluation time")
    evaluation_mode: str = Field(..., description="Evaluation strategy used")
    
    @validator('recall', 'precision_llm', 'semantic_fidelity', 'faithfulness', 
              'coverage', 'novelty_score', 'llm_agreement', 'extraction_accuracy', 
              'success_rate', 'completeness', 'consistency', pre=True)
    @classmethod
    def validate_percentage_metrics(cls, v: Optional[float]) -> Optional[float]:
        """Ensure percentage metrics are in valid range"""
        if v is not None and not (0.0 <= v <= 1.0):
            raise ValueError('Percentage metrics must be between 0.0 and 1.0')
        return v


class MetricsSummary(BaseModel):
    """Aggregated metrics summary for reporting"""
    
    model_config = ConfigDict(validate_assignment=True)
    
    # Summary statistics
    total_evaluations: int = Field(..., description="Number of evaluations", ge=0)
    average_scores: Dict[str, float] = Field(default_factory=dict, description="Average metric scores")
    score_ranges: Dict[str, Dict[str, float]] = Field(default_factory=dict, description="Min/max ranges")
    
    # Trend analysis
    improvement_trend: Dict[str, float] = Field(default_factory=dict, description="Score improvement trends")
    consistency_scores: Dict[str, float] = Field(default_factory=dict, description="Consistency measurements")
    
    # Time-based analysis
    time_range: Dict[str, datetime] = Field(default_factory=dict, description="Evaluation time range")
    evaluation_frequency: Optional[float] = Field(None, description="Evaluations per time unit")
    
    # Quality assessment
    overall_quality_score: Optional[float] = Field(None, description="Composite quality score", ge=0.0, le=1.0)
    recommended_improvements: List[str] = Field(default_factory=list, description="Improvement suggestions")
    
    @validator('overall_quality_score', pre=True)
    @classmethod
    def validate_quality_score(cls, v: Optional[float]) -> Optional[float]:
        """Validate overall quality score range"""
        if v is not None and not (0.0 <= v <= 1.0):
            raise ValueError('Overall quality score must be between 0.0 and 1.0')
        return v


class EvaluationResponse(BaseModel):
    """Response schema for evaluation operations"""
    
    model_config = ConfigDict(validate_assignment=True)
    
    success: bool = Field(..., description="Evaluation success status")
    metrics: Optional[EvaluationMetrics] = Field(None, description="Calculated metrics")
    summary: Optional[MetricsSummary] = Field(None, description="Aggregated summary")
    error: Optional[str] = Field(None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('metrics', 'summary')
    @classmethod
    def validate_success_requires_data(cls, v, values):
        """Ensure successful evaluations have metrics or summary"""
        if values.get('success', False) and v is None:
            if not any(values.get(field) for field in ['metrics', 'summary']):
                raise ValueError('Successful evaluations must provide metrics or summary')
        return v