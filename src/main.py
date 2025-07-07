from fastapi import FastAPI
from src.api import ingest  # this works because you're using src.main

app = FastAPI()

# Register router
app.include_router(ingest.router, prefix="/ingest")
