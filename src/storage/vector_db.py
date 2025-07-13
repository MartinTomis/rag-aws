from weaviate import connect_to_custom
from uuid import uuid4
import os
import weaviate.classes as wvc
import weaviate.exceptions



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


def delete_document(doc_id: str) -> bool:
    client = get_client()
    try:
        client.data_object.delete(uuid=doc_id, class_name="Document")
        return True
    except weaviate.exceptions.ObjectNotFoundException:
        return False
    finally:
        client.close()


def list_documents(limit: int = 100):
    client = get_client()
    try:
        doc_collection = client.collections.get("Document")
        results = doc_collection.query.fetch_objects(limit=limit)

        return [
            {
                "id": obj.uuid,
                "text": obj.properties.get("text", ""),
                "document_name": obj.properties.get("document_name", "unknown"),
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
def query_documents(query: str, vector: list[float], top_k: int = 5, alpha: float = 0.7, min_score: float = 0.5):
    client = get_client() 
    try:
        doc_collection = client.collections.get("Document")
        ### Hybrid
        results = doc_collection.query.hybrid(query = query,  vector = vector, limit = top_k, alpha = alpha,return_metadata=wvc.query.MetadataQuery(score=True, explain_score=True))

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