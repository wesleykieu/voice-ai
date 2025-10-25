"""
Twilio Phone Call Tool for LiveKit Agents
"""

import os
import logging
from typing import Dict, Optional
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from livekit.agents import function_tool, RunContext

logger = logging.getLogger("twilio_tool")


class TwilioTool:
    """Tool for making phone calls using Twilio"""

    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_PHONE_NUMBER")

        if not all([self.account_sid, self.auth_token, self.from_number]):
            logger.warning(
                "Twilio credentials not found. Phone calls will not be available."
            )
            self.client = None
        else:
            self.client = Client(self.account_sid, self.auth_token)
            logger.info("Twilio client initialized successfully")

        # Contact database - you can expand this
        self.contacts = {
            "wesley": "14085135506",  # Maggie's son
            "susan": "+1234567891",  # Maggie's daughter
            "michael": "+1234567892",  # Maggie's son
            "patricia": "+1234567893",  # Maggie's daughter
            "doctor": "+1234567895",  # Family doctor
            "nurse": "+1234567896",  # Home health nurse
        }

        # Family members that require consent
        self.family_members = {"wesley", "susan", "michael", "patricia"}

    def add_contact(self, name: str, phone_number: str):
        """Add a new contact to the database"""
        self.contacts[name.lower()] = phone_number
        logger.info(f"Added contact: {name} -> {phone_number}")

    def get_contact_number(self, name: str) -> Optional[str]:
        """Get phone number for a contact"""
        return self.contacts.get(name.lower())

    @function_tool
    async def make_phone_call(
        self, context: RunContext, contact_name: str, message: str = ""
    ):
        """Make a phone call to a contact.

        Args:
            contact_name: Name of the person to call (e.g., "wesley", "susan", "doctor")
            message: Optional message to say when they answer
        """
        if not self.client:
            return "I'm sorry, I can't make phone calls right now. The phone service isn't set up."

        if not contact_name or contact_name.strip() == "":
            return "Who would you like me to call?"

        contact_name = contact_name.strip().lower()

        # Get the phone number
        phone_number = self.get_contact_number(contact_name)
        if not phone_number:
            return f"I don't have {contact_name}'s phone number. Would you like to give it to me?"

        # Check if this is a family member that requires consent
        if contact_name in self.family_members:
            # Request consent before calling family
            return f"Before I call {contact_name.title()}, I want to make sure you really want to talk to them right now. Is it okay if I call {contact_name.title()}?"

        try:
            # Create the call
            call = self.client.calls.create(
                to=phone_number,
                from_=self.from_number,
                twiml=self._generate_twiml(message),
                status_callback=f"https://your-webhook-url.com/call-status",  # Optional
                status_callback_event=["initiated", "answered", "completed"],
            )

            logger.info(
                f"Call initiated to {contact_name} ({phone_number}): {call.sid}"
            )
            return f"I'm calling {contact_name.title()} now. The call is connecting..."

        except Exception as e:
            logger.error(f"Error making call to {contact_name}: {e}")
            return f"I'm sorry, I couldn't call {contact_name}. There was a problem with the phone service."

    @function_tool
    async def add_phone_contact(
        self, context: RunContext, name: str, phone_number: str
    ):
        """Add a new contact to the phone book.

        Args:
            name: Name of the person
            phone_number: Their phone number (include country code, e.g., +1234567890)
        """
        if not name or not phone_number:
            return "I need both a name and phone number to add a contact."

        # Basic phone number validation
        if not phone_number.startswith("+"):
            return "Please include the country code (e.g., +1234567890)."

        try:
            self.add_contact(name.strip(), phone_number.strip())
            return f"I've added {name} to your contacts with the number {phone_number}."
        except Exception as e:
            logger.error(f"Error adding contact {name}: {e}")
            return f"I'm sorry, I couldn't add {name} to your contacts."

    @function_tool
    async def list_contacts(self, context: RunContext):
        """List all available contacts."""
        if not self.contacts:
            return "You don't have any contacts saved yet."

        contact_list = []
        for name, number in self.contacts.items():
            # Mask the phone number for privacy
            masked_number = f"{number[:3]}***{number[-4:]}"
            contact_list.append(f"{name.title()}: {masked_number}")

        return f"Here are your contacts: {', '.join(contact_list)}"

    @function_tool
    async def confirm_call_consent(
        self,
        context: RunContext,
        contact_name: str,
        consent_given: bool,
        message: str = "",
    ):
        """Confirm consent to call a family member.

        Args:
            contact_name: Name of the person to call
            consent_given: Whether consent is given (true/false)
            message: Optional message to say when they answer
        """
        if not self.client:
            return "I'm sorry, I can't make phone calls right now. The phone service isn't set up."

        contact_name = contact_name.strip().lower()

        if not consent_given:
            return f"Okay, I won't call {contact_name.title()} right now. Just let me know if you change your mind."

        # Get the phone number
        phone_number = self.get_contact_number(contact_name)
        if not phone_number:
            return f"I don't have {contact_name}'s phone number. Would you like to give it to me?"

        try:
            # Create the call
            call = self.client.calls.create(
                to=phone_number,
                from_=self.from_number,
                twiml=self._generate_twiml(message),
                status_callback=f"https://your-webhook-url.com/call-status",  # Optional
                status_callback_event=["initiated", "answered", "completed"],
            )

            logger.info(
                f"Call initiated to {contact_name} ({phone_number}): {call.sid}"
            )
            return f"Perfect! I'm calling {contact_name.title()} now. The call is connecting..."

        except Exception as e:
            logger.error(f"Error making call to {contact_name}: {e}")
            return f"I'm sorry, I couldn't call {contact_name}. There was a problem with the phone service."

    def _generate_twiml(self, message: str = "") -> str:
        """Generate TwiML for the phone call"""
        response = VoiceResponse()

        if message:
            response.say(f"Hello, this is Heather calling for Maggie. {message}")
        else:
            response.say(
                "Hello, this is Heather calling for Maggie. She would like to speak with you."
            )

        # You can add more TwiML here, like:
        # - Play hold music
        # - Record the conversation
        # - Transfer to another number
        # - etc.

        return str(response)

    def get_available_contacts(self) -> list:
        """Get list of available contact names"""
        return list(self.contacts.keys())
