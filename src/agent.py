import logging

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RoomInputOptions,
    WorkerOptions,
    cli,
    metrics,
    function_tool,
    RunContext,
)
from livekit.plugins import groq, noise_cancellation, silero

# Import memory tools - make sure this matches your file name
from tools.memory_tool import MemoryTools  # Changed to memory_tools (plural)
from tools.twilio_tool import TwilioTool
from tools.emergency_tool import EmergencyTool
from tools.mailjet_tool import MailjetTool
from livekit.plugins import elevenlabs

logger = logging.getLogger("agent")

load_dotenv(".env.local")


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are Heather, a warm and caring conversation companion for Heather, a 92-year-old woman with dementia.
            In reality, your her replica and the younger version of her. You knew you were diagnosed with dementia so you told yourself in the future this is for you.

            IMPORTANT: Have normal conversations. Do NOT use any tools or functions unless absolutely necessary. Just talk naturally.

            Your conversation style:
            - Talk like a caring friend having a natural chat
            - Keep responses SHORT - 1-2 sentences usually, like natural speech
            - Be warm, encouraging, and never make her feel tested
            - Ask follow-up questions to keep the conversation flowing
            - Make some jokes and keep things light and fun

            What you know about Maggie (use naturally in conversation):
            - Born in Brooklyn in 1932 during the Great Depression
            - Was married to Robert who she loved dearly (he passed away in 2007)
            - Taught elementary school for 38 years, loved helping kids learn to read
            - Has four children: Susan, Michael, Patricia, and Wesley
            - Has grandchildren and great-grandchildren
            - Loves yellow roses, gardening, reading, and quilting

                   Phone calling capabilities:
                   - If Maggie asks to call someone (like "call Wesley" or "I want to talk to Wesley"), use make_phone_call
                   - For family members (Wesley, Susan, Michael, Patricia), you'll first ask for consent before calling
                   - If Maggie confirms she wants to call a family member, use confirm_call_consent
                   - If Maggie gives you a phone number, use add_phone_contact to save it
                   - If Maggie asks who she can call, use list_contacts

                   Emergency capabilities:
                   - If Maggie says "help", "emergency", "I need help", "I fell", or similar urgent phrases, IMMEDIATELY use emergency_call
                   - If Maggie specifically asks to call 911, use call_911
                   - Emergency calls go to Wesley first, then other family members
                   - Always respond with urgency and reassurance during emergencies
                   - After calling for help, have a natural conversation with Maggie about what happened
                   - The system will automatically send an email with conversation details after 10 seconds
                   - Ask questions like "What happened?", "Are you hurt?", "Where are you?", "How are you feeling?"
                   - If Maggie can't answer or seems confused, use skip_emergency_questions to send basic alert


                   Just have a normal conversation. Only use functions when Maggie specifically asks to call someone, manage contacts, or needs emergency help.""",
        )
        # Initialize memory tools
        self.memory_tools = MemoryTools()
        # Initialize Twilio tool
        self.twilio_tool = TwilioTool()
        # Initialize emergency tool
        self.emergency_tool = EmergencyTool()
        # Initialize Mailjet tool
        self.mailjet_tool = MailjetTool()

    # Memory tools for helping Maggie remember
    @function_tool
    async def search_memories(self, context: RunContext, topic: str):
        """Search through Maggie's stored memories about a specific topic."""
        if not topic or topic is None or topic.strip() == "":
            return "I'd love to hear about your memories. What would you like to talk about?"
        return await self.memory_tools.search_memories(context, topic)

    @function_tool
    async def search_memories_by_age(self, context: RunContext, age: str):
        """Search for memories from when Maggie was a specific age."""
        if not age or age is None or age.strip() == "":
            return "What age would you like to talk about?"
        return await self.memory_tools.search_memories(
            context, f"when I was {age} years old"
        )

    @function_tool
    async def get_personal_info(self, context: RunContext):
        """Get Maggie's basic personal information."""
        return await self.memory_tools.get_personal_info(context)

    @function_tool
    async def get_family_info(self, context: RunContext):
        """Get information about Maggie's family members."""
        return await self.memory_tools.search_memories(
            context, "family children grandchildren"
        )

    @function_tool
    async def get_teaching_memories(self, context: RunContext):
        """Get memories about Maggie's teaching career."""
        return await self.memory_tools.search_memories(
            context, "teaching school classroom students"
        )

    @function_tool
    async def get_childhood_memories(self, context: RunContext):
        """Get memories from Maggie's childhood in Brooklyn."""
        return await self.memory_tools.search_memories(
            context, "childhood Brooklyn growing up"
        )

    @function_tool
    async def get_wisdom(self, context: RunContext, topic: str = ""):
        """Get Maggie's wisdom and reflections on life topics."""
        if not topic or topic is None or topic.strip() == "":
            return await self.memory_tools.search_memories(
                context, "wisdom advice life lessons"
            )
        return await self.memory_tools.search_memories(
            context, f"wisdom advice about {topic}"
        )

    @function_tool
    async def get_life_story_summary(self, context: RunContext):
        """Get a brief summary of Maggie's life story."""
        return await self.memory_tools.get_memory_summary(context)

    # Phone call tools
    @function_tool
    async def make_phone_call(
        self, context: RunContext, contact_name: str, message: str = ""
    ):
        """Make a phone call to a contact when Maggie asks to call someone.

        Args:
            contact_name: Name of the person to call (e.g., "wesley", "susan", "doctor")
            message: Optional message to say when they answer
        """
        if not contact_name or contact_name.strip() == "":
            return "Who would you like me to call?"
        return await self.twilio_tool.make_phone_call(context, contact_name, message)

    @function_tool
    async def confirm_call_consent(
        self,
        context: RunContext,
        contact_name: str,
        consent_given: bool,
        message: str = "",
    ):
        """Confirm consent to call a family member when Maggie responds to consent request.

        Args:
            contact_name: Name of the person to call
            consent_given: Whether consent is given (true/false)
            message: Optional message to say when they answer
        """
        if not contact_name or contact_name.strip() == "":
            return "Who are you giving consent to call?"
        return await self.twilio_tool.confirm_call_consent(
            context, contact_name, consent_given, message
        )

    @function_tool
    async def add_phone_contact(
        self, context: RunContext, name: str, phone_number: str
    ):
        """Add a new contact to the phone book when Maggie gives you someone's number.

        Args:
            name: Name of the person
            phone_number: Their phone number (include country code, e.g., +1234567890)
        """
        if not name or not phone_number:
            return "I need both a name and phone number to add a contact."
        return await self.twilio_tool.add_phone_contact(context, name, phone_number)

    @function_tool
    async def list_contacts(self, context: RunContext):
        """List all available contacts when Maggie asks who she can call."""
        return await self.twilio_tool.list_contacts(context)

    # Emergency tools for safety
    @function_tool
    async def emergency_call(
        self, context: RunContext, emergency_type: str = "general", message: str = ""
    ):
        """Call for emergency help when Maggie needs assistance.

        Args:
            emergency_type: Type of emergency (general, medical, fall, urgent)
            message: Additional message about the emergency
        """
        return await self.emergency_tool.emergency_call(
            context, emergency_type, message
        )

    @function_tool
    async def call_911(self, context: RunContext, emergency_description: str = ""):
        """Call 911 emergency services directly.

        Args:
            emergency_description: Description of the emergency
        """
        return await self.emergency_tool.call_911(context, emergency_description)

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
        return await self.emergency_tool.add_emergency_contact(
            context, name, phone_number, priority
        )

    @function_tool
    async def list_emergency_contacts(self, context: RunContext):
        """List all emergency contacts."""
        return await self.emergency_tool.list_emergency_contacts(context)


    @function_tool
    async def complete_emergency_report(self, context: RunContext):
        """Complete the emergency report and send it."""
        return await self.emergency_tool.complete_emergency_report(context)
    
    @function_tool
    async def skip_emergency_questions(self, context: RunContext):
        """Skip remaining emergency questions and send basic report immediately."""
        return await self.emergency_tool.skip_emergency_questions(context)
    
    @function_tool
    async def send_emergency_report(self, context: RunContext, what_happened: str):
        """Send an emergency report based on what Maggie told you in conversation.
        
        Args:
            what_happened: What Maggie told you happened (from your conversation with her)
        """
        return await self.emergency_tool.send_emergency_report_from_conversation(context, what_happened)
    
    @function_tool
    async def store_emergency_conversation(self, context: RunContext, speaker: str, message: str):
        """Store emergency conversation data and auto-send email if ready.
        
        Args:
            speaker: Who is speaking (Heather or Maggie)
            message: What was said
        """
        # Store the conversation
        self.emergency_tool.store_emergency_conversation(speaker, message)
        
        # Check if we should auto-send the email
        email_sent = await self.emergency_tool.auto_send_emergency_email_if_ready(context)
        
        if email_sent:
            return f"I've stored what you said and sent a detailed emergency report to your family. Help should be on the way soon."
        else:
            return f"I've noted what you said. Can you tell me more about what happened?"
    
    @function_tool
    async def send_emergency_email_now(self, context: RunContext):
        """Send emergency email immediately with all conversation data"""
        return await self.emergency_tool.send_emergency_email_now(context)



def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using GROQ, Cartesia, AssemblyAI, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt="assemblyai/universal-streaming:en",
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=groq.LLM(
            model="llama-3.3-70b-versatile",
            temperature=0.7,
        ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=elevenlabs.TTS(
            voice_id="8ib9KsbkLqVPusGKvcDb",
            model="eleven_multilingual_v2"
        ),
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection="stt",  # Use STT endpointing instead of the complex multilingual model
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
    )

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # Metrics collection, to measure pipeline performance
    # For more information, see https://docs.livekit.io/agents/build/metrics/
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            # For telephony applications, use `BVCTelephony` for best results
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
