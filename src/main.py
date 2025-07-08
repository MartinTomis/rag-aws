from fastapi import FastAPI
from src.api import ingest
from src.api import query

app = FastAPI()

# Register router
app.include_router(ingest.router, prefix="/ingest")
app.include_router(query.router, prefix="/query")
