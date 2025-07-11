from src.processing.chunking import fixed_size_chunk, sentence_chunk, sliding_window_chunk
from src.processing.embedding import embed_texts
from src.storage.vector_db import add_document
from typing import List, Dict, Optional
from src.storage.vector_db import query_documents as retrieve_docs
from dotenv import load_dotenv
import os
load_dotenv()  # This will load variables from .env into os.environ
from openai import OpenAI  # or any LLM SDK
from openai import AzureOpenAI

#client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # make sure it's set
api_key=os.getenv("OPENAI_API_KEY")
client = AzureOpenAI(
    api_key=api_key,
    api_version="2024-12-01-preview",  # or whichever version you're using
    azure_endpoint="https://marti-mc2ahbcl-eastus2.cognitiveservices.azure.com/"
)

def generate_answer(query: str, context_chunks: list[str]) -> str:
    context_text = "\n\n".join(context_chunks)
    prompt = f"""Use the following context to answer the question:\n\n{context_text}\n\nQuestion: {query}"""

    response = client.chat.completions.create(
        model="gpt-4",  # or "gpt-3.5-turbo"
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()



def query_with_generation(query: str, top_k: int = 5) -> dict:
    query_vector = embed_texts([query])[0]  # Convert query to vector
    results = retrieve_docs(query, query_vector, top_k=top_k)
    context_chunks = [doc["text"] for doc in results]
    answer = generate_answer(query, context_chunks)
    return {
        "answer": answer,
        "sources": [doc["text"] for doc in results] 
    }


def chunk_text(text: str, strategy: str = "fixed", **kwargs) -> list[str]:
    if strategy == "fixed":
        return fixed_size_chunk(text, size=kwargs.get("size", 512))
    elif strategy == "sentence":
        return sentence_chunk(text, max_sentences=kwargs.get("max_sentences", 5))
    elif strategy == "sliding":
        return sliding_window_chunk(text, window_size=kwargs.get("window_size", 512),
                                    stride=kwargs.get("stride", 256))
    else:
        raise ValueError(f"Unknown chunking strategy: {strategy}")

def ingest_document(text: str, strategy: str = "fixed", chunk_args: Optional[Dict] = None,doc_name: str = None) -> List[str]:
    chunk_args = chunk_args or {}  # Safely handle default
    chunks = chunk_text(text, strategy, **chunk_args)
    embeddings = embed_texts(chunks)
    doc_ids = []

    for chunk, vector in zip(chunks, embeddings):
        metadata = {"document_name": doc_name} if doc_name else {}
        doc_id = add_document(chunk, vector, metadata)  # Stores in Weaviate
        doc_ids.append(doc_id)

    return doc_ids