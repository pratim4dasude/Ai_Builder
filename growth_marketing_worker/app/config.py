import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"

load_dotenv(BASE_DIR / ".env")

PRODUCTS_DATA_PATH = DATA_DIR / "products.csv"
SALES_DATA_PATH = DATA_DIR / "sales.csv"
CAMPAIGNS_DATA_PATH = DATA_DIR / "campaigns.csv"
CUSTOMERS_DATA_PATH = DATA_DIR / "customers.csv"
CONTENT_CALENDAR_DATA_PATH = DATA_DIR / "content_calendar.csv"

RUN_LOG_PATH = LOG_DIR / "runs.json"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
# USE_LLM = os.getenv("USE_LLM", "false").lower() == "true"


USE_LLM_RAW = os.getenv("USE_LLM", "false")

USE_LLM = str(USE_LLM_RAW).strip().lower() in [
    "true",
    "1",
    "yes",
    "y",
    "on",
]