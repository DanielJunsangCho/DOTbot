"""
Basic HTTP scraper following CLAUDE.md web scraping standards.
"""

from __future__ import annotations

from typing import List, Optional
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import logging

from .base_scraper import BaseScraper
from app.schemas import RawScrapeData

logger = logging.getLogger(__name__)


class BasicScraper(BaseScraper):
    """
    HTTP-based scraper using aiohttp and BeautifulSoup.
    
    Suitable for static websites and simple content following
    CLAUDE.md web scraping standards.
    """
    
    capabilities = ["static_html", "basic_forms", "simple_navigation"]
    
    def __init__(self, rate_limit: float = 1.0):
        """
        Initialize basic scraper with HTTP session.
        
        Args:
            rate_limit: Seconds between requests
        """
        super().__init__(rate_limit)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def scrape_url(self, url: str, max_depth: int = 1) -> List[RawScrapeData]:
        """
        Scrape URL using HTTP requests and BeautifulSoup parsing.
        
        Args:
            url: URL to scrape
            max_depth: Maximum scraping depth
            
        Returns:
            List of raw scraped data
        """
        
        if not self._should_visit_url(url):
            return []
        
        self.logger.info(f"Starting basic scrape of {url} (depth: {max_depth})")
        
        try:
            await self._ensure_session()
            
            # Apply rate limiting
            await self._apply_rate_limit()
            
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    raise ValueError(f"HTTP {response.status}: {response.reason}")
                
                html_content = await response.text()
                
                # Parse content with BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extract text content
                text_content = self._extract_text_content(soup)
                
                # Create raw scrape data
                raw_data = await self._create_raw_scrape_data(
                    url=url,
                    text=text_content,
                    html=html_content,
                    metadata={
                        "scraper": "BasicScraper",
                        "status_code": response.status,
                        "content_type": response.headers.get("content-type", "unknown"),
                        "content_length": len(html_content)
                    }
                )
                
                results = [raw_data]
                
                # Handle recursive scraping if depth allows
                if max_depth > 1:
                    child_urls = self._extract_child_urls(soup, url)
                    
                    for child_url in child_urls[:5]:  # Limit child URLs
                        try:
                            child_results = await self.scrape_url(child_url, max_depth - 1)
                            results.extend(child_results)
                        except Exception as e:
                            self.logger.warning(f"Failed to scrape child URL {child_url}: {e}")
                
                self._log_scraping_attempt(url, True)
                return results
                
        except Exception as e:
            self._log_scraping_attempt(url, False, str(e))
            return []
    
    def is_suitable_for_url(self, url: str) -> bool:
        """
        Check if basic scraper is suitable for the URL.
        
        Args:
            url: URL to evaluate
            
        Returns:
            True if this scraper can handle the URL
        """
        
        # Basic scraper works for most standard websites
        unsuitable_patterns = [
            # Heavy JavaScript applications
            "app.", "spa.", "api.",
            # Known dynamic content platforms
            "twitter.com", "facebook.com", "instagram.com"
        ]
        
        url_lower = url.lower()
        return not any(pattern in url_lower for pattern in unsuitable_patterns)
    
    async def _ensure_session(self) -> None:
        """Ensure HTTP session is available"""
        
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=3)
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                headers={
                    "User-Agent": "DOTbot/1.0 (Web Analysis Tool)",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate",
                    "Connection": "keep-alive",
                }
            )
    
    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        """
        Extract clean text content from HTML.
        
        Args:
            soup: BeautifulSoup parsed HTML
            
        Returns:
            Cleaned text content
        """
        
        # Remove script and style elements
        for element in soup(["script", "style", "nav", "header", "footer"]):
            element.decompose()
        
        # Extract text from main content areas
        main_content = soup.find("main") or soup.find("article") or soup.find("div", class_="content") or soup
        
        text = main_content.get_text(separator=" ", strip=True)
        
        # Clean up whitespace
        import re
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _extract_child_urls(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Extract child URLs for recursive scraping.
        
        Args:
            soup: BeautifulSoup parsed HTML
            base_url: Base URL for relative link resolution
            
        Returns:
            List of child URLs
        """
        
        from urllib.parse import urljoin, urlparse
        
        child_urls = []
        base_domain = urlparse(base_url).netloc
        
        # Find links within the same domain
        for link in soup.find_all("a", href=True):
            href = link["href"]
            full_url = urljoin(base_url, href)
            
            # Only include same-domain links
            if urlparse(full_url).netloc == base_domain:
                child_urls.append(full_url)
        
        return list(set(child_urls))  # Remove duplicates
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with cleanup"""
        if self.session and not self.session.closed:
            await self.session.close()