from src.processing.chunking import fixed_size_chunk, sentence_chunk, sliding_window_chunk
from src.processing.embedding import embed_texts
from src.storage.vector_db import add_document

def chunk_text(text: str, strategy: str = "fixed", **kwargs) -> list[str]:
    if strategy == "fixed":
        return fixed_size_chunk(text, size=kwargs.get("size", 512))
    elif strategy == "sentence":
        return sentence_chunk(text, max_sentences=kwargs.get("max_sentences", 5))
    elif strategy == "sliding":
        return sliding_window_chunk(text, window_size=kwargs.get("window_size", 512), stride=kwargs.get("stride", 256))
    else:
        raise ValueError(f"Unknown chunking strategy: {strategy}")

def ingest_document(text: str, strategy: str = "fixed", chunk_args: dict = {}):
    chunks = chunk_text(text, strategy, **chunk_args)
    embeddings = embed_texts(chunks)
    
    doc_ids = []
    for chunk, vector in zip(chunks, embeddings):
        doc_id = add_document(chunk, vector)  # Stores in Weaviate
        doc_ids.append(doc_id)
    
    return doc_ids
