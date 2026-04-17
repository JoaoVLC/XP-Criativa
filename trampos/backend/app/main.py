from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routes import jobs, users, auth

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Trampos API", version="2.0.0")

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
