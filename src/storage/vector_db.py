from weaviate import connect_to_custom
from weaviate.connect import ConnectionParams
#from weaviate.collections.classes.config import Property, VectorIndexConfig, Vectorizer
from weaviate.classes.config import Property
from weaviate.classes.config import Configure
from uuid import uuid4
from weaviate import connect_to_custom, ConnectionParams
import weaviate.classes.config as wc
import os
from weaviate import connect_to_custom
from weaviate.connect import ConnectionParams
from weaviate.classes.config import Property, Configure, DataType
import weaviate.exceptions


# ✅ Create a reusable connection factory
def get_client():
    return connect_to_custom(

        http_host = os.getenv("WEAVIATE_HTTP_HOST", "weaviate" if os.getenv("IN_DOCKER") else "localhost"),
        http_port=int(os.getenv("WEAVIATE_HTTP_PORT", 8080)),
        grpc_host = os.getenv("WEAVIATE_GRPC_HOST", "weaviate" if os.getenv("IN_DOCKER") else "localhost"),
        grpc_port=int(os.getenv("WEAVIATE_GRPC_PORT", 50051)),
        http_secure=False,
        grpc_secure=False,
        skip_init_checks=True,

    )


# ✅ Init schema
def init_schema():
    

    client = get_client()
    try:
        if "Document" not in client.collections.list_all():
            client.collections.create(
                name="Document",
                description="Stores ingested document chunks",
                vectorizer_config=None,
                properties=[
                    Property(
                        name="text",
                        data_type=DataType.TEXT,
                        description="Chunked text",
                        skip_vectorization=True
                    )
                ],
                vector_index_config=Configure.VectorIndex.hnsw(),
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
    client = get_client()  # This returns a full Weaviate client, not just the collection
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



# https://docs.weaviate.io/weaviate/tutorials/query
# https://docs.weaviate.io/weaviate/api/graphql/search-operators
# https://docs.weaviate.io/weaviate/api/graphql/search-operators#hybrid
'''
alpha can be any number from 0 to 1, defaulting to 0.75.
alpha = 0 forces using a pure keyword search method (BM25)
alpha = 1 forces using a pure vector search method
alpha = 0.5 weighs the BM25 and vector methods evenly

'''
# https://docs.weaviate.io/weaviate/api/graphql/additional-properties
def query_documents(query: str, vector: list[float], top_k: int = 5,min_score: float = 0.5):
    client = get_client()  # assuming you have a helper like this
    try:
        doc_collection = client.collections.get("Document")
        #results = doc_collection.query.near_vector(near_vector=vector,limit=top_k,return_properties=["text"],).with_additional("distance")
        
        #results = doc_collection.query.near_vector(vector).with_limit(top_k).with_fetch_vector().do()
        print("NEAR VECTOR TYPE")


        #results = doc_collection.query.near_vector(near_vector = vector, limit = top_k, distance = 0.7)
        ### Hybrid
        results = doc_collection.query.hybrid(query = query,  vector = vector, limit = top_k, alpha = 0.7)

        return [
            {
                "id": obj.uuid,
                "text": obj.properties["text"],
                "score": 1.0 - obj.metadata.distance if obj.metadata.distance is not None else 0.0  # convert distance to similarity
            }
            for obj in results.objects if (getattr(obj.metadata, "score", 0.0) or 0.0) >= min_score
            ]
    finally:
        client.close()

def retrieve_docs(query: str, vector: list[float], top_k: int = 5, min_score: float = 0.5):
    return query_documents(query, vector, top_k=top_k, min_score = min_score)