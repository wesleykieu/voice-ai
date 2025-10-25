#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from tools.memory_tool import MemoryTools


async def test_memory_search():
    """Test the memory search functionality directly"""
    print("Testing memory search...")

    # Create a mock context
    class MockContext:
        def __init__(self):
            self.room = type("Room", (), {"name": "test_room"})()

    context = MockContext()

    # Initialize memory tools
    memory_tools = MemoryTools()

    # Test queries
    test_queries = [
        "hobbies",
        "high school graduation",
        "where did I graduate",
        "teaching career",
        "family children",
    ]

    for query in test_queries:
        print(f"\n--- Testing query: '{query}' ---")
        try:
            result = await memory_tools.search_memories(context, query)
            print(f"Result: {result}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_memory_search())
