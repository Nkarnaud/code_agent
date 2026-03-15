import os


from dotenv import load_dotenv
load_dotenv()


API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")

LLM_MODEL = os.getenv("LLM_MODEL", "qwen/qwen3-coder:free")
