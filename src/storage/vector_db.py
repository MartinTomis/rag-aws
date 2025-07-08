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
# https://docs.weaviate.io/weaviate/tutorials/query
# https://docs.weaviate.io/weaviate/api/graphql/search-operators
def query_documents(vector: list[float], top_k: int = 5):
    client = get_client()  # assuming you have a helper like this
    try:
        doc_collection = client.collections.get("Document")
        #results = doc_collection.query.near_vector(near_vector=vector,limit=top_k,return_properties=["text"],).with_additional("distance")
        
        #results = doc_collection.query.near_vector(vector).with_limit(top_k).with_fetch_vector().do()
        print("NEAR VECTOR TYPE")
        #print(type(doc_collection.query.near_vector(vector)))
        results = doc_collection.query.near_vector(near_vector = vector, limit = top_k, distance = 0.7) #.with_limit(top_k).with_additional(["distance"]).with_fields(["text"]).do()

        return [
            {
                "id": obj.uuid,
                "text": obj.properties["text"],
                "score": 1.0 - obj.metadata.distance if obj.metadata.distance is not None else 0.0  # convert distance to similarity
            }
            for obj in results.objects
            ]
    finally:
        client.close()

def retrieve_docs(vector: list[float], top_k: int = 5):
    return query_documents(vector, top_k=top_k)