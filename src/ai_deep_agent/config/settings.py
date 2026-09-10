import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY   = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL     = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# Which roles use Gemini (better for long-form synthesis)
GEMINI_ROLES = {r.strip() for r in os.getenv("GEMINI_ROLES", "writer").split(",")}
