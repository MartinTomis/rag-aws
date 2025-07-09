import json
import pandas as pd
from pathlib import Path
from PyPDF2 import PdfReader

def extract_text_from_pdf(file_path: str) -> list[str]:
    reader = PdfReader(file_path)
    pages = [page.extract_text() or "" for page in reader.pages]
    return pages  # list[str]

def extract_text_from_json(file_path: str) -> list[str]:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [json.dumps(data, indent=2)]  # Wrap in list[str]

def extract_text_from_txt(file_path: str) -> list[str]:
    with open(file_path, "r", encoding="utf-8") as f:
        return [f.read()]  # Wrap in list[str]
    
def extract_text_from_file(file_path: str) -> list[str]:
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext == ".json":
        return extract_text_from_json(file_path)
    elif ext == ".txt":
        return extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
