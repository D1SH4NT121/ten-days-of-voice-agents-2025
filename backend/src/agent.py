import logging
import json
import os
import asyncio
from typing import Annotated, Literal, Optional, Dict, List
from dataclasses import dataclass

print("\n" + "🧬" * 50)
print("🚀 Soft Computing Tutor")
print("💡 agent.py LOADED SUCCESSFULLY!")
print("🧬" * 50 + "\n")

from dotenv import load_dotenv
from pydantic import Field
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    RoomInputOptions,
    WorkerOptions,
    cli,
    function_tool,
    RunContext,
)

# 🔌 PLUGINS
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")
load_dotenv(".env.local")



# 🆕 Renamed file so it generates fresh data for you
CONTENT_FILE = "soft_computing.json" 

DEFAULT_CONTENT = [
  {
    "id": "fuzzy_logic",
    "title": "The Fuzzy Logic",
    "summary": "Fuzzy logic is a mathematical framework for dealing with uncertainty and approximate reasoning, allowing values between true and false.",
    "sample_question": "What is fuzzy logic and how does it differ from classical binary logic?"
  },
  {
    "id": "neural_networks",
    "title": "The Neural Networks",
    "summary": "Neural networks are computational models inspired by the human brain, used in pattern recognition and machine learning.",
    "sample_question": "Describe how a neural network learns from data."
  },
  {
    "id": "genetic_algorithms",
    "title": "The Genetic Algorithms",
    "summary": "Genetic algorithms are optimization techniques inspired by the process of natural selection, used to solve complex problems.",
    "sample_question": "What are the main steps in a genetic algorithm?"
  },
  {
    "id": "soft_computing_features",
    "title": "The Soft Computing Features",
    "summary": "Soft Computing deals with approximate solutions, tolerance for imprecision, and the ability to handle uncertainty, unlike traditional hard computing.",
    "sample_question": "List some key differences between soft computing and hard computing."
  }
]


def load_content() -> List[Dict[str, str]]:
    """
    📖 Checks if soft computing JSON exists. 
    If NO: Generates it from DEFAULT_CONTENT.
    If YES: Loads it.
    """
    try:
        path = os.path.join(os.path.dirname(__file__), CONTENT_FILE)
        
        # Check if file exists
        if not os.path.exists(path):
            print(f"⚠️ {CONTENT_FILE} not found. Generating soft computing data...")
            with open(path, "w", encoding='utf-8') as f:
                json.dump(DEFAULT_CONTENT, f, indent=4)
            print("✅ Soft computing data created successfully.") 
            
        # Read the file
        with open(path, "r", encoding='utf-8') as f:
            data = json.load(f)
            return data
            
    except Exception as e:
        print(f"⚠️ Error managing content file: {e}")
        return []

# Load data immediately on startup
COURSE_CONTENT: List[Dict[str, str]] = load_content()



@dataclass
class TutorState:
    """🧠 Tracks the current learning context"""
    current_topic_id: str | None = None
    current_topic_data: dict | None = None
    mode: Literal["learn", "quiz", "teach_back"] = "learn"
    
    def set_topic(self, topic_id: str):
        # Find topic in loaded content
        topic = next((item for item in COURSE_CONTENT if item["id"] == topic_id), None)
        if topic:
            self.current_topic_id = topic_id
            self.current_topic_data = topic
            return True
        return False

@dataclass
class Userdata:
    tutor_state: TutorState
    agent_session: Optional[AgentSession] = None 


@function_tool
async def select_topic(
    ctx: RunContext[Userdata], 
    topic_id: Annotated[str, Field(description="The ID of the topic to study (e.g., 'dna', 'cell', 'nucleus')")]
) -> str:
    """📚 Selects a topic to study from the available list."""
    state = ctx.userdata.tutor_state
    success = state.set_topic(topic_id.lower())
    
    if success:
        return f"Topic set to {state.current_topic_data['title']}. Ask the user if they want to 'Learn', be 'Quizzed', or 'Teach it back'."
    else:
        available = ", ".join([t["id"] for t in COURSE_CONTENT])
        return f"Topic not found. Available topics are: {available}"

@function_tool
async def set_learning_mode(
    ctx: RunContext[Userdata], 
    mode: Annotated[str, Field(description="The mode to switch to: 'learn', 'quiz', or 'teach_back'")]
) -> str:
    """🔄 Switches the interaction mode and updates the agent's voice/persona."""
    
    # 1. Update State
    state = ctx.userdata.tutor_state
    state.mode = mode.lower()
    
    # 2. Switch Voice based on Mode
    agent_session = ctx.userdata.agent_session 
    
    if agent_session:
        if state.mode == "learn":
            # 👨‍🏫 MATTHEW: The Lecturer
            agent_session.tts.update_options(voice="en-US-matthew", style="Promo")
            instruction = f"Mode: LEARN. Explain: {state.current_topic_data['summary']}"
            
        elif state.mode == "quiz":
            # 👩‍🏫 ALICIA: The Examiner
            agent_session.tts.update_options(voice="en-US-alicia", style="Conversational")
            instruction = f"Mode: QUIZ. Ask this question: {state.current_topic_data['sample_question']}"
            
        elif state.mode == "teach_back":
            # 👨‍🎓 KEN: The Student/Coach
            agent_session.tts.update_options(voice="en-US-ken", style="Promo")
            instruction = "Mode: TEACH_BACK. Ask the user to explain the concept to you as if YOU are the beginner."
        else:
            return "Invalid mode."
    else:
        instruction = "Voice switch failed (Session not found)."

    print(f"🔄 SWITCHING MODE -> {state.mode.upper()}")
    return f"Switched to {state.mode} mode. {instruction}"

@function_tool
async def evaluate_teaching(
    ctx: RunContext[Userdata],
    user_explanation: Annotated[str, Field(description="The explanation given by the user during teach-back")]
) -> str:
    """📝 call this when the user has finished explaining a concept in 'teach_back' mode."""
    print(f"📝 EVALUATING EXPLANATION: {user_explanation}")
    return "Analyze the user's explanation. Give them a score out of 10 on accuracy and clarity, and correct any mistakes."



class TutorAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions="""
            You are a Soft Computing Tutor. Help users learn about fuzzy logic, neural networks, and genetic algorithms.
            
            🎯 **YOUR ROLE:**
            - Ask what topic they want to study
            - Use tools to select topics and switch learning modes
            - Provide clear, engaging explanations
            
            📚 **MODES:**
            - LEARN: Explain concepts clearly
            - QUIZ: Test their knowledge
            - TEACH_BACK: Let them explain to you
            """,
            tools=[select_topic, set_learning_mode, evaluate_teaching],
        )



def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    print("\n" + "🧬" * 25)
    print("🚀 STARTING SOFT COMPUTING SESSION")
    print(f"📚 Loaded {len(COURSE_CONTENT)} topics from Knowledge Base")
    
    # 1. Initialize State
    userdata = Userdata(tutor_state=TutorState())

    # 2. Setup Agent
    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-2.5-flash"),
        tts=murf.TTS(
            voice="en-US-matthew", 
            style="Promo",        
            text_pacing=True,
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        userdata=userdata,
    )
    
    # 3. Store session in userdata for tools to access
    userdata.agent_session = session
    
    # 4. Start
    await session.start(
        agent=TutorAgent(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC()
        ),
    )

    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
