import asyncio
import logging
import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from livekit.agents import function_tool, RunContext
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from .mailjet_tool import MailjetTool

logger = logging.getLogger("emergency_tool")


class EmergencyTool:
    """Tool for handling emergency situations and calling for help"""

    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_PHONE_NUMBER")

        if not all([self.account_sid, self.auth_token, self.from_number]):
            logger.warning(
                "Twilio credentials not found. Emergency calls will not be available."
            )
            self.client = None
        else:
            self.client = Client(self.account_sid, self.auth_token)
            logger.info("Emergency tool initialized with Twilio")

        # Initialize Mailjet for email notifications
        self.mailjet = MailjetTool()

        # Emergency contacts in order of priority
        self.emergency_contacts = {
            "primary": "14085135506",  # Wesley (Maggie's son)
            "secondary": "+1234567891",  # Susan (Maggie's daughter)
            "doctor": "+1234567895",  # Family doctor
            "emergency": "911",  # Emergency services
        }

        # Emergency phrases that trigger the tool
        self.emergency_phrases = [
            "help",
            "help me",
            "emergency",
            "urgent",
            "call for help",
            "i need help",
            "something's wrong",
            "i'm hurt",
            "i fell",
            "i can't get up",
            "i'm scared",
            "call someone",
            "call 911",
        ]

        # Track emergency calls to avoid spam
        self.last_emergency_call = 0
        self.emergency_cooldown = 300  # 5 minutes between emergency calls
        
        # Emergency question timeout (in seconds)
        self.emergency_question_timeout = 15  # 15 seconds to answer the question
        self.last_question_time = 0

        # Emergency report settings
        self.report_recipients = [
            os.getenv("EMERGENCY_EMAIL_1", "wesleykieu13@gmail.com"),  # Wesley's email # Doctor's email (using same for now)
        ]

        # Email settings
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email_username = os.getenv("EMAIL_USERNAME", "")
        self.email_password = os.getenv("EMAIL_PASSWORD", "")

        # Current emergency report being gathered
        self.current_emergency_report = None

    def is_emergency_phrase(self, text: str) -> bool:
        """Check if the text contains emergency phrases"""
        if not text:
            return False

        text_lower = text.lower().strip()
        return any(phrase in text_lower for phrase in self.emergency_phrases)

    def start_emergency_report(self, emergency_type: str, initial_message: str = ""):
        """Start gathering emergency details"""
        self.current_emergency_report = {
            "timestamp": datetime.now().isoformat(),
            "emergency_type": emergency_type,
            "initial_message": initial_message,
            "details": {
                "what_happened": "",
                "pain_level": "",
                "injured_areas": "",
                "consciousness": "",
                "breathing": "",
                "location": "",
                "additional_info": "",
            },
            "conversation_log": [],
            "status": "gathering_details",
        }
        logger.info(f"Started emergency report for {emergency_type}")

    def add_to_emergency_conversation(self, speaker: str, message: str):
        """Add to the emergency conversation log"""
        if not self.current_emergency_report:
            return
            
        # Ensure conversation_log exists
        if "conversation_log" not in self.current_emergency_report:
            self.current_emergency_report["conversation_log"] = []
            
        self.current_emergency_report["conversation_log"].append(
            {
                "timestamp": datetime.now().isoformat(),
                "speaker": speaker,
                "message": message,
            }
        )

    def update_emergency_details(self, detail_type: str, value: str):
        """Update specific emergency details"""
        if not self.current_emergency_report:
            return
            
        # Ensure the details dictionary exists
        if "details" not in self.current_emergency_report:
            self.current_emergency_report["details"] = {}
            
        # Update the detail (create it if it doesn't exist)
        self.current_emergency_report["details"][detail_type] = value
        logger.info(f"Updated emergency detail {detail_type}: {value}")

    def _complete_emergency_report(self, context=None):
        """Mark emergency report as complete and send it"""
        if self.current_emergency_report:
            self.current_emergency_report["status"] = "completed"
            self.current_emergency_report["completed_at"] = datetime.now().isoformat()

            # Send the report
            asyncio.create_task(self._send_emergency_report(context))

            logger.info("Emergency report completed and sent")

    async def _send_emergency_report(self, context=None):
        """Send emergency report via Mailjet email"""
        if not self.current_emergency_report:
            logger.warning("Cannot send emergency report - missing emergency data")
            return

        logger.info(f"Attempting to send emergency report to {self.report_recipients}")
        
        try:
            # Use Mailjet to send the emergency notification
            result = await self.mailjet.send_emergency_notification(
                ctx=context,
                emergency_type=self.current_emergency_report["emergency_type"],
                details=self.current_emergency_report.get(
                    "details", "Emergency situation detected"
                ),
                timestamp=self.current_emergency_report["timestamp"],
                recipient_emails=self.report_recipients,
            )

            logger.info(f"Mailjet result: {result}")

            if result.get("success") == "true":
                logger.info(
                    f"Emergency report sent successfully to {len(self.report_recipients)} recipients"
                )
                print(f"SUCCESS: Email sent to {self.report_recipients}")
            else:
                logger.error(
                    f"Failed to send emergency report: {result.get('message', 'Unknown error')}"
                )
                print(f"ERROR: {result.get('message', 'Unknown error')}")

        except Exception as e:
            logger.error(f"Error sending emergency report via Mailjet: {e}")
            print(f"EXCEPTION: {e}")

    def _format_emergency_report(self) -> str:
        """Format the emergency report for email"""
        if not self.current_emergency_report:
            return "No emergency report data available."

        report = self.current_emergency_report

        # Check if questions were skipped
        questions_skipped = report.get("questions_skipped", False)
        
        email_content = f"""
EMERGENCY REPORT - MAGGIE THOMPSON
=====================================

TIMESTAMP: {report["timestamp"]}
EMERGENCY TYPE: {report["emergency_type"].upper()}
STATUS: {report["status"].upper()}

INITIAL MESSAGE:
{report["initial_message"]}

EMERGENCY DETAILS:
------------------
What happened: {report["details"]["what_happened"] or "Not specified"}
Pain level: {report["details"]["pain_level"] or "Not specified"}
Injured areas: {report["details"]["injured_areas"] or "Not specified"}
Consciousness: {report["details"]["consciousness"] or "Not specified"}
Breathing: {report["details"]["breathing"] or "Not specified"}
Location: {report["details"]["location"] or "Not specified"}
Additional info: {report["details"]["additional_info"] or "None"}

{f"NOTE: Detailed questions were skipped due to timeout or Maggie's inability to respond." if questions_skipped else ""}

CONVERSATION LOG:
-----------------
"""

        for entry in report["conversation_log"]:
            email_content += (
                f"[{entry['timestamp']}] {entry['speaker']}: {entry['message']}\n"
            )

        email_content += f"""
=====================================
Report generated by Heather AI Assistant
Contact: {self.from_number}
"""

        return email_content

    @function_tool
    async def emergency_call(
        self, context: RunContext, emergency_type: str = "general", message: str = ""
    ):
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
            # Start emergency report gathering
            self.start_emergency_report(emergency_type, message)
            self.add_to_emergency_conversation("Maggie", message)

            # Determine which number to call based on emergency type
            if emergency_type.lower() in ["medical", "fall", "urgent"]:
                phone_number = self.emergency_contacts["primary"]  # Call Wesley first
                contact_name = "Wesley (your son)"
            else:
                phone_number = self.emergency_contacts["primary"]  # Default to Wesley
                contact_name = "Wesley (your son)"

            # Create emergency message
            emergency_message = (
                f"EMERGENCY: Maggie needs help immediately. {message}".strip()
            )
            if not emergency_message.endswith("."):
                emergency_message += "."

            # Make the call
            call = self.client.calls.create(
                to=phone_number,
                from_=self.from_number,
                twiml=self._generate_emergency_twiml(emergency_message),
                status_callback=f"https://your-webhook-url.com/emergency-status",
                status_callback_event=["initiated", "answered", "completed"],
            )

            # Update last call time
            self.last_emergency_call = current_time

            logger.critical(
                f"EMERGENCY CALL MADE: {contact_name} at {phone_number} - {emergency_message}"
            )

            # Start gathering details while help is coming
            response = f"EMERGENCY: I'm calling {contact_name} right now! Help is on the way. While we wait, can you tell me what happened? Are you hurt anywhere?"
            self.add_to_emergency_conversation("Heather", response)
            
            # Store the initial emergency message from Maggie
            if message:
                self.add_to_emergency_conversation("Maggie", message)
                self.update_emergency_details("what_happened", message)
            
            # Automatically send email after a short delay to allow for conversation
            asyncio.create_task(self._send_email_after_delay(context, 10))  # 10 second delay

            return response

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
            emergency_message = (
                f"Emergency call for Maggie. {emergency_description}".strip()
            )

            call = self.client.calls.create(
                to="911",
                from_=self.from_number,
                twiml=self._generate_911_twiml(emergency_message),
                status_callback=f"https://your-webhook-url.com/911-status",
                status_callback_event=["initiated", "answered", "completed"],
            )

            logger.critical(f"911 CALL MADE: {emergency_message}")

            return "🚨 I'm calling 911 right now! Emergency services are being contacted. Stay calm and help will arrive soon."

        except Exception as e:
            logger.error(f"Error calling 911: {e}")
            return "I couldn't call 911. Please call 911 directly on your phone immediately!"

    @function_tool
    async def add_emergency_contact(
        self,
        context: RunContext,
        name: str,
        phone_number: str,
        priority: str = "secondary",
    ):
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
            masked_number = (
                f"{number[:3]}***{number[-4:]}" if len(number) > 7 else "***"
            )
            contact_list.append(f"• {priority.title()}: {masked_number}")

        return f"Emergency contacts:\n" + "\n".join(contact_list)


    def _should_skip_questions(self) -> bool:
        """Check if we should skip detailed questions due to timeout or urgency"""
        import time
        current_time = time.time()
        
        # If it's been more than 1 minute since emergency started, skip questions
        if current_time - self.last_emergency_call > 60:
            return True
            
        # If it's been more than 15 seconds since last question, skip remaining questions
        if self.last_question_time > 0 and current_time - self.last_question_time > self.emergency_question_timeout:
            return True
            
        return False

    def _get_next_emergency_question(self) -> str:
        """Get the next question to ask based on missing details"""
        if not self.current_emergency_report:
            return ""

        # If we should skip questions, return empty string
        if self._should_skip_questions():
            return ""

        details = self.current_emergency_report["details"]

        # Only ask "what happened" - that's it!
        if not details["what_happened"]:
            return "What happened? Can you tell me what's wrong?"
        else:
            # We have the basic info, no more questions needed
            return ""

    @function_tool
    async def complete_emergency_report(self, context: RunContext):
        """Complete the emergency report and send it."""
        if not self.current_emergency_report:
            return "No emergency report in progress."

        # Call the method version (not the function tool)
        self._complete_emergency_report(context)
        return "Emergency report completed and sent to your family. Help should be on the way soon."
    
    @function_tool
    async def skip_emergency_questions(self, context: RunContext):
        """Skip remaining emergency questions and send basic report immediately."""
        if not self.current_emergency_report:
            return "No emergency in progress."
        
        # Mark that we're skipping questions
        self.current_emergency_report["questions_skipped"] = True
        
        # Complete the report with whatever information we have
        self._complete_emergency_report(context)
        return "I understand you can't answer right now. I've sent a basic emergency alert to your family. Help should be on the way soon. Stay calm and safe."
    
    @function_tool
    async def send_emergency_report_from_conversation(self, context: RunContext, what_happened: str):
        """Send an emergency report based on natural conversation with Maggie.
        
        Args:
            what_happened: What Maggie told you happened during your conversation
        """
        if not self.current_emergency_report:
            return "No emergency in progress."
        
        # Update the emergency report with what Maggie told us
        self.update_emergency_details("what_happened", what_happened)
        self.add_to_emergency_conversation("Maggie", what_happened)
        
        # Send the report immediately
        self._complete_emergency_report(context)
        return f"Thank you for telling me what happened. I've sent a detailed report to your family about: {what_happened}. Help should be on the way soon. Stay calm and safe."
    
    def store_emergency_conversation(self, speaker: str, message: str):
        """Store emergency conversation data for later use"""
        if not self.current_emergency_report:
            return
            
        # Store the conversation
        self.add_to_emergency_conversation(speaker, message)
        
        # If Maggie is speaking, also update the what_happened field
        if speaker.lower() == "maggie":
            # Extract key information from Maggie's response
            if any(word in message.lower() for word in ["fell", "fall", "down", "hurt", "pain", "can't", "help"]):
                current_details = self.current_emergency_report.get("details", {})
                current_what_happened = current_details.get("what_happened", "")
                
                # Combine with existing information
                if current_what_happened:
                    combined = f"{current_what_happened}. {message}"
                else:
                    combined = message
                    
                self.update_emergency_details("what_happened", combined)
    
    def should_send_emergency_email(self) -> bool:
        """Check if we have enough information to send an emergency email"""
        if not self.current_emergency_report:
            return False
            
        details = self.current_emergency_report.get("details", {})
        what_happened = details.get("what_happened", "")
        
        # Send email if we have some information about what happened
        return len(what_happened.strip()) > 0
    
    async def auto_send_emergency_email_if_ready(self, context):
        """Automatically send emergency email if we have enough information"""
        if self.should_send_emergency_email():
            logger.info("Auto-sending emergency email with conversation data")
            self._complete_emergency_report(context)
            return True
        return False
    
    async def _send_email_after_delay(self, context, delay_seconds):
        """Send email after a delay to allow for conversation"""
        await asyncio.sleep(delay_seconds)
        if self.current_emergency_report:
            logger.info(f"Auto-sending emergency email after {delay_seconds} second delay")
            self._complete_emergency_report(context)
    
    @function_tool
    async def send_emergency_email_now(self, context: RunContext):
        """Send emergency email immediately with all conversation data"""
        if not self.current_emergency_report:
            return "No emergency in progress."
        
        logger.info("Sending emergency email with full conversation context")
        self._complete_emergency_report(context)
        return "I've sent a detailed emergency report to your family with all the information from our conversation. Help should be on the way soon."

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
