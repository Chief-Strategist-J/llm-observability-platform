import logging
from videosdk.agents import Agent, RealTimePipeline
from videosdk.plugins.google import GeminiRealtime
from videosdk.agents.utils import VideoSDKAgentConfig

logger = logging.getLogger(__name__)

class CustomVoiceAgent(Agent):
    def __init__(self, google_ai_key: str):
        super().__init__(instructions="You are a helpful and friendly voice assistant. Keep your responses concise and conversational.")
        self.google_ai_key = google_ai_key

    async def on_enter(self):
        llm = GeminiRealtime(
            api_key=self.google_ai_key,
            model="gemini-1.5-flash"
        )
        self.pipeline = RealTimePipeline(model=llm)
        self.pipeline.set_agent(self)
        await self.pipeline.start()

    async def on_exit(self):
        await self.pipeline.cleanup()

from videosdk.agents import Worker, WorkerOptions

async def run_agent(meeting_id: str, token: str, google_ai_key: str):
    async def entrypoint(ctx):
        agent = CustomVoiceAgent(google_ai_key=google_ai_key)
        await ctx.connect(agent)

    options = WorkerOptions(
        entrypoint_fnc=entrypoint,
        auth_token=token,
        register=False
    )
    
    Worker.run_worker(options)
