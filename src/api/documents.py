from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from src.storage.vector_db import list_documents, delete_document, delete_documents_by_name

router = APIRouter()

@router.get("/documents")
async def get_documents(topics: Optional[List[str]] = Query(None)):
    return list_documents(topics)

@router.delete("/documents/{id}")
async def delete(id: str, by_name: bool = Query(False)):
    """
    Delete a document by UUID (default) or by document_name (if `by_name=true`).
    """
    if by_name:
        deleted_count = delete_documents_by_name(id)
        if deleted_count == 0:
            raise HTTPException(status_code=404, detail="No documents found with this name.")
        return {"status": "deleted", "count": deleted_count, "document_name": id}
    else:
        if not delete_document(id):
            raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "deleted", "id": id}
