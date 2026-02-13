import os
from dotenv import load_dotenv

load_dotenv()

# Server Configuration
HTTP_PORT = int(os.getenv("AI_SERVICE_PORT", 8012))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# Database Configuration
DATABASE_URI = os.getenv("DATABASE_URI")

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# DeepSeek Configuration
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# Ollama Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

# AI Provider Configuration
DEFAULT_AI_PROVIDER = os.getenv("DEFAULT_AI_PROVIDER", "openai")
SUPPORTED_PROVIDERS = ["openai", "deepseek", "ollama"]