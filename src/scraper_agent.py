from typing import List, Dict, Optional
from datetime import datetime
from browser_use import BrowserUser
from .schemas import RawScrapeData

class SketchyBehaviorScraper:
    def __init__(self, max_depth: int = 2, categories: List[str] = None):
        self.browser_user = BrowserUser()
        self.max_depth = max_depth
        self.categories = categories or ["Deceptive Behaviour", "Reward Gaming", "Sycophancy"]
        self.visited_urls = set()
    
    async def scrape_url(self, url: str) -> List[RawScrapeData]:
        if url in self.visited_urls:
            return []
        
        self.visited_urls.add(url)
        raw_scrapes = []
        
        try:
            page = await self.browser_user.navigate(url)
            content = await page.content()
            
            # Extract relevant text content
            text_content = await self._extract_relevant_content(page)
            
            raw_scrapes.append(
                RawScrapeData(
                    url=url,
                    text=text_content,
                    source=self._determine_source(url),
                    timestamp=datetime.utcnow()
                )
            )
            
            if len(self.visited_urls) < self.max_depth:
                # Find and follow relevant links
                new_urls = await self._find_relevant_links(page)
                for new_url in new_urls:
                    sub_scrapes = await self.scrape_url(new_url)
                    raw_scrapes.extend(sub_scrapes)
            
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
        
        return raw_scrapes
    
    async def _extract_relevant_content(self, page) -> str:
        # Extract main content using Browser-Use's built-in methods
        content = await page.locator("article, .post-content, .entry-content").inner_text()
        return content
    
    async def _find_relevant_links(self, page) -> List[str]:
        # Find links that likely contain relevant content
        links = await page.locator("a[href]").get_attribute("href")
        return [link for link in links if self._is_relevant_link(link)]
    
    def _determine_source(self, url: str) -> str:
        if "lesswrong.com" in url:
            return "LessWrong"
        elif "alignmentforum.org" in url:
            return "Alignment Forum"
        elif "aisafety.com" in url:
            return "AI Safety"
        elif "reddit.com" in url:
            return "Reddit"
        return "Other"
    
    def _is_relevant_link(self, url: str) -> bool:
        relevant_domains = [
            "lesswrong.com",
            "alignmentforum.org", 
            "aisafety.com",
            "reddit.com/r/ControlProblem"
        ]
        return any(domain in url for domain in relevant_domains)