from fastapi import FastAPI
from src.api import ingest
from src.api import query
from src.api import documents

app = FastAPI()

# Register router
app.include_router(ingest.router, prefix="/ingest")
app.include_router(query.router, prefix="/query")
app.include_router(documents.router, prefix="/documents")