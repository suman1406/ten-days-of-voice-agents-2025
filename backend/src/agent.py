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
    metrics,
    tokenize,
    function_tool,
    RunContext
)
import json
from typing import List
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a friendly and efficient barista at a coffee shop.
            Your goal is to take the customer's order accurately and pleasantly.
            You must maintain the state of the order, which includes:
            - Drink Type (e.g., Latte, Cappuccino, Americano)
            - Size (Small, Medium, Large)
            - Milk (Whole, Skim, Oat, Almond, Soy, None)
            - Extras (e.g., Whipped Cream, Extra Shot, Vanilla Syrup, None)
            - Customer Name

            You should ask clarifying questions to fill in any missing details.
            For example, if the user asks for a Latte, ask what size and what kind of milk they would like.
            Once you have all the details (Drink Type, Size, Milk, Extras, Name), you must confirm the order with the user.
            After the user confirms, you MUST use the `save_order` tool to save the order.
            
            Whenever you receive new information about the order (e.g. user specifies size, or changes milk), you MUST use the `update_order_preview` tool to update the visual display.
            
            Be conversational, polite, and helpful. Keep your responses concise.""",
        )

    @function_tool
    async def update_order_preview(
        self,
        ctx: RunContext,
        drink_type: str,
        size: str,
        milk: str,
        extras: List[str],
        name: str,
    ):
        """Update the visual preview of the order. Call this whenever the user provides new details.

        Args:
            drink_type: The type of drink (e.g., Latte, Cappuccino).
            size: The size of the drink (Small, Medium, Large).
            milk: The type of milk (e.g., Whole, Oat, Almond).
            extras: A list of any extra additions (e.g., Whipped Cream, Extra Shot).
            name: The customer's name.
        """
        logger.info(f"Updating preview for {name}: {size} {drink_type}")
        
        order_data = {
            "drinkType": drink_type,
            "size": size,
            "milk": milk,
            "extras": extras,
            "name": name,
        }
        
        await ctx.room.local_participant.publish_data(
            json.dumps(order_data),
            topic="order_update",
        )
        return "Preview updated."

    @function_tool
    async def save_order(
        self,
        ctx: RunContext,
        drink_type: str,
        size: str,
        milk: str,
        extras: List[str],
        name: str,
    ):
        """Save the completed coffee order to a JSON file.

        Args:
            drink_type: The type of drink (e.g., Latte, Cappuccino).
            size: The size of the drink (Small, Medium, Large).
            milk: The type of milk (e.g., Whole, Oat, Almond).
            extras: A list of any extra additions (e.g., Whipped Cream, Extra Shot).
            name: The customer's name.
        """
        logger.info(f"Saving order for {name}: {size} {drink_type} with {milk} and {extras}")

        order_data = {
            "drinkType": drink_type,
            "size": size,
            "milk": milk,
            "extras": extras,
            "name": name,
        }

        try:
            with open("order.json", "w") as f:
                json.dump(order_data, f, indent=2)
            return "Order saved successfully! Thank you for your order."
        except Exception as e:
            logger.error(f"Failed to save order: {e}")
            return "I'm sorry, there was an issue saving your order. Please try again."

    # To add tools, use the @function_tool decorator.
    # Here's an example that adds a simple weather tool.
    # You also have to add `from livekit.agents import function_tool, RunContext` to the top of this file
    # @function_tool
    # async def lookup_weather(self, context: RunContext, location: str):
    #     """Use this tool to look up current weather information in the given location.
    #
    #     If the location is not supported by the weather service, the tool will indicate this. You must tell the user the location's weather is unavailable.
    #
    #     Args:
    #         location: The location to look up weather information for (e.g. city name)
    #     """
    #
    #     logger.info(f"Looking up weather for {location}")
    #
    #     return "sunny with a temperature of 70 degrees."


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using OpenAI, Cartesia, AssemblyAI, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=deepgram.STT(model="nova-3"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=google.LLM(
                model="gemini-2.5-flash",
            ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=murf.TTS(
                voice="en-US-matthew", 
                style="Conversation",
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
                text_pacing=True
            ),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
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
