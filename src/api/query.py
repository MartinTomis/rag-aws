from fastapi import APIRouter, Query
from src.api.models import QueryRequest, QueryResponse
from typing import Optional, List
from src.processing.rag import query_with_generation
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/query", response_model=list[QueryResponse])
async def query(req: QueryRequest, top_k: int = 5, alpha: float = 0.7,  min_score: float = 0.5,topics: Optional[List[str]] = Query(None)):
    """
    Handles a query request and returns a list of generated responses based on the input query.

    Parameters:
    - req (QueryRequest): The query input containing the search string.
    - top_k (int, optional): The number of top results to retrieve. Defaults to 5.
    - alpha (float, optional): Weighting factor for ranking results. Defaults to 0.7.
    - min_score (float, optional): Minimum relevance score threshold. Defaults to 0.5.
    - topics (List[str], optional): Optional list of topic filters to refine the query.

    Returns:
    - List[QueryResponse]: A list containing the top generated query responses.
    """
    logger.info("Received query", extra={"query": req.query, "top_k": top_k, "alpha": alpha, "min_score": min_score })
    raw_result = query_with_generation(req.query, top_k, alpha, min_score, topics)
    logger.info("Query processed", extra={"answer": raw_result["answer"]})
    return [QueryResponse(**raw_result)]
