"""
Scraping service implementing business logic following CLAUDE.md standards.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional
import logging
import asyncio
from datetime import datetime

from app.schemas import ScrapeRequest, WorkflowOutput, ScrapeResult, RawScrapeData
from app.scrapers import ScraperFactory
from app.services.browser_scraper import BrowserScraper
import os

logger = logging.getLogger(__name__)


class ScrapingService:
    """
    Business logic service for scraping operations.
    
    Implements pragmatic scraping with explicit contracts and 
    composable autonomy following CLAUDE.md principles.
    """
    
    def __init__(self):
        """Initialize scraping service with factory pattern"""
        self.scraper_factory = ScraperFactory()
        self.browser_scraper = BrowserScraper(api_key=os.getenv("OPENAI_API_KEY"))
        self._active_scrapers: Dict[str, Any] = {}
        
        logger.info("ScrapingService initialized with browser automation")
    
    async def execute_scrape(self, request: ScrapeRequest) -> WorkflowOutput:
        """
        Execute scraping operation with comprehensive error handling.
        
        Args:
            request: Validated scraping request
            
        Returns:
            Workflow output with results and metadata
            
        Raises:
            ValueError: On invalid scraping parameters
            RuntimeError: On scraping execution failures
        """
        
        operation_id = self._generate_operation_id()
        start_time = datetime.utcnow()
        
        logger.info(f"Executing scrape operation {operation_id} for {request.url}")
        
        try:
            # Use browser-based scraping for robust content extraction
            logger.info(f"Using browser scraper for multi-depth extraction: {request.url}")
            
            # Execute multi-depth scraping to get comprehensive content
            raw_data = await self.browser_scraper.scrape_with_depth(
                url=request.url,
                max_depth=request.max_depth
            )
            
            if not raw_data:
                raise RuntimeError("Browser scraping returned no data")
            
            # Create result structure with enhanced data
            structured_items = []
            for item in raw_data:
                structured_items.append({
                    "url": item.url,
                    "text": item.text[:2000],  # Truncate very long text
                    "full_text": item.text,
                    "source": item.source,
                    "timestamp": item.timestamp.isoformat(),
                    "depth": item.metadata.get("depth", 0),
                    "word_count": len(item.text.split()),
                    "char_count": len(item.text)
                })
            
            result = ScrapeResult(
                structured_data=structured_items,
                metadata={
                    "operation_id": operation_id,
                    "scraper_type": "BrowserScraper",
                    "request_params": request.model_dump(),
                    "processing_time": (datetime.utcnow() - start_time).total_seconds(),
                    "pages_scraped": len(raw_data),
                    "total_content_length": sum(len(item.text) for item in raw_data)
                },
                scrape_mode="auto",
                success=True
            )
            
            return WorkflowOutput(
                success=True,
                result=result,
                metadata={
                    "operation_id": operation_id,
                    "items_scraped": len(raw_data),
                    "pages_scraped": len(raw_data),
                    "processing_time": (datetime.utcnow() - start_time).total_seconds(),
                    "scraping_method": "browser-use-agent"
                }
            )
            
        except Exception as e:
            logger.error(f"Scraping operation {operation_id} failed: {e}")
            
            return WorkflowOutput(
                success=False,
                error=str(e),
                metadata={
                    "operation_id": operation_id,
                    "processing_time": (datetime.utcnow() - start_time).total_seconds()
                }
            )
    
    async def execute_ai_behavior_analysis(self, request: ScrapeRequest) -> WorkflowOutput:
        """
        Execute AI behavior analysis workflow.
        
        Args:
            request: Analysis request with required question
            
        Returns:
            Analysis results with AI behavior reports
            
        Raises:
            ValueError: On missing or invalid analysis parameters
        """
        
        if not request.question:
            raise ValueError("Question is required for AI behavior analysis")
        
        # Set AI behavior specific parameters
        enhanced_request = ScrapeRequest(
            url=request.url,
            question=request.question,
            max_depth=max(request.max_depth, 2),  # Deeper analysis
            categories=request.categories or [
                "Deceptive Behaviour", "Reward Gaming", "Sycophancy", 
                "Goal Misgeneralization", "Unauthorized Access",
                "Proxy Goal Formation", "Power Seeking", "Social Engineering",
                "Cognitive Off-Policy Behavior", "Collusion"
            ],
            export_format=request.export_format
        )
        
        logger.info(f"Executing AI behavior analysis for {request.url}")
        
        # Execute scraping directly without circular dependency
        operation_id = self._generate_operation_id()
        start_time = datetime.utcnow()
        
        try:
            # Use browser scraper for content extraction
            raw_data = await self.browser_scraper.scrape_with_depth(
                url=enhanced_request.url,
                max_depth=enhanced_request.max_depth
            )
            
            if not raw_data:
                raise RuntimeError("AI behavior scraping returned no data")
            
            # Analyze content for AI behavior patterns
            ai_reports = await self._analyze_for_ai_behavior(
                raw_data, 
                enhanced_request.categories, 
                enhanced_request.question
            )
            
            # Create result with AI behavior analysis
            result = ScrapeResult(
                structured_data=[],  # AI behavior mode focuses on reports
                ai_reports=ai_reports,
                metadata={
                    "operation_id": operation_id,
                    "analysis_type": "ai_behavior",
                    "categories_analyzed": enhanced_request.categories,
                    "question": enhanced_request.question,
                    "reports_found": len(ai_reports),
                    "pages_analyzed": len(raw_data)
                },
                scrape_mode="ai_behavior",
                success=True
            )
            
            return WorkflowOutput(
                success=True,
                result=result,
                metadata={
                    "operation_id": operation_id,
                    "analysis_mode": "ai_behavior",
                    "processing_time": (datetime.utcnow() - start_time).total_seconds()
                }
            )
            
        except Exception as e:
            logger.error(f"AI behavior analysis failed: {e}")
            return WorkflowOutput(
                success=False,
                error=str(e),
                metadata={
                    "operation_id": operation_id,
                    "analysis_mode": "ai_behavior",
                    "processing_time": (datetime.utcnow() - start_time).total_seconds()
                }
            )
    
    async def execute_batch_scrape(
        self, 
        requests: List[ScrapeRequest]
    ) -> List[WorkflowOutput]:
        """
        Execute batch scraping with rate limiting and error isolation.
        
        Args:
            requests: List of scraping requests
            
        Returns:
            List of workflow outputs for each request
        """
        
        logger.info(f"Executing batch scrape for {len(requests)} requests")
        
        results = []
        for i, request in enumerate(requests):
            try:
                logger.info(f"Processing batch item {i+1}/{len(requests)}: {request.url}")
                
                result = await self.execute_scrape(request)
                results.append(result)
                
                # Rate limiting between requests
                if i < len(requests) - 1:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.error(f"Batch item {i+1} failed: {e}")
                results.append(WorkflowOutput(
                    success=False,
                    error=str(e),
                    metadata={"batch_index": i, "url": request.url}
                ))
        
        successful = sum(1 for r in results if r.success)
        logger.info(f"Batch scrape completed: {successful}/{len(requests)} successful")
        
        return results
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get scraping service status and capabilities.
        
        Returns:
            Service status with available scrapers and configuration
        """
        
        try:
            available_scrapers = self.scraper_factory.get_available_scrapers()
            
            return {
                "service_status": "operational",
                "available_scrapers": available_scrapers,
                "active_operations": len(self._active_scrapers),
                "configuration": {
                    "default_scrape_mode": "auto",
                    "max_depth": 5,
                    "request_timeout": 30
                }
            }
            
        except Exception as e:
            logger.error(f"Status check failed: {e}")
            return {
                "service_status": "error",
                "error": str(e)
            }
    
    async def _get_scraper(self, mode: str, url: str) -> Optional[Any]:
        """
        Get appropriate scraper based on mode and URL characteristics.
        
        Args:
            mode: Scraping mode preference
            url: Target URL for analysis
            
        Returns:
            Configured scraper instance or None if unavailable
        """
        
        try:
            return self.scraper_factory.create_scraper(mode, url)
            
        except Exception as e:
            logger.error(f"Scraper creation failed for {mode}: {e}")
            return None
    
    def _generate_operation_id(self) -> str:
        """Generate unique operation identifier"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        return f"scrape_{timestamp}"
    
    async def _analyze_for_ai_behavior(
        self, 
        raw_data: List[Any], 
        categories: List[str], 
        question: str
    ) -> List[Any]:
        """Analyze scraped content for AI behavior patterns using LLM evaluator"""
        
        # Import here to avoid circular dependencies
        from app.schemas import AIBehaviorReport
        from app.services.ai_behavior_evaluator import AIBehaviorEvaluator
        
        ai_reports = []
        
        try:
            # Initialize LLM evaluator
            evaluator = AIBehaviorEvaluator(api_key=os.getenv("OPENAI_API_KEY"))
            
            for data_item in raw_data:
                content = data_item.text if hasattr(data_item, 'text') else str(data_item)
                url = data_item.url if hasattr(data_item, 'url') else 'unknown'
                
                # Skip very short content
                if len(content.strip()) < 50:
                    continue
                
                # Analyze each category using LLM evaluator
                for category in categories:
                    try:
                        detection = await evaluator.evaluate_content(content, category, question)
                        
                        # Only create reports for detected behaviors
                        if detection.detected:
                            report = AIBehaviorReport(
                                url=url,
                                excerpt=self._extract_relevant_excerpt(content, category),
                                full_text=content.replace('\\n', '\n').replace('\\t', '\t'),  # Convert escaped characters to real ones
                                categories=[category],
                                source=f"Analysis of {url}",
                                confidence=detection.confidence,  # Use LLM confidence (1-100)
                                keywords=detection.keywords,  # Include detected keywords
                                reasoning=detection.reasoning,  # Include LLM reasoning
                                stance="concerning",
                                tone="analytical"
                            )
                            ai_reports.append(report)
                            logger.debug(f"Detected {category} behavior in {url} (confidence: {detection.confidence})")
                        
                    except Exception as e:
                        logger.error(f"Failed to analyze {category} for {url}: {e}")
                        continue
            
            logger.info(f"Generated {len(ai_reports)} AI behavior reports from LLM analysis")
            return ai_reports
            
        except Exception as e:
            logger.error(f"AI behavior analysis failed: {e}")
            return []
    
    
    def _extract_relevant_excerpt(self, content: str, category: str) -> str:
        """Extract a relevant excerpt from content for the behavior category"""
        
        # Find sentences containing relevant keywords
        sentences = content.split('.')
        for sentence in sentences:
            if len(sentence.strip()) > 20 and any(
                keyword in sentence.lower() 
                for keyword in ["ai", "behavior", "system", "model", category.lower()]
            ):
                return sentence.strip()[:200] + ("..." if len(sentence) > 200 else "")
        
        # Fallback: return first meaningful chunk
        return content[:200] + ("..." if len(content) > 200 else "")
    
