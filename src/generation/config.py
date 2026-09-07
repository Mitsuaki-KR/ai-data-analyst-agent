import os

from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = "openai/gpt-oss-120b"

MAX_ROWS_RETURNED = 1000
QUERY_TIMEOUT_SECONDS = 5
MAX_RETRIES = 2