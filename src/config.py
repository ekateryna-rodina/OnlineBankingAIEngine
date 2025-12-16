import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Environment configuration
TOOL_BASE_URL = os.getenv("TOOL_BASE_URL", "http://localhost:8000")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/v1/chat/completions")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")

# Debug logging
print(f"[CONFIG] TOOL_BASE_URL: {TOOL_BASE_URL}")
print(f"[CONFIG] OLLAMA_URL: {OLLAMA_URL}")
print(f"[CONFIG] OLLAMA_MODEL: {OLLAMA_MODEL}")
print(f"[CONFIG] .env path: {env_path}, exists: {env_path.exists()}")
