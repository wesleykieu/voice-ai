#!/usr/bin/env python3
"""
Test script for Twilio functionality
"""

import os
import asyncio
from dotenv import load_dotenv
from src.tools.twilio_tool import TwilioTool

load_dotenv(".env.local")


async def test_twilio():
    """Test Twilio tool functionality"""
    print("🧪 Testing Twilio Tool...")

    # Initialize the tool
    twilio_tool = TwilioTool()

    # Check if Twilio is configured
    if not twilio_tool.client:
        print("❌ Twilio not configured. Please add these to .env.local:")
        print("   TWILIO_ACCOUNT_SID=your_account_sid")
        print("   TWILIO_AUTH_TOKEN=your_auth_token")
        print("   TWILIO_PHONE_NUMBER=+1234567890")
        return

    print("✅ Twilio client initialized")

    # Test listing contacts
    print("\n📞 Testing list_contacts...")
    contacts = await twilio_tool.list_contacts(None)
    print(f"Contacts: {contacts}")

    # Test adding a contact
    print("\n➕ Testing add_phone_contact...")
    result = await twilio_tool.add_phone_contact(None, "Test Contact", "+15551234567")
    print(f"Add contact result: {result}")

    # Test listing contacts again
    print("\n📞 Testing list_contacts after adding...")
    contacts = await twilio_tool.list_contacts(None)
    print(f"Contacts: {contacts}")

    # Test making a call (this will actually make a call!)
    print("\n📞 Testing make_phone_call...")
    print("⚠️  This will make a real phone call to Mary!")

    response = input("Do you want to make a test call? (y/N): ")
    if response.lower() == "y":
        result = await twilio_tool.make_phone_call(
            None, "mary", "This is a test call from Heather."
        )
        print(f"Call result: {result}")
    else:
        print("Skipping actual phone call test.")

    print("\n✅ Twilio tool test completed!")


if __name__ == "__main__":
    asyncio.run(test_twilio())
