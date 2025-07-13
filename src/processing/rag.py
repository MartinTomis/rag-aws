from src.processing.chunking import fixed_size_chunk, sentence_chunk, sliding_window_chunk
from src.processing.embedding import embed_texts
from src.storage.vector_db import add_document, load_known_topics,add_new_topic
from typing import List, Dict, Optional
from src.storage.vector_db import query_documents as retrieve_docs
from dotenv import load_dotenv
from typing import Optional, List
import os
load_dotenv()  # This will load variables from .env into os.environ
from openai import AzureOpenAI


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
        model="gpt-4", 
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()



def query_with_generation(query: str, top_k: int = 5, alpha : float = 0.7, min_score: float = 0.5,topics: Optional[List[str]] = None ) -> dict:
    query_vector = embed_texts([query])[0]  # Convert query to vector
    results = retrieve_docs(query, query_vector, top_k=top_k, alpha = alpha,  min_score = min_score, topics = topics)
    context_chunks = [doc["text"] for doc in results]
    scores = [doc["score"] for doc in results]
    document_names = [doc["document_name"] for doc in results]
    answer = generate_answer(query, context_chunks)
    return {
        "answer": answer,
        "sources": [doc["text"] for doc in results],
        "scores": scores,
        "document_names": document_names
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
    
def generate_metadata(text: str, possible_topics: list[str]) -> list[str]:
    """
    Uses OpenAI to identify which of the possible topics are relevant to the input text.
    Returns a list of matching topics.
    """
    prompt = f"""
    You are a helpful assistant that tags documents with relevant topics.

    Here is a list of possible topics:
    {', '.join(possible_topics)}

    Given the following document, return only the topics from the list that are clearly mentioned or relevant:

    Document:
    {text}

    Respond with a JSON list of topics.
    """

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2  # to make responses more deterministic
    )

    import json
    try:
        return json.loads(response.choices[0].message.content.strip())
    except json.JSONDecodeError:
        return []


def ingest_document(text: str, strategy: str = "fixed", chunk_args: Optional[Dict] = None,doc_name: str = None, new_topics: Optional[List[str]] = None) -> List[str]:
    chunk_args = chunk_args or {}  # Safely handle default
    chunks = chunk_text(text, strategy, **chunk_args)
    all_topics = load_known_topics()
    embeddings = embed_texts(chunks)
    doc_ids = []

    for chunk, vector in zip(chunks, embeddings):
        metadata = {"document_name": doc_name} if doc_name else {}

        if new_topics:
            for new_topic in new_topics:
                if new_topic not in all_topics:
                    all_topics.append(new_topic)
                    add_new_topic(new_topic)

        if all_topics:
            metadata["topics"] = generate_metadata(chunk, list(set(all_topics)))

        doc_id = add_document(chunk, vector, metadata)  # Stores in Weaviate
        doc_ids.append(doc_id)

    return doc_ids