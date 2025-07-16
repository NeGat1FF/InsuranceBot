import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    MINDEE_API_KEY = os.getenv("MINDEE_API_KEY")
    MINDEE_PASS_MODEL = os.getenv("MINDEE_PASS_MODEL")
    MINDEE_VEHICLE_MODEL = os.getenv("MINDEE_VEHICLE_MODEL")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

config = Config()