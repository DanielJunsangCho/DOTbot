"""
Abstract base scraper following CLAUDE.md web scraping standards.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Set, Optional
import asyncio
import logging
from datetime import datetime

from app.schemas import RawScrapeData
from core.config import config

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """
    Abstract base class for web scrapers following CLAUDE.md standards.
    
    Implements rate limiting, user agent rotation, and error handling
    as specified in CLAUDE.md web scraping standards.
    """
    
    def __init__(self, rate_limit: float = 1.0):
        """
        Initialize base scraper with rate limiting.
        
        Args:
            rate_limit: Seconds between requests (default 1.0 as per CLAUDE.md)
        """
        self.rate_limit = rate_limit
        self.visited_urls: Set[str] = set()
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        
        self.logger.info(f"Initialized {self.__class__.__name__} with {rate_limit}s rate limit")
    
    @abstractmethod
    async def scrape_url(self, url: str, max_depth: int = 1) -> List[RawScrapeData]:
        """
        Core scraping method to be implemented by subclasses.
        
        Args:
            url: URL to scrape
            max_depth: Maximum scraping depth
            
        Returns:
            List of raw scraped data
            
        Raises:
            NotImplementedError: Must be implemented by concrete classes
        """
        raise NotImplementedError("Subclasses must implement scrape_url method")
    
    @abstractmethod
    def is_suitable_for_url(self, url: str) -> bool:
        """
        Check if this scraper is suitable for the given URL.
        
        Args:
            url: URL to evaluate
            
        Returns:
            True if this scraper can handle the URL
            
        Raises:
            NotImplementedError: Must be implemented by concrete classes
        """
        raise NotImplementedError("Subclasses must implement is_suitable_for_url method")
    
    async def _apply_rate_limit(self) -> None:
        """Apply rate limiting between requests as per CLAUDE.md standards"""
        if self.rate_limit > 0:
            await asyncio.sleep(self.rate_limit)
    
    def _should_visit_url(self, url: str) -> bool:
        """
        Check if URL should be visited (not already processed).
        
        Args:
            url: URL to check
            
        Returns:
            True if URL should be visited
        """
        if url in self.visited_urls:
            return False
        
        self.visited_urls.add(url)
        return True
    
    def _determine_source(self, url: str) -> str:
        """
        Determine content source from URL following CLAUDE.md source mapping.
        
        Args:
            url: Source URL
            
        Returns:
            Source identifier based on domain mapping
        """
        
        for domain, source_name in config.SOURCE_DOMAINS.items():
            if domain in url.lower():
                return source_name
        
        # Default source extraction from domain
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.replace('www.', '').split('.')[0].title()
        except Exception:
            return "Unknown"
    
    async def _create_raw_scrape_data(
        self, 
        url: str, 
        text: str, 
        html: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> RawScrapeData:
        """
        Create standardized RawScrapeData object.
        
        Args:
            url: Source URL
            text: Extracted text content
            html: Raw HTML content (optional)
            metadata: Additional metadata (optional)
            
        Returns:
            Validated RawScrapeData object
        """
        
        return RawScrapeData(
            url=url,
            text=text.strip(),
            html=html,
            source=self._determine_source(url),
            timestamp=datetime.utcnow(),
            metadata=metadata or {}
        )
    
    def _log_scraping_attempt(self, url: str, success: bool, error: Optional[str] = None) -> None:
        """
        Log scraping attempts and errors as per CLAUDE.md requirements.
        
        Args:
            url: URL that was scraped
            success: Whether scraping was successful
            error: Error message if failed
        """
        
        if success:
            self.logger.info(f"Successfully scraped: {url}")
        else:
            self.logger.error(f"Failed to scrape {url}: {error or 'Unknown error'}")
    
    def get_scraper_info(self) -> dict:
        """
        Get scraper information for factory registration.
        
        Returns:
            Scraper metadata and capabilities
        """
        
        return {
            "name": self.__class__.__name__,
            "rate_limit": self.rate_limit,
            "visited_count": len(self.visited_urls),
            "capabilities": getattr(self, 'capabilities', [])
        }