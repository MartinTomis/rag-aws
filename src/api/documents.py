from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from src.storage.vector_db import list_documents, delete_document, delete_documents_by_name
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/documents")
async def get_documents(topics: Optional[List[str]] = Query(None)):
    """
    List all documents. Optionally, list only documents where topics match any of those provided by user.
    """
    if topics:
        logger.info("Fetching documents", extra={"topic_filter": ", ".join(topics)})
    else:
        logger.info("Fetching documents")
    docs = list_documents(topics)
    logger.info("Documents fetched", extra={"count": len(docs)})
    return docs

@router.delete("/documents/{id}")
async def delete(id: str, by_name: bool = Query(False)):
    """
    Delete a document by UUID (default) or by document_name (if `by_name=true`).
    """
    if by_name:
        logger.info("Deleting documents by name", extra={"file name": id})
        deleted_count = delete_documents_by_name(id)
        if deleted_count == 0:
            raise HTTPException(status_code=404, detail="No documents found with this name.")
        return {"status": "deleted", "count": deleted_count, "document_name": id}
    else:
        logger.info("Deleting documents by id", extra={"id": id})
        if not delete_document(id):
            logger.warning("Document not found")
            raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "deleted", "id": id}
