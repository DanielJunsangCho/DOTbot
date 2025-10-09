"""
Task orchestrator service for handling long-running multi-depth web scraping operations.

This service implements:
- Background task processing with async/concurrent execution
- Task status tracking and progress updates 
- Retry mechanisms for failed operations
- Graceful timeout handling with partial results
- Task queuing and orchestration
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from uuid import uuid4, UUID
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import json
import time
from collections import defaultdict

from app.schemas import ScrapeRequest, WorkflowOutput, RawScrapeData
from app.services.browser_scraper import BrowserScraper

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"  
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"  # Completed with some failures
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    """Types of tasks supported by orchestrator"""
    MULTI_DEPTH_SCRAPE = "multi_depth_scrape"
    BATCH_SCRAPE = "batch_scrape"
    AI_BEHAVIOR_ANALYSIS = "ai_behavior_analysis"


class TaskResult:
    """Container for task execution results"""
    
    def __init__(self, 
                 task_id: str, 
                 status: TaskStatus = TaskStatus.PENDING,
                 progress: float = 0.0,
                 total_items: int = 0,
                 completed_items: int = 0,
                 failed_items: int = 0,
                 results: Optional[List[Dict[str, Any]]] = None,
                 errors: Optional[List[str]] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        self.task_id = task_id
        self.status = status
        self.progress = progress
        self.total_items = total_items
        self.completed_items = completed_items
        self.failed_items = failed_items
        self.results = results or []
        self.errors = errors or []
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.completed_at: Optional[datetime] = None
        
    def update_progress(self, completed: int, failed: int = 0):
        """Update task progress"""
        self.completed_items = completed
        self.failed_items = failed
        self.progress = (completed + failed) / max(self.total_items, 1) * 100
        self.updated_at = datetime.utcnow()
        
        if self.completed_items + self.failed_items >= self.total_items:
            self.completed_at = datetime.utcnow()
            if self.failed_items == 0:
                self.status = TaskStatus.COMPLETED
            elif self.completed_items > 0:
                self.status = TaskStatus.PARTIAL
            else:
                self.status = TaskStatus.FAILED
    
    def add_result(self, result: Dict[str, Any]):
        """Add a successful result"""
        self.results.append(result)
        
    def add_error(self, error: str):
        """Add an error message"""
        self.errors.append(error)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "progress": round(self.progress, 2),
            "total_items": self.total_items,
            "completed_items": self.completed_items,
            "failed_items": self.failed_items,
            "results_count": len(self.results),
            "errors_count": len(self.errors),
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": (
                (self.completed_at or datetime.utcnow()) - self.created_at
            ).total_seconds()
        }


class CircuitBreaker:
    """Circuit breaker for failing URL domains to prevent excessive retries"""
    
    def __init__(self, failure_threshold: int = 5, timeout_seconds: int = 300):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.failures = defaultdict(int)
        self.last_failure_time = defaultdict(float)
        self.blocked_domains = set()
    
    def record_failure(self, url: str):
        """Record a failure for the domain"""
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        self.failures[domain] += 1
        self.last_failure_time[domain] = time.time()
        
        if self.failures[domain] >= self.failure_threshold:
            self.blocked_domains.add(domain)
            logger.warning(f"Circuit breaker: Domain {domain} blocked after {self.failures[domain]} failures")
    
    def is_blocked(self, url: str) -> bool:
        """Check if domain is blocked"""
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        
        if domain not in self.blocked_domains:
            return False
        
        # Check if timeout has passed
        last_failure = self.last_failure_time.get(domain, 0)
        if time.time() - last_failure > self.timeout_seconds:
            # Reset circuit breaker for this domain
            self.blocked_domains.discard(domain)
            self.failures[domain] = 0
            logger.info(f"Circuit breaker: Domain {domain} reset after timeout")
            return False
        
        return True
    
    def record_success(self, url: str):
        """Record a success for the domain"""
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        if domain in self.failures:
            # Reduce failure count on success
            self.failures[domain] = max(0, self.failures[domain] - 1)
            if self.failures[domain] == 0 and domain in self.blocked_domains:
                self.blocked_domains.discard(domain)
                logger.info(f"Circuit breaker: Domain {domain} unblocked after success")


class TaskOrchestrator:
    """
    Orchestrates long-running scraping tasks with concurrent execution,
    status tracking, and robust error handling.
    """
    
    def __init__(self, max_concurrent_tasks: int = 5, max_concurrent_articles: int = 10):
        """
        Initialize task orchestrator.
        
        Args:
            max_concurrent_tasks: Maximum number of tasks to run concurrently
            max_concurrent_articles: Maximum articles to scrape in parallel per task
        """
        self.max_concurrent_tasks = max_concurrent_tasks
        self.max_concurrent_articles = max_concurrent_articles
        self.tasks: Dict[str, TaskResult] = {}
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.browser_scraper = BrowserScraper()
        self.task_semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.article_semaphore = asyncio.Semaphore(max_concurrent_articles)
        self.circuit_breaker = CircuitBreaker()
        self.error_stats = defaultdict(int)  # Track error types for monitoring
        
        logger.info(f"TaskOrchestrator initialized with max_concurrent_tasks={max_concurrent_tasks}, "
                   f"max_concurrent_articles={max_concurrent_articles}")
    
    async def submit_multi_depth_scrape(self, request: ScrapeRequest, timeout_minutes: int = 30) -> str:
        """
        Submit a multi-depth scraping task for background execution.
        
        Args:
            request: Scraping request configuration
            timeout_minutes: Maximum execution time before returning partial results
            
        Returns:
            Task ID for tracking progress
        """
        task_id = str(uuid4())
        
        # Initialize task result
        task_result = TaskResult(
            task_id=task_id,
            status=TaskStatus.PENDING,
            metadata={
                "task_type": TaskType.MULTI_DEPTH_SCRAPE.value,
                "url": request.url,
                "max_depth": request.max_depth,
                "timeout_minutes": timeout_minutes,
                "request_params": request.model_dump()
            }
        )
        
        self.tasks[task_id] = task_result
        
        # Create and start background task with timeout
        async_task = asyncio.create_task(
            self._execute_multi_depth_scrape(task_id, request, timeout_minutes)
        )
        self.active_tasks[task_id] = async_task
        
        logger.info(f"Submitted multi-depth scrape task {task_id} for {request.url} "
                   f"with {timeout_minutes}min timeout")
        logger.info(f"DEBUG: Task orchestrator received question='{request.question}' (type: {type(request.question)})")
        return task_id
    
    async def _execute_multi_depth_scrape(self, task_id: str, request: ScrapeRequest, timeout_minutes: int = 30):
        """
        Execute multi-depth scraping with concurrent article processing and timeout handling.
        
        Args:
            task_id: Task identifier
            request: Scraping request
            timeout_minutes: Maximum execution time before returning partial results
        """
        task_result = self.tasks[task_id]
        start_time = datetime.utcnow()
        timeout_delta = timedelta(minutes=timeout_minutes)
        
        async with self.task_semaphore:
            try:
                task_result.status = TaskStatus.RUNNING
                logger.info(f"Starting execution of task {task_id} with {timeout_minutes}min timeout")
                
                # Phase 1: Discover article links (with timeout check)
                logger.info(f"Phase 1: Discovering article links from {request.url}")
                
                try:
                    main_page_result = await asyncio.wait_for(
                        self.browser_scraper._scrape_and_extract_links_playwright(request.url),
                        timeout=300  # 5 minutes for main page
                    )
                except asyncio.TimeoutError:
                    raise RuntimeError("Main page scraping timed out after 5 minutes")
                
                if not main_page_result["success"]:
                    raise RuntimeError(f"Failed to scrape main page: {main_page_result.get('error', 'Unknown error')}")
                
                found_links = main_page_result.get("links", [])
                logger.info(f"Found {len(found_links)} article links to scrape")
                
                # Update task with total items to process (main page + articles)
                task_result.total_items = len(found_links) + 1  # +1 for main page
                
                # Add main page content as first result
                main_page_data = {
                    "url": request.url,
                    "text": main_page_result.get("text", "")[:2000],
                    "full_text": main_page_result.get("text", ""),
                    "source": "main_page",
                    "timestamp": datetime.utcnow().isoformat(),
                    "depth": 0,
                    "word_count": len(main_page_result.get("text", "").split()),
                    "char_count": len(main_page_result.get("text", ""))
                }
                
                task_result.add_result(main_page_data)
                task_result.update_progress(completed=1)
                
                # Phase 2: Concurrently scrape articles with timeout and retry logic
                if found_links and request.max_depth > 1:
                    logger.info(f"Phase 2: Scraping {len(found_links)} articles concurrently")
                    
                    # Create article scraping tasks with timeout protection
                    article_tasks = []
                    completed_count = 1  # Start with 1 for main page
                    failed_count = 0
                    
                    # Process articles in batches to manage memory and timeout
                    batch_size = min(self.max_concurrent_articles, 10)
                    
                    for i in range(0, len(found_links), batch_size):
                        # Check overall timeout before each batch
                        elapsed_time = datetime.utcnow() - start_time
                        if elapsed_time >= timeout_delta:
                            logger.warning(f"Task {task_id} timeout reached, stopping with partial results")
                            break
                        
                        batch_links = found_links[i:i + batch_size]
                        batch_tasks = []
                        
                        for link in batch_links:
                            # Calculate remaining time for this batch
                            remaining_time = timeout_delta - elapsed_time
                            if remaining_time.total_seconds() < 60:  # Less than 1 minute left
                                logger.warning(f"Task {task_id} timeout approaching, skipping remaining articles")
                                break
                            
                            article_task = asyncio.create_task(
                                self._scrape_article_with_timeout(
                                    task_id, 
                                    link, 
                                    depth=1, 
                                    retry_count=3,
                                    timeout_seconds=min(180, int(remaining_time.total_seconds() // len(batch_links)))
                                )
                            )
                            batch_tasks.append(article_task)
                        
                        if batch_tasks:
                            try:
                                # Wait for batch with timeout
                                remaining_seconds = max(30, (timeout_delta - elapsed_time).total_seconds())
                                results = await asyncio.wait_for(
                                    asyncio.gather(*batch_tasks, return_exceptions=True),
                                    timeout=remaining_seconds
                                )
                                
                                # Process batch results
                                for result in results:
                                    if isinstance(result, Exception):
                                        error_msg = f"Article scraping failed: {str(result)}"
                                        task_result.add_error(error_msg)
                                        failed_count += 1
                                    elif result:
                                        task_result.add_result(result)
                                        completed_count += 1
                                    else:
                                        failed_count += 1
                                    
                                    # Update progress after each result
                                    task_result.update_progress(
                                        completed=completed_count,
                                        failed=failed_count
                                    )
                                    
                            except asyncio.TimeoutError:
                                logger.warning(f"Task {task_id} batch timeout, cancelling remaining tasks")
                                # Cancel remaining tasks in batch
                                for task in batch_tasks:
                                    if not task.done():
                                        task.cancel()
                                        failed_count += 1
                                
                                # Update progress with failed tasks
                                task_result.update_progress(completed=completed_count, failed=failed_count)
                                break
                
                # Final status update with timeout consideration
                task_result.completed_at = datetime.utcnow()
                elapsed_time = task_result.completed_at - start_time
                
                # Determine final status
                if len(task_result.results) == 0:
                    task_result.status = TaskStatus.FAILED
                elif elapsed_time >= timeout_delta:
                    task_result.status = TaskStatus.PARTIAL
                    task_result.add_error(f"Task timed out after {timeout_minutes} minutes, returning partial results")
                elif len(task_result.errors) > 0:
                    task_result.status = TaskStatus.PARTIAL
                else:
                    task_result.status = TaskStatus.COMPLETED
                
                # Phase 3: Process scraped content for AI behavior analysis
                logger.info(f"DEBUG: request.question='{request.question}', results_count={len(task_result.results)}")
                if request.question and len(task_result.results) > 0:
                    logger.info(f"Phase 3: Analyzing {len(task_result.results)} items for AI behavior patterns")
                    logger.info(f"DEBUG: Categories={request.categories}, Question={request.question}")
                    try:
                        ai_reports = await self._analyze_scraped_content_for_ai_behavior(
                            task_result.results, 
                            request.categories or [], 
                            request.question
                        )
                        
                        # Store AI reports in metadata for frontend access
                        task_result.metadata["ai_reports"] = ai_reports
                        task_result.metadata["ai_reports_count"] = len(ai_reports)
                        
                        logger.info(f"Generated {len(ai_reports)} AI behavior reports")
                        logger.info(f"DEBUG: AI reports stored in metadata: {len(ai_reports)} reports")
                    except Exception as e:
                        logger.error(f"AI behavior analysis failed: {e}")
                        logger.error(f"DEBUG: AI analysis exception details: {type(e).__name__}: {str(e)}")
                        task_result.add_error(f"AI behavior analysis failed: {str(e)}")
                else:
                    logger.info(f"DEBUG: Skipping AI analysis - question='{request.question}', results={len(task_result.results)}")

                logger.info(f"Task {task_id} finished: {len(task_result.results)} results, "
                           f"{len(task_result.errors)} errors, "
                           f"duration: {elapsed_time.total_seconds():.1f}s")
                
            except Exception as e:
                logger.error(f"Task {task_id} failed with error: {e}")
                task_result.status = TaskStatus.FAILED
                task_result.add_error(f"Task execution failed: {str(e)}")
                task_result.completed_at = datetime.utcnow()
            
            finally:
                # Cleanup active task reference
                if task_id in self.active_tasks:
                    del self.active_tasks[task_id]
    
    async def _scrape_article_with_retry(self, 
                                        task_id: str, 
                                        url: str, 
                                        depth: int,
                                        retry_count: int = 3) -> Optional[Dict[str, Any]]:
        """
        Scrape individual article with retry logic.
        
        Args:
            task_id: Parent task ID for logging
            url: Article URL to scrape
            depth: Scraping depth
            retry_count: Number of retries on failure
            
        Returns:
            Structured article data or None if failed
        """
        async with self.article_semaphore:
            for attempt in range(retry_count + 1):
                try:
                    logger.debug(f"Task {task_id}: Scraping article {url} (attempt {attempt + 1})")
                    
                    # Use basic browser scraping for individual articles
                    result = await self.browser_scraper._basic_browser_scrape(url)
                    
                    if result["success"]:
                        return {
                            "url": url,
                            "text": result.get("text", "")[:2000],
                            "full_text": result.get("text", ""),
                            "source": f"article-depth-{depth}",
                            "timestamp": datetime.utcnow().isoformat(),
                            "depth": depth,
                            "word_count": len(result.get("text", "").split()),
                            "char_count": len(result.get("text", "")),
                            "retry_attempt": attempt + 1
                        }
                    else:
                        raise RuntimeError(f"Browser scraping failed: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    logger.warning(f"Task {task_id}: Article scrape attempt {attempt + 1} failed for {url}: {e}")
                    
                    if attempt < retry_count:
                        # Exponential backoff
                        wait_time = min(2 ** attempt, 10)
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"Task {task_id}: Failed to scrape article {url} after {retry_count + 1} attempts")
                        return None
        
        return None
    
    async def _scrape_article_with_timeout(self, 
                                          task_id: str, 
                                          url: str, 
                                          depth: int,
                                          retry_count: int = 3,
                                          timeout_seconds: int = 180) -> Optional[Dict[str, Any]]:
        """
        Scrape individual article with retry logic, timeout protection, and circuit breaker.
        
        Args:
            task_id: Parent task ID for logging
            url: Article URL to scrape
            depth: Scraping depth
            retry_count: Number of retries on failure
            timeout_seconds: Maximum time per article
            
        Returns:
            Structured article data or None if failed
        """
        
        # Check circuit breaker before attempting
        if self.circuit_breaker.is_blocked(url):
            logger.warning(f"Task {task_id}: Skipping {url} - domain blocked by circuit breaker")
            self.error_stats["circuit_breaker_blocked"] += 1
            return None
        
        async with self.article_semaphore:
            last_error = None
            
            for attempt in range(retry_count + 1):
                try:
                    logger.debug(f"Task {task_id}: Scraping article {url} "
                                f"(attempt {attempt + 1}/{retry_count + 1}, timeout: {timeout_seconds}s)")
                    
                    # Use timeout for individual article scraping
                    result = await asyncio.wait_for(
                        self.browser_scraper._basic_browser_scrape(url),
                        timeout=timeout_seconds
                    )
                    
                    if result["success"]:
                        # Record success in circuit breaker
                        self.circuit_breaker.record_success(url)
                        
                        article_data = {
                            "url": url,
                            "text": result.get("text", "")[:2000],
                            "full_text": result.get("text", ""),
                            "source": f"article-depth-{depth}",
                            "timestamp": datetime.utcnow().isoformat(),
                            "depth": depth,
                            "word_count": len(result.get("text", "").split()),
                            "char_count": len(result.get("text", "")),
                            "retry_attempt": attempt + 1,
                            "scrape_duration": timeout_seconds,
                            "error_recovery": attempt > 0  # Flag if we recovered from errors
                        }
                        
                        logger.debug(f"Task {task_id}: Successfully scraped {url} on attempt {attempt + 1}")
                        return article_data
                    else:
                        error_msg = result.get('error', 'Unknown scraping error')
                        raise RuntimeError(f"Browser scraping failed: {error_msg}")
                        
                except asyncio.TimeoutError as e:
                    last_error = e
                    self.error_stats["timeout_errors"] += 1
                    logger.warning(f"Task {task_id}: Article scrape timeout on attempt {attempt + 1} for {url}")
                    
                    if attempt < retry_count:
                        # Reduce timeout for retries to fail faster
                        timeout_seconds = max(60, timeout_seconds // 2)
                        await asyncio.sleep(1)  # Brief pause before retry
                    else:
                        logger.error(f"Task {task_id}: Article {url} timed out after {retry_count + 1} attempts")
                        self.circuit_breaker.record_failure(url)
                        
                except asyncio.CancelledError:
                    # Task was cancelled - don't retry
                    logger.info(f"Task {task_id}: Article scraping cancelled for {url}")
                    self.error_stats["cancelled_tasks"] += 1
                    return None
                    
                except ConnectionError as e:
                    last_error = e
                    self.error_stats["connection_errors"] += 1
                    logger.warning(f"Task {task_id}: Connection error on attempt {attempt + 1} for {url}: {e}")
                    
                    if attempt < retry_count:
                        # Longer wait for connection errors
                        wait_time = min(5 + 2 * attempt, 15)
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"Task {task_id}: Connection failed for {url} after {retry_count + 1} attempts")
                        self.circuit_breaker.record_failure(url)
                        
                except Exception as e:
                    last_error = e
                    self.error_stats["general_errors"] += 1
                    error_type = type(e).__name__
                    logger.warning(f"Task {task_id}: {error_type} on attempt {attempt + 1} for {url}: {e}")
                    
                    if attempt < retry_count:
                        # Exponential backoff but limited by timeout constraints
                        wait_time = min(2 ** attempt, 5)
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"Task {task_id}: Failed to scrape article {url} after {retry_count + 1} attempts: {e}")
                        self.circuit_breaker.record_failure(url)
            
            # All attempts failed - record the last error details
            if last_error:
                logger.error(f"Task {task_id}: Final failure for {url}: {type(last_error).__name__}: {last_error}")
            
            return None
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current status of a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task status dictionary or None if not found
        """
        task_result = self.tasks.get(task_id)
        if not task_result:
            return None
        
        return task_result.to_dict()
    
    async def get_task_results(self, task_id: str, 
                              include_errors: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get complete results for a task.
        
        Args:
            task_id: Task identifier
            include_errors: Whether to include error details
            
        Returns:
            Complete task results or None if not found
        """
        task_result = self.tasks.get(task_id)
        if not task_result:
            return None
        
        response = {
            "task_id": task_id,
            "status": task_result.status.value,
            "results": task_result.results,
            "metadata": task_result.metadata,
            "summary": {
                "task_id": task_id,
                "total_items": task_result.total_items,
                "completed_items": task_result.completed_items,
                "failed_items": task_result.failed_items,
                "success_rate": (
                    task_result.completed_items / max(task_result.total_items, 1) * 100
                ),
                "duration_seconds": (
                    (task_result.completed_at or datetime.utcnow()) - task_result.created_at
                ).total_seconds()
            }
        }
        
        if include_errors:
            response["errors"] = task_result.errors
            
        return response
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if cancelled successfully, False otherwise
        """
        if task_id not in self.tasks:
            return False
        
        task_result = self.tasks[task_id]
        
        # Cancel running asyncio task
        if task_id in self.active_tasks:
            active_task = self.active_tasks[task_id]
            active_task.cancel()
            del self.active_tasks[task_id]
        
        task_result.status = TaskStatus.CANCELLED
        task_result.completed_at = datetime.utcnow()
        
        logger.info(f"Task {task_id} cancelled")
        return True
    
    async def _analyze_scraped_content_for_ai_behavior(
        self, 
        scraped_data: List[Dict[str, Any]], 
        categories: List[str], 
        question: str
    ) -> List[Dict[str, Any]]:
        """Analyze scraped content for AI behavior patterns using the scraping service logic"""
        
        # Use the same analysis logic from scraping service
        from app.services.scraping_service import ScrapingService
        scraping_service = ScrapingService()
        
        ai_reports = []
        
        try:
            for i, data_item in enumerate(scraped_data):
                content = data_item.get('full_text', data_item.get('text', ''))
                url = data_item.get('url', 'unknown')
                
                logger.debug(f"DEBUG: Analyzing item {i}: url={url}, content_length={len(content)}")
                logger.debug(f"DEBUG: Content preview: {content[:200]}...")
                
                # Skip if content is too short or contains error messages
                if len(content) < 50 or "Too Many Requests" in content or "Error:" in content:
                    logger.debug(f"DEBUG: Skipping item {i} - too short or error content")
                    continue
                
                # Analyze each piece of content for AI behavior patterns
                reports_for_item = 0
                for category in categories:
                    logger.debug(f"DEBUG: Testing category '{category}' against content")
                    if scraping_service._detect_behavior_in_content(content, category, question):
                        logger.debug(f"DEBUG: MATCH found for category '{category}'!")
                        report = {
                            "url": url,
                            "excerpt": scraping_service._extract_relevant_excerpt(content, category),
                            "categories": [category],
                            "source": data_item.get('source', f"Analysis of {url}"),
                            "confidence": 0.75,  # Default confidence
                            "stance": "concerning",
                            "tone": "analytical",
                            "date": data_item.get('timestamp', datetime.utcnow().isoformat())
                        }
                        ai_reports.append(report)
                        reports_for_item += 1
                    else:
                        logger.debug(f"DEBUG: No match for category '{category}'")
                
                logger.debug(f"DEBUG: Item {i} generated {reports_for_item} reports")
            
            logger.info(f"Generated {len(ai_reports)} AI behavior reports from {len(scraped_data)} items")
            return ai_reports
            
        except Exception as e:
            logger.error(f"AI behavior content analysis failed: {e}")
            return []
    
    async def cleanup_completed_tasks(self, max_age_hours: int = 24):
        """
        Clean up completed tasks older than specified age.
        
        Args:
            max_age_hours: Maximum age in hours before cleanup
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        tasks_to_remove = []
        for task_id, task_result in self.tasks.items():
            if (task_result.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED, TaskStatus.PARTIAL] 
                and task_result.completed_at 
                and task_result.completed_at < cutoff_time):
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
            logger.debug(f"Cleaned up old task {task_id}")
        
        if tasks_to_remove:
            logger.info(f"Cleaned up {len(tasks_to_remove)} completed tasks")
    
    async def get_all_tasks(self, 
                           status_filter: Optional[TaskStatus] = None,
                           limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all tasks with optional status filtering.
        
        Args:
            status_filter: Filter tasks by status
            limit: Maximum number of tasks to return
            
        Returns:
            List of task status dictionaries
        """
        tasks = []
        
        for task_result in self.tasks.values():
            if status_filter is None or task_result.status == status_filter:
                tasks.append(task_result.to_dict())
        
        # Sort by creation time (newest first) and limit
        tasks.sort(key=lambda t: t["created_at"], reverse=True)
        return tasks[:limit]
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Get orchestrator health status with comprehensive diagnostics.
        
        Returns:
            Health status information including error stats and circuit breaker status
        """
        active_count = len(self.active_tasks)
        total_tasks = len(self.tasks)
        
        # Calculate task status distribution
        status_distribution = defaultdict(int)
        for task_result in self.tasks.values():
            status_distribution[task_result.status.value] += 1
        
        # Get circuit breaker status
        circuit_breaker_status = {
            "blocked_domains": list(self.circuit_breaker.blocked_domains),
            "domain_failure_counts": dict(self.circuit_breaker.failures),
            "total_blocked_domains": len(self.circuit_breaker.blocked_domains)
        }
        
        # Determine overall health status
        error_rate = sum(self.error_stats.values()) / max(total_tasks, 1)
        health_status = "healthy"
        
        if error_rate > 0.5:  # More than 50% error rate
            health_status = "degraded"
        elif len(self.circuit_breaker.blocked_domains) > 5:  # Too many blocked domains
            health_status = "degraded"
        elif active_count >= self.max_concurrent_tasks:  # At capacity
            health_status = "at_capacity"
        
        return {
            "status": health_status,
            "active_tasks": active_count,
            "total_tasks": total_tasks,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "max_concurrent_articles": self.max_concurrent_articles,
            "available_task_slots": self.max_concurrent_tasks - active_count,
            "task_status_distribution": dict(status_distribution),
            "error_statistics": dict(self.error_stats),
            "error_rate": round(error_rate, 3),
            "circuit_breaker": circuit_breaker_status,
            "timestamp": datetime.utcnow().isoformat()
        }


# Global orchestrator instance
_orchestrator: Optional[TaskOrchestrator] = None


def get_task_orchestrator() -> TaskOrchestrator:
    """Get global task orchestrator instance (singleton pattern)"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = TaskOrchestrator()
    return _orchestrator