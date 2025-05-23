# orchestrator/main.py
from fastapi import FastAPI
from routers.routers import router as register_router

app = FastAPI(title="Orchestrator Microservice")

app.include_router(register_router, tags=["Register"])
