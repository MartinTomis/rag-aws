from fastapi import FastAPI
from src.api import ingest, query, documents

app = FastAPI()

app.include_router(ingest.router)
app.include_router(query.router)
app.include_router(documents.router)
