"""
Workflow service implementing business logic following CLAUDE.md standards.
"""

from __future__ import annotations

from typing import Dict, Any, Optional
import logging
import asyncio
from datetime import datetime
import uuid
import json
import csv
from pathlib import Path

from app.schemas import WorkflowInput, WorkflowOutput, ScrapeRequest, ScrapeResult, AIBehaviorReport

logger = logging.getLogger(__name__)


class WorkflowService:
    """
    Business logic service for workflow orchestration.
    """
    
    def __init__(self):
        """Initialize workflow service with state management"""
        self._active_workflows: Dict[str, Dict[str, Any]] = {}
        self.export_dir = Path("./exports")
        self.export_dir.mkdir(exist_ok=True)
        logger.info("WorkflowService initialized")
    
    async def execute_unified_workflow(self, workflow_input: WorkflowInput) -> WorkflowOutput:
        """
        Execute the unified DOTbot workflow.
        
        Args:
            workflow_input: Workflow configuration
            
        Returns:
            Workflow execution results
        """
        
        workflow_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        logger.info(f"Executing unified workflow {workflow_id} for URL: {workflow_input.url}")
        
        self._active_workflows[workflow_id] = {
            "status": "running",
            "start_time": start_time,
            "current_step": "initialization",
            "url": workflow_input.url
        }
        
        try:
            # Simulate workflow execution with steps
            await self._update_workflow_status(workflow_id, "scraping", "Scraping website content")
            await asyncio.sleep(1)  # Simulate processing time
            
            await self._update_workflow_status(workflow_id, "processing", "Processing scraped content")
            await asyncio.sleep(1)
            
            await self._update_workflow_status(workflow_id, "analysis", "Analyzing for AI behavior patterns")
            await asyncio.sleep(1)
            
            await self._update_workflow_status(workflow_id, "export", "Exporting results")
            await asyncio.sleep(0.5)
            
            # Execute actual scraping with real browser service
            from app.services.scraping_service import ScrapingService
            from app.schemas import ScrapeRequest
            
            scraping_service = ScrapingService()
            
            # Convert export format to proper enum value
            from app.schemas.scrape_schemas import ExportFormat
            export_format = workflow_input.export_format.lower()
            if export_format == "csv":
                export_enum = ExportFormat.CSV
            elif export_format == "json":
                export_enum = ExportFormat.JSON
            else:
                export_enum = ExportFormat.CSV  # Default fallback
            
            scrape_request = ScrapeRequest(
                url=workflow_input.url,
                question=workflow_input.question,
                max_depth=workflow_input.max_depth,
                categories=workflow_input.categories,
                export_format=export_enum
            )
            
            if workflow_input.question:
                # AI behavior analysis mode
                scrape_result = await scraping_service.execute_ai_behavior_analysis(scrape_request)
                result = scrape_result.result
            else:
                # General scraping mode
                scrape_result = await scraping_service.execute_scrape(scrape_request)
                result = scrape_result.result
            
            # Create actual export file
            export_filename = f"workflow_{workflow_id}.{workflow_input.export_format}"
            await self._create_export_file(result, export_filename, workflow_input.export_format)
            
            self._active_workflows[workflow_id]["status"] = "completed"
            self._active_workflows[workflow_id]["completed_time"] = datetime.utcnow()
            
            logger.info(f"Workflow {workflow_id} completed successfully")
            
            return WorkflowOutput(
                success=True,
                result=result,
                export_path=f"/exports/{export_filename}",
                metadata={
                    "workflow_id": workflow_id,
                    "processing_time": (datetime.utcnow() - start_time).total_seconds(),
                    "steps_completed": ["scraping", "processing", "analysis", "export"]
                }
            )
            
        except Exception as e:
            logger.error(f"Workflow {workflow_id} failed: {e}")
            
            self._active_workflows[workflow_id]["status"] = "failed"
            self._active_workflows[workflow_id]["error"] = str(e)
            
            return WorkflowOutput(
                success=False,
                error=str(e),
                metadata={
                    "workflow_id": workflow_id,
                    "processing_time": (datetime.utcnow() - start_time).total_seconds(),
                    "failed_at": self._active_workflows[workflow_id].get("current_step", "unknown")
                }
            )
    
    async def execute_ai_behavior_workflow(self, workflow_input: WorkflowInput) -> WorkflowOutput:
        """
        Execute specialized AI behavior analysis workflow.
        
        Args:
            workflow_input: Analysis configuration
            
        Returns:
            AI behavior analysis results
        """
        
        logger.info(f"Executing AI behavior workflow for URL: {workflow_input.url}")
        
        # Enhanced workflow for AI behavior analysis
        enhanced_input = WorkflowInput(
            url=workflow_input.url,
            question=workflow_input.question or "Analyze for concerning AI behaviors",
            max_depth=max(workflow_input.max_depth, 2),  # Deeper analysis
            categories=workflow_input.categories or [
                "Deceptive Behaviour", "Reward Gaming", "Sycophancy", 
                "Goal Misgeneralization", "Unauthorized Access"
            ],
            export_format=workflow_input.export_format
        )
        
        return await self.execute_unified_workflow(enhanced_input)
    
    async def execute_general_scrape_workflow(self, workflow_input: WorkflowInput) -> WorkflowOutput:
        """
        Execute general purpose scraping workflow.
        
        Args:
            workflow_input: Scraping configuration
            
        Returns:
            General scraping results
        """
        
        logger.info(f"Executing general scrape workflow for URL: {workflow_input.url}")
        
        # Standard workflow for general data extraction
        return await self.execute_unified_workflow(workflow_input)
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a running workflow.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Workflow status or None if not found
        """
        
        return self._active_workflows.get(workflow_id)
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """
        Cancel a running workflow.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            True if cancelled, False if not found
        """
        
        if workflow_id in self._active_workflows:
            self._active_workflows[workflow_id]["status"] = "cancelled"
            self._active_workflows[workflow_id]["cancelled_time"] = datetime.utcnow()
            logger.info(f"Workflow {workflow_id} cancelled")
            return True
        
        return False
    
    async def get_available_workflows(self) -> Dict[str, Any]:
        """
        Get information about available workflow types.
        
        Returns:
            Available workflow types and capabilities
        """
        
        return {
            "unified": {
                "description": "Complete scraping and analysis workflow",
                "capabilities": ["web_scraping", "content_processing", "ai_behavior_analysis", "data_export"],
                "supported_formats": ["csv", "json", "db"]
            },
            "ai_behavior": {
                "description": "Specialized AI behavior analysis",
                "capabilities": ["deep_content_analysis", "behavior_categorization"],
                "categories": [
                    "Deceptive Behaviour", "Reward Gaming", "Sycophancy", 
                    "Goal Misgeneralization", "Unauthorized Access"
                ]
            },
            "general_scrape": {
                "description": "General purpose data extraction",
                "capabilities": ["structured_data_extraction", "content_cleaning", "format_conversion"],
                "supported_sites": ["static_html", "dynamic_content", "tables", "lists"]
            }
        }
    
    async def schedule_cleanup(self, export_path: str) -> None:
        """
        Schedule cleanup of temporary files.
        
        Args:
            export_path: Path to file for cleanup
        """
        
        # Schedule actual cleanup of temporary files
        logger.info(f"Scheduled cleanup for: {export_path}")
        
        # Schedule file cleanup after 1 hour (3600 seconds)
        async def cleanup_file():
            await asyncio.sleep(3600)  # Wait 1 hour
            try:
                file_path = Path(export_path)
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Cleaned up export file: {export_path}")
            except Exception as e:
                logger.error(f"Failed to cleanup {export_path}: {e}")
        
        # Start cleanup task in background
        asyncio.create_task(cleanup_file())
    
    async def _update_workflow_status(
        self, 
        workflow_id: str, 
        step: str, 
        description: str
    ) -> None:
        """Update workflow status for monitoring"""
        
        if workflow_id in self._active_workflows:
            self._active_workflows[workflow_id].update({
                "current_step": step,
                "step_description": description,
                "last_update": datetime.utcnow()
            })
            
            logger.info(f"Workflow {workflow_id}: {step} - {description}")
    
    async def _analyze_content_for_ai_behavior(self, scraped_data: List[Any], categories: List[str], question: str) -> List[AIBehaviorReport]:
        """Analyze scraped content for AI behavior patterns"""
        
        from app.langgraph.analysis_nodes import ContentAnalysisNode
        from app.schemas import UnifiedState
        
        analysis_node = ContentAnalysisNode()
        ai_reports = []
        
        for data_item in scraped_data:
            try:
                # Create analysis state from scraped data
                state = UnifiedState(
                    url=data_item.get('url', ''),
                    question=question,
                    categories=categories,
                    raw_content=data_item.get('full_text', data_item.get('text', ''))
                )
                
                # Run content analysis
                analysis_result = await analysis_node.process(state)
                
                if analysis_result.get('ai_reports'):
                    ai_reports.extend(analysis_result['ai_reports'])
                    
            except Exception as e:
                logger.warning(f"Failed to analyze content item: {e}")
                continue
        
        return ai_reports
    
    async def _process_general_scraping_data(self, scraped_data: List[Any]) -> List[Dict[str, Any]]:
        """Process scraped data into structured format for general use"""
        
        structured_data = []
        
        for item in scraped_data:
            try:
                # Extract meaningful structured data from raw scraped content
                structured_item = {
                    "url": item.get('url', ''),
                    "title": self._extract_title_from_content(item.get('text', '')),
                    "content": item.get('text', '')[:2000],  # Truncate for display
                    "full_content": item.get('text', ''),
                    "word_count": len(item.get('text', '').split()),
                    "timestamp": item.get('timestamp', datetime.utcnow().isoformat()),
                    "source": item.get('source', 'scraper'),
                    "depth": item.get('depth', 0)
                }
                structured_data.append(structured_item)
                
            except Exception as e:
                logger.warning(f"Failed to process scraped item: {e}")
                continue
        
        return structured_data
    
    def _extract_title_from_content(self, text: str) -> str:
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
    
    async def _create_export_file(self, result: ScrapeResult, filename: str, format: str) -> None:
        """Create actual export file with workflow results"""
        
        file_path = self.export_dir / filename
        
        try:
            if format.lower() == 'json':
                # Export as JSON
                export_data = {
                    "success": result.success,
                    "structured_data": result.structured_data,
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
                        for report in (result.ai_reports or [])
                    ],
                    "metadata": result.metadata,
                    "scrape_mode": result.scrape_mode,
                    "export_timestamp": datetime.utcnow().isoformat()
                }
                
                with open(file_path, 'w') as f:
                    json.dump(export_data, f, indent=2)
                    
            elif format.lower() == 'csv':
                # Export AI reports as CSV
                if result.ai_reports:
                    with open(file_path, 'w', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([
                            'URL', 'Excerpt', 'Categories', 
                            'Source', 'Date', 'Stance', 'Tone', 'Confidence'
                        ])
                        for report in result.ai_reports:
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
                else:
                    # Export structured data as CSV
                    with open(file_path, 'w', newline='') as f:
                        if result.structured_data:
                            writer = csv.DictWriter(f, fieldnames=result.structured_data[0].keys())
                            writer.writeheader()
                            writer.writerows(result.structured_data)
                        else:
                            writer = csv.writer(f)
                            writer.writerow(['No data available'])
            
            logger.info(f"Export file created: {file_path}")
                            
        except Exception as e:
            logger.error(f"Failed to create export file {filename}: {e}")
            # Create a simple fallback file
            with open(file_path, 'w') as f:
                f.write(f"Export failed: {str(e)}\nGenerated at: {datetime.utcnow().isoformat()}")