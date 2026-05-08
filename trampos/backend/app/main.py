from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .routes import auth, jobs, users

app = FastAPI(title="Trampos API", version="2.0.0")
BACKEND_DIR = Path(__file__).resolve().parents[1]
UPLOADS_DIR = BACKEND_DIR / "uploads"
AVATARS_DIR = UPLOADS_DIR / "avatars"

AVATARS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(jobs.router)

@app.get("/")
def root():
    return {"message": "Trampos API está rodando!"}
