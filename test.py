import weaviate

client = weaviate.Client("http://localhost:8080")

# Optional: Test connection
if not client.is_ready():
    raise Exception("Weaviate is not ready")
