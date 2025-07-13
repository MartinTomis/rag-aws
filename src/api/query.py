from fastapi import APIRouter
from src.api.models import QueryRequest, QueryResponse
from src.processing.rag import query_with_generation

router = APIRouter()

@router.post("/query", response_model=list[QueryResponse])
async def query(req: QueryRequest, top_k: int = 5, alpha: float = 0.7,  min_score: float = 0.5):
    raw_result = query_with_generation(req.query, top_k, alpha, min_score)
    return [QueryResponse(**raw_result)]
