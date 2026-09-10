from ai_deep_agent.config.settings import (
    GROQ_API_KEY, GROQ_MODEL, GEMINI_API_KEY, GEMINI_MODEL, GEMINI_ROLES
)

def get_llm(role: str = "default", temperature: float = 0.0):
    if role in GEMINI_ROLES and GEMINI_API_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model=GEMINI_MODEL, google_api_key=GEMINI_API_KEY,
                temperature=temperature,
            )
        except Exception:
            pass
    from langchain_groq import ChatGroq
    return ChatGroq(
        model=GROQ_MODEL, api_key=GROQ_API_KEY,
        temperature=temperature, max_retries=3,
    )
