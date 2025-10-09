"""
Scraper factory for automatic scraper selection following CLAUDE.md standards.
"""

from __future__ import annotations

from typing import Optional, Dict, Any
import logging

from .base_scraper import BaseScraper
from .basic_scraper import BasicScraper
from .browser_scraper import BrowserScraper

logger = logging.getLogger(__name__)


class ScraperFactory:
    """
    Factory for creating appropriate scrapers based on URL and mode.
    
    Follows CLAUDE.md factory pattern with graceful fallbacks.
    """
    
    def __init__(self):
        """Initialize factory with available scrapers"""
        self._scrapers = {
            "basic": BasicScraper,
            "browser": BrowserScraper
        }
        
        logger.info("ScraperFactory initialized")
    
    def create_scraper(self, mode: str = "auto", url: str = "") -> Optional[BaseScraper]:
        """
        Create appropriate scraper based on mode and URL characteristics.
        
        Args:
            mode: Scraping mode ("basic", "browser", "auto")
            url: Target URL for analysis
            
        Returns:
            Configured scraper instance or None
        """
        
        if mode == "auto":
            # Auto-select based on URL characteristics
            if self._requires_browser_scraping(url):
                mode = "browser"
            else:
                mode = "basic"
        
        scraper_class = self._scrapers.get(mode)
        
        if not scraper_class:
            logger.error(f"Unknown scraper mode: {mode}")
            return None
        
        try:
            scraper = scraper_class()
            
            if not scraper.is_suitable_for_url(url):
                logger.warning(f"{scraper_class.__name__} not suitable for {url}, falling back")
                # Fallback to basic scraper
                return BasicScraper()
            
            logger.info(f"Created {scraper_class.__name__} for {url}")
            return scraper
            
        except Exception as e:
            logger.error(f"Failed to create scraper {mode}: {e}")
            
            # Fallback to basic scraper
            try:
                return BasicScraper()
            except Exception as fallback_error:
                logger.error(f"Fallback scraper creation failed: {fallback_error}")
                return None
    
    def get_available_scrapers(self) -> Dict[str, Any]:
        """
        Get information about available scrapers.
        
        Returns:
            Dictionary of scraper capabilities and availability
        """
        
        scrapers_info = {}
        
        for name, scraper_class in self._scrapers.items():
            try:
                # Test scraper creation
                test_scraper = scraper_class()
                scrapers_info[name] = {
                    "available": True,
                    "description": getattr(scraper_class, '__doc__', 'No description'),
                    "capabilities": getattr(test_scraper, 'capabilities', [])
                }
            except Exception as e:
                scrapers_info[name] = {
                    "available": False,
                    "error": str(e),
                    "description": "Unavailable due to missing dependencies"
                }
        
        return scrapers_info
    
    def _requires_browser_scraping(self, url: str) -> bool:
        """
        Determine if URL requires browser-based scraping.
        
        Args:
            url: URL to analyze
            
        Returns:
            True if browser scraping is recommended
        """
        
        # Simple heuristics for browser requirement
        browser_indicators = [
            "spa", "react", "angular", "vue",  # SPA frameworks
            "dynamic", "ajax", "api",          # Dynamic content
            "app.", "app-",                    # Web apps
        ]
        
        url_lower = url.lower()
        
        return any(indicator in url_lower for indicator in browser_indicators)