from fastapi import APIRouter
from pydantic import BaseModel
from src.processing.rag import ingest_document

router = APIRouter()

class IngestRequest(BaseModel):
    text: str
    strategy: str = "fixed"
    chunk_args: dict = {}

@router.post("/ingest")
async def ingest(req: IngestRequest):
    doc_ids = ingest_document(req.text, req.strategy, req.chunk_args)
    return {"status": "success", "chunks": len(doc_ids), "ids": doc_ids}
