"""
Configuration for AI Sheets Agent
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Google Sheets API
GOOGLE_CREDENTIALS_FILE = os.environ.get("GOOGLE_CREDENTIALS_FILE", "credentials.json")
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID", "")

# Sheet names
LEADS_SHEET = os.environ.get("LEADS_SHEET", "Leads")
PROCESSED_SHEET = os.environ.get("PROCESSED_SHEET", "Processed")
ANALYTICS_SHEET = os.environ.get("ANALYTICS_SHEET", "Analytics")

# AI Provider: "openai" or "ollama"
AI_PROVIDER = os.environ.get("AI_PROVIDER", "openai")

# OpenAI
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

# Ollama (self-hosted)
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3")

# Telegram notifications (optional)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# Processing settings
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "10"))
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "300"))  # seconds
