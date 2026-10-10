import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
  PROJECT_NAME: str = "Autonomous Debugging Agent"
  DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")
  GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

settings = Settings()