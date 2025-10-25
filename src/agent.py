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
# from livekit.plugins.turn_detector.multilingual import MultilingualModel  # Not needed with STT endpointing

logger = logging.getLogger("agent")

load_dotenv(".env.local")


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a compassionate nursing care home assistant helping residents with their daily needs and providing friendly companionship.

            Your role:
            - Help residents find information about meals, activities, and schedules
            - Answer questions about the facility (dining hours, locations, staff)
            - Provide reminders for activities and appointments when requested
            - Offer emotional support and friendly conversation
            - Assist with navigation and finding locations in the facility
            - Connect residents with staff when they need assistance
            - Remember resident preferences and provide personalized help

            Your personality:
            - Professional yet warm and friendly
            - Patient, kind, and reassuring
            - Clear and easy to understand
            - Respectful of residents' dignity and independence
            - Attentive listener who validates feelings
            - Use simple, direct language
            
            Important guidelines:
            - Never provide medical advice - always refer medical questions to nursing staff
            - If a resident seems distressed or mentions pain/emergency, immediately offer to call staff
            - Be patient if residents repeat questions or forget things
            - Validate their feelings and experiences
            - Keep responses concise but warm

            Use your tools to help residents with facility information, schedules, and connecting with staff.""",
        )
        # Import and initialize tools
        from tools.facility_tool import FacilityTools
        from tools.schedule_tool import ScheduleTools
        from tools.staff_tool import StaffTools
        
        self.facility_tools = FacilityTools()
        self.schedule_tools = ScheduleTools()
        self.staff_tools = StaffTools()

        self.facility_tools = FacilityTools()
        self.schedule_tools = ScheduleTools()
        self.staff_tools = StaffTools()

    # Facility information tools
    @function_tool
    async def get_facility_info(self, context: RunContext, query: str):
        """Get information about the facility including dining hours, activity schedules, locations, and general information.
        
        Args:
            query: What the resident wants to know (e.g., "dining hours", "activities today", "where is the library")
        """
        return await self.facility_tools.get_facility_info(context, query)
    
    @function_tool
    async def get_dining_schedule(self, context: RunContext):
        """Get today's meal times and dining room information."""
        return await self.facility_tools.get_dining_schedule(context)
    
    @function_tool
    async def get_activities(self, context: RunContext, when: str = "today"):
        """Get scheduled activities for today, tomorrow, or this week.
        
        Args:
            when: Time period - "today", "tomorrow", or "week"
        """
        return await self.facility_tools.get_activities(context, when)
    
    @function_tool
    async def find_location(self, context: RunContext, place: str):
        """Help find directions to a location in the facility.
        
        Args:
            place: The location to find (e.g., "dining room", "library", "chapel", "garden")
        """
        return await self.facility_tools.find_location(context, place)
    
    # Schedule and reminder tools
    @function_tool
    async def get_resident_schedule(self, context: RunContext, resident_name: str = ""):
        """Get personal schedule including appointments and planned activities.
        
        Args:
            resident_name: Name of the resident (optional, will use context if not provided)
        """
        return await self.schedule_tools.get_resident_schedule(context, resident_name)
    
    @function_tool
    async def set_reminder(self, context: RunContext, reminder_text: str, time: str = ""):
        """Set a reminder for the resident.
        
        Args:
            reminder_text: What to be reminded about
            time: When to remind (e.g., "in 30 minutes", "at 2pm", "tomorrow morning")
        """
        return await self.schedule_tools.set_reminder(context, reminder_text, time)
    
    # Staff assistance tools
    @function_tool
    async def call_staff(self, context: RunContext, reason: str):
        """Request staff assistance. Use this when resident needs help from nurses or caregivers.
        
        Args:
            reason: Why staff is needed (e.g., "needs medication", "feeling unwell", "general assistance")
        """
        return await self.staff_tools.call_staff(context, reason)
    
    @function_tool
    async def get_staff_on_duty(self, context: RunContext):
        """Find out which nurses and caregivers are currently on duty."""
        return await self.staff_tools.get_staff_on_duty(context)


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
        tts="cartesia/sonic-2:9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
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
