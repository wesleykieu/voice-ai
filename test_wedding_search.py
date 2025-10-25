#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from tools.memory_tool import MemoryTools
from livekit.agents import RunContext

class MockContext:
    def __init__(self):
        self.room = MockRoom()

class MockRoom:
    def __init__(self):
        self.name = "default_user"

async def test_wedding_search():
    """Test searching for wedding information"""
    print("Testing wedding search functionality...")
    
    # Create memory tools
    memory_tools = MemoryTools()
    
    # Create mock context
    context = MockContext()
    
    # Test different wedding-related queries
    queries = [
        "when did I get married",
        "wedding day",
        "marriage",
        "Robert and I married",
        "June 12, 1955",
        "wedding dress",
        "St. Mary's Church"
    ]
    
    for query in queries:
        print(f"\nSearching for: '{query}'")
        try:
            result = await memory_tools.search_memories(context, query)
            print(f"Result: {result}")
        except Exception as e:
            print(f"Error: {e}")
    
    # Test getting memory summary
    print(f"\nGetting memory summary...")
    try:
        summary = await memory_tools.get_memory_summary(context)
        print(f"Summary: {summary}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_wedding_search())
