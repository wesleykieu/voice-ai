#!/usr/bin/env python3
"""
Test script to verify email includes conversation context
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add src to path so we can import our tools
sys.path.append('src')

from tools.emergency_tool import EmergencyTool

async def test_email_context():
    """Test that email includes conversation context"""
    print("Testing Email with Conversation Context...")
    print("=" * 45)
    
    load_dotenv('.env.local')
    emergency_tool = EmergencyTool()
    
    # Simulate emergency call
    print("1. Emergency call made...")
    await emergency_tool.emergency_call(None, "general", "I need help")
    
    # Simulate conversation
    print("2. Storing conversation...")
    emergency_tool.store_emergency_conversation("Maggie", "I fell down and can't get up")
    emergency_tool.store_emergency_conversation("Heather", "Are you hurt anywhere?")
    emergency_tool.store_emergency_conversation("Maggie", "My leg hurts and I can't move")
    emergency_tool.store_emergency_conversation("Heather", "Where are you right now?")
    emergency_tool.store_emergency_conversation("Maggie", "I'm in the living room")
    
    print("3. Sending email with conversation context...")
    result = await emergency_tool.send_emergency_email_now(None)
    print(f"Result: {result}")
    
    print("\n4. Check your email at wesleykieu13@gmail.com")
    print("   The email should now include the full conversation log!")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_email_context())
