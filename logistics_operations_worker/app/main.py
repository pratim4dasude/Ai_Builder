import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from fastapi import FastAPI
from app.api.chat import router as chat_router

app = FastAPI(
    title="Logistics Operations Worker",
    description="Multi-agent AI worker for dispatch planning",
    version="1.0.0",
)

app.include_router(chat_router)


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )