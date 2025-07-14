from weaviate import connect_to_custom
from uuid import uuid4
import os
from typing import Optional, List
import weaviate.classes as wvc

#from weaviate.collections.classes.filters import Filter
import weaviate.exceptions
from fastapi import HTTPException



def get_client():
    http_host = os.getenv("WEAVIATE_HTTP_HOST", "weaviate" if os.getenv("IN_DOCKER") else "localhost")
    http_port=int(os.getenv("WEAVIATE_HTTP_PORT", 8080))
    grpc_host = os.getenv("WEAVIATE_GRPC_HOST", "weaviate.myapp.local" if os.getenv("IN_DOCKER") else "localhost")
    grpc_port=int(os.getenv("WEAVIATE_GRPC_PORT", 50051))
    return connect_to_custom(
        http_host=http_host,
        http_port=int(http_port),
        grpc_host=grpc_host,
        grpc_port=int(grpc_port),
        http_secure=False,
        grpc_secure=False,
        skip_init_checks=True
    )

# ✅ Init schema
def init_schema():
    

    client = get_client()
    try:
        # Document class
        if "Document" not in client.collections.list_all():
            client.collections.create(
                name="Document",
                description="Stores ingested document chunks",
                vectorizer_config=None,
                properties=[
                    wvc.config.Property(name="text",data_type=wvc.config.DataType.TEXT,description="Chunked text",skip_vectorization=True),
                    wvc.config.Property(name="document_name",data_type=wvc.config.DataType.TEXT,description="File name",skip_vectorization=True),
                    wvc.config.Property(name="topics",data_type=wvc.config.DataType.TEXT_ARRAY,description="Topics of the document",skip_vectorization=True),

                ],
                vector_index_config=wvc.config.Configure.VectorIndex.hnsw(),
            )
        # Topic class
        if "Topic" not in client.collections.list_all():
            client.collections.create(
                name="Topic",
                description="Stores list of allowed/known topics",
                vectorizer_config=None,
                properties=[
                    wvc.config.Property(name="name", data_type=wvc.config.DataType.TEXT, skip_vectorization=True)
                ],
                vector_index_config=wvc.config.Configure.VectorIndex.hnsw(),
            )
        
        # Populate "Topic" at initialialization
        topic_collection = client.collections.get("Topic")
        existing = topic_collection.query.fetch_objects(limit=1)
        if not existing.objects:
            with open("weaviate_data/topics_list.txt", "r") as f:
                topics = [line.strip() for line in f if line.strip()]
            for topic in topics:
                topic_collection.data.insert(properties={"name": topic})
            print(f"Initialized Topic collection with {len(topics)} topics.")
        else:
            print("Topic collection already initialized.")
    finally:
        client.close()

def add_document(text: str, vector: list[float],  metadata: dict = None) -> str:
    doc_id = str(uuid4())
    client = get_client()
    try:
        doc_collection = client.collections.get("Document")
        properties = {"text": text}
        if metadata:
            properties.update(metadata)
        obj = doc_collection.data.insert(properties=properties, vector=vector)
        return doc_id
    finally:
        client.close()


# https://docs.weaviate.io/weaviate/manage-objects/delete
def delete_document(doc_id: str) -> bool:
    client = get_client()
    try:
        collection = client.collections.get("Document")
        collection.data.delete_by_id(uuid=doc_id)
        return True
    except weaviate.exceptions.UnexpectedStatusCodeException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error while deleting document: {e.message}"
        )
    finally:
        client.close()

#https://docs.weaviate.io/weaviate/manage-objects/delete
def delete_documents_by_name(doc_name: str) -> int:
    client = get_client()
    total_deleted = 0
    try:
        collection = client.collections.get("Document")

        filter_obj= wvc.query.Filter.by_property("document_name").equal(doc_name)
        while True:
            result = collection.data.delete_many(where=filter_obj)
            deleted_count = result.matches
            total_deleted += deleted_count
            if deleted_count < 100:
                break  # No more matches

        return total_deleted 
    except weaviate.exceptions.UnexpectedStatusCodeException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error while deleting document: {e.message}"
        )
    finally:
        client.close()


