import os
from dotenv import load_dotenv

# Load and check OPENAI_API_KEY env var presence
load_dotenv(override=True)

if os.getenv("OPENAI_API_KEY") is None:
    raise ValueError("OPENAI_API_KEY must be set in .env file")
api_key = os.getenv("OPENAI_API_KEY", "NOT SET")