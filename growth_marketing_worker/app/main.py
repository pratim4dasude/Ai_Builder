import os
import sys

import uvicorn
from fastapi import FastAPI

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.api.chat import router as chat_router
from app.api.growth import router as growth_router


app = FastAPI(
    title="Growth Marketing Worker",
    description="Agentic AI worker for product promotion, campaign analysis, content generation, and marketing action memos.",
    version="0.1.0",
)

app.include_router(chat_router)
app.include_router(growth_router)


@app.get("/")
def root():
    return {
        "message": "Growth Marketing Worker is running",
        "docs": "/docs",
        "chat_endpoint": "/chat",
        "stream_endpoint": "/chat/stream",
        "validation_endpoint": "/growth/validate",
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8002,
        reload=True,
    )