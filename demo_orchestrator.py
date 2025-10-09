#!/usr/bin/env python3
"""
Demonstration script showing the robust orchestrator system capabilities.

This demonstrates how the system now handles:
1. Long-running multi-depth scraping without timing out
2. Concurrent article processing
3. Real-time progress updates
4. Graceful timeout handling with partial results
5. Comprehensive error handling and retry mechanisms
"""

import asyncio
import json
import time
from datetime import datetime

import aiohttp


async def demonstrate_orchestrator():
    """Demonstrate the orchestrator capabilities with a quick example"""
    
    print("🚀 Robust Web Scraping Orchestrator Demonstration")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%H:%M:%S')}")
    
    async with aiohttp.ClientSession() as session:
        
        # Step 1: Submit async scraping task
        print("\n1️⃣ Submitting async scraping task...")
        
        request_data = {
            "url": "https://example.com",  # Simple test for demo
            "max_depth": 1,
            "timeout_minutes": 5,
            "max_concurrent_articles": 3,
            "export_format": "json"
        }
        
        async with session.post(
            "http://localhost:8000/scraping/async-scrape",
            json=request_data
        ) as response:
            if response.status == 200:
                data = await response.json()
                task_id = data["task_id"]
                print(f"✅ Task submitted: {task_id}")
                print(f"📝 Message: {data['message']}")
                print(f"⏱️ Estimated duration: {data['estimated_duration_minutes']} minutes")
            else:
                print(f"❌ Failed to submit task: {await response.text()}")
                return
        
        # Step 2: Monitor progress
        print(f"\n2️⃣ Monitoring task progress...")
        
        for i in range(30):  # Check for up to 30 seconds
            async with session.get(
                f"http://localhost:8000/scraping/tasks/{task_id}/status"
            ) as response:
                if response.status == 200:
                    status = await response.json()
                    
                    current_status = status["status"]
                    progress = status["progress"]
                    completed = status["completed_items"]
                    total = status["total_items"]
                    
                    print(f"📊 {current_status.upper()} | Progress: {progress:.1f}% | Items: {completed}/{total}")
                    
                    if current_status in ["completed", "failed", "partial"]:
                        print(f"✅ Task finished with status: {current_status.upper()}")
                        break
                else:
                    print(f"❌ Status check failed: {await response.text()}")
                    break
            
            await asyncio.sleep(1)
        
        # Step 3: Get results
        print(f"\n3️⃣ Retrieving task results...")
        
        async with session.get(
            f"http://localhost:8000/scraping/tasks/{task_id}/results"
        ) as response:
            if response.status == 200:
                results = await response.json()
                
                print(f"📋 Results retrieved successfully:")
                print(f"   • Status: {results['status']}")
                print(f"   • Results count: {results['summary']['results_count']}")
                print(f"   • Success rate: {results['summary']['success_rate']:.1f}%")
                print(f"   • Total items: {results['summary']['total_items']}")
                
                if results['results']:
                    first_result = results['results'][0]
                    print(f"   • Sample result URL: {first_result['url']}")
                    print(f"   • Sample text length: {len(first_result['full_text'])} chars")
                
            else:
                print(f"❌ Results retrieval failed: {await response.text()}")
        
        # Step 4: Show orchestrator health
        print(f"\n4️⃣ Orchestrator health status...")
        
        async with session.get("http://localhost:8000/scraping/status") as response:
            if response.status == 200:
                health = await response.json()
                orchestrator = health["orchestrator"]
                
                print(f"🏥 Health Status: {orchestrator['status']}")
                print(f"🔄 Active tasks: {orchestrator['active_tasks']}")
                print(f"📊 Total tasks: {orchestrator['total_tasks']}")
                print(f"🎯 Available slots: {orchestrator['available_task_slots']}")
                
                if orchestrator.get('error_statistics'):
                    print(f"⚠️ Error statistics: {orchestrator['error_statistics']}")
                
            else:
                print(f"❌ Health check failed: {await response.text()}")
    
    print(f"\n🎉 Demonstration completed at {datetime.now().strftime('%H:%M:%S')}")
    print("\n" + "=" * 60)
    print("🔥 KEY IMPROVEMENTS IMPLEMENTED:")
    print("✅ Background task processing - no more 60s timeouts!")
    print("✅ Concurrent article scraping - handles 25+ articles efficiently")
    print("✅ Real-time progress tracking - monitor scraping status")
    print("✅ Graceful timeout handling - returns partial results")
    print("✅ Comprehensive retry logic - recovers from individual failures")
    print("✅ Circuit breaker pattern - prevents overwhelming failing domains")
    print("✅ Task queuing system - manages multiple concurrent operations")
    print("✅ Health monitoring - tracks system performance and errors")


if __name__ == "__main__":
    try:
        asyncio.run(demonstrate_orchestrator())
    except KeyboardInterrupt:
        print("\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()