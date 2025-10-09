"""
DOTbot - Unified Web Scraping and AI Behavior Analysis Tool

A comprehensive system that combines general web scraping capabilities
with specialized AI behavior detection and analysis.
"""

__version__ = "1.0.0"
__author__ = "DOTbot Team"
__description__ = "Unified web scraping and AI behavior analysis tool"

# Main API exports
from api import DOTbotAPI, create_dotbot_instance

# Core components
from core.schemas import (
    ScrapeRequest,
    ScrapeResult, 
    AISketchyReport,
    EvaluationMetrics
)
from core.config import config

# Scraping components
from scraping import ScraperFactory, BasicScraper

# Processing components  
from processing import ProcessingPipeline

# Workflows
from workflows import UnifiedScraperWorkflow

# Evaluation
from evaluation import UnifiedEvaluator

__all__ = [
    # Main API
    "DOTbotAPI",
    "create_dotbot_instance",
    
    # Core schemas
    "ScrapeRequest",
    "ScrapeResult",
    "AISketchyReport", 
    "EvaluationMetrics",
    
    # Configuration
    "config",
    
    # Components
    "ScraperFactory",
    "BasicScraper",
    "ProcessingPipeline",
    "UnifiedScraperWorkflow",
    "UnifiedEvaluator"
]