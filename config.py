import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

    assert ANTHROPIC_API_KEY, "Missing ANTHROPIC_API_KEY in .env"

config = Config()
