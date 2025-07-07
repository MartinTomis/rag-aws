from pydantic import BaseModel
from typing import List

class Document(BaseModel):
    id: str
    text: str

class QueryRequest(BaseModel):
    query: str

class QueryResult(BaseModel):
    id: str
    text: str
    score: float
