from fastapi import APIRouter, HTTPException
from src.storage.vector_db import list_documents, delete_document

router = APIRouter()

@router.get("/documents")
async def get_documents():
    return list_documents()

@router.delete("/documents/{id}")
async def delete(id: str):
    if not delete_document(id):
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "deleted", "id": id}
