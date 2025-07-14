from src.processing.chunking import fixed_size_chunk, sentence_chunk, sliding_window_chunk
from src.processing.embedding import embed_texts
from src.storage.vector_db import add_document, load_known_topics,add_new_topic,query_documents as retrieve_docs
from typing import List, Dict, Optional
from dotenv import load_dotenv
import os
load_dotenv()
from openai import AzureOpenAI


api_key=os.getenv("OPENAI_API_KEY")
azure_endpoint = os.getenv("AZURE_ENDPOINT")
api_version= os.getenv("API_VERSION")
openai_model = os.getenv("OPENAI_MODEL")
client = AzureOpenAI(
    api_key=api_key,
    api_version=api_version,
    azure_endpoint=azure_endpoint
)

def generate_answer(query: str, context_chunks: list[str]) -> str:
    """
    Generates an answer to a query using retrieved context chunks by prompting a LLM model.

    Parameters:
    - query (str): The user's question.
    - context_chunks (list[str]): List of text segments retrieved from DB based on selected similarity.

    Returns:
    - str: The generated answer from the model.
    """

    context_text = "\n\n".join(context_chunks)
    prompt = f"""Use the following context to answer the question:\n\n{context_text}\n\nQuestion: {query}"""

    response = client.chat.completions.create(
        model=openai_model, 
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()



def query_with_generation(query: str, top_k: int = 5, alpha : float = 0.7, min_score: float = 0.5,topics: Optional[List[str]] = None ) -> dict:
    """
    Retrieves relevant documents for a query and generates an answer using retrieved context and additional information like score and document names.

    Parameters:
    - query (str): The input question or query string.
    - top_k (int, optional): Number of top documents to retrieve. Defaults to 5.
    - alpha (float, optional): Weight for hybrid search between keyword and vector. Defaults to 0.7.
    - min_score (float, optional): Minimum relevance score for document filtering. Defaults to 0.5.
    - topics (List[str], optional): Optional list of topics to filter the documents.

    Returns:
    - dict: A dictionary containing the generated answer, document sources, their scores, and document names.
    """

    query_vector = embed_texts([query])[0]  
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
    """
    Calls functions from /src/processing/chunking.py, depending on chunking strategy.

    Is used when ingesting documents into DB - is called by ingest_documents


    Returns:
    - List[str]: Text split into chunks.
    """
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
    Needs to be tested. 
    
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
        model=openai_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2 
    )

    import json
    try:
        return json.loads(response.choices[0].message.content.strip())
    except json.JSONDecodeError:
        return []


def ingest_document(text: str, strategy: str = "fixed", chunk_args: Optional[Dict] = None,doc_name: str = None, new_topics: Optional[List[str]] = None) -> List[str]:
    """
    Chunks the input text, generates embeddings and metadata, and stores each chunk in the document database.

    Parameters:
    - text (str): The full document text to be processed.
    - strategy (str): The chunking strategy to apply (e.g., 'fixed', 'sentence', 'sliding').
    - chunk_args (dict, optional): Additional arguments for the chunking function.
    - doc_name (str, optional): Optional name of the source document to include in metadata.
    - new_topics (List[str], optional): Optional list of new topics to add and include in metadata.

    Returns:
    - List[str]: A list of document IDs for the stored chunks.
    """

    chunk_args = chunk_args or {} 
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