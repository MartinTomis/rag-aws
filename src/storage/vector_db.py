from weaviate import connect_to_custom
from weaviate.connect import ConnectionParams
#from weaviate.collections.classes.config import Property, VectorIndexConfig, Vectorizer
from weaviate.classes.config import Property
from weaviate.classes.config import Configure
from uuid import uuid4
from weaviate import connect_to_custom, ConnectionParams
import weaviate.classes.config as wc

from weaviate import connect_to_custom
from weaviate.connect import ConnectionParams
from weaviate.classes.config import Property, Configure, DataType
from uuid import uuid4
import weaviate.exceptions


# ✅ Create a reusable connection factory
def get_client():
    return connect_to_custom(
        http_host="localhost",
        http_port=8080,
        http_secure=False,
        grpc_host="localhost",
        grpc_port=50051,
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


# ✅ Add document
def add_document(text: str, vector: list[float]) -> str:
    doc_id = str(uuid4())
    client = get_client()
    try:
        client.collections.get("Document").data.insert(
            properties={"text": text},
            vector=vector,
            uuid=doc_id,
        )
        return doc_id
    finally:
        client.close()



# ✅ Delete document
def delete_document(doc_id: str) -> bool:
    client = get_client()
    try:
        client.data_object.delete(uuid=doc_id, class_name="Document")
        return True
    except weaviate.exceptions.ObjectNotFoundException:
        return False
    finally:
        client.close()


# ✅ List documents
def list_documents(limit: int = 100):
    client = get_client()
    try:
        result = client.query.get("Document", ["text"]).with_limit(limit).do()
        return [
            {"id": obj["_additional"]["id"], "text": obj["text"]}
            for obj in result["data"]["Get"]["Document"]
        ]
    finally:
        client.close()


# ✅ Vector search
def query_documents(vector: list[float], top_k: int = 5):
    client = get_client()
    try:
        result = client.query.get("Document", ["text"]).with_near_vector({
            "vector": vector
        }).with_limit(top_k).with_additional("distance").do()

        return [
            {
                "id": doc["_additional"]["id"],
                "text": doc["text"],
                "score": 1.0 - doc["_additional"]["distance"]
            }
            for doc in result["data"]["Get"]["Document"]
        ]
    finally:
        client.close()