def load_known_topics() -> list[str]:
    client = get_client()
    try:
        if "Topic" not in client.collections.list_all():
            return []
        topic_collection = client.collections.get("Topic")
        results = topic_collection.query.fetch_objects(limit=500)
        return [obj.properties["name"] for obj in results.objects]
    finally:
        client.close()

def add_new_topic(topic: str):
    known_topics = load_known_topics()
    if topic in known_topics:
        return
    client = get_client()
    try:
        topic_collection = client.collections.get("Topic")
        topic_collection.data.insert(properties={"name": topic})
    finally:
        client.close()

# https://docs.weaviate.io/weaviate/search/filters
def list_documents(topics: Optional[List[str]] = None, limit: int = 100):
    client = get_client()
    try:
        doc_collection = client.collections.get("Document")
        if topics:
            results = doc_collection.query.fetch_objects(
                limit=limit,
                filters= wvc.query.Filter.by_property("topics").contains_any(topics))
        else: results = doc_collection.query.fetch_objects(limit=limit)

        return [
            {
                "id": obj.uuid,
                "text": obj.properties.get("text", ""),
                "document_name": obj.properties.get("document_name", "unknown"),
                "topics": obj.properties.get("topics", "unknown"),
                "metadata": {
                    k: v for k, v in obj.properties.items() if k != "text" and k != "document_name"
                }
            }
            for obj in results.objects
        ]
    finally:
        client.close()


'''
# https://docs.weaviate.io/weaviate/api/graphql/search-operators#hybrid
alpha can be any number from 0 to 1, defaulting to 0.75.
alpha = 0 forces using a pure keyword search method (BM25)
alpha = 1 forces using a pure vector search method
alpha = 0.5 weighs the BM25 and vector methods evenly

'''
def query_documents(query: str, vector: list[float], top_k: int = 5, alpha: float = 0.7, min_score: float = 0.5,topics: Optional[List[str]] = None):
    """
    Performs a hybrid search over documents using a query string and vector embedding.

    Parameters:
    - query (str): The text query to search for.
    - vector (list[float]): The vector representation of the query.
    - top_k (int, optional): Number of top results to return. Defaults to 5.
    - alpha (float, optional): Balance between keyword and vector search. Defaults to 0.7.
    - min_score (float, optional): Minimum relevance score for returned documents. Defaults to 0.5.
    - topics (List[str], optional): Optional list of topics to filter results.

    Returns:
    - List[dict]: A list of documents matching the query with text, name, and score.
    """
    client = get_client() 
    try:
        doc_collection = client.collections.get("Document")
        ### Hybrid
        if topics:
            results = doc_collection.query.hybrid(
                query = query,  
                vector = vector, 
                limit = top_k, 
                alpha = alpha,
                filters = wvc.query.Filter.by_property("topics").contains_any(topics),
                return_metadata=wvc.query.MetadataQuery(score=True, explain_score=True))
        else:
            results = doc_collection.query.hybrid(
                query = query,  
                vector = vector, 
                limit = top_k, 
                alpha = alpha,
                return_metadata=wvc.query.MetadataQuery(score=True, explain_score=True))


        return [
            {
                "id": obj.uuid,
                "text": obj.properties["text"],
                "document_name": obj.properties["document_name"],
                "score": obj.metadata.score if obj.metadata.score is not None else 0.0 
            }
            for obj in results.objects if (getattr(obj.metadata, "score", 0.0) or 0.0) >= min_score
            ]
    finally:
        client.close()

def retrieve_docs(query: str, vector: list[float], top_k: int = 5, alpha: float = 0.7, min_score: float = 0.5):
    return query_documents(query, vector, top_k=top_k, min_score = min_score)