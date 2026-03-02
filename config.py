import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
XAI_API_KEY = os.getenv("XAI_API_KEY")
BOT_NAME = os.getenv("BOT_NAME", "Даниэль")

# xAI (Grok) API
GROK_MODEL = os.getenv("GROK_MODEL", "grok-4-1-fast-reasoning")
GROK_BASE_URL = "https://api.x.ai/v1"

# Web search (Tavily)
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Database (Render Postgres or external Postgres)
DATABASE_URL = os.getenv("DATABASE_URL")

# Access control
ALLOWED_USER_IDS = []
if os.getenv("ALLOWED_USER_IDS"):
    ALLOWED_USER_IDS = [int(x.strip()) for x in os.getenv("ALLOWED_USER_IDS").split(",") if x.strip()]

ADMIN_USER_IDS = []
if os.getenv("ADMIN_USER_IDS"):
    ADMIN_USER_IDS = [int(x.strip()) for x in os.getenv("ADMIN_USER_IDS").split(",") if x.strip()]