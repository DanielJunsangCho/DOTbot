#!/usr/bin/env python3
"""
Test script for the robust orchestrator system.

This script demonstrates:
1. Submitting async multi-depth scraping tasks
2. Monitoring task progress 
3. Retrieving results when complete
4. Handling timeouts and partial results
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Optional

import aiohttp


class OrchestratorTestClient:
    """Test client for the orchestrator system"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def submit_async_scrape(self, 
                                 url: str, 
                                 max_depth: int = 2,
                                 timeout_minutes: int = 30,
                                 max_concurrent_articles: int = 10) -> Optional[str]:
        """Submit an async scraping task"""
        
        if not self.session:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        
        request_data = {
            "url": url,
            "max_depth": max_depth,
            "timeout_minutes": timeout_minutes,
            "max_concurrent_articles": max_concurrent_articles,
            "export_format": "json"
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/scraping/async-scrape",
                json=request_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    task_id = data.get("task_id")
                    print(f"✅ Task submitted successfully: {task_id}")
                    print(f"   Message: {data.get('message')}")
                    print(f"   Estimated duration: {data.get('estimated_duration_minutes')} minutes")
                    return task_id
                else:
                    error_data = await response.json()
                    print(f"❌ Failed to submit task: {error_data}")
                    return None
                    
        except Exception as e:
            print(f"❌ Error submitting task: {e}")
            return None
    
    async def get_task_status(self, task_id: str) -> Optional[dict]:
        """Get task status and progress"""
        
        if not self.session:
            raise RuntimeError("Client not initialized.")
        
        try:
            async with self.session.get(
                f"{self.base_url}/scraping/tasks/{task_id}/status"
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_data = await response.json()
                    print(f"❌ Failed to get task status: {error_data}")
                    return None
                    
        except Exception as e:
            print(f"❌ Error getting task status: {e}")
            return None
    
    async def get_task_results(self, task_id: str, include_errors: bool = False) -> Optional[dict]:
        """Get complete task results"""
        
        if not self.session:
            raise RuntimeError("Client not initialized.")
        
        try:
            params = {"include_errors": include_errors} if include_errors else {}
            async with self.session.get(
                f"{self.base_url}/scraping/tasks/{task_id}/results",
                params=params
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_data = await response.json()
                    print(f"❌ Failed to get task results: {error_data}")
                    return None
                    
        except Exception as e:
            print(f"❌ Error getting task results: {e}")
            return None
    
    async def get_orchestrator_status(self) -> Optional[dict]:
        """Get orchestrator health status"""
        
        if not self.session:
            raise RuntimeError("Client not initialized.")
        
        try:
            async with self.session.get(
                f"{self.base_url}/scraping/status"
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_data = await response.json()
                    print(f"❌ Failed to get orchestrator status: {error_data}")
                    return None
                    
        except Exception as e:
            print(f"❌ Error getting orchestrator status: {e}")
            return None
    
    async def monitor_task_progress(self, task_id: str, max_wait_minutes: int = 35):
        """Monitor task progress until completion"""
        
        start_time = time.time()
        max_wait_seconds = max_wait_minutes * 60
        
        print(f"\n🔍 Monitoring task {task_id}...")
        print("=" * 60)
        
        while True:
            elapsed = time.time() - start_time
            
            if elapsed > max_wait_seconds:
                print(f"⏰ Max wait time ({max_wait_minutes} minutes) exceeded")
                break
            
            status = await self.get_task_status(task_id)
            
            if not status:
                print("❌ Failed to get task status")
                break
            
            current_status = status.get("status")
            progress = status.get("progress", 0)
            completed_items = status.get("completed_items", 0)
            failed_items = status.get("failed_items", 0)
            total_items = status.get("total_items", 0)
            
            elapsed_time = elapsed / 60  # Convert to minutes
            
            print(f"📊 Status: {current_status.upper()} | "
                  f"Progress: {progress:.1f}% | "
                  f"Items: {completed_items}/{total_items} | "
                  f"Failed: {failed_items} | "
                  f"Elapsed: {elapsed_time:.1f}m")
            
            if current_status in ["completed", "failed", "partial", "cancelled"]:
                print(f"\n✅ Task finished with status: {current_status.upper()}")
                
                # Get final results
                results = await self.get_task_results(task_id, include_errors=True)
                if results:
                    summary = results.get("summary", {})
                    print(f"📋 Results: {summary.get('results_count', 0)} items scraped")
                    print(f"🎯 Success rate: {summary.get('success_rate', 0):.1f}%")
                    
                    if results.get("errors"):
                        print(f"⚠️ Errors encountered: {len(results['errors'])}")
                        for i, error in enumerate(results["errors"][:3]):  # Show first 3 errors
                            print(f"   {i+1}. {error[:100]}...")
                        
                        if len(results["errors"]) > 3:
                            print(f"   ... and {len(results['errors']) - 3} more errors")
                
                break
            
            # Wait before next status check
            await asyncio.sleep(10)  # Check every 10 seconds
        
        return status


async def test_robust_orchestrator():
    """Main test function for the robust orchestrator system"""
    
    print("🚀 Testing Robust Orchestrator System")
    print("=" * 60)
    
    # Test URLs - using LessWrong as it has many articles
    test_urls = [
        "https://www.lesswrong.com",  # Should find 25+ articles
        # "https://example.com",       # Simple test case
    ]
    
    async with OrchestratorTestClient() as client:
        
        # Check orchestrator health first
        print("\n1️⃣ Checking orchestrator health...")
        health = await client.get_orchestrator_status()
        
        if health:
            orchestrator_status = health.get("orchestrator", {})
            print(f"   Status: {orchestrator_status.get('status', 'unknown')}")
            print(f"   Active tasks: {orchestrator_status.get('active_tasks', 0)}")
            print(f"   Available slots: {orchestrator_status.get('available_task_slots', 0)}")
        
        # Test async scraping for each URL
        for i, url in enumerate(test_urls, 1):
            print(f"\n{i+1}️⃣ Testing async scraping for: {url}")
            
            # Submit async scraping task
            task_id = await client.submit_async_scrape(
                url=url,
                max_depth=2,  # Main page + articles
                timeout_minutes=10,  # 10 minute timeout for testing
                max_concurrent_articles=5  # Moderate concurrency for testing
            )
            
            if not task_id:
                print(f"❌ Failed to submit task for {url}")
                continue
            
            # Monitor progress
            final_status = await client.monitor_task_progress(task_id, max_wait_minutes=12)
            
            if final_status:
                print(f"✅ Task {task_id} completed successfully")
            else:
                print(f"❌ Task {task_id} monitoring failed")
        
        # Final orchestrator status
        print(f"\n3️⃣ Final orchestrator health check...")
        final_health = await client.get_orchestrator_status()
        
        if final_health:
            orchestrator_status = final_health.get("orchestrator", {})
            print(f"   Status: {orchestrator_status.get('status', 'unknown')}")
            print(f"   Total tasks processed: {orchestrator_status.get('total_tasks', 0)}")
            
            error_stats = orchestrator_status.get("error_statistics", {})
            if error_stats:
                print(f"   Error statistics: {error_stats}")
            
            circuit_breaker = orchestrator_status.get("circuit_breaker", {})
            blocked_domains = circuit_breaker.get("blocked_domains", [])
            if blocked_domains:
                print(f"   Blocked domains: {blocked_domains}")
    
    print("\n🎉 Orchestrator testing completed!")


if __name__ == "__main__":
    print("Starting robust orchestrator system test...")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    try:
        asyncio.run(test_robust_orchestrator())
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()