from fastapi import APIRouter
from src.api.models import QueryRequest, QueryResult, QueryResponse
from src.processing.rag import query_with_generation

router = APIRouter()

@router.post("/query", response_model=list[QueryResponse])
async def query(req: QueryRequest):
    return [query_with_generation(req.query)]
