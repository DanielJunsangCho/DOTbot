"""
Browser-Use based web scraping service for robust content extraction.
Implements intelligent browser automation with AI-powered navigation.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import re
from urllib.parse import urljoin, urlparse

from browser_use import Agent, Browser
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from app.schemas import RawScrapeData

logger = logging.getLogger(__name__)


class BrowserScraper:
    """
    Robust browser-based scraping using browser-use AI agent.
    Implements fallback modes and intelligent content extraction.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize browser scraper with OpenAI client"""
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key) if (api_key and OPENAI_AVAILABLE) else None
        self._browser = None
        self._agent_pool = []
        
    async def run_browser_agent(self, task: str, url: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Wrapper function for browser-use agent execution.
        Implements Pattern A: Wrapping Agent for reuse with error handling.
        """
        options = options or {}
        use_cloud = options.get('use_cloud', False)
        max_retries = options.get('max_retries', 2)
        
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"Attempting browser scrape of {url} (attempt {attempt + 1}/{max_retries + 1})")
                
                # Create agent - browser-use will auto-detect API keys from environment
                agent = Agent(
                    task=f"{task}. Navigate to {url} and extract the requested information.",
                    use_vision=False  # Disable vision to avoid extra costs
                )
                
                # Execute agent
                result = await agent.run()
                
                # Extract content from agent results
                html_content = ""
                text_content = ""
                
                logger.info(f"Agent result type: {type(result)}, attributes: {list(dir(result)) if hasattr(result, '__dict__') else 'N/A'}")
                
                # Try to get content from the result - browser-use returns AgentHistoryList
                if hasattr(result, 'model_output') and result.model_output:
                    text_content = str(result.model_output)
                elif hasattr(result, 'last_output') and result.last_output:
                    text_content = str(result.last_output)
                elif hasattr(result, 'output_text') and result.output_text:
                    text_content = result.output_text
                elif isinstance(result, str):
                    text_content = result
                elif hasattr(result, '__str__'):
                    text_content = str(result)
                
                # Always try to get actual page content from browser
                try:
                    # Get the browser session from the agent
                    if hasattr(agent, 'browser_session') and agent.browser_session:
                        browser_session = agent.browser_session
                        page = None
                        
                        if hasattr(browser_session, 'get_current_page'):
                            # Await the coroutine properly
                            page = await browser_session.get_current_page()
                        
                        if page:
                            html_content = await page.content()
                            page_text = await page.evaluate("() => document.body.innerText || document.body.textContent || ''")
                            
                            # Use actual page content if it's more substantial than agent output
                            if len(page_text.strip()) > len(text_content.strip()):
                                text_content = page_text
                                
                            logger.info(f"Extracted {len(page_text)} characters of page content")
                        else:
                            logger.warning(f"No page available from browser session")
                    else:
                        logger.warning(f"No browser_session available from agent")
                        
                except Exception as e:
                    logger.warning(f"Could not extract page content from browser: {e}")
                
                # Ensure we have some content
                if not text_content.strip():
                    text_content = f"Successfully navigated to {url} but could not extract detailed content"
                
                # Clean up
                if hasattr(agent, 'cleanup'):
                    await agent.cleanup()
                
                return {
                    "success": True,
                    "html": html_content,
                    "text": text_content or f"Successfully processed {url} using browser agent",
                    "actions_log": getattr(result, 'actions', []),
                    "screenshot": None,
                    "metadata": {
                        "url": url,
                        "task": task,
                        "attempt": attempt + 1,
                        "timestamp": datetime.utcnow().isoformat(),
                        "agent_result": str(result)[:500]  # Truncated result for debugging
                    }
                }
                
            except Exception as e:
                logger.error(f"Browser agent attempt {attempt + 1} failed for {url}: {e}")
                
                if attempt == max_retries:
                    # Final attempt with AI agent failed, try basic scraping as fallback
                    logger.info(f"AI agent failed for {url}, attempting basic browser scraping as fallback")
                    try:
                        fallback_result = await self._basic_browser_scrape(url)
                        fallback_result["metadata"]["fallback_used"] = True
                        return fallback_result
                    except Exception as fallback_error:
                        logger.error(f"Fallback scraping also failed: {fallback_error}")
                        return {
                            "success": False,
                            "error": f"Both AI agent and fallback failed. AI agent: {str(e)}, Fallback: {str(fallback_error)}",
                            "metadata": {
                                "url": url,
                                "task": task,
                                "attempts": max_retries + 1,
                                "timestamp": datetime.utcnow().isoformat()
                            }
                        }
                
                # Wait before retry with exponential backoff
                await asyncio.sleep(2 ** attempt)
        
    async def _basic_browser_scrape(self, url: str) -> Dict[str, Any]:
        """
        Basic browser scraping using playwright as fallback.
        """
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()
                
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(2)  # Wait for dynamic content
                
                html = await page.content()
                text = await page.evaluate("() => document.body.innerText")
                
                await browser.close()
                
                return {
                    "success": True,
                    "html": html,
                    "text": text,
                    "actions_log": [{"action": "navigate", "url": url}],
                    "metadata": {
                        "method": "basic_playwright",
                        "url": url,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
                
        except Exception as e:
            logger.error(f"Basic browser scrape failed for {url}: {e}")
            raise
    
    async def scrape_with_depth(self, url: str, max_depth: int = 2) -> List[RawScrapeData]:
        """
        Multi-depth scraping to extract comprehensive content.
        For sites like LessWrong, this will find article links and scrape them.
        """
        logger.info(f"Starting multi-depth scrape of {url} with depth {max_depth}")
        
        all_scraped_data = []
        scraped_urls = set()
        urls_to_scrape = [(url, 0)]  # (url, depth)
        
        while urls_to_scrape and len(all_scraped_data) < 25:  # Limit to prevent infinite loops
            current_url, current_depth = urls_to_scrape.pop(0)
            
            if current_url in scraped_urls or current_depth > max_depth:
                continue
                
            scraped_urls.add(current_url)
            
            try:
                # Determine task based on depth
                if current_depth == 0:
                    task = f"""Navigate to this page and extract all content including:
1. All text content from the main page
2. Find and collect ALL article/post links (look for <a> tags with href attributes)
3. Pay special attention to pagination and 'Load More' buttons
4. For sites like LessWrong, look for post titles, article links, and content previews
5. Extract the main navigation and content areas completely"""
                else:
                    task = f"""Navigate to this article page and extract the complete content:
1. Article title
2. Full article text/content  
3. Author name and date
4. Any metadata or tags
5. All text content from the page"""
                
                # Use efficient Playwright-only approach to avoid API rate limits
                if current_depth == 0:
                    # Use Playwright to find all links and get homepage content
                    playwright_result = await self._scrape_and_extract_links_playwright(current_url)
                    
                    # Add found links to scraping queue for depth 1
                    found_links = playwright_result.get("links", [])
                    for link in found_links[:15]:  # Get up to 15 articles
                        if link not in scraped_urls:
                            urls_to_scrape.append((link, current_depth + 1))
                    
                    logger.info(f"Found {len(found_links)} article links to scrape")
                    result = playwright_result
                    
                else:
                    # For individual articles, use Playwright for content extraction
                    result = await self._basic_browser_scrape(current_url)
                
                if result["success"]:
                    # Parse scraped content
                    raw_data = RawScrapeData(
                        url=current_url,
                        text=result.get("text", ""),
                        html=result.get("html", ""),
                        source=f"playwright-depth-{current_depth}",
                        metadata={
                            **result.get("metadata", {}),
                            "depth": current_depth,
                            "scraping_method": "playwright_optimized"
                        }
                    )
                    
                    all_scraped_data.append(raw_data)
                
                # Add delay between requests to be respectful
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Failed to scrape {current_url} at depth {current_depth}: {e}")
                continue
        
        logger.info(f"Multi-depth scrape completed: {len(all_scraped_data)} pages scraped")
        return all_scraped_data
    
    async def _extract_links_with_agent(self, result: Dict[str, Any], current_url: str) -> List[str]:
        """
        Extract links using both HTML parsing and browser page access.
        """
        found_links = set()
        
        # Method 1: Extract from HTML if available
        if result.get("html"):
            found_links.update(self._extract_article_links(result["html"], current_url))
        
        # Method 2: Try to use the last used browser agent to get links directly
        try:
            # Use a new simple agent just to extract links
            link_task = f"""Navigate to {current_url} and extract all article/post links from the page. 
            Look for links that contain '/posts/', '/p/', or are article/blog links.
            Return a list of URLs."""
            
            link_agent = Agent(
                task=link_task,
                use_vision=False
            )
            
            # Run agent and extract URLs from the result
            link_result = await link_agent.run()
            
            # Try to get the browser page from this agent
            if hasattr(link_agent, 'browser_session') and link_agent.browser_session:
                browser_session = link_agent.browser_session
                page = await browser_session.get_current_page()
                
                if page:
                    # Get all links from the current page
                    links_js = """
                    Array.from(document.querySelectorAll('a[href]')).map(a => a.href)
                        .filter(href => href && (
                            href.includes('/posts/') || 
                            href.includes('/p/') || 
                            href.includes('lesswrong.com') ||
                            href.match(/\/[a-zA-Z0-9-]+$/) // Simple slug pattern
                        ))
                        .slice(0, 20)
                    """
                    page_links = await page.evaluate(links_js)
                    found_links.update([link for link in page_links if link.startswith('http')])
                    
                    logger.info(f"Extracted {len(page_links)} links via JavaScript from page")
                    
        except Exception as e:
            logger.warning(f"Could not extract links via agent: {e}")
        
        return list(found_links)
    
    async def _scrape_and_extract_links_playwright(self, url: str) -> Dict[str, Any]:
        """
        Combined method: scrape page content AND extract links using Playwright only.
        Much more efficient than using AI agents for link discovery.
        """
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = await context.new_page()
                
                # Set extra headers to avoid bot detection
                await page.set_extra_http_headers({
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate",
                    "DNT": "1",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                })
                
                # Add delay before navigation to avoid rate limits
                await asyncio.sleep(2)
                
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                    await asyncio.sleep(5)  # Longer wait for dynamic content and to avoid rate limits
                    
                    # Check if we got rate limited
                    page_text = await page.evaluate("() => document.body.innerText || document.body.textContent || ''")
                    if "Too Many Requests" in page_text or "429" in page_text:
                        logger.warning(f"Rate limited on {url}, waiting 30 seconds and retrying...")
                        await asyncio.sleep(30)  # Wait 30 seconds
                        await page.reload(wait_until="domcontentloaded", timeout=45000)
                        await asyncio.sleep(10)  # Additional wait after retry
                        
                except Exception as nav_error:
                    logger.warning(f"Navigation error for {url}: {nav_error}")
                    # Try a simple reload if navigation fails
                    await asyncio.sleep(10)
                    await page.reload(wait_until="domcontentloaded", timeout=45000)
                
                # Get page content
                html = await page.content()
                text = await page.evaluate("() => document.body.innerText || document.body.textContent || ''")
                
                # Extract links with JavaScript - comprehensive approach for sites like LessWrong
                links_js = """
                () => {
                    const links = Array.from(document.querySelectorAll('a[href]'))
                        .map(a => a.href)
                        .filter(href => {
                            if (!href || href === '#' || href.startsWith('javascript:')) return false;
                            
                            // For LessWrong specifically - match their URL patterns
                            if (href.includes('lesswrong.com')) {
                                return href.includes('/posts/') || 
                                       href.includes('/p/') || 
                                       href.match(/lesswrong\.com\/posts\/[a-zA-Z0-9]+/) ||
                                       href.match(/lesswrong\.com\/s\/[a-zA-Z0-9]+/);
                            }
                            
                            // Generic article patterns for other sites
                            return href.includes('/post/') || 
                                   href.includes('/article/') || 
                                   href.includes('/blog/') || 
                                   href.includes('/p/') ||
                                   href.match(/\/20\d{2}\//) || // Year-based URLs
                                   href.match(/\/[a-zA-Z0-9\-]{8,}\/?$/); // Long slug URLs
                        });
                    
                    // Remove duplicates and limit to reasonable number
                    return [...new Set(links)].slice(0, 25);
                }
                """
                
                found_links = await page.evaluate(links_js)
                await browser.close()
                
                logger.info(f"Playwright extracted {len(found_links)} article links and content from {url}")
                
                return {
                    "success": True,
                    "text": text,
                    "html": html,
                    "links": found_links,
                    "metadata": {
                        "method": "playwright_combined",
                        "url": url,
                        "timestamp": datetime.utcnow().isoformat(),
                        "links_found": len(found_links)
                    }
                }
                
        except Exception as e:
            logger.error(f"Playwright combined scraping failed for {url}: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "html": "",
                "links": [],
                "metadata": {
                    "method": "playwright_combined",
                    "url": url,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
    
    async def _extract_links_with_playwright(self, url: str) -> List[str]:
        """
        Use Playwright to quickly extract article links from a page.
        Much faster than using AI agents for link discovery.
        """
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()
                
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(3)  # Wait for dynamic content
                
                # Extract links with JavaScript - more comprehensive than regex
                links_js = """
                () => {
                    const links = Array.from(document.querySelectorAll('a[href]'))
                        .map(a => a.href)
                        .filter(href => {
                            if (!href || href === '#') return false;
                            
                            // For LessWrong specifically
                            if (href.includes('lesswrong.com')) {
                                return href.includes('/posts/') || href.includes('/p/') || 
                                       href.match(/lesswrong\.com\/[a-zA-Z0-9-]+$/);
                            }
                            
                            // Generic article patterns
                            return href.includes('/post/') || href.includes('/article/') || 
                                   href.includes('/blog/') || href.match(/\/[a-zA-Z0-9-]+\/?$/);
                        });
                    
                    // Remove duplicates and limit
                    return [...new Set(links)].slice(0, 25);
                }
                """
                
                found_links = await page.evaluate(links_js)
                await browser.close()
                
                logger.info(f"Playwright extracted {len(found_links)} potential article links")
                return found_links
                
        except Exception as e:
            logger.error(f"Playwright link extraction failed for {url}: {e}")
            return []
    
    def _extract_article_links(self, html: str, base_url: str) -> List[str]:
        """
        Extract article/post links from HTML content.
        Focuses on common patterns for articles on sites like LessWrong.
        """
        if not html:
            return []
        
        # Common patterns for article links
        patterns = [
            # LessWrong specific patterns
            r'href="(/posts/[^"]+)"',
            r'href="(https://www\.lesswrong\.com/posts/[^"]+)"',
            
            # General article patterns  
            r'href="(/article/[^"]+)"',
            r'href="(/blog/[^"]+)"',
            r'href="(/post/[^"]+)"',
            r'href="([^"]*/(article|blog|post|story)/[^"]*)"',
            
            # More general patterns
            r'href="(/[^"]*[0-9]{4}[^"]*)"',  # URLs with years
            r'href="(/[^"]*-[0-9]+[^"]*)"',   # URLs with numbers/IDs
        ]
        
        links = set()
        base_domain = urlparse(base_url).netloc
        
        for pattern in patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                
                # Convert relative URLs to absolute
                if match.startswith('/'):
                    full_url = urljoin(base_url, match)
                else:
                    full_url = match
                
                # Only include URLs from the same domain (avoid external links)
                if urlparse(full_url).netloc == base_domain:
                    links.add(full_url)
        
        return list(links)
    
    async def health_check(self) -> bool:
        """
        Health check by scraping a simple test page.
        Implements Pattern E: Health checks & warmups.
        """
        try:
            result = await self.run_browser_agent(
                "Navigate to this page and confirm it loads correctly",
                "https://example.com",
                {"max_retries": 1}
            )
            return result["success"]
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup browser resources"""
        if self._browser:
            await self._browser.close()
            self._browser = None