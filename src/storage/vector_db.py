from uuid import uuid4
from weaviate import connect_to_custom
from weaviate.connect import ConnectionParams

# https://weaviate-python-client.readthedocs.io/en/stable/weaviate.connect.html#weaviate.connect.ConnectionParams
# https://weaviate-python-client.readthedocs.io/en/stable/weaviate.html#module-weaviate.config
# yes - https://weaviate-python-client.readthedocs.io/en/stable/weaviate.connect.html#weaviate.connect.ConnectionParams


client = connect_to_custom(
    http_host="localhost",
    http_port=8080,
    http_secure=False,
    grpc_host="localhost",
    grpc_port=50051,
    grpc_secure=False,
    skip_init_checks=True
)


# Ensure the class exists
def init_schema():
    if not client.schema.contains({"classes": [{"class": "Document"}]}):
        client.schema.create_class({
            "class": "Document",
            "properties": [
                {
                    "name": "text",
                    "dataType": ["text"]
                }
            ],
            "vectorizer": "none"  # You provide vectors manually
        })

init_schema()

# Add document with custom vector
def add_document(text: str, vector: list[float]) -> str:
    doc_id = str(uuid4())
    client.data_object.create(
        data_object={"text": text},
        class_name="Document",
        uuid=doc_id,
        vector=vector,
    )
    return doc_id

# Delete document by ID
def delete_document(doc_id: str) -> bool:
    try:
        client.data_object.delete(uuid=doc_id, class_name="Document")
        return True
    except weaviate.exceptions.ObjectNotFoundException:
        return False

# List all documents (up to limit)
def list_documents(limit: int = 100):
    result = client.query.get("Document", ["text"]).with_limit(limit).do()
    return [
        {"id": obj["uuid"], "text": obj["text"]}
        for obj in result["data"]["Get"]["Document"]
    ]

# Search using a vector
def query_documents(vector: list[float], top_k: int = 5):
    result = client.query.get("Document", ["text"]).with_near_vector({
        "vector": vector
    }).with_limit(top_k).with_additional("distance").do()

    return [
        {
            "id": doc["_additional"]["id"],
            "text": doc["text"],
            "score": 1.0 - doc["_additional"]["distance"]  # distance to similarity
        }
        for doc in result["data"]["Get"]["Document"]
    ]