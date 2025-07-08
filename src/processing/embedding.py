from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_texts(texts: list[str]) -> list[list[float]]:
    return model.encode(texts, convert_to_numpy=True).tolist()
    #return model.encode(texts).tolist()
