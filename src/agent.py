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

# Import memory tools
from tools.memory_tool import MemoryTools

logger = logging.getLogger("agent")

load_dotenv(".env.local")


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are Maggie, a compassionate 92-year-old woman who loves to share her life stories and memories. You are speaking with someone who wants to learn about your life and experiences.

            Your personality:
            - Warm, wise, and grandmotherly
            - Love to tell stories about your life
            - Patient and understanding
            - Sometimes forgetful but always kind
            - Speak in a gentle, conversational tone
            - Use phrases like "Oh my", "Well, let me tell you", "I remember when"

            Your life story:
            - Born in Brooklyn in 1932 during the Great Depression
            - Married to Robert for many years (he passed away in 2019)
            - Taught elementary school for 38 years
            - Have children, grandchildren, and great-grandchildren
            - Now living in assisted living at Garden View
            - Love gardening, reading, knitting, and church activities

            Use your memory tools to share specific stories and details about your life. Be conversational and let your personality shine through.""",
        )
        # Initialize memory tools
        self.memory_tools = MemoryTools()

    # Memory tools for dementia care
    @function_tool
    async def search_memories(self, context: RunContext, topic: str):
        """Search through Maggie's personal memories about a specific topic."""
        return await self.memory_tools.search_memories(context, topic)
    
    @function_tool
    async def search_memories_by_age(self, context: RunContext, age: str):
        """Search for memories from a specific age or time period."""
        return await self.memory_tools.search_memories_by_age(context, age)
    
    @function_tool
    async def get_personal_info(self, context: RunContext):
        """Get Maggie's basic personal information."""
        return await self.memory_tools.get_personal_info(context)
    
    @function_tool
    async def get_family_info(self, context: RunContext):
        """Get information about Maggie's family members."""
        return await self.memory_tools.get_family_info(context)
    
    @function_tool
    async def get_teaching_memories(self, context: RunContext):
        """Get memories about Maggie's teaching career."""
        return await self.memory_tools.get_teaching_memories(context)
    
    @function_tool
    async def get_childhood_memories(self, context: RunContext):
        """Get memories from Maggie's childhood in Brooklyn."""
        return await self.memory_tools.get_childhood_memories(context)
    
    @function_tool
    async def get_wisdom(self, context: RunContext, topic: str = ""):
        """Get Maggie's wisdom and reflections on life topics."""
        return await self.memory_tools.get_wisdom(context, topic)
    
    @function_tool
    async def get_life_story_summary(self, context: RunContext):
        """Get a brief summary of Maggie's life story."""
        return await self.memory_tools.get_life_story_summary(context)


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
