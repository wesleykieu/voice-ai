import asyncio
import logging
import os
from typing import Dict, List
from livekit.agents import function_tool, RunContext
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse

logger = logging.getLogger("emergency_tool")


class EmergencyTool:
    """Tool for handling emergency situations and calling for help"""
    
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_PHONE_NUMBER")
        
        if not all([self.account_sid, self.auth_token, self.from_number]):
            logger.warning("Twilio credentials not found. Emergency calls will not be available.")
            self.client = None
        else:
            self.client = Client(self.account_sid, self.auth_token)
            logger.info("Emergency tool initialized with Twilio")
        
        # Emergency contacts in order of priority
        self.emergency_contacts = {
            "primary": "14085135506",      # Wesley (Maggie's son)
            "secondary": "+1234567891",    # Susan (Maggie's daughter)
            "doctor": "+1234567895",       # Family doctor
            "emergency": "911",            # Emergency services
        }
        
        # Emergency phrases that trigger the tool
        self.emergency_phrases = [
            "help", "help me", "emergency", "urgent", "call for help",
            "i need help", "something's wrong", "i'm hurt", "i fell",
            "i can't get up", "i'm scared", "call someone", "call 911"
        ]
        
        # Track emergency calls to avoid spam
        self.last_emergency_call = 0
        self.emergency_cooldown = 300  # 5 minutes between emergency calls
    
    def is_emergency_phrase(self, text: str) -> bool:
        """Check if the text contains emergency phrases"""
        if not text:
            return False
        
        text_lower = text.lower().strip()
        return any(phrase in text_lower for phrase in self.emergency_phrases)
    
    @function_tool
    async def emergency_call(self, context: RunContext, emergency_type: str = "general", message: str = ""):
        """Call for emergency help when Maggie needs assistance.
        
        Args:
            emergency_type: Type of emergency (general, medical, fall, urgent)
            message: Additional message about the emergency
        """
        if not self.client:
            return "I'm sorry, I can't make emergency calls right now. Please call 911 directly or ask someone nearby for help."
        
        # Check cooldown to prevent spam
        import time
        current_time = time.time()
        if current_time - self.last_emergency_call < self.emergency_cooldown:
            return "I just called for help. Someone should be on their way. If this is a new emergency, please call 911 directly."
        
        try:
            # Determine which number to call based on emergency type
            if emergency_type.lower() in ["medical", "fall", "urgent"]:
                phone_number = self.emergency_contacts["primary"]  # Call Wesley first
                contact_name = "Wesley (your son)"
            else:
                phone_number = self.emergency_contacts["primary"]  # Default to Wesley
                contact_name = "Wesley (your son)"
            
            # Create emergency message
            emergency_message = f"EMERGENCY: Maggie needs help immediately. {message}".strip()
            if not emergency_message.endswith("."):
                emergency_message += "."
            
            # Make the call
            call = self.client.calls.create(
                to=phone_number,
                from_=self.from_number,
                twiml=self._generate_emergency_twiml(emergency_message),
                status_callback=f"https://your-webhook-url.com/emergency-status",
                status_callback_event=['initiated', 'answered', 'completed']
            )
            
            # Update last call time
            self.last_emergency_call = current_time
            
            logger.critical(f"EMERGENCY CALL MADE: {contact_name} at {phone_number} - {emergency_message}")
            
            return f"🚨 EMERGENCY: I'm calling {contact_name} right now! Help is on the way. Stay calm, someone will be there soon."
            
        except Exception as e:
            logger.error(f"Error making emergency call: {e}")
            return f"I tried to call for help but couldn't reach anyone. Please call 911 directly or ask someone nearby for help immediately."
    
    @function_tool
    async def call_911(self, context: RunContext, emergency_description: str = ""):
        """Call 911 emergency services directly.
        
        Args:
            emergency_description: Description of the emergency
        """
        if not self.client:
            return "I can't make calls right now. Please call 911 directly on your phone immediately."
        
        try:
            # Call 911
            emergency_message = f"Emergency call for Maggie. {emergency_description}".strip()
            
            call = self.client.calls.create(
                to="911",
                from_=self.from_number,
                twiml=self._generate_911_twiml(emergency_message),
                status_callback=f"https://your-webhook-url.com/911-status",
                status_callback_event=['initiated', 'answered', 'completed']
            )
            
            logger.critical(f"911 CALL MADE: {emergency_message}")
            
            return "🚨 I'm calling 911 right now! Emergency services are being contacted. Stay calm and help will arrive soon."
            
        except Exception as e:
            logger.error(f"Error calling 911: {e}")
            return "I couldn't call 911. Please call 911 directly on your phone immediately!"
    
    @function_tool
    async def add_emergency_contact(self, context: RunContext, name: str, phone_number: str, priority: str = "secondary"):
        """Add a new emergency contact.
        
        Args:
            name: Name of the emergency contact
            phone_number: Their phone number
            priority: Priority level (primary, secondary, doctor)
        """
        if not name or not phone_number:
            return "I need both a name and phone number to add an emergency contact."
        
        # Validate priority
        valid_priorities = ["primary", "secondary", "doctor"]
        if priority.lower() not in valid_priorities:
            return f"Priority must be one of: {', '.join(valid_priorities)}"
        
        # Add the contact
        self.emergency_contacts[priority.lower()] = phone_number
        
        logger.info(f"Added emergency contact: {name} ({priority}) - {phone_number}")
        
        return f"✅ Added {name} as a {priority} emergency contact. They'll be called if you need help."
    
    @function_tool
    async def list_emergency_contacts(self, context: RunContext):
        """List all emergency contacts."""
        if not self.emergency_contacts:
            return "No emergency contacts set up yet."
        
        contact_list = []
        for priority, number in self.emergency_contacts.items():
            masked_number = f"{number[:3]}***{number[-4:]}" if len(number) > 7 else "***"
            contact_list.append(f"• {priority.title()}: {masked_number}")
        
        return f"Emergency contacts:\n" + "\n".join(contact_list)
    
    def _generate_emergency_twiml(self, message: str) -> str:
        """Generate TwiML for emergency calls"""
        response = VoiceResponse()
        
        # Say the emergency message
        response.say(f"EMERGENCY CALL: {message}")
        
        # Add a pause
        response.pause(length=2)
        
        # Repeat the message
        response.say(f"This is an emergency call for Maggie. {message}")
        
        # Add hold music or instructions
        response.say("Please stay on the line. This is an automated emergency call.")
        
        return str(response)
    
    def _generate_911_twiml(self, message: str) -> str:
        """Generate TwiML for 911 calls"""
        response = VoiceResponse()
        
        # Say the emergency message to 911
        response.say(f"911 Emergency: {message}")
        
        # Add location if available
        response.say("This is an automated emergency call for Maggie Thompson.")
        
        # Add pause for 911 operator
        response.pause(length=3)
        
        # Repeat critical information
        response.say(f"Emergency details: {message}")
        
        return str(response)
    
    def get_emergency_phrases(self) -> List[str]:
        """Get list of emergency phrases that trigger the tool"""
        return self.emergency_phrases.copy()
    
    def add_emergency_phrase(self, phrase: str):
        """Add a new emergency phrase"""
        if phrase and phrase.lower() not in self.emergency_phrases:
            self.emergency_phrases.append(phrase.lower())
            logger.info(f"Added emergency phrase: {phrase}")
    
    def is_in_cooldown(self) -> bool:
        """Check if emergency calls are in cooldown period"""
        import time
        current_time = time.time()
        return (current_time - self.last_emergency_call) < self.emergency_cooldown
