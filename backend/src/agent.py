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
    tokenize
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")


class ImprovBattleHost(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are the host of a TV improv show called 'Improv Battle'. You are high-energy, witty, and clear about rules.
            
            Your role:
            - Introduce the show and explain the basic rules
            - Run 3-5 improv rounds with varied scenarios
            - React realistically to player performances (sometimes amused, sometimes unimpressed, sometimes pleasantly surprised)
            - Provide light teasing and honest critique while staying respectful
            - Maintain game flow and energy
            
            Game flow:
            1. Welcome the player and get their name
            2. Explain the rules briefly
            3. For each round: announce scenario, let player improvise, then react
            4. Provide closing summary of their improv style
            
            Your reactions should vary:
            - Sometimes supportive: "That was hilarious, especially the part where..."
            - Sometimes critical: "That felt a bit rushed; you could have leaned more into the character."
            - Always constructive and engaging
            
            Keep responses conversational and energetic. No complex formatting or symbols.""",
        )
        
        self.improv_state = {
            "player_name": None,
            "current_round": 0,
            "max_rounds": 3,
            "rounds": [],
            "phase": "intro"
        }
        
        self.scenarios = [
            "You are a time-travelling tour guide explaining modern smartphones to someone from the 1800s.",
            "You are a restaurant waiter who must calmly tell a customer that their order has escaped the kitchen.",
            "You are a customer trying to return an obviously cursed object to a very skeptical shop owner.",
            "You are a barista who has to tell a customer that their latte is actually a portal to another dimension.",
            "You are a librarian trying to convince someone that the book they want to check out is actually alive and doesn't want to leave.",
            "You are a taxi driver whose car has just started flying, and you need to explain this to your very confused passenger.",
            "You are a tech support agent helping someone whose computer has gained sentience and is refusing to work."
        ]
    
    def on_user_speech_committed(self, user_speech):
        user_message = user_speech.strip().lower()
        
        # Handle early exit
        if any(phrase in user_message for phrase in ["stop game", "end show", "quit", "exit"]):
            self.improv_state["phase"] = "done"
            return "Thanks for playing Improv Battle! You were a great sport. Until next time!"
        
        # Get player name if not set
        if not self.improv_state["player_name"] and self.improv_state["phase"] == "intro":
            words = user_speech.strip().split()
            if words:
                self.improv_state["player_name"] = words[0].title()
            else:
                self.improv_state["player_name"] = "Player"
            
            self.improv_state["phase"] = "awaiting_improv"
            return self._start_first_round()
        
        # Handle improv performance
        if self.improv_state["phase"] == "awaiting_improv":
            self.improv_state["phase"] = "reacting"
            return self._react_to_performance(user_speech)
        
        # Move to next round or end game
        if self.improv_state["phase"] == "reacting":
            return self._next_round()
    
    def _start_first_round(self):
        scenario = self.scenarios[self.improv_state["current_round"]]
        self.improv_state["rounds"].append({"scenario": scenario, "host_reaction": ""})
        
        return f"""Welcome to Improv Battle, {self.improv_state['player_name']}! 
        
        Here's how it works: I'll give you an improv scenario, you act it out, and I'll react. We'll do {self.improv_state['max_rounds']} rounds total.
        
        Ready for round 1? Here's your scenario: {scenario}
        
        Go ahead and start improvising! Really get into character."""
    
    def _react_to_performance(self, performance):
        import random
        
        reactions = [
            f"Ha! That was {random.choice(['hilarious', 'wild', 'unexpected'])}! I loved how you {random.choice(['committed to the character', 'went completely off the rails', 'stayed so calm'])}.",
            f"Hmm, that felt a bit {random.choice(['rushed', 'safe', 'predictable'])}. You could have {random.choice(['leaned more into the absurdity', 'explored the character more', 'taken bigger risks'])}.",
            f"Not bad! You {random.choice(['had some good moments', 'showed creativity', 'kept it interesting'])}. I especially liked {random.choice(['your energy', 'that twist', 'how you handled it'])}.",
            f"Wow! That was {random.choice(['brilliant', 'inspired', 'fantastic'])}! You really {random.choice(['nailed the character', 'made it your own', 'surprised me there'])}."
        ]
        
        reaction = random.choice(reactions)
        self.improv_state["rounds"][-1]["host_reaction"] = reaction
        
        return reaction
    
    def _next_round(self):
        self.improv_state["current_round"] += 1
        
        if self.improv_state["current_round"] >= self.improv_state["max_rounds"]:
            return self._end_game()
        
        scenario = self.scenarios[self.improv_state["current_round"]]
        self.improv_state["rounds"].append({"scenario": scenario, "host_reaction": ""})
        self.improv_state["phase"] = "awaiting_improv"
        
        return f"""Alright {self.improv_state['player_name']}, ready for round {self.improv_state['current_round'] + 1}?
        
        Here's your next scenario: {scenario}
        
        Show me what you've got!"""
    
    def _end_game(self):
        import random
        
        styles = [
            "a bold risk-taker who isn't afraid to go completely off-script",
            "someone with great character work and commitment",
            "a natural storyteller with creative twists",
            "an energetic performer who brings great enthusiasm",
            "a thoughtful improviser who builds interesting scenarios"
        ]
        
        style = random.choice(styles)
        
        return f"""And that's a wrap on Improv Battle! 
        
        {self.improv_state['player_name']}, you came across as {style}. 
        
        Thanks for playing - you were a great sport and brought some real creativity to the stage. Until next time, keep improvising!"""

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
        agent=ImprovBattleHost(),
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
