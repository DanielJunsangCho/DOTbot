"""
Browser automation scraper following CLAUDE.md web scraping standards.
"""

from __future__ import annotations

from typing import List, Optional
import asyncio
import logging

from .base_scraper import BaseScraper
from app.schemas import RawScrapeData

logger = logging.getLogger(__name__)


class BrowserScraper(BaseScraper):
    """
    Browser automation scraper with fallback support.
    
    Handles JavaScript-heavy sites and dynamic content following
    CLAUDE.md graceful degradation principles.
    """
    
    capabilities = ["dynamic_content", "javascript", "spa_applications", "complex_navigation"]
    
    def __init__(self, rate_limit: float = 2.0):
        """
        Initialize browser scraper with enhanced rate limiting.
        
        Args:
            rate_limit: Seconds between requests (higher for browser automation)
        """
        super().__init__(rate_limit)
        self.browser_available = False
        self._check_browser_availability()
    
    async def scrape_url(self, url: str, max_depth: int = 1) -> List[RawScrapeData]:
        """
        Scrape URL using browser automation with fallback.
        
        Args:
            url: URL to scrape
            max_depth: Maximum scraping depth
            
        Returns:
            List of raw scraped data
        """
        
        if not self._should_visit_url(url):
            return []
        
        self.logger.info(f"Starting browser scrape of {url} (depth: {max_depth})")
        
        try:
            # Apply enhanced rate limiting for browser automation
            await self._apply_rate_limit()
            
            if self.browser_available:
                return await self._scrape_with_browser(url, max_depth)
            else:
                # Fallback to basic scraping
                self.logger.warning("Browser automation unavailable, falling back to basic scraping")
                return await self._scrape_with_fallback(url, max_depth)
                
        except Exception as e:
            self._log_scraping_attempt(url, False, str(e))
            return []
    
    def is_suitable_for_url(self, url: str) -> bool:
        """
        Check if browser scraper is suitable for the URL.
        
        Args:
            url: URL to evaluate
            
        Returns:
            True if browser automation is recommended
        """
        
        # Browser scraper is suitable for dynamic content
        dynamic_indicators = [
            "app.", "spa.", "react", "angular", "vue",
            "ajax", "api", "dynamic"
        ]
        
        url_lower = url.lower()
        return any(indicator in url_lower for indicator in dynamic_indicators)
    
    def _check_browser_availability(self) -> None:
        """Check if browser automation dependencies are available"""
        
        try:
            # Check for actual browser automation dependencies
            from playwright.async_api import async_playwright
            import browser_use
            self.browser_available = True
            self.logger.info("Browser automation available (Playwright + browser-use)")
            
        except ImportError as e:
            self.browser_available = False
            self.logger.warning(f"Browser automation unavailable: {e}")
    
    async def _scrape_with_browser(self, url: str, max_depth: int) -> List[RawScrapeData]:
        """
        Scrape using real browser automation with browser-use and Playwright.
        
        Args:
            url: URL to scrape
            max_depth: Maximum scraping depth
            
        Returns:
            List of scraped data
        """
        
        # Use the real browser scraper service
        from app.services.browser_scraper import BrowserScraper as RealBrowserScraper
        import os
        
        browser_scraper = RealBrowserScraper(api_key=os.getenv("OPENAI_API_KEY"))
        
        try:
            # Execute multi-depth scraping
            scraped_data = await browser_scraper.scrape_with_depth(url, max_depth)
            
            # Convert to expected format
            results = []
            for data_item in scraped_data:
                raw_data = await self._create_raw_scrape_data(
                    url=data_item.url,
                    text=data_item.text,
                    html=data_item.html,
                    metadata={
                        **data_item.metadata,
                        "scraper": "BrowserScraper",
                        "browser_automation": True
                    }
                )
                results.append(raw_data)
            
            self._log_scraping_attempt(url, True)
            return results
            
        except Exception as e:
            self.logger.error(f"Real browser scraping failed: {e}")
            # Fall back to basic scraping
            return await self._scrape_with_fallback(url, max_depth)
    
    async def _scrape_with_fallback(self, url: str, max_depth: int) -> List[RawScrapeData]:
        """
        Fallback scraping when browser automation is unavailable.
        
        Args:
            url: URL to scrape
            max_depth: Maximum scraping depth
            
        Returns:
            List of scraped data
        """
        
        # Import and use basic scraper as fallback
        from .basic_scraper import BasicScraper
        
        fallback_scraper = BasicScraper(rate_limit=self.rate_limit)
        
        try:
            async with fallback_scraper:
                results = await fallback_scraper.scrape_url(url, max_depth)
                
                # Add metadata indicating fallback was used
                for result in results:
                    result.metadata.update({
                        "fallback_mode": True,
                        "intended_scraper": "BrowserScraper",
                        "actual_scraper": "BasicScraper"
                    })
                
                return results
                
        except Exception as e:
            self.logger.error(f"Fallback scraping failed: {e}")
            return []