"""
Workflow and LangGraph-related schemas following CLAUDE.md standards.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
# from langgraph.graph import MessagesState  # Commented out for testing

from .scrape_schemas import ScrapeResult, RawScrapeData


class WorkflowInput(BaseModel):
    """Standardized input for all workflow operations"""
    
    model_config = ConfigDict(validate_assignment=True)
    
    url: str = Field(..., description="Target URL for processing")
    question: Optional[str] = Field(None, description="Processing context or question") 
# scrape_mode removed - always use "auto"
    max_depth: int = Field(1, description="Maximum processing depth", ge=1, le=5)
    categories: Optional[List[str]] = Field(None, description="Analysis categories")
    export_format: str = Field("csv", description="Output format preference")


class WorkflowOutput(BaseModel):
    """Standardized output for all workflow operations"""
    
    model_config = ConfigDict(validate_assignment=True)
    
    success: bool = Field(..., description="Operation success status")
    result: Optional[ScrapeResult] = Field(None, description="Processing results")
    export_path: Optional[str] = Field(None, description="Path to exported data")
    error: Optional[str] = Field(None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Operation metadata")


class UnifiedState(BaseModel):
    """
    Workflow state schema following CLAUDE.md standards.
    
    Maintains type safety and validation for workflow processing.
    """
    
    # Core processing parameters
    url: str = Field(..., description="Target URL")
    question: Optional[str] = Field(None, description="Processing context")
# scrape_mode removed - always use "auto" 
    max_depth: int = Field(1, description="Processing depth")
    categories: Optional[List[str]] = Field(None, description="Analysis categories")
    
    # Processing state
    raw_scrapes: List[RawScrapeData] = Field(default_factory=list, description="Raw scraped data")
    processed_data: Optional[ScrapeResult] = Field(None, description="Processed results")
    
    # Output configuration
    export_format: str = Field("csv", description="Export format")
    export_path: Optional[str] = Field(None, description="Export destination")
    
    # Operation status
    success: bool = Field(True, description="Operation status")
    error: Optional[str] = Field(None, description="Error information")
    
    # Workflow metadata
    current_step: str = Field("initialize", description="Current workflow step")
    step_history: List[str] = Field(default_factory=list, description="Completed steps")
    
    model_config = ConfigDict(arbitrary_types_allowed=True)


class NodeInput(BaseModel):
    """Standardized input for individual workflow nodes"""
    
    model_config = ConfigDict(validate_assignment=True)
    
    state: Dict[str, Any] = Field(..., description="Current workflow state")
    config: Optional[Dict[str, Any]] = Field(None, description="Node configuration")


class NodeOutput(BaseModel):
    """Standardized output for individual workflow nodes"""
    
    model_config = ConfigDict(validate_assignment=True)
    
    state_updates: Dict[str, Any] = Field(..., description="State updates to apply")
    success: bool = Field(True, description="Node execution status")
    error: Optional[str] = Field(None, description="Error information")
    next_step: Optional[str] = Field(None, description="Suggested next step")