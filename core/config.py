from dotenv import load_dotenv
import os

load_dotenv()

class LLMKeys:
    groq: str = os.getenv("GROQ_API_KEY")
    openai: str = os.getenv("OPENAI_API_KEY")
    gemini: str = os.getenv("GEMINI_API_KEY")
    # Add more keys here

REDIS_URL = os.getenv("REDIS_URL")
llm_keys = LLMKeys()