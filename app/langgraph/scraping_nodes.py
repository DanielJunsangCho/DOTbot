"""
Scraping-specific LangGraph nodes following CLAUDE.md standards.
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional
import logging
from pathlib import Path
from datetime import datetime

from .base_nodes import BaseLangGraphNode
from app.schemas import UnifiedState, RawScrapeData, ScrapeResult
from app.scrapers import ScraperFactory
# Commented out for now - will implement as needed
# from processing.pipeline import ProcessingPipeline
# from core.storage import StorageManager

logger = logging.getLogger(__name__)


class ScrapingNode(BaseLangGraphNode):
    """
    LangGraph node for web scraping operations.
    
    Explicit contracts as required by CLAUDE.md standards.
    """
    
    # Explicit input/output contracts
    inputs = {
        "url": str,
        "scrape_mode": str,
        "max_depth": int
    }
    outputs = {
        "raw_scrapes": List[RawScrapeData],
        "success": bool,
        "error": Optional[str]
    }
    
    def __init__(self):
        """Initialize scraping node with factory dependencies"""
        super().__init__("scraping")
        self.scraper_factory = ScraperFactory()
    
    async def process(self, state: UnifiedState) -> Dict[str, Any]:
        """
        Execute web scraping with explicit error handling.
        
        Args:
            state: Workflow state containing scraping parameters
            
        Returns:
            State updates with scraped data or error information
        """
        
        self.logger.info(f"Scraping URL: {state.url} with mode: {state.scrape_mode}")
        
        try:
            # Create appropriate scraper
            scraper = self.scraper_factory.create_scraper(
                mode=state.scrape_mode,
                url=state.url
            )
            
            if not scraper:
                raise RuntimeError(f"No suitable scraper for {state.url}")
            
            # Execute scraping with depth control
            raw_data = await scraper.scrape_url(
                url=state.url,
                max_depth=state.max_depth
            )
            
            if not raw_data:
                raise RuntimeError("Scraping returned no data")
            
            self.logger.info(f"Successfully scraped {len(raw_data)} items")
            
            return {
                "raw_scrapes": raw_data,
                "success": True,
                "error": None
            }
            
        except Exception as e:
            self.logger.error(f"Scraping failed: {e}")
            
            return {
                "raw_scrapes": [],
                "success": False,
                "error": str(e)
            }


class ProcessingNode(BaseLangGraphNode):
    """
    LangGraph node for content processing and classification.
    
    Handles both general data extraction and AI behavior analysis
    following CLAUDE.md composable autonomy principles.
    """
    
    # Explicit contracts
    inputs = {
        "raw_scrapes": List[RawScrapeData],
        "question": Optional[str],
        "categories": Optional[List[str]],
        "scrape_mode": str
    }
    outputs = {
        "processed_data": ScrapeResult,
        "success": bool,
        "error": Optional[str]
    }
    
    def __init__(self):
        """Initialize processing node with pipeline dependencies"""
        super().__init__("processing")
        # self.pipeline = ProcessingPipeline()  # Will implement as needed
    
    async def process(self, state: UnifiedState) -> Dict[str, Any]:
        """
        Process raw scraped data into structured results.
        
        Args:
            state: Workflow state with raw scraping data
            
        Returns:
            State updates with processed structured data
        """
        
        if not state.raw_scrapes:
            return {
                "processed_data": ScrapeResult(
                    structured_data=[],
                    metadata={"processing_error": "No raw data to process"},
                    scrape_mode=state.scrape_mode,
                    success=False
                ),
                "success": False,
                "error": "No raw scraping data available for processing"
            }
        
        self.logger.info(f"Processing {len(state.raw_scrapes)} scraped items")
        
        try:
            # Real content processing based on scraped data
            processing_mode = "behavior" if state.question else "general"
            
            # Process actual scraped content
            if processing_mode == "behavior":
                # Use real AI behavior analysis
                ai_reports = await self._analyze_for_ai_behavior(
                    state.raw_scrapes,
                    state.categories or [],
                    state.question
                )
                
                result = ScrapeResult(
                    structured_data=[],
                    ai_reports=ai_reports,
                    metadata={
                        "processing_mode": processing_mode,
                        "items_analyzed": len(state.raw_scrapes),
                        "reports_generated": len(ai_reports)
                    },
                    scrape_mode=state.scrape_mode,
                    success=True
                )
            else:
                # Extract structured data from scraped content
                structured_data = await self._extract_structured_data(state.raw_scrapes)
                
                result = ScrapeResult(
                    structured_data=structured_data,
                    ai_reports=None,
                    metadata={
                        "processing_mode": processing_mode,
                        "items_extracted": len(structured_data)
                    },
                    scrape_mode=state.scrape_mode,
                    success=True
                )
            
            self.logger.info(f"Successfully processed data in {processing_mode} mode")
            
            return {
                "processed_data": result,
                "success": True,
                "error": None
            }
            
        except Exception as e:
            self.logger.error(f"Processing failed: {e}")
            
            # Return minimal result structure on error
            return {
                "processed_data": ScrapeResult(
                    structured_data=[],
                    metadata={
                        "processing_error": str(e),
                        "raw_items_count": len(state.raw_scrapes)
                    },
                    scrape_mode=state.scrape_mode,
                    success=False
                ),
                "success": False,
                "error": str(e)
            }


class ExportNode(BaseLangGraphNode):
    """
    LangGraph node for data export and storage operations.
    
    Supports multiple export formats with consistent error handling
    following CLAUDE.md pragmatism over perfection principle.
    """
    
    # Explicit contracts
    inputs = {
        "processed_data": ScrapeResult,
        "export_format": str
    }
    outputs = {
        "export_path": Optional[str],
        "success": bool,
        "error": Optional[str]
    }
    
    def __init__(self):
        """Initialize export node with storage dependencies"""
        super().__init__("export")
        # self.storage_manager = StorageManager()  # Will implement as needed
    
    async def process(self, state: UnifiedState) -> Dict[str, Any]:
        """
        Export processed data to specified format.
        
        Args:
            state: Workflow state with processed data and export configuration
            
        Returns:
            State updates with export path or error information
        """
        
        if not state.processed_data:
            return {
                "export_path": None,
                "success": False,
                "error": "No processed data available for export"
            }
        
        self.logger.info(f"Exporting data in {state.export_format} format")
        
        try:
            # Real export implementation
            from datetime import datetime
            from pathlib import Path
            import json
            import csv
            
            # Create export directory if it doesn't exist
            export_dir = Path("./exports")
            export_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_filename = f"export_{timestamp}.{state.export_format}"
            export_path = export_dir / export_filename
            
            # Export based on format
            if state.export_format.lower() == 'json':
                await self._export_json(state.processed_data, export_path)
            elif state.export_format.lower() == 'csv':
                await self._export_csv(state.processed_data, export_path)
            else:
                raise ValueError(f"Unsupported export format: {state.export_format}")
            
            self.logger.info(f"Successfully exported to: {export_path}")
            
            return {
                "export_path": str(export_path),
                "success": True,
                "error": None
            }
            
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            
            return {
                "export_path": None,
                "success": False,
                "error": str(e)
            }
    
    async def _analyze_for_ai_behavior(self, raw_scrapes: List[RawScrapeData], categories: List[str], question: str) -> List[Any]:
        """Analyze scraped content for AI behavior patterns"""
        try:
            from app.langgraph.analysis_nodes import ContentAnalysisNode
            
            analysis_node = ContentAnalysisNode()
            ai_reports = []
            
            for raw_data in raw_scrapes:
                try:
                    # Create analysis state for content processing
                    analysis_state = type('AnalysisState', (), {
                        'url': raw_data.url,
                        'question': question,
                        'categories': categories,
                        'raw_content': raw_data.text
                    })()
                    
                    analysis_result = await analysis_node.process(analysis_state)
                    
                    if analysis_result.get('ai_reports'):
                        ai_reports.extend(analysis_result['ai_reports'])
                        
                except Exception as e:
                    self.logger.warning(f"Failed to analyze content from {raw_data.url}: {e}")
                    continue
            
            return ai_reports
            
        except Exception as e:
            self.logger.error(f"AI behavior analysis failed: {e}")
            return []
    
    async def _extract_structured_data(self, raw_scrapes: List[RawScrapeData]) -> List[Dict[str, Any]]:
        """Extract structured data from raw scraped content"""
        structured_data = []
        
        for raw_data in raw_scrapes:
            try:
                # Extract meaningful structured information
                item = {
                    "url": raw_data.url,
                    "title": self._extract_title_from_text(raw_data.text),
                    "content": raw_data.text[:1000] if raw_data.text else "",
                    "full_content": raw_data.text,
                    "word_count": len(raw_data.text.split()) if raw_data.text else 0,
                    "timestamp": raw_data.timestamp.isoformat(),
                    "source": raw_data.source,
                    "metadata": raw_data.metadata
                }
                structured_data.append(item)
                
            except Exception as e:
                self.logger.warning(f"Failed to extract structured data from {raw_data.url}: {e}")
                continue
        
        return structured_data
    
    def _extract_title_from_text(self, text: str) -> str:
        """Extract a reasonable title from content text"""
        if not text:
            return "Untitled"
        
        # Take first meaningful line as title
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line and len(line) > 10 and len(line) < 200:
                return line
        
        # Fallback: first 100 characters
        return text[:100].strip() + ('...' if len(text) > 100 else '')
    
    async def _export_json(self, data: ScrapeResult, file_path: Path) -> None:
        """Export data to JSON format"""
        import json
        
        export_data = {
            "success": data.success,
            "structured_data": data.structured_data or [],
            "ai_reports": [
                {
                    "url": report.url,
                    "excerpt": report.excerpt,
                    "categories": report.categories,
                    "source": report.source,
                    "date": report.date,
                    "stance": report.stance,
                    "tone": report.tone,
                    "confidence": report.confidence
                }
                for report in (data.ai_reports or [])
            ],
            "metadata": data.metadata,
            "scrape_mode": data.scrape_mode,
            "export_timestamp": datetime.utcnow().isoformat()
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    async def _export_csv(self, data: ScrapeResult, file_path: Path) -> None:
        """Export data to CSV format"""
        import csv
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            if data.ai_reports:
                # Export AI reports as CSV
                writer = csv.writer(f)
                writer.writerow([
                    'URL', 'Excerpt', 'Categories', 
                    'Source', 'Date', 'Stance', 'Tone', 'Confidence'
                ])
                for report in data.ai_reports:
                    writer.writerow([
                        report.url,
                        report.excerpt,
                        ', '.join(report.categories),
                        report.source,
                        report.date or '',
                        report.stance or '',
                        report.tone or '',
                        report.confidence
                    ])
            elif data.structured_data:
                # Export structured data as CSV
                writer = csv.DictWriter(f, fieldnames=data.structured_data[0].keys())
                writer.writeheader()
                writer.writerows(data.structured_data)
            else:
                # No data to export
                writer = csv.writer(f)
                writer.writerow(['No data available'])