from fastapi import APIRouter
from src.api.models import QueryRequest, QueryResult
from scr.api.db import query_documents

router = APIRouter()

@router.post("/query", response_model=list[QueryResult])
async def query(req: QueryRequest):
    results = query_documents(req.query)
    return results
