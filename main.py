# orchestrator/main.py
from fastapi import FastAPI
from routers.register import router as register_router

app = FastAPI(title="Orchestrator Microservice")

app.include_router(register_router, prefix="/orchestrator", tags=["Register"])
