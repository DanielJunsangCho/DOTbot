"""
Storage service implementing business logic following CLAUDE.md standards.
"""

from __future__ import annotations

from typing import Optional
import logging
from pathlib import Path
from datetime import datetime

from app.schemas import ScrapeResult

logger = logging.getLogger(__name__)


class StorageService:
    """
    Business logic service for storage operations.
    """
    
    def __init__(self):
        """Initialize storage service with export directory"""
        self.export_dir = Path("./exports")
        self.export_dir.mkdir(exist_ok=True)
        logger.info("StorageService initialized")
    
    async def store_result(
        self, 
        result: Optional[ScrapeResult], 
        export_format: str = "csv"
    ) -> Optional[str]:
        """
        Store scraping results in specified format.
        
        Args:
            result: Scrape result to store
            export_format: Storage format (csv, json, db)
            
        Returns:
            Path to stored file or None if failed
        """
        
        if not result:
            logger.warning("No result provided for storage")
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scrape_result_{timestamp}.{export_format}"
        file_path = self.export_dir / filename
        
        try:
            if export_format == "json":
                await self._store_as_json(result, file_path)
            elif export_format == "csv":
                await self._store_as_csv(result, file_path)
            else:
                logger.warning(f"Unsupported export format: {export_format}")
                return None
            
            logger.info(f"Successfully stored result to: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to store result: {e}")
            return None
    
    async def get_export_path(self, export_id: str) -> Optional[Path]:
        """
        Get path to exported file by ID.
        
        Args:
            export_id: Export file identifier
            
        Returns:
            Path to export file or None if not found
        """
        
        # For simplicity, treat export_id as filename
        file_path = self.export_dir / export_id
        
        if file_path.exists():
            return file_path
        
        # Try common extensions if no extension provided
        for ext in ['.csv', '.json']:
            extended_path = self.export_dir / f"{export_id}{ext}"
            if extended_path.exists():
                return extended_path
        
        logger.warning(f"Export file not found: {export_id}")
        return None
    
    async def _store_as_json(self, result: ScrapeResult, file_path: Path) -> None:
        """Store result as JSON file"""
        
        import json
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(result.dict(), f, indent=2, default=str)
    
    async def _store_as_csv(self, result: ScrapeResult, file_path: Path) -> None:
        """Store result as CSV file"""
        
        import csv
        
        data_to_write = []
        
        if result.ai_reports:
            # AI behavior analysis mode
            for report in result.ai_reports:
                data_to_write.append({
                    "url": report.url,
                    "excerpt": report.excerpt,
                    "categories": "|".join(report.categories),
                    "severity": report.severity,
                    "source": report.source,
                    "stance": report.stance or "",
                    "tone": report.tone or "",
                    "confidence": report.confidence
                })
        else:
            # General scraping mode
            data_to_write = result.structured_data
        
        if data_to_write:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = data_to_write[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data_to_write)