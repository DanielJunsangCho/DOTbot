#!/usr/bin/env python3
"""
DOTbot Main Entry Point

Provides both CLI and programmatic access to DOTbot functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from api.cli import main as cli_main
from api.main import create_dotbot_instance

async def example_usage():
    """Example of programmatic usage"""
    
    print("DOTbot Example Usage")
    print("=" * 30)
    
    try:
        # Create DOTbot instance
        dotbot = create_dotbot_instance()
        
        # Example 1: General web scraping
        print("\n1. General Web Scraping Example:")
        print("Scraping a sample website...")
        
        scrape_result = await dotbot.extract_structured_data(
            url="https://httpbin.org/json",  # Simple JSON endpoint for testing
            export_format="json"
        )
        
        print(f"Result: {'Success' if scrape_result.get('success') else 'Failed'}")
        if scrape_result.get("export_path"):
            print(f"Exported to: {scrape_result['export_path']}")
        
        # Show session info
        session_info = dotbot.get_session_info()
        print(f"\nSession Info:")
        print(f"  Session ID: {session_info['session_id']}")
        print(f"  Total operations: {session_info['total_operations']}")
        print(f"  Success rate: {session_info['success_rate']:.2%}")
        
        # Show available scrapers
        print(f"\nAvailable Scrapers:")
        for scraper_name, info in session_info['available_scrapers'].items():
            status = "✓" if info["available"] else "✗"
            print(f"  {status} {scraper_name}")
        
    except Exception as e:
        print(f"Error in example usage: {e}")

def main():
    """Main entry point - decides between CLI and example usage"""
    
    if len(sys.argv) > 1:
        # CLI mode - arguments provided
        return asyncio.run(cli_main())
    else:
        # Interactive example mode
        print("DOTbot - Unified Web Scraping and AI Behavior Analysis Tool")
        print("=" * 60)
        print()
        print("Usage options:")
        print("1. Command line interface:")
        print("   python main.py scrape <url> [options]")
        print("   python main.py analyze <url> <question> [options]")
        print("   python main.py batch --urls <url1> <url2> ... [options]")
        print("   python main.py info")
        print()
        print("2. Running example (current mode):")
        
        try:
            return asyncio.run(example_usage())
        except KeyboardInterrupt:
            print("\nExample cancelled by user")
            return 0
        except Exception as e:
            print(f"Example failed: {e}")
            return 1

if __name__ == "__main__":
    sys.exit(main())