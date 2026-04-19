import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path

# Load backend/.env BEFORE importing api/router (so env vars are available)
load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=False)

# Ensure app INFO logs (e.g. RAG) show in uvicorn console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stderr,
    force=True,
)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

from api import router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/health")
def health():
    return {"status": "ok"}
