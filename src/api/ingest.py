from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from typing import Optional, List
from tempfile import NamedTemporaryFile
from pathlib import Path
import json

from src.processing.rag import ingest_document
from src.processing.file_parsing import extract_text_from_file
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/ingest")
async def ingest(
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    strategy: str = Form("fixed"),
    chunk_args: str = Form("{}"),
    new_topics: Optional[List[str]] = Query(None)):
    """
    Ingest PDF, JSON or TXT file.
    Options include:
    strategy: 
        - 'fixed' (default value) - chunks of a particular length - default 512 characters (size = 512)
        - 'sentence' - by complete sentences - default mumber is 5 sentences (max_sentences = 5)
        - 'sliding' - uses overlapping window - 512 characters (window_size = 512) with 256 character stride by default (stride = 256)
    """
    
    if new_topics:
        logger.info("Ingest request received", extra={"strategy": strategy,"file": file, "new_topics": ", ".join(new_topics)})
    else:
        logger.info("Ingest request received", extra={"strategy": strategy,"file": file})



    if not text and not file:
        logger.warning("No text or file provided")
        raise HTTPException(status_code=400, detail="Either 'text' or 'file' must be provided.")

    if file:
        suffix = Path(file.filename).suffix
        doc_name = Path(file.filename).name
        try:
            with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(await file.read())
                tmp_path = tmp.name
            text_chunks = extract_text_from_file(tmp_path)  # returns list[str]
            logger.info("Text extracted from the file.")
            text = "\n".join(text_chunks)
        except Exception as e:
            logger.warning("File parsing failed")
            raise HTTPException(status_code=500, detail=f"File parsing failed: {str(e)}")

    try:
        chunk_args_dict = json.loads(chunk_args)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid 'chunk_args' JSON.")

    doc_ids = ingest_document(text, strategy, chunk_args_dict,doc_name=doc_name, new_topics= new_topics)
    logger.info("Document ingested", extra={"file": file})
    return {"status": "success", "chunks": len(doc_ids), "ids": doc_ids}
