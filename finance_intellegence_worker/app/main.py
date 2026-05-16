import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

import uvicorn
from fastapi import FastAPI
from app.api.chat import router as chat_router

app = FastAPI(
    title="Finance Intelligence Worker",
    version="1.0.0",
)

app.include_router(chat_router)


@app.get("/")
def root():
    return {
        "message": "Finance Intelligence Worker Running"
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8001,
        reload=True,
    )