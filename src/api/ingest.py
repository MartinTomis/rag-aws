from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
from tempfile import NamedTemporaryFile
from pathlib import Path
import json

from src.processing.rag import ingest_document
from src.processing.file_parsing import extract_text_from_file

router = APIRouter()

@router.post("/ingest")
async def ingest(
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    strategy: str = Form("fixed"),
    chunk_args: str = Form("{}")
):
    if not text and not file:
        raise HTTPException(status_code=400, detail="Either 'text' or 'file' must be provided.")

    if file:
        suffix = Path(file.filename).suffix
        doc_name = Path(file.filename).name
        try:
            with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(await file.read())
                tmp_path = tmp.name
            text_chunks = extract_text_from_file(tmp_path)  # returns list[str]
            text = "\n".join(text_chunks)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"File parsing failed: {str(e)}")

    try:
        chunk_args_dict = json.loads(chunk_args)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid 'chunk_args' JSON.")

    doc_ids = ingest_document(text, strategy, chunk_args_dict,doc_name=doc_name)
    return {"status": "success", "chunks": len(doc_ids), "ids": doc_ids}
